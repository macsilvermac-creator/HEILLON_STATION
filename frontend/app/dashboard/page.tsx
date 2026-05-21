"use client";

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { motion } from "framer-motion";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Legend,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import { useAuth } from "@/lib/auth-context";
import { getDiaryStats, listMissions } from "@/lib/api";

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

const PIE_COLORS = ["#d4af37", "#34d399", "#60a5fa", "#f472b6", "#a78bfa", "#fb923c", "#94a3b8"];

export default function DashboardPage() {
  const router = useRouter();
  const { isAuthenticated, user, logout, isReady } = useAuth();
  const [missions, setMissions] = useState<MissionRow[]>([]);
  const [stats, setStats] = useState<DiaryStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

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
        const [mRaw, sRaw] = await Promise.all([
          listMissions(0, 8) as Promise<unknown>,
          getDiaryStats() as Promise<unknown>,
        ]);
        if (cancelled) return;
        setMissions(Array.isArray(mRaw) ? (mRaw as MissionRow[]) : []);
        setStats(typeof sRaw === "object" && sRaw !== null ? (sRaw as DiaryStats) : null);
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

  const total = stats?.total_missions ?? missions.length;

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

        <div className="mb-10 grid gap-4 sm:grid-cols-3">
          {[
            { label: "Missões (átomo)", value: loading ? "…" : String(total), hint: "Diário / org" },
            { label: "Taxa conformidade*", value: loading ? "…" : complianceRate !== null ? `${complianceRate}%` : "—", hint: "concluídas / (concl.+falhas+bloq.)" },
            { label: "Tempo médio (DAG)", value: loading ? "…" : `${Math.round(stats?.avg_execution_time_ms ?? 0)} ms`, hint: "orquestração EASY" },
          ].map((card) => (
            <div key={card.label} className="glass-elite rounded-2xl p-5">
              <p className="text-[11px] uppercase tracking-wider text-white/40">{card.label}</p>
              <p className="mt-2 text-2xl font-semibold text-white">{card.value}</p>
              <p className="mt-1 text-xs text-white/35">{card.hint}</p>
            </div>
          ))}
        </div>

        {!loading && stats ? (
          <div className="mb-10 grid gap-6 lg:grid-cols-2">
            <div className="glass-elite rounded-2xl border border-white/10 p-5">
              <h3 className="text-sm font-semibold text-white">Ciclo de vida (missões)</h3>
              <p className="mt-1 text-[11px] text-white/40">Distribuição agregada do diário.</p>
              <div className="mt-4 h-56 w-full">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={lifecycleData} margin={{ top: 8, right: 8, left: 0, bottom: 0 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.08)" />
                    <XAxis dataKey="name" tick={{ fill: "rgba(255,255,255,0.45)", fontSize: 11 }} />
                    <YAxis tick={{ fill: "rgba(255,255,255,0.35)", fontSize: 10 }} allowDecimals={false} />
                    <Tooltip
                      contentStyle={{
                        background: "rgba(15,23,42,0.95)",
                        border: "1px solid rgba(255,255,255,0.12)",
                        borderRadius: "12px",
                        fontSize: "12px",
                      }}
                    />
                    <Bar dataKey="v" fill="#d4af37" radius={[6, 6, 0, 0]} name="Missões" />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </div>

            <div className="glass-elite rounded-2xl border border-white/10 p-5">
              <h3 className="text-sm font-semibold text-white">Agentes EASY (uso)</h3>
              <p className="mt-1 text-[11px] text-white/40">Frequência relativa no período agregado.</p>
              <div className="mt-4 h-56 w-full">
                {agentPieData.length ? (
                  <ResponsiveContainer width="100%" height="100%">
                    <PieChart>
                      <Pie data={agentPieData} dataKey="value" nameKey="name" cx="50%" cy="50%" outerRadius={72} label>
                        {agentPieData.map((_, i) => (
                          <Cell key={i} fill={PIE_COLORS[i % PIE_COLORS.length]} stroke="rgba(0,0,0,0.2)" />
                        ))}
                      </Pie>
                      <Tooltip
                        contentStyle={{
                          background: "rgba(15,23,42,0.95)",
                          border: "1px solid rgba(255,255,255,0.12)",
                          borderRadius: "12px",
                          fontSize: "12px",
                        }}
                      />
                      <Legend wrapperStyle={{ fontSize: "11px", color: "rgba(255,255,255,0.55)" }} />
                    </PieChart>
                  </ResponsiveContainer>
                ) : (
                  <div className="flex h-full items-center justify-center text-xs text-white/40">
                    Sem frequências de agente — execute missões para povoar.
                  </div>
                )}
              </div>
            </div>
          </div>
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
