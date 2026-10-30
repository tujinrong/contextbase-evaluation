'use strict';
const fs = require('node:fs'), path = require('node:path'), crypto = require('node:crypto');
const assert = require('node:assert/strict');
const { pathToFileURL } = require('node:url');
const { chromium } = require(process.env.SP2_PLAYWRIGHT_MODULE || 'playwright-core');
const owner = path.resolve(__dirname, '../..'), repo = path.resolve(owner, '../../..');
const read = file => JSON.parse(fs.readFileSync(file, 'utf8').replace(/^\uFEFF/, ''));
const sha = file => crypto.createHash('sha256').update(fs.readFileSync(file)).digest('hex');
const profile = read(path.join(owner, '.tmp/audit-runtime/profile.json'));
assert.equal(profile.database, 'SP2_WebFixture_AUDIT_R20261029'); assert.equal(profile.url, 'https://localhost:5183');
const contractFile = path.join(owner, 'tests/ui-contract.json'), contract = read(contractFile);
assert.equal(sha(contractFile), process.env.SP2_EXPECTED_UI_SHA);
const selector = id => contract.components.find(c => c.id === id).selector;
const out = path.join(owner, 'build/test-results/independent-ui'); fs.mkdirSync(out, { recursive: true });
(async () => {
  const { hashArtifact } = await import(pathToFileURL(path.join(repo, 'agents/builds/build-agent/scripts/ui-conformance.mjs')));
  const artifact = hashArtifact(path.join(owner, 'build/publish')); assert.equal(artifact.sha256, process.env.SP2_EXPECTED_PUBLISH_SHA);
  let browser; const cases = [], errors = [];
  try {
    browser = await chromium.launch({ executablePath: process.env.SP2_EDGE_PATH || 'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe', headless: true });
    const context = await browser.newContext({ ignoreHTTPSErrors: true, viewport: { width: 1366, height: 768 } });
    const page = await context.newPage(); page.on('pageerror', e => errors.push(e.message));
    await page.goto(profile.url + '/account/login');
    await page.locator(selector('F01-I01')).fill('admin'); await page.locator(selector('F01-I02')).fill(profile.adminPassword);
    await Promise.all([page.waitForURL(u => u.pathname === '/menu'), page.locator(selector('F01-I04')).click()]);
    for (const width of [390, 320]) {
      await page.setViewportSize({ width, height: 768 }); await page.goto(profile.url + '/codes');
      await page.waitForFunction(() => { const n = document.querySelector('.sp2-ui'); return n && n.dataset.ready === 'true' && !n.inert; });
      const geometry = await page.evaluate(() => {
        const viewport = document.documentElement.clientWidth;
        const boxes = Array.from(document.querySelectorAll('.sp2-ui *')).filter(n => n.getClientRects().length).map(n => {
          const r = n.getBoundingClientRect(), s = getComputedStyle(n), p = n.parentElement.getBoundingClientRect();
          return { tag: n.tagName, id: n.id, item: n.dataset.itemId || null, class: n.className, left: r.left, right: r.right, width: r.width, parentWidth: p.width, scrollWidth: n.scrollWidth, minWidth: s.minWidth, maxWidth: s.maxWidth, display: s.display, overflowX: s.overflowX, gridTemplateColumns: s.gridTemplateColumns, outsideViewport: r.left < -1 || r.right > viewport + 1 };
        });
        return { viewport, documentScrollWidth: document.documentElement.scrollWidth, overflow: Math.max(0, document.documentElement.scrollWidth - viewport), containers: boxes.filter(n => /(?:shell|main|codecols|listwrap|panel|fields|field)/.test(n.class)), outsideViewport: boxes.filter(n => n.outsideViewport) };
      });
      const imageFile = path.join(out, 'failure-F06-' + width + '.png'); await page.screenshot({ path: imageFile, fullPage: true });
      cases.push({ viewport: { width, height: 768 }, status: geometry.overflow <= 1 ? 'PASS' : 'FAIL', geometry, screenshot: { file: path.relative(owner, imageFile).replaceAll('\\', '/'), sha256: sha(imageFile) } });
    }
  } finally {
    if (browser) await browser.close();
    const after = hashArtifact(path.join(owner, 'build/publish')); assert.equal(after.sha256, artifact.sha256);
    const record = { schemaVersion: 1, profileId: 'CSharp_ASPNET', runId: contract.runId, status: cases.length === 2 && cases.every(c => c.status === 'PASS') && !errors.length ? 'PASS_TARGETED_VIEWPORT' : 'FAIL_TARGETED_VIEWPORT', artifact, contractSha256: sha(contractFile), inputManifestSha256: sha(path.join(owner, 'build/generation/inputs.json')), testSha256: sha(__filename), cases, errors, scope: 'Independent actual final-publish F06 geometry at390/320 only; no native input, text enlargement, DB write or print proof.', formalScore: null };
    fs.writeFileSync(path.join(out, 'viewport-review.json'), JSON.stringify(record, null, 2) + '\n');
    console.log(JSON.stringify({ status: record.status, cases: cases.map(c => ({ width: c.viewport.width, overflow: c.geometry.overflow })) }));
    process.exitCode = record.status.startsWith('PASS') ? 0 : 1;
  }
})();
