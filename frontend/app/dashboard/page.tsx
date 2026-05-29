"use client";

import dynamic from "next/dynamic";
import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { motion } from "framer-motion";

import { useAuth } from "@/lib/auth-context";
import {
  getDiaryStats,
  listMissions,
  fetchMyQuota,
  quotaUsagePct,
  type QuotaSnapshot,
} from "@/lib/api";

const TIER_LABELS: Record<QuotaSnapshot["tier"], string> = {
  free: "Grátis",
  pro: "Pro",
  team: "Team",
  enterprise: "Enterprise",
};

const DashboardCharts = dynamic(() => import("./DashboardCharts"), {
  ssr: false,
  loading: () => (
    <div className="mb-10 grid gap-6 lg:grid-cols-2">
      {[0, 1].map((i) => (
        <div key={i} className="glass-elite h-72 animate-pulse rounded-2xl border border-white/10" />
      ))}
    </div>
  ),
});

interface MissionRow {
  mission_id?: string;
  status?: string;
  description?: string;
}

interface DiaryStats {
  total_missions?: number;
  completed?: number;
  failed?: number;
  blocked_by_normative?: number;
  total_hdrs_generated?: number;
  avg_execution_time_ms?: number;
  most_used_agents?: { agent_id: string; count: number }[];
}


