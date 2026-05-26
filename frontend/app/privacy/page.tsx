"use client";

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { motion, AnimatePresence } from "framer-motion";

import { useAuth } from "@/lib/auth-context";
import {
  fetchDpoContact,
  submitDpoRequest,
  fetchConsentBundle,
  setConsent,
  revokeAllConsent,
  listRipd,
  createRipd,
  ripdDownloadUrl,
  privacyExportUrl,
  listIncidents,
  registerIncident,
  purgeLogs,
} from "@/lib/api";

/* ─── types ──────────────────────────────────────────────────────────── */

interface DPOContact {
  dpo_name: string;
  dpo_email: string;
  organization_name: string;
  privacy_policy_url: string;
  request_form_url: string;
}

interface ConsentRecord {
  consent_id: string;
  purpose: string;
  legal_basis: string;
  granted: boolean;
  granted_at: string | null;
  revoked_at: string | null;
  version: string;
}

interface ConsentBundle {
  user_id: string;
  records: ConsentRecord[];
}

interface RIPDReport {
  ripd_id: string;
  title: string;
  processing_type: string;
  legal_basis: string;
  status: string;
  created_at: string;
  dpo_name: string;
  dpo_email: string;
}

interface SecurityIncident {
  incident_id: string;
  category: string;
  severity: string;
  status: string;
  affected_subjects_count: number;
  detected_at: string;
  anpd_notification_due_at: string | null;
  anpd_notified_at: string | null;
  is_overdue_anpd: boolean;
}

/* ─── helpers ────────────────────────────────────────────────────────── */

const CONSENT_PURPOSES = [
  { id: "analytics", label: "Análise de uso", basis: "Interesse legítimo", optional: true },
  { id: "ai_training", label: "Treino de modelos de IA", basis: "Consentimento", optional: true },
  { id: "marketing", label: "Comunicações de marketing", basis: "Consentimento", optional: true },
  { id: "third_party", label: "Partilha com terceiros", basis: "Consentimento", optional: true },
  { id: "research", label: "Investigação e desenvolvimento", basis: "Consentimento", optional: true },
];

const LEGAL_BASES = [
  { id: "consent", label: "Consentimento" },
  { id: "contract", label: "Execução de contrato" },
  { id: "legal_obligation", label: "Obrigação legal" },
  { id: "legitimate_interest", label: "Interesse legítimo" },
];

const INCIDENT_CATEGORIES = [
  { id: "unauthorized_access", label: "Acesso não autorizado" },
  { id: "data_leak", label: "Vazamento de dados" },
  { id: "ransomware", label: "Ransomware" },
  { id: "insider_threat", label: "Ameaça interna" },
  { id: "lost_device", label: "Dispositivo perdido/furtado" },
  { id: "other", label: "Outro" },
];

const SEVERITY_COLORS: Record<string, string> = {
  low: "bg-blue-500/15 text-blue-300 border-blue-500/30",
  medium: "bg-amber-500/15 text-amber-300 border-amber-500/30",
  high: "bg-orange-500/15 text-orange-300 border-orange-500/30",
  critical: "bg-red-500/15 text-red-300 border-red-500/30",
};

const STATUS_COLORS: Record<string, string> = {
  detected: "bg-red-500/15 text-red-300",
  evaluating: "bg-amber-500/15 text-amber-300",
  anpd_notified: "bg-blue-500/15 text-blue-300",
  subjects_notified: "bg-indigo-500/15 text-indigo-300",
  closed: "bg-green-500/15 text-green-300",
  draft: "bg-white/10 text-white/50",
  approved: "bg-green-500/15 text-green-300",
};

/* ─── tabs ───────────────────────────────────────────────────────────── */

type Tab = "overview" | "consent" | "ripd" | "incidents" | "request";

/* ─── page ───────────────────────────────────────────────────────────── */

