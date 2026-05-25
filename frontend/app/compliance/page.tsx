"use client";

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { motion } from "framer-motion";

import { useAuth } from "@/lib/auth-context";
import {
  complianceReportDownloadUrl,
  fetchComplianceFrameworks,
  listMissions,
  postComplianceReport,
  searchNormativeRules,
} from "@/lib/api";

/* ─── types ──────────────────────────────────────────────────────── */

interface Framework {
  framework_id: string;
  name: string;
  jurisdiction: string;
  version: string;
  description: string;
}

interface Mission {
  mission_id?: string;
  status?: string;
  description?: string;
}

interface AnchorBlock {
  framework_id: string;
  framework_name: string;
  articles: { article_id: string; fields: Record<string, string> }[];
}

interface HDRAnchor {
  hdr_id: string;
  anchors: AnchorBlock[];
}

interface ReportSummary {
  mission_id: string;
  framework_id: string;
  framework_name: string;
  total_hdrs: number;
  compliant_hdrs: number;
  hdr_anchors: HDRAnchor[];
  generated_at: string;
}

interface NormativeRule {
  rule_id: string;
  name: string;
  description: string;
  category: string;
  action_on_violation: string;
  priority: number;
}

/* ─── helpers ────────────────────────────────────────────────────── */

const ACTION_COLORS: Record<string, string> = {
  BLOCK: "bg-red-500/15 text-red-300 border-red-500/30",
  REALIGN: "bg-amber-500/15 text-amber-300 border-amber-500/30",
  WARN: "bg-blue-500/15 text-blue-300 border-blue-500/30",
};

/* ─── page ───────────────────────────────────────────────────────── */

