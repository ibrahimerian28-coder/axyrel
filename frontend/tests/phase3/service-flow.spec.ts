import { expect, test, type Page } from "@playwright/test";

async function login(page: Page, role = "admin") { await page.goto("/login"); await page.getByLabel("Email", { exact: true }).fill(`${role}@example.test`); await page.getByLabel("Password", { exact: true }).fill("synthetic-password"); await page.getByRole("button", { name: "Sign in", exact: true }).click(); await expect(page).toHaveURL(/module=Dashboard/); await expect(page.locator(".identity")).toBeVisible(); }
async function module(page: Page, name: string) { if (await page.locator("nav").isHidden()) await page.getByRole("button", { name: "Toggle navigation" }).click(); await page.locator("nav").getByRole("button", { name, exact: true }).click(); }
function editor(page: Page, label: string) { return page.getByRole("region", { name: label, exact: true }); }
const detail = (page: Page) => page.getByRole("region", { name: "Service record details", exact: true });
const origin = { Origin: `http://127.0.0.1:${process.env.AXYREL_TEST_FRONTEND_PORT||3130}` };
const recordId = (page: Page) => new URL(page.url()).searchParams.get("record")!;
async function records(page: Page, resource: string) { const response = await page.request.get(`/api/backend/${resource}`); expect(response.ok()).toBe(true); return response.json(); }

test("real PostgreSQL Request → Order → Schedule → Visit → explicit History flow and stock reversal", async ({ page }) => {
  await page.setViewportSize({ width: 1536, height: 1024 }); await login(page); await module(page, "Requests");
  await page.getByRole("button", { name: "+ Add Request", exact: true }).click(); const request = editor(page, "Create Request");
  await request.getByLabel("Customer", { exact: true }).selectOption({ label: "#1001 · Synthetic Customer" });
  await request.getByLabel("Asset (optional)", { exact: true }).selectOption({ label: "#2001 · SYN-001" });
  await request.getByLabel("Title", { exact: true }).fill("Browser service flow"); await request.getByRole("button", { name: "Save", exact: true }).click();
  await expect(detail(page).getByRole("heading", { name: /Browser service flow/ })).toBeVisible(); const requestId = recordId(page);
  await detail(page).getByRole("button", { name: "Edit Request", exact: true }).click(); await editor(page, "Edit Request").getByLabel("Notes", { exact: true }).fill("Customer called"); await editor(page, "Edit Request").getByRole("button", { name: "Save", exact: true }).click(); await expect(detail(page)).toContainText("Customer called");
  await detail(page).getByRole("button", { name: "Create Work Order", exact: true }).click(); const order = editor(page, "Create Work Order");
  await expect(order.getByLabel("Service Request (optional)", { exact: true })).toHaveValue(requestId);
  await order.getByLabel("Technician (optional)", { exact: true }).selectOption({ label: "Synthetic Technician" });
  await order.getByRole("button", { name: "Save", exact: true }).click(); await expect(detail(page).getByRole("heading", { name: /Browser service flow/ })).toBeVisible(); const orderId = recordId(page);
  await detail(page).getByRole("button", { name: "Add Schedule", exact: true }).click(); const schedule = editor(page, "Create Schedule");
  await expect(schedule.getByLabel("Work Order", { exact: true })).toHaveValue(orderId);
  await schedule.getByLabel("Start (Cairo)", { exact: true }).fill("2026-10-05T10:00"); await schedule.getByLabel("End (Cairo)", { exact: true }).fill("2026-10-05T11:00");
  await schedule.getByLabel("Start UTC offset (optional)", { exact: true }).fill("+03:00"); await schedule.getByLabel("End UTC offset (optional)", { exact: true }).fill("+03:00");
  await schedule.getByRole("button", { name: "Save", exact: true }).click(); await expect(detail(page).getByRole("heading", { name: /Schedule.*Browser service flow/ })).toBeVisible(); const scheduleId = recordId(page);
  await page.getByLabel("Week starting", { exact: true }).fill("2026-10-05"); await expect(page.locator(".week-view > section")).toHaveCount(7);
  await expect(page.getByRole("region", { name: "Schedule for 2026-10-05" })).toContainText("Browser service flow");
  await page.screenshot({ path: test.info().outputPath("schedule-desktop.png"), fullPage: true });
  await detail(page).getByRole("button", { name: "Add Service Visit", exact: true }).click(); const visit = editor(page, "Create Service Visit");
  await expect(visit.getByLabel("Schedule (optional)", { exact: true })).toHaveValue(scheduleId);
  await visit.getByLabel("Status", { exact: true }).selectOption("In Progress"); await visit.getByLabel("Actual start (Cairo)", { exact: true }).fill("2026-10-05T10:05");
  await visit.getByLabel("Actual start UTC offset (optional)", { exact: true }).fill("+03:00"); await visit.getByRole("button", { name: "Save", exact: true }).click();
  await expect(detail(page).getByRole("heading", { name: /Visit.*Browser service flow/ })).toBeVisible(); const visitId = recordId(page);
  expect((await records(page, "work-orders")).find((r: { id: string }) => r.id === orderId).status).toBe("In Progress");
  const inventory = page.getByRole("region", { name: "Visit inventory", exact: true }); await inventory.getByLabel("Inventory item", { exact: true }).selectOption({ label: "Synthetic Filter · Technician stock 8" }); await inventory.getByLabel("Quantity", { exact: true }).fill("2"); await inventory.getByRole("button", { name: "Install part", exact: true }).click();
  await expect(detail(page).getByRole("status")).toHaveText("Part installation recorded."); await expect(inventory).toContainText("Installed · Synthetic Filter · Quantity 2");
  await detail(page).getByRole("button", { name: "Edit Service Visit", exact: true }).click(); const complete = editor(page, "Edit Service Visit");
  await complete.getByLabel("Status", { exact: true }).selectOption("Completed"); await complete.getByLabel("Actual end (Cairo)", { exact: true }).fill("2026-10-05T11:00"); await complete.getByLabel("Actual end UTC offset (optional)", { exact: true }).fill("+03:00"); await complete.getByRole("button", { name: "Save", exact: true }).click();
  await expect(detail(page).locator(".profile-header .badge")).toHaveText("Completed"); await page.reload(); await expect(detail(page).locator(".profile-header .badge")).toHaveText("Completed");
  expect((await records(page, "work-orders")).find((r: { id: string }) => r.id === orderId).status).toBe("Completed");
  // Explicit accepted API record, never inferred from visit completion.
  const storedVisit = (await records(page, "service-visits")).find((r: { id: string }) => r.id === visitId);
  const response = await page.request.post("/api/backend/service-history", { headers: origin, data: { customer_id: storedVisit.customer_id, asset_id: storedVisit.asset_id, work_order_id: orderId, service_visit_id: visitId, technician_id: storedVisit.technician_id, service_type: "Inspection", service_date: "2026-10-05T11:00:00", summary: "Explicit browser inspection record" } }); expect(response.status()).toBe(201);
  await page.getByRole("button", { name: "Refresh records", exact: true }).click(); await detail(page).getByRole("button", { name: /Explicit browser inspection record/ }).click();
  await expect(detail(page).getByRole("heading", { name: "Explicit browser inspection record", exact: true })).toBeVisible();
  await detail(page).getByRole("button", { name: /Visit.*Browser service flow/ }).click(); await detail(page).getByRole("button", { name: "Edit Service Visit", exact: true }).click();
  await expect(editor(page, "Edit Service Visit").getByLabel("Status", { exact: true }).locator("option")).toHaveText(["Completed", "Cancelled"]);
  await editor(page, "Edit Service Visit").getByLabel("Status", { exact: true }).selectOption("Cancelled"); await editor(page, "Edit Service Visit").getByRole("button", { name: "Save", exact: true }).click(); await expect(inventory).toContainText("Reversal · Synthetic Filter · Quantity 2");
  expect((await records(page, "technician-stock"))[0].quantity).toBe(8);
  expect((await records(page, "inventory"))[0].quantity).toBe(20);
  expect(await page.locator("#workspace").innerText()).not.toMatch(/[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}/i);
  await detail(page).getByRole("button", { name: "Delete Service Visit", exact: true }).click(); await page.getByRole("button", { name: "Confirm delete", exact: true }).click(); await expect(detail(page).getByRole("heading", { name: "Select a record", exact: true })).toBeVisible(); expect((await page.request.get(`/api/backend/service-visits/${visitId}`)).status()).toBe(404); expect((await records(page, "technician-stock"))[0].quantity).toBe(8);
});

