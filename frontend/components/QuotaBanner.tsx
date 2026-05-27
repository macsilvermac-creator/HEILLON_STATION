"use client";

/**
 * QuotaBanner — discreet, non-intrusive banner showing free-tier status.
 *
 * Renders ONLY when:
 * - user is authenticated AND
 * - tier is "free" AND
 * - either usage > 70% OR the banner has not been dismissed this session.
 *
 * The CTA "Ver planos" links to the EXTERNAL marketing site (not inside the
 * system). The system has zero pricing UI per product policy.
 */

import Link from "next/link";
import { useEffect, useState } from "react";

import { useAuth } from "@/lib/auth-context";
import { fetchMyQuota, quotaUsagePct, type QuotaSnapshot } from "@/lib/api";

const DISMISS_STORAGE_KEY = "heillon_quota_banner_dismissed_until";
const DISMISS_HOURS = 24;
const EXTERNAL_PLANS_URL = process.env.NEXT_PUBLIC_PLANS_URL ?? "https://heillon.com/planos";

export function QuotaBanner() {
  const { isAuthenticated, isReady } = useAuth();
  const [snap, setSnap] = useState<QuotaSnapshot | null>(null);
  const [dismissed, setDismissed] = useState(false);

  useEffect(() => {
    if (!isReady || !isAuthenticated) return;

    // Honor session dismissal
    try {
      const stored = localStorage.getItem(DISMISS_STORAGE_KEY);
      if (stored) {
        const until = parseInt(stored, 10);
        if (Date.now() < until) {
          setDismissed(true);
          return;
        }
      }
    } catch {
      /* localStorage unavailable — ignore */
    }

    let cancelled = false;
    fetchMyQuota()
      .then((q) => {
        if (!cancelled) setSnap(q);
      })
      .catch(() => {
        // Quota endpoint failure is silent — banner just doesn't render
      });
    return () => {
      cancelled = true;
    };
  }, [isReady, isAuthenticated]);

  const handleDismiss = () => {
    try {
      const until = Date.now() + DISMISS_HOURS * 60 * 60 * 1000;
      localStorage.setItem(DISMISS_STORAGE_KEY, String(until));
    } catch {
      /* ignore */
    }
    setDismissed(true);
  };

  if (!isReady || !isAuthenticated || !snap || dismissed) return null;
  if (snap.tier !== "free") return null;

  const pct = quotaUsagePct(snap) ?? 0;
  const isHigh = pct >= 0.7;
  const isExceeded = snap.is_exceeded;

  // Only show banner when usage is meaningful (≥70%) or already exceeded
  if (!isHigh && !isExceeded) return null;

  const variant = isExceeded
    ? {
        bg: "bg-rose-500/10",
        border: "border-rose-500/30",
        text: "text-rose-200",
        label: `Limite atingido — ${snap.used_in_period}/${snap.monthly_hdr_limit} HDRs`,
      }
    : {
        bg: "bg-gold-400/8",
        border: "border-gold-400/30",
        text: "text-gold-200",
        label: `Plano Free — ${snap.used_in_period}/${snap.monthly_hdr_limit} HDRs este mês`,
      };

  return (
    <div
      role="status"
      aria-live="polite"
      className={`relative z-30 border-b ${variant.bg} ${variant.border} px-4 py-2.5`}
    >
      <div className="mx-auto flex max-w-6xl items-center justify-between gap-4 text-xs">
        <p className={`${variant.text} font-medium`}>{variant.label}</p>
        <div className="flex items-center gap-3">
          <Link
            href={EXTERNAL_PLANS_URL}
            target="_blank"
            rel="noopener noreferrer"
            className="rounded-md border border-gold-400/50 bg-gold-400/10 px-3 py-1 text-gold-200 transition hover:bg-gold-400/20 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-gold-400/60"
          >
            Ver planos →
          </Link>
          <button
            type="button"
            onClick={handleDismiss}
            aria-label="Dispensar aviso de quota"
            className="text-white/45 transition hover:text-white/80 focus-visible:outline-none"
          >
            ✕
          </button>
        </div>
      </div>
    </div>
  );
}
