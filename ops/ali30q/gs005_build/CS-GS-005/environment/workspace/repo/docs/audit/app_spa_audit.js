const { chromium } = require('playwright');
const ROUTES = ['', 'login', 'pricing', 'leaderboard', 'dashboard', 'submit', 'tasks', 'agents'];
(async () => {
  const browser = await chromium.launch();
  const page = await browser.newPage();
  for (const r of ROUTES) {
    const errors = [];
    const onC = m => { if (m.type() === 'error') errors.push(m.text().slice(0, 80)); };
    page.on('console', onC);
    let status = 0, textLen = 0;
    try {
      const resp = await page.goto('https://app.nautilus.social/' + r, { waitUntil: 'domcontentloaded', timeout: 20000 });
      status = resp ? resp.status() : 0;
      await page.waitForTimeout(700);
      textLen = await page.evaluate(() => document.body ? document.body.innerText.length : 0);
    } catch (e) { errors.push('NAV ' + String(e).slice(0, 60)); }
    page.off('console', onC);
    const flags = [];
    if (status >= 400) flags.push('HTTP' + status);
    if (textLen < 40 && status < 400) flags.push('BLANK?');
    if (errors.length) flags.push(`console x${errors.length}`);
    console.log(`${flags.length ? '🔴' : '✅'} /${r} ${status} text:${textLen} ${flags.join(' | ')}`);
    errors.slice(0, 2).forEach(e => console.log('    E: ' + e));
  }
  await browser.close();
})();
