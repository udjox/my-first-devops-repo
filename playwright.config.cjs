const {defineConfig} = require('@playwright/test');
module.exports = defineConfig({
  testDir: './tests',
  workers: 1,
  timeout: 30000,
  reporter: [['list'], ['json', {outputFile: 'artifacts/test-results.json'}], ['html', {outputFolder: 'artifacts/playwright-report', open: 'never'}]],
  use: {baseURL: `http://127.0.0.1:${process.env.APP_PORT || '8080'}`, browserName: 'chromium', headless: true, screenshot: 'only-on-failure'},
});
