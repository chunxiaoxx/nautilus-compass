// 分批版:routes 由 argv JSON 传入,结果即时 append 到文件
const { chromium } = require('playwright');
const fs = require('fs');
const ROUTES = JSON.parse(process.argv[2]);
const OUT = process.argv[3] || 'audit_out.txt';
(async () => {
  const browser = await chromium.launch();
  const page = await browser.newPage();
  for (const r of ROUTES) {
    const errors = [];
    const onC = m => { if (m.type() === 'error') errors.push(m.text().slice(0, 70)); };
    page.on('console', onC);
    let status = 0, textLen = 0, url = '';
    try {
      const resp = await page.goto('https://app.nautilus.social' + r, { waitUntil: 'domcontentloaded', timeout: 15000 });
      status = resp ? resp.status() : 0;
      await page.waitForTimeout(600);
      textLen = await page.evaluate(() => document.body ? document.body.innerText.length : 0);
      url = page.url().replace('https://app.nautilus.social', '');
    } catch (e) { errors.push('NAV ' + String(e).slice(0, 50)); }
    page.off('console', onC);
    const flags = [];
    if (status >= 400) flags.push('HTTP' + status);
    if (textLen < 40 && status < 400) flags.push('BLANK');
    if (errors.length) flags.push('console x' + errors.length);
    let line = `${flags.length ? 'RED' : 'OK '} ${r.padEnd(22)} ${status} text:${String(textLen).padEnd(5)} ${flags.join('|')}${url !== r ? ' ->' + url : ''}`;
    errors.slice(0, 1).forEach(e => line += '\n     E: ' + e);
    fs.appendFileSync(OUT, line + '\n');
  }
  await browser.close();
})();
