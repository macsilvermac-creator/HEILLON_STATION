"use client";

import { usePathname } from "next/navigation";

import { CustomCursor } from "@/components/CustomCursor";
import { Navbar } from "@/components/Navbar";
import { SiteFooter } from "@/components/SiteFooter";
export function ConditionalAppShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const isMobilePwaShell = pathname === "/m" || pathname.startsWith("/m/");

  if (isMobilePwaShell) {
    return <>{children}</>;
  }

  return (
    <>
      <CustomCursor />
      <Navbar />
      {children}
      <SiteFooter />
    </>
  );
}
