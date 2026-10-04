import { siWhatsapp } from "simple-icons";
import { expect, test } from "@playwright/test";
async function login(page: import("@playwright/test").Page, role = "admin") { await page.goto("/login"); await page.getByLabel("Email", { exact: true }).fill(`${role}@example.test`); await page.getByLabel("Password", { exact: true }).fill("synthetic-password"); await page.getByRole("button", { name: "Sign in", exact: true }).click(); await expect(page.getByRole("heading", { name: "Workspace", exact: true })).toBeVisible(); }
async function module(page: import("@playwright/test").Page, name: string) { await page.locator("nav").getByRole("button", { name, exact: true }).click(); }
test("desktop dashboard and all three screens at phone width", async ({ page }) => {
  await page.setViewportSize({ width: 1536, height: 1024 }); await login(page); await module(page, "Dashboard"); await expect(page.getByRole("heading", { name: "Welcome back, Synthetic Admin" })).toBeVisible(); await page.screenshot({ path: test.info().outputPath("dashboard-desktop.png"), fullPage: true });
  await expect(page.getByRole("region", { name: "Current service activity chart" })).toBeVisible();
  await expect(page.getByRole("table", { name: "Current service record counts by status" })).toContainText("Open");
  await expect(page.locator("body")).not.toContainText("Frontend v1");
  await expect(page).toHaveTitle("Axyrel");
  await expect(page.getByRole("region", { name: "Asset types chart" })).toBeVisible();
  await expect(page.getByRole("table", { name: "Asset counts by device type" })).toContainText("HVAC");
  await page.setViewportSize({ width: 390, height: 844 });
  for (const name of ["Dashboard", "Customers", "Assets"]) { await page.getByRole("button", { name: "Toggle navigation" }).click(); await module(page, name); await expect(page.getByRole("heading", { name: name === "Dashboard" ? "Welcome back, Synthetic Admin" : name, exact: true })).toBeVisible(); expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true); await page.screenshot({ path: test.info().outputPath(`${name.toLowerCase()}-phone.png`), fullPage: true }); }
  await page.getByRole("button", { name: "#2001 · SYN-001", exact: true }).click(); await expect(page.getByRole("heading", { name: "Synthetic Model" })).toBeVisible(); await page.getByRole("button", { name: "View Customer", exact: true }).click(); await expect(page.getByRole("heading", { name: "Synthetic Customer", exact: true })).toBeVisible(); await page.screenshot({ path: test.info().outputPath("customers-mobile.png"), fullPage: true });
});
test("real API dashboard, customer/asset contexts and explicit phone actions", async ({ page, context }) => {
  await login(page); await module(page, "Dashboard"); await expect(page.getByRole("heading", { name: "Welcome back, Synthetic Admin" })).toBeVisible(); await expect(page.getByRole("heading", { name: "Work Orders", exact: true })).toBeVisible();
  await module(page, "Customers"); await page.getByRole("button", { name: "#1001 · Synthetic Customer", exact: true }).click(); await expect(page.getByRole("heading", { name: "Synthetic Customer", exact: true })).toBeVisible();
  await expect(page.getByRole("link", { name: "Call", exact: true })).toHaveAttribute("href", "tel:+201000000001");
  await expect(page.locator("svg[data-brand=whatsapp] path")).toHaveAttribute("d", siWhatsapp.path); await expect(page.getByRole("link", { name: "WhatsApp", exact: true })).toHaveAttribute("href", "https://wa.me/201000000001");
  for (const action of [page.getByRole("link", { name: "Call", exact: true }), page.getByRole("link", { name: "WhatsApp", exact: true }), page.getByRole("button", { name: "Copy Number", exact: true })]) {
    await expect(action).toHaveAttribute("title", /.+/); await action.focus(); await expect(action).toBeFocused();
    expect(await action.evaluate(el => el.getBoundingClientRect().width)).toBe(44);
  }
  await context.grantPermissions(["clipboard-read", "clipboard-write"]); await page.getByRole("button", { name: "Copy Number" }).focus(); await page.keyboard.press("Enter"); expect(await page.evaluate(() => navigator.clipboard.readText())).toBe("+201000000001");
  await page.getByRole("tab", { name: "Assets", exact: true }).click(); await page.getByRole("button", { name: /#2001.*SYN-001/ }).click(); await expect(page.getByRole("heading", { name: "Synthetic Model" })).toBeVisible();
  await page.getByRole("tab", { name: "Service History" }).click(); await expect(page.getByText("Synthetic completed inspection", { exact: true })).toBeVisible(); await page.getByRole("button", { name: "Customer: #1001 · Synthetic Customer", exact: true }).click(); await expect(page.getByRole("heading", { name: "Synthetic Customer", exact: true })).toBeVisible();
  const content = await page.locator("#workspace").innerText(); expect(content).not.toMatch(/[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}/i);
  await page.screenshot({ path: test.info().outputPath("customers-desktop.png"), fullPage: true });
});
test("customer create/edit, linked asset create/edit, filters and unsupported phone country", async ({ page }) => {
  await login(page); await module(page, "Customers"); await page.getByRole("button", { name: "+ Add Customer", exact: true }).click(); const form = page.getByRole("region", { name: "Create customer" }); await form.getByLabel("Name", { exact: true }).fill("Synthetic New Customer"); await form.getByLabel("Phone", { exact: true }).fill("01000000002"); await form.getByRole("button", { name: "Save", exact: true }).click(); await expect(page.getByRole("heading", { name: "Synthetic New Customer", exact: true })).toBeVisible(); await expect(page.getByRole("link", { name: "WhatsApp", exact: true })).toHaveCount(0); await expect(page.getByRole("button", { name: "WhatsApp", exact: true })).toHaveAttribute("aria-disabled", "true");
  await page.getByRole("button", { name: "Edit Customer", exact: true }).click(); const edit = page.getByRole("region", { name: "Edit customer" }); await edit.getByLabel("Name", { exact: true }).fill("Synthetic Updated Customer"); await edit.getByRole("button", { name: "Save", exact: true }).click(); await expect(page.getByRole("heading", { name: "Synthetic Updated Customer", exact: true })).toBeVisible();
  await page.getByRole("button", { name: "Add Asset for Customer" }).click(); const asset = page.getByRole("region", { name: "Create asset" }); await expect(asset.getByRole("combobox", { name: "Customer", exact: true })).toHaveValue(/.+/); await asset.getByLabel("Asset type", { exact: true }).fill("Generator"); await asset.getByLabel("Model", { exact: true }).fill("Synthetic Generator"); await asset.getByLabel("Serial number", { exact: true }).fill("SYN-NEW"); await asset.getByRole("button", { name: "Save", exact: true }).click(); await expect(page.getByRole("heading", { name: "Synthetic Generator", exact: true })).toBeVisible();
  await page.getByRole("button", { name: "Edit Asset", exact: true }).click(); const editAsset = page.getByRole("region", { name: "Edit asset" }); await editAsset.getByLabel("Model", { exact: true }).fill("Synthetic Revised Generator"); await editAsset.getByLabel("Installation date", { exact: true }).fill("2026-01-15"); await editAsset.getByRole("button", { name: "Save", exact: true }).click(); await expect(page.getByRole("heading", { name: "Synthetic Revised Generator", exact: true })).toBeVisible(); await expect(page.getByText("2026-01-15", { exact: true }).last()).toBeVisible();
  await page.getByLabel("Search assets", { exact: true }).fill("does-not-exist"); await expect(page.getByRole("heading", { name: "No records found" })).toBeVisible(); await page.getByRole("button", { name: "Clear", exact: true }).click(); await expect(page.locator("tbody").getByText("SYN-NEW", { exact: false })).toBeVisible();
  await page.screenshot({ path: test.info().outputPath("assets-desktop.png"), fullPage: true });
});
test("mobile, RTL, read-only role and backend load errors", async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 }); await login(page, "technician"); await page.getByRole("button", { name: "Toggle navigation" }).click(); await module(page, "Assets"); await expect(page.getByRole("button", { name: "+ Add Asset", exact: true })).toHaveCount(0); await page.getByRole("button", { name: "#2001 · SYN-001", exact: true }).click(); await expect(page.getByRole("heading", { name: "Synthetic Model" })).toBeVisible(); await page.evaluate(() => { document.documentElement.dir = "rtl"; }); expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true); await page.screenshot({ path: test.info().outputPath("assets-mobile-rtl.png"), fullPage: true });
  await page.route("**/api/backend/assets", route => route.fulfill({ status: 503, contentType: "application/json", body: '{"detail":"synthetic failure"}' })); await page.reload(); await expect(page.getByRole("heading", { name: "Unable to load", exact: true })).toBeVisible();
});

test("chart empty state and clipboard failure preserve contact safeguards", async ({ page }) => {
  await page.route("**/api/backend/work-orders", route => route.fulfill({ json: [] }));
  await page.route("**/api/backend/service-visits", route => route.fulfill({ json: [] }));
  await login(page); await module(page, "Dashboard");
  await expect(page.getByRole("heading", { name: "No service activity yet" })).toBeVisible();
  await module(page, "Assets"); await page.getByRole("button", { name: "#2001 \u00b7 SYN-001", exact: true }).click();
  await expect(page.getByRole("link", { name: "WhatsApp", exact: true })).toHaveAttribute("rel", "noopener noreferrer");
  await expect(page.getByRole("link", { name: "Call", exact: true })).toHaveAttribute("href", "tel:+201000000001");
  await expect(page.locator("svg[data-brand=whatsapp] path")).toHaveAttribute("d", siWhatsapp.path);
  await page.evaluate(() => { Object.defineProperty(navigator.clipboard, "writeText", { value: () => Promise.reject(new Error("Unavailable")) }); });
  await page.getByRole("button", { name: "Copy Number" }).click();
  await expect(page.locator(".phone-actions [role=status]")).toHaveText("Copy unavailable. Select the displayed number to copy it.");
});
