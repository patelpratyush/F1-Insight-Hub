import { expect, test, type Page } from "@playwright/test";

// Seeded by apps/worker/scripts/seed_browse.py: 2025 rounds 1-2, round 1 results, constructor standings.
// The seeded season is in the past, so the home card shows the season's last race.

const teamVar = (page: Page, testId: string) =>
  page.getByTestId(testId).evaluate((el) => getComputedStyle(el).getPropertyValue("--team").trim());

test("home shows the next race card", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByText("Season complete")).toBeVisible();
  await expect(page.getByRole("heading", { name: "Chinese Grand Prix" })).toBeVisible();
});

test("command palette search navigates to the driver", async ({ page }) => {
  await page.goto("/");
  await page.keyboard.press("ControlOrMeta+k");
  await page.getByPlaceholder("Search drivers, races, sessions").fill("norris");
  await expect(page.getByRole("option", { name: /Lando Norris/ })).toBeVisible();
  await page.keyboard.press("Enter");
  await expect(page).toHaveURL(/\/drivers\/norris$/);
  await expect(page.getByRole("heading", { name: "Lando Norris" })).toBeVisible();
});

test("calendar links to a race page with results", async ({ page }) => {
  await page.goto("/calendar");
  await expect(page.getByText("Sprint", { exact: true })).toBeVisible();
  await page.getByRole("link", { name: "Australian Grand Prix" }).click();
  await expect(page).toHaveURL(/\/races\/2025\/1$/);
  const table = page.getByRole("table");
  await expect(table.getByRole("link", { name: "Max Verstappen" })).toBeVisible();
  await expect(table.getByText("DNF")).toBeVisible();
  await expect(table.getByText("Retired")).toBeVisible();
  await expect(page.getByRole("tab", { name: "Sprint" })).toHaveCount(0);
});

test("driver page accent colour equals the team colour", async ({ page }) => {
  await page.goto("/drivers/norris");
  const driver = await teamVar(page, "driver-header");
  await page.getByRole("link", { name: "McLaren" }).click();
  await expect(page).toHaveURL(/\/teams\/mclaren$/);
  const team = await teamVar(page, "team-header");
  expect(driver).toBe(team);
  expect(team.toUpperCase()).toBe("#FF8000");
});
