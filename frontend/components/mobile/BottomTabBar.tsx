"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const tabs = [
  { href: "/m", label: "Início", re: /^\/m$/ },
  { href: "/m/missions", label: "Casos", re: /^\/m\/missions|\/m\/approve\// },
  { href: "/m/verify", label: "Verificar", re: /^\/m\/verify/ },
  { href: "/m/profile", label: "Perfil", re: /^\/m\/profile/ },
] as const;

export function BottomTabBar() {
  const pathname = usePathname() || "";

  return (
    <nav
      className="glass-elite fixed bottom-0 left-0 right-0 z-[140] flex justify-around gap-2 border-white/15 px-4 pt-4"
      style={{
        paddingBottom: "max(calc(env(safe-area-inset-bottom, 0px) + 10px), 14px)",
        paddingTop: "0.85rem",
      }}
    >
      {tabs.map((tab) => {
        const active = pathname === tab.href || tab.re.test(pathname);
        const icon =
          tab.href === "/m" ? "◇" : tab.href === "/m/missions" ? "≡" : tab.href === "/m/verify" ? "✦" : "●";
        return (
          <Link
            key={tab.href}
            href={tab.href}
            prefetch={false}
            className={`flex min-h-[48px] min-w-[72px] flex-1 flex-col items-center justify-center gap-1 rounded-xl text-[11px] font-medium transition-colors ${
              active ? "text-gold-400" : "text-white/45"
            }`}
          >
            <span className={`text-lg duration-300 ${active ? "scale-110" : "scale-100"}`}>{icon}</span>
            {tab.label}
          </Link>
        );
      })}
    </nav>
  );
}
