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
  fetchFeedbackSummary,
  type BetaMetrics,
  type BetaFeedEvent,
  type FeedbackSummary,
} from "@/lib/api";

const TOKEN_KEY = "heillon_admin_token";

const ADOPT_LABELS: Record<string, string> = {
  now: "Sim, em até 30 dias",
  "3-6m": "Sim, em 3–6 meses",
  "12m": "Sim, em 12+ meses",
  depends: "Depende de ajustes",
  no: "Não adotaria",
};

function StatCard({ label, value, hint }: { label: string; value: string | number; hint?: string }) {
  return (
    <div className="rounded-xl border border-white/10 bg-white/5 p-4">
      <p className="text-xs uppercase tracking-wide text-white/50">{label}</p>
      <p className="mt-1 text-2xl font-semibold text-gold-200">{value}</p>
      {hint ? <p className="mt-1 text-xs text-white/40">{hint}</p> : null}
    </div>
  );
}

/** Minimal SVG bar sparkline for daily HDR volume (last 14d). */
function Sparkline({ data }: { data: Array<{ date: string; count: number }> }) {
  if (data.length === 0) {
    return <p className="text-xs text-white/40">Sem HDRs nos últimos 14 dias.</p>;
  }
  const max = Math.max(1, ...data.map((d) => d.count));
  return (
    <div className="flex h-24 items-end gap-1">
      {data.map((d) => (
        <div key={d.date} className="flex flex-1 flex-col items-center gap-1" title={`${d.date}: ${d.count}`}>
          <div className="flex w-full items-end justify-center" style={{ height: "100%" }}>
            <div
              className="w-full rounded-sm bg-gold-400/70"
              style={{ height: `${Math.max(4, (d.count / max) * 100)}%` }}
            />
          </div>
          <span className="text-[9px] text-white/30">{d.date.slice(5)}</span>
        </div>
      ))}
    </div>
  );
}

function avg(v: number | null): string {
  return v === null ? "—" : v.toFixed(1);
}

/** Activation funnel bar — each stage as a proportion of organizations. */
function FunnelRow({ label, value, total }: { label: string; value: number; total: number }) {
  const pct = total > 0 ? Math.round((value / total) * 100) : 0;
  return (
    <div>
      <div className="mb-1 flex justify-between text-xs text-white/70">
        <span>{label}</span>
        <span className="text-gold-200">
          {value} <span className="text-white/40">({pct}%)</span>
        </span>
      </div>
      <div className="h-2 overflow-hidden rounded-full bg-white/10">
        <div className="h-full rounded-full bg-gold-400/70" style={{ width: `${pct}%` }} />
      </div>
    </div>
  );
}

