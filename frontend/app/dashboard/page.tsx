"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { motion } from "framer-motion";
import { useAuth } from "@/lib/auth-context";
import { getDiaryStats, listMissions } from "@/lib/api";

interface MissionRow {
  mission_id?: string;
  status?: string;
  description?: string;
}

export default function DashboardPage() {
  const router = useRouter();
  const { isAuthenticated, user, logout, isReady } = useAuth();
  const [missions, setMissions] = useState<MissionRow[]>([]);
  const [stats, setStats] = useState<{ total_missions?: number } | null>(null);
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
        setStats(typeof sRaw === "object" && sRaw !== null ? (sRaw as { total_missions?: number }) : null);
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

  const total = stats?.total_missions ?? missions.length;

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
              logout();
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
            { label: "Papel", value: user?.role ?? "—", hint: "perfil" },
            { label: "Estado", value: "Ativo", hint: "sessão JWT" },
          ].map((card) => (
            <div key={card.label} className="glass-elite rounded-2xl p-5">
              <p className="text-[11px] uppercase tracking-wider text-white/40">{card.label}</p>
              <p className="mt-2 text-2xl font-semibold text-white">{card.value}</p>
              <p className="mt-1 text-xs text-white/35">{card.hint}</p>
            </div>
          ))}
        </div>

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
        </div>
      </motion.div>
    </div>
  );
}
