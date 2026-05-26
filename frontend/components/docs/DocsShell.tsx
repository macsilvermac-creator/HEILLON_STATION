"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { type ReactNode, useState } from "react";

import { DocsMobileOverlay, DocsSidebar } from "@/components/docs/DocsSidebar";
import { DocsSearch } from "@/components/docs/DocsSearch";

export function DocsShell({ children }: { children: ReactNode }) {
  const pathname = usePathname() || "";
  const [mobileNav, setMobileNav] = useState(false);

  const crumbs = breadcrumbTrail(pathname);

  const isHub = pathname === "/docs" || pathname === "/docs/";

  return (
    <>
      <DocsMobileOverlay mobileOpen={mobileNav} setMobileOpen={setMobileNav} />

      <div className="mx-auto flex w-full max-w-[92rem] gap-0 px-3 pb-36 pt-[6rem] lg:gap-10 lg:px-6 lg:pb-44 lg:pt-32">
        <DocsSidebar mobileOpen={mobileNav} setMobileOpen={setMobileNav} />

        <div className="min-w-0 flex-1 lg:max-w-none">
          <div className="mb-8 flex flex-col gap-6 md:flex-row md:items-start md:justify-between">
            <div className="min-w-0 flex-1">
              <nav aria-label="Breadcrumb" className="mb-3 text-[11px] text-white/45">
                <ol className="flex flex-wrap items-center gap-1">
                  {crumbs.map((c, i) => (
                    <li key={c.href} className="flex items-center gap-1">
                      {i > 0 ? <span className="text-white/25">/</span> : null}
                      <Link href={c.href} className="truncate hover:text-gold-400/92">
                        {c.label}
                      </Link>
                    </li>
                  ))}
                </ol>
              </nav>

              <button
                type="button"
                onClick={() => setMobileNav(true)}
                className="mb-4 inline-flex items-center gap-2 rounded-xl border border-white/15 bg-white/[0.04] px-3 py-2 text-[12px] text-white/75 lg:hidden"
              >
                <span aria-hidden>☰</span>
                Índice da documentação
              </button>

              {!isHub ? (
                <div className="max-w-xl lg:max-w-md">
                  <DocsSearch dense autoFocusHub={false} id="docs-search-inline" />
                </div>
              ) : null}
            </div>
          </div>

          <div>{children}</div>
        </div>
      </div>
    </>
  );
}

function breadcrumbTrail(pathname: string): { label: string; href: string }[] {
  const base = [{ label: "Início", href: "/" }];
  base.push({ label: "Docs", href: "/docs" });
  if (!pathname.startsWith("/docs") || pathname === "/docs") return base;

  const tail = pathname.replace(/^\/docs\/?/, "").split("/")[0];

  const labelMap: Record<string, string> = {
    quickstart:           "Início rápido",
    architecture:         "Arquitetura",
    regulations:          "Regulatório",
    usage:                "Manual de uso",
    "chain-of-custody":   "Cadeia de custódia",
    lgpd:                 "LGPD",
    faq:                  "FAQ",
    terms:                "Termos",
    privacy:              "Privacidade",
    compliance:           "Conformidade",
    expert:               "Perito",
    admin:                "Administrador",
    changelog:            "Changelog",
  };

  const label = labelMap[tail] ?? "Documentação";
  return [...base, { label, href: pathname }];
}
