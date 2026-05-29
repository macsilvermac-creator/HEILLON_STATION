"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { fetchMyQuota, quotaUsagePct, type QuotaSnapshot } from "@/lib/api";

const EXTERNAL_PLANS_URL = process.env.NEXT_PUBLIC_PLANS_URL ?? "https://heillon.com/planos";

const TIER_META: Record<QuotaSnapshot["tier"], { name: string; description: string }> = {
  free: {
    name: "Free",
    description: "Plano gratuito — 50 HDRs por mês, retenção de 30 dias.",
  },
  pro: {
    name: "Pro",
    description: "Plano individual — HDRs ilimitados, retenção 1 ano, PDF/A-3 forense.",
  },
  team: {
    name: "Team",
    description: "Plano para escritórios — até 10 usuários, retenção 5 anos.",
  },
  enterprise: {
    name: "Enterprise",
    description: "Plano corporativo — sem limites, on-prem disponível, SLA com penalidades.",
  },
};

function formatDate(iso: string): string {
  try {
    return new Date(iso).toLocaleDateString("pt-BR", {
      day: "2-digit",
      month: "short",
      year: "numeric",
    });
  } catch {
    return iso;
  }
}

function daysUntil(iso: string): number {
  try {
    const ms = new Date(iso).getTime() - Date.now();
    return Math.max(Math.ceil(ms / (1000 * 60 * 60 * 24)), 0);
  } catch {
    return 0;
  }
}

