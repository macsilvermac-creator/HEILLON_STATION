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
  const headers = new Headers(extra);
  if (typeof window !== "undefined") {
    const token = window.localStorage.getItem("heillon_bearer");
    if (token) headers.set("Authorization", `Bearer ${token}`);
  }
  return headers;
}

export function persistAuthBearer(token: string | null): void {
  if (typeof window === "undefined") return;
  if (!token || token.trim().length === 0) window.localStorage.removeItem("heillon_bearer");
  else window.localStorage.setItem("heillon_bearer", token.trim());
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

  const response = await fetch(`${PREFIX}/ingestion`, {
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
  const response = await fetch(`${PREFIX}/verify/${hdrId}`);
  const payload = await parseJsonResponse(response);

  if (!response.ok) {
    throw new Error(formatProblemDetail(payload));
  }

  return payload;
}

export async function fetchChainVerification(missionId: string): Promise<unknown> {
  const response = await fetch(`${PREFIX}/verify/chain/${missionId}`);
  const payload = await parseJsonResponse(response);

  if (!response.ok) {
    throw new Error(formatProblemDetail(payload));
  }

  return payload;
}

export async function planMission(description: string, authorizedAgents: string[]): Promise<unknown> {
  const response = await fetch(`${PREFIX}/mission/plan`, {
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
  const response = await fetch(`${PREFIX}/mission/${missionId}/approve`, {
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
  const response = await fetch(`${PREFIX}/mission/${missionId}/reject`, {
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
  const response = await fetch(`${PREFIX}/mission/${missionId}/execute`, {
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
  const response = await fetch(`${PREFIX}/mission/${missionId}`, { headers: authorizedHeaders() });
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
  const response = await fetch(`${PREFIX}/mission/diary${suffix}`, {
    headers: authorizedHeaders(),
  });
  const payload = await parseJsonResponse(response);

  if (!response.ok) {
    throw new Error(formatProblemDetail(payload));
  }

  return payload;
}

export async function getDiaryStats(): Promise<unknown> {
  const response = await fetch(`${PREFIX}/mission/diary/stats`, { headers: authorizedHeaders() });
  const payload = await parseJsonResponse(response);

  if (!response.ok) {
    throw new Error(formatProblemDetail(payload));
  }

  return payload;
}

export async function fetchMobileQuickStats(): Promise<unknown> {
  const response = await fetch(`${PREFIX}/mobile/quick-stats`, { headers: authorizedHeaders() });
  const payload = await parseJsonResponse(response);
  if (!response.ok) {
    throw new Error(formatProblemDetail(payload));
  }
  return payload;
}

export async function fetchMobilePendingApprovals(): Promise<unknown> {
  const response = await fetch(`${PREFIX}/mobile/pending-approvals`, {
    headers: authorizedHeaders(),
  });
  const payload = await parseJsonResponse(response);

  if (!response.ok) {
    throw new Error(formatProblemDetail(payload));
  }

  return payload;
}

export async function registerPushTokenJson(subscriptionJson: string): Promise<unknown> {
  const response = await fetch(`${PREFIX}/mobile/push-token`, {
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
  const response = await fetch(`${PREFIX}/forensic/package/${missionId}?generated_by=${encodeURIComponent(generatedBy)}`, {
    method: "POST",
  });
  const payload = await parseJsonResponse(response);

  if (!response.ok) {
    throw new Error(formatProblemDetail(payload));
  }

  return payload;
}

export async function getNormativeRules(): Promise<unknown> {
  const response = await fetch(`${PREFIX}/normative/rules`);
  const payload = await parseJsonResponse(response);

  if (!response.ok) {
    throw new Error(formatProblemDetail(payload));
  }

  return payload;
}

export async function fetchComplianceFrameworks(): Promise<unknown> {
  const response = await fetch(`${PREFIX}/compliance/frameworks`);
  const payload = await parseJsonResponse(response);
  if (!response.ok) {
    throw new Error(formatProblemDetail(payload));
  }
  return payload;
}

export async function postComplianceReport(missionId: string, frameworkId = "LGPD-BR"): Promise<unknown> {
  const url = `${PREFIX}/compliance/report/${missionId}?framework_id=${encodeURIComponent(frameworkId)}`;
  const response = await fetch(url, {
    method: "POST",
    headers: authorizedHeaders(),
  });
  const payload = await parseJsonResponse(response);
  if (!response.ok) {
    throw new Error(formatProblemDetail(payload));
  }
  return payload;
}

export async function loginLegalOperator(email: string, password: string): Promise<unknown> {
  const response = await fetch(`${PREFIX}/auth/login`, {
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
  const response = await fetch(`${PREFIX}/auth/register`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  const payload = await parseJsonResponse(response);

  if (!response.ok) {
    throw new Error(formatProblemDetail(payload));
  }

  const tokenCandidate = typeof payload.access_token === "string" ? payload.access_token : null;
  if (tokenCandidate) persistAuthBearer(tokenCandidate);

  return payload;
}

export async function fetchCurrentUser(): Promise<unknown> {
  const response = await fetch(`${PREFIX}/auth/me`, { headers: authorizedHeaders() });
  const payload = await parseJsonResponse(response);
  if (!response.ok) {
    throw new Error(formatProblemDetail(payload));
  }
  return payload;
}

export async function listMissions(skip = 0, limit = 20): Promise<unknown> {
  const response = await fetch(`${PREFIX}/mission/?skip=${skip}&limit=${limit}`, {
    headers: authorizedHeaders(),
  });
  const payload = await parseJsonResponse(response);

  if (!response.ok) {
    throw new Error(formatProblemDetail(payload));
  }

  return payload;
}

export async function listAgentConfigs(): Promise<unknown> {
  const response = await fetch(`${PREFIX}/agent-config/`, { headers: authorizedHeaders() });
  const payload = await parseJsonResponse(response);

  if (!response.ok) {
    throw new Error(formatProblemDetail(payload));
  }

  return payload;
}

export async function putAgentModelConfig(agentId: string, patch: Record<string, unknown>): Promise<unknown> {
  const response = await fetch(`${PREFIX}/agent-config/${encodeURIComponent(agentId)}`, {
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
  const response = await fetch(`${PREFIX}/agent-config/${encodeURIComponent(agentId)}/test`, {
    method: "POST",
    headers: authorizedHeaders(),
  });
  const payload = await parseJsonResponse(response);

  if (!response.ok) {
    throw new Error(formatProblemDetail(payload));
  }

  return payload;
}
