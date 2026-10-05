import { defineConfig } from "@playwright/test";
import config from "./playwright.mvp.config";
export default defineConfig({...config,testDir:"./tests/smart-import",outputDir:"./test-results/smart-import"});
