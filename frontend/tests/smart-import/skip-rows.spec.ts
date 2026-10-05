import { expect,test } from "@playwright/test";
import { execFileSync } from "node:child_process";

test("explicit source-row skip and restore: Owner workbook on desktop, 390px and RTL",async({page})=>{
  await page.setViewportSize({width:1440,height:900});
  await page.goto('/login');await page.getByLabel('Email',{exact:true}).fill('admin@example.test');await page.getByLabel('Password',{exact:true}).fill('synthetic-password');await page.getByRole('button',{name:'Sign in',exact:true}).click();await expect(page).toHaveURL(/module=Dashboard/);
  // These API calls address only the generated phase3-api disposable database.
  let customers=await(await page.request.get('/api/backend/customers')).json();
  while(!customers.some((c:{display_id:number})=>c.display_id===1010)){
    const number=Math.max(...customers.map((c:{display_id:number})=>c.display_id))+1;
    expect(number).toBeLessThanOrEqual(1010);
    const response=await page.request.post('/api/backend/customers',{headers:{Origin:new URL(page.url()).origin},data:{name:number===1010?'Owner Scenario Customer':`Disposable filler ${number}`,phones:[{country:'EG',number:number===1010?'01000000031':`0100000${number}`,label:'Primary'}]}});
    expect(response.status(),await response.text()).toBe(201);customers=await(await page.request.get('/api/backend/customers')).json();
  }
  const existing=customers.find((c:{display_id:number})=>c.display_id===1010);
  expect(existing.name).toBe('Owner Scenario Customer');
  const seeded=await page.request.post('/api/backend/assets',{headers:{Origin:new URL(page.url()).origin},data:{customer_id:existing.id,asset_type:'Filter',serial_number:'SMART-TEST-001',country:'EG',state:'EG-C',status:'Active'}});expect(seeded.status(),await seeded.text()).toBe(201);const originalAsset=await seeded.json();
  await page.locator('nav').getByRole('button',{name:'Assets',exact:true}).click();await page.getByRole('button',{name:'Import Data',exact:true}).click();const wizard=page.getByRole('region',{name:'Smart Import'});
  const encoded=execFileSync('../.venv/Scripts/python.exe',['-B','-c',"import io,base64; from openpyxl import Workbook; w=Workbook(); w.active.append(['Customer Name','Phone','Asset Type','Serial Number','Country','State']); w.active.append(['Owner Scenario Customer','01000000031','Filter','SMART-TEST-001','Egypt','Cairo']); w.active.append(['New Import Customer','01099998888','Filter','SMART-TEST-002','Egypt','Cairo']); b=io.BytesIO(); w.save(b); print(base64.b64encode(b.getvalue()).decode())"],{windowsHide:true}).toString().trim();
  await wizard.getByLabel('Spreadsheet file',{exact:true}).setInputFiles({name:'owner-scenario.xlsx',mimeType:'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',buffer:Buffer.from(encoded,'base64')});await wizard.getByRole('button',{name:'Review import',exact:true}).click();
  await expect(wizard.getByRole('region',{name:'Row 2 errors'})).toContainText('Serial belongs to an existing or deleted asset');await expect(wizard.getByRole('article',{name:'Source row 2'})).toContainText('Customer No. #1010');await expect(wizard.getByRole('heading',{name:'Ready (1)',exact:true})).toBeVisible();
  const skip=wizard.getByRole('button',{name:'Skip this row 2',exact:true});await skip.focus();await page.keyboard.press('Enter');await expect(wizard.getByRole('heading',{name:'Skipped (1)',exact:true})).toBeVisible();
  await expect(wizard.getByText('1 rows skipped',{exact:true})).toBeVisible();await expect(wizard.getByText('0 rows need attention',{exact:true})).toBeVisible();await expect(wizard.getByText('0 existing Customers matched',{exact:true})).toBeVisible();await expect(wizard.getByText('1 new Assets',{exact:true})).toBeVisible();
  const restore=wizard.getByRole('button',{name:'Restore row 2',exact:true});await restore.focus();await page.keyboard.press('Enter');await expect(wizard.getByRole('region',{name:'Row 2 errors'})).toBeVisible();await expect(wizard.getByRole('button',{name:'Continue to Import',exact:true})).toBeDisabled();
  await wizard.getByRole('button',{name:'Skip this row 2',exact:true}).click();await expect(wizard.getByRole('button',{name:'Continue to Import',exact:true})).toBeEnabled();
  // Ready rows can be skipped, and an all-skipped batch cannot be confirmed.
  await wizard.getByRole('button',{name:'Skip this row 3',exact:true}).click();await expect(wizard.getByRole('status')).toHaveText('No rows selected for import.');await expect(wizard.getByText('2 rows skipped',{exact:true})).toBeVisible();await expect(wizard.getByRole('button',{name:'Continue to Import',exact:true})).toBeDisabled();
  await wizard.getByRole('button',{name:'Restore row 3',exact:true}).click();await expect(wizard.getByRole('button',{name:'Continue to Import',exact:true})).toBeEnabled();
  for(const [width,dir,label] of [[1440,'ltr','desktop'],[390,'ltr','390'],[390,'rtl','390-rtl']] as const){
    await page.setViewportSize({width,height:900});await page.evaluate(value=>{document.documentElement.dir=value;},dir);
    expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBe(true);
    expect(await page.locator('main').innerText()).not.toMatch(/[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}/i);
    await expect(wizard.getByRole('button',{name:'Restore row 2',exact:true})).toBeVisible();await page.evaluate(()=>window.scrollTo(0,0));await page.screenshot({path:test.info().outputPath(`skip-review-${label}.png`),fullPage:true});
  }
  await wizard.getByRole('button',{name:'Continue to Import',exact:true}).click();await expect(wizard.getByText('1 rows skipped',{exact:true})).toBeVisible();await expect(wizard.getByText('1 new Customers',{exact:true})).toBeVisible();await expect(wizard.getByText('1 new Assets',{exact:true})).toBeVisible();await expect(wizard.getByText('Skipped rows create nothing. Existing customers and assets will remain unchanged.',{exact:true})).toBeVisible();
  await wizard.getByRole('checkbox').check();await wizard.getByRole('button',{name:'Confirm import',exact:true}).click();await expect(wizard.getByRole('status')).toContainText('Import completed');await expect(wizard.getByRole('status')).toContainText('1 rows skipped');
  customers=await(await page.request.get('/api/backend/customers')).json();const assets=await(await page.request.get('/api/backend/assets')).json();
  expect(customers.find((c:{id:string})=>c.id===existing.id)).toEqual(existing);expect(assets.find((a:{id:string})=>a.id===originalAsset.id)).toEqual(originalAsset);
  const created=customers.filter((c:{name:string})=>c.name==='New Import Customer');expect(created).toHaveLength(1);const imported=assets.filter((a:{serial_number:string})=>a.serial_number==='SMART-TEST-002');expect(imported).toHaveLength(1);expect(imported[0].customer_id).toBe(created[0].id);
  expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBe(true);await page.evaluate(()=>window.scrollTo(0,0));await page.screenshot({path:test.info().outputPath('skip-receipt-390-rtl.png'),fullPage:true});
});
