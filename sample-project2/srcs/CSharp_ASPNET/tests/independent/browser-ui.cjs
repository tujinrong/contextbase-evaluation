'use strict';
// Independent spec-driven checks, run only against our explicitly owned final-publish fixture.
const fs = require('node:fs'), path = require('node:path'), crypto = require('node:crypto');
const assert = require('node:assert/strict');
const { chromium } = require(process.env.SP2_PLAYWRIGHT_MODULE || 'playwright-core');
const root = path.resolve(__dirname, '../..');
const scratch = path.join(root, '.tmp', 'audit-runtime');
const profilePath = path.resolve(process.env.SP2_AUDIT_PROFILE || path.join(scratch, 'profile.json'));
const read = file => JSON.parse(fs.readFileSync(file, 'utf8').replace(/^\uFEFF/, ''));
const sha = file => crypto.createHash('sha256').update(fs.readFileSync(file)).digest('hex');
assert.equal(profilePath, path.join(scratch, 'profile.json'), 'Explicit independent owned runtime only');
const profile = read(profilePath);
assert.equal(profile.database, 'SP2_WebFixture_AUDIT_R20261029');
assert.equal(profile.url, 'https://localhost:5183');
const expectedContract = process.env.SP2_EXPECTED_UI_SHA;
assert.match(expectedContract || '', /^[a-f0-9]{64}$/, 'Require notified frozen contract SHA');
const contractPath = path.join(root, 'tests', 'ui-contract.json');
assert.equal(sha(contractPath), expectedContract);
const contract = read(contractPath), inputPath = path.join(root, 'build', 'generation', 'inputs.json');
assert.equal(contract.authorship.frozenInputManifestSha256, sha(inputPath));
assert.equal(read(inputPath).inspectionOnly, false);
const out = path.join(root, 'build', 'test-results', 'independent-ui');
fs.mkdirSync(out, { recursive: true });
const selector = id => {
  const component = contract.components.find(c => c.id === id);
  assert.ok(component, 'Missing frozen component: ' + id);
  return component.selector;
};
function productTree() {
  const base = path.join(root, 'build', 'publish'), files = [];
  function walk(dir) {
    for (const e of fs.readdirSync(dir, { withFileTypes: true })) {
      const file = path.join(dir, e.name);
      assert.ok(!fs.lstatSync(file).isSymbolicLink(), 'Redirected product resource');
      if (e.isDirectory()) walk(file);
      else { assert.ok(e.isFile()); files.push({ file: path.relative(base, file).replaceAll('\\', '/'), bytes: fs.statSync(file).size, sha256: sha(file) }); }
    }
  }
  walk(base); files.sort((a, b) => a.file < b.file ? -1 : a.file > b.file ? 1 : 0);
  return { file: 'build/publish', files, sha256: crypto.createHash('sha256').update(JSON.stringify(files)).digest('hex'), digestConvention: 'SHA256 UTF8 JSON of ordinal file/bytes/sha256 array; independent full-resource witness' };
}
const productBefore = productTree(), results = [], traffic = [], errors = [];
assert.match(process.env.SP2_EXPECTED_PUBLISH_SHA || '', /^[a-f0-9]{64}$/, 'Require builder-notified full publish SHA');
assert.equal(productBefore.sha256, process.env.SP2_EXPECTED_PUBLISH_SHA, 'Current publish differs from notified candidate');
let browser, context, page, fatal, lastConsumedNavUrl;
const redact = value => String(value).replaceAll(String(profile.adminPassword), '[redacted]').replaceAll(String(profile.staffPassword), '[redacted]');
async function check(id, fn) {
  const start = Date.now();
  try { const evidence = await fn(); results.push({ id, status: 'PASS', elapsedMs: Date.now() - start, evidence }); }
  catch (e) { results.push({ id, status: 'FAIL', elapsedMs: Date.now() - start, error: redact(e.message) }); throw e; }
}
async function shot(name) {
  const file = path.join(out, name + '.png');
  await page.screenshot({ path: file, fullPage: true });
  return { file: path.relative(root, file).replaceAll('\\', '/'), sha256: sha(file) };
}
const field = id => page.locator(selector(id));
async function screen(id) {
  const target = selector(id + '.surface');
  await page.locator(target).waitFor({ state: 'visible' });
  if (id !== 'F01') await page.waitForFunction(s => { const n = document.querySelector(s); return n && n.dataset.ready === 'true' && !n.inert && !n.hasAttribute('data-pending-init'); }, target);
}
async function raw4() { return await Promise.all(['F03-I01', 'F03-I02', 'F03-I03', 'F03-I04'].map(id => field(id).inputValue())); }
async function newCancel() {
  const start = traffic.length;
  const opening = page.waitForResponse(r => new URL(r.url()).pathname === '/employees/open' && r.request().method() === 'POST');
  await Promise.all([page.waitForURL(u => u.pathname === '/employees/new'), field('F03-I10').click()]);
  const openResponse = await opening;
  assert.equal(openResponse.status(), 200, 'Navigation envelope must not use a fetch redirect');
  assert.match((await openResponse.allHeaders())['content-type'] || '', /^application\/json(?:;|$)/i);
  await screen('F04');
  assert.equal(await page.locator('dialog[open]').count(), 0);
  const cancelling = page.waitForResponse(r => new URL(r.url()).pathname === '/employees/cancel' && r.request().method() === 'POST');
  await Promise.all([page.waitForURL(u => u.pathname === '/employees'), field('F04-I29').click()]);
  const cancelResponse = await cancelling;
  assert.equal(cancelResponse.status(), 200);
  assert.match((await cancelResponse.allHeaders())['content-type'] || '', /^application\/json(?:;|$)/i);
  await screen('F03');
  assert.equal(await page.locator('dialog[open]').count(), 0, 'Untouched New cancel must not ask to save/discard');
  const requests = traffic.slice(start);
  for (const route of ['/employees/open', '/employees/cancel']) {
    const post = requests.filter(r => r.method === 'POST' && r.path === route);
    assert.equal(post.length, 1, 'One protected POST only');
    assert.match(post[0].contentType || '', /^application\/json(?:;|$)/i);
  }
  for (const route of ['/employees/new', '/employees']) assert.equal(requests.filter(r => r.method === 'GET' && r.path === route).length, 1, 'One navigation GET; no fetch ticket preconsumption');
  assert.equal(requests.filter(r => r.method === 'POST' && r.path === '/employees/search').length, 0);
  assert.equal(requests.filter(r => r.method === 'POST' && r.path === '/employees/save').length, 0);
  return requests;
}
async function overflow() {
  return page.evaluate(() => ({ width: innerWidth, height: innerHeight, scrollWidth: document.documentElement.scrollWidth, clientWidth: document.documentElement.clientWidth, overflow: Math.max(0, document.documentElement.scrollWidth - document.documentElement.clientWidth) }));
}
async function openNavIfCollapsed() {
  for (const details of await page.locator('nav details,.nav details').all()) {
    if (await details.isVisible() && await details.getAttribute('open') === null) {
      const summary = details.locator(':scope > summary');
      await summary.focus(); await page.keyboard.press('Enter');
      assert.notEqual(await details.getAttribute('open'), null, 'Native disclosure must open by keyboard');
    }
  }
  const candidates = await page.locator('button[aria-expanded][aria-controls]').all();
  for (const button of candidates) {
    const controls = await button.getAttribute('aria-controls');
    const ownsNav = await page.evaluate(id => { const n = document.getElementById(id); return !!n && n.matches('nav,.nav,[role="navigation"]'); }, controls);
    if (ownsNav && await button.isVisible() && await button.getAttribute('aria-expanded') === 'false') {
      await button.focus(); await page.keyboard.press('Enter');
      assert.equal(await button.getAttribute('aria-expanded'), 'true');
    }
  }
}
(async () => {
  try {
    browser = await chromium.launch({ executablePath: process.env.SP2_EDGE_PATH || 'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe', headless: true });
    context = await browser.newContext({ ignoreHTTPSErrors: true, viewport: { width: 1366, height: 768 } });
    page = await context.newPage();
    page.on('pageerror', e => errors.push(redact(e.message)));
    page.on('request', req => {
      const u = new URL(req.url());
      if (u.origin !== profile.url) return;
      if (req.method() === 'GET' && req.isNavigationRequest() && u.pathname === '/employees/new' && u.searchParams.has('nav')) lastConsumedNavUrl = u.pathname + u.search; // Private in-memory ticket, never logged.
      traffic.push({ method: req.method(), path: u.pathname, navigation: req.isNavigationRequest(), contentType: req.headers()['content-type'] || null });
    });
    await check('AUDIT-LOGIN', async () => {
      await page.goto(profile.url + '/account/login'); await screen('F01');
      await field('F01-I01').fill('admin'); await field('F01-I02').fill(profile.adminPassword);
      await Promise.all([page.waitForURL(u => u.pathname === '/menu'), field('F01-I04').click()]); await screen('F02');
      return { screenshot: await shot('menu-normal') };
    });
    await page.goto(profile.url + '/employees'); await screen('F03');
    await check('AUDIT-PH05-UNSEARCHED', async () => {
      await field('F03-I01').fill('000002'); await field('F03-I02').fill(' 佐藤 ');
      await field('F03-I03').selectOption('02'); await field('F03-I04').selectOption('02');
      const before = await raw4(), requests = await newCancel();
      assert.deepEqual(await raw4(), before, 'Raw4 must survive untouched New cancel without trimming/default overwrite');
      return { raw4: before, requests, screenshot: await shot('ph05-unsearched-return') };
    });
    await check('AUDIT-GET-RELOAD-AND-COPY', async () => {
      const before = await raw4(), start = traffic.length;
      await page.reload(); await screen('F03');
      assert.deepEqual(await raw4(), before, 'Valid search snapshot must resume on reload');
      assert.equal(traffic.slice(start).filter(r => r.method === 'POST' && r.path === '/employees/save').length, 0);
      const copy = await context.newPage();
      await copy.goto(profile.url + '/employees');
      await copy.locator(selector('F03.surface')).waitFor();
      assert.equal(await copy.locator(selector('F03-I01')).inputValue(), '', 'Direct second tab is independent');
      assert.deepEqual(await raw4(), before, 'Second tab must not alter original live state');
      await copy.close();
      return { originalRawRetained: true, directSecondTabIndependent: true, requests: traffic.slice(start), screenshot: await shot('reload-original-raw') };
    });
    await check('AUDIT-HISTORY-SNAPSHOT-COPY', async () => {
      const before = await raw4(), reference = await page.evaluate(() => history.state);
      assert.ok(reference?.resumeRef && reference?.sourceTabId, 'Opaque search snapshot is required');
      const copy = await context.newPage();
      try {
        await copy.goto(profile.url + '/employees');
        await copy.locator(selector('F03.surface')).waitFor();
        await copy.waitForFunction(s => { const n = document.querySelector(s); return n && n.dataset.ready === 'true' && !n.inert && !n.hasAttribute('data-pending-init'); }, selector('F03.surface'));
        await copy.evaluate(h => history.replaceState(h, '', '/employees'), reference);
        await copy.reload();
        await copy.waitForFunction(s => { const n = document.querySelector(s); return n && n.dataset.ready === 'true' && !n.inert && !n.hasAttribute('data-pending-init'); }, selector('F03.surface'));
        assert.deepEqual(await Promise.all(['F03-I01', 'F03-I02', 'F03-I03', 'F03-I04'].map(id => copy.locator(selector(id)).inputValue())), before);
        const changed = copy.waitForResponse(r => new URL(r.url()).pathname === '/employees/invalidate' && r.request().method() === 'POST');
        await copy.locator(selector('F03-I01')).fill('000001'); await changed;
        assert.deepEqual(await raw4(), before, 'Copied immutable snapshot must not share mutable live search state');
      } finally { await copy.close(); }
      assert.ok(Object.keys(reference).every(k => ['resumeRef', 'sourceTabId'].includes(k)), 'History may contain only opaque ref/source-tab metadata');
      return { snapshotCopiedIntoIndependentState: true, originalMutableStateUnchanged: true, noRawOrNamesInHistory: true };
    });
    await check('AUDIT-GET-OUTCOME-SHELL', async () => {
      const evidence = [];
      for (const [name, route, status] of [['consumed-ticket', lastConsumedNavUrl, 410], ['missing-employee', '/employees/9223372036854775807/edit', 404]]) {
        const response = await page.goto(profile.url + route);
        assert.equal(response.status(), status);
        assert.match((await response.allHeaders())['content-type'] || '', /^text\/html(?:;|$)/i);
        assert.ok(await page.locator('.sp2-ui').isVisible(), 'Normal GET failure must have application shell');
        assert.ok(await page.locator('a[href="/employees"]').first().isVisible(), 'Recovery action must be reachable');
        evidence.push({ name, status, screenshot: await shot('get-' + name) });
      }
      const staffContext = await browser.newContext({ ignoreHTTPSErrors: true, viewport: { width: 1366, height: 768 } });
      const staff = await staffContext.newPage();
      try {
        await staff.goto(profile.url + '/account/login');
        await staff.locator(selector('F01-I01')).fill('staff');
        await staff.locator(selector('F01-I02')).fill(profile.staffPassword);
        await Promise.all([staff.waitForURL(u => u.pathname === '/menu'), staff.locator(selector('F01-I04')).click()]);
        const response = await staff.goto(profile.url + '/codes');
        assert.equal(response.status(), 403);
        assert.match((await response.allHeaders())['content-type'] || '', /^text\/html(?:;|$)/i);
        assert.ok(await staff.locator('.sp2-ui').isVisible());
        assert.equal(await staff.locator('.nav a[href="/codes"]').count(), 0, 'STAFF error shell must not expose ADMIN entry');
        evidence.push({ name: 'staff-direct-forbidden', status: 403, htmlShell: true, administratorLinkAbsent: true });
      } finally { await staffContext.close(); }
      return evidence;
    });
    const routes = { F01: '/account/login', F02: '/menu', F03: '/employees', F04: '/employees/new', F06: '/codes' };
    for (const [id, route] of Object.entries(routes)) {
      if (id === 'F01') continue; // Logged-in public login behavior belongs to a separate unauthenticated context.
      for (const width of [1366, 1280, 768, 390, 320]) await check('AUDIT-VIEWPORT-' + id + '-' + width, async () => {
        await page.setViewportSize({ width, height: 768 }); await page.goto(profile.url + route); await screen(id);
        const rect = await overflow(); assert.ok(rect.overflow <= 1, 'Document horizontal overflow');
        await openNavIfCollapsed();
        const nav = page.locator('.nav a[href="/employees"]');
        assert.ok(await nav.isVisible(), 'Protected navigation must be reachable');
        await nav.scrollIntoViewIfNeeded(); await nav.focus();
        assert.equal(await nav.evaluate(n => n === document.activeElement), true);
        return { geometry: rect, screenshot: await shot('viewport-' + id + '-' + width) };
      });
    }
    assert.deepEqual(errors, [], 'No uncaught browser errors');
  } catch (e) { fatal = redact(e.message); }
  finally {
    if (browser) await browser.close();
    const productAfter = productTree();
    if (productBefore.sha256 !== productAfter.sha256) fatal = 'Final publish changed during independent test';
    const record = { schemaVersion: 1, runId: contract.runId, profileId: 'CSharp_ASPNET', status: fatal ? 'FAIL' : 'PASS_PARTIAL_INDEPENDENT_BROWSER', contractSha256: expectedContract, inputManifestSha256: sha(inputPath), testSha256: sha(__filename), product: productBefore, productAfterSha256: productAfter.sha256, fixture: { database: profile.database, url: profile.url }, results, errors, fatal, coverage: 'Owned final-publish headless Edge raw cancel/reload/direct and copied-snapshot second tabs, normal GET error shells and protected normal/narrow viewport subset only.', unexecuted: ['Native Windows keys/IME/clipboard', 'Actual browser text-only200%/OS DPI/real BFCache', 'Saved-commit ticket expiry/Unknown/fault/DB write/readback/Excel tests', 'User acceptance/formal score'], formalScore: null };
    fs.writeFileSync(path.join(out, 'review.json'), JSON.stringify(record, null, 2) + '\n');
    console.log(JSON.stringify({ status: record.status, cases: results.length, failed: results.filter(r => r.status === 'FAIL').length, fatal }));
    process.exitCode = fatal ? 1 : 0;
  }
})();