export default function AdminPage() {
  const [token, setToken] = useState("");
  const [metrics, setMetrics] = useState<BetaMetrics | null>(null);
  const [feed, setFeed] = useState<BetaFeedEvent[]>([]);
  const [feedback, setFeedback] = useState<FeedbackSummary | null>(null);
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
      const [m, f, fb] = await Promise.all([
        fetchBetaMetrics(t.trim()),
        fetchBetaFeed(t.trim(), 20),
        fetchFeedbackSummary(t.trim()),
      ]);
      setMetrics(m);
      setFeed(f.events);
      setFeedback(fb);
      try {
        sessionStorage.setItem(TOKEN_KEY, t.trim());
      } catch {
        /* ignore */
      }
    } catch (e) {
      setMetrics(null);
      setFeed([]);
      setFeedback(null);
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

          <section className="mb-8 grid gap-3 lg:grid-cols-2">
            <div className="rounded-xl border border-white/10 bg-white/5 p-4">
              <p className="mb-3 text-xs uppercase tracking-wide text-white/50">
                HDRs por dia (14d)
              </p>
              <Sparkline data={metrics.daily_hdrs} />
            </div>
            <div className="rounded-xl border border-white/10 bg-white/5 p-4">
              <p className="mb-3 text-xs uppercase tracking-wide text-white/50">
                Funil de ativação
              </p>
              <div className="space-y-3">
                <FunnelRow
                  label="Organizações"
                  value={metrics.funnel.organizations}
                  total={metrics.funnel.organizations}
                />
                <FunnelRow
                  label="Com API key"
                  value={metrics.funnel.with_api_key}
                  total={metrics.funnel.organizations}
                />
                <FunnelRow
                  label="Com ≥1 HDR"
                  value={metrics.funnel.with_hdr}
                  total={metrics.funnel.organizations}
                />
                <FunnelRow
                  label="Ativas (7d)"
                  value={metrics.funnel.active_7d}
                  total={metrics.funnel.organizations}
                />
              </div>
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

      {feedback ? (
        <section className="mt-10 border-t border-white/10 pt-8">
          <header className="mb-4">
            <h2 className="text-lg font-semibold text-white">Opinião do beta</h2>
            <p className="mt-1 text-xs text-white/50">
              {feedback.response_count} resposta(s) · agregado de-identificado, sem
              identidade de usuário ou organização.
            </p>
          </header>

          <div className="mb-6 grid grid-cols-2 gap-3 sm:grid-cols-5">
            <StatCard label="Usabilidade" value={avg(feedback.averages.usability)} hint="média 0–10" />
            <StatCard label="Experiência" value={avg(feedback.averages.experience)} hint="média 0–10" />
            <StatCard label="Funcionalidades" value={avg(feedback.averages.functionality)} hint="média 0–10" />
            <StatCard label="Entrega" value={avg(feedback.averages.delivers)} hint="média 0–10" />
            <StatCard
              label="NPS"
              value={feedback.nps.score === null ? "—" : feedback.nps.score}
              hint={`${feedback.nps.promoters}P · ${feedback.nps.passives}N · ${feedback.nps.detractors}D`}
            />
          </div>

          <div className="mb-6 grid gap-3 sm:grid-cols-2">
            <div className="rounded-xl border border-white/10 bg-white/5 p-4">
              <p className="mb-2 text-xs uppercase tracking-wide text-white/50">
                Adotaria na organização
              </p>
              {Object.keys(feedback.adopt_breakdown).length === 0 ? (
                <p className="text-xs text-white/40">Sem respostas ainda.</p>
              ) : (
                <ul className="space-y-1 text-sm text-white/80">
                  {Object.entries(feedback.adopt_breakdown).map(([k, n]) => (
                    <li key={k} className="flex justify-between">
                      <span>{ADOPT_LABELS[k] ?? k}</span>
                      <span className="text-gold-200">{n}</span>
                    </li>
                  ))}
                </ul>
              )}
            </div>
            <div className="rounded-xl border border-white/10 bg-white/5 p-4">
              <p className="mb-2 text-xs uppercase tracking-wide text-white/50">
                Querem contato do time
              </p>
              <p className="text-2xl font-semibold text-gold-200">
                {feedback.contact_optins}
              </p>
              <p className="mt-1 text-xs text-white/40">
                opt-ins para conversar sobre o beta
              </p>
            </div>
          </div>

          <p className="mb-2 text-xs uppercase tracking-wide text-white/50">
            Comentários recentes (de-identificados)
          </p>
          <div className="space-y-3">
            {feedback.recent_comments.length === 0 ? (
              <p className="text-xs text-white/40">Nenhum comentário ainda.</p>
            ) : (
              feedback.recent_comments.map((c, i) => (
                <div key={`${c.created_at}-${i}`} className="rounded-xl border border-white/10 bg-white/5 p-4 text-sm">
                  <p className="mb-2 font-mono text-[11px] text-white/35">{c.created_at}</p>
                  {c.most_valuable ? (
                    <p className="mb-1 text-white/80">
                      <span className="text-gold-300/80">Valor: </span>
                      {c.most_valuable}
                    </p>
                  ) : null}
                  {c.frictions ? (
                    <p className="mb-1 text-white/80">
                      <span className="text-rose-300/80">Fricção: </span>
                      {c.frictions}
                    </p>
                  ) : null}
                  {c.improvements ? (
                    <p className="text-white/80">
                      <span className="text-sky-300/80">Melhoria: </span>
                      {c.improvements}
                    </p>
                  ) : null}
                </div>
              ))
            )}
          </div>
        </section>
      ) : null}
    </main>
  );
}
