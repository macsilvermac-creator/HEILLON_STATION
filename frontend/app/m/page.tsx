"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import {
  approveMission,
  executeMission,
  fetchMobilePendingApprovals,
  fetchMobileQuickStats,
  listMissions,
} from "@/lib/api";
import { useAuth } from "@/lib/auth-context";

interface MissionBrief {
  mission_id?: string;
  status?: string;
  description?: string;
}

interface PendingEnvelope {
  total?: number;
  missions?: MissionBrief[];
}

export default function MobileHomePage() {
  const { user, isReady, isAuthenticated } = useAuth();
  const [stats, setStats] = useState<{ pending_approvals: number; total_missions: number } | null>(null);
  const [pendingPreview, setPendingPreview] = useState<MissionBrief[]>([]);
  const [recent, setRecent] = useState<MissionBrief[]>([]);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!isReady || !isAuthenticated) {
      setLoading(false);
      return;
    }

    let cancel = false;
    (async () => {
      setLoading(true);
      setError("");
      try {
        const [sRaw, pendRaw, mRaw] = await Promise.all([
          fetchMobileQuickStats() as Promise<Record<string, unknown>>,
          fetchMobilePendingApprovals() as Promise<PendingEnvelope>,
          listMissions(0, 5) as Promise<unknown>,
        ]);
        if (cancel) return;
        setStats({
          pending_approvals:
            typeof sRaw.pending_approvals === "number"
              ? sRaw.pending_approvals
              : Number(sRaw.pending_approvals) || 0,
          total_missions:
            typeof sRaw.total_missions === "number" ? sRaw.total_missions : Number(sRaw.total_missions) || 0,
        });
        const p = Array.isArray(pendRaw?.missions) ? pendRaw!.missions!.slice(0, 4) : [];
        setPendingPreview(p);
        setRecent(Array.isArray(mRaw) ? (mRaw as MissionBrief[]) : []);
      } catch (err) {
        if (!cancel) setError(err instanceof Error ? err.message : "Falhou carregar cockpit.");
      } finally {
        if (!cancel) setLoading(false);
      }
    })();

    return () => {
      cancel = true;
    };
  }, [isReady, isAuthenticated]);

  return (
    <div className="px-5">
      {!isAuthenticated || !isReady ? (
        <div className="glass-elite mx-auto mt-10 max-w-md rounded-3xl px-8 py-12 text-center">
          <p className="text-sm text-white/55">Precisa iniciar sessão para filas EASY e estatísticas móveis.</p>
          <Link href="/login" className="btn-gold mt-8 inline-block min-h-[48px] px-10 py-4 text-sm font-semibold">
            Entrar
          </Link>
        </div>
      ) : null}

      {isAuthenticated && isReady ? (
        <>
          <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
            <h1 className="text-xl font-semibold text-white">
              Olá, <span className="text-gradient">{user?.name || "Operador"}</span>
            </h1>
            <p className="mt-1 text-xs uppercase tracking-[0.2em] text-white/40">Painel rápido PWA</p>
          </motion.div>

          {error ? <p className="mt-4 text-xs text-rose-300">{error}</p> : null}

          <div className="mt-8 grid grid-cols-2 gap-3">
            {[
              { label: "Pendentes", value: loading ? "…" : String(stats?.pending_approvals ?? "0") },
              { label: "Missões globais", value: loading ? "…" : String(stats?.total_missions ?? 0) },
            ].map((card) => (
              <div key={card.label} className="glass-elite rounded-2xl p-5">
                <p className="text-[11px] text-white/40">{card.label}</p>
                <p className="mt-2 text-2xl font-bold text-white">{card.value}</p>
              </div>
            ))}
          </div>

          <div className="mt-8 flex flex-wrap gap-2">
            <Link
              href="/m/docs"
              prefetch={false}
              className="btn-glass flex-1 min-h-[52px] py-4 text-center text-xs text-white/80"
            >
              Documentação
            </Link>
            <Link href="/m/verify" prefetch={false} className="btn-gold flex-1 min-h-[52px] text-center py-4 text-xs">
              Nova verificação HDR
            </Link>
            {pendingPreview[0]?.mission_id ? (
              <Link
                prefetch={false}
                href={`/m/approve/${pendingPreview[0].mission_id}`}
                className="btn-glass flex-1 min-h-[52px] py-4 text-center text-xs"
              >
                Aprovar pendente
              </Link>
            ) : (
              <span className="btn-glass flex-1 cursor-not-allowed py-4 text-center text-xs opacity-40">
                Sem pendentes
              </span>
            )}
          </div>

          <section className="mt-14">
            <div className="mb-5 flex items-center justify-between">
              <h2 className="text-sm font-semibold text-white/80">Aprovações abertas</h2>
              <Link prefetch={false} href="/m/missions" className="text-[11px] text-gold-400">
                Lista completa ↑
              </Link>
            </div>
            {pendingPreview.length ? (
              <ul className="space-y-2">
                {pendingPreview.map((m) =>
                  m.mission_id ? (
                    <li key={m.mission_id}>
                      <Link
                        href={`/m/approve/${m.mission_id}`}
                        prefetch={false}
                        className="glass-elite flex min-h-[54px] items-center justify-between rounded-2xl px-5 py-3"
                      >
                        <span className="font-mono text-[11px] text-gold-200/90">{m.mission_id}</span>
                        <span className="text-[11px] text-white/40">swipe ›</span>
                      </Link>
                    </li>
                  ) : null,
                )}
              </ul>
            ) : (
              <p className="text-xs text-white/35">Sem filas pendentes visíveis.</p>
            )}
          </section>

          <section className="mt-12">
            <h2 className="mb-4 text-sm font-semibold text-white/80">Recentes</h2>
            <ul className="space-y-2">
              {recent.map((m) =>
                m.mission_id ? (
                  <li key={m.mission_id}>
                    <Link prefetch={false} href={`/m/missions/${m.mission_id}`} className="glass-card block rounded-xl px-4 py-3">
                      <span className="font-mono text-[11px] text-white/70">{m.mission_id}</span>
                      <p className="mt-2 line-clamp-2 text-xs text-white/40">{m.description}</p>
                    </Link>
                  </li>
                ) : null,
              )}
              {!recent.length ? <li className="text-xs text-white/35">Ainda não há missões registadas aqui.</li> : null}
            </ul>
          </section>

          {/* Atalhos dev: aprovar+executar com um toque apenas em ambiente de demo */}
          {pendingPreview[0]?.mission_id ? (
            <div className="mt-10 rounded-2xl border border-dashed border-white/15 p-5 text-[11px] text-white/40">
              <p className="font-semibold text-white/65">Fluxo rápido (demo técnico)</p>
              <p className="mt-3">Opcionalmente aprova e lança DAG num único ciclo quando estiver só em testes privados.</p>
              <div className="mt-4 grid grid-cols-2 gap-2">
                <button
                  type="button"
                  className="rounded-xl bg-white/[0.04] px-3 py-3 text-emerald-200"
                  onClick={async () => {
                    try {
                      const id = pendingPreview[0]?.mission_id;
                      if (!id) return;
                      await approveMission(id);
                      await executeMission(id);
                      window.alert("DAG executado no backend.");
                      window.location.reload();
                    } catch (e) {
                      window.alert(e instanceof Error ? e.message : "erro");
                    }
                  }}
                >
                  Turbo (aprovar + executar)
                </button>
              </div>
            </div>
          ) : null}
        </>
      ) : null}
    </div>
  );
}
