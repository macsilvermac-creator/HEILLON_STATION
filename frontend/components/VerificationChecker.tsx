"use client";

import { useEffect, useMemo, useState } from "react";
import { useSearchParams } from "next/navigation";

import {
  fetchChainVerification,
  fetchHdrVerification,
} from "@/lib/api";

/** Public verification UX surface (RFC 3161 + digests without login). */

interface VerifyResult {
  valid?: boolean;
  hdr_id?: string;
  mission_id?: string;
  integrity_status?: string;
  timestamp_status?: string;
  chain_status?: string;
  chained_hdr_count?: number;
  details?: { steps?: string[] };
  [key: string]: unknown;
}

export function VerificationChecker() {
  const searchParams = useSearchParams();
  const [mode, setMode] = useState<"hdr" | "chain">("hdr");
  const [target, setTarget] = useState("");
  const [busy, setBusy] = useState(false);
  const [data, setData] = useState<VerifyResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const hinted = searchParams.get("hdr") || searchParams.get("id") || "";
    const normalized = hinted.trim();
    if (normalized) {
      setMode("hdr");
      setTarget(normalized);
    }
  }, [searchParams]);

  const descriptor = useMemo(
    () => (mode === "hdr" ? "hash SHA-256 de 64 hex" : "identificador de missão"),
    [mode],
  );

  const handleVerify = async () => {
    const trimmed = target.trim();
    if (!trimmed) {
      setError("Informe um identificador válido para verificar.");
      setData(null);
      return;
    }
    setBusy(true);
    setError(null);
    setData(null);
    try {
      const payload =
        mode === "hdr"
          ? await fetchHdrVerification(trimmed)
          : await fetchChainVerification(trimmed);
      setData(payload as VerifyResult);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro de rede ou API. Tente novamente.");
    } finally {
      setBusy(false);
    }
  };

  const valid = data?.valid === true;
  const steps = data?.details?.steps ?? [];

  return (
    <div className="space-y-6 rounded-xl border border-neutral-800 bg-neutral-900/70 p-4">
      <div className="flex gap-6 text-xs">
        <label className="flex gap-2">
          <input
            type="radio"
            checked={mode === "hdr"}
            onChange={() => {
              setMode("hdr");
              setData(null);
              setError(null);
            }}
          />{" "}
          HDR único
        </label>
        <label className="flex gap-2">
          <input
            type="radio"
            checked={mode === "chain"}
            onChange={() => {
              setMode("chain");
              setData(null);
              setError(null);
            }}
          />
          Missão inteira
        </label>
      </div>

      <label className="block space-y-2 text-sm">
        <span>Identificador ({descriptor})</span>
        <input
          value={target}
          onChange={(e) => setTarget(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter" && !busy) void handleVerify();
          }}
          className="w-full rounded-lg border border-neutral-800 bg-neutral-950 px-3 py-2 font-mono text-xs outline-none ring-blue-600/70 focus-visible:ring-2"
          placeholder={mode === "hdr" ? "64 hex lowercase" : "mission_xxx"}
        />
      </label>

      <button
        type="button"
        onClick={() => void handleVerify()}
        disabled={busy}
        className="inline-flex items-center gap-2 rounded-lg bg-amber-500 px-4 py-2 text-sm font-semibold text-neutral-950 transition hover:bg-amber-400 disabled:cursor-not-allowed disabled:opacity-50"
      >
        {busy ? (
          <>
            <span className="h-4 w-4 animate-spin rounded-full border-2 border-neutral-950 border-t-transparent" />
            A validar custódia…
          </>
        ) : (
          "Validar custódia"
        )}
      </button>

      {error ? (
        <div
          role="alert"
          className="rounded-lg border border-rose-500/40 bg-rose-500/10 px-4 py-3 text-sm text-rose-200"
        >
          {error}
        </div>
      ) : null}

      {data ? (
        <div className="space-y-4" aria-live="polite">
          <div
            className={`rounded-lg border px-4 py-3 ${
              valid
                ? "border-emerald-500/40 bg-emerald-500/10 text-emerald-200"
                : "border-rose-500/40 bg-rose-500/10 text-rose-200"
            }`}
          >
            <p className="flex items-center gap-2 text-sm font-semibold">
              <span aria-hidden>{valid ? "✓" : "✕"}</span>
              {valid ? "Custódia íntegra" : "Custódia comprometida"}
            </p>
            <p className="mt-1 text-xs opacity-80">
              {valid
                ? "Os elementos criptográficos conferem: o registo não foi adulterado desde a selagem."
                : "Um ou mais elementos não conferem. Este registo não deve ser considerado íntegro."}
            </p>
          </div>

          <dl className="grid grid-cols-2 gap-3 text-xs sm:grid-cols-3">
            <Fact label="Integridade" value={data.integrity_status} />
            <Fact label="Carimbo de tempo" value={data.timestamp_status} />
            <Fact label="Cadeia" value={data.chain_status} />
            {typeof data.chained_hdr_count === "number" ? (
              <Fact label="HDRs encadeados" value={String(data.chained_hdr_count)} />
            ) : null}
            {data.hdr_id ? <Fact label="HDR" value={data.hdr_id} mono /> : null}
            {data.mission_id ? <Fact label="Missão" value={data.mission_id} mono /> : null}
          </dl>

          {steps.length ? (
            <ul className="space-y-1 text-xs text-neutral-300">
              {steps.map((s, i) => (
                <li key={i} className="flex items-start gap-2">
                  <span className="text-amber-400" aria-hidden>
                    •
                  </span>
                  {s}
                </li>
              ))}
            </ul>
          ) : null}

          <details className="group">
            <summary className="cursor-pointer text-xs text-neutral-400 hover:text-neutral-200">
              Ver resposta técnica (JSON)
            </summary>
            <pre className="mt-2 max-h-[420px] overflow-auto rounded-lg border border-neutral-800 bg-neutral-950 p-4 text-[11px] text-neutral-200">
              {JSON.stringify(data, null, 2)}
            </pre>
          </details>
        </div>
      ) : null}
    </div>
  );
}

function Fact({ label, value, mono }: { label: string; value?: string; mono?: boolean }) {
  return (
    <div className="rounded-lg border border-neutral-800 bg-neutral-950/60 px-3 py-2">
      <dt className="text-[10px] uppercase tracking-wider text-neutral-500">{label}</dt>
      <dd className={`mt-0.5 break-all text-neutral-200 ${mono ? "font-mono text-[11px]" : ""}`}>
        {value ?? "—"}
      </dd>
    </div>
  );
}
