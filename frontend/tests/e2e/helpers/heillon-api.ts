import { expect, type APIRequestContext } from "@playwright/test";

/** Caminho real do utilizador: browser → Next (3000) → proxy → FastAPI (8000). */
const API_PREFIX = "/api/v1";

export type AuthSession = {
  bearer: string;
  email: string;
};

export async function assertOk(
  response: Awaited<ReturnType<APIRequestContext["post"]>>,
  label: string,
): Promise<Record<string, unknown>> {
  const text = await response.text();
  let payload: Record<string, unknown> = {};
  try {
    payload = text ? (JSON.parse(text) as Record<string, unknown>) : {};
  } catch {
    payload = { raw: text };
  }
  expect(response.ok(), `${label} falhou (${response.status()}): ${JSON.stringify(payload)}`).toBeTruthy();
  return payload;
}

export async function registerOperator(
  request: APIRequestContext,
  email: string,
  password: string,
): Promise<AuthSession> {
  const reg = await request.post(`${API_PREFIX}/auth/register`, {
    data: {
      name: "Perito E2E",
      email,
      password,
      role: "perito",
    },
  });
  const body = await assertOk(reg, "registo");
  const bearer = String(body.access_token ?? "");
  expect(bearer.length).toBeGreaterThan(10);
  return { bearer, email };
}

function sessionHeaders(bearer: string): Record<string, string> {
  const headers: Record<string, string> = { "Content-Type": "application/json" };
  if (bearer) {
    headers.Authorization = `Bearer ${bearer}`;
  }
  return headers;
}

export async function planMission(
  request: APIRequestContext,
  bearer: string,
  description: string,
  authorizedAgents: string[],
): Promise<string> {
  const plan = await request.post(`${API_PREFIX}/mission/plan`, {
    headers: sessionHeaders(bearer),
    data: {
      description,
      authorized_agents: authorizedAgents,
    },
  });
  const body = await assertOk(plan, "planear missão");
  const missionId = String(body.mission_id ?? "");
  expect(missionId.length).toBeGreaterThan(0);
  const normative = body.normative_result as { allowed?: boolean } | undefined;
  expect(normative?.allowed, "Corpus normativo bloqueou a missão E2E").toBe(true);
  return missionId;
}

export async function approveMission(request: APIRequestContext, bearer: string, missionId: string): Promise<void> {
  const res = await request.post(`${API_PREFIX}/mission/${missionId}/approve`, {
    headers: sessionHeaders(bearer),
  });
  await assertOk(res, "aprovar missão");
}

export async function executeMission(
  request: APIRequestContext,
  bearer: string,
  missionId: string,
): Promise<Record<string, unknown>> {
  const res = await request.post(`${API_PREFIX}/mission/${missionId}/execute`, {
    headers: sessionHeaders(bearer),
  });
  const body = await assertOk(res, "executar missão");
  const totalHdrs = Number(body.total_hdrs ?? 0);
  expect(totalHdrs, "Execução deve gerar pelo menos um HDR").toBeGreaterThan(0);
  return body;
}

export async function verifyChainValid(request: APIRequestContext, missionId: string): Promise<void> {
  const res = await request.get(`${API_PREFIX}/verify/chain/${missionId}`);
  const body = await assertOk(res, "verificar cadeia");
  expect(body.valid).toBe(true);
}

export async function generateCompliance(
  request: APIRequestContext,
  bearer: string,
  missionId: string,
): Promise<Record<string, unknown>> {
  const res = await request.post(
    `${API_PREFIX}/compliance/report/${missionId}?framework_id=LGPD-BR`,
    { headers: sessionHeaders(bearer) },
  );
  return assertOk(res, "relatório LGPD");
}
