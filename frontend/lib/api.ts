function resolveApiOrigin(): string {
  if (typeof window !== "undefined") {
    return "";
  }
  return (
    process.env.INTERNAL_API_ORIGIN ||
    process.env.NEXT_PUBLIC_BACKEND_URL ||
    "http://127.0.0.1:8000"
  );
}

const DEFAULT_ORIGIN = resolveApiOrigin();
const PREFIX = `${DEFAULT_ORIGIN}/api/v1`;

function authorizedHeaders(extra?: HeadersInit): HeadersInit {
  return new Headers(extra);
}

// Default timeout: backend has 60s for LLM calls but UI requests should not hang past 15s.
const DEFAULT_TIMEOUT_MS = 15_000;

async function apiFetch(input: string, init?: RequestInit): Promise<Response> {
  // Compose AbortSignal: caller-provided signal AND our timeout signal.
  const timeoutSignal = AbortSignal.timeout(DEFAULT_TIMEOUT_MS);
  const callerSignal = init?.signal ?? null;
  const signal: AbortSignal = callerSignal
    ? AbortSignal.any([callerSignal, timeoutSignal])
    : timeoutSignal;

  const next: RequestInit = {
    ...init,
    headers: authorizedHeaders(init?.headers),
    credentials: "include",
    signal,
  };

  const response = await fetch(input, next);

  // Session-expiry handling: 401 in browser → trigger global logout-redirect.
  if (response.status === 401 && typeof window !== "undefined") {
    const url = new URL(input, window.location.origin);
    const isAuthEndpoint = url.pathname.includes("/auth/login") || url.pathname.includes("/auth/register");
    if (!isAuthEndpoint) {
      window.dispatchEvent(new CustomEvent("heillon:session-expired"));
    }
  }

  return response;
}

/** @deprecated JWT is now carried exclusively via HttpOnly cookie. */
export function persistAuthBearer(_token: string | null): void {
  if (typeof window === "undefined") return;
  window.localStorage.removeItem("heillon_bearer");
}

export function getBackendPublicUrl(): string {
  if (typeof window !== "undefined") {
    return window.location.origin;
  }
  const fallback =
    typeof process.env.NEXT_PUBLIC_BACKEND_URL === "string" && process.env.NEXT_PUBLIC_BACKEND_URL.length > 0
      ? process.env.NEXT_PUBLIC_BACKEND_URL
      : "http://127.0.0.1:8000";
  return fallback;
}

/** @deprecated Prefer getBackendPublicUrl() — valor estático não reflecte proxy same-origin no browser. */
export const BACKEND_PUBLIC_URL = typeof process.env.NEXT_PUBLIC_BACKEND_URL === "string"
  ? process.env.NEXT_PUBLIC_BACKEND_URL
  : "http://127.0.0.1:8000";

function formatProblemDetail(payload: Record<string, unknown>) {
  const detail = payload.detail;
  if (typeof detail === "string") {
    return detail;
  }
  if (Array.isArray(detail) || typeof detail === "object") {
    try {
      return JSON.stringify(detail);
    } catch {
      return "Erro estrutural devolvido pelo backend.";
    }
  }

  return "Erro estrutural devolvido pelo backend.";
}

async function parseJsonResponse(response: Response): Promise<Record<string, unknown>> {
  try {
    return (await response.json()) as Record<string, unknown>;
  } catch {
    throw new Error(await response.text());
  }
}

/** Monta URLs absolutos para artefactos com caminhos relativos devolvidos pelo backend. */

export function toAbsoluteHref(relativePath: string | null | undefined): string | null {
  if (!relativePath || !relativePath.startsWith("/")) {
    return null;
  }

  const base = getBackendPublicUrl().replace(/\/$/, "");
  return `${base}${relativePath}`;
}

export async function postIngestFile(file: File, missionId?: string): Promise<unknown> {
  const form = new FormData();
  form.append("file", file);
  if (missionId) {
    form.append("mission_id", missionId);
  }

  const response = await apiFetch(`${PREFIX}/ingestion`, {
    method: "POST",
    headers: authorizedHeaders(),
    body: form,
  });

  if (!response.ok) {
    const payload = await parseJsonResponse(response);
    throw new Error(formatProblemDetail(payload));
  }

  return response.json() as unknown;
}

