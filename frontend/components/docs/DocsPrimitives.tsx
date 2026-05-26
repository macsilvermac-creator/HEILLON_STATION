"use client";

/**
 * DocsPrimitives — componentes visuais reutilizáveis para a Central de Documentação.
 *
 * Inclui: Step, ScreenFrame, Callout, FlowDiagram, Badge, StatCard, RegTable.
 * Todos usam a paleta gold / deep-space do Heillon Legal.
 */

import { type ReactNode } from "react";

// ── Callout ────────────────────────────────────────────────────────────────────

type CalloutVariant = "info" | "warning" | "danger" | "success" | "tip";

const CALLOUT_STYLES: Record<CalloutVariant, { border: string; bg: string; icon: string; label: string }> = {
  info:    { border: "border-blue-400/40",   bg: "bg-blue-400/8",   icon: "ℹ",  label: "Nota" },
  warning: { border: "border-amber-400/50",  bg: "bg-amber-400/8",  icon: "⚠",  label: "Atenção" },
  danger:  { border: "border-red-400/50",    bg: "bg-red-400/8",    icon: "🚨", label: "Crítico" },
  success: { border: "border-emerald-400/40",bg: "bg-emerald-400/8",icon: "✓",  label: "OK" },
  tip:     { border: "border-gold-400/40",   bg: "bg-gold-400/6",   icon: "💡", label: "Dica" },
};

export function Callout({
  variant = "info",
  title,
  children,
}: {
  variant?: CalloutVariant;
  title?: string;
  children: ReactNode;
}) {
  const s = CALLOUT_STYLES[variant];
  return (
    <div className={`my-5 rounded-xl border ${s.border} ${s.bg} px-5 py-4`}>
      <p className="mb-1 flex items-center gap-2 text-[11px] font-semibold uppercase tracking-widest text-white/60">
        <span aria-hidden>{s.icon}</span>
        {title ?? s.label}
      </p>
      <div className="text-[13px] leading-relaxed text-white/80">{children}</div>
    </div>
  );
}

// ── Step ───────────────────────────────────────────────────────────────────────

export function Steps({ children }: { children: ReactNode }) {
  return <ol className="my-6 space-y-4 pl-0">{children}</ol>;
}

export function Step({
  n,
  title,
  children,
}: {
  n: number;
  title: string;
  children: ReactNode;
}) {
  return (
    <li className="flex gap-4">
      <span
        aria-hidden
        className="mt-0.5 flex h-7 w-7 shrink-0 items-center justify-center rounded-full text-[12px] font-bold"
        style={{
          background: "linear-gradient(135deg,#EDD97A,#C9A227)",
          color: "#050A18",
        }}
      >
        {n}
      </span>
      <div className="min-w-0 flex-1 pt-0.5">
        <p className="font-semibold text-white">{title}</p>
        <div className="mt-1 text-[13px] leading-relaxed text-white/72">{children}</div>
      </div>
    </li>
  );
}

// ── ScreenFrame ────────────────────────────────────────────────────────────────
// Simula um mockup de interface — representa visualmente como a UI aparece

export function ScreenFrame({
  title,
  url,
  children,
}: {
  title?: string;
  url?: string;
  children: ReactNode;
}) {
  return (
    <figure className="my-6 overflow-hidden rounded-2xl border border-white/12 bg-[#040810] shadow-2xl">
      {/* Barra do browser */}
      <div className="flex items-center gap-3 border-b border-white/8 bg-[#080d1f] px-4 py-2.5">
        <span className="flex gap-1.5" aria-hidden>
          <span className="h-2.5 w-2.5 rounded-full bg-red-500/70" />
          <span className="h-2.5 w-2.5 rounded-full bg-amber-400/70" />
          <span className="h-2.5 w-2.5 rounded-full bg-emerald-400/70" />
        </span>
        {url && (
          <span className="flex-1 truncate rounded-md bg-white/[0.04] px-3 py-1 text-center text-[11px] text-white/40">
            {url}
          </span>
        )}
        {title && !url && (
          <span className="text-[11px] font-medium text-white/40">{title}</span>
        )}
      </div>
      {/* Conteúdo */}
      <div className="p-4 text-[12px]">{children}</div>
    </figure>
  );
}

// ── FlowStep / FlowDiagram ─────────────────────────────────────────────────────

export function FlowDiagram({ steps }: { steps: { icon: string; label: string; sub?: string }[] }) {
  return (
    <div className="my-6 flex flex-wrap items-center gap-0">
      {steps.map((s, i) => (
        <div key={i} className="flex items-center">
          <div className="flex flex-col items-center gap-1 rounded-xl border border-white/10 bg-white/[0.03] px-4 py-3 text-center">
            <span className="text-xl" aria-hidden>{s.icon}</span>
            <span className="text-[12px] font-semibold text-white/88">{s.label}</span>
            {s.sub && <span className="text-[10px] text-white/45">{s.sub}</span>}
          </div>
          {i < steps.length - 1 && (
            <span className="mx-1 text-[18px] text-gold-400/60" aria-hidden>→</span>
          )}
        </div>
      ))}
    </div>
  );
}

