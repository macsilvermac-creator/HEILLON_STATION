"use client";

/**
 * ConditionalAppShell
 *
 * Desktop + Mobile → FolderTopbar (filing-drawer gold tabs, fixed top)
 * PWA /m/*        → bare shell (no chrome)
 *
 * FolderSidebar is preserved but not active (can be re-enabled if needed).
 */

import { usePathname } from "next/navigation";

import { CustomCursor } from "@/components/CustomCursor";
import { FolderTopbar, TOPBAR_H } from "@/components/FolderTopbar";
import { QuotaBanner } from "@/components/QuotaBanner";
import { SiteFooter } from "@/components/SiteFooter";

export function ConditionalAppShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const isMobilePwaShell = pathname === "/m" || pathname.startsWith("/m/");

  if (isMobilePwaShell) {
    // Mobile PWA: bare shell with single <main> landmark (a11y)
    return <main className="relative">{children}</main>;
  }

  return (
    <>
      <CustomCursor />
      <FolderTopbar />

      {/* Content sits below the fixed topbar */}
      <div
        id="main-content-shell"
        style={{ paddingTop: `${TOPBAR_H}px` }}
        className="min-h-screen"
      >
        <QuotaBanner />
        <main className="relative">{children}</main>
        <SiteFooter />
      </div>
    </>
  );
}
