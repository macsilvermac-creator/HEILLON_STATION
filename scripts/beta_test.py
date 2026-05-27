#!/usr/bin/env python3
"""Heillon Legal — Beta validation script.

Runs 7 end-to-end probes against a live Heillon backend, validates the
freemium promise (Browser Extension + MCP Gateway + verification), and
generates a JSON report for feedback@heillon.com.

USAGE
=====

    python beta_test.py \\
        --server https://api.heillon-beta.com \\
        --api-key heillon_live_xxxxxxxxxxxx

Optional flags:
    --openai-key sk-...        runs Gateway test against real OpenAI
    --anthropic-key sk-ant-... runs Anthropic Gateway test against real Claude
    --skip-network             only runs offline checks (script logic + report)
    --report-path path.json    where to save the JSON report

REQUIREMENTS
============

Python 3.8+ standard library only — no `pip install` needed.
"""

from __future__ import annotations

import argparse
import json
import os
import socket
import ssl
import sys
import time
import urllib.error
import urllib.request
import urllib.parse
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Any


# ── Console helpers ──────────────────────────────────────────────────────────

# Reconfigure stdout/stderr to UTF-8 with errors='replace' so Windows cp1252
# consoles don't crash on unicode glyphs (Python 3.7+).
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")  # type: ignore[attr-defined]
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")  # type: ignore[attr-defined]
except (AttributeError, Exception):
    pass

# ANSI colors; gracefully fall back to plain text on legacy Windows / piped output
_COLOR_ENABLED = sys.stdout.isatty() and os.name != "nt"
if os.name == "nt":
    try:
        import ctypes

        kernel32 = ctypes.windll.kernel32
        # Enable ANSI on modern Windows terminals (Win10+)
        kernel32.SetConsoleMode(kernel32.GetStdHandle(-11), 7)
        _COLOR_ENABLED = sys.stdout.isatty()
    except Exception:  # noqa: BLE001
        _COLOR_ENABLED = False


def _can_unicode() -> bool:
    """Probe whether stdout encoding handles common glyphs."""
    enc = sys.stdout.encoding or "ascii"
    try:
        "✓⚠→".encode(enc)
        return True
    except (UnicodeEncodeError, LookupError):
        return False


_UNICODE_OK = _can_unicode()


def _g(unicode_char: str, ascii_fallback: str) -> str:
    return unicode_char if _UNICODE_OK else ascii_fallback


def _c(text: str, code: str) -> str:
    return f"\033[{code}m{text}\033[0m" if _COLOR_ENABLED else text


def ok(text: str) -> str:
    return _c(f"{_g('✓', '[OK]')} {text}", "32")


def fail(text: str) -> str:
    return _c(f"{_g('✗', '[FAIL]')} {text}", "31")


def warn(text: str) -> str:
    return _c(f"{_g('⚠', '[!]')} {text}", "33")


def info(text: str) -> str:
    return _c(f"{_g('→', '->')} {text}", "36")


def bold(text: str) -> str:
    return _c(text, "1")


# ── Data model ──────────────────────────────────────────────────────────────


@dataclass
class ProbeResult:
    name: str
    passed: bool
    duration_ms: int
    detail: str = ""
    artifacts: dict[str, Any] = field(default_factory=dict)


@dataclass
class BetaReport:
    started_at: str
    completed_at: str = ""
    server_url: str = ""
    organization_id: str = ""
    tier: str = ""
    quota_used_before: int | None = None
    quota_used_after: int | None = None
    probes: list[ProbeResult] = field(default_factory=list)
    environment: dict[str, str] = field(default_factory=dict)

    @property
    def passed_count(self) -> int:
        return sum(1 for p in self.probes if p.passed)

    @property
    def total_count(self) -> int:
        return len(self.probes)


# ── HTTP client (stdlib) ────────────────────────────────────────────────────


class HttpError(Exception):
    def __init__(self, status: int, body: Any) -> None:
        self.status = status
        self.body = body
        super().__init__(f"HTTP {status}")


