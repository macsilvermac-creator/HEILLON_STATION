"use client";

import { useEffect, useState } from "react";
import Link from "next/link";

import { fetchChainVerification, fetchMissionPlan } from "@/lib/api";

interface DAGNode {
  node_id: string;
  agent_id: string;
  description?: string;
  action?: string;
}

interface MissionPlan {
  mission_id: string;
  description?: string;
  status?: string;
  hdrs_generated?: string[];
  dag?: { nodes?: DAGNode[] };
  created_at?: string;
}

interface ChainVerification {
  valid?: boolean;
  mission_id?: string;
  total_hdrs?: number;
}

interface HDRChainProps {
  missionId: string;
}

const AGENT_LABELS: Record<string, string> = {
  "ocr-agent": "Extração de texto (OCR)",
  "classification-agent": "Classificação de documentos",
  "analysis-agent": "Análise de risco",
  "prioritization-agent": "Priorização por relevância",
  "clustering-agent": "Agrupamento temático",
  "summarization-agent": "Resumo executivo",
  "extraction-agent": "Extracção de entidades",
  "forensic-agent": "Análise forense",
};

function labelForNode(node: DAGNode, index: number): string {
  return AGENT_LABELS[node.agent_id] ?? node.description ?? `Passo ${index + 1}`;
}

function shortHash(hash: string): string {
  return hash.slice(0, 8).toUpperCase();
}

export function HDRChain({ missionId }: HDRChainProps) {
  const [mission, setMission] = useState<MissionPlan | null>(null);
  const [verification, setVerification] = useState<ChainVerification | null>(null);
  const [error, setError] = useState<string>("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let ignore = false;
    (async () => {
      setLoading(true);
      try {
        const [snap, chain] = await Promise.all([
          fetchMissionPlan(missionId) as Promise<MissionPlan>,
          fetchChainVerification(missionId) as Promise<ChainVerification>,
        ]);
        if (ignore) return;
        setMission(snap);
        setVerification(chain);
      } catch (err) {
        if (!ignore) setError(err instanceof Error ? err.message : "Falhou leitura do registo de custódia.");
      } finally {
        if (!ignore) setLoading(false);
      }
    })();
    return () => {
      ignore = true;
    };
  }, [missionId]);

  const nodes: DAGNode[] = mission?.dag?.nodes ?? [];
  const hdrIds: string[] = mission?.hdrs_generated ?? [];
  const isValid = verification?.valid === true;
  const totalHdrs = verification?.total_hdrs ?? hdrIds.length;

  if (loading) {
    return (
      <div className="space-y-3 rounded-2xl border border-neutral-800 bg-neutral-900/60 p-5">
        <div className="h-4 w-40 animate-pulse rounded-full bg-white/5" />
        <div className="h-3 w-full animate-pulse rounded-full bg-white/5" />
        <div className="h-3 w-2/3 animate-pulse rounded-full bg-white/5" />
      </div>
    );
  }

  return (
    <div className="space-y-5 rounded-2xl border border-neutral-800 bg-neutral-900/60 p-5">
      <div className="flex flex-col gap-1 sm:flex-row sm:items-center sm:justify-between">
        <h2 className="text-base font-semibold text-white">Registo de custódia</h2>
        {verification !== null ? (
          <span
            className={`inline-flex items-center gap-1.5 rounded-full px-3 py-1 text-xs font-semibold ${
              isValid
                ? "border border-emerald-500/30 bg-emerald-500/10 text-emerald-300"
                : "border border-rose-500/30 bg-rose-500/10 text-rose-300"
            }`}
          >
            {isValid ? (
              <svg className="h-3 w-3" fill="currentColor" viewBox="0 0 20 20" aria-hidden>
                <path
                  fillRule="evenodd"
                  d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.857-9.809a.75.75 0 00-1.214-.882l-3.483 4.79-1.88-1.88a.75.75 0 10-1.06 1.061l2.5 2.5a.75.75 0 001.137-.089l4-5.5z"
                  clipRule="evenodd"
                />
              </svg>
            ) : (
              <svg className="h-3 w-3" fill="currentColor" viewBox="0 0 20 20" aria-hidden>
                <path
                  fillRule="evenodd"
                  d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-8-5a.75.75 0 01.75.75v4.5a.75.75 0 01-1.5 0v-4.5A.75.75 0 0110 5zm0 10a1 1 0 100-2 1 1 0 000 2z"
                  clipRule="evenodd"
                />
              </svg>
            )}
            {isValid ? "Cadeia íntegra" : "Integridade pendente"}
          </span>
        ) : null}
      </div>

      <div className="rounded-xl border border-gold-500/20 bg-gold-500/[0.07] px-4 py-3 text-[11px] leading-relaxed text-gold-100/80">
        Cada passo abaixo gerou um registo HDR imutável com hash SHA-256 e carimbo temporal certificado.
        A cadeia pode ser verificada publicamente a qualquer momento.{" "}
        <Link href="/normative" className="text-gold-300 underline-offset-4 hover:underline">
          Ver âncoras normativas →
        </Link>
      </div>

      {error ? (
        <p className="rounded-lg border border-rose-500/25 bg-rose-500/10 px-3 py-2 text-xs text-rose-300">{error}</p>
      ) : null}

      {/* Steps timeline */}
      {hdrIds.length > 0 ? (
        <ol className="relative space-y-0 border-l border-white/10 pl-5">
          {hdrIds.map((hdrId, idx) => {
            const node = nodes[idx];
            const label = node ? labelForNode(node, idx) : `Passo ${idx + 1}`;
            return (
              <li key={hdrId} className="relative pb-5 last:pb-0">
                <span className="absolute -left-[1.125rem] flex h-5 w-5 items-center justify-center rounded-full border border-emerald-500/50 bg-emerald-500/10 text-[9px] font-bold text-emerald-300">
                  {idx + 1}
                </span>
                <div className="ml-1 rounded-xl border border-white/[0.07] bg-neutral-950/70 px-4 py-3">
                  <p className="text-sm font-medium text-white">{label}</p>
                  {node?.agent_id ? (
                    <p className="mt-0.5 text-[11px] text-white/40">Assistente: {node.agent_id}</p>
                  ) : null}
                  <p className="mt-2 font-mono text-[10px] text-white/25">
                    ID de custódia: {shortHash(hdrId)}…
                    <span className="ml-2 text-white/15">(SHA-256)</span>
                  </p>
                </div>
              </li>
            );
          })}
        </ol>
      ) : (
        <p className="text-xs text-neutral-500">
          {mission?.status === "approved"
            ? "Análise aprovada — execute para gerar os registos de custódia."
            : "Sem registos de custódia nesta análise ainda."}
        </p>
      )}

      {totalHdrs > 0 && (
        <div className="border-t border-white/5 pt-3 text-[11px] text-white/35">
          {totalHdrs} registo{totalHdrs > 1 ? "s" : ""} de custódia · verificável por qualquer parte
          <Link href={`/verification`} className="ml-2 text-gold-400/70 hover:text-gold-300">
            Portal de verificação →
          </Link>
        </div>
      )}
    </div>
  );
}
