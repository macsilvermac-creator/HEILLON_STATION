import Link from "next/link";

import { DocsSearch } from "@/components/docs/DocsSearch";
import { DOC_ENTRIES, DOCS_CATEGORY_LABELS, type DocsCategoryKey } from "@/lib/docs-registry";

const ORDER: DocsCategoryKey[] = ["start", "manuals", "legal", "guides", "faq", "changelog"];

const SYSTEM_STATS = [
  { value: "272",          label: "Testes automatizados", icon: "✅" },
  { value: "32",           label: "Rotas frontend",       icon: "🗺" },
  { value: "18",           label: "Domínios DDD",         icon: "🏛" },
  { value: "7+",           label: "Jurisdições cobertas", icon: "🌍" },
  { value: "ISO 42001",    label: "Certificação global",  icon: "🏅" },
  { value: "Fase 20",      label: "Sistema definitivo",   icon: "🏆" },
];

export default function DocsHubPage() {
  return (
    <div className="space-y-12">

      {/* ── Hero ── */}
      <section className="glass-elite rounded-3xl border border-white/12 p-6 md:p-10">
        <div className="flex flex-wrap items-start justify-between gap-6">
          <div className="min-w-0 flex-1">
            <div className="flex flex-wrap items-center gap-2">
              <p className="text-[11px] font-semibold uppercase tracking-[0.35em] text-gold-400/88">
                Fase 20 · Documentação
              </p>
              <span className="inline-flex items-center gap-1 rounded-full border border-emerald-400/30 bg-emerald-400/8 px-2.5 py-0.5 text-[10px] font-semibold text-emerald-300">
                ● Sistema Definitivo Global
              </span>
            </div>
            <h1 className="mt-3 text-gradient text-3xl font-semibold tracking-tight md:text-4xl">
              Central de Documentação
            </h1>
            <p className="mt-4 max-w-3xl text-sm leading-relaxed text-white/62">
              Manuais operacionais completos, guias regulatórios globais (LGPD, EU AI Act, ISO 42001, APAC),
              arquitetura técnica e FAQ por perfil — tudo o que precisa para operar o Heillon Legal
              com legitimidade computacional plena.
            </p>
          </div>

          {/* Badge de estado */}
          <div className="shrink-0 rounded-2xl border border-gold-400/20 bg-gold-400/5 p-4 text-center">
            <div
              className="text-2xl font-bold"
              style={{
                background: "linear-gradient(135deg,#EDD97A,#C9A227)",
                WebkitBackgroundClip: "text",
                WebkitTextFillColor: "transparent",
              }}
            >
              v20
            </div>
            <div className="mt-1 text-[10px] text-white/50">Mai 2026</div>
          </div>
        </div>

        {/* Busca */}
        <div id="docs-search-anchor" className="mt-8 max-w-2xl">
          <DocsSearch autoFocusHub id="docs-search-main" />
        </div>
      </section>

      {/* ── Métricas do sistema ── */}
      <section>
        <h2 className="mb-4 text-[11px] font-semibold uppercase tracking-[0.28em] text-white/40">
          Estado do sistema
        </h2>
        <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-6">
          {SYSTEM_STATS.map((s) => (
            <div
              key={s.label}
              className="flex flex-col items-center gap-1 rounded-xl border border-white/8 bg-white/[0.02] px-3 py-4 text-center"
            >
              <span className="text-lg" aria-hidden>{s.icon}</span>
              <span
                className="text-xl font-bold"
                style={{
                  background: "linear-gradient(135deg,#EDD97A,#C9A227)",
                  WebkitBackgroundClip: "text",
                  WebkitTextFillColor: "transparent",
                }}
              >
                {s.value}
              </span>
              <span className="text-[10px] leading-tight text-white/50">{s.label}</span>
            </div>
          ))}
        </div>
      </section>

      {/* ── Atalhos rápidos ── */}
      <section>
        <h2 className="mb-4 text-[11px] font-semibold uppercase tracking-[0.28em] text-white/40">
          Por onde começar
        </h2>
        <div className="grid gap-3 sm:grid-cols-3">
          {[
            { href: "/docs/quickstart",   icon: "🚀", title: "Início em 5 minutos", desc: "Crie o primeiro HDR verificável rapidamente" },
            { href: "/docs/usage",        icon: "📘", title: "Manual completo",      desc: "Todos os fluxos: autenticação, missões, verificação" },
            { href: "/docs/chain-of-custody", icon: "🔐", title: "Cadeia de custódia", desc: "SHA-256, RFC 3161, ICP-Brasil, valor probatório" },
          ].map((item) => (
            <Link
              key={item.href}
              href={item.href}
              prefetch={false}
              className="group flex items-start gap-4 rounded-2xl border border-gold-400/20 bg-gold-400/5 px-5 py-4 transition-all hover:border-gold-400/40 hover:bg-gold-400/8"
            >
              <span className="mt-0.5 text-2xl" aria-hidden>{item.icon}</span>
              <div>
                <p className="font-semibold text-gold-200 group-hover:text-gold-100">{item.title}</p>
                <p className="mt-0.5 text-[12px] text-white/50">{item.desc}</p>
              </div>
            </Link>
          ))}
        </div>
      </section>

      {/* ── Índice por categoria ── */}
      <section className="grid gap-6 md:grid-cols-2">
        {ORDER.map((key) => {
          const meta = DOCS_CATEGORY_LABELS[key];
          const items = DOC_ENTRIES.filter((d) => d.category === key);
          return (
            <div key={key} className="glass-card rounded-2xl border border-white/10 p-6">
              <h2 className="flex items-center gap-2 text-sm font-semibold text-white">
                <span aria-hidden>{meta.icon}</span>
                {meta.label}
              </h2>
              <ul className="mt-4 space-y-2 text-[13px]">
                {items.map((doc) => (
                  <li key={doc.href}>
                    <Link
                      href={doc.href}
                      prefetch={false}
                      className="group flex items-start gap-3 rounded-xl border border-white/6 bg-white/[0.02] px-4 py-3 transition-colors hover:border-gold-500/30 hover:bg-white/[0.04]"
                    >
                      <div className="min-w-0 flex-1">
                        <span className="font-medium text-white group-hover:text-gold-200">{doc.title}</span>
                        <span className="mt-0.5 block text-[11px] text-white/45">{doc.description}</span>
                      </div>
                      <span className="mt-0.5 shrink-0 text-white/20 group-hover:text-gold-400/50" aria-hidden>→</span>
                    </Link>
                  </li>
                ))}
              </ul>
            </div>
          );
        })}
      </section>

      {/* ── Regulatório ── */}
      <section className="rounded-2xl border border-white/8 bg-white/[0.015] p-6">
        <h2 className="mb-4 text-sm font-semibold text-white">🌍 Cobertura regulatória</h2>
        <div className="flex flex-wrap gap-2">
          {[
            "🇧🇷 LGPD + ICP-Brasil",
            "🇧🇷 CNJ 615/2025",
            "🇪🇺 EU AI Act",
            "🇪🇺 GDPR + eIDAS 2.0",
            "🇺🇸 Colorado SB 205",
            "🇺🇸 CCPA/CPRA + ABA",
            "🇦🇪 UAE PDPL + DIFC",
            "🇬🇧 UK GDPR",
            "🇸🇬 PDPA + Agentic AI",
            "🇦🇺 Privacy Act",
            "🇨🇦 PIPEDA + C-27",
            "🏅 ISO 42001:2023",
          ].map((tag) => (
            <span
              key={tag}
              className="inline-flex items-center rounded-lg border border-white/8 bg-white/[0.03] px-2.5 py-1 text-[11px] text-white/60"
            >
              {tag}
            </span>
          ))}
        </div>
        <p className="mt-4 text-[11px] text-white/38">
          <Link href="/docs/regulations" className="text-gold-400/60 hover:text-gold-400 underline">
            Ver mapa regulatório completo →
          </Link>
        </p>
      </section>

      <p className="text-[11px] text-white/30">
        Última revisão: 25 de maio de 2026 — Fase 20 (Sistema Definitivo Global).
        Contacte o DPO / owner legal da organização para versões assinadas em processos enterprise.
      </p>
    </div>
  );
}
