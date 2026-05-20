import Link from "next/link";

import { DocsSearch } from "@/components/docs/DocsSearch";
import { DOC_ENTRIES, DOCS_CATEGORY_LABELS, type DocsCategoryKey } from "@/lib/docs-registry";

const ORDER: DocsCategoryKey[] = ["manuals", "legal", "guides", "faq", "changelog"];

export default function DocsHubPage() {
  return (
    <div className="space-y-10">
      <section className="glass-elite rounded-3xl border border-white/12 p-6 md:p-10">
        <p className="text-[11px] font-semibold uppercase tracking-[0.35em] text-gold-400/88">Fase 10 · Documentação</p>
        <h1 className="mt-3 text-gradient text-3xl font-semibold tracking-tight md:text-4xl">Central de Documentação</h1>
        <p className="mt-4 max-w-3xl text-sm leading-relaxed text-white/62">
          Manuais operacionais, quadro legal mínimo (Termos, Privacidade, LGPD), guias de conformidade e FAQ integrados ao
          cockpit Heillon Legal. Documentação completa em Português (Brasil) para suportar auditorias internas e exigências de
          transparência do mercado jurídico.
        </p>
        <div id="docs-search-anchor" className="mt-8 max-w-2xl">
          <DocsSearch autoFocusHub id="docs-search-main" />
        </div>
      </section>

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
              <ul className="mt-4 space-y-3 text-[13px]">
                {items.map((doc) => (
                  <li key={doc.href}>
                    <Link
                      href={doc.href}
                      prefetch={false}
                      className="group block rounded-xl border border-white/8 bg-white/[0.02] px-4 py-3 transition-colors hover:border-gold-500/35 hover:bg-white/[0.05]"
                    >
                      <span className="font-medium text-white group-hover:text-gold-200">{doc.title}</span>
                      <span className="mt-1 block text-[11px] text-white/48">{doc.description}</span>
                    </Link>
                  </li>
                ))}
              </ul>
            </div>
          );
        })}
      </section>

      <p className="text-[11px] text-white/38">
        Última revisão editorial global: 19 de maio de 2026. Contacte o DPO / owner legal da vossa organização para anexar
        versões assinadas destes textos em processos ou contratos enterprise.
      </p>
    </div>
  );
}
