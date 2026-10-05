import { test, expect } from "@playwright/test";
async function login(page: import("@playwright/test").Page, role = "admin") {
  await page.goto("/login"); await page.getByLabel("Email", { exact: true }).fill(`${role}@example.test`); await page.getByLabel("Password", { exact: true }).fill("synthetic-password"); await page.getByRole("button", { name: "Sign in", exact: true }).click(); await expect(page).toHaveURL(/module=Dashboard/); await expect(page.locator(".identity")).toBeVisible();
}
test("login, role navigation, unchanged logo and logout session cleanup", async ({ page, context }) => {
  await login(page);
  await expect(page.getByText("Synthetic Admin", { exact: true })).toBeVisible();
  await expect(page.getByRole("button", { name: "Dashboard", exact: true })).toBeVisible();
  const cookie = (await context.cookies()).find(c => c.name === "axyrel_session"); expect(cookie?.httpOnly).toBe(true); expect(cookie?.sameSite).toBe("Strict");
  expect(await page.evaluate(() => document.cookie)).not.toContain("synthetic-admin-token");
  expect(await page.evaluate(() => localStorage.length)).toBe(0);
  const image = page.locator(".brand-image"); await expect(image).toHaveAttribute("src", "/brand/axyrel-logo.png");
  expect(await image.evaluate((img: HTMLImageElement) => img.naturalWidth > 0 && Math.abs(img.width / img.height - img.naturalWidth / img.naturalHeight) < 0.02)).toBe(true);
  await page.route("**/api/backend/customers", route => route.fulfill({ json: [] }));
  await page.getByRole("button", { name: "Schedule", exact: true }).click(); await expect(page.getByRole("heading", { name: "Schedule", exact: true })).toBeVisible();
  await page.getByRole("button", { name: "Sign out" }).click(); await expect(page).toHaveURL(/\/login$/); expect((await context.cookies()).some(c => c.name === "axyrel_session")).toBe(false);
  await login(page, "technician"); await expect(page.getByText("Synthetic Technician", { exact: true })).toBeVisible(); await expect(page.getByRole("button", { name: "Invoices", exact: true })).toHaveCount(0);
});
test("incorrect credentials, unauthenticated request and origin protection", async ({ page, request }) => {
  await page.goto("/login"); await page.getByLabel("Email", { exact: true }).fill("admin@example.test"); await page.getByLabel("Password", { exact: true }).fill("wrong"); await page.getByRole("button", { name: "Sign in", exact: true }).click(); await expect(page.locator("form [role='alert']")).toContainText("Incorrect email or password");
  expect((await request.get("/api/backend/auth/me")).status()).toBe(401);
  expect((await request.post("/api/auth/logout", { headers: { Origin: "https://foreign.example" } })).status()).toBe(403);
  expect((await request.get("/api/backend/not-approved")).status()).toBe(404);
  await page.goto("/workspace"); await expect(page.getByRole("heading", { name: "Sign in to continue" })).toBeVisible();
});
test("mobile navigation, RTL logical layout and keyboard entry", async ({ page }) => {
  await page.route("**/api/backend/customers", route => route.fulfill({ json: [] }));
  await page.setViewportSize({ width: 390, height: 844 }); await page.goto("/login"); await page.keyboard.press("Tab"); await expect(page.getByLabel("Email", { exact: true })).toBeFocused(); await login(page, "technician");
  await page.getByRole("button", { name: "Toggle navigation" }).click(); await expect(page.getByRole("button", { name: "Schedule", exact: true })).toBeVisible();
  await page.getByRole("button", { name: "Schedule", exact: true }).click(); await expect(page.getByRole("heading", { name: "Schedule", exact: true })).toBeVisible();
  await page.evaluate(() => { document.documentElement.dir = "rtl"; }); await page.getByRole("button", { name: "Toggle navigation" }).click();
  const side = await page.locator(".sidebar").boundingBox(); expect(side && side.x > 100).toBeTruthy();
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBe(true);
});
test("safe forwarding, permission failure and no cross-origin mutation", async ({ page, request }) => {
  await login(page);
  const permission = await page.evaluate(async () => { const r = await fetch("/api/backend/customers"); return { status: r.status, body: await r.json() }; });
  expect(permission).toEqual({ status: 403, body: { detail: "Insufficient permissions" } });
  expect((await request.post("/api/backend/customers", { headers: { Origin: "https://foreign.example" }, data: {} })).status()).toBe(403);
  expect((await request.get("/api/backend/https%3A%2F%2Fforeign.example")).status()).toBe(404);
});
test("shared loading, safe error/retry and permission states", async ({ page }) => {
  await page.route("**/api/backend/auth/me", async route => { await new Promise(resolve => setTimeout(resolve, 400)); await route.fulfill({ status: 503, contentType: "application/json", body: '{"detail":"synthetic-private-diagnostic"}' }); });
  await page.goto("/workspace"); await expect(page.getByRole("status")).toBeVisible(); await expect(page.locator("section[role='alert']")).toContainText("Unable to load"); await expect(page.getByRole("button", { name: "Try again" })).toBeVisible(); await expect(page.getByText("synthetic-private-diagnostic")).toHaveCount(0);
  await page.unroute("**/api/backend/auth/me"); await page.route("**/api/backend/auth/me", route => route.fulfill({ status: 403, contentType: "application/json", body: '{"detail":"Insufficient permissions"}' }));
  await page.getByRole("button", { name: "Try again" }).click(); await expect(page.getByRole("heading", { name: "Access unavailable" })).toBeVisible();
});
