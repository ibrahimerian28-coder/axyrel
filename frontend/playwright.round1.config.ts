import { defineConfig } from "@playwright/test";
import config from "./playwright.mvp.config";
export default defineConfig({...config,testDir:"./tests/round1",outputDir:`./test-results/round1-${process.env.AXYREL_TEST_FRONTEND_PORT||3130}`});
