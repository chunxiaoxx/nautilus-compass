// 全站渲染级审计:40 静态页+关键 SPA 路由,抓 console error/failed request/空白页
const { chromium } = require('playwright');
const path = require('path');

const PAGES = [
  'index.html','pricing.html','products/unipat.html','products/harness.html','products/compass.html',
  'products/data.html','products/embodied.html','products/companion.html','developers.html','customer.html',
  'submit/','intake.html','criteria.html','criteria/','leaderboard.html','login.html','os.html',
  'org/','org/business-plan.html','org/whitepaper.html','org/e2e.html',
  'admin.html','status.html','sites.html','tasks.html','blog.html','insights.html','errata.html',
  'two_week_report.html','whitepaper.html','business-plan.html','l2_sample.html','annotate.html',
  'announcement.html','pipeline.html','registry.html','auth/callback.html','unipat.html'
];
const BASE = 'https://www.nautilus.social/';

(async () => {
  const browser = await chromium.launch();
  const ctx = await browser.newContext({ viewport: { width: 1366, height: 900 } });
  const page = await ctx.newPage();
  const report = [];
  for (const p of PAGES) {
    const errors = [], failed = [];
    const onConsole = m => { if (m.type() === 'error') errors.push(m.text().slice(0, 90)); };
    const onReqFail = r => { if (!r.url().includes('favicon')) failed.push(r.url().replace(BASE, '').slice(0, 70)); };
    page.on('console', onConsole); page.on('requestfailed', onReqFail);
    let status = 0, bodyLen = 0;
    try {
      const resp = await page.goto(BASE + p, { waitUntil: 'domcontentloaded', timeout: 20000 });
      status = resp ? resp.status() : 0;
      await page.waitForTimeout(600);
      bodyLen = (await page.content()).length;
      const textLen = (await page.evaluate(() => document.body ? document.body.innerText.length : 0));
      const entry = { p, status, textLen };
      if (textLen < 40) entry.blank = true;
      if (errors.length) entry.consoleErrors = [...new Set(errors)].slice(0, 3);
      if (failed.length) entry.failedReq = [...new Set(failed)].slice(0, 3);
      report.push(entry);
    } catch (e) {
      report.push({ p, error: String(e).slice(0, 80) });
    }
    page.off('console', onConsole); page.off('requestfailed', onReqFail);
  }
  await browser.close();
  for (const r of report) {
    const flags = [];
    if (r.blank) flags.push('BLANK');
    if (r.error) flags.push('NAV-FAIL');
    if (r.consoleErrors) flags.push(`console x${r.consoleErrors.length}`);
    if (r.failedReq) flags.push(`reqfail x${r.failedReq.length}`);
    console.log(`${flags.length ? '🔴' : '✅'} ${r.p}  ${r.status || '-'} text:${r.textLen || 0} ${flags.join(' | ')}`);
    if (r.consoleErrors) r.consoleErrors.forEach(e => console.log('    E: ' + e));
    if (r.failedReq) r.failedReq.forEach(f => console.log('    F: ' + f));
  }
})();