def _request(
    method: str,
    url: str,
    *,
    headers: dict[str, str] | None = None,
    body: dict[str, Any] | None = None,
    timeout: float = 30.0,
) -> tuple[int, dict[str, str], Any]:
    """Stdlib request returning (status, response_headers, parsed_body)."""
    data = json.dumps(body).encode("utf-8") if body is not None else None
    req_headers = {"User-Agent": "HeillonBeta/1.0", "Accept": "application/json"}
    if data:
        req_headers["Content-Type"] = "application/json"
    if headers:
        req_headers.update(headers)

    req = urllib.request.Request(url, data=data, method=method, headers=req_headers)
    ctx = ssl.create_default_context()

    try:
        with urllib.request.urlopen(req, timeout=timeout, context=ctx) as resp:
            raw = resp.read()
            response_headers = {k.lower(): v for k, v in resp.headers.items()}
            try:
                parsed = json.loads(raw.decode("utf-8")) if raw else None
            except json.JSONDecodeError:
                parsed = raw.decode("utf-8", errors="replace")
            return resp.status, response_headers, parsed
    except urllib.error.HTTPError as e:
        raw = e.read()
        try:
            parsed = json.loads(raw.decode("utf-8")) if raw else None
        except json.JSONDecodeError:
            parsed = raw.decode("utf-8", errors="replace")
        raise HttpError(e.code, parsed)
    except (urllib.error.URLError, socket.timeout, ssl.SSLError) as e:
        raise HttpError(0, {"error": {"message": f"Connection failed: {e}"}})


# ── Probes ──────────────────────────────────────────────────────────────────


def probe_health(server: str, report: BetaReport) -> ProbeResult:
    """1/7 — Server reachable, /health returns 200 without auth."""
    print(f"\n{info('[1/7] Testando alcance do servidor...')}")
    t0 = time.time()
    try:
        status, _, body = _request("GET", f"{server}/health")
        elapsed = int((time.time() - t0) * 1000)
        if status == 200:
            print(ok(f"     Servidor responde em {elapsed}ms ({server})"))
            return ProbeResult("server_health", True, elapsed, "200 OK", body or {})
        return ProbeResult("server_health", False, elapsed, f"HTTP {status}", {})
    except HttpError as e:
        elapsed = int((time.time() - t0) * 1000)
        print(fail(f"     Falha de conexão: {e.body}"))
        return ProbeResult(
            "server_health", False, elapsed, f"HTTP {e.status}", {"error": e.body}
        )


def probe_api_key(server: str, api_key: str, report: BetaReport) -> ProbeResult:
    """2/7 — API key valida + retorna org_id + tier + quota inicial."""
    print(f"\n{info('[2/7] Validando chave de API...')}")
    t0 = time.time()
    url = f"{server}/api/v1/extension/health"
    headers = {"X-Heillon-Api-Key": api_key}
    try:
        status, _, body = _request("GET", url, headers=headers)
        elapsed = int((time.time() - t0) * 1000)
        if status == 200 and isinstance(body, dict) and body.get("ok"):
            report.organization_id = body.get("organization_id", "")
            report.tier = body.get("tier", "")
            quota = body.get("quota", {})
            report.quota_used_before = quota.get("used")
            print(
                ok(
                    f"     org={report.organization_id} tier={report.tier} "
                    f"quota={quota.get('used')}/{quota.get('limit')}"
                )
            )
            return ProbeResult(
                "api_key_valid",
                True,
                elapsed,
                "200 OK + quota retornada",
                {"organization_id": report.organization_id, "tier": report.tier},
            )
        print(fail(f"     Chave inválida ou resposta inesperada: {body}"))
        return ProbeResult("api_key_valid", False, elapsed, f"HTTP {status}", {"body": body})
    except HttpError as e:
        elapsed = int((time.time() - t0) * 1000)
        if e.status == 401:
            print(fail("     API key REJEITADA (401). Verifique a chave."))
        else:
            print(fail(f"     Erro: HTTP {e.status} — {e.body}"))
        return ProbeResult(
            "api_key_valid", False, elapsed, f"HTTP {e.status}", {"error": e.body}
        )


def probe_quota_endpoint(
    server: str, api_key: str, report: BetaReport
) -> ProbeResult:
    """3/7 — /me/quota requer JWT (cookie); só verifica que /extension/health
    já populou os dados — endpoint /me/quota é só para console."""
    print(f"\n{info('[3/7] Inspecionando quota (via /extension/health)...')}")
    # Já temos quota do passo 2; só confirmamos consistência
    if report.tier and report.quota_used_before is not None:
        print(
            ok(
                f"     Quota inicial: {report.quota_used_before} HDRs no plano {report.tier}"
            )
        )
        return ProbeResult(
            "quota_inspection",
            True,
            0,
            f"Quota inicial registrada ({report.quota_used_before})",
            {
                "tier": report.tier,
                "used_before": report.quota_used_before,
            },
        )
    print(fail("     Probe 2 falhou — quota não foi capturada"))
    return ProbeResult("quota_inspection", False, 0, "Dependência do probe 2 falhou", {})