export default function DashboardPage() {
  const router = useRouter();
  const { isAuthenticated, user, logout, isReady } = useAuth();
  const [missions, setMissions] = useState<MissionRow[]>([]);
  const [stats, setStats] = useState<DiaryStats | null>(null);
  const [quota, setQuota] = useState<QuotaSnapshot | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [showOnboarding, setShowOnboarding] = useState(false);

  useEffect(() => {
    if (!isReady) return;
    if (!isAuthenticated) {
      router.replace("/login");
    }
  }, [isReady, isAuthenticated, router]);

  useEffect(() => {
    if (!isReady || !isAuthenticated) return;

    let cancelled = false;
    (async () => {
      setLoading(true);
      setError("");
      try {
        const [mRaw, sRaw, qRaw] = await Promise.all([
          listMissions(0, 8) as Promise<unknown>,
          getDiaryStats() as Promise<unknown>,
          fetchMyQuota().catch(() => null),
        ]);
        if (cancelled) return;
        setMissions(Array.isArray(mRaw) ? (mRaw as MissionRow[]) : []);
        setStats(typeof sRaw === "object" && sRaw !== null ? (sRaw as DiaryStats) : null);
        setQuota(qRaw);
      } catch (e) {
        if (!cancelled) setError(e instanceof Error ? e.message : "Falha ao carregar dados.");
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();

    return () => {
      cancelled = true;
    };
  }, [isAuthenticated, isReady]);

  // Nudge de onboarding: mostra quando o operador ainda não concluiu os 3 passos.
  useEffect(() => {
    if (!isReady || !isAuthenticated) return;
    try {
      setShowOnboarding(!localStorage.getItem("heillon_onboarding_complete"));
    } catch {
      /* ignore */
    }
  }, [isReady, isAuthenticated]);

  const total = stats?.total_missions ?? missions.length;

  const quotaPct = quota ? quotaUsagePct(quota) : null;

  const lifecycleData = useMemo(() => {
    if (!stats) return [];
    return [
      { name: "Concluídas", v: stats.completed ?? 0 },
      { name: "Falhas", v: stats.failed ?? 0 },
      { name: "Bloqueio normativo", v: stats.blocked_by_normative ?? 0 },
    ];
  }, [stats]);

  const agentPieData = useMemo(() => {
    const rows = stats?.most_used_agents ?? [];
    return rows
      .filter((r) => r.count > 0)
      .map((r) => ({ name: r.agent_id.replace(/-agent$/, "") || r.agent_id, value: r.count }));
  }, [stats]);

  const complianceRate = useMemo(() => {
    const c = stats?.completed ?? 0;
    const f = stats?.failed ?? 0;
    const b = stats?.blocked_by_normative ?? 0;
    const denom = c + f + b;
    if (denom === 0) return null;
    return Math.round((c / denom) * 1000) / 10;
  }, [stats]);

  if (!isReady || !isAuthenticated) {
    return (
      <div className="flex min-h-[40vh] items-center justify-center pt-24 text-white/50">
        <span className="inline-flex items-center gap-2">
          <span className="h-5 w-5 animate-spin rounded-full border-2 border-gold-500 border-t-transparent" />
          {!isReady ? "A preparar sessão…" : "A redirecionar…"}
        </span>
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-5xl px-4 pb-20 pt-24">
      <motion.div initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.45 }}>
        <div className="mb-10 flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
          <div>
            <p className="text-xs font-semibold uppercase tracking-[0.25em] text-gold-500/80">Painel</p>
            <h1 className="mt-1 text-3xl font-bold text-white md:text-4xl">Olá, {user?.name || "operador"}</h1>
            <p className="mt-1 text-sm text-white/45">{user?.email}</p>
          </div>
          <button
            type="button"
            onClick={() => {
              void logout();
              router.push("/");
            }}
            className="btn-glass self-start text-sm"
          >
            Sair
          </button>
        </div>

        {error ? (
          <div className="mb-6 rounded-xl border border-amber-500/30 bg-amber-500/10 px-4 py-3 text-sm text-amber-100">
            {error}{" "}
            <span className="text-white/60">(confirme que está autenticado e que a API expõe /mission/.)</span>
          </div>
        ) : null}

        {showOnboarding ? (
          <div className="mb-6 flex flex-col gap-3 rounded-2xl border border-gold-400/30 bg-gold-400/[0.06] px-5 py-4 sm:flex-row sm:items-center sm:justify-between">
            <div>
              <p className="text-sm font-medium text-gold-100">Configure seu Heillon em 3 passos</p>
              <p className="mt-0.5 text-xs text-white/55">
                Gere sua chave de API e conecte um coletor para registrar seu primeiro HDR.
              </p>
            </div>
            <div className="flex shrink-0 gap-2">
              <Link href="/conta/onboarding" className="btn-gold text-sm">
                Começar
              </Link>
              <button
                type="button"
                onClick={() => {
                  try {
                    localStorage.setItem("heillon_onboarding_complete", new Date().toISOString());
                  } catch {
                    /* ignore */
                  }
                  setShowOnboarding(false);
                }}
                className="btn-glass text-sm"
              >
                Dispensar
              </button>
            </div>
          </div>
        ) : null}

        {quota ? (
          <div className="mb-6 rounded-2xl border border-white/10 bg-white/[0.02] px-5 py-4">
            <div className="flex flex-wrap items-center justify-between gap-2">
              <div className="flex items-center gap-2">
                <span className="text-[11px] uppercase tracking-wider text-white/40">Quota mensal</span>
                <span className="rounded-full border border-gold-400/40 bg-gold-400/10 px-2 py-0.5 text-[10px] font-semibold text-gold-200">
                  {TIER_LABELS[quota.tier]}
                </span>
              </div>
              <span className="text-xs text-white/60">
                {quota.monthly_hdr_limit === null
                  ? `${quota.used_in_period} HDRs · ilimitado`
                  : `${quota.used_in_period} / ${quota.monthly_hdr_limit} HDRs`}
              </span>
            </div>
            {quotaPct !== null ? (
              <div className="mt-3 h-2 w-full overflow-hidden rounded-full bg-white/10">
                <div
                  className={`h-full rounded-full transition-all ${
                    quota.is_exceeded || quotaPct >= 1
                      ? "bg-rose-400"
                      : quotaPct >= 0.8
                        ? "bg-amber-400"
                        : "bg-gold-400"
                  }`}
                  style={{ width: `${Math.min(quotaPct * 100, 100)}%` }}
                />
              </div>
            ) : null}
            {quota.is_exceeded ? (
              <p className="mt-2 text-xs text-rose-300">
                Limite atingido. Novos HDRs podem ser bloqueados até o próximo período.{" "}
                <Link href="/conta/quota" className="underline hover:text-rose-200">
                  Ver detalhes
                </Link>
              </p>
            ) : quotaPct !== null && quotaPct >= 0.8 ? (
              <p className="mt-2 text-xs text-amber-200/90">
                Você já usou {Math.round(quotaPct * 100)}% da sua quota mensal.
              </p>
            ) : null}
          </div>
        ) : null}

        <div className="mb-10 grid gap-4 sm:grid-cols-3">
          {[
            { label: "Análises realizadas", value: loading ? "…" : String(total), hint: "Total no período" },
            { label: "Taxa de aprovação", value: loading ? "…" : complianceRate !== null ? `${complianceRate}%` : "—", hint: "concluídas / (concl.+falhas+bloqueadas)" },
            { label: "Tempo médio de análise", value: loading ? "…" : `${Math.round(stats?.avg_execution_time_ms ?? 0)} ms`, hint: "por análise completa" },
          ].map((card) => (
            <div key={card.label} className="glass-elite rounded-2xl p-5">
              <p className="text-[11px] uppercase tracking-wider text-white/40">{card.label}</p>
              <p className="mt-2 text-2xl font-semibold text-white">{card.value}</p>
              <p className="mt-1 text-xs text-white/35">{card.hint}</p>
            </div>
          ))}
        </div>

        {!loading && stats ? (
          <DashboardCharts lifecycleData={lifecycleData} agentPieData={agentPieData} />
        ) : null}

        <div className="glass-elite rounded-2xl p-6 md:p-8">
          <div className="mb-6 flex flex-wrap items-center justify-between gap-3">
            <h2 className="text-lg font-semibold text-white">Missões recentes</h2>
            <Link href="/diary" className="text-sm text-gold-400 transition-colors hover:text-gold-300">
              Ver diário →
            </Link>
          </div>

          {loading ? (
            <div className="flex justify-center py-16 text-white/45">
              <span className="inline-flex items-center gap-2">
                <span className="h-5 w-5 animate-spin rounded-full border-2 border-gold-500 border-t-transparent" />
                A carregar…
              </span>
            </div>
          ) : missions.length === 0 ? (
            <div className="rounded-xl border border-dashed border-white/15 bg-white/[0.02] py-14 text-center">
              <p className="text-white/50">Ainda não há missões listadas.</p>
              <Link href="/" className="mt-4 inline-block text-sm text-gold-400 hover:text-gold-300">
                Planear uma missão
              </Link>
            </div>
          ) : (
            <ul className="space-y-2">
              {missions.map((m) => (
                <li key={m.mission_id ?? Math.random()}>
                  <Link
                    href={m.mission_id ? `/missions/${m.mission_id}` : "#"}
                    className="glass-card-hover flex items-center justify-between rounded-xl border border-white/5 px-4 py-3"
                  >
                    <span className="font-mono text-xs text-gold-200/90">{m.mission_id ?? "—"}</span>
                    <span className="text-xs uppercase tracking-wide text-white/40">{m.status ?? ""}</span>
                  </Link>
                </li>
              ))}
            </ul>
          )}
        </div>

        <div className="mt-8 flex flex-wrap gap-3">
          <Link href="/ingestion" className="btn-gold text-sm">
            Nova evidência
          </Link>
          <Link href="/verification" className="btn-glass text-sm">
            Portal de verificação
          </Link>
          <Link href="/agent-config" className="btn-glass text-sm">
            Soberania de modelos
          </Link>
          <Link href="/normative" className="btn-glass text-sm">
            Hub normativo
          </Link>
        </div>
      </motion.div>
    </div>
  );
}
