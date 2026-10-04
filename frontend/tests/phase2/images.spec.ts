import { expect, test } from "@playwright/test";
import { readFileSync } from "node:fs";
import { siWhatsapp } from "simple-icons";

const png = readFileSync("tests/fixtures/profile.png");
const jpeg = readFileSync("tests/fixtures/profile.jpg");
async function login(page: import("@playwright/test").Page, role = "admin") {
  await page.goto("/login"); await page.getByLabel("Email", { exact: true }).fill(`${role}@example.test`);
  await page.getByLabel("Password", { exact: true }).fill("synthetic-password");
  await page.getByRole("button", { name: "Sign in", exact: true }).click();
  await expect(page.getByRole("heading", { name: "Workspace", exact: true })).toBeVisible();
}
async function select(page: import("@playwright/test").Page, kind: string) {
  if (await page.locator("nav").isHidden()) await page.getByRole("button", { name: "Toggle navigation" }).click();
  await page.locator("nav").getByRole("button", { name: kind, exact: true }).click();
  await page.locator("tbody").getByRole("button", { name: kind === "Customers" ? /^#1001.*Synthetic Customer/ : /^#2001.*SYN-001/ }).click();
}

test("customer and asset images preview, upload, reload, replace, remove at desktop and 390px", async ({ page }) => {
  await page.setViewportSize({ width: 1536, height: 1024 }); await login(page);
  for (const kind of ["Customers", "Assets"]) {
    await page.setViewportSize({ width: 1536, height: 1024 }); await select(page, kind);
    const title = kind === "Customers" ? "Customer" : "Asset";
    const section = page.getByRole("region", { name: `${title} profile image` });
    await expect(section.getByRole("img", { name: `${title} image fallback` })).toBeVisible();
    if (kind === "Customers") await expect(section.getByRole("img")).toHaveText("SC");
    await section.getByLabel(`${title} image file`).setInputFiles({ name: "synthetic.png", mimeType: "image/png", buffer: png });
    await expect(section.getByRole("img", { name: /image preview/ })).toBeVisible();
    await section.getByRole("button", { name: "Cancel preview" }).click();
    await expect(section.getByRole("img", { name: `${title} image fallback` })).toBeVisible();
    await section.getByLabel(`${title} image file`).setInputFiles({ name: "synthetic.png", mimeType: "image/png", buffer: png });
    await section.getByRole("button", { name: "Save image" }).click();
    await expect(section.getByRole("status")).toHaveText("Image saved.");
    const displayed = section.getByRole("img", { name: /profile image/ });
    await expect(displayed).toBeVisible();
    await expect.poll(() => displayed.evaluate(el => (el as HTMLImageElement).naturalWidth)).toBe(64);
    await page.reload(); await expect(displayed).toBeVisible();
    await expect.poll(() => displayed.evaluate(el => (el as HTMLImageElement).naturalWidth)).toBe(64);
    await page.screenshot({ path: test.info().outputPath(`${kind.toLowerCase()}-image-desktop.png`), fullPage: true });
    await page.setViewportSize({ width: 390, height: 844 });
    await section.getByLabel(`${title} image file`).setInputFiles({ name: "replacement.jpg", mimeType: "image/jpeg", buffer: jpeg });
    await section.getByRole("button", { name: "Save image" }).click();
    await expect(section.getByRole("status")).toHaveText("Image saved.");
    await expect.poll(() => displayed.evaluate(el => (el as HTMLImageElement).naturalWidth)).toBe(80);
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
    await expect(page.locator("svg[data-brand=whatsapp] path")).toHaveAttribute("d", siWhatsapp.path);
    await expect(page.getByRole("link", { name: "WhatsApp", exact: true })).toHaveAttribute("title", "WhatsApp");
    await page.screenshot({ path: test.info().outputPath(`${kind.toLowerCase()}-image-mobile.png`), fullPage: true });
    await section.getByRole("button", { name: "Remove image" }).click();
    await expect(section.getByRole("status")).toHaveText("Image removed.");
    await expect(section.getByRole("img", { name: `${title} image fallback` })).toBeVisible();
  }
});

test("image validation errors and same-origin private proxy protections", async ({ page }) => {
  await login(page); await select(page, "Customers");
  const section = page.getByRole("region", { name: "Customer profile image" });
  await section.getByLabel("Customer image file").setInputFiles({ name: "false.png", mimeType: "image/png", buffer: Buffer.from("not a PNG") });
  await section.getByRole("button", { name: "Save image" }).click();
  await expect(section.getByRole("alert")).toContainText("Invalid image");
  await section.getByRole("button", { name: "Cancel preview" }).click();
  await section.getByLabel("Customer image file").setInputFiles({ name: "oversized.png", mimeType: "image/png", buffer: Buffer.alloc(5 * 1024 * 1024 + 1) });
  await expect(section.getByRole("alert")).toContainText("5 MB");
  const id = new URL(page.url()).searchParams.get("record"); const path = `/api/backend/customers/${id}/image`;
  const oversized = await page.request.put(path, { headers: { Origin: "http://127.0.0.1:3120", "Content-Type": "image/png" }, data: Buffer.alloc(5 * 1024 * 1024 + 1) });
  expect(oversized.status()).toBe(413);
  const forged = await page.request.put(path, { headers: { Origin: "https://foreign.example", "Content-Type": "image/png" }, data: png });
  expect(forged.status()).toBe(403);
  const svg = await page.request.put(path, { headers: { Origin: "http://127.0.0.1:3120", "Content-Type": "image/svg+xml" }, data: "<svg/>" });
  expect(svg.status()).toBe(415);
  await page.getByRole("button", { name: "Sign out" }).click();
  await expect(page).toHaveURL(/\/login$/);
  expect((await page.request.get(path)).status()).toBe(401);
  await login(page, "technician"); await select(page, "Customers");
  await expect(section.getByLabel("Customer image file")).toHaveCount(0);
  const denied = await page.request.put(path, { headers: { Origin: "http://127.0.0.1:3120", "Content-Type": "image/png" }, data: png });
  expect(denied.status()).toBe(403);
});
