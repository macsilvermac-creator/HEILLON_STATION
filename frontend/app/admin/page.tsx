"use client";

/**
 * /admin — Painel de métricas do beta (Fase 30B3).
 *
 * Consome /api/v1/admin/beta-metrics e /beta-feed. Autenticação por token
 * compartilhado (X-Heillon-Admin-Token) que o operador cola e fica em
 * sessionStorage (não persiste entre sessões do navegador). O operador também
 * precisa estar logado (cookie de sessão) — defesa em profundidade.
 *
 * NÃO expõe prompts/respostas/PII — apenas contagens agregadas.
 */

import { useCallback, useEffect, useState } from "react";

import {
  fetchBetaMetrics,
  fetchBetaFeed,
  type BetaMetrics,
  type BetaFeedEvent,
} from "@/lib/api";

const TOKEN_KEY = "heillon_admin_token";

function StatCard({ label, value, hint }: { label: string; value: string | number; hint?: string }) {
  return (
    <div className="rounded-xl border border-white/10 bg-white/5 p-4">
      <p className="text-xs uppercase tracking-wide text-white/50">{label}</p>
      <p className="mt-1 text-2xl font-semibold text-gold-200">{value}</p>
      {hint ? <p className="mt-1 text-xs text-white/40">{hint}</p> : null}
    </div>
  );
}

export default function AdminPage() {
  const [token, setToken] = useState("");
  const [metrics, setMetrics] = useState<BetaMetrics | null>(null);
  const [feed, setFeed] = useState<BetaFeedEvent[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    try {
      const saved = sessionStorage.getItem(TOKEN_KEY);
      if (saved) setToken(saved);
    } catch {
      /* ignore */
    }
  }, []);

  const load = useCallback(async (t: string) => {
    if (!t.trim()) {
      setError("Informe o token de administrador.");
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const [m, f] = await Promise.all([
        fetchBetaMetrics(t.trim()),
        fetchBetaFeed(t.trim(), 20),
      ]);
      setMetrics(m);
      setFeed(f.events);
      try {
        sessionStorage.setItem(TOKEN_KEY, t.trim());
      } catch {
        /* ignore */
      }
    } catch (e) {
      setMetrics(null);
      setFeed([]);
      setError(e instanceof Error ? e.message : "Falha ao carregar métricas.");
    } finally {
      setLoading(false);
    }
  }, []);

  return (
    <main className="mx-auto max-w-5xl px-4 py-10">
      <header className="mb-6">
        <h1 className="text-2xl font-semibold text-white">Painel do Beta</h1>
        <p className="mt-1 text-sm text-white/50">
          Métricas agregadas de adesão. Sem prompts, respostas ou dados pessoais.
        </p>
      </header>

      <form
        onSubmit={(e) => {
          e.preventDefault();
          void load(token);
        }}
        className="mb-8 flex flex-col gap-2 sm:flex-row"
      >
        <input
          type="password"
          value={token}
          onChange={(e) => setToken(e.target.value)}
          placeholder="X-Heillon-Admin-Token"
          aria-label="Token de administrador"
          className="flex-1 rounded-md border border-white/15 bg-deep-space-900 px-3 py-2 text-sm text-white placeholder:text-white/30 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-gold-400/60"
        />
        <button
          type="submit"
          disabled={loading}
          className="rounded-md border border-gold-400/50 bg-gold-400/15 px-5 py-2 text-sm font-medium text-gold-100 transition hover:bg-gold-400/25 disabled:opacity-50"
        >
          {loading ? "Carregando…" : "Carregar"}
        </button>
      </form>

      {error ? (
        <div
          role="alert"
          className="mb-6 rounded-md border border-rose-500/30 bg-rose-500/10 px-4 py-3 text-sm text-rose-200"
        >
          {error}
        </div>
      ) : null}

      {metrics ? (
        <>
          <section className="mb-8 grid grid-cols-2 gap-3 sm:grid-cols-4">
            <StatCard label="Organizações" value={metrics.organizations.total} />
            <StatCard
              label="Usuários"
              value={metrics.users.total}
              hint={`${metrics.users.active_last_7d} ativos (7d)`}
            />
            <StatCard
              label="API keys ativas"
              value={metrics.api_keys.active}
              hint={`${metrics.api_keys.revoked} revogadas`}
            />
            <StatCard
              label="HDRs"
              value={metrics.hdrs.total}
              hint={`${metrics.hdrs.last_24h} em 24h · ${metrics.hdrs.last_7d} em 7d`}
            />
          </section>

          <section className="mb-8 grid gap-3 sm:grid-cols-2">
            <div className="rounded-xl border border-white/10 bg-white/5 p-4">
              <p className="mb-2 text-xs uppercase tracking-wide text-white/50">
                Por tier
              </p>
              <ul className="space-y-1 text-sm text-white/80">
                {Object.entries(metrics.organizations.by_tier).map(([tier, n]) => (
                  <li key={tier} className="flex justify-between">
                    <span className="capitalize">{tier}</span>
                    <span className="text-gold-200">{n}</span>
                  </li>
                ))}
              </ul>
            </div>
            <div className="rounded-xl border border-white/10 bg-white/5 p-4">
              <p className="mb-2 text-xs uppercase tracking-wide text-white/50">
                HDRs por tipo
              </p>
              <ul className="space-y-1 text-sm text-white/80">
                {Object.entries(metrics.hdrs.by_type).map(([t, n]) => (
                  <li key={t} className="flex justify-between">
                    <span>{t}</span>
                    <span className="text-gold-200">{n}</span>
                  </li>
                ))}
              </ul>
            </div>
          </section>

          <section>
            <p className="mb-2 text-xs uppercase tracking-wide text-white/50">
              Atividade recente (sanitizada)
            </p>
            <div className="overflow-hidden rounded-xl border border-white/10">
              <table className="w-full text-left text-xs">
                <thead className="bg-white/5 text-white/50">
                  <tr>
                    <th className="px-3 py-2">Quando</th>
                    <th className="px-3 py-2">Tipo</th>
                    <th className="px-3 py-2">Missão</th>
                    <th className="px-3 py-2">Org</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-white/5 text-white/75">
                  {feed.map((ev) => (
                    <tr key={ev.hdr_id}>
                      <td className="px-3 py-2 font-mono">{ev.created_at}</td>
                      <td className="px-3 py-2">{ev.hdr_type}</td>
                      <td className="px-3 py-2 font-mono">{ev.mission_id}</td>
                      <td className="px-3 py-2 font-mono">{ev.organization_id}</td>
                    </tr>
                  ))}
                  {feed.length === 0 ? (
                    <tr>
                      <td colSpan={4} className="px-3 py-4 text-center text-white/40">
                        Nenhum evento ainda.
                      </td>
                    </tr>
                  ) : null}
                </tbody>
              </table>
            </div>
            <p className="mt-4 text-xs text-white/40">
              Snapshot: {metrics.snapshot_at}
            </p>
          </section>
        </>
      ) : null}
    </main>
  );
}