export async function fetchHdrVerification(hdrId: string): Promise<unknown> {
  const response = await apiFetch(`${PREFIX}/verify/${hdrId}`);
  const payload = await parseJsonResponse(response);

  if (!response.ok) {
    throw new Error(formatProblemDetail(payload));
  }

  return payload;
}

export async function fetchChainVerification(missionId: string): Promise<unknown> {
  const response = await apiFetch(`${PREFIX}/verify/chain/${missionId}`);
  const payload = await parseJsonResponse(response);

  if (!response.ok) {
    throw new Error(formatProblemDetail(payload));
  }

  return payload;
}

export async function planMission(description: string, authorizedAgents: string[]): Promise<unknown> {
  const response = await apiFetch(`${PREFIX}/mission/plan`, {
    method: "POST",
    headers: authorizedHeaders({ "Content-Type": "application/json" }),
    body: JSON.stringify({ description, authorized_agents: authorizedAgents }),
  });
  const payload = await parseJsonResponse(response);

  if (!response.ok) {
    throw new Error(formatProblemDetail(payload));
  }

  return payload;
}

export async function approveMission(missionId: string): Promise<unknown> {
  const response = await apiFetch(`${PREFIX}/mission/${missionId}/approve`, {
    method: "POST",
    headers: authorizedHeaders(),
  });
  const payload = await parseJsonResponse(response);

  if (!response.ok) {
    throw new Error(formatProblemDetail(payload));
  }

  return payload;
}

export async function rejectMission(missionId: string): Promise<unknown> {
  const response = await apiFetch(`${PREFIX}/mission/${missionId}/reject`, {
    method: "POST",
    headers: authorizedHeaders(),
  });
  const payload = await parseJsonResponse(response);

  if (!response.ok) {
    throw new Error(formatProblemDetail(payload));
  }

  return payload;
}

export async function executeMission(missionId: string): Promise<unknown> {
  const response = await apiFetch(`${PREFIX}/mission/${missionId}/execute`, {
    method: "POST",
    headers: authorizedHeaders(),
  });
  const payload = await parseJsonResponse(response);

  if (!response.ok) {
    throw new Error(formatProblemDetail(payload));
  }

  return payload;
}

export async function fetchMissionPlan(missionId: string): Promise<unknown> {
  const response = await apiFetch(`${PREFIX}/mission/${missionId}`, { headers: authorizedHeaders() });
  const payload = await parseJsonResponse(response);

  if (!response.ok) {
    throw new Error(formatProblemDetail(payload));
  }

  return payload;
}

export async function getDiary(search: Record<string, string | undefined>): Promise<unknown> {
  const query = new URLSearchParams();
  for (const [k, v] of Object.entries(search)) {
    if (v !== undefined && v !== "") {
      query.set(k, v);
    }
  }
  const qs = query.toString();
  const suffix = qs ? `?${qs}` : "";
  const response = await apiFetch(`${PREFIX}/mission/diary${suffix}`, {
    headers: authorizedHeaders(),
  });
  const payload = await parseJsonResponse(response);

  if (!response.ok) {
    throw new Error(formatProblemDetail(payload));
  }

  return payload;
}

export async function getDiaryStats(): Promise<unknown> {
  const response = await apiFetch(`${PREFIX}/mission/diary/stats`, { headers: authorizedHeaders() });
  const payload = await parseJsonResponse(response);

  if (!response.ok) {
    throw new Error(formatProblemDetail(payload));
  }

  return payload;
}

export async function fetchMobileQuickStats(): Promise<unknown> {
  const response = await apiFetch(`${PREFIX}/mobile/quick-stats`, { headers: authorizedHeaders() });
  const payload = await parseJsonResponse(response);
  if (!response.ok) {
    throw new Error(formatProblemDetail(payload));
  }
  return payload;
}

