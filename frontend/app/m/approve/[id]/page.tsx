"use client";

import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { approveMission, fetchMissionPlan, rejectMission } from "@/lib/api";
import { SwipeApproval } from "@/components/mobile/SwipeApproval";

export default function MobileApproveMissionPage() {
  const router = useRouter();
  const params = useParams();
  const id = typeof params?.id === "string" ? params.id : "";

  const [plan, setPlan] = useState<Record<string, unknown> | null>(null);
  const [err, setErr] = useState("");

  useEffect(() => {
    if (!id) return;
    let c = false;
    fetchMissionPlan(id)
      .then((p) => {
        if (!c) setPlan(p as Record<string, unknown>);
      })
      .catch((e) => {
        if (!c) setErr(e instanceof Error ? e.message : "Erro ao carregar missão.");
      });
    return () => {
      c = true;
    };
  }, [id]);

  if (!id) return null;

  return (
    <div className="px-6 pt-12">
      <Link href={`/m/missions/${id}`} className="text-xs text-white/35">
        ← Detalhes
      </Link>
      <h1 className="mt-6 text-lg font-semibold text-white">Aprovação táctil</h1>
      <p className="mt-4 text-[11px] leading-relaxed text-white/55">
        {typeof plan?.description === "string" ? plan.description : "A carregar resumo EASY…"}
      </p>

      <div className="mt-10 rounded-xl border border-white/10 bg-white/[0.02] p-6 text-[11px] text-white/50">
        <p>
          Custódia EASY — qualquer decisão será gravada irreversivamente no dossier assim que o backend confirmar permissões
          normativas.
        </p>
      </div>

      {err ? <p className="mt-6 text-xs text-rose-300">{err}</p> : null}

      <SwipeApproval
        onApprove={async () => {
          await approveMission(id);
          router.push(`/m/missions/${id}`);
        }}
        onReject={async () => {
          await rejectMission(id);
          router.push("/m/missions");
        }}
      />
    </div>
  );
}
