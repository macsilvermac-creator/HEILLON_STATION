"use client";

import { useEffect, useMemo, useState } from "react";

import Link from "next/link";

import { ComplianceReportCard } from "@/components/ComplianceReportCard";
import { fetchComplianceFrameworks, getNormativeRules, postComplianceReport } from "@/lib/api";
import { useAuth } from "@/lib/auth-context";

export default function NormativeHubPage() {
  const { isAuthenticated, isReady } = useAuth();
  const [frameworks, setFrameworks] = useState<unknown[]>([]);
  const [rules, setRules] = useState<unknown[]>([]);
  const [missionIdInput, setMissionIdInput] = useState("");
  const [preview, setPreview] = useState<Record<string, unknown> | null>(null);
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState<string | null>(null);

  useEffect(() => {
    let ignore = false;
    (async () => {
      try {
        const [fw, nw] = await Promise.all([fetchComplianceFrameworks(), getNormativeRules()]);
        if (ignore) return;
        setFrameworks(Array.isArray(fw) ? (fw as unknown[]) : []);
        setRules(Array.isArray(nw) ? (nw as unknown[]) : []);
      } catch (e) {
        if (!ignore) setErr(e instanceof Error ? e.message : "Falha ao carregar âncoras.");
      }
    })();
    return () => {
      ignore = true;
    };
  }, []);

  const gated = useMemo(() => ({ missionIdInput, trimmed: missionIdInput.trim() }), [missionIdInput]);

  async function handleGenerateReport() {
    if (!isAuthenticated || !gated.trimmed.length) return;
    setBusy(true);
    setErr(null);
    setPreview(null);
    try {
      const report = await postComplianceReport(gated.trimmed);
      setPreview(report as Record<string, unknown>);
    } catch (e) {
      setErr(e instanceof Error ? e.message : "Falha ao gerar relatório.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="mx-auto max-w-5xl space-y-8 px-4 pb-36 pt-28">
      <div>
        <h1 className="text-gradient text-3xl font-semibold tracking-tight">Hub normativo — âncoras de legitimidade</h1>
        <p className="mt-3 max-w-3xl text-sm text-white/60">
          Corpus Normativo ativo antes da execução EASY; relatórios de conformidade LGPD ligam HDRs já executados aos
          artigos registados neste quadro jurídico.
        </p>
      </div>

      <section className="grid gap-6 md:grid-cols-2">
        <div className="rounded-2xl border border-white/[0.08] bg-white/[0.03] p-5">
          <h2 className="text-xs font-semibold uppercase tracking-[0.2em] text-gold-400">Frameworks</h2>
          <ul className="mt-3 space-y-2 text-sm text-white/75">
            {frameworks.length ? (
              frameworks.map((fw) => {
                const frame = fw as { framework_id?: string; name?: string; jurisdiction?: string };
                return (
                  <li key={frame.framework_id}>
                    <span className="font-mono text-xs text-emerald-300">{frame.framework_id}</span>
                    {" — "}
                    {frame.name}
                    <span className="text-white/35"> ({frame.jurisdiction})</span>
                  </li>
                );
              })
            ) : (
              <li className="text-xs text-white/45">Sem frameworks — verifique backend /api/v1/compliance/frameworks.</li>
            )}
          </ul>
        </div>

        <div className="rounded-2xl border border-white/[0.08] bg-white/[0.03] p-5">
          <h2 className="text-xs font-semibold uppercase tracking-[0.2em] text-gold-400">Regras activas</h2>
          <p className="mt-2 text-sm text-white/60">{rules.length} regras no corpus (prioridade global).</p>
          <Link href="/missions" className="mt-3 inline-block text-xs text-gold-400 underline-offset-4 hover:underline">
            Abrir dossiers de missão
          </Link>
        </div>
      </section>

      <section className="rounded-2xl border border-white/[0.08] bg-white/[0.03] p-5">
        <h2 className="text-xs font-semibold uppercase tracking-[0.2em] text-gold-400">Relatório LGPD por missão</h2>
        {!isReady || !isAuthenticated ? (
          <p className="mt-3 text-sm text-white/50">Faça sessão para gerar relatórios ancorados à sua organização.</p>
        ) : (
          <div className="mt-4 space-y-3">
            <input
              className="w-full rounded-lg border border-white/15 bg-neutral-950 px-3 py-2 font-mono text-xs text-white"
              placeholder="mission_id …"
              value={missionIdInput}
              onChange={(e) => setMissionIdInput(e.target.value)}
            />
            <button
              type="button"
              onClick={() => void handleGenerateReport()}
              disabled={busy || gated.trimmed.length === 0}
              className="rounded-lg bg-gold-500 px-4 py-2 text-xs font-semibold uppercase tracking-wide text-deep-space-900 disabled:opacity-40"
            >
              Gerar (LGPD-BR)
            </button>
            <ComplianceReportCard
              report={preview}
              busy={busy}
              error={err ?? undefined}
            />
          </div>
        )}
      </section>

      <p className="text-[11px] text-white/40">
        Fase 9 — primeira âncora: LGPD. Extensível para GDPR / ISO 42001 via o mesmo registo de frameworks no backend.
      </p>
    </div>
  );
}
