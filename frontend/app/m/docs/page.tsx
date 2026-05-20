"use client";

import Link from "next/link";
import { useMemo, useState } from "react";

import { DocsSearch } from "@/components/docs/DocsSearch";
import {
  DOC_ENTRIES,
  DOCS_CATEGORY_LABELS,
  type DocsCategoryKey,
} from "@/lib/docs-registry";

const ORDER: DocsCategoryKey[] = ["manuals", "legal", "guides", "faq", "changelog"];

export default function MobileDocsHubPage() {
  const [open, setOpen] = useState<DocsCategoryKey | null>("manuals");

  const grouped = useMemo(() => {
    const m = new Map<DocsCategoryKey, typeof DOC_ENTRIES>();
    for (const k of ORDER) m.set(k, []);
    for (const d of DOC_ENTRIES) {
      const list = m.get(d.category);
      if (list) list.push(d);
    }
    return m;
  }, []);

  return (
    <div className="px-5 pb-6">
      <header className="pt-10">
        <p className="text-[10px] font-semibold uppercase tracking-[0.28em] text-gold-500/82">Docs · PWA</p>
        <h1 className="mt-2 text-xl font-semibold text-white">Central de Documentação</h1>
        <p className="mt-3 text-[13px] leading-relaxed text-white/52">
          Mesmos manuais e textos legais que em <Link href="/docs" className="text-gold-400 underline-offset-4 hover:underline">/docs</Link>
          , com navegação compacta para o cockpit móvel. Abrir um documento leva‑o à versão completa com índice e impressão/PDF quando
          aplicável no browser.
        </p>
      </header>

      <div className="mt-8">
        <DocsSearch dense id="docs-search-mobile-hub" />
      </div>

      <div className="mt-10 space-y-3">
        {ORDER.map((key) => {
          const meta = DOCS_CATEGORY_LABELS[key];
          const items = grouped.get(key) ?? [];
          const expanded = open === key;
          return (
            <div key={key} className="glass-elite rounded-2xl border border-white/12">
              <button
                type="button"
                aria-expanded={expanded}
                className="flex w-full items-center justify-between px-5 py-4 text-left text-sm font-semibold text-white"
                onClick={() => setOpen(expanded ? null : key)}
              >
                <span className="flex items-center gap-2">
                  <span aria-hidden>{meta.icon}</span>
                  {meta.label}
                  <span className="rounded-full bg-white/[0.06] px-2 py-0.5 text-[10px] font-normal text-white/45">
                    {items.length}
                  </span>
                </span>
                <span aria-hidden className="text-white/35">
                  {expanded ? "−" : "+"}
                </span>
              </button>
              {expanded ? (
                <ul className="border-t border-white/10 px-2 pb-2">
                  {items.map((doc) => (
                    <li key={doc.href}>
                      <Link
                        href={doc.href}
                        prefetch={false}
                        className="block rounded-xl px-4 py-3 text-[13px] text-white/88 transition-colors hover:bg-white/[0.05]"
                      >
                        <span className="font-medium text-white">{doc.title}</span>
                        <span className="mt-1 block text-[11px] text-white/45">{doc.description}</span>
                      </Link>
                    </li>
                  ))}
                </ul>
              ) : null}
            </div>
          );
        })}
      </div>

      <p className="mt-10 text-[11px] text-white/35">
        Ligações rápidas:{" "}
        <Link prefetch={false} href="/docs/terms" className="text-gold-400/90 hover:underline">
          Termos
        </Link>{" "}
        ·{" "}
        <Link prefetch={false} href="/docs/privacy" className="text-gold-400/90 hover:underline">
          Privacidade
        </Link>{" "}
        ·{" "}
        <Link prefetch={false} href="/docs/faq" className="text-gold-400/90 hover:underline">
          FAQ
        </Link>
      </p>
    </div>
  );
}
