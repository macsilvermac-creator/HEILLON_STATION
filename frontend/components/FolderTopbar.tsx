"use client";

/**
 * FolderTopbar — LiquidGlass Filing-Drawer Navigation
 *
 * Visual: a dark glass strip at the top of the screen representing a filing
 * cabinet drawer. Each section is a compact folder-tab ear sitting inside the
 * strip — rounded top, flat bottom, all in the same gold palette. The 1 px
 * gold line at the very bottom of the strip is the "drawer rim" that the tabs
 * sit against.
 *
 * Design rules:
 *  • Single colour — gold (#D4AF37 palette) for all tabs
 *  • Compact — 48 px total height, tabs 28 px inside the strip
 *  • No sidebar, no collapse button, no colour-per-section
 *  • Fullscreen toggle on the far right
 *
 * Fase 20 — Heillon Legal
 */

import { AnimatePresence, motion } from "framer-motion";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useCallback, useEffect, useRef, useState } from "react";

import { useAuth } from "@/lib/auth-context";

// ── Constants ──────────────────────────────────────────────────────────────────

export const TOPBAR_H = 48; // px — total height, used by ConditionalAppShell

// ── Colour tokens (all gold, single palette) ───────────────────────────────────

const G = {
  active_bg:      "rgba(212,175,55,0.93)",
  active_text:    "#040810",
  inactive_bg:    "rgba(212,175,55,0.06)",
  inactive_text:  "rgba(212,175,55,0.60)",
  hover_bg:       "rgba(212,175,55,0.14)",
  hover_text:     "rgba(212,175,55,0.96)",
  border:         "rgba(212,175,55,0.28)",   // slightly more visible folder edges
  rim:            "rgba(212,175,55,0.30)",   // brighter drawer rim line
  strip_bg:       "rgba(4,7,18,0.92)",       // deeper, richer dark
};

// ── Nav catalogue ──────────────────────────────────────────────────────────────

interface NavItem { href: string; label: string; adminOnly?: boolean }

const NAV: NavItem[] = [
  { href: "/",              label: "Missão"       },
  { href: "/dashboard",    label: "Painel"        },
  { href: "/ingestion",    label: "Evidências"    },
  { href: "/missions",     label: "Missões"       },
  { href: "/verification", label: "Verificar"     },
  { href: "/compliance",   label: "Conformidade"  },
  { href: "/normative",    label: "Normativo"     },
  { href: "/privacy",      label: "Privacidade"   },
  { href: "/docs",         label: "Docs"          },
  { href: "/agent-config", label: "Modelos"       },
  { href: "/diary",        label: "Diário"        },
  { href: "/m",            label: "Mobile"        },
  { href: "/health",       label: "Health",       adminOnly: true },
];

// ── SVG icons ─────────────────────────────────────────────────────────────────

const IcoFullscreen = () => (
  <svg viewBox="0 0 20 20" fill="none" stroke="currentColor" strokeWidth={1.5} strokeLinecap="round">
    <path d="M3 7V3h4M13 3h4v4M17 13v4h-4M7 17H3v-4" />
  </svg>
);
const IcoExitFullscreen = () => (
  <svg viewBox="0 0 20 20" fill="none" stroke="currentColor" strokeWidth={1.5} strokeLinecap="round">
    <path d="M7 3v4H3M17 7h-4V3M3 13h4v4M13 17v-4h4" />
  </svg>
);
const IcoMenu = () => (
  <svg viewBox="0 0 20 20" fill="none" stroke="currentColor" strokeWidth={1.5} strokeLinecap="round">
    <path d="M3 5h14M3 10h14M3 15h14" />
  </svg>
);
const IcoClose = () => (
  <svg viewBox="0 0 20 20" fill="none" stroke="currentColor" strokeWidth={1.5} strokeLinecap="round">
    <path d="M5 5l10 10M15 5 5 15" />
  </svg>
);
const IcoExit = () => (
  <svg viewBox="0 0 20 20" fill="none" stroke="currentColor" strokeWidth={1.5} strokeLinecap="round">
    <path d="M13 3h4v14h-4M9 13l4-3-4-3M3 10h10" />
  </svg>
);

