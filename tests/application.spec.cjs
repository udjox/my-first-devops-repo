const {test, expect} = require('@playwright/test');
const {execFileSync} = require('node:child_process');
const fs = require('node:fs');
function databaseItems() {
  // Данные читаются непосредственно из PostgreSQL, без API приложения.
  const sql = "SELECT COALESCE(json_agg(t ORDER BY t.id), '[]'::json) FROM (SELECT id, name FROM items) t;";
  return JSON.parse(execFileSync('docker', ['compose','exec','-T','db','sh','-c','exec psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -At -v ON_ERROR_STOP=1 -c "$1"','sh',sql], {encoding:'utf8'}));
}
test('Application health and database API', async ({request}) => {
  const health = await request.get('/healthz');
  expect(health.status()).toBe(200);
  expect((await health.text()).trim()).toBe('ok');
  const response = await request.get('/api/items');
  expect(response.status()).toBe(200);
  expect(await response.json()).toEqual(databaseItems());
});
test('Database records match the visible page and refresh', async ({page}) => {
  const expected = databaseItems();
  await page.goto('/');
  await expect(page.locator('#status')).toHaveText(`Получено записей: ${expected.length}`);
  const rows = page.locator('#items li');
  await expect(rows).toHaveText(expected.map(item => `${item.id}. ${item.name}`));
  await page.getByRole('button', {name:'Обновить список'}).click();
  await expect(page.locator('#status')).toHaveText(`Получено записей: ${expected.length}`);
  await expect(rows).toHaveText(expected.map(item => `${item.id}. ${item.name}`));
  fs.mkdirSync('artifacts', {recursive:true});
  await page.screenshot({path:'artifacts/site.png', fullPage:true});
  fs.writeFileSync('artifacts/data-comparison.json', JSON.stringify({database:expected, visibleRows:await rows.allTextContents(), passed:true},null,2));
});