test("schedule range errors, edit persistence, seven-day navigation and 390px agenda", async ({ page }) => {
  await login(page); await module(page, "Schedule"); await page.getByRole("button", { name: "+ Add Schedule", exact: true }).click(); const form = editor(page, "Create Schedule");
  await form.getByLabel("Work Order", { exact: true }).selectOption({ label: "#1 · Synthetic Order" });
  await form.getByLabel("Start (Cairo)", { exact: true }).fill("2026-10-12T14:00"); await form.getByLabel("End (Cairo)", { exact: true }).fill("2026-10-12T13:00"); await form.getByRole("button", { name: "Save", exact: true }).click(); await expect(form.getByRole("alert")).toBeVisible();
  await form.getByLabel("End (Cairo)", { exact: true }).fill("2026-10-12T15:00"); await form.getByRole("button", { name: "Save", exact: true }).click(); await expect(detail(page).getByRole("heading", { name: /Schedule.*Synthetic Order/ })).toBeVisible();
  await detail(page).getByRole("button", { name: "Edit Schedule", exact: true }).click(); const edit = editor(page, "Edit Schedule"); await edit.getByLabel("Notes", { exact: true }).fill("Notes-only edit preserves instant"); await edit.getByRole("button", { name: "Save", exact: true }).click(); await expect(detail(page)).toContainText("Notes-only edit preserves instant");
  await page.getByLabel("Week starting", { exact: true }).fill("2026-10-12"); await page.getByRole("button", { name: "Next seven days", exact: true }).click(); await expect(page.getByLabel("Week starting", { exact: true })).toHaveValue("2026-10-19"); await page.getByRole("button", { name: "Previous seven days", exact: true }).click();
  await page.setViewportSize({ width: 390, height: 844 }); await expect(page.locator(".agenda-view")).toBeVisible(); await expect(page.locator(".week-view")).toBeHidden(); expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true); await page.screenshot({ path: test.info().outputPath("schedule-mobile.png"), fullPage: true });
  await page.evaluate(() => { document.documentElement.dir = "rtl"; }); expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
  await detail(page).getByRole("button", { name: "Delete Schedule", exact: true }).click(); await page.getByRole("button", { name: "Confirm delete", exact: true }).click(); await expect(detail(page).getByRole("heading", { name: "Select a record", exact: true })).toBeVisible();
});