// ── Badge ──────────────────────────────────────────────────────────────────────

type BadgeVariant = "gold" | "green" | "blue" | "red" | "gray";

const BADGE_STYLES: Record<BadgeVariant, string> = {
  gold:  "border-gold-400/40 bg-gold-400/10 text-gold-300",
  green: "border-emerald-400/40 bg-emerald-400/8 text-emerald-300",
  blue:  "border-blue-400/40 bg-blue-400/8 text-blue-300",
  red:   "border-red-400/40 bg-red-400/8 text-red-300",
  gray:  "border-white/15 bg-white/[0.04] text-white/60",
};

export function Badge({ variant = "gray", children }: { variant?: BadgeVariant; children: ReactNode }) {
  return (
    <span className={`inline-flex items-center rounded-md border px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wider ${BADGE_STYLES[variant]}`}>
      {children}
    </span>
  );
}

// ── StatCard ───────────────────────────────────────────────────────────────────

export function StatGrid({ children }: { children: ReactNode }) {
  return <div className="my-6 grid grid-cols-2 gap-3 sm:grid-cols-4">{children}</div>;
}

export function StatCard({ value, label, icon }: { value: string; label: string; icon?: string }) {
  return (
    <div className="flex flex-col items-center gap-1 rounded-xl border border-white/10 bg-white/[0.03] px-3 py-4 text-center">
      {icon && <span className="text-xl" aria-hidden>{icon}</span>}
      <span
        className="text-2xl font-bold"
        style={{ background: "linear-gradient(135deg,#EDD97A,#C9A227)", WebkitBackgroundClip: "text", WebkitTextFillColor: "transparent" }}
      >
        {value}
      </span>
      <span className="text-[11px] text-white/55">{label}</span>
    </div>
  );
}

// ── RegTable ───────────────────────────────────────────────────────────────────

export interface RegRow {
  jurisdiction: string;
  flag: string;
  diplomas: string;
  status: "implemented" | "planned" | "partial";
  phase: string;
}

const STATUS_LABEL: Record<RegRow["status"], { label: string; cls: string }> = {
  implemented: { label: "✅ Implementado", cls: "text-emerald-400" },
  planned:     { label: "🟢 Planeado",      cls: "text-blue-400" },
  partial:     { label: "🟡 Parcial",       cls: "text-amber-400" },
};

export function RegTable({ rows }: { rows: RegRow[] }) {
  return (
    <div className="my-5 overflow-x-auto rounded-xl border border-white/10">
      <table className="w-full min-w-[540px] text-[12px]">
        <thead>
          <tr className="border-b border-white/8 bg-white/[0.03] text-left text-[10px] font-semibold uppercase tracking-wider text-white/50">
            <th className="px-4 py-3">Jurisdição</th>
            <th className="px-4 py-3">Diplomas principais</th>
            <th className="px-4 py-3">Estado</th>
            <th className="px-4 py-3">Fase</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((r, i) => (
            <tr key={i} className="border-b border-white/6 transition-colors hover:bg-white/[0.02]">
              <td className="px-4 py-3 font-medium text-white/88">
                {r.flag} {r.jurisdiction}
              </td>
              <td className="px-4 py-3 text-white/65">{r.diplomas}</td>
              <td className={`px-4 py-3 font-medium ${STATUS_LABEL[r.status].cls}`}>
                {STATUS_LABEL[r.status].label}
              </td>
              <td className="px-4 py-3 text-white/50">{r.phase}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

// ── ApiBlock ───────────────────────────────────────────────────────────────────

export function ApiBlock({
  method,
  path,
  description,
  auth,
}: {
  method: "GET" | "POST" | "PUT" | "DELETE" | "PATCH";
  path: string;
  description: string;
  auth?: boolean;
}) {
  const METHOD_COLORS: Record<string, string> = {
    GET:    "bg-emerald-500/20 text-emerald-300 border-emerald-500/30",
    POST:   "bg-blue-500/20 text-blue-300 border-blue-500/30",
    PUT:    "bg-amber-500/20 text-amber-300 border-amber-500/30",
    DELETE: "bg-red-500/20 text-red-300 border-red-500/30",
    PATCH:  "bg-purple-500/20 text-purple-300 border-purple-500/30",
  };
  return (
    <div className="my-3 flex items-start gap-3 rounded-xl border border-white/8 bg-white/[0.02] px-4 py-3">
      <span className={`shrink-0 rounded-md border px-2 py-0.5 text-[10px] font-bold uppercase ${METHOD_COLORS[method]}`}>
        {method}
      </span>
      <div className="min-w-0 flex-1">
        <code className="text-[12px] font-mono text-white/90">{path}</code>
        <p className="mt-0.5 text-[11px] text-white/55">{description}</p>
      </div>
      {auth && (
        <span className="shrink-0 rounded-md border border-gold-400/30 bg-gold-400/8 px-2 py-0.5 text-[10px] text-gold-300">
          🔐 Auth
        </span>
      )}
    </div>
  );
}
