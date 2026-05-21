import { expect, test } from "@playwright/test";

test.describe("Heillon Legal — smoke (frontend)", () => {
  test("Docs Hub carrega", async ({ page }) => {
    await page.goto("/docs");
    await expect(page.getByRole("heading", { name: /Central de Documentação/i })).toBeVisible();
  });

  test("Página de login renderiza", async ({ page }) => {
    await page.goto("/login");
    await expect(page.getByRole("heading", { name: /Bem-vindo/i })).toBeVisible();
  });
});