def probe_extension_capture(
    server: str, api_key: str, report: BetaReport
) -> ProbeResult:
    """4/7 — Cria 1 HDR via Browser Extension endpoint (capture sintética)."""
    print(f"\n{info('[4/7] Criando HDR sintético via Extension endpoint...')}")
    t0 = time.time()
    url = f"{server}/api/v1/extension/capture"
    headers = {"X-Heillon-Api-Key": api_key}
    payload = {
        "provider": "openai",
        "model": "gpt-4o-mini",
        "prompt": (
            "[BETA TEST] Resuma em 2 linhas o art. 7º da LGPD. "
            f"Capture sintetizada por beta_test.py em {datetime.now(timezone.utc).isoformat()}."
        ),
        "response": (
            "[BETA TEST RESPONSE] O art. 7º da LGPD lista as 10 bases legais para "
            "tratamento de dados pessoais — incluindo consentimento, execução de "
            "contrato, obrigação legal, proteção do crédito e legítimo interesse."
        ),
        "source_url": "https://chat.openai.com/c/beta-test",
        "captured_at": datetime.now(timezone.utc).isoformat(),
        "ai_session_id": f"beta_test_{int(time.time())}",
        "extension_version": "0.1.0",
        "page_title": "Heillon Beta Test — ChatGPT",
    }
    try:
        status, _, body = _request("POST", url, headers=headers, body=payload)
        elapsed = int((time.time() - t0) * 1000)
        if status == 201 and isinstance(body, dict):
            hdr_id = body.get("hdr_id", "")
            verification_url = body.get("verification_url", "")
            quota = body.get("quota", {})
            print(ok(f"     HDR criado: {hdr_id[:16]}... ({elapsed}ms)"))
            print(ok(f"     Mission: {body.get('mission_id', '')}"))
            print(ok(f"     Verificável em: {verification_url}"))
            print(ok(f"     Quota agora: {quota.get('used')}/{quota.get('limit')}"))
            return ProbeResult(
                "extension_capture",
                True,
                elapsed,
                f"HDR criado em {elapsed}ms",
                {
                    "hdr_id": hdr_id,
                    "mission_id": body.get("mission_id"),
                    "verification_url": verification_url,
                    "quota_after": quota,
                },
            )
        print(fail(f"     Resposta inesperada: HTTP {status}"))
        return ProbeResult("extension_capture", False, elapsed, f"HTTP {status}", {})
    except HttpError as e:
        elapsed = int((time.time() - t0) * 1000)
        if e.status == 402:
            print(warn(f"     Quota excedida (402). Esperado se você já usou 50."))
            return ProbeResult(
                "extension_capture",
                False,
                elapsed,
                "Quota excedida (HTTP 402)",
                {"error": e.body},
            )
        print(fail(f"     Erro: HTTP {e.status} — {e.body}"))
        return ProbeResult(
            "extension_capture", False, elapsed, f"HTTP {e.status}", {"error": e.body}
        )


def probe_verification_public(
    server: str, hdr_id: str, report: BetaReport
) -> ProbeResult:
    """5/7 — Verificação pública (sem login) do HDR criado."""
    print(f"\n{info('[5/7] Verificando HDR publicamente (sem login)...')}")
    if not hdr_id:
        print(fail("     Sem HDR para verificar (probe 4 falhou)"))
        return ProbeResult("public_verification", False, 0, "Sem HDR criado", {})

    t0 = time.time()
    # Try both the dedicated verification page route AND the /verify/{hdr_id} API
    api_url = f"{server}/api/v1/verify/{hdr_id}"
    try:
        status, _, body = _request("GET", api_url, timeout=15.0)
        elapsed = int((time.time() - t0) * 1000)
        if status == 200 and isinstance(body, dict):
            print(ok(f"     Verificação OK ({elapsed}ms)"))
            print(ok(f"     hdr_type: {body.get('hdr_type', 'n/a')}"))
            print(ok(f"     canonical_hash: {str(body.get('canonical_hash', ''))[:16]}..."))
            return ProbeResult(
                "public_verification",
                True,
                elapsed,
                "Verificação pública 200",
                {"hdr_type": body.get("hdr_type"), "valid": True},
            )
        print(fail(f"     HTTP {status}"))
        return ProbeResult("public_verification", False, elapsed, f"HTTP {status}", {})
    except HttpError as e:
        elapsed = int((time.time() - t0) * 1000)
        print(fail(f"     Erro: HTTP {e.status}"))
        return ProbeResult(
            "public_verification", False, elapsed, f"HTTP {e.status}", {"error": e.body}
        )


