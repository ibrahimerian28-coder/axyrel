import { expect, test } from "@playwright/test";
import { readFileSync } from "node:fs";
test("identified persistent local owner review login and MVP navigation",async({page})=>{
 const password=readFileSync("../.owner-review/credentials.txt","utf-8").split("Password: ")[1].trim();
 await page.goto("/login");await page.getByLabel("Email",{exact:true}).fill("owner@axyrel.local");await page.getByLabel("Password",{exact:true}).fill(password);await page.getByRole("button",{name:"Sign in",exact:true}).click();await expect(page).toHaveURL(/module=Dashboard/); await expect(page.locator(".identity")).toBeVisible();
 for(const name of ["Dashboard","Customers","Assets","Requests","Work Orders","Schedule","Service Visits","Service History","Inventory","Invoices","Expenses","Reports"]){await page.locator("nav").getByRole("button",{name,exact:true}).click();await expect(page.locator("main h1")).toBeVisible();await expect(page.getByRole("heading",{name:"Unable to load",exact:true})).toHaveCount(0);}
 await page.setViewportSize({width:390,height:844});await expect(page.getByRole("heading",{name:"Reports",exact:true})).toBeVisible();expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBe(true);await page.screenshot({path:test.info().outputPath("persistent-owner-report-mobile.png"),fullPage:true});
 await page.getByRole("button",{name:"Sign out",exact:true}).click();await expect(page).toHaveURL(/\/login$/);
});
