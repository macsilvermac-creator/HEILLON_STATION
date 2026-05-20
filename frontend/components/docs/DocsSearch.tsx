"use client";

import Link from "next/link";
import { useMemo, useState } from "react";

import type { DocEntryMeta } from "@/lib/docs-registry";
import { DOCS_CATEGORY_LABELS, filterDocsByQuery } from "@/lib/docs-registry";

export function DocsSearch(props: {
  dense?: boolean;
  autoFocusHub?: boolean;
  id?: string;
}) {
  const { dense = false, autoFocusHub = false, id = "docs-search-main" } = props;
  const [q, setQ] = useState("");
  const [open, setOpen] = useState(false);

  const results = useMemo(() => filterDocsByQuery(q), [q]);

  const showDropdown = open && q.trim().length > 0;

  return (
    <div className={`relative ${dense ? "" : "w-full"}`}>
      <label htmlFor={id} className="sr-only">
        Pesquisar documentação
      </label>
      <div className="glass-elite relative flex overflow-hidden rounded-2xl border border-white/12">
        <span className="pointer-events-none flex items-center pl-4 text-xs text-white/45" aria-hidden>
          🔍
        </span>
        <input
          id={id}
          type="search"
          autoComplete="off"
          autoFocus={autoFocusHub}
          placeholder="Filtrar títulos e tópicos…"
          value={q}
          onFocus={() => setOpen(true)}
          onBlur={(e) => {
            const rel = e.relatedTarget;
            window.setTimeout(() => {
              const panel = document.querySelector("[data-docs-search-panel]");
              if (
                rel instanceof Node &&
                panel instanceof HTMLElement &&
                panel.contains(rel)
              ) {
                return;
              }
              setOpen(false);
            }, 150);
          }}
          onChange={(e) => {
            setOpen(true);
            setQ(e.target.value);
          }}
          className={`w-full bg-transparent py-3 pr-5 pl-3 text-sm text-white placeholder:text-white/30 focus:outline-none ${
            dense ? "py-2 text-[13px]" : ""
          }`}
        />
      </div>

      {showDropdown ? (
        <div
          data-docs-search-panel
          className="absolute top-full left-0 z-[95] mt-2 max-h-80 w-full overflow-y-auto rounded-2xl border border-white/12 bg-deep-space-800/96 py-2 shadow-2xl shadow-black/55 backdrop-blur-xl"
          role="listbox"
          aria-label="Resultados da pesquisa na documentação"
        >
          {results.length === 0 ? (
            <p className="px-4 py-3 text-xs text-white/45">Nenhum resultado. Refine ou limpe os termos.</p>
          ) : (
            results.map((doc: DocEntryMeta) => (
              <Link
                key={doc.href}
                href={doc.href}
                prefetch={false}
                role="option"
                className="block px-4 py-2.5 text-left transition-colors hover:bg-white/[0.05]"
              >
                <span className="block text-[11px] text-gold-400/95">
                  {DOCS_CATEGORY_LABELS[doc.category].icon}{" "}
                  {DOCS_CATEGORY_LABELS[doc.category].label}
                </span>
                <span className="text-sm font-medium text-white">{doc.title}</span>
                <span className="mt-1 block text-[11px] text-white/42">{doc.description}</span>
              </Link>
            ))
          )}
        </div>
      ) : null}
    </div>
  );
}