export default function PrivacyPage() {
  const router = useRouter();
  const { isAuthenticated, isReady, user } = useAuth();
  const isAdmin = user?.role === "admin";

  const [tab, setTab] = useState<Tab>("overview");

  /* data */
  const [dpoContact, setDpoContact] = useState<DPOContact | null>(null);
  const [consentBundle, setConsentBundle] = useState<ConsentBundle | null>(null);
  const [ripds, setRipds] = useState<RIPDReport[]>([]);
  const [incidents, setIncidents] = useState<SecurityIncident[]>([]);
  const [loading, setLoading] = useState(true);

  /* form: DPO request */
  const [reqName, setReqName] = useState("");
  const [reqEmail, setReqEmail] = useState("");
  const [reqType, setReqType] = useState("access");
  const [reqDesc, setReqDesc] = useState("");
  const [reqSending, setReqSending] = useState(false);
  const [reqDone, setReqDone] = useState(false);
  const [reqError, setReqError] = useState("");

  /* form: RIPD */
  const [ripdTitle, setRipdTitle] = useState("");
  const [ripdType, setRipdType] = useState("ingestion");
  const [ripdBasis, setRipdBasis] = useState("contract");
  const [ripdPurpose, setRipdPurpose] = useState("");
  const [ripdCategories, setRipdCategories] = useState("dados de identificação, documentos jurídicos");
  const [ripdLifecycle, setRipdLifecycle] = useState("Mínimo 5 anos; eliminação automática após prazo legal.");
  const [ripdCreating, setRipdCreating] = useState(false);
  const [ripdError, setRipdError] = useState("");

  /* form: Incident */
  const [incCategory, setIncCategory] = useState("unauthorized_access");
  const [incDesc, setIncDesc] = useState("");
  const [incSeverity, setIncSeverity] = useState("medium");
  const [incSubjects, setIncSubjects] = useState("0");
  const [incCreating, setIncCreating] = useState(false);
  const [incError, setIncError] = useState("");

  /* purge */
  const [purging, setPurging] = useState(false);
  const [purgeResult, setPurgeResult] = useState<{ purged_count: number } | null>(null);

  /* auth gate */
  useEffect(() => {
    if (!isReady) return;
    if (!isAuthenticated) router.replace("/login");
  }, [isReady, isAuthenticated, router]);

  /* initial load */
  useEffect(() => {
    if (!isReady || !isAuthenticated) return;
    (async () => {
      setLoading(true);
      try {
        const [dpo, consent] = await Promise.all([
          fetchDpoContact() as Promise<DPOContact>,
          fetchConsentBundle() as Promise<ConsentBundle>,
        ]);
        setDpoContact(dpo);
        setConsentBundle(consent);

        const ripdList = (await listRipd()) as RIPDReport[];
        setRipds(Array.isArray(ripdList) ? ripdList : []);

        if (isAdmin) {
          try {
            const inc = (await listIncidents()) as SecurityIncident[];
            setIncidents(Array.isArray(inc) ? inc : []);
          } catch { /* non-admin */ }
        }
      } catch { /* ignore */ }
      finally { setLoading(false); }
    })();
  }, [isReady, isAuthenticated, isAdmin]);

  /* consent toggle */
  async function handleConsent(purpose: string, granted: boolean) {
    try {
      await setConsent(purpose, granted);
      const updated = (await fetchConsentBundle()) as ConsentBundle;
      setConsentBundle(updated);
    } catch { /* ignore */ }
  }

  async function handleRevokeAll() {
    await revokeAllConsent();
    const updated = (await fetchConsentBundle()) as ConsentBundle;
    setConsentBundle(updated);
  }

  /* get consent state for a purpose */
  const consentMap = useMemo(() => {
    const map: Record<string, boolean> = {};
    if (consentBundle?.records) {
      for (const r of consentBundle.records) {
        map[r.purpose] = r.granted;
      }
    }
    return map;
  }, [consentBundle]);

  /* submit DPO request */
  async function handleDpoRequest(e: React.FormEvent) {
    e.preventDefault();
    setReqSending(true);
    setReqError("");
    try {
      await submitDpoRequest({
        requester_name: reqName,
        requester_email: reqEmail,
        request_type: reqType,
        description: reqDesc,
      });
      setReqDone(true);
      setReqName(""); setReqEmail(""); setReqDesc("");
    } catch (err) {
      setReqError(err instanceof Error ? err.message : "Erro ao enviar.");
    } finally {
      setReqSending(false);
    }
  }

  /* create RIPD */
  async function handleCreateRipd(e: React.FormEvent) {
    e.preventDefault();
    setRipdCreating(true);
    setRipdError("");
    try {
      await createRipd({
        title: ripdTitle,
        processing_type: ripdType,
        legal_basis: ripdBasis,
        purpose: ripdPurpose,
        data_categories: ripdCategories.split(",").map(s => s.trim()).filter(Boolean),
        data_lifecycle: ripdLifecycle,
        recipients: [],
        risks_identified: [],
        safeguards: [],
      });
      const updated = (await listRipd()) as RIPDReport[];
      setRipds(Array.isArray(updated) ? updated : []);
      setRipdTitle(""); setRipdPurpose("");
    } catch (err) {
      setRipdError(err instanceof Error ? err.message : "Erro ao criar RIPD.");
    } finally {
      setRipdCreating(false);
    }
  }

  /* register incident */
  async function handleIncident(e: React.FormEvent) {
    e.preventDefault();
    setIncCreating(true);
    setIncError("");
    try {
      await registerIncident({
        category: incCategory,
        description: incDesc,
        severity: incSeverity,
        affected_subjects_count: parseInt(incSubjects, 10) || 0,
        affected_data_types: [],
      });
      const updated = (await listIncidents()) as SecurityIncident[];
      setIncidents(Array.isArray(updated) ? updated : []);
      setIncDesc(""); setIncSubjects("0");
    } catch (err) {
      setIncError(err instanceof Error ? err.message : "Erro ao registar incidente.");
    } finally {
      setIncCreating(false);
    }
  }

  async function handlePurge() {
    setPurging(true);
    try {
      const result = (await purgeLogs()) as { purged_count: number };
      setPurgeResult(result);
    } catch { /* ignore */ }
    finally { setPurging(false); }
  }

  if (!isReady || !isAuthenticated) {
    return (
      <div className="flex min-h-[40vh] items-center justify-center pt-24 text-white/50">
        <span className="h-5 w-5 animate-spin rounded-full border-2 border-gold-500 border-t-transparent" />
      </div>
    );
  }

  const tabs: { id: Tab; label: string }[] = [
    { id: "overview", label: "Visão geral" },
    { id: "consent", label: "Consentimento" },
    { id: "ripd", label: "RIPD" },
    { id: "request", label: "Solicitar direitos" },
    ...(isAdmin ? [{ id: "incidents" as Tab, label: "Incidentes" }] : []),
  ];

  return (
    <div className="mx-auto max-w-5xl px-4 pb-20 pt-24">
      <motion.div initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.4 }}>

        {/* header */}
        <div className="mb-8">
          <p className="text-xs font-semibold uppercase tracking-[0.25em] text-gold-500/80">Privacidade</p>
          <h1 className="mt-1 text-3xl font-bold text-white md:text-4xl">Centro de Privacidade LGPD</h1>
          <p className="mt-2 text-sm text-white/45">
            Gestão de consentimentos, RIPDs, direitos do titular e incidentes de segurança — Lei 13.709/2018.
          </p>
        </div>

        {/* tabs */}
        <div className="mb-8 flex flex-wrap gap-2 border-b border-white/10 pb-4">
          {tabs.map((t) => (
            <button
              key={t.id}
              type="button"
              onClick={() => setTab(t.id)}
              className={`rounded-full px-4 py-2 text-xs font-medium transition-colors ${
                tab === t.id
                  ? "bg-gold-500/20 text-gold-300 border border-gold-500/40"
                  : "text-white/50 hover:bg-white/5 hover:text-white"
              }`}
            >
              {t.label}
            </button>
          ))}
        </div>

        {/* ─── TAB: OVERVIEW ─── */}
        {tab === "overview" && (
          <div className="grid gap-6 lg:grid-cols-2">

            {/* DPO contact */}
            <div className="glass-elite rounded-2xl border border-white/10 p-6">
              <h2 className="mb-4 text-base font-semibold text-white">Encarregado de Dados (DPO)</h2>
              {loading ? (
                <div className="space-y-2">
                  <div className="h-4 w-48 animate-pulse rounded bg-white/5" />
                  <div className="h-4 w-36 animate-pulse rounded bg-white/5" />
                </div>
              ) : dpoContact ? (
                <div className="space-y-2 text-sm">
                  <p className="text-white">{dpoContact.dpo_name}</p>
                  <a href={`mailto:${dpoContact.dpo_email}`} className="text-gold-400 hover:text-gold-300">
                    {dpoContact.dpo_email}
                  </a>
                  <p className="mt-3 text-xs text-white/40">
                    LGPD art. 41 — Encarregado obrigatório para plataformas de IA
                  </p>
                </div>
              ) : (
                <p className="text-sm text-white/40">DPO não configurado.</p>
              )}
            </div>

            {/* quick actions */}
            <div className="glass-elite rounded-2xl border border-white/10 p-6">
              <h2 className="mb-4 text-base font-semibold text-white">Acções rápidas</h2>
              <div className="flex flex-col gap-3">
                <button
                  type="button"
                  onClick={() => setTab("request")}
                  className="btn-glass w-full text-sm text-left"
                >
                  📋 Solicitar acesso / eliminação dos meus dados
                </button>
                <button
                  type="button"
                  onClick={() => setTab("consent")}
                  className="btn-glass w-full text-sm text-left"
                >
                  ✅ Gerir consentimentos
                </button>
                <a
                  href={privacyExportUrl()}
                  className="btn-glass block w-full text-center text-sm"
                  target="_blank"
                  rel="noopener noreferrer"
                >
                  📦 Exportar todos os meus dados (ZIP)
                </a>
              </div>
            </div>

            {/* legal basis info */}
            <div className="glass-elite rounded-2xl border border-white/10 p-6 lg:col-span-2">
              <h2 className="mb-4 text-base font-semibold text-white">Bases legais de tratamento (LGPD art. 7)</h2>
              <div className="grid gap-3 sm:grid-cols-2 md:grid-cols-3">
                {[
                  { basis: "Consentimento", desc: "Treino IA, marketing, investigação", badge: "🟡 Revogável" },
                  { basis: "Execução de contrato", desc: "Gestão da conta, missões, HDRs", badge: "🔒 Necessário" },
                  { basis: "Obrigação legal", desc: "Guarda de logs (Marco Civil arts. 13-15)", badge: "🔒 Necessário" },
                  { basis: "Interesse legítimo", desc: "Análise de uso agregado (anonimizado)", badge: "🟡 Oponível" },
                  { basis: "Valor probatório", desc: "HDRs e evidências (5 anos mínimo)", badge: "🔒 Legal" },
                ].map((item) => (
                  <div key={item.basis} className="rounded-xl border border-white/5 bg-white/[0.03] p-3">
                    <p className="text-xs font-semibold text-white">{item.basis}</p>
                    <p className="mt-1 text-[11px] text-white/40">{item.desc}</p>
                    <span className="mt-2 inline-block text-[10px] text-white/50">{item.badge}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* ─── TAB: CONSENT ─── */}
        {tab === "consent" && (
          <div className="space-y-4">
            <div className="glass-elite rounded-2xl border border-white/10 p-6">
              <div className="mb-4 flex items-center justify-between">
                <h2 className="text-base font-semibold text-white">Consentimentos granulares (LGPD art. 8)</h2>
                <button
                  type="button"
                  onClick={handleRevokeAll}
                  className="rounded-full border border-red-500/30 px-3 py-1.5 text-[11px] text-red-300 hover:bg-red-500/10"
                >
                  Revogar todos
                </button>
              </div>
              <p className="mb-5 text-xs text-white/40">
                Pode revogar o consentimento a qualquer momento (LGPD art. 8 §5). Tratamentos baseados em contrato
                ou obrigação legal não podem ser revogados.
              </p>
              <ul className="space-y-3">
                {CONSENT_PURPOSES.map((p) => {
                  const isGranted = consentMap[p.id] ?? false;
                  return (
                    <li
                      key={p.id}
                      className="flex items-center justify-between rounded-xl border border-white/5 bg-white/[0.03] px-4 py-3"
                    >
                      <div>
                        <p className="text-sm font-medium text-white">{p.label}</p>
                        <p className="text-[11px] text-white/40">Base legal: {p.basis}</p>
                      </div>
                      <button
                        type="button"
                        onClick={() => handleConsent(p.id, !isGranted)}
                        className={`relative h-6 w-11 rounded-full transition-colors ${
                          isGranted ? "bg-gold-500" : "bg-white/15"
                        }`}
                        aria-label={isGranted ? `Revogar ${p.label}` : `Conceder ${p.label}`}
                      >
                        <span
                          className={`absolute top-0.5 h-5 w-5 rounded-full bg-white shadow transition-transform ${
                            isGranted ? "translate-x-5" : "translate-x-0.5"
                          }`}
                        />
                      </button>
                    </li>
                  );
                })}
              </ul>
            </div>

            {/* Admin: purge logs */}
            {isAdmin && (
              <div className="glass-elite rounded-2xl border border-amber-500/20 p-6">
                <h2 className="mb-2 text-base font-semibold text-white">Purga de logs (Marco Civil arts. 13-15)</h2>
                <p className="mb-4 text-xs text-white/40">
                  Elimina logs de acesso expirados. Logs com ordem judicial (judicial_hold=1) nunca são eliminados.
                </p>
                <button
                  type="button"
                  onClick={handlePurge}
                  disabled={purging}
                  className="btn-glass text-sm disabled:opacity-50"
                >
                  {purging ? "A purgar…" : "Executar purga"}
                </button>
                {purgeResult && (
                  <p className="mt-3 text-xs text-green-300">
                    ✓ {purgeResult.purged_count} log(s) eliminado(s).
                  </p>
                )}
              </div>
            )}
          </div>
        )}

        {/* ─── TAB: RIPD ─── */}
        {tab === "ripd" && (
          <div className="space-y-6">
            {/* create form */}
            <div className="glass-elite rounded-2xl border border-white/10 p-6">
              <h2 className="mb-4 text-base font-semibold text-white">
                Novo RIPD (LGPD art. 38)
              </h2>
              <form onSubmit={handleCreateRipd} className="space-y-3">
                <div className="grid gap-3 sm:grid-cols-2">
                  <div>
                    <label className="mb-1 block text-xs text-white/50">Título</label>
                    <input
                      required
                      value={ripdTitle}
                      onChange={(e) => setRipdTitle(e.target.value)}
                      placeholder="RIPD — Ingestão de Evidências"
                      className="w-full rounded-xl border border-white/10 bg-white/5 px-3 py-2 text-sm text-white placeholder-white/25 focus:outline-none focus:ring-1 focus:ring-gold-500"
                    />
                  </div>
                  <div>
                    <label className="mb-1 block text-xs text-white/50">Tipo de tratamento</label>
                    <input
                      required
                      value={ripdType}
                      onChange={(e) => setRipdType(e.target.value)}
                      placeholder="ingestion"
                      className="w-full rounded-xl border border-white/10 bg-white/5 px-3 py-2 text-sm text-white placeholder-white/25 focus:outline-none focus:ring-1 focus:ring-gold-500"
                    />
                  </div>
                </div>
                <div className="grid gap-3 sm:grid-cols-2">
                  <div>
                    <label className="mb-1 block text-xs text-white/50">Base legal</label>
                    <select
                      value={ripdBasis}
                      onChange={(e) => setRipdBasis(e.target.value)}
                      className="w-full rounded-xl border border-white/10 bg-white/5 px-3 py-2 text-sm text-white focus:outline-none focus:ring-1 focus:ring-gold-500"
                    >
                      {LEGAL_BASES.map((b) => (
                        <option key={b.id} value={b.id}>{b.label}</option>
                      ))}
                    </select>
                  </div>
                  <div>
                    <label className="mb-1 block text-xs text-white/50">Categorias de dados (separar por vírgula)</label>
                    <input
                      required
                      value={ripdCategories}
                      onChange={(e) => setRipdCategories(e.target.value)}
                      className="w-full rounded-xl border border-white/10 bg-white/5 px-3 py-2 text-sm text-white placeholder-white/25 focus:outline-none focus:ring-1 focus:ring-gold-500"
                    />
                  </div>
                </div>
                <div>
                  <label className="mb-1 block text-xs text-white/50">Finalidade</label>
                  <textarea
                    required
                    rows={2}
                    value={ripdPurpose}
                    onChange={(e) => setRipdPurpose(e.target.value)}
                    placeholder="Descreva a finalidade do tratamento de dados..."
                    className="w-full rounded-xl border border-white/10 bg-white/5 px-3 py-2 text-sm text-white placeholder-white/25 focus:outline-none focus:ring-1 focus:ring-gold-500"
                  />
                </div>
                <div>
                  <label className="mb-1 block text-xs text-white/50">Ciclo de vida dos dados</label>
                  <input
                    required
                    value={ripdLifecycle}
                    onChange={(e) => setRipdLifecycle(e.target.value)}
                    className="w-full rounded-xl border border-white/10 bg-white/5 px-3 py-2 text-sm text-white placeholder-white/25 focus:outline-none focus:ring-1 focus:ring-gold-500"
                  />
                </div>
                {ripdError && (
                  <p className="rounded-xl border border-red-500/30 bg-red-500/10 px-3 py-2 text-xs text-red-300">
                    {ripdError}
                  </p>
                )}
                <button
                  type="submit"
                  disabled={ripdCreating}
                  className="btn-gold text-sm disabled:opacity-50"
                >
                  {ripdCreating ? "A criar…" : "Criar RIPD"}
                </button>
              </form>
            </div>

            {/* list */}
            {ripds.length > 0 && (
              <div className="glass-elite rounded-2xl border border-white/10 p-6">
                <h2 className="mb-4 text-base font-semibold text-white">RIPDs da organização</h2>
                <ul className="space-y-2">
                  {ripds.map((r) => (
                    <li
                      key={r.ripd_id}
                      className="flex items-center justify-between rounded-xl border border-white/5 bg-white/[0.03] px-4 py-3"
                    >
                      <div>
                        <p className="text-sm font-medium text-white">{r.title}</p>
                        <p className="text-[11px] text-white/40">
                          {r.processing_type} · {r.legal_basis} ·{" "}
                          {new Date(r.created_at).toLocaleDateString("pt-BR")}
                        </p>
                      </div>
                      <div className="flex items-center gap-2">
                        <span className={`rounded-full px-2 py-0.5 text-[10px] font-semibold ${STATUS_COLORS[r.status] ?? "bg-white/5 text-white/50"}`}>
                          {r.status}
                        </span>
                        <a
                          href={ripdDownloadUrl(r.ripd_id)}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="btn-glass text-xs"
                        >
                          PDF
                        </a>
                      </div>
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        )}

        {/* ─── TAB: INCIDENTS (admin) ─── */}
        {tab === "incidents" && isAdmin && (
          <div className="space-y-6">
            {/* register form */}
            <div className="glass-elite rounded-2xl border border-red-500/20 p-6">
              <h2 className="mb-2 text-base font-semibold text-white">Registar incidente (ANPD Res. 15/2024)</h2>
              <p className="mb-4 text-xs text-amber-300">
                ⚠️ Prazo de notificação à ANPD: <strong>72 horas</strong> após a detecção.
              </p>
              <form onSubmit={handleIncident} className="space-y-3">
                <div className="grid gap-3 sm:grid-cols-3">
                  <div>
                    <label className="mb-1 block text-xs text-white/50">Categoria</label>
                    <select
                      value={incCategory}
                      onChange={(e) => setIncCategory(e.target.value)}
                      className="w-full rounded-xl border border-white/10 bg-white/5 px-3 py-2 text-sm text-white focus:outline-none focus:ring-1 focus:ring-gold-500"
                    >
                      {INCIDENT_CATEGORIES.map((c) => (
                        <option key={c.id} value={c.id}>{c.label}</option>
                      ))}
                    </select>
                  </div>
                  <div>
                    <label className="mb-1 block text-xs text-white/50">Gravidade</label>
                    <select
                      value={incSeverity}
                      onChange={(e) => setIncSeverity(e.target.value)}
                      className="w-full rounded-xl border border-white/10 bg-white/5 px-3 py-2 text-sm text-white focus:outline-none focus:ring-1 focus:ring-gold-500"
                    >
                      <option value="low">Baixa</option>
                      <option value="medium">Média</option>
                      <option value="high">Alta</option>
                      <option value="critical">Crítica</option>
                    </select>
                  </div>
                  <div>
                    <label className="mb-1 block text-xs text-white/50">Titulares afetados</label>
                    <input
                      type="number"
                      min="0"
                      value={incSubjects}
                      onChange={(e) => setIncSubjects(e.target.value)}
                      className="w-full rounded-xl border border-white/10 bg-white/5 px-3 py-2 text-sm text-white focus:outline-none focus:ring-1 focus:ring-gold-500"
                    />
                  </div>
                </div>
                <div>
                  <label className="mb-1 block text-xs text-white/50">Descrição detalhada</label>
                  <textarea
                    required
                    rows={3}
                    value={incDesc}
                    onChange={(e) => setIncDesc(e.target.value)}
                    placeholder="Descreva o incidente, como foi detetado e o impacto estimado..."
                    className="w-full rounded-xl border border-white/10 bg-white/5 px-3 py-2 text-sm text-white placeholder-white/25 focus:outline-none focus:ring-1 focus:ring-gold-500"
                  />
                </div>
                {incError && (
                  <p className="rounded-xl border border-red-500/30 bg-red-500/10 px-3 py-2 text-xs text-red-300">
                    {incError}
                  </p>
                )}
                <button
                  type="submit"
                  disabled={incCreating}
                  className="btn-gold text-sm disabled:opacity-50"
                >
                  {incCreating ? "A registar…" : "Registar incidente"}
                </button>
              </form>
            </div>

            {/* list */}
            {incidents.length > 0 && (
              <div className="glass-elite rounded-2xl border border-white/10 p-6">
                <h2 className="mb-4 text-base font-semibold text-white">Incidentes registados</h2>
                <ul className="space-y-3">
                  {incidents.map((inc) => (
                    <li
                      key={inc.incident_id}
                      className={`rounded-xl border px-4 py-3 ${
                        inc.is_overdue_anpd
                          ? "border-red-500/50 bg-red-500/10"
                          : "border-white/5 bg-white/[0.03]"
                      }`}
                    >
                      <div className="flex flex-wrap items-start justify-between gap-2">
                        <div>
                          <span className="font-mono text-xs text-gold-400">{inc.incident_id.slice(0, 16)}…</span>
                          <p className="mt-0.5 text-sm font-medium text-white capitalize">
                            {inc.category.replace("_", " ")}
                          </p>
                          <p className="text-[11px] text-white/40">
                            Detetado: {new Date(inc.detected_at).toLocaleString("pt-BR")}
                          </p>
                          {inc.anpd_notification_due_at && (
                            <p className={`text-[11px] ${inc.is_overdue_anpd ? "text-red-300 font-semibold" : "text-white/40"}`}>
                              Prazo ANPD: {new Date(inc.anpd_notification_due_at).toLocaleString("pt-BR")}
                              {inc.is_overdue_anpd && " ⚠️ VENCIDO"}
                            </p>
                          )}
                        </div>
                        <div className="flex items-center gap-2">
                          <span className={`rounded-full border px-2 py-0.5 text-[10px] font-semibold ${SEVERITY_COLORS[inc.severity] ?? ""}`}>
                            {inc.severity}
                          </span>
                          <span className={`rounded-full px-2 py-0.5 text-[10px] font-semibold ${STATUS_COLORS[inc.status] ?? "bg-white/5 text-white/50"}`}>
                            {inc.status.replace("_", " ")}
                          </span>
                        </div>
                      </div>
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        )}

        {/* ─── TAB: REQUEST RIGHTS ─── */}
        {tab === "request" && (
          <div className="glass-elite rounded-2xl border border-white/10 p-6">
            <h2 className="mb-2 text-base font-semibold text-white">
              Exercer direitos do titular (LGPD art. 18)
            </h2>
            <p className="mb-5 text-xs text-white/40">
              Pode solicitar: acesso, correção, eliminação, portabilidade ou revogação de consentimento.
              O prazo de resposta é de <strong className="text-white/70">15 dias úteis</strong> (LGPD art. 19).
            </p>

            {reqDone ? (
              <motion.div
                initial={{ opacity: 0, scale: 0.97 }}
                animate={{ opacity: 1, scale: 1 }}
                className="rounded-xl border border-green-500/30 bg-green-500/10 p-4 text-sm text-green-300"
              >
                ✓ Solicitação recebida. Responderemos em até 15 dias úteis no e-mail indicado.
                <button
                  type="button"
                  className="ml-3 text-xs text-white/50 hover:text-white"
                  onClick={() => setReqDone(false)}
                >
                  Nova solicitação
                </button>
              </motion.div>
            ) : (
              <form onSubmit={handleDpoRequest} className="space-y-4">
                <div className="grid gap-3 sm:grid-cols-2">
                  <div>
                    <label className="mb-1 block text-xs text-white/50">Nome completo</label>
                    <input
                      required
                      value={reqName}
                      onChange={(e) => setReqName(e.target.value)}
                      className="w-full rounded-xl border border-white/10 bg-white/5 px-3 py-2 text-sm text-white placeholder-white/25 focus:outline-none focus:ring-1 focus:ring-gold-500"
                    />
                  </div>
                  <div>
                    <label className="mb-1 block text-xs text-white/50">E-mail de contacto</label>
                    <input
                      required
                      type="email"
                      value={reqEmail}
                      onChange={(e) => setReqEmail(e.target.value)}
                      className="w-full rounded-xl border border-white/10 bg-white/5 px-3 py-2 text-sm text-white placeholder-white/25 focus:outline-none focus:ring-1 focus:ring-gold-500"
                    />
                  </div>
                </div>
                <div>
                  <label className="mb-1 block text-xs text-white/50">Tipo de solicitação</label>
                  <select
                    value={reqType}
                    onChange={(e) => setReqType(e.target.value)}
                    className="w-full rounded-xl border border-white/10 bg-white/5 px-3 py-2 text-sm text-white focus:outline-none focus:ring-1 focus:ring-gold-500"
                  >
                    <option value="access">Acesso aos meus dados</option>
                    <option value="correction">Correção de dados incorretos</option>
                    <option value="deletion">Eliminação dos meus dados</option>
                    <option value="portability">Portabilidade dos dados</option>
                    <option value="revocation">Revogação de consentimento</option>
                    <option value="info">Informação sobre o tratamento</option>
                  </select>
                </div>
                <div>
                  <label className="mb-1 block text-xs text-white/50">Descrição da solicitação</label>
                  <textarea
                    required
                    rows={4}
                    value={reqDesc}
                    onChange={(e) => setReqDesc(e.target.value)}
                    placeholder="Descreva o que pretende solicitar..."
                    className="w-full rounded-xl border border-white/10 bg-white/5 px-3 py-2 text-sm text-white placeholder-white/25 focus:outline-none focus:ring-1 focus:ring-gold-500"
                  />
                </div>
                {reqError && (
                  <p className="rounded-xl border border-red-500/30 bg-red-500/10 px-3 py-2 text-xs text-red-300">
                    {reqError}
                  </p>
                )}
                <button
                  type="submit"
                  disabled={reqSending}
                  className="btn-gold w-full text-sm disabled:opacity-50"
                >
                  {reqSending ? "A enviar…" : "Enviar solicitação"}
                </button>
              </form>
            )}
          </div>
        )}

        {/* navigation */}
        <div className="mt-8 flex flex-wrap gap-3">
          <Link href="/compliance" className="btn-glass text-sm">Conformidade</Link>
          <Link href="/dashboard" className="btn-glass text-sm">Painel</Link>
          <Link href="/normative" className="btn-glass text-sm">Hub normativo</Link>
        </div>

      </motion.div>
    </div>
  );
}