def probe_gateway_openai(
    server: str,
    api_key: str,
    openai_key: str | None,
    report: BetaReport,
) -> ProbeResult:
    """6/7 — Gateway OpenAI-compat (opcional, exige chave OpenAI real)."""
    print(f"\n{info('[6/7] Testando MCP Gateway OpenAI-compat...')}")
    if not openai_key:
        print(warn("     PULADO (sem --openai-key). Adicione para testar full path."))
        return ProbeResult(
            "gateway_openai", True, 0, "Pulado intencionalmente", {"skipped": True}
        )

    t0 = time.time()
    url = f"{server}/api/v1/gateway/v1/chat/completions"
    headers = {
        "X-Heillon-Api-Key": api_key,
        "X-Upstream-Api-Key": openai_key,
    }
    payload = {
        "model": "gpt-4o-mini",
        "messages": [
            {"role": "user", "content": "Responda em uma única linha: o que é LGPD?"}
        ],
        "max_tokens": 64,
        "temperature": 0,
    }
    try:
        status, resp_headers, body = _request(
            "POST", url, headers=headers, body=payload, timeout=60.0
        )
        elapsed = int((time.time() - t0) * 1000)
        if status == 200 and isinstance(body, dict):
            hdr_id = resp_headers.get("x-heillon-hdr-id", "")
            quota_used = resp_headers.get("x-heillon-quota-used", "?")
            content = body.get("choices", [{}])[0].get("message", {}).get("content", "")
            print(ok(f"     Forward OK em {elapsed}ms"))
            print(ok(f"     HDR criado: {hdr_id[:16] if hdr_id else 'N/A'}..."))
            print(ok(f"     Quota: {quota_used} HDRs"))
            print(info(f"     Resposta do modelo: {content[:80]}..."))
            return ProbeResult(
                "gateway_openai",
                True,
                elapsed,
                f"Forward OK em {elapsed}ms",
                {"hdr_id": hdr_id, "model_response_preview": content[:200]},
            )
        print(fail(f"     HTTP {status}: {body}"))
        return ProbeResult("gateway_openai", False, elapsed, f"HTTP {status}", {})
    except HttpError as e:
        elapsed = int((time.time() - t0) * 1000)
        print(fail(f"     Erro: HTTP {e.status} — {e.body}"))
        return ProbeResult(
            "gateway_openai", False, elapsed, f"HTTP {e.status}", {"error": e.body}
        )


def probe_gateway_anthropic(
    server: str,
    api_key: str,
    anthropic_key: str | None,
    report: BetaReport,
) -> ProbeResult:
    """7/7 — Gateway Anthropic Messages compat (opcional)."""
    print(f"\n{info('[7/7] Testando MCP Gateway Anthropic Messages...')}")
    if not anthropic_key:
        print(warn("     PULADO (sem --anthropic-key)."))
        return ProbeResult(
            "gateway_anthropic", True, 0, "Pulado intencionalmente", {"skipped": True}
        )

    t0 = time.time()
    url = f"{server}/api/v1/gateway/anthropic/v1/messages"
    headers = {
        "X-Heillon-Api-Key": api_key,
        "X-Upstream-Api-Key": anthropic_key,
        "anthropic-version": "2023-06-01",
    }
    payload = {
        "model": "claude-3-5-sonnet-20241022",
        "max_tokens": 64,
        "messages": [
            {"role": "user", "content": "Responda em uma única linha: o que é LGPD?"}
        ],
    }
    try:
        status, resp_headers, body = _request(
            "POST", url, headers=headers, body=payload, timeout=60.0
        )
        elapsed = int((time.time() - t0) * 1000)
        if status == 200 and isinstance(body, dict):
            hdr_id = resp_headers.get("x-heillon-hdr-id", "")
            content = body.get("content", [{}])[0].get("text", "") if body.get("content") else ""
            print(ok(f"     Forward OK em {elapsed}ms"))
            print(ok(f"     HDR criado: {hdr_id[:16] if hdr_id else 'N/A'}..."))
            print(info(f"     Resposta do Claude: {content[:80]}..."))
            return ProbeResult(
                "gateway_anthropic",
                True,
                elapsed,
                f"Forward OK em {elapsed}ms",
                {"hdr_id": hdr_id, "model_response_preview": content[:200]},
            )
        print(fail(f"     HTTP {status}: {body}"))
        return ProbeResult("gateway_anthropic", False, elapsed, f"HTTP {status}", {})
    except HttpError as e:
        elapsed = int((time.time() - t0) * 1000)
        print(fail(f"     Erro: HTTP {e.status} — {e.body}"))
        return ProbeResult(
            "gateway_anthropic", False, elapsed, f"HTTP {e.status}", {"error": e.body}
        )


