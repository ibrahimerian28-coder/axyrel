import { test, expect } from "@playwright/test";

for (const status of [500, 403, 401, "network", "timeout"] as const) {
  test(`BFF upstream ${status} retains credentials except definitive 401`, async ({ page, request }) => {
    test.setTimeout(60000);
    await page.goto("/login");
    await page.getByLabel("Email", { exact: true }).fill("admin@example.test");
    await page.getByLabel("Password", { exact: true }).fill("synthetic-password");
    await page.getByRole("button", { name: "Sign in", exact: true }).click();
    await expect(page.locator(".identity")).toBeVisible();
    const credential = (await page.context().cookies()).find(c => c.name === "axyrel_session")!;
    await request.post("http://127.0.0.1:8109/test/failure", { data: { path: "/api/v1/auth/me", status } });
    try {
      const response = await page.request.get("/api/backend/auth/me");
      expect(response.status()).toBe(typeof status === "number" ? status : 502);
      const after = (await page.context().cookies()).find(c => c.name === "axyrel_session");
      if (status === 401) expect(after).toBeUndefined();
      else expect(after?.value === credential.value).toBe(true);
    } finally { await request.post("http://127.0.0.1:8109/test/failure", { data: {} }); }
  });
}

test("failed Logout keeps credential for recoverable retry", async ({ page, request }) => {
  await page.goto("/login");
  await page.getByLabel("Email", { exact: true }).fill("admin@example.test");
  await page.getByLabel("Password", { exact: true }).fill("synthetic-password");
  await page.getByRole("button", { name: "Sign in", exact: true }).click();
  await expect(page.locator(".identity")).toBeVisible();
  const before = (await page.context().cookies()).find(c => c.name === "axyrel_session")!;
  await request.post("http://127.0.0.1:8109/test/failure", { data: { path: "/api/v1/auth/sessions/logout", status: 503 } });
  try {
    await page.getByRole("button", { name: "Sign out", exact: true }).click();
    await expect(page.getByRole("alert")).toBeVisible();
    expect((await page.context().cookies()).find(c => c.name === "axyrel_session")?.value === before.value).toBe(true);
  } finally { await request.post("http://127.0.0.1:8109/test/failure", { data: {} }); }
  await page.getByRole("button", { name: "Sign out", exact: true }).click(); await expect(page).toHaveURL(/login/);
});
