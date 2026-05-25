"use client";

/**
 * FolderSidebar — LiquidGlass Hanging-Folder Navigation
 *
 * Visual concept: each section is a colorful hanging A4 file folder.
 * The folder "ear/tab" sticks up from the top of each item, staggered
 * across three positions (mimicking real filing-cabinet folder tabs).
 * The folder body is LiquidGlass: tinted, blurred, with a specular
 * highlight on the top edge.
 *
 * Fase 20 — Heillon Legal
 */

import { AnimatePresence, motion, useReducedMotion } from "framer-motion";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useCallback, useEffect, useId, useState } from "react";

import { useAuth } from "@/lib/auth-context";

// ── Types ──────────────────────────────────────────────────────────────────────

interface FolderDef {
  href: string;
  label: string;
  icon: React.ReactNode;
  color: string; // hex / rgb accent color
  tourKey?: string;
  adminOnly?: boolean;
}

// ── Inline SVG Icons (no extra dependency) ────────────────────────────────────

const Ico = {
  scale: (
    <svg viewBox="0 0 20 20" fill="none" stroke="currentColor" strokeWidth={1.4} strokeLinecap="round" strokeLinejoin="round">
      <path d="M10 2v2M3 8l7-4 7 4M5 8l-2 5h4L5 8zm10 0l-2 5h4l-2-5zM3 18h14" />
    </svg>
  ),
  grid: (
    <svg viewBox="0 0 20 20" fill="none" stroke="currentColor" strokeWidth={1.4} strokeLinecap="round">
      <rect x="2" y="2" width="7" height="7" rx="1.5" />
      <rect x="11" y="2" width="7" height="7" rx="1.5" />
      <rect x="2" y="11" width="7" height="7" rx="1.5" />
      <rect x="11" y="11" width="7" height="7" rx="1.5" />
    </svg>
  ),
  folder: (
    <svg viewBox="0 0 20 20" fill="none" stroke="currentColor" strokeWidth={1.4} strokeLinecap="round">
      <path d="M2 6.5A1.5 1.5 0 0 1 3.5 5h4.086a1.5 1.5 0 0 1 1.06.44L9.5 6.5H16.5A1.5 1.5 0 0 1 18 8v7a1.5 1.5 0 0 1-1.5 1.5h-13A1.5 1.5 0 0 1 2 15V6.5z" />
    </svg>
  ),
  target: (
    <svg viewBox="0 0 20 20" fill="none" stroke="currentColor" strokeWidth={1.4} strokeLinecap="round">
      <circle cx="10" cy="10" r="7" /><circle cx="10" cy="10" r="3" />
      <path d="M10 2v2M10 16v2M2 10h2M16 10h2" />
    </svg>
  ),
  search: (
    <svg viewBox="0 0 20 20" fill="none" stroke="currentColor" strokeWidth={1.4} strokeLinecap="round">
      <circle cx="8.5" cy="8.5" r="5.5" /><path d="m14 14 3.5 3.5" />
    </svg>
  ),
  shield: (
    <svg viewBox="0 0 20 20" fill="none" stroke="currentColor" strokeWidth={1.4} strokeLinecap="round">
      <path d="M10 2 3.5 5v5c0 4.5 6.5 7.5 6.5 7.5s6.5-3 6.5-7.5V5L10 2z" />
      <path d="m7 10 2 2 4-4" />
    </svg>
  ),
  book: (
    <svg viewBox="0 0 20 20" fill="none" stroke="currentColor" strokeWidth={1.4} strokeLinecap="round">
      <path d="M4 3h10a1 1 0 0 1 1 1v12a1 1 0 0 1-1 1H4a1 1 0 0 1-1-1V4a1 1 0 0 1 1-1z" />
      <path d="M7 7h6M7 10h6M7 13h4" />
    </svg>
  ),
  lock: (
    <svg viewBox="0 0 20 20" fill="none" stroke="currentColor" strokeWidth={1.4} strokeLinecap="round">
      <rect x="4" y="9" width="12" height="9" rx="2" />
      <path d="M7 9V6a3 3 0 0 1 6 0v3" />
      <circle cx="10" cy="13.5" r="1.5" fill="currentColor" stroke="none" />
    </svg>
  ),
  docs: (
    <svg viewBox="0 0 20 20" fill="none" stroke="currentColor" strokeWidth={1.4} strokeLinecap="round">
      <path d="M6 2h8a1 1 0 0 1 1 1v14a1 1 0 0 1-1 1H6a1 1 0 0 1-1-1V3a1 1 0 0 1 1-1z" />
      <path d="M8 6h4M8 9h4M8 12h2" />
    </svg>
  ),
  cpu: (
    <svg viewBox="0 0 20 20" fill="none" stroke="currentColor" strokeWidth={1.4} strokeLinecap="round">
      <rect x="5" y="5" width="10" height="10" rx="1" />
      <path d="M8 5V3M12 5V3M8 17v-2M12 17v-2M5 8H3M5 12H3M15 8h2M15 12h2" />
    </svg>
  ),
  pen: (
    <svg viewBox="0 0 20 20" fill="none" stroke="currentColor" strokeWidth={1.4} strokeLinecap="round">
      <path d="m3 17 4-1 9-9-3-3-9 9-1 4z" /><path d="m13 4 3 3" />
    </svg>
  ),
  mobile: (
    <svg viewBox="0 0 20 20" fill="none" stroke="currentColor" strokeWidth={1.4} strokeLinecap="round">
      <rect x="5" y="2" width="10" height="16" rx="2" />
      <circle cx="10" cy="15" r="0.8" fill="currentColor" stroke="none" />
    </svg>
  ),
  health: (
    <svg viewBox="0 0 20 20" fill="none" stroke="currentColor" strokeWidth={1.4} strokeLinecap="round">
      <path d="M3 10h3l2-5 4 10 2-5h3" />
    </svg>
  ),
  exit: (
    <svg viewBox="0 0 20 20" fill="none" stroke="currentColor" strokeWidth={1.4} strokeLinecap="round">
      <path d="M13 3h4v14h-4M9 13l4-3-4-3M3 10h10" />
    </svg>
  ),
  menu: (
    <svg viewBox="0 0 20 20" fill="none" stroke="currentColor" strokeWidth={1.4} strokeLinecap="round">
      <path d="M3 5h14M3 10h14M3 15h14" />
    </svg>
  ),
  close: (
    <svg viewBox="0 0 20 20" fill="none" stroke="currentColor" strokeWidth={1.4} strokeLinecap="round">
      <path d="M5 5l10 10M15 5 5 15" />
    </svg>
  ),
  chevronLeft: (
    <svg viewBox="0 0 20 20" fill="none" stroke="currentColor" strokeWidth={1.6} strokeLinecap="round">
      <path d="m12 5-6 5 6 5" />
    </svg>
  ),
  chevronRight: (
    <svg viewBox="0 0 20 20" fill="none" stroke="currentColor" strokeWidth={1.6} strokeLinecap="round">
      <path d="m8 5 6 5-6 5" />
    </svg>
  ),
};

