const {defineConfig} = require('@playwright/test');
module.exports = defineConfig({
  testDir: './tests',
  testMatch: 'mattermost.spec.cjs',
  workers: 1,
  timeout: 120000,
  reporter: [['list'], ['json', {outputFile:'migration-artifacts/browser-test-results.json'}]],
  use: {baseURL:'http://localhost:8065', browserName:'chromium', headless:true, viewport:{width:1440,height:1000}, screenshot:'only-on-failure'},
  outputDir:'migration-artifacts/browser-failures',
});
