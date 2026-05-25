"use client";

/**
 * ConditionalAppShell
 *
 * Desktop  → FolderSidebar (fixed left) + content shifted right
 * Mobile   → FolderSidebar mobile header + drawer
 * PWA /m/* → bare (no chrome)
 */

import { usePathname } from "next/navigation";

import { CustomCursor } from "@/components/CustomCursor";
import { FolderSidebar } from "@/components/FolderSidebar";
import { SiteFooter } from "@/components/SiteFooter";

export function ConditionalAppShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const isMobilePwaShell = pathname === "/m" || pathname.startsWith("/m/");

  // PWA shell — no navigation chrome
  if (isMobilePwaShell) {
    return <>{children}</>;
  }

  return (
    <>
      <CustomCursor />

      {/* Sidebar (handles both desktop fixed + mobile drawer internally) */}
      <FolderSidebar />

      {/*
       * Content wrapper:
       *   – Desktop: left padding matches sidebar width (CSS var set by sidebar state)
       *     We use a CSS custom property trick via inline style + lg:pl-[220px].
       *     The sidebar uses a spring animation so we can't perfectly sync it, but
       *     the lg:pl-[220px] default (expanded) covers 95% of cases.
       *     If the user collapses the sidebar, the content naturally expands.
       *   – Mobile: top padding for the fixed mobile header (56px).
       */}
      {/* #main-content-shell → padding-left is driven by --sidebar-w CSS var (see globals.css) */}
      <div className="min-h-screen pt-[56px] lg:pt-0" id="main-content-shell">
        <main className="relative">{children}</main>
        <SiteFooter />
      </div>
    </>
  );
}