test("authoritative stored flow links, mobile screens, tenant isolation and load failures", async ({ page }) => {
  await login(page, "technician"); await module(page, "Requests"); await page.getByRole("region", { name: "Requests records", exact: true }).getByRole("button", { name: "#1 · Synthetic Request", exact: true }).click();
  await detail(page).getByRole("button", { name: /#1.*Synthetic Order/ }).click(); await expect(detail(page)).toContainText("Synthetic Technician");
  await detail(page).getByRole("button", { name: /^Schedule.*Synthetic Order/ }).click(); await detail(page).getByRole("button", { name: /^Visit.*Synthetic Order/ }).click(); const visitId = recordId(page);
  await detail(page).getByRole("button", { name: /Explicit synthetic service history/ }).click(); await expect(detail(page)).toContainText("Inspection");
  await page.setViewportSize({ width: 390, height: 844 }); for (const name of ["Requests", "Work Orders", "Schedule", "Service Visits", "Service History"]) { await module(page, name); await expect(page.getByRole("heading", { name: name === "Requests" ? "Service Requests" : name, exact: true })).toBeVisible(); expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true); await page.screenshot({ path: test.info().outputPath(`${name.replaceAll(" ", "-")}-mobile.png`), fullPage: true }); }
  await page.getByRole("button", { name: "Sign out", exact: true }).click(); await expect(page).toHaveURL(/\/login$/); expect((await page.request.get(`/api/backend/service-visits/${visitId}`)).status()).toBe(401);
  await login(page, "foreign"); await module(page, "Service Visits"); await expect(page.getByRole("heading", { name: "No records found", exact: true })).toBeVisible(); expect((await page.request.get(`/api/backend/service-visits/${visitId}`)).status()).toBe(404); expect((await page.request.patch(`/api/backend/service-visits/${visitId}`, { headers: origin, data: { status: "Cancelled" } })).status()).toBe(404);
  await page.route("**/api/backend/service-visits", route => route.fulfill({ status: 503, json: { detail: "synthetic error" } })); await page.reload(); await expect(page.getByRole("heading", { name: "Unable to load", exact: true })).toBeVisible();
});

test("requests and work orders delete only after explicit confirmation; permission presentation", async ({ page }) => {
  await login(page); await module(page, "Requests"); await page.getByRole("button", { name: "+ Add Request", exact: true }).click(); const form = editor(page, "Create Request"); await form.getByLabel("Customer", { exact: true }).selectOption({ label: "#1001 · Synthetic Customer" }); await form.getByLabel("Title", { exact: true }).fill("Delete-only request"); await form.getByRole("button", { name: "Save", exact: true }).click(); await expect(detail(page)).toContainText("Delete-only request"); const id = recordId(page);
  await detail(page).getByRole("button", { name: "Delete Request", exact: true }).click(); await page.getByRole("button", { name: "Keep record", exact: true }).click(); expect((await page.request.get(`/api/backend/service-requests/${id}`)).status()).toBe(200); await detail(page).getByRole("button", { name: "Delete Request", exact: true }).click(); await page.getByRole("button", { name: "Confirm delete", exact: true }).click(); await expect(detail(page).getByRole("heading", { name: "Select a record", exact: true })).toBeVisible(); expect((await page.request.get(`/api/backend/service-requests/${id}`)).status()).toBe(404);
  await module(page, "Work Orders"); await page.getByRole("button", { name: "+ Add Work Order", exact: true }).click(); const order = editor(page, "Create Work Order"); await order.getByLabel("Customer", { exact: true }).selectOption({ label: "#1001 · Synthetic Customer" }); await order.getByLabel("Title", { exact: true }).fill("Delete-only order"); await order.getByRole("button", { name: "Save", exact: true }).click(); await expect(detail(page)).toContainText("Delete-only order"); await detail(page).getByRole("button", { name: "Delete Work Order", exact: true }).click(); await page.getByRole("button", { name: "Confirm delete", exact: true }).click(); await expect(detail(page)).toContainText("Select a record");
  // Presentation-only permission reduction; backend role permissions are not invented.
  await page.route("**/api/backend/auth/me", async route => { const response = await route.fetch(); const body = await response.json(); body.permissions = body.permissions.filter((p: string) => p !== "service:manage"); await route.fulfill({ json: body }); }); await page.reload(); await expect(page.getByRole("button", { name: "+ Add Work Order", exact: true })).toHaveCount(0);
});
