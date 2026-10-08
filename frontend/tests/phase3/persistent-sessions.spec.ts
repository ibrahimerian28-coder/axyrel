import { test, expect, chromium } from "@playwright/test";
import { mkdtemp } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join } from "node:path";

const origin = `http://127.0.0.1:${process.env.AXYREL_TEST_FRONTEND_PORT || 3130}`;
const backend = `http://127.0.0.1:${process.env.AXYREL_PHASE3_TEST_PORT || 8130}`;

test("persistent cookie survives browser restart, renews on use, and Logout revokes reuse", async () => {
  const profile = await mkdtemp(join(tmpdir(), "axyrel-session-browser-"));
  let context = await chromium.launchPersistentContext(profile, { headless: true });
  try {
    let page = await context.newPage();
    await page.goto(`${origin}/login`);
    await page.getByLabel("Email", { exact: true }).fill("admin@example.test");
    await page.getByLabel("Password", { exact: true }).fill("synthetic-password");
    await page.getByRole("button", { name: "Sign in", exact: true }).click();
    await expect(page.locator(".identity")).toBeVisible();
    const credential = (await context.cookies()).find(c => c.name === "axyrel_session")!;
    expect(credential.httpOnly).toBe(true); expect(credential.sameSite).toBe("Strict");
    expect(credential.secure).toBe(false); // Disposable local HTTP; HTTPS uses Secure.
    expect(credential.expires).toBeGreaterThan(Date.now() / 1000 + 390 * 86400);
    expect(await page.evaluate(() => document.cookie.includes("axyrel_session"))).toBe(false);
    expect(await page.evaluate(() => localStorage.length + sessionStorage.length)).toBe(0);
    // Shorten only the browser retention to verify successful use renews it.
    await context.addCookies([{ ...credential, expires: Date.now() / 1000 + 3600 }]);
    expect((await context.request.get(`${origin}/api/backend/auth/me`)).ok()).toBe(true);
    expect((await context.cookies()).find(c => c.name === "axyrel_session")!.expires).toBeGreaterThan(Date.now() / 1000 + 390 * 86400);
    await context.close();
    context = await chromium.launchPersistentContext(profile, { headless: true });
    page = await context.newPage();
    await page.goto(`${origin}/workspace`); await expect(page.locator(".identity")).toBeVisible();
    expect((await context.cookies()).find(c => c.name === "axyrel_session")?.value === credential.value).toBe(true);
    const csrf = await context.request.post(`${origin}/api/auth/logout`, { headers: { Origin: "https://foreign.example" } });
    expect(csrf.status()).toBe(403);
    expect((await context.request.get(`${origin}/api/backend/auth/me`)).ok()).toBe(true);
    await page.getByRole("button", { name: "Sign out", exact: true }).click(); await expect(page).toHaveURL(/login/);
    expect((await context.cookies()).some(c => c.name === "axyrel_session")).toBe(false);
    const reuse = await context.request.get(`${backend}/api/v1/auth/me`, { headers: { Authorization: `Bearer ${credential.value}` } });
    expect(reuse.status()).toBe(401);
  } finally { await context.close(); }
});
