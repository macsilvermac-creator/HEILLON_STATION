import { expect, test } from "@playwright/test";

const backendUrl = (process.env.NEXT_PUBLIC_BACKEND_URL || "http://127.0.0.1:8000").replace(/\/$/, "");

test.describe("Full User Journey — Heillon Legal", () => {
  test.describe.configure({ mode: "serial" });
  test.setTimeout(120_000);

  test.beforeAll(async () => {
    try {
      const res = await fetch(`${backendUrl}/health`);
      if (!res.ok) {
        test.skip(true, "Backend não disponível — ignorar jornada completa.");
      }
    } catch {
      test.skip(true, "Backend não disponível — ignorar jornada completa.");
    }
  });

  test("Registo → missão → verificação → conformidade → docs", async ({ page, request }) => {
    const testEmail = `e2e-${Date.now()}@test.com`;
    const testPassword = "securepassword123";

    await page.goto("/register");
    await page.getByLabel("Nome").fill("Perito E2E");
    await page.getByLabel("Email").fill(testEmail);
    await page.getByLabel(/Password/i).fill(testPassword);
    await page.getByLabel("Função").selectOption("perito");
    await page.getByRole("button", { name: /Criar conta/i }).click();
    await expect(page).toHaveURL(/\/dashboard/, { timeout: 30_000 });

    const token = await page.waitForFunction(
      () => localStorage.getItem("heillon_bearer"),
      null,
      { timeout: 15_000 },
    );
    const bearer = (await token.jsonValue()) as string;
    expect(bearer.length).toBeGreaterThan(10);

    const authHeaders = { Authorization: `Bearer ${bearer}` };

    const planRes = await request.post(`${backendUrl}/api/v1/mission/plan`, {
      headers: { ...authHeaders, "Content-Type": "application/json" },
      data: {
        description: "Analisar documentos financeiros e identificar cláusulas de risco",
        authorized_agents: ["ocr-agent", "classification-agent", "analysis-agent"],
      },
    });
    expect(planRes.ok()).toBeTruthy();
    const planBody = (await planRes.json()) as { mission_id?: string };
    const missionId = planBody.mission_id || "";
    expect(missionId.length).toBeGreaterThan(0);

    const approveRes = await request.post(`${backendUrl}/api/v1/mission/${missionId}/approve`, {
      headers: authHeaders,
    });
    expect(approveRes.ok()).toBeTruthy();

    const executeRes = await request.post(`${backendUrl}/api/v1/mission/${missionId}/execute`, {
      headers: authHeaders,
    });
    expect(executeRes.ok()).toBeTruthy();

    await page.goto("/verification");
    await page.getByLabel(/Missão inteira/i).check();
    await page.getByPlaceholder("mission_xxx").fill(missionId);
    await page.getByRole("button", { name: /Validar custódia/i }).click();
    await expect(page.locator("pre")).toContainText(/"valid":\s*true|"valid": true/i, { timeout: 30_000 });

    await page.goto("/normative");
    await page.getByPlaceholder(/mission_id/i).fill(missionId);
    await page.getByRole("button", { name: /Gerar \(LGPD-BR\)/i }).click();
    await expect(page.getByText("Relatório", { exact: true })).toBeVisible({ timeout: 30_000 });

    await page.goto("/docs");
    await expect(page.getByRole("heading", { name: /Central de Documentação/i })).toBeVisible();
    await page.getByRole("link", { name: /Manual de uso geral/i }).click();
    await expect(page.getByRole("heading", { name: "Introdução" })).toBeVisible({ timeout: 15_000 });
  });
});
