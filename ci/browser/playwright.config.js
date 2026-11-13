const {defineConfig} = require('@playwright/test');

module.exports = defineConfig({
  testDir: '.',
  testMatch: '*.spec.js',
  workers: 1,
  retries: 0,
  timeout: 30000,
  globalTimeout: 60000,
  use: {
    browserName: 'chromium',
    baseURL: 'http://127.0.0.1:8082',
    trace: 'retain-on-failure',
    screenshot: 'only-on-failure'
  }
});