export async function fetchMobilePendingApprovals(): Promise<unknown> {
  const response = await apiFetch(`${PREFIX}/mobile/pending-approvals`, {
    headers: authorizedHeaders(),
  });
  const payload = await parseJsonResponse(response);

  if (!response.ok) {
    throw new Error(formatProblemDetail(payload));
  }

  return payload;
}

export async function registerPushTokenJson(subscriptionJson: string): Promise<unknown> {
  const response = await apiFetch(`${PREFIX}/mobile/push-token`, {
    method: "POST",
    headers: authorizedHeaders({ "Content-Type": "application/json" }),
    body: JSON.stringify({ subscription_json: subscriptionJson }),
  });
  const payload = await parseJsonResponse(response);

  if (!response.ok) {
    throw new Error(formatProblemDetail(payload));
  }

  return payload;
}

export async function generateForensicPackage(missionId: string, generatedBy: string): Promise<unknown> {
  const response = await apiFetch(`${PREFIX}/forensic/package/${missionId}?generated_by=${encodeURIComponent(generatedBy)}`, {
    method: "POST",
  });
  const payload = await parseJsonResponse(response);

  if (!response.ok) {
    throw new Error(formatProblemDetail(payload));
  }

  return payload;
}

export async function getNormativeRules(): Promise<unknown> {
  const response = await apiFetch(`${PREFIX}/normative/rules`);
  const payload = await parseJsonResponse(response);

  if (!response.ok) {
    throw new Error(formatProblemDetail(payload));
  }

  return payload;
}

export async function fetchComplianceFrameworks(): Promise<unknown> {
  const response = await apiFetch(`${PREFIX}/compliance/frameworks`);
  const payload = await parseJsonResponse(response);
  if (!response.ok) {
    throw new Error(formatProblemDetail(payload));
  }
  return payload;
}

export async function postComplianceReport(missionId: string, frameworkId = "LGPD-BR"): Promise<unknown> {
  const url = `${PREFIX}/compliance/report/${missionId}?framework_id=${encodeURIComponent(frameworkId)}`;
  const response = await apiFetch(url, {
    method: "POST",
    headers: authorizedHeaders(),
  });
  const payload = await parseJsonResponse(response);
  if (!response.ok) {
    throw new Error(formatProblemDetail(payload));
  }
  return payload;
}

export function complianceReportDownloadUrl(missionId: string, frameworkId = "LGPD-BR"): string {
  return `${PREFIX}/compliance/report/${encodeURIComponent(missionId)}/download?framework_id=${encodeURIComponent(frameworkId)}`;
}

export async function searchNormativeRules(query: string): Promise<unknown> {
  const response = await apiFetch(
    `${PREFIX}/normative/search?q=${encodeURIComponent(query)}&limit=20`,
  );
  const payload = await parseJsonResponse(response);
  if (!response.ok) {
    throw new Error(formatProblemDetail(payload));
  }
  return payload;
}

