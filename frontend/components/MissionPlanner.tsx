"use client";

import Link from "next/link";
import { useState } from "react";

import { approveMission, executeMission, planMission } from "@/lib/api";

const DEFAULT_AGENT_LIST =
  "ocr-agent, classification-agent, analysis-agent, prioritization-agent, clustering-agent";

function parseAgents(raw: string): string[] {
  return raw
    .split(/[,;\s]+/)
    .map((s) => s.trim())
    .filter(Boolean);
}

export function MissionPlanner() {
  const [intent, setIntent] = useState("");
  const [agentsCsv, setAgentsCsv] = useState(DEFAULT_AGENT_LIST);
  const [plan, setPlan] = useState<Record<string, unknown> | null>(null);
  const [execution, setExecution] = useState<Record<string, unknown> | null>(null);
  const [busy, setBusy] = useState<string | null>(null);
  const [error, setError] = useState<string>("");

  const missionId =
    typeof plan?.mission_id === "string"
      ? (plan.mission_id as string)
      : typeof execution?.mission_id === "string"
        ? (execution.mission_id as string)
        : "";

  const handlePlan = async () => {
    if (!intent.trim()) {
      setError("Escreva o comando antes de planear.");
      return;
    }
    setBusy("Planeamento…");
    setError("");
    setExecution(null);
    try {
      const payload = (await planMission(intent, parseAgents(agentsCsv))) as Record<string, unknown>;
      setPlan(payload);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro no plano.");
    } finally {
      setBusy(null);
    }
  };

  const handleApprove = async () => {
    if (!missionId) return;
    setBusy("Aprovação…");
    setError("");
    try {
      const refreshed = (await approveMission(missionId)) as Record<string, unknown>;
      setPlan(refreshed);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro ao aprovar.");
    } finally {
      setBusy(null);
    }
  };

  const handleExecute = async () => {
    if (!missionId) return;
    setBusy("Execução EASY…");
    setError("");
    try {
      const payload = (await executeMission(missionId)) as Record<string, unknown>;
      setExecution(payload);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro na execução.");
    } finally {
      setBusy(null);
    }
  };

  const dag = plan?.dag as { nodes?: { node_id?: string; agent_id?: string; description?: string }[] } | undefined;
  const normativeAllowed =
    typeof (plan?.normative_result as { allowed?: boolean } | undefined)?.allowed === "boolean"
      ? (plan!.normative_result as { allowed: boolean }).allowed
      : undefined;

  return (
    <div className="space-y-6">
      <label className="block space-y-2 text-sm">
        <span className="font-medium text-white/80">Comando jurídico</span>
        <textarea
          data-tour="mission-input"
          value={intent}
          onChange={(e) => setIntent(e.target.value)}
          className="min-h-[140px] w-full rounded-xl border border-white/10 bg-deep-space-800/90 px-4 py-3 text-sm text-white outline-none ring-gold-500/40 focus-visible:ring-2"
          placeholder="Ex.: OCR destes pactos sociais e analisar risco contratual; respeitar o Corpus Normativo."
        />
      </label>

      <label className="block space-y-2 text-sm">
        <span className="font-medium text-white/80">Agentes autorizados (IDs EASY, separados)</span>
        <input
          value={agentsCsv}
          onChange={(e) => setAgentsCsv(e.target.value)}
          className="w-full rounded-xl border border-white/10 bg-deep-space-800/90 px-4 py-2 font-mono text-xs text-white outline-none ring-gold-500/40 focus-visible:ring-2"
        />
      </label>

      <div className="flex flex-wrap gap-3">
        <button
          type="button"
          data-cursor-hover
          onClick={() => void handlePlan()}
          disabled={busy !== null}
          className="rounded-full border border-white/25 bg-white/10 px-4 py-2 text-sm font-medium text-white transition hover:border-gold-500/50 hover:bg-gold-500/10 disabled:opacity-40"
        >
          Planear DAG
        </button>
        <button
          type="button"
          data-tour="mission-approve"
          data-cursor-hover
          onClick={() => void handleApprove()}
          disabled={!missionId || busy !== null}
          className="rounded-full bg-gold-500 px-4 py-2 text-sm font-semibold text-deep-space-900 transition hover:bg-gold-400 disabled:opacity-40"
        >
          Aprovar
        </button>
        <button
          type="button"
          data-cursor-hover
          onClick={() => void handleExecute()}
          disabled={!missionId || busy !== null}
          className="rounded-full border border-emerald-400/50 bg-emerald-500/20 px-4 py-2 text-sm font-medium text-emerald-50 transition hover:bg-emerald-500/35 disabled:opacity-40"
        >
          Executar
        </button>
      </div>

      {busy ? <p className="text-xs text-white/55">{busy}</p> : null}
      {error ? <p className="text-xs text-rose-400">{error}</p> : null}

      {missionId ? (
        <p className="text-xs text-white/60">
          Missão:{" "}
          <Link
            className="font-mono text-gold-300 underline"
            href={`/missions/${missionId}`}
            data-mission-id={missionId}
          >
            {missionId}
          </Link>
        </p>
      ) : null}

      {typeof normativeAllowed === "boolean" ? (
        <p className={`text-xs ${normativeAllowed ? "text-emerald-400" : "text-gold-300"}`}>
          Corpus Normativo: {normativeAllowed ? "autorizada" : "bloqueada / alertas"}
        </p>
      ) : null}

      <section className="rounded-2xl border border-dashed border-white/20 bg-deep-space-900/40 p-4">
        <h2 className="text-sm font-semibold text-white/90">DAG proposto</h2>
        <ol className="mt-4 space-y-3 text-xs text-white/70">
          {dag?.nodes?.length ? (
            dag.nodes.map((node, idx) => (
              <li key={node.node_id ?? idx} className="rounded-xl border border-white/10 bg-white/[0.02] p-3">
                <div className="font-mono text-[11px] text-gold-300">{node.agent_id}</div>
                <div className="mt-1 text-white/60">{node.description}</div>
              </li>
            ))
          ) : (
            <li className="text-white/50">Ainda sem DAG planeada — planear comando.</li>
          )}
        </ol>
      </section>

      {execution ? (
        <section className="rounded-2xl border border-white/12 bg-white/[0.02] p-4 text-xs">
          <h3 className="text-sm font-semibold text-white">Resultado execução</h3>
          <pre className="mt-3 max-h-[360px] overflow-auto text-[11px] text-white/70">
            {JSON.stringify(execution, null, 2)}
          </pre>
        </section>
      ) : null}
    </div>
  );
}
