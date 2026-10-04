import { defineConfig } from "@playwright/test";
export default defineConfig({ testDir:"./tests/owner-review",outputDir:"../.owner-review/browser-validation",workers:1,timeout:60000,expect:{timeout:15000},reporter:"list",use:{baseURL:"http://127.0.0.1:3140",trace:"off"},projects:[{name:"chromium",use:{browserName:"chromium"}}] });
