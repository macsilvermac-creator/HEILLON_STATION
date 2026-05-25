"use client";

import Link from "next/link";
import { useState } from "react";

import { approveMission, executeMission, planMission } from "@/lib/api";

interface AnalysisTemplate {
  id: string;
  label: string;
  intent: string;
  agents: string;
}

const TEMPLATES: AnalysisTemplate[] = [
  {
    id: "risk-contract",
    label: "Risco contratual",
    intent:
      "Analisar os documentos enviados para identificar cláusulas de risco, responsabilidades excessivas e desequilíbrios contratuais. Priorizar por grau de exposição jurídica.",
    agents: "ocr-agent, analysis-agent, prioritization-agent",
  },
  {
    id: "due-diligence",
    label: "Due diligence societária",
    intent:
      "Realizar due diligence societária: extrair entidades, classificar documentos por categoria legal, agrupar temas e gerar resumo executivo para tomada de decisão.",
    agents: "ocr-agent, classification-agent, clustering-agent, extraction-agent, summarization-agent",
  },
  {
    id: "lgpd-compliance",
    label: "Conformidade LGPD",
    intent:
      "Verificar conformidade dos documentos com a LGPD: identificar dados pessoais, bases legais, finalidades e potenciais violações. Gerar relatório de conformidade.",
    agents: "ocr-agent, classification-agent, analysis-agent, extraction-agent",
  },
  {
    id: "forensic",
    label: "Análise forense",
    intent:
      "Conduzir análise forense digital dos documentos: verificar integridade, detectar alterações, extrair metadados e produzir laudo pericial com cadeia de custódia certificada.",
    agents: "ocr-agent, forensic-agent, analysis-agent",
  },
  {
    id: "clause-review",
    label: "Revisão de cláusulas",
    intent:
      "Extrair e revisar todas as cláusulas relevantes dos contratos, classificar por tipo (penalidade, prazo, exclusividade, rescisão) e destacar itens que requerem atenção.",
    agents: "ocr-agent, extraction-agent, classification-agent, prioritization-agent",
  },
];

const AGENT_LABELS: Record<string, string> = {
  "ocr-agent": "OCR",
  "classification-agent": "Classificação",
  "analysis-agent": "Análise",
  "prioritization-agent": "Priorização",
  "clustering-agent": "Agrupamento",
  "summarization-agent": "Resumo",
  "extraction-agent": "Extracção",
  "forensic-agent": "Forense",
};

function parseAgents(raw: string): string[] {
  return raw
    .split(/[,;\s]+/)
    .map((s) => s.trim())
    .filter(Boolean);
}

function agentBadge(id: string) {
  return AGENT_LABELS[id] ?? id;
}

