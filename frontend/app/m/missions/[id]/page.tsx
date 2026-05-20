"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useEffect, useState } from "react";
import {
  approveMission,
  fetchChainVerification,
  fetchMissionPlan,
  rejectMission,
} from "@/lib/api";
import { CameraCapture } from "@/components/mobile/CameraCapture";
import { MobileTimeline } from "@/components/mobile/MobileTimeline";
import { ShareSheet } from "@/components/mobile/ShareSheet";

export default function MobileMissionDetailPage() {
  const params = useParams();
  const id = typeof params?.id === "string" ? params.id : "";
  const [plan, setPlan] = useState<Record<string, unknown> | null>(null);
  const [chain, setChain] = useState<{ valid?: boolean } | null>(null);
  const [err, setErr] = useState("");

  useEffect(() => {
    if (!id) return;

    let c = false;
    (async () => {
      try {
        const p = (await fetchMissionPlan(id)) as Record<string, unknown>;
        if (!c) setPlan(p);
        const cv = (await fetchChainVerification(id)) as { valid?: boolean };
        if (!c) setChain(cv);
      } catch (e) {
        if (!c) setErr(e instanceof Error ? e.message : "Erro HDR.");
      }
    })();

    return () => {
      c = true;
    };
  }, [id]);

  const hdrIds = plan && Array.isArray((plan as { hdrs_generated?: string[] }).hdrs_generated)
    ? ((plan as { hdrs_generated: string[] }).hdrs_generated)
    : [];

  async function approve() {
    await approveMission(id);
    window.location.reload();
  }

  async function reject() {
    await rejectMission(id);
    window.location.href = "/m/missions";
  }

  return (
    <div className="px-5 pb-40">
      <div className="mb-10 flex justify-between gap-3">
        <Link prefetch={false} href="/m/missions" className="text-xs text-gold-400">
          ‹ Voltar
        </Link>
        <Link prefetch={false} href={`/m/approve/${id}`} className="text-xs text-emerald-200">
          Gestos rápidos
        </Link>
      </div>
      <h1 className="font-mono text-sm text-white/85">{id}</h1>
      <p className="mt-3 text-xs text-white/45">
        Estado:&nbsp;<span className="text-gold-200">{String(plan?.status ?? "…")}</span>
      </p>
      {err ? <p className="mt-4 text-xs text-rose-300">{err}</p> : null}

      <div className="mt-12">
        <MobileTimeline hdrIds={hdrIds} chainValid={chain?.valid ?? null} />
      </div>

      <ShareSheet missionId={id} />

      <CameraCapture missionId={id} />

      {plan?.status === "pending" ? (
        <div className="mt-14 grid gap-4">
          <button type="button" className="btn-glass min-h-[52px]" onClick={() => approve()}>
            Aprovar (fallback botão)
          </button>
          <button type="button" className="rounded-2xl border border-rose-500/35 py-5 text-xs text-rose-200" onClick={() => reject()}>
            Rejeitar
          </button>
        </div>
      ) : null}

      <Link href={`/missions/${id}`} className="mt-12 inline-block text-[11px] text-white/30 underline decoration-dashed">
        Ver modo desktop ›
      </Link>
    </div>
  );
}
