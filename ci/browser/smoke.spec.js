const {test, expect} = require('@playwright/test');

test('form loads and displays a real Python regex result with CSP enforced', async ({page}) => {
  const errors = [];
  page.on('pageerror', error => errors.push(error.message));
  page.on('console', message => {
    if (message.type() === 'error') errors.push(message.text());
  });
  page.on('requestfailed', request => errors.push(`${request.url()}: ${request.failure().errorText}`));
  await page.addInitScript(() => {
    window.cspViolations = [];
    document.addEventListener('securitypolicyviolation', event => {
      window.cspViolations.push(`${event.violatedDirective}: ${event.blockedURI}`);
    });
  });

  const response = await page.goto('/');
  expect(response.ok()).toBeTruthy();
  expect(response.headers()['content-security-policy']).toContain("script-src 'self'");
  await expect(page.locator('#regex')).toBeVisible();
  await expect(page.locator('#test-string')).toBeVisible();
  await page.locator('#regex').fill('(?P<word>hello)');
  const result = page.waitForResponse(response => {
    const url = new URL(response.url());
    return url.pathname === '/api/regex/test/' &&
      url.searchParams.get('regex') === '(?P<word>hello)' &&
      url.searchParams.get('test_string') === 'hello world';
  });
  await page.locator('#test-string').fill('hello world');
  const apiResponse = await result;
  expect(apiResponse.status()).toBe(200);
  expect(await apiResponse.json()).toMatchObject({result_type: 'match', result: {group: 'hello'}});
  await expect(page.getByText('Success!', {exact: true})).toBeVisible();
  await expect(page.locator('.main-group code')).toBeVisible();
  await expect(page.locator('.main-group code')).toHaveText('hello');
  expect(await page.evaluate(() => window.cspViolations)).toEqual([]);
  expect(errors).toEqual([]);
});
