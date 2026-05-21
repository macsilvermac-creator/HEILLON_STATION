import { expect, test } from "@playwright/test";

const backendUrl = process.env.NEXT_PUBLIC_BACKEND_URL || "http://127.0.0.1:8000";

test.describe("Full User Journey — Heillon Legal", () => {
  test.setTimeout(120_000);

  test.beforeAll(async () => {
    try {
      const res = await fetch(`${backendUrl.replace(/\/$/, "")}/health`);
      if (!res.ok) {
        test.skip(true, "Backend não disponível — ignorar jornada completa.");
      }
    } catch {
      test.skip(true, "Backend não disponível — ignorar jornada completa.");
    }
  });

  test("Registo → missão → verificação → conformidade → docs", async ({ page }) => {
    const testEmail = `e2e-${Date.now()}@test.com`;
    const testPassword = "securepassword123";

    await page.goto("/register");
    await page.getByLabel("Nome").fill("Perito E2E");
    await page.getByLabel("Email").fill(testEmail);
    await page.getByLabel(/Password/i).fill(testPassword);
    await page.getByLabel("Função").selectOption("perito");
    await page.getByRole("button", { name: /Criar conta/i }).click();
    await expect(page).toHaveURL(/\/dashboard/, { timeout: 30_000 });

    await page.goto("/");
    await expect(page.locator("[data-tour='mission-input']")).toBeVisible();
    await page
      .locator("[data-tour='mission-input']")
      .fill("Analisar documentos financeiros e identificar cláusulas de risco");
    await page.getByRole("button", { name: /Planear DAG/i }).click();
    await expect(page.getByText(/DAG proposto/i)).toBeVisible({ timeout: 30_000 });

    const missionLink = page.locator("[data-mission-id]").first();
    await expect(missionLink).toBeVisible({ timeout: 30_000 });
    const missionId = (await missionLink.getAttribute("data-mission-id"))?.trim() || "";
    expect(missionId.length).toBeGreaterThan(0);

    await page.getByRole("button", { name: /^Aprovar$/i }).click();
    await page.getByRole("button", { name: /^Executar$/i }).click();
    await expect(page.getByText(/Resultado execução/i)).toBeVisible({ timeout: 45_000 });

    await page.goto("/verification");
    await page.getByLabel(/Missão inteira/i).check();
    await page.getByPlaceholder("mission_xxx").fill(missionId);
    await page.getByRole("button", { name: /Validar custódia/i }).click();
    await expect(page.locator("pre")).toContainText(/"valid":\s*true/i, { timeout: 30_000 });

    await page.goto("/normative");
    await page.getByPlaceholder(/mission_id/i).fill(missionId);
    await page.getByRole("button", { name: /Gerar \(LGPD-BR\)/i }).click();
    await expect(page.getByText(/LGPD|conformidade|Compliance/i).first()).toBeVisible({
      timeout: 30_000,
    });

    await page.goto("/docs");
    await expect(page.getByRole("heading", { name: /Central de Documentação/i })).toBeVisible();
    await page.getByRole("link", { name: /Manual de uso geral/i }).click();
    await expect(page.getByRole("heading", { name: /Introdução/i })).toBeVisible({ timeout: 15_000 });
  });
});