// ── Folder catalogue ───────────────────────────────────────────────────────────

const FOLDERS: FolderDef[] = [
  { href: "/",             label: "Missão",       icon: Ico.scale,  color: "#F59E0B" },
  { href: "/dashboard",   label: "Painel",        icon: Ico.grid,   color: "#3B82F6" },
  { href: "/ingestion",   label: "Evidências",    icon: Ico.folder, color: "#EAB308", tourKey: "evidencias-link" },
  { href: "/missions",    label: "Missões",       icon: Ico.target, color: "#EF4444" },
  { href: "/verification",label: "Verificar",     icon: Ico.search, color: "#8B5CF6", tourKey: "verify-link" },
  { href: "/compliance",  label: "Conformidade",  icon: Ico.shield, color: "#10B981" },
  { href: "/normative",   label: "Normativo",     icon: Ico.book,   color: "#06B6D4", tourKey: "normative-link" },
  { href: "/privacy",     label: "Privacidade",   icon: Ico.lock,   color: "#EC4899" },
  { href: "/docs",        label: "Docs",          icon: Ico.docs,   color: "#6366F1", tourKey: "docs-link" },
  { href: "/agent-config",label: "Modelos",       icon: Ico.cpu,    color: "#94A3B8" },
  { href: "/diary",       label: "Diário",        icon: Ico.pen,    color: "#F97316" },
  { href: "/m",           label: "Mobile",        icon: Ico.mobile, color: "#14B8A6" },
  { href: "/health",      label: "Health",        icon: Ico.health, color: "#64748B", adminOnly: true },
];

// Tab ear positions cycle: left / center-left / center-right
const TAB_OFFSETS = [10, 50, 90]; // px from left edge of folder body

// ── Helper: hex → rgba ────────────────────────────────────────────────────────

