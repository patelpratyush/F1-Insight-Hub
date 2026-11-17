import { expect, test } from "@playwright/test";

test("unauthenticated user is redirected to sign-in with next param", async ({ page }) => {
  await page.goto("/standings");
  await expect(page).toHaveURL(/\/sign-in\?next=%2Fstandings/);
});

test("sign up, return to standings, and see ingested data", async ({ page }) => {
  const email = `e2e-${Date.now()}@example.com`;
  await page.goto("/sign-up");
  await page.getByLabel("Name").fill("E2E User");
  await page.getByLabel("Email").fill(email);
  await page.getByLabel("Password").fill("correct-horse-battery");
  await page.getByRole("button", { name: "Sign up" }).click();
  await expect(page).toHaveURL(/\/standings/);
  await expect(page.getByRole("heading", { name: "Driver Standings" })).toBeVisible();
  await expect(page.getByRole("row").first()).toBeVisible();
  await expect(page.getByText(/Updated|stale|No data yet/)).toBeVisible();
});

test("signed-out user signs in and is returned to standings", async ({ page }) => {
  const email = `e2e-return-${Date.now()}@example.com`;
  const password = "correct-horse-battery";
  await page.goto("/sign-up");
  await page.getByLabel("Name").fill("E2E Return");
  await page.getByLabel("Email").fill(email);
  await page.getByLabel("Password").fill(password);
  await page.getByRole("button", { name: "Sign up" }).click();
  await expect(page).toHaveURL(/\/standings/);
  await page.context().clearCookies();

  await page.goto("/standings");
  await expect(page).toHaveURL(/\/sign-in\?next=%2Fstandings/);
  await page.getByLabel("Email").fill(email);
  await page.getByLabel("Password").fill(password);
  await page.getByRole("button", { name: "Sign in" }).click();
  await expect(page).toHaveURL(/\/standings$/);
  await expect(page.getByRole("heading", { name: "Driver Standings" })).toBeVisible();
});

test("open redirect via next param is ignored", async ({ page }) => {
  const email = `e2e-redirect-${Date.now()}@example.com`;
  const password = "correct-horse-battery";
  await page.goto("/sign-up");
  await page.getByLabel("Name").fill("E2E Redirect");
  await page.getByLabel("Email").fill(email);
  await page.getByLabel("Password").fill(password);
  await page.getByRole("button", { name: "Sign up" }).click();
  await expect(page).toHaveURL(/\/standings/);
  await page.context().clearCookies();

  await page.goto("/sign-in?next=https://evil.com");
  await page.getByLabel("Email").fill(email);
  await page.getByLabel("Password").fill(password);
  await page.getByRole("button", { name: "Sign in" }).click();
  await expect(page).toHaveURL("http://localhost:3000/standings");
});