export default function QuotaPage() {
  const [snap, setSnap] = useState<QuotaSnapshot | null>(null);
  const [err, setErr] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    fetchMyQuota()
      .then((q) => {
        if (!cancelled) {
          setSnap(q);
          setLoading(false);
        }
      })
      .catch((e) => {
        if (!cancelled) {
          setErr(e instanceof Error ? e.message : "Não foi possível carregar a quota.");
          setLoading(false);
        }
      });
    return () => {
      cancelled = true;
    };
  }, []);

  if (loading) {
    return (
      <section className="mx-auto max-w-5xl px-6 py-16">
        <p className="text-sm text-white/45" aria-live="polite">
          Carregando informações da conta…
        </p>
      </section>
    );
  }

  if (err || !snap) {
    return (
      <section className="mx-auto max-w-5xl px-6 py-16">
        <div role="alert" className="rounded-xl border border-rose-500/40 bg-rose-500/10 px-5 py-4 text-sm text-rose-200">
          {err || "Sem dados de quota."}
        </div>
      </section>
    );
  }

  const tierMeta = TIER_META[snap.tier];
  const pct = quotaUsagePct(snap);
  const isUnlimited = snap.monthly_hdr_limit === null;
  const isExceeded = snap.is_exceeded;
  const periodDays = daysUntil(snap.period_end);

  return (
    <section className="mx-auto max-w-5xl px-6 py-16">
      <header className="mb-10">
        <p className="text-xs uppercase tracking-widest text-gold-400/80">Minha Conta</p>
        <h1 className="mt-2 text-3xl font-semibold text-white">Quota e Plano</h1>
        <p className="mt-2 max-w-2xl text-sm text-white/60">
          Acompanhe o uso da sua organização e veja quando o período de cobrança renova.
        </p>
      </header>

      {/* Plano atual */}
      <div className="grid gap-6 md:grid-cols-2">
        <article className="rounded-2xl border border-white/10 bg-white/[0.02] p-6">
          <p className="text-xs uppercase tracking-wider text-white/40">Plano atual</p>
          <h2 className="mt-2 text-2xl font-semibold text-white">{tierMeta.name}</h2>
          <p className="mt-2 text-sm text-white/65">{tierMeta.description}</p>
          {snap.tier === "free" ? (
            <Link
              href={EXTERNAL_PLANS_URL}
              target="_blank"
              rel="noopener noreferrer"
              className="mt-6 inline-block rounded-full border border-gold-400/50 bg-gold-400/10 px-5 py-2 text-sm font-medium text-gold-200 transition hover:bg-gold-400/20 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-gold-400/60"
            >
              Ver planos pagos →
            </Link>
          ) : null}
        </article>

        {/* Uso no período */}
        <article className="rounded-2xl border border-white/10 bg-white/[0.02] p-6">
          <p className="text-xs uppercase tracking-wider text-white/40">Uso no período</p>
          {isUnlimited ? (
            <>
              <p className="mt-2 text-3xl font-semibold text-white">
                {snap.used_in_period}
                <span className="ml-2 text-sm font-normal text-white/45">HDRs · ilimitado</span>
              </p>
              <p className="mt-3 text-xs text-white/50">
                Período renova em {periodDays} dias ({formatDate(snap.period_end)}).
              </p>
            </>
          ) : (
            <>
              <p className="mt-2 text-3xl font-semibold text-white">
                {snap.used_in_period}
                <span className="ml-1 text-base font-normal text-white/45">
                  / {snap.monthly_hdr_limit}
                </span>
              </p>
              <div
                role="progressbar"
                aria-valuenow={Math.round((pct ?? 0) * 100)}
                aria-valuemin={0}
                aria-valuemax={100}
                className="mt-4 h-2 w-full overflow-hidden rounded-full bg-white/10"
              >
                <div
                  className={`h-full transition-all ${
                    isExceeded
                      ? "bg-rose-500"
                      : (pct ?? 0) >= 0.7
                        ? "bg-gold-400"
                        : "bg-emerald-400"
                  }`}
                  style={{ width: `${Math.min((pct ?? 0) * 100, 100)}%` }}
                />
              </div>
              <p className="mt-3 text-xs text-white/50">
                {isExceeded
                  ? `Limite atingido. Renova em ${periodDays} dias.`
                  : `${snap.remaining ?? 0} HDRs restantes · período renova em ${periodDays} dias.`}
              </p>
            </>
          )}
        </article>
      </div>

      {/* Recursos do plano */}
      <article className="mt-6 rounded-2xl border border-white/10 bg-white/[0.02] p-6">
        <p className="text-xs uppercase tracking-wider text-white/40">Recursos inclusos</p>
        <ul className="mt-4 grid gap-3 text-sm text-white/75 sm:grid-cols-2">
          <li className="flex items-start gap-2">
            <span className="text-gold-400">✓</span>
            <span>
              Retenção:{" "}
              {snap.retention_days === null
                ? "indefinida"
                : `${snap.retention_days} dias`}
            </span>
          </li>
          <li className="flex items-start gap-2">
            <span className={snap.forensic_pdf_enabled ? "text-gold-400" : "text-white/30"}>
              {snap.forensic_pdf_enabled ? "✓" : "—"}
            </span>
            <span className={snap.forensic_pdf_enabled ? "" : "text-white/40 line-through"}>
              Relatório forense PDF/A-3 com selo de tempo (RFC 3161, pronto para ICP-Brasil)
            </span>
          </li>
          <li className="flex items-start gap-2">
            <span className="text-gold-400">✓</span>
            <span>Corpus normativo BR (LGPD, CNJ, OAB, CPC, CPP, CLT, NBC TP)</span>
          </li>
          <li className="flex items-start gap-2">
            <span className="text-gold-400">✓</span>
            <span>Verificação pública /verification/&lt;hdr_id&gt;</span>
          </li>
        </ul>
      </article>

      {/* Período de cobrança */}
      <article className="mt-6 rounded-2xl border border-white/10 bg-white/[0.02] p-6">
        <p className="text-xs uppercase tracking-wider text-white/40">Período de cobrança</p>
        <dl className="mt-4 grid gap-3 text-sm sm:grid-cols-2">
          <div>
            <dt className="text-white/45">Início</dt>
            <dd className="mt-1 text-white">{formatDate(snap.period_start)}</dd>
          </div>
          <div>
            <dt className="text-white/45">Fim</dt>
            <dd className="mt-1 text-white">{formatDate(snap.period_end)}</dd>
          </div>
        </dl>
      </article>

      {/* Links úteis */}
      <nav aria-label="Ações da conta" className="mt-10 flex flex-wrap gap-3 text-sm">
        <Link
          href="/conta/api-keys"
          className="rounded-full border border-white/15 px-5 py-2 text-white transition hover:border-white/30 hover:bg-white/[0.03] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-gold-400/60"
        >
          Chaves de API
        </Link>
        <Link
          href="/missions"
          className="rounded-full border border-white/15 px-5 py-2 text-white transition hover:border-white/30 hover:bg-white/[0.03] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-gold-400/60"
        >
          Meus casos
        </Link>
        <Link
          href="/docs/quickstart"
          className="rounded-full border border-white/15 px-5 py-2 text-white transition hover:border-white/30 hover:bg-white/[0.03] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-gold-400/60"
        >
          Documentação
        </Link>
      </nav>
    </section>
  );
}