function hexToRgba(hex: string, alpha: number): string {
  const h = hex.replace("#", "");
  const r = parseInt(h.slice(0, 2), 16);
  const g = parseInt(h.slice(2, 4), 16);
  const b = parseInt(h.slice(4, 6), 16);
  return `rgba(${r},${g},${b},${alpha})`;
}

// ── FolderItem ─────────────────────────────────────────────────────────────────

interface FolderItemProps {
  folder: FolderDef;
  index: number;
  expanded: boolean;
  isActive: boolean;
  onClick?: () => void;
}

function FolderItem({ folder, index, expanded, isActive, onClick }: FolderItemProps) {
  const reduced = useReducedMotion();
  const tabOffset = TAB_OFFSETS[index % TAB_OFFSETS.length];
  const { color } = folder;

  const bodyBg       = hexToRgba(color, isActive ? 0.18 : 0.07);
  const bodyBgHover  = hexToRgba(color, 0.16);
  const borderColor  = hexToRgba(color, isActive ? 0.55 : 0.22);
  const tabBg        = hexToRgba(color, isActive ? 0.85 : 0.55);
  const glowColor    = hexToRgba(color, 0.35);
  const textColor    = isActive ? "#ffffff" : hexToRgba(color, 0.9);

  const TAB_H   = 10; // tab ear height in px
  const TAB_W   = 52; // tab ear width in px

  return (
    <motion.div
      className="relative"
      style={{ paddingTop: `${TAB_H}px`, marginBottom: "2px" }}
      initial={reduced ? false : { opacity: 0, x: -16 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ delay: index * 0.04, duration: 0.3, ease: "easeOut" }}
    >
      {/* ── Folder tab (ear sticking above) ── */}
      <div
        className="absolute top-0"
        style={{
          left: expanded ? `${tabOffset}px` : "8px",
          width: expanded ? `${TAB_W}px` : "40px",
          height: `${TAB_H + 2}px`,
          background: tabBg,
          borderRadius: "5px 5px 0 0",
          backdropFilter: "blur(12px)",
          WebkitBackdropFilter: "blur(12px)",
          transition: "left 0.3s ease, width 0.3s ease, background 0.25s ease",
          boxShadow: isActive ? `0 -2px 8px ${glowColor}` : "none",
        }}
        aria-hidden="true"
      />

      {/* ── Folder body ── */}
      <Link
        href={folder.href}
        onClick={onClick}
        {...(folder.tourKey ? { "data-tour": folder.tourKey } : {})}
        aria-current={isActive ? "page" : undefined}
        className="group relative flex items-center gap-3 overflow-hidden rounded-b-xl rounded-tr-xl outline-none focus-visible:ring-2 transition-all duration-200"
        style={{
          paddingLeft: expanded ? "14px" : "14px",
          paddingRight: expanded ? "14px" : "14px",
          paddingTop: "10px",
          paddingBottom: "10px",
          background: bodyBg,
          border: `1px solid ${borderColor}`,
          borderTop: `1px solid ${hexToRgba(color, isActive ? 0.6 : 0.3)}`,
          backdropFilter: "blur(20px)",
          WebkitBackdropFilter: "blur(20px)",
          boxShadow: isActive
            ? `0 4px 24px ${glowColor}, inset 0 1px 0 rgba(255,255,255,0.1)`
            : "inset 0 1px 0 rgba(255,255,255,0.04)",
          // Specular highlight gradient on top edge
          backgroundImage: `linear-gradient(160deg, rgba(255,255,255,0.07) 0%, rgba(255,255,255,0.01) 45%, ${hexToRgba(color, 0.05)} 100%)`,
        }}
      >
        {/* Hover overlay (separate from Framer to avoid z-index issues) */}
        <span
          className="pointer-events-none absolute inset-0 opacity-0 transition-opacity duration-200 group-hover:opacity-100"
          style={{ background: bodyBgHover }}
          aria-hidden="true"
        />

        {/* Icon */}
        <span
          className="relative z-10 flex h-5 w-5 shrink-0 items-center justify-center"
          style={{ color: textColor, transition: "color 0.2s" }}
        >
          {folder.icon}
        </span>

        {/* Label */}
        <AnimatePresence initial={false}>
          {expanded && (
            <motion.span
              key="label"
              initial={{ opacity: 0, width: 0 }}
              animate={{ opacity: 1, width: "auto" }}
              exit={{ opacity: 0, width: 0 }}
              transition={{ duration: 0.2, ease: "easeOut" }}
              className="relative z-10 overflow-hidden whitespace-nowrap text-[12.5px] font-medium tracking-wide"
              style={{ color: textColor }}
            >
              {folder.label}
            </motion.span>
          )}
        </AnimatePresence>
      </Link>
    </motion.div>
  );
}

