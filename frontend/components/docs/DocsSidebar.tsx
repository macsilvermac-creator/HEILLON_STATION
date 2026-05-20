"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import type { Dispatch, ReactNode, SetStateAction } from "react";

import type { DocsCategoryKey } from "@/lib/docs-registry";
import { DOC_ENTRIES, DOCS_CATEGORY_LABELS } from "@/lib/docs-registry";

const ORDER: DocsCategoryKey[] = ["manuals", "legal", "guides", "faq", "changelog"];

export function DocsSidebar(props: {
  mobileOpen?: boolean;
  setMobileOpen?: Dispatch<SetStateAction<boolean>>;
  headerSlot?: ReactNode;
}) {
  const pathname = usePathname() || "";
  const { mobileOpen = false, setMobileOpen, headerSlot } = props;

  const closeIfMobile = () => setMobileOpen?.(false);

  return (
    <aside
      className={`fixed inset-y-0 left-0 z-[90] flex w-[min(100vw,18rem)] flex-col gap-6 border-r border-white/10 bg-deep-space-900/94 p-6 pt-[6rem] backdrop-blur-2xl transition-transform lg:sticky lg:top-28 lg:h-[calc(100vh-9rem)] lg:w-64 lg:translate-x-0 lg:flex-shrink-0 lg:border-r lg:bg-white/[0.02] lg:pt-8 ${
        mobileOpen ? "translate-x-0" : "-translate-x-full lg:translate-x-0"
      }`}
    >
      {headerSlot}
      <nav className="flex-1 overflow-y-auto pr-2 text-[13px]">
        <p className="mb-4 text-[10px] font-semibold uppercase tracking-[0.35em] text-white/35">Índice</p>
        {ORDER.map((key) => {
          const meta = DOCS_CATEGORY_LABELS[key];
          const items = DOC_ENTRIES.filter((d) => d.category === key);
          return (
            <div key={key} className="mb-5">
              <p className="mb-2 flex items-center gap-2 text-[11px] font-semibold text-gold-400/95">
                <span aria-hidden>{meta.icon}</span>
                {meta.label}
              </p>
              <ul className="space-y-1">
                {items.map((doc) => {
                  const active = pathname === doc.href;
                  return (
                    <li key={doc.href}>
                      <Link
                        href={doc.href}
                        onClick={closeIfMobile}
                        prefetch={false}
                        className={`block rounded-xl border-l-[3px] py-2 pl-3 pr-2 transition-colors ${
                          active
                            ? "border-gold-500 bg-white/[0.07] font-medium text-white"
                            : "border-transparent text-white/58 hover:border-white/20 hover:bg-white/[0.035] hover:text-white"
                        }`}
                      >
                        {doc.title}
                      </Link>
                    </li>
                  );
                })}
              </ul>
            </div>
          );
        })}
      </nav>
      <Link
        href="/docs"
        onClick={closeIfMobile}
        className="text-[11px] text-gold-400/85 underline-offset-4 hover:text-gold-300 hover:underline"
      >
        ← Hub da documentação
      </Link>
    </aside>
  );
}

export function DocsMobileOverlay(props: {
  mobileOpen: boolean;
  setMobileOpen: Dispatch<SetStateAction<boolean>>;
}) {
  const { mobileOpen, setMobileOpen } = props;
  if (!mobileOpen) return null;
  return (
    <button
      type="button"
      aria-label="Fechar menu de documentação"
      className="fixed inset-0 z-[85] bg-black/55 backdrop-blur-sm lg:hidden"
      onClick={() => setMobileOpen(false)}
    />
  );
}
