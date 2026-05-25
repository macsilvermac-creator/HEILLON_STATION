"use client";

import { AnimatePresence, useScroll, motion, useTransform } from "framer-motion";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";

import { useAuth } from "@/lib/auth-context";

const navLinks = [
  { href: "/", label: "Missão" },
  { href: "/m", label: "Mobile" },
  { href: "/diary", label: "Diário" },
  { href: "/compliance", label: "Conformidade" },
  { href: "/privacy", label: "Privacidade" },
  { href: "/docs", label: "Docs", tour: "docs-link" },
  { href: "/normative", label: "Normativo", tour: "normative-link" },
  { href: "/verification", label: "Verificar", tour: "verify-link" },
  { href: "/ingestion", label: "Evidências" },
  { href: "/agent-config", label: "Modelos" },
];

export function Navbar() {
  const { scrollYProgress } = useScroll();
  const barWidth = useTransform(scrollYProgress, [0, 1], ["0%", "100%"]);
  const { isAuthenticated, logout, isReady, user } = useAuth();
  const isAdmin = user?.role === "admin";
  const router = useRouter();
  const [mobileOpen, setMobileOpen] = useState(false);

  return (
    <nav className="fixed left-1/2 top-4 z-[100] w-[95%] max-w-5xl -translate-x-1/2">
      <div className="glass-card px-6 py-3">
        <div className="flex items-center justify-between gap-6">
          <Link href="/" className="flex items-center gap-2" data-cursor-hover>
            <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-gold-500">
              <span className="text-sm font-bold text-deep-space-900">H</span>
            </div>
            <div className="flex flex-col leading-tight">
              <span className="text-[11px] font-semibold uppercase tracking-[0.2em] text-white/55">Legal</span>
              <span className="font-semibold tracking-tight text-white">Heillon</span>
            </div>
          </Link>

          <div className="hidden items-center gap-1 md:flex">
            {navLinks.map((link) => (
              <Link
                key={link.href}
                href={link.href}
                data-cursor-hover
                {...("tour" in link && link.tour ? { "data-tour": link.tour } : {})}
                className="rounded-full px-3 py-2 text-xs text-white/60 transition-colors duration-300 hover:bg-white/5 hover:text-white"
              >
                {link.label}
              </Link>
            ))}
          </div>

          <div className="flex items-center gap-2">
            {!isReady ? (
              <span className="hidden h-9 w-[7.5rem] rounded-full bg-white/5 sm:block" aria-hidden />
            ) : isAuthenticated ? (
              <>
                <Link
                  href="/dashboard"
                  className="btn-glass hidden rounded-full px-4 py-2 text-xs sm:inline-flex"
                  data-cursor-hover
                >
                  Painel
                </Link>
                {isAdmin ? (
                  <Link
                    href="/health"
                    className="hidden rounded-full px-3 py-2 text-xs text-white/50 transition-colors hover:text-gold-400 sm:inline-flex"
                    data-cursor-hover
                  >
                    Health
                  </Link>
                ) : null}
                <button
                  type="button"
                  className="hidden rounded-full border border-white/15 px-3 py-2 text-xs text-white/70 transition-colors hover:border-white/25 hover:text-white sm:inline-flex"
                  data-cursor-hover
                  onClick={() => {
                    void logout();
                    router.push("/");
                  }}
                >
                  Sair
                </button>
              </>
            ) : (
              <Link
                href="/login"
                className="hidden rounded-full border border-gold-500/35 bg-gold-500/10 px-4 py-2 text-xs text-gold-200 transition-colors hover:bg-gold-500/20 sm:inline-flex"
                data-cursor-hover
              >
                Entrar
              </Link>
            )}
            <Link href="/ingestion" className="btn-gold text-xs sm:inline-flex md:text-sm" data-cursor-hover>
              Nova análise
            </Link>

            {/* Mobile menu toggle */}
            <button
              type="button"
              aria-label={mobileOpen ? "Fechar menu" : "Abrir menu"}
              aria-expanded={mobileOpen}
              aria-controls="mobile-nav-drawer"
              className="ml-1 flex h-9 w-9 items-center justify-center rounded-full border border-white/15 text-white/70 transition-colors hover:border-white/25 hover:text-white md:hidden"
              onClick={() => setMobileOpen((v) => !v)}
            >
              <span className="sr-only">{mobileOpen ? "Fechar" : "Menu"}</span>
              <svg
                aria-hidden
                className="h-4 w-4"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
                strokeWidth={2}
              >
                {mobileOpen ? (
                  <>
                    <line x1="18" y1="6" x2="6" y2="18" />
                    <line x1="6" y1="6" x2="18" y2="18" />
                  </>
                ) : (
                  <>
                    <line x1="3" y1="8" x2="21" y2="8" />
                    <line x1="3" y1="16" x2="21" y2="16" />
                  </>
                )}
              </svg>
            </button>
          </div>
        </div>

        <div className="mt-3 h-[2px] w-full overflow-hidden rounded-full bg-white/5">
          <motion.div style={{ width: barWidth }} className="h-full bg-gradient-to-r from-gold-700 via-gold-400 to-white/70" />
        </div>
      </div>

      {/* Mobile drawer — AnimatePresence for accessible enter/exit transitions */}
      <AnimatePresence>
        {mobileOpen && (
          <motion.div
            id="mobile-nav-drawer"
            role="dialog"
            aria-label="Menu de navegação"
            initial={{ opacity: 0, y: -8 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -8 }}
            transition={{ duration: 0.18 }}
            className="glass-card mt-3 px-5 py-4 md:hidden"
          >
            <div className="flex flex-wrap gap-2">
              {navLinks.map((link) => (
                <Link
                  key={link.href}
                  href={link.href}
                  data-cursor-hover
                  {...("tour" in link && link.tour ? { "data-tour": link.tour } : {})}
                  className="rounded-full border border-white/10 px-4 py-2 text-[11px] text-white/70"
                  onClick={() => setMobileOpen(false)}
                >
                  {link.label}
                </Link>
              ))}
              {isReady ? (
                isAuthenticated ? (
                  <>
                    <Link
                      href="/dashboard"
                      className="rounded-full border border-gold-500/30 px-4 py-2 text-[11px] text-gold-200"
                      onClick={() => setMobileOpen(false)}
                    >
                      Painel
                    </Link>
                    <button
                      type="button"
                      className="rounded-full border border-white/15 px-4 py-2 text-[11px] text-white/70"
                      onClick={() => {
                        setMobileOpen(false);
                        void logout();
                        router.push("/");
                      }}
                    >
                      Sair
                    </button>
                  </>
                ) : (
                  <Link
                    href="/login"
                    className="rounded-full border border-gold-500/30 px-4 py-2 text-[11px] text-gold-200"
                    onClick={() => setMobileOpen(false)}
                  >
                    Entrar
                  </Link>
                )
              ) : null}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </nav>
  );
}