// ── FolderSidebar (main export) ────────────────────────────────────────────────

export function FolderSidebar() {
  const [expanded, setExpanded] = useState(true);
  const [mobileOpen, setMobileOpen] = useState(false);

  // Sync sidebar width as a CSS custom property so ConditionalAppShell can
  // adjust the content area's padding-left smoothly.
  useEffect(() => {
    document.documentElement.style.setProperty(
      "--sidebar-w",
      `${expanded ? SIDEBAR_EXPANDED_W : SIDEBAR_COLLAPSED_W}px`,
    );
  }, [expanded]);
  const pathname = usePathname();
  const { isAuthenticated, logout, isReady, user } = useAuth();
  const router = useRouter();
  const reduced = useReducedMotion();
  const navId = useId();

  const isAdmin = user?.role === "admin";

  const visibleFolders = FOLDERS.filter((f) => {
    if (f.adminOnly) return isAdmin;
    return true;
  });

  const handleLogout = useCallback(async () => {
    await logout();
    router.push("/");
    setMobileOpen(false);
  }, [logout, router]);

  const isActive = (href: string) => {
    if (href === "/") return pathname === "/";
    return pathname === href || pathname.startsWith(`${href}/`);
  };

  // ── SIDEBAR WIDTH ──────────────────────────────────────────────────────────
  const EXPANDED_W  = 220;
  const COLLAPSED_W = 64;
  const sidebarW = expanded ? EXPANDED_W : COLLAPSED_W;

  // ── SHARED FOLDER LIST ──────────────────────────────────────────────────────
  const folderList = (inDrawer = false) => (
    <nav aria-label="Navegação principal" id={navId}>
      <div className="flex flex-col gap-0">
        {visibleFolders.map((folder, idx) => (
          <FolderItem
            key={folder.href}
            folder={folder}
            index={idx}
            expanded={inDrawer || expanded}
            isActive={isActive(folder.href)}
            onClick={inDrawer ? () => setMobileOpen(false) : undefined}
          />
        ))}
      </div>
    </nav>
  );

  return (
    <>
      {/* ── DESKTOP SIDEBAR ───────────────────────────────────────────────── */}
      <motion.aside
        aria-label="Barra lateral"
        className="fixed inset-y-0 left-0 z-40 hidden flex-col lg:flex"
        animate={{ width: sidebarW }}
        initial={false}
        transition={reduced ? { duration: 0 } : { type: "spring", stiffness: 300, damping: 35 }}
        style={{
          background: "rgba(5,9,20,0.72)",
          backdropFilter: "blur(32px)",
          WebkitBackdropFilter: "blur(32px)",
          borderRight: "1px solid rgba(255,255,255,0.07)",
          boxShadow: "4px 0 32px rgba(0,0,0,0.4)",
        }}
      >
        {/* ── Logo ── */}
        <div
          className="flex items-center gap-3 px-4 py-5"
          style={{ borderBottom: "1px solid rgba(255,255,255,0.06)" }}
        >
          <Link
            href="/"
            className="flex items-center gap-3"
            aria-label="Heillon Legal — Página inicial"
          >
            {/* Gold H badge */}
            <span
              className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg font-bold text-deep-space-900"
              style={{ background: "linear-gradient(135deg,#F0E0A0,#D4AF37)" }}
            >
              H
            </span>
            <AnimatePresence initial={false}>
              {expanded && (
                <motion.div
                  key="wordmark"
                  initial={{ opacity: 0, width: 0 }}
                  animate={{ opacity: 1, width: "auto" }}
                  exit={{ opacity: 0, width: 0 }}
                  transition={{ duration: 0.2 }}
                  className="flex flex-col leading-tight overflow-hidden"
                >
                  <span className="whitespace-nowrap text-[10px] font-semibold uppercase tracking-[0.22em] text-white/45">
                    Legal
                  </span>
                  <span className="whitespace-nowrap font-semibold tracking-tight text-white">
                    Heillon
                  </span>
                </motion.div>
              )}
            </AnimatePresence>
          </Link>
        </div>

        {/* ── Folder list (scrollable) ── */}
        <div className="flex-1 overflow-y-auto overflow-x-hidden px-3 py-4 scrollbar-thin">
          {folderList()}
        </div>

        {/* ── Footer: auth + collapse toggle ── */}
        <div
          className="px-3 py-4 flex flex-col gap-2"
          style={{ borderTop: "1px solid rgba(255,255,255,0.06)" }}
        >
          {/* Auth actions */}
          {isReady && (
            <AnimatePresence initial={false}>
              {isAuthenticated ? (
                <motion.button
                  key="logout"
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  exit={{ opacity: 0 }}
                  type="button"
                  onClick={() => void handleLogout()}
                  className="relative flex items-center gap-3 rounded-xl px-3 py-2 text-[12px] text-white/40 transition-colors hover:bg-white/5 hover:text-white/70"
                  title="Terminar sessão"
                >
                  <span className="flex h-5 w-5 shrink-0 items-center justify-center">
                    {Ico.exit}
                  </span>
                  <AnimatePresence initial={false}>
                    {expanded && (
                      <motion.span
                        key="lbl"
                        initial={{ opacity: 0, width: 0 }}
                        animate={{ opacity: 1, width: "auto" }}
                        exit={{ opacity: 0, width: 0 }}
                        className="overflow-hidden whitespace-nowrap"
                      >
                        Sair
                      </motion.span>
                    )}
                  </AnimatePresence>
                </motion.button>
              ) : (
                <Link
                  key="login"
                  href="/login"
                  className="relative flex items-center gap-3 rounded-xl px-3 py-2 text-[12px] text-gold-400/70 transition-colors hover:bg-gold-500/10 hover:text-gold-300"
                  title="Entrar"
                >
                  <span
                    className="flex h-5 w-5 shrink-0 items-center justify-center"
                    style={{ color: "#D4AF37" }}
                  >
                    {Ico.grid}
                  </span>
                  <AnimatePresence initial={false}>
                    {expanded && (
                      <motion.span
                        key="lbl"
                        initial={{ opacity: 0, width: 0 }}
                        animate={{ opacity: 1, width: "auto" }}
                        exit={{ opacity: 0, width: 0 }}
                        className="overflow-hidden whitespace-nowrap"
                      >
                        Entrar
                      </motion.span>
                    )}
                  </AnimatePresence>
                </Link>
              )}
            </AnimatePresence>
          )}

          {/* Collapse / Expand toggle */}
          <button
            type="button"
            onClick={() => setExpanded((v) => !v)}
            aria-label={expanded ? "Recolher sidebar" : "Expandir sidebar"}
            className="flex items-center gap-3 rounded-xl px-3 py-2 text-[11px] text-white/25 transition-colors hover:bg-white/5 hover:text-white/50"
            title={expanded ? "Recolher" : "Expandir"}
          >
            <span className="flex h-5 w-5 shrink-0 items-center justify-center">
              {expanded ? Ico.chevronLeft : Ico.chevronRight}
            </span>
            <AnimatePresence initial={false}>
              {expanded && (
                <motion.span
                  key="lbl"
                  initial={{ opacity: 0, width: 0 }}
                  animate={{ opacity: 1, width: "auto" }}
                  exit={{ opacity: 0, width: 0 }}
                  className="overflow-hidden whitespace-nowrap"
                >
                  Recolher
                </motion.span>
              )}
            </AnimatePresence>
          </button>
        </div>
      </motion.aside>

      {/* ── MOBILE: top strip + hamburger ─────────────────────────────────── */}
      <header
        className="fixed inset-x-0 top-0 z-40 flex items-center justify-between px-4 py-3 lg:hidden"
        style={{
          background: "rgba(5,9,20,0.82)",
          backdropFilter: "blur(24px)",
          WebkitBackdropFilter: "blur(24px)",
          borderBottom: "1px solid rgba(255,255,255,0.07)",
        }}
      >
        <Link href="/" className="flex items-center gap-2" aria-label="Início">
          <span
            className="flex h-8 w-8 items-center justify-center rounded-lg text-sm font-bold text-deep-space-900"
            style={{ background: "linear-gradient(135deg,#F0E0A0,#D4AF37)" }}
          >
            H
          </span>
          <span className="text-sm font-semibold text-white">Heillon Legal</span>
        </Link>

        <div className="flex items-center gap-2">
          <Link
            href="/ingestion"
            className="rounded-full px-3 py-1.5 text-[11px] font-semibold text-deep-space-900"
            style={{ background: "linear-gradient(135deg,#F0E0A0,#D4AF37)" }}
          >
            + Nova análise
          </Link>
          <button
            type="button"
            aria-label={mobileOpen ? "Fechar menu" : "Abrir menu"}
            aria-expanded={mobileOpen}
            aria-controls="mobile-folder-drawer"
            onClick={() => setMobileOpen((v) => !v)}
            className="flex h-9 w-9 items-center justify-center rounded-xl border border-white/10 text-white/70 transition-colors hover:border-white/20 hover:text-white"
          >
            {mobileOpen ? Ico.close : Ico.menu}
          </button>
        </div>
      </header>

      {/* ── MOBILE DRAWER ─────────────────────────────────────────────────── */}
      <AnimatePresence>
        {mobileOpen && (
          <>
            {/* Backdrop */}
            <motion.div
              key="backdrop"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              transition={{ duration: 0.18 }}
              className="fixed inset-0 z-[45] bg-black/60 backdrop-blur-sm lg:hidden"
              onClick={() => setMobileOpen(false)}
              aria-hidden="true"
            />

            {/* Drawer */}
            <motion.div
              key="drawer"
              id="mobile-folder-drawer"
              role="dialog"
              aria-label="Menu de navegação"
              aria-modal="true"
              initial={{ x: "-100%" }}
              animate={{ x: 0 }}
              exit={{ x: "-100%" }}
              transition={
                reduced
                  ? { duration: 0 }
                  : { type: "spring", stiffness: 320, damping: 36 }
              }
              className="fixed inset-y-0 left-0 z-[50] flex w-72 flex-col lg:hidden"
              style={{
                background: "rgba(5,9,20,0.92)",
                backdropFilter: "blur(32px)",
                WebkitBackdropFilter: "blur(32px)",
                borderRight: "1px solid rgba(255,255,255,0.08)",
              }}
            >
              {/* Drawer header */}
              <div
                className="flex items-center justify-between px-4 py-4"
                style={{ borderBottom: "1px solid rgba(255,255,255,0.07)" }}
              >
                <div className="flex items-center gap-3">
                  <span
                    className="flex h-9 w-9 items-center justify-center rounded-lg font-bold text-deep-space-900"
                    style={{ background: "linear-gradient(135deg,#F0E0A0,#D4AF37)" }}
                  >
                    H
                  </span>
                  <div className="flex flex-col leading-tight">
                    <span className="text-[10px] font-semibold uppercase tracking-[0.22em] text-white/45">Legal</span>
                    <span className="font-semibold tracking-tight text-white">Heillon</span>
                  </div>
                </div>
                <button
                  type="button"
                  aria-label="Fechar menu"
                  onClick={() => setMobileOpen(false)}
                  className="flex h-8 w-8 items-center justify-center rounded-lg text-white/40 transition-colors hover:text-white"
                >
                  {Ico.close}
                </button>
              </div>

              {/* Drawer folders */}
              <div className="flex-1 overflow-y-auto px-3 py-4">
                {folderList(true)}
              </div>

              {/* Drawer footer */}
              <div
                className="px-3 py-4"
                style={{ borderTop: "1px solid rgba(255,255,255,0.06)" }}
              >
                {isReady && (
                  isAuthenticated ? (
                    <button
                      type="button"
                      onClick={() => void handleLogout()}
                      className="flex w-full items-center gap-3 rounded-xl px-3 py-2 text-[12px] text-white/40 transition-colors hover:bg-white/5 hover:text-white/70"
                    >
                      <span className="flex h-5 w-5 items-center justify-center">{Ico.exit}</span>
                      Terminar sessão
                    </button>
                  ) : (
                    <Link
                      href="/login"
                      onClick={() => setMobileOpen(false)}
                      className="flex items-center gap-3 rounded-xl px-3 py-2 text-[12px] text-gold-400/80 transition-colors hover:bg-gold-500/10"
                    >
                      <span className="flex h-5 w-5 items-center justify-center" style={{ color: "#D4AF37" }}>{Ico.grid}</span>
                      Entrar na plataforma
                    </Link>
                  )
                )}
              </div>
            </motion.div>
          </>
        )}
      </AnimatePresence>
    </>
  );
}

// ── Main content offset hook (used in layout to shift content right) ───────────
export const SIDEBAR_EXPANDED_W  = 220;
export const SIDEBAR_COLLAPSED_W = 64;