// ── Fullscreen button ──────────────────────────────────────────────────────────

function FullscreenBtn() {
  const [full, setFull] = useState(false);

  useEffect(() => {
    const fn = () => setFull(!!document.fullscreenElement);
    document.addEventListener("fullscreenchange", fn);
    return () => document.removeEventListener("fullscreenchange", fn);
  }, []);

  const toggle = useCallback(() => {
    if (!document.fullscreenElement) {
      void document.documentElement.requestFullscreen();
    } else {
      void document.exitFullscreen();
    }
  }, []);

  return (
    <button
      type="button"
      onClick={toggle}
      aria-label={full ? "Sair de ecrã inteiro" : "Ecrã inteiro"}
      title={full ? "Sair de ecrã inteiro" : "Ecrã inteiro"}
      className="flex h-7 w-7 shrink-0 items-center justify-center rounded-md text-[rgba(212,175,55,0.65)] transition-colors hover:text-[rgba(212,175,55,0.95)]"
    >
      <span className="h-4 w-4">
        {full ? <IcoExitFullscreen /> : <IcoFullscreen />}
      </span>
    </button>
  );
}

// ── FolderTab (single nav item) ────────────────────────────────────────────────

interface FolderTabProps {
  item: NavItem;
  active: boolean;
  onClick?: () => void;
}

function FolderTab({ item, active, onClick }: FolderTabProps) {
  const [hovered, setHovered] = useState(false);

  return (
    <Link
      href={item.href}
      onClick={onClick}
      aria-current={active ? "page" : undefined}
      onMouseEnter={() => setHovered(true)}
      onMouseLeave={() => setHovered(false)}
      className="relative shrink-0 select-none whitespace-nowrap text-[11px] font-medium tracking-[0.06em] outline-none focus-visible:ring-1 focus-visible:ring-gold-400/60"
      style={{
        // Folder-tab ear shape: one rounded corner (top-left), one sharp (top-right)
        // — mimics a real physical folder label/ear in a filing drawer
        height: "28px",
        padding: "0 12px",
        display: "inline-flex",
        alignItems: "center",
        borderRadius: "6px 0 0 0",
        border: `1px solid ${G.border}`,
        borderBottom: active ? "none" : `1px solid ${G.border}`,
        background: active
          ? G.active_bg
          : hovered
          ? G.hover_bg
          : G.inactive_bg,
        color: active
          ? G.active_text
          : hovered
          ? G.hover_text
          : G.inactive_text,
        // Specular highlight — strong on active (folder ear catching light), soft on hover
        backgroundImage: active
          ? "linear-gradient(180deg, rgba(255,255,255,0.24) 0%, rgba(255,255,255,0.04) 55%, rgba(0,0,0,0) 100%)"
          : hovered
          ? "linear-gradient(180deg, rgba(255,255,255,0.09) 0%, rgba(255,255,255,0) 60%)"
          : "none",
        transition: "background 0.18s ease, color 0.18s ease, border-color 0.18s ease, box-shadow 0.18s ease",
        // Active tab: top glow gives a "lit folder ear" look; no bottom border creates open-folder illusion
        boxShadow: active
          ? "0 -2px 10px rgba(212,175,55,0.18), inset 0 1px 0 rgba(255,255,255,0.2)"
          : hovered
          ? "0 -1px 6px rgba(212,175,55,0.08)"
          : "none",
        // Active tab sits flush with the strip bottom border (marginBottom -1px
        // so it visually overlaps the rim line, creating the "open folder" illusion)
        marginBottom: active ? "-1px" : "0",
        fontWeight: active ? "600" : "500",
        letterSpacing: active ? "0.04em" : "0.06em",
        zIndex: active ? 2 : 1,
      }}
    >
      {item.label}
    </Link>
  );
}

// ── FolderTopbar (main export) ─────────────────────────────────────────────────

