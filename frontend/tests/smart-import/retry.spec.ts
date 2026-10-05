import { expect,test } from "@playwright/test";
test("lost Smart Import response freezes review and retries the durable receipt",async({page})=>{
  await page.goto('/login');await page.getByLabel('Email',{exact:true}).fill('admin@example.test');await page.getByLabel('Password',{exact:true}).fill('synthetic-password');await page.getByRole('button',{name:'Sign in',exact:true}).click();await expect(page).toHaveURL(/module=Dashboard/);
  await page.locator('nav').getByRole('button',{name:'Assets',exact:true}).click();await page.getByRole('button',{name:'Import Data',exact:true}).click();const wizard=page.getByRole('region',{name:'Smart Import'});
  await wizard.getByLabel('Import type',{exact:true}).selectOption('assets');await wizard.getByLabel('Spreadsheet file',{exact:true}).setInputFiles({name:'retry.csv',mimeType:'text/csv',buffer:Buffer.from('Customer Name,Phone,Asset Type\nSynthetic Customer,01000000001,Smart Retry No Serial\n')});
  await wizard.getByRole('button',{name:'Review import',exact:true}).click();await wizard.getByRole('button',{name:'Continue to Import',exact:true}).click();await wizard.getByRole('checkbox').check();
  const before=await(await page.request.get('/api/backend/assets')).json();let first=true;const keys:string[]=[];
  await page.route('**/api/backend/imports/commit',async route=>{keys.push(route.request().postDataJSON().idempotency_key);if(first){first=false;const response=await route.fetch();expect(response.ok()).toBe(true);await route.abort('failed');}else await route.continue();});
  await wizard.getByRole('button',{name:'Confirm import',exact:true}).click();await expect(wizard.getByRole('button',{name:'Retry same import safely',exact:true})).toBeVisible();await expect(wizard.getByRole('button',{name:'Back to review',exact:true})).toBeDisabled();await expect(wizard.getByRole('checkbox')).toBeDisabled();
  await wizard.getByRole('button',{name:'Retry same import safely',exact:true}).click();await expect(wizard.getByRole('status')).toContainText('Existing receipt retrieved; no duplicate records created.');expect(keys).toHaveLength(2);expect(keys[0]).toBe(keys[1]);
  const after=await(await page.request.get('/api/backend/assets')).json();expect(after).toHaveLength(before.length+1);
});