export default function CompliancePage() {
  const router = useRouter();
  const { isAuthenticated, isReady } = useAuth();

  /* auth gate */
  useEffect(() => {
    if (!isReady) return;
    if (!isAuthenticated) router.replace("/login");
  }, [isReady, isAuthenticated, router]);

  /* data */
  const [frameworks, setFrameworks] = useState<Framework[]>([]);
  const [missions, setMissions] = useState<Mission[]>([]);
  const [loading, setLoading] = useState(true);

  /* form state */
  const [selectedFramework, setSelectedFramework] = useState("LGPD-BR");
  const [selectedMission, setSelectedMission] = useState("");

  /* report */
  const [report, setReport] = useState<ReportSummary | null>(null);
  const [generating, setGenerating] = useState(false);
  const [reportError, setReportError] = useState("");

  /* fts search */
  const [searchQuery, setSearchQuery] = useState("");
  const [searchResults, setSearchResults] = useState<NormativeRule[]>([]);
  const [searching, setSearching] = useState(false);

  useEffect(() => {
    if (!isReady || !isAuthenticated) return;
    (async () => {
      setLoading(true);
      try {
        const [fw, ms] = await Promise.all([
          fetchComplianceFrameworks() as Promise<Framework[]>,
          listMissions(0, 50) as Promise<Mission[]>,
        ]);
        setFrameworks(Array.isArray(fw) ? fw : []);
        const mArr = Array.isArray(ms) ? ms : [];
        setMissions(mArr);
        if (mArr.length > 0 && mArr[0].mission_id) setSelectedMission(mArr[0].mission_id);
      } catch {
        /* frameworks optional */
      } finally {
        setLoading(false);
      }
    })();
  }, [isReady, isAuthenticated]);

  async function handleGenerate() {
    if (!selectedMission) return;
    setGenerating(true);
    setReportError("");
    setReport(null);
    try {
      const r = (await postComplianceReport(selectedMission, selectedFramework)) as ReportSummary;
      setReport(r);
    } catch (e) {
      setReportError(e instanceof Error ? e.message : "Erro ao gerar relatório.");
    } finally {
      setGenerating(false);
    }
  }

  async function handleSearch() {
    if (!searchQuery.trim()) return;
    setSearching(true);
    try {
      const res = (await searchNormativeRules(searchQuery)) as NormativeRule[];
      setSearchResults(Array.isArray(res) ? res : []);
    } catch {
      setSearchResults([]);
    } finally {
      setSearching(false);
    }
  }

  const complianceRate = useMemo(() => {
    if (!report || report.total_hdrs === 0) return null;
    return Math.round((report.compliant_hdrs / report.total_hdrs) * 100);
  }, [report]);

  if (!isReady || !isAuthenticated) {
    return (
      <div className="flex min-h-[40vh] items-center justify-center pt-24 text-white/50">
        <span className="h-5 w-5 animate-spin rounded-full border-2 border-gold-500 border-t-transparent" />
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-5xl px-4 pb-20 pt-24">
      <motion.div initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.45 }}>

        {/* header */}
        <div className="mb-10">
          <p className="text-xs font-semibold uppercase tracking-[0.25em] text-gold-500/80">Conformidade</p>
          <h1 className="mt-1 text-3xl font-bold text-white md:text-4xl">Relatórios de conformidade</h1>
          <p className="mt-2 text-sm text-white/45">
            Ancoragem constitucional de HDRs ao Corpus LGPD-BR / GDPR — geração de relatório PDF.
          </p>
        </div>

        <div className="grid gap-6 lg:grid-cols-2">

          {/* ── Gerador de relatório ── */}
          <div className="glass-elite rounded-2xl border border-white/10 p-6">
            <h2 className="mb-4 text-base font-semibold text-white">Gerar relatório</h2>

            <label className="mb-1 block text-xs text-white/50">Framework</label>
            <select
              value={selectedFramework}
              onChange={(e) => setSelectedFramework(e.target.value)}
              className="mb-4 w-full rounded-xl border border-white/10 bg-white/5 px-3 py-2 text-sm text-white focus:outline-none focus:ring-1 focus:ring-gold-500"
            >
              {frameworks.length === 0
                ? <option value="LGPD-BR">LGPD-BR (padrão)</option>
                : frameworks.map((fw) => (
                    <option key={fw.framework_id} value={fw.framework_id}>
                      {fw.name} — {fw.jurisdiction}
                    </option>
                  ))}
            </select>

            <label className="mb-1 block text-xs text-white/50">Missão</label>
            {loading ? (
              <div className="mb-4 h-10 animate-pulse rounded-xl bg-white/5" />
            ) : missions.length === 0 ? (
              <p className="mb-4 text-xs text-white/40">
                Sem missões disponíveis.{" "}
                <Link href="/" className="text-gold-400 hover:text-gold-300">Criar missão →</Link>
              </p>
            ) : (
              <select
                value={selectedMission}
                onChange={(e) => setSelectedMission(e.target.value)}
                className="mb-4 w-full rounded-xl border border-white/10 bg-white/5 px-3 py-2 text-sm text-white focus:outline-none focus:ring-1 focus:ring-gold-500"
              >
                {missions.map((m) => (
                  <option key={m.mission_id} value={m.mission_id ?? ""}>
                    {m.mission_id?.slice(0, 14)}… — {m.status ?? "?"}
                  </option>
                ))}
              </select>
            )}

            <button
              type="button"
              onClick={handleGenerate}
              disabled={generating || !selectedMission}
              className="btn-gold w-full text-sm disabled:opacity-50"
            >
              {generating ? (
                <span className="flex items-center justify-center gap-2">
                  <span className="h-4 w-4 animate-spin rounded-full border-2 border-white/30 border-t-white" />
                  A gerar…
                </span>
              ) : "Gerar relatório"}
            </button>

            {reportError && (
              <p className="mt-3 rounded-xl border border-amber-500/30 bg-amber-500/10 px-3 py-2 text-xs text-amber-200">
                {reportError}
              </p>
            )}
          </div>

          {/* ── Pesquisa FTS5 ── */}
          <div className="glass-elite rounded-2xl border border-white/10 p-6">
            <h2 className="mb-4 text-base font-semibold text-white">Pesquisar Corpus Normativo</h2>
            <p className="mb-3 text-xs text-white/40">FTS5 — suporta sintaxe: <code className="rounded bg-white/5 px-1">LGPD AND transfer</code></p>
            <div className="flex gap-2">
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && handleSearch()}
                placeholder="ex: dados pessoais"
                className="flex-1 rounded-xl border border-white/10 bg-white/5 px-3 py-2 text-sm text-white placeholder-white/25 focus:outline-none focus:ring-1 focus:ring-gold-500"
              />
              <button
                type="button"
                onClick={handleSearch}
                disabled={searching}
                className="btn-glass shrink-0 text-sm"
              >
                {searching ? "…" : "Buscar"}
              </button>
            </div>

            {searchResults.length > 0 && (
              <ul className="mt-4 space-y-2">
                {searchResults.map((rule) => (
                  <li key={rule.rule_id} className="rounded-xl border border-white/5 bg-white/[0.03] p-3">
                    <div className="flex items-start justify-between gap-2">
                      <div>
                        <span className="text-xs font-mono text-gold-400">{rule.rule_id}</span>
                        <p className="mt-0.5 text-sm font-medium text-white">{rule.name}</p>
                        <p className="mt-1 text-xs text-white/45 line-clamp-2">{rule.description}</p>
                      </div>
                      <span className={`shrink-0 rounded-full border px-2 py-0.5 text-[10px] font-semibold ${ACTION_COLORS[rule.action_on_violation] ?? "bg-white/5 text-white/50"}`}>
                        {rule.action_on_violation}
                      </span>
                    </div>
                  </li>
                ))}
              </ul>
            )}
          </div>
        </div>

        {/* ── Resultado do relatório ── */}
        {report && (
          <motion.div
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            className="mt-8 glass-elite rounded-2xl border border-white/10 p-6"
          >
            <div className="mb-6 flex flex-wrap items-start justify-between gap-4">
              <div>
                <h2 className="text-lg font-semibold text-white">
                  {report.framework_name}
                  <span className="ml-2 font-mono text-xs text-white/40">{report.framework_id}</span>
                </h2>
                <p className="mt-1 text-xs text-white/40">
                  Missão <span className="font-mono text-gold-400">{report.mission_id}</span> ·{" "}
                  {new Date(report.generated_at).toLocaleString("pt-BR")}
                </p>
              </div>
              <a
                href={complianceReportDownloadUrl(report.mission_id, report.framework_id)}
                target="_blank"
                rel="noreferrer"
                className="btn-glass text-sm"
              >
                Descarregar PDF
              </a>
            </div>

            {/* métricas */}
            <div className="mb-6 grid gap-4 sm:grid-cols-3">
              {[
                { label: "HDRs analisados", value: String(report.total_hdrs) },
                { label: "HDRs conformes", value: String(report.compliant_hdrs) },
                { label: "Taxa de conformidade", value: complianceRate !== null ? `${complianceRate}%` : "—" },
              ].map((card) => (
                <div key={card.label} className="rounded-xl border border-white/5 bg-white/[0.03] p-4">
                  <p className="text-[11px] uppercase tracking-wider text-white/40">{card.label}</p>
                  <p className="mt-1 text-2xl font-semibold text-white">{card.value}</p>
                </div>
              ))}
            </div>

            {/* lista de HDR anchors */}
            {report.hdr_anchors.length > 0 && (
              <div>
                <h3 className="mb-3 text-sm font-semibold text-white/70">Registos HDR analisados</h3>
                <ul className="space-y-2">
                  {report.hdr_anchors.map((anchor) => {
                    const articlesOk = anchor.anchors.flatMap((b) => b.articles).filter(
                      (a) => Object.values(a.fields).some(Boolean),
                    ).length;
                    const articlesTotal = anchor.anchors.flatMap((b) => b.articles).length;
                    return (
                      <li key={anchor.hdr_id} className="flex items-center justify-between rounded-xl border border-white/5 bg-white/[0.03] px-4 py-3">
                        <span className="font-mono text-xs text-gold-200/80">{anchor.hdr_id.slice(0, 20)}…</span>
                        <span className="text-xs text-white/40">
                          {articlesOk}/{articlesTotal} artigos cobertos
                        </span>
                      </li>
                    );
                  })}
                </ul>
              </div>
            )}
          </motion.div>
        )}

        {/* quick links */}
        <div className="mt-8 flex flex-wrap gap-3">
          <Link href="/dashboard" className="btn-glass text-sm">Painel</Link>
          <Link href="/normative" className="btn-glass text-sm">Hub normativo</Link>
          <Link href="/diary" className="btn-glass text-sm">Diário forense</Link>
        </div>

      </motion.div>
    </div>
  );
}