export function FolderTopbar() {
  const pathname = usePathname();
  const { isAuthenticated, logout, isReady, user } = useAuth();
  const router = useRouter();
  const [mobileOpen, setMobileOpen] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);
  const isAdmin = user?.role === "admin";

  const visibleItems = NAV.filter((n) => {
    if (n.adminOnly) return isAdmin;
    return true;
  });

  const isActive = (href: string) => {
    if (href === "/") return pathname === "/";
    return pathname === href || pathname.startsWith(`${href}/`);
  };

  const handleLogout = useCallback(async () => {
    await logout();
    router.push("/");
    setMobileOpen(false);
  }, [logout, router]);

  // Auto-scroll the active tab into view on navigation
  useEffect(() => {
    const el = scrollRef.current?.querySelector('[aria-current="page"]') as HTMLElement | null;
    el?.scrollIntoView({ block: "nearest", inline: "center", behavior: "smooth" });
  }, [pathname]);

  return (
    <>
      {/* ── TOPBAR STRIP ──────────────────────────────────────────────────── */}
      <header
        className="fixed inset-x-0 top-0 z-50 flex items-end gap-0"
        style={{
          height: `${TOPBAR_H}px`,
          background: G.strip_bg,
          backdropFilter: "blur(28px)",
          WebkitBackdropFilter: "blur(28px)",
          borderBottom: `1px solid ${G.rim}`,
          // Shadow lifts topbar; inner glow reinforces the "drawer rim"
          boxShadow: "0 4px 32px rgba(0,0,0,0.55), 0 1px 0 rgba(212,175,55,0.18) inset, 0 -1px 0 rgba(212,175,55,0.06) inset",
        }}
      >
        {/* ── Logo ── */}
        <Link
          href="/"
          aria-label="Heillon Legal — Início"
          className="flex shrink-0 items-center gap-2 self-center px-4"
        >
          <span
            className="flex h-7 w-7 items-center justify-center rounded-md text-[13px] font-bold"
            style={{
              background: "linear-gradient(135deg,#EDD97A,#C9A227)",
              color: "#050A18",
              boxShadow: "0 1px 6px rgba(212,175,55,0.35), inset 0 1px 0 rgba(255,255,255,0.25)",
            }}
          >
            H
          </span>
          <div className="hidden flex-col leading-none sm:flex">
            <span className="text-[8px] font-semibold uppercase tracking-[0.28em] text-white/40">
              Legal
            </span>
            <span className="text-[12px] font-semibold tracking-tight text-white/85">
              Heillon
            </span>
          </div>
        </Link>

        {/* ── Divider ── */}
        <span
          className="mx-3 hidden h-4 shrink-0 self-center sm:block"
          style={{ width: "1px", background: "rgba(212,175,55,0.18)" }}
          aria-hidden
        />

        {/* ── Folder tabs — desktop ── */}
        <div
          ref={scrollRef}
          className="hidden flex-1 items-end gap-[3px] overflow-x-auto md:flex"
          style={{
            // Vertically: tabs align to the bottom of the strip
            paddingBottom: "0",
            paddingLeft: "2px",
            // Hide scrollbar but keep scrollability
            scrollbarWidth: "none",
            msOverflowStyle: "none",
          }}
          role="navigation"
          aria-label="Navegação principal"
        >
          {visibleItems.map((item) => (
            <FolderTab
              key={item.href}
              item={item}
              active={isActive(item.href)}
            />
          ))}
        </div>

        {/* ── Right actions ── */}
        <div className="ml-auto flex shrink-0 items-center gap-2 self-center px-3 md:ml-0">
          {/* Auth */}
          {isReady && (
            isAuthenticated ? (
              <button
                type="button"
                onClick={() => void handleLogout()}
                title="Terminar sessão"
                aria-label="Terminar sessão"
                className="hidden h-7 items-center gap-1.5 rounded-md border px-3 text-[11px] font-medium transition-colors md:flex"
                style={{
                  borderColor: "rgba(212,175,55,0.22)",
                  color: "rgba(212,175,55,0.55)",
                }}
              >
                <span className="h-3.5 w-3.5"><IcoExit /></span>
                Sair
              </button>
            ) : (
              <Link
                href="/login"
                className="hidden h-7 items-center rounded-md px-3 text-[11px] font-semibold transition-colors hover:opacity-90 md:flex"
                style={{
                  background: G.active_bg,
                  color: G.active_text,
                  borderRadius: "5px",
                }}
              >
                Entrar
              </Link>
            )
          )}

          {/* Fullscreen */}
          <FullscreenBtn />

          {/* Mobile hamburger */}
          <button
            type="button"
            aria-label={mobileOpen ? "Fechar menu" : "Abrir menu"}
            aria-expanded={mobileOpen}
            aria-controls="mobile-folder-menu"
            onClick={() => setMobileOpen((v) => !v)}
            className="flex h-7 w-7 items-center justify-center rounded-md text-[rgba(212,175,55,0.6)] transition-colors hover:text-[rgba(212,175,55,0.9)] md:hidden"
          >
            <span className="h-4 w-4">
              {mobileOpen ? <IcoClose /> : <IcoMenu />}
            </span>
          </button>
        </div>
      </header>

      {/* ── MOBILE MENU ───────────────────────────────────────────────────── */}
      <AnimatePresence>
        {mobileOpen && (
          <>
            {/* Backdrop */}
            <motion.div
              key="bd"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              transition={{ duration: 0.15 }}
              className="fixed inset-0 z-[48] bg-black/55 backdrop-blur-sm md:hidden"
              onClick={() => setMobileOpen(false)}
              aria-hidden="true"
            />

            {/* Dropdown panel */}
            <motion.nav
              key="menu"
              id="mobile-folder-menu"
              role="dialog"
              aria-label="Menu de navegação"
              aria-modal="true"
              initial={{ opacity: 0, y: -6 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -6 }}
              transition={{ duration: 0.18, ease: "easeOut" }}
              className="fixed inset-x-0 z-[49] md:hidden"
              style={{
                top: `${TOPBAR_H}px`,
                background: "rgba(5,9,20,0.96)",
                backdropFilter: "blur(32px)",
                WebkitBackdropFilter: "blur(32px)",
                borderBottom: `1px solid ${G.rim}`,
                padding: "12px 16px 16px",
              }}
            >
              <div className="flex flex-wrap gap-2">
                {visibleItems.map((item) => (
                  <Link
                    key={item.href}
                    href={item.href}
                    onClick={() => setMobileOpen(false)}
                    aria-current={isActive(item.href) ? "page" : undefined}
                    className="rounded-md px-3 py-1.5 text-[12px] font-medium transition-colors"
                    style={{
                      border: `1px solid ${G.border}`,
                      background: isActive(item.href) ? G.active_bg : G.inactive_bg,
                      color: isActive(item.href) ? G.active_text : G.inactive_text,
                    }}
                  >
                    {item.label}
                  </Link>
                ))}
              </div>

              {/* Auth in mobile */}
              {isReady && (
                <div className="mt-3 flex justify-end">
                  {isAuthenticated ? (
                    <button
                      type="button"
                      onClick={() => void handleLogout()}
                      className="flex items-center gap-1.5 rounded-md px-3 py-1.5 text-[11px]"
                      style={{ color: "rgba(212,175,55,0.55)" }}
                    >
                      <span className="h-3.5 w-3.5"><IcoExit /></span>
                      Terminar sessão
                    </button>
                  ) : (
                    <Link
                      href="/login"
                      onClick={() => setMobileOpen(false)}
                      className="rounded-md px-4 py-1.5 text-[12px] font-semibold"
                      style={{ background: G.active_bg, color: G.active_text }}
                    >
                      Entrar
                    </Link>
                  )}
                </div>
              )}
            </motion.nav>
          </>
        )}
      </AnimatePresence>
    </>
  );
}
