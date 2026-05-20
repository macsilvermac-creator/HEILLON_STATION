"use client";

import Link from "next/link";
import { type ReactNode, useLayoutEffect, useRef, useState } from "react";

export type RelatedDocLink = {
  href: string;
  label: string;
};

export type DocsContentProps = {
  title: string;
  subtitle?: string;
  lastUpdated: string;
  related?: RelatedDocLink[];
  children: ReactNode;
};

export function DocsContent({ title, subtitle, lastUpdated, related = [], children }: DocsContentProps) {
  const mainRef = useRef<HTMLDivElement>(null);
  const [toc, setToc] = useState<{ id: string; label: string; depth: number }[]>([]);

  useLayoutEffect(() => {
    const root = mainRef.current;
    if (!root) return;
    const nodes = Array.from(root.querySelectorAll("h2[id], h3[id]"));
    setToc(
      nodes.map((el) => ({
        id: el.id,
        label: el.textContent?.trim() ?? el.id,
        depth: el.tagName === "H3" ? 2 : 1,
      }))
    );
  }, [children]);

  return (
    <article className="min-w-0 flex-1">
      <header className="glass-elite mb-8 rounded-2xl border border-white/12 p-6 md:p-8">
        <p className="text-[11px] font-semibold uppercase tracking-[0.3em] text-gold-400/90">Central de Documentação</p>
        <h1 className="mt-2 text-gradient text-2xl font-semibold tracking-tight md:text-3xl">{title}</h1>
        {subtitle ? (
          <p className="mt-3 max-w-3xl text-sm leading-relaxed text-white/60">{subtitle}</p>
        ) : null}
        <div className="mt-5 flex flex-wrap items-center gap-3 border-t border-white/10 pt-5 text-[11px] text-white/45">
          <span>Última actualização: {lastUpdated}</span>
          <span className="hidden h-1 w-1 rounded-full bg-white/35 sm:inline" aria-hidden />
          <button
            type="button"
            disabled
            className="rounded-full border border-white/14 px-4 py-1.5 text-[10px] font-semibold uppercase tracking-wider text-white/35 cursor-not-allowed"
            title="Exportação PDF em roadmap (Fase 10.1)."
          >
            PDF (brevemente)
          </button>
          <span className="hidden h-1 w-1 rounded-full bg-white/35 sm:inline" aria-hidden />
          <span className="text-[10px] font-semibold uppercase tracking-wider text-white/38">
            Sugestão editorial (CMS interno)
          </span>
        </div>
      </header>

      <div className="flex gap-10 lg:flex-row-reverse">
        {toc.length > 1 ? (
          <nav aria-label="Nesta página" className="hidden w-52 flex-shrink-0 lg:block">
            <p className="mb-3 text-[10px] font-semibold uppercase tracking-[0.3em] text-white/38">Nesta página</p>
            <ul className="space-y-2 text-[11px] text-white/55">
              {toc.map((row) => (
                <li key={row.id} style={{ paddingLeft: row.depth > 1 ? "0.6rem" : 0 }}>
                  <a href={`#${row.id}`} className="leading-snug underline-offset-2 hover:text-gold-300 hover:underline">
                    {row.label}
                  </a>
                </li>
              ))}
            </ul>
          </nav>
        ) : null}

        <div ref={mainRef} className="docs-prose min-w-0 flex-1 pb-28">
          {children}
        </div>
      </div>

      {related.length > 0 ? (
        <footer className="glass-card mt-10 rounded-2xl border border-white/10 p-5">
          <p className="text-[11px] font-semibold uppercase tracking-[0.25em] text-white/42">Veja também</p>
          <ul className="mt-3 space-y-2 text-sm">
            {related.map((r) => (
              <li key={r.href}>
                <Link href={r.href} className="text-gold-400 underline-offset-4 hover:text-gold-300 hover:underline">
                  {r.label}
                </Link>
              </li>
            ))}
          </ul>
        </footer>
      ) : null}
    </article>
  );
}