export function MissionPlanner() {
  const [intent, setIntent] = useState("");
  const [agentsCsv, setAgentsCsv] = useState("ocr-agent, classification-agent, analysis-agent");
  const [activeTemplate, setActiveTemplate] = useState<string | null>(null);
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

  const applyTemplate = (tpl: AnalysisTemplate) => {
    setActiveTemplate(tpl.id);
    setIntent(tpl.intent);
    setAgentsCsv(tpl.agents);
    setError("");
    setPlan(null);
    setExecution(null);
  };

  const handlePlan = async () => {
    if (!intent.trim()) {
      setError("Descreva a análise antes de iniciar.");
      return;
    }
    setBusy("A planear análise…");
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
    setBusy("A aprovar…");
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
    setBusy("A executar e gerar registos de custódia…");
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
      {/* Templates pré-configurados */}
      <div className="space-y-2">
        <p className="text-xs font-medium uppercase tracking-wider text-white/40">Modelos de análise</p>
        <div className="flex flex-wrap gap-2">
          {TEMPLATES.map((tpl) => (
            <button
              key={tpl.id}
              type="button"
              onClick={() => applyTemplate(tpl)}
              className={`rounded-full border px-3 py-1.5 text-xs font-medium transition-colors ${
                activeTemplate === tpl.id
                  ? "border-gold-500/60 bg-gold-500/15 text-gold-200"
                  : "border-white/10 bg-white/[0.04] text-white/60 hover:border-white/20 hover:bg-white/[0.07] hover:text-white/80"
              }`}
            >
              {tpl.label}
            </button>
          ))}
        </div>
      </div>

      <label className="block space-y-2 text-sm">
        <span className="font-medium text-white/80">Descrição da análise</span>
        <textarea
          data-tour="mission-input"
          value={intent}
          onChange={(e) => {
            setIntent(e.target.value);
            setActiveTemplate(null);
          }}
          className="min-h-[120px] w-full rounded-xl border border-white/10 bg-deep-space-800/90 px-4 py-3 text-sm text-white outline-none ring-gold-500/40 focus-visible:ring-2"
          placeholder="Ex.: Analisar estes contratos e identificar cláusulas de risco por grau de exposição."
        />
      </label>

      {/* Assistentes selecionados */}
      {agentsCsv && (
        <div className="space-y-1.5">
          <p className="text-xs font-medium text-white/40">Assistentes autorizados</p>
          <div className="flex flex-wrap gap-1.5">
            {parseAgents(agentsCsv).map((a) => (
              <span key={a} className="rounded-full border border-emerald-500/20 bg-emerald-500/8 px-2.5 py-1 text-[11px] font-mono text-emerald-300/80">
                {agentBadge(a)}
              </span>
            ))}
          </div>
          <input
            value={agentsCsv}
            onChange={(e) => setAgentsCsv(e.target.value)}
            className="w-full rounded-lg border border-white/8 bg-transparent px-3 py-1.5 font-mono text-[11px] text-white/35 outline-none ring-gold-500/40 focus-visible:ring-1"
            aria-label="Editar assistentes (IDs separados por vírgula)"
          />
        </div>
      )}

      <div className="flex flex-wrap gap-3">
        <button
          type="button"
          data-cursor-hover
          onClick={() => void handlePlan()}
          disabled={busy !== null}
          className="rounded-full border border-white/25 bg-white/10 px-4 py-2 text-sm font-medium text-white transition hover:border-gold-500/50 hover:bg-gold-500/10 disabled:opacity-40"
        >
          Iniciar análise
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
          Executar e registar custódia
        </button>
      </div>

      {busy ? (
        <div className="flex items-center gap-2 text-xs text-white/55">
          <span className="h-3 w-3 animate-spin rounded-full border-2 border-gold-400 border-t-transparent" />
          {busy}
        </div>
      ) : null}
      {error ? <p className="text-xs text-rose-400">{error}</p> : null}

      {missionId ? (
        <p className="text-xs text-white/60">
          Análise:{" "}
          <Link
            className="font-mono text-gold-300 underline"
            href={`/missions/${missionId}`}
            data-mission-id={missionId}
          >
            {missionId}
          </Link>
          {" "}— <span className="text-white/40">clique para ver o registo de custódia</span>
        </p>
      ) : null}

      {typeof normativeAllowed === "boolean" ? (
        <p className={`text-xs ${normativeAllowed ? "text-emerald-400" : "text-gold-300"}`}>
          Corpus Normativo: {normativeAllowed ? "análise autorizada" : "alerta normativo — revisar antes de executar"}
        </p>
      ) : null}

      {/* Passos da análise planeada */}
      {dag?.nodes?.length ? (
        <section className="rounded-2xl border border-dashed border-white/20 bg-deep-space-900/40 p-4">
          <h2 className="text-sm font-semibold text-white/90">Passos da análise</h2>
          <ol className="mt-4 space-y-2 text-xs text-white/70">
            {dag.nodes.map((node, idx) => (
              <li key={node.node_id ?? idx} className="flex items-start gap-3 rounded-xl border border-white/10 bg-white/[0.02] p-3">
                <span className="flex h-5 w-5 shrink-0 items-center justify-center rounded-full bg-gold-500/20 text-[10px] font-bold text-gold-300">
                  {idx + 1}
                </span>
                <div>
                  <div className="font-medium text-white/80">{AGENT_LABELS[node.agent_id ?? ""] ?? node.agent_id}</div>
                  <div className="mt-0.5 text-white/50">{node.description}</div>
                </div>
              </li>
            ))}
          </ol>
        </section>
      ) : null}

      {execution ? (
        <section
          data-tour="hdr-result"
          className="rounded-2xl border border-emerald-500/20 bg-emerald-500/[0.04] p-4"
        >
          <h3 className="text-sm font-semibold text-emerald-200">
            Registos de custódia gerados
          </h3>
          <p className="mt-1 text-xs text-white/50">
            Cada passo produziu um registo HDR imutável com hash SHA-256 encadeado.{" "}
            {missionId && (
              <Link href={`/missions/${missionId}`} className="text-gold-300 underline">
                Ver cadeia completa →
              </Link>
            )}
          </p>
          <pre className="mt-3 max-h-[200px] overflow-auto rounded-lg bg-black/30 p-3 text-[10px] text-white/50">
            {JSON.stringify(execution, null, 2)}
          </pre>
        </section>
      ) : null}
    </div>
  );
}
