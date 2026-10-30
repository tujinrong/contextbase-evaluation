'use strict';
// Owned fixture only. Save tests mutate one employee and one department name.
const fs = require('node:fs'), path = require('node:path'), crypto = require('node:crypto');
const assert = require('node:assert/strict'), { execFileSync } = require('node:child_process');
const { pathToFileURL } = require('node:url');
const { chromium } = require(process.env.SP2_PLAYWRIGHT_MODULE || 'playwright-core');
const owner = path.resolve(__dirname, '../..'), repo = path.resolve(owner, '../../..');
const read = file => JSON.parse(fs.readFileSync(file, 'utf8').replace(/^\uFEFF/, ''));
const sha = file => crypto.createHash('sha256').update(fs.readFileSync(file)).digest('hex');
const profile = read(path.join(owner, '.tmp/audit-runtime/profile.json'));
assert.equal(profile.database, 'SP2_WebFixture_AUDIT_R20261029'); assert.equal(profile.url, 'https://localhost:5183');
const contractPath = path.join(owner, 'tests/ui-contract.json'), contract = read(contractPath);
assert.equal(sha(contractPath), process.env.SP2_EXPECTED_UI_SHA);
const selector = id => contract.components.find(c => c.id === id).selector;
const out = path.join(owner, 'build/test-results/independent-ui'); fs.mkdirSync(out, { recursive: true });
const queries = { employee: "SELECT CONVERT(varchar(max),CONVERT(varbinary(max),employee_name),2) FROM dbo.m_employee WHERE employee_no='000001';", code: "SELECT CONVERT(varchar(max),CONVERT(varbinary(max),code_name),2) FROM dbo.m_code WHERE category_id='DEPARTMENT' AND code='01';" };
function dbValue(kind) {
  assert.ok(Object.hasOwn(queries, kind));
  const sql = "SET NOCOUNT ON; IF DB_NAME()<>N'SP2_WebFixture_AUDIT_R20261029' THROW 51000,'Database differs',1; IF NOT EXISTS(SELECT 1 FROM sys.extended_properties WHERE class=0 AND name=N'SP2Owner' AND CONVERT(nvarchar(200),value)=N'sample-project2/CSharp_ASPNET/SP2-DEMO-01') THROW 51000,'Owner differs',1; " + queries[kind];
  const result = execFileSync('C:/Program Files/Microsoft SQL Server/Client SDK/ODBC/180/Tools/Binn/SQLCMD.EXE', ['-S', '.\\SQLEXPRESS', '-E', '-C', '-b', '-d', profile.database, '-h', '-1', '-u', '-W', '-Q', sql], { windowsHide: true });
  // ASCII hex avoids sqlcmd console codepage differences; SQL nvarchar bytes are UTF16LE.
  const hex = result.toString(result.includes(0) ? 'utf16le' : 'utf8').replace(/^\uFEFF/, '').trim();
  assert.match(hex, /^(?:[0-9A-Fa-f]{2})+$/, 'Expected exact owned SQL nvarchar hex');
  return Buffer.from(hex, 'hex').toString('utf16le');
}
const digestText = s => crypto.createHash('sha256').update(s).digest('hex');
(async () => {
  const { hashArtifact } = await import(pathToFileURL(path.join(repo, 'agents/builds/build-agent/scripts/ui-conformance.mjs')));
  const artifact = hashArtifact(path.join(owner, 'build/publish')); assert.equal(artifact.sha256, process.env.SP2_EXPECTED_PUBLISH_SHA);
  let browser, page, fatal; const cases = [], errors = [];
  const redact = value => String(value).replaceAll(profile.adminPassword, '[redacted]').replaceAll(profile.staffPassword, '[redacted]');
  const item = id => page.locator(selector(id));
  async function ready(screen) {
    await page.locator(selector(screen + '.surface')).waitFor();
    await page.waitForFunction(s => { const n = document.querySelector(s); return n && n.dataset.ready === 'true' && !n.inert; }, selector(screen + '.surface'));
  }
  async function shot(name) { const file = path.join(out, name + '.png'); await page.screenshot({ path: file, fullPage: true }); return { file: path.relative(owner, file).replaceAll('\\', '/'), sha256: sha(file) }; }
  async function check(id, action) {
    try { cases.push({ id, status: 'PASS', evidence: await action() }); }
    catch (e) { const evidence = page ? { screenshot: await shot('interaction-failure-' + id) } : null; cases.push({ id, status: 'FAIL', error: redact(e.message), evidence }); throw e; }
  }
  async function states() {
    return page.locator('[data-screen-id] input:not([type="hidden"]),[data-screen-id] select,[data-screen-id] textarea').evaluateAll(nodes => nodes.map(n => ({ id: n.id, disabled: n.disabled, readOnly: !!n.readOnly })).sort((a, b) => a.id.localeCompare(b.id)));
  }
  async function pausedSave(routePath, buttonId) {
    let release, reached, delivered;
    const gate = new Promise(resolve => { release = resolve; }), arrived = new Promise(resolve => { reached = resolve; });
    const handled = new Promise(resolve => { delivered = resolve; });
    await page.route('**' + routePath, async route => {
      try { reached(); await gate; await route.continue(); }
      finally { delivered(); }
    });
    const response = page.waitForResponse(r => new URL(r.url()).pathname === routePath && r.request().method() === 'POST');
    try {
      await item(buttonId).click(); await arrived;
      const controls = await states();
      assert.ok(controls.length > 0 && controls.every(c => c.disabled), 'Every employee/career/code input including classification must disable during pending save');
      await page.keyboard.press('Tab'); await page.keyboard.type('X');
      return { controls, response };
    } finally { release(); await handled; await page.unroute('**' + routePath); }
  }
  try {
    browser = await chromium.launch({ executablePath: process.env.SP2_EDGE_PATH || 'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe', headless: true });
    const context = await browser.newContext({ ignoreHTTPSErrors: true, viewport: { width: 1366, height: 768 } }); page = await context.newPage(); page.on('pageerror', e => errors.push(redact(e.message)));
    await page.goto(profile.url + '/account/login'); await item('F01-I01').fill('admin'); await item('F01-I02').fill(profile.adminPassword);
    await Promise.all([page.waitForURL(u => u.pathname === '/menu'), item('F01-I04').click()]);
    await check('STAFF-FORBIDDEN-RECOVERY-AND-LOGOUT', async () => {
      const adminPage = page;
      const staffContext = await browser.newContext({ ignoreHTTPSErrors: true, viewport: { width: 1366, height: 768 } });
      page = await staffContext.newPage();
      try {
        await page.goto(profile.url + '/account/login'); await item('F01-I01').fill('staff'); await item('F01-I02').fill(profile.staffPassword);
        await Promise.all([page.waitForURL(u => u.pathname === '/menu'), item('F01-I04').click()]);
        const response = await page.goto(profile.url + '/codes'); assert.equal(response.status(), 403); await page.locator('[data-ui-error]').waitFor();
        assert.equal(await page.locator('#code-new').count(), 0, 'Forbidden code error must not expose inert New code CTA');
        await page.locator('a[href="/employees"]').first().click(); await page.waitForURL(u => u.pathname === '/employees'); await ready('F03');
        await page.goto(profile.url + '/codes'); await page.locator('[data-ui-error]').waitFor();
        await page.locator('[data-action="logout"]').click(); await page.waitForURL(u => u.pathname === '/account/login');
        return { actualStatus: 403, actualRecoveryCompleted: true, actualErrorLogoutCompleted: true, inertCodeCtaAbsent: true, screenshot: await shot('staff-forbidden-logout-complete') };
      } finally { await staffContext.close(); page = adminPage; }
    });
    await check('GET-RECOVERY-AND-LOGOUT', async () => {
      const response = await page.goto(profile.url + '/employees/9223372036854775807/edit'); assert.equal(response.status(), 404);
      const errorRoot = page.locator('[data-ui-error]'); await errorRoot.waitFor();
      const ctaCount = await page.locator('#code-new').count(); assert.equal(ctaCount, 0, 'Error page must not expose nonfunctional screen CTA');
      await page.locator('a[href="/employees"]').first().click(); await page.waitForURL(u => u.pathname === '/employees'); await ready('F03');
      const recovery = await shot('get-recovery-complete');
      await page.goto(profile.url + '/employees/9223372036854775807/edit'); await page.locator('[data-ui-error]').waitFor();
      await page.locator('[data-action="logout"]').click(); await page.waitForURL(u => u.pathname === '/account/login');
      await item('F01-I01').fill('admin'); await item('F01-I02').fill(profile.adminPassword);
      await Promise.all([page.waitForURL(u => u.pathname === '/menu'), item('F01-I04').click()]);
      return { errorPageCtaAbsent: true, actualRecoveryCompleted: true, actualErrorPageLogoutCompleted: true, screenshot: recovery };
    });
    await check('CONSUMED-TICKET-RECOVERY', async () => {
      await page.goto(profile.url + '/employees'); await ready('F03');
      let privateTicket;
      const captureTicket = request => { const u = new URL(request.url()); if (request.isNavigationRequest() && u.pathname === '/employees/new' && u.searchParams.has('nav')) privateTicket = u.pathname + u.search; };
      page.on('request', captureTicket);
      try { await Promise.all([page.waitForURL(u => u.pathname === '/employees/new'), item('F03-I10').click()]); await ready('F04'); }
      finally { page.off('request', captureTicket); }
      assert.ok(privateTicket);
      await Promise.all([page.waitForURL(u => u.pathname === '/employees'), item('F04-I29').click()]); await ready('F03');
      const response = await page.goto(profile.url + privateTicket); assert.equal(response.status(), 410); await page.locator('[data-ui-error]').waitFor();
      await page.locator('a[href="/employees"]').first().click(); await page.waitForURL(u => u.pathname === '/employees'); await ready('F03');
      return { actualStatus: 410, actualRecoveryCompleted: true, screenshot: await shot('consumed-ticket-recovery-complete') };
    });
    await page.goto(profile.url + '/employees'); await ready('F03');
    await item('F03-I01').fill('000001');
    const searched = page.waitForResponse(r => new URL(r.url()).pathname === '/employees/search' && r.request().method() === 'POST'); await item('F03-I05').click(); assert.equal((await searched).status(), 200);
    const edit = page.locator(selector('F03-I11')).first(), editUrl = await edit.getAttribute('href');
    await Promise.all([page.waitForURL(u => u.pathname === editUrl), edit.click()]); await ready('F04');
    await check('EMPLOYEE-VALIDATION-BUSY-RESTORE', async () => {
      const dbBefore = dbValue('employee'); await item('F04-I02').fill(''); const prior = await states();
      const paused = await pausedSave('/employees/save', 'F04-I28'); assert.equal((await paused.response).status(), 422);
      await page.waitForFunction(() => !document.querySelector('[data-item-id="F04-I02"]').disabled);
      assert.equal(await item('F04-I02').inputValue(), ''); assert.deepEqual(await states(), prior, 'Original disabled/readonly states must restore after rejection');
      assert.equal(dbValue('employee'), dbBefore, 'Validation must not modify persisted employee');
      return { waitingControls: paused.controls, priorStatesRestored: true, rejectedRawRetained: true, databaseUnchanged: true, screenshot: await shot('employee-invalid-retained') };
    });
    await check('EMPLOYEE-SAVE-BUSY-DB-READBACK', async () => {
      const name = '監査員' + Date.now().toString().slice(-6); await item('F04-I02').fill(name);
      const navigation = page.waitForURL(u => u.pathname === '/employees');
      const paused = await pausedSave('/employees/save', 'F04-I28'); assert.equal((await paused.response).status(), 200); await navigation; await ready('F03');
      assert.equal(dbValue('employee'), name, 'Actual SQL value must equal the pre-request capture, excluding typing attempted while busy');
      await page.goto(profile.url + editUrl); await ready('F04'); assert.equal(await item('F04-I02').inputValue(), name);
      assert.equal(await item('F04-I01').evaluate(n => n.readOnly && !n.disabled), true, 'Immutable employee key must remain readonly and copyable');
      return { waitingControls: paused.controls, sqlReadbackSha256: digestText(name), reopenedSavedValueMatches: true, immutableKeyStateRestored: true, screenshot: await shot('employee-saved-readback') };
    });
    await page.goto(profile.url + '/codes'); await ready('F06');
    const opened = page.waitForResponse(r => new URL(r.url()).pathname === '/codes/open' && r.request().method() === 'POST'); await page.locator('#code-rows button').filter({ hasText: /^01$/ }).click(); assert.equal((await opened).status(), 200);
    await check('CODE-SAVE-BUSY-DB-READBACK', async () => {
      const name = '監査コード' + Date.now().toString().slice(-6); await item('F06-I04').fill(name);
      const paused = await pausedSave('/codes/save', 'F06-I09'); assert.equal((await paused.response).status(), 200);
      await page.waitForFunction(() => !document.querySelector('[data-item-id="F06-I04"]').disabled);
      assert.equal(await item('F06-I04').inputValue(), name); assert.equal(dbValue('code'), name);
      assert.equal(await item('F06-I03').evaluate(n => n.readOnly && !n.disabled), true);
      assert.equal(await item('F06-I01').isDisabled(), false, 'Classification should restore its original enabled state');
      return { waitingControls: paused.controls, sqlReadbackSha256: digestText(name), immutableKeyStateRestored: true, classificationStateRestored: true, screenshot: await shot('code-saved-readback') };
    });
    assert.deepEqual(errors, []);
  } catch (e) { fatal = redact(e.message); }
  finally {
    if (browser) await browser.close();
    const after = hashArtifact(path.join(owner, 'build/publish'));
    if (after.sha256 !== artifact.sha256) fatal = 'Publish changed during targeted interaction test';
    const record = { schemaVersion: 1, profileId: 'CSharp_ASPNET', runId: contract.runId, status: fatal ? 'FAIL_TARGETED_INTERACTIONS' : 'PASS_TARGETED_INTERACTIONS', artifact, contractSha256: sha(contractPath), inputManifestSha256: sha(path.join(owner, 'build/generation/inputs.json')), testSha256: sha(__filename), fixture: { database: profile.database, url: profile.url, businessMutationScope: 'One existing employee name and one existing DEPARTMENT01 name; IDs/roles/counts preserved' }, cases, errors, fatal, unexecuted: ['Full29 interaction/366 rule matrix', 'Physical native keys/IME/clipboard/BFCache/text200/Excel/print/Unknown faults', 'Final source package reproduction/formal acceptance'], formalScore: null };
    fs.writeFileSync(path.join(out, 'interaction-review.json'), JSON.stringify(record, null, 2) + '\n');
    console.log(JSON.stringify({ status: record.status, cases: cases.length, failed: cases.filter(c => c.status === 'FAIL').length, fatal })); process.exitCode = fatal ? 1 : 0;
  }
})();
