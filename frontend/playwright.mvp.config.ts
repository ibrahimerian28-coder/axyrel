import { defineConfig } from "@playwright/test";
const apiPort=Number(process.env.AXYREL_PHASE3_TEST_PORT||8130);
const uiPort=Number(process.env.AXYREL_TEST_FRONTEND_PORT||3130);
const backend=`http://127.0.0.1:${apiPort}`;const origin=`http://127.0.0.1:${uiPort}`;
export default defineConfig({testDir:"./tests/mvp",outputDir:`./test-results/mvp-${uiPort}`,workers:1,timeout:90000,expect:{timeout:15000},reporter:"list",use:{baseURL:origin,trace:"retain-on-failure"},webServer:[{command:"..\\.venv\\Scripts\\python.exe -B tests/phase3-api.py",url:`${backend}/health`,env:{AXYREL_PHASE3_TEST_PORT:String(apiPort)},timeout:90000,reuseExistingServer:false},{command:`npm.cmd run start -- --port ${uiPort}`,url:`${origin}/login`,env:{AXYREL_BACKEND_URL:backend,AXYREL_FRONTEND_ORIGIN:origin},reuseExistingServer:false}],projects:[{name:"chromium",use:{browserName:"chromium",timezoneId:"Africa/Cairo"}}]});
