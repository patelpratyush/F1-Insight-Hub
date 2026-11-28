import { spawn, type ChildProcess } from "node:child_process";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { expect, test, type Page } from "@playwright/test";

// Replays a recorded session through the real poller code (apps/worker/scripts/replay_live.py)
// into Redis; the browser streams it from the api. Needs the api (with Redis) running, like CI.
const REPO = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "../../..");
const FIXTURE = "apps/worker/tests/fixtures/live_replay_9999.jsonl";

function startReplay(): ChildProcess {
  return spawn("uv", ["run", "python", "apps/worker/scripts/replay_live.py", FIXTURE, "--speed", "5"], {
    cwd: REPO,
    env: process.env,
    stdio: ["ignore", "pipe", "inherit"],
  });
}

/** Resolves once the replay prints a line matching `pattern` (it flushes line by line). */
function waitForOutput(proc: ChildProcess, pattern: RegExp): Promise<void> {
  return new Promise((resolve, reject) => {
    let buf = "";
    proc.stdout?.on("data", (chunk: Buffer) => {
      buf += chunk.toString();
      if (pattern.test(buf)) resolve();
    });
    proc.on("exit", (code) => reject(new Error(`replay exited (${code}) before ${pattern}`)));
  });
}

const towerOrder = (page: Page) =>
  page.locator("[data-flip-key]").evaluateAll((rows) => rows.map((r) => r.getAttribute("data-flip-key")));

test.describe("live race centre", () => {
  let replay: ChildProcess | undefined;
  test.afterEach(() => {
    replay?.kill();
  });

  test("tower follows the replay, goes stale during a gap and recovers", async ({ page }) => {
    test.setTimeout(120_000);
    // The replay first clears live:9999* (seq restarts at 1); open the page only after that, or
    // it would keep a previous run's higher seq and ignore the new entries.
    replay = startReplay();
    await waitForOutput(replay, /published seq=\d+ /); // first batch is in, keys were reset
    await page.goto("/live/9999");
    await expect(page.getByText("Unofficial, community data (OpenF1)")).toBeVisible();
    // After the scripted overtake (16 passes 4) and 81 retiring, before the 25 s pause.
    await expect.poll(() => towerOrder(page), { timeout: 30_000 }).toEqual(["1", "16", "4", "44", "81"]);
    await expect(page.getByRole("row", { name: /81/ })).toContainText("OUT");
    await expect(page.getByText("+1 LAP")).toBeVisible();

    // The fixture pauses 25 s; the page marks the feed stale after 20 s of silence.
    const stale = page.getByRole("alert").filter({ hasText: "gone quiet" });
    await expect(stale).toBeVisible({ timeout: 30_000 });
    // The replay resumes; the banner clears on the next update.
    await expect(stale).toBeHidden({ timeout: 15_000 });
  });

  test("an unknown session shows the waiting state, never an empty tower", async ({ page }) => {
    await page.goto("/live/123456789");
    await expect(page.getByText("Waiting for live data")).toBeVisible();
    await expect(page.getByRole("table", { name: "Live timing tower" })).toHaveCount(0);
  });
});