export async function loginLegalOperator(email: string, password: string): Promise<unknown> {
  const response = await apiFetch(`${PREFIX}/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password }),
  });
  const payload = await parseJsonResponse(response);

  if (!response.ok) {
    throw new Error(formatProblemDetail(payload));
  }

  return payload;
}

export async function registerLegalOperator(body: Record<string, unknown>): Promise<unknown> {
  const response = await apiFetch(`${PREFIX}/auth/register`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  const payload = await parseJsonResponse(response);

  if (!response.ok) {
    throw new Error(formatProblemDetail(payload));
  }

  persistAuthBearer(null);

  return payload;
}

export async function fetchCurrentUser(): Promise<unknown> {
  const response = await apiFetch(`${PREFIX}/auth/me`, { headers: authorizedHeaders() });
  const payload = await parseJsonResponse(response);
  if (!response.ok) {
    throw new Error(formatProblemDetail(payload));
  }
  return payload;
}

// ── Quota / Tier (Fase 26) ──────────────────────────────────────────────────

export interface QuotaSnapshot {
  organization_id: string;
  tier: "free" | "pro" | "team" | "enterprise";
  monthly_hdr_limit: number | null;
  used_in_period: number;
  remaining: number | null;
  period_start: string;
  period_end: string;
  is_exceeded: boolean;
  retention_days: number | null;
  forensic_pdf_enabled: boolean;
}

export async function fetchMyQuota(): Promise<QuotaSnapshot> {
  const response = await apiFetch(`${PREFIX}/me/quota`, { headers: authorizedHeaders() });
  const payload = await parseJsonResponse(response);
  if (!response.ok) {
    throw new Error(formatProblemDetail(payload));
  }
  return payload as unknown as QuotaSnapshot;
}

/**
 * Compute usage percent (0-1) and warning thresholds.
 * Returns null when unlimited (Pro/Team/Enterprise).
 */
export function quotaUsagePct(snap: QuotaSnapshot): number | null {
  if (snap.monthly_hdr_limit === null || snap.monthly_hdr_limit === 0) return null;
  return Math.min(snap.used_in_period / snap.monthly_hdr_limit, 1);
}

// ── API Keys (Fase 27) ─────────────────────────────────────────────────────

export interface ApiKeyPublic {
  api_key_id: string;
  name: string;
  prefix: string;
  last_used_at: string | null;
  revoked_at: string | null;
  created_at: string;
}

export interface ApiKeyMintResponse {
  api_key_id: string;
  name: string;
  plaintext_key: string;
  prefix: string;
  created_at: string;
}

export async function listApiKeys(): Promise<ApiKeyPublic[]> {
  const response = await apiFetch(`${PREFIX}/me/api-keys`, { headers: authorizedHeaders() });
  const payload = await parseJsonResponse(response);
  if (!response.ok) {
    throw new Error(formatProblemDetail(payload));
  }
  return payload as unknown as ApiKeyPublic[];
}

export async function mintApiKey(name: string): Promise<ApiKeyMintResponse> {
  const response = await apiFetch(`${PREFIX}/me/api-keys`, {
    method: "POST",
    headers: {
      ...authorizedHeaders(),
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ name }),
  });
  const payload = await parseJsonResponse(response);
  if (!response.ok) {
    throw new Error(formatProblemDetail(payload));
  }
  return payload as unknown as ApiKeyMintResponse;
}

export async function revokeApiKey(apiKeyId: string): Promise<void> {
  const response = await apiFetch(`${PREFIX}/me/api-keys/${encodeURIComponent(apiKeyId)}`, {
    method: "DELETE",
    headers: authorizedHeaders(),
  });
  if (!response.ok && response.status !== 204) {
    const payload = await parseJsonResponse(response);
    throw new Error(formatProblemDetail(payload));
  }
}

export async function listMissions(skip = 0, limit = 20): Promise<unknown> {
  const response = await apiFetch(`${PREFIX}/mission/?skip=${skip}&limit=${limit}`, {
    headers: authorizedHeaders(),
  });
  const payload = await parseJsonResponse(response);

  if (!response.ok) {
    throw new Error(formatProblemDetail(payload));
  }

  return payload;
}

export async function listAgentConfigs(): Promise<unknown> {
  const response = await apiFetch(`${PREFIX}/agent-config/`, { headers: authorizedHeaders() });
  const payload = await parseJsonResponse(response);

  if (!response.ok) {
    throw new Error(formatProblemDetail(payload));
  }

  return payload;
}

export async function putAgentModelConfig(agentId: string, patch: Record<string, unknown>): Promise<unknown> {
  const response = await apiFetch(`${PREFIX}/agent-config/${encodeURIComponent(agentId)}`, {
    method: "PUT",
    headers: authorizedHeaders({ "Content-Type": "application/json" }),
    body: JSON.stringify(patch),
  });
  const payload = await parseJsonResponse(response);

  if (!response.ok) {
    throw new Error(formatProblemDetail(payload));
  }

  return payload;
}

export async function testAgentModel(agentId: string): Promise<unknown> {
  const response = await apiFetch(`${PREFIX}/agent-config/${encodeURIComponent(agentId)}/test`, {
    method: "POST",
    headers: authorizedHeaders(),
  });
  const payload = await parseJsonResponse(response);

  if (!response.ok) {
    throw new Error(formatProblemDetail(payload));
  }

  return payload;
}

export async function logoutLegalOperator(): Promise<void> {
  try {
    await apiFetch(`${PREFIX}/auth/logout`, { method: "POST" });
  } catch {
    /* rede directa / offline */
  }
}

// ─── Privacy / LGPD Fase 14 ──────────────────────────────────────────────────

/** GET /privacy/dpo-contact — public, no auth */
export async function fetchDpoContact(): Promise<unknown> {
  const response = await apiFetch(`${PREFIX}/privacy/dpo-contact`);
  const payload = await parseJsonResponse(response);
  if (!response.ok) throw new Error(formatProblemDetail(payload));
  return payload;
}

/** POST /privacy/dpo-request — public, no auth */
export async function submitDpoRequest(body: Record<string, unknown>): Promise<unknown> {
  const response = await apiFetch(`${PREFIX}/privacy/dpo-request`, {
    method: "POST",
    headers: authorizedHeaders({ "Content-Type": "application/json" }),
    body: JSON.stringify(body),
  });
  const payload = await parseJsonResponse(response);
  if (!response.ok) throw new Error(formatProblemDetail(payload));
  return payload;
}

/** GET /privacy/dpo-requests — admin */
export async function listDpoRequests(statusFilter?: string): Promise<unknown> {
  const qs = statusFilter ? `?status=${encodeURIComponent(statusFilter)}` : "";
  const response = await apiFetch(`${PREFIX}/privacy/dpo-requests${qs}`, { headers: authorizedHeaders() });
  const payload = await parseJsonResponse(response);
  if (!response.ok) throw new Error(formatProblemDetail(payload));
  return payload;
}

/** GET /privacy/consent */
export async function fetchConsentBundle(): Promise<unknown> {
  const response = await apiFetch(`${PREFIX}/privacy/consent`, { headers: authorizedHeaders() });
  const payload = await parseJsonResponse(response);
  if (!response.ok) throw new Error(formatProblemDetail(payload));
  return payload;
}

/** POST /privacy/consent */
export async function setConsent(purpose: string, granted: boolean): Promise<unknown> {
  const response = await apiFetch(`${PREFIX}/privacy/consent`, {
    method: "POST",
    headers: authorizedHeaders({ "Content-Type": "application/json" }),
    body: JSON.stringify({ purpose, granted }),
  });
  const payload = await parseJsonResponse(response);
  if (!response.ok) throw new Error(formatProblemDetail(payload));
  return payload;
}

/** DELETE /privacy/consent — revoke all */
export async function revokeAllConsent(): Promise<unknown> {
  const response = await apiFetch(`${PREFIX}/privacy/consent`, {
    method: "DELETE",
    headers: authorizedHeaders(),
  });
  const payload = await parseJsonResponse(response);
  if (!response.ok) throw new Error(formatProblemDetail(payload));
  return payload;
}

/** GET /privacy/export — portability ZIP download URL */
export function privacyExportUrl(): string {
  return `${PREFIX}/privacy/export`;
}

/**
 * DELETE /privacy/account — elimina a conta (LGPD art. 18 VI).
 *
 * Anonimiza o cadastro, revoga API keys e consentimentos. PRESERVA HDRs
 * (cadeia de custódia imutável). Operação IRREVERSÍVEL — exige o token de
 * confirmação literal. Retorna 204 (sem corpo) em caso de sucesso.
 */
export async function deleteAccount(): Promise<void> {
  const response = await apiFetch(
    `${PREFIX}/privacy/account?confirm=CONFIRMO_ELIMINACAO`,
    {
      method: "DELETE",
      headers: authorizedHeaders(),
    },
  );
  if (response.status === 204) return;
  const payload = await parseJsonResponse(response);
  if (!response.ok) throw new Error(formatProblemDetail(payload));
}

/** POST /privacy/ripd */
export async function createRipd(body: Record<string, unknown>): Promise<unknown> {
  const response = await apiFetch(`${PREFIX}/privacy/ripd`, {
    method: "POST",
    headers: authorizedHeaders({ "Content-Type": "application/json" }),
    body: JSON.stringify(body),
  });
  const payload = await parseJsonResponse(response);
  if (!response.ok) throw new Error(formatProblemDetail(payload));
  return payload;
}

/** GET /privacy/ripd */
export async function listRipd(): Promise<unknown> {
  const response = await apiFetch(`${PREFIX}/privacy/ripd`, { headers: authorizedHeaders() });
  const payload = await parseJsonResponse(response);
  if (!response.ok) throw new Error(formatProblemDetail(payload));
  return payload;
}

/** GET /privacy/ripd/{id}/download — URL for PDF download */
export function ripdDownloadUrl(ripdId: string): string {
  return `${PREFIX}/privacy/ripd/${encodeURIComponent(ripdId)}/download`;
}

/** POST /security/incident */
export async function registerIncident(body: Record<string, unknown>): Promise<unknown> {
  const response = await apiFetch(`${PREFIX}/security/incident`, {
    method: "POST",
    headers: authorizedHeaders({ "Content-Type": "application/json" }),
    body: JSON.stringify(body),
  });
  const payload = await parseJsonResponse(response);
  if (!response.ok) throw new Error(formatProblemDetail(payload));
  return payload;
}

/** GET /security/incidents — admin */
export async function listIncidents(): Promise<unknown> {
  const response = await apiFetch(`${PREFIX}/security/incidents`, { headers: authorizedHeaders() });
  const payload = await parseJsonResponse(response);
  if (!response.ok) throw new Error(formatProblemDetail(payload));
  return payload;
}

/** POST /privacy/purge-logs — admin */
export async function purgeLogs(): Promise<unknown> {
  const response = await apiFetch(`${PREFIX}/privacy/purge-logs`, {
    method: "POST",
    headers: authorizedHeaders(),
  });
  const payload = await parseJsonResponse(response);
  if (!response.ok) throw new Error(formatProblemDetail(payload));
  return payload;
}

/* ─── Admin beta-metrics (Fase 30B3) ─────────────────────────────────────
 * Autenticação por token compartilhado (X-Heillon-Admin-Token), separado do
 * JWT de usuário. O operador também precisa estar logado (cookie de sessão)
 * para o middleware do Next deixar a requisição passar — defesa em profundidade.
 */

/** Tipos da resposta de /admin/beta-metrics. */
export interface BetaMetrics {
  snapshot_at: string;
  organizations: { total: number; by_tier: Record<string, number> };
  users: { total: number; active_last_7d: number };
  api_keys: { active: number; revoked: number; total: number };
  hdrs: {
    total: number;
    last_24h: number;
    last_7d: number;
    by_type: Record<string, number>;
    latest_at: string | null;
  };
}

export interface BetaFeedEvent {
  hdr_id: string;
  created_at: string;
  mission_id: string;
  hdr_type: string;
  organization_id: string;
}

/** GET /admin/beta-metrics */
export async function fetchBetaMetrics(adminToken: string): Promise<BetaMetrics> {
  const response = await apiFetch(`${PREFIX}/admin/beta-metrics`, {
    headers: authorizedHeaders({ "X-Heillon-Admin-Token": adminToken }),
  });
  const payload = await parseJsonResponse(response);
  if (!response.ok) throw new Error(formatProblemDetail(payload));
  return payload as unknown as BetaMetrics;
}

/** GET /admin/beta-feed */
export async function fetchBetaFeed(
  adminToken: string,
  limit = 20,
): Promise<{ events: BetaFeedEvent[]; count: number }> {
  const response = await apiFetch(`${PREFIX}/admin/beta-feed?limit=${limit}`, {
    headers: authorizedHeaders({ "X-Heillon-Admin-Token": adminToken }),
  });
  const payload = await parseJsonResponse(response);
  if (!response.ok) throw new Error(formatProblemDetail(payload));
  return payload as unknown as { events: BetaFeedEvent[]; count: number };
}
