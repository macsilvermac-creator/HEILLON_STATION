import { expect, test } from "@playwright/test";

import {
  approveMission,
  executeMission,
  generateCompliance,
  planMission,
  registerOperator,
  verifyChainValid,
} from "./helpers/heillon-api";

const BACKEND_HEALTH =
  (process.env.BACKEND_HEALTH_URL || process.env.NEXT_PUBLIC_BACKEND_URL || "http://127.0.0.1:8000").replace(
    /\/$/,
    "",
  );

/** Descrição e agentes alinhados ao teste de integração backend (normativa permite + 2 HDRs). */
const MISSION_DESCRIPTION = "Analyze financial documents for risk and prioritize by relevance";
const MISSION_AGENTS = ["analysis-agent", "prioritization-agent"];

test.describe("Jornada completa — Heillon Legal", () => {
  test.describe.configure({ mode: "serial" });
  test.setTimeout(120_000);

  test.beforeAll(async ({ request }) => {
    try {
      const res = await request.get(`${BACKEND_HEALTH}/health`);
      expect(res.ok()).toBeTruthy();
    } catch {
      test.skip(true, "Backend indisponível para E2E.");
    }
  });

  test("UI registo + API via proxy + verificação + conformidade + docs", async ({ page }) => {
    const api = page.request;
    const testEmail = `e2e-${Date.now()}@heillon.test`;
    const testPassword = "securepassword123";

    await page.goto("/register");
    await page.getByLabel("Nome").fill("Perito E2E");
    await page.getByLabel("Email").fill(testEmail);
    await page.getByLabel(/Password/i).fill(testPassword);
    await page.getByLabel("Função").selectOption("perito");
    await page.getByRole("button", { name: /Criar conta/i }).click();
    await expect(page).toHaveURL(/\/dashboard/, { timeout: 30_000 });

    // Obtain bearer via API (cookie auth is set by the browser; bearer used for API helper calls).
    const session = await registerOperator(api, testEmail, testPassword);
    const { bearer } = session;
    expect(bearer.length).toBeGreaterThan(10);

    const missionId = await planMission(api, bearer, MISSION_DESCRIPTION, MISSION_AGENTS);
    await approveMission(api, bearer, missionId);
    await executeMission(api, bearer, missionId);
    await verifyChainValid(api, missionId);

    await page.goto("/verification");
    await page.getByLabel(/Missão inteira/i).check();
    await page.getByPlaceholder("mission_xxx").fill(missionId);
    await page.getByRole("button", { name: /Validar custódia/i }).click();
    await expect(page.locator("pre")).toContainText(/"valid":\s*true|"valid": true/i, {
      timeout: 30_000,
    });

    await page.goto("/normative");
    await expect(page.getByPlaceholder(/mission_id/i)).toBeVisible({ timeout: 30_000 });
    await page.getByPlaceholder(/mission_id/i).fill(missionId);
    const reportBtn = page.getByRole("button", { name: /Gerar \(LGPD-BR\)/i });
    await expect(reportBtn).toBeEnabled({ timeout: 30_000 });
    await reportBtn.click();
    await expect(page.getByText("Relatório", { exact: true })).toBeVisible({ timeout: 30_000 });

    const reportViaApi = await generateCompliance(api, bearer, missionId);
    expect(reportViaApi.framework_id ?? reportViaApi.mission_id).toBeTruthy();

    await page.goto("/docs");
    await expect(page.getByRole("heading", { name: /Central de Documentação/i })).toBeVisible();
    await page.getByRole("link", { name: /Manual de uso geral/i }).click();
    await expect(page.getByRole("heading", { name: "Introdução" })).toBeVisible({ timeout: 15_000 });
  });
});
