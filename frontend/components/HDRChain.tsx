"use client";

import { useEffect, useState } from "react";
import Link from "next/link";

import { fetchChainVerification, fetchMissionPlan } from "@/lib/api";

interface HDRChainProps {
  missionId: string;
}

export function HDRChain({ missionId }: HDRChainProps) {
  const [mission, setMission] = useState<unknown>(null);
  const [verification, setVerification] = useState<unknown>(null);
  const [error, setError] = useState<string>("");

  useEffect(() => {
    let ignore = false;
    (async () => {
      try {
        const snapshot = await fetchMissionPlan(missionId);
        if (!ignore) {
          setMission(snapshot);
        }
        const verdict = await fetchChainVerification(missionId);
        if (!ignore) {
          setVerification(verdict);
        }
      } catch (err) {
        if (!ignore) {
          setError(err instanceof Error ? err.message : "Falhou leitura do ledger.");
        }
      }
    })();
    return () => {
      ignore = true;
    };
  }, [missionId]);

  const hdrs =
    typeof mission === "object" && mission !== null && Array.isArray((mission as { hdrs_generated?: unknown }).hdrs_generated)
      ? ((mission as { hdrs_generated?: string[] }).hdrs_generated ?? [])
      : [];

  return (
    <div className="space-y-4 rounded-xl border border-neutral-800 bg-neutral-900/60 p-4">
      <h2 className="text-sm font-semibold text-neutral-200">Corrente HDR</h2>

      <div className="rounded-lg border border-gold-500/25 bg-gold-500/10 p-3 text-[11px] text-gold-100/95">
        <span className="font-semibold">Âncora normativa:</span> pós-execução, os HDR desta missão são mapeados para
        artigos registados (ex.: LGPD-BR).
        <Link href="/normative" className="ml-2 text-gold-300 underline-offset-4 hover:underline">
          Hub normativo
        </Link>
      </div>

      {error ? <p className="text-xs text-rose-400">{error}</p> : null}
      <div className="space-y-2 text-xs">
        <div className="rounded-lg border border-neutral-900 bg-neutral-950 p-3 text-neutral-300">
          Verificação pública:&nbsp;
          <span className="font-semibold text-emerald-300">
            {verification && typeof verification === "object" && verification !== null && "valid" in verification
              ? String((verification as { valid?: boolean }).valid)
              : "…"}
          </span>
        </div>
        {hdrs.length ? (
          hdrs.map((hdrId: string, idx: number) => (
            <div
              key={hdrId}
              className="flex flex-col gap-1 rounded-lg border border-neutral-800 bg-neutral-950 p-3 text-xs text-neutral-400"
            >
              <span className="font-mono text-[11px] text-emerald-400">HDR #{idx + 1}</span>
              <span className="font-mono">{hdrId}</span>
            </div>
          ))
        ) : (
          <p className="text-neutral-500">Sem HDRs registados nesta missão (ainda).</p>
        )}
      </div>
    </div>
  );
}