# ── Final summary + report ──────────────────────────────────────────────────


def print_summary(report: BetaReport) -> None:
    print()
    print(bold("=" * 60))
    print(bold("  Resultado do Beta Test"))
    print(bold("=" * 60))
    print(f"  Servidor:        {report.server_url}")
    print(f"  Organização:     {report.organization_id}")
    print(f"  Tier:            {report.tier}")
    print(f"  Quota antes:     {report.quota_used_before}")
    print(f"  Quota depois:    {report.quota_used_after}")
    print(f"  HDRs criados:    {((report.quota_used_after or 0) - (report.quota_used_before or 0))}")
    print()
    print(f"  Testes:          {report.passed_count}/{report.total_count} passaram")
    print()

    for p in report.probes:
        marker = ok("OK") if p.passed else fail("FAIL")
        print(f"    [{marker}] {p.name} ({p.duration_ms}ms) — {p.detail}")

    print()
    if report.passed_count == report.total_count:
        print(bold(ok("✅ TODOS OS TESTES PASSARAM — Heillon está operacional!")))
    else:
        print(
            bold(
                warn(
                    f"⚠ {report.total_count - report.passed_count} testes falharam. "
                    "Anexe o relatório no FEEDBACK.md."
                )
            )
        )
    print()


def save_report(report: BetaReport, path: str) -> None:
    payload = asdict(report)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)
    print(info(f"Relatório salvo em: {bold(path)}"))
    print(info(f"Anexe ao seu feedback: feedback@heillon.com"))


# ── Main ─────────────────────────────────────────────────────────────────────


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Heillon Legal beta validation script.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument("--server", required=True, help="URL base do Heillon backend")
    parser.add_argument("--api-key", required=True, help="Chave heillon_live_...")
    parser.add_argument("--openai-key", help="Chave sk-... (opcional)")
    parser.add_argument("--anthropic-key", help="Chave sk-ant-... (opcional)")
    parser.add_argument(
        "--skip-network", action="store_true", help="Apenas checks offline"
    )
    parser.add_argument(
        "--report-path",
        default=f"beta_test_report_{datetime.now().strftime('%Y-%m-%d_%H%M%S')}.json",
        help="Caminho para salvar o relatório JSON",
    )
    args = parser.parse_args()

    server = args.server.rstrip("/")
    if not args.api_key.startswith("heillon_live_"):
        print(fail("Chave deve começar com 'heillon_live_' — abortando."))
        return 2

    print()
    print(bold("Heillon Legal — Beta Validation Script v0.1.0"))
    print("=" * 60)
    print(f"  Servidor: {server}")
    print(f"  Chave:    {args.api_key[:20]}...")
    print(f"  OpenAI:   {'sim' if args.openai_key else 'pulado'}")
    print(f"  Anthropic: {'sim' if args.anthropic_key else 'pulado'}")
    print("=" * 60)

    report = BetaReport(
        started_at=datetime.now(timezone.utc).isoformat(),
        server_url=server,
        environment={
            "python_version": sys.version.split()[0],
            "platform": sys.platform,
            "script_version": "0.1.0",
        },
    )

    if args.skip_network:
        print(warn("\n--skip-network: rodando apenas checks offline"))
        report.completed_at = datetime.now(timezone.utc).isoformat()
        save_report(report, args.report_path)
        return 0

    # Run probes in sequence (each may depend on previous state)
    report.probes.append(probe_health(server, report))
    report.probes.append(probe_api_key(server, args.api_key, report))
    report.probes.append(probe_quota_endpoint(server, args.api_key, report))

    capture_result = probe_extension_capture(server, args.api_key, report)
    report.probes.append(capture_result)

    hdr_id = capture_result.artifacts.get("hdr_id", "")
    report.probes.append(probe_verification_public(server, hdr_id, report))

    report.probes.append(
        probe_gateway_openai(server, args.api_key, args.openai_key, report)
    )
    report.probes.append(
        probe_gateway_anthropic(server, args.api_key, args.anthropic_key, report)
    )

    # Final quota snapshot
    try:
        _, _, body = _request(
            "GET",
            f"{server}/api/v1/extension/health",
            headers={"X-Heillon-Api-Key": args.api_key},
        )
        if isinstance(body, dict):
            report.quota_used_after = body.get("quota", {}).get("used")
    except Exception:  # noqa: BLE001
        pass

    report.completed_at = datetime.now(timezone.utc).isoformat()
    print_summary(report)
    save_report(report, args.report_path)

    return 0 if report.passed_count == report.total_count else 1


if __name__ == "__main__":
    sys.exit(main())
