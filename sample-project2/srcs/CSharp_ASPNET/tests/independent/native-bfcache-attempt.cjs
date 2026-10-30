'use strict';
// One bounded, actual native BFCache trial. No synthetic lifecycle events or successful Save.
const fs = require('node:fs'), path = require('node:path'), crypto = require('node:crypto'), assert = require('node:assert/strict'), http = require('node:http');
const { pathToFileURL } = require('node:url');
const owner = path.resolve(__dirname, '../..'), repo = path.resolve(owner, '../../..');
const read = f => JSON.parse(fs.readFileSync(f, 'utf8').replace(/^\uFEFF/, ''));
const sha = f => crypto.createHash('sha256').update(fs.readFileSync(f)).digest('hex');
const rel = f => path.relative(owner, f).replaceAll('\\', '/');
const proof = f => ({ file: rel(f), sha256: sha(f) });
const profileFile = path.join(owner, '.tmp/audit-additional-runtime/profile.json'), profile = read(profileFile);
assert.equal(profile.database, 'SP2_WebFixture_AUDIT_ADD_R20261030'); assert.equal(profile.url, 'https://localhost:5185');
const contractFile = path.join(owner, 'tests/ui-contract.json'), inputFile = path.join(owner, 'build/generation/inputs.json');
assert.equal(sha(contractFile), process.env.SP2_EXPECTED_UI_SHA);
const rule = read(contractFile).rules.find(r => r.id === 'DUI11.bfcache');
const descriptor = { id: rule.id, target: rule.target, propertyNames: Object.keys(rule.properties) };
const out = path.join(owner, 'build/test-results/independent-native-bfcache'); fs.mkdirSync(out, { recursive: true });

async function run() {
  const { hashArtifact } = await import(pathToFileURL(path.join(repo, 'agents/builds/build-agent/scripts/ui-conformance.mjs')));
  const artifact = hashArtifact(path.join(owner, 'build/publish')); assert.equal(artifact.sha256, process.env.SP2_EXPECTED_PUBLISH_SHA);
  const source = proof(__filename), inputSha = sha(inputFile), contractSha = sha(contractFile);
  const { chromium } = require(process.env.SP2_PLAYWRIGHT_MODULE || 'playwright-core');
  const browser = await chromium.launch({ executablePath: 'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe', headless: true, ignoreDefaultArgs: ['--disable-back-forward-cache'] });
  const events = [], requests = [], errors = [], observations = [], notMeasured = [], lifecycleWaitNotes = [];
  const server = http.createServer((req, res) => { res.writeHead(200, { 'Content-Type': 'text/html; charset=utf-8', 'Cache-Control': 'public, max-age=300' }); res.end('<!doctype html><title>Owned BFCache positive control</title><p>' + (req.url === '/a' ? 'A' : 'B') + '</p>'); });
  let context, page, control = null, actual = null;
  async function ready() { await page.waitForFunction(() => { const n = document.querySelector('.sp2-ui'); return n && n.dataset.ready === 'true' && !n.inert && !n.hasAttribute('data-pending-init'); }); }
  async function backOnce(expectedUrl) {
    try { await page.goBack({ waitUntil: 'commit', timeout: 5000 }); }
    catch (e) {
      if (e.name !== 'TimeoutError' || page.url() !== expectedUrl) throw e;
      // BFCache restoration need not emit a fresh DOMContentLoaded lifecycle event.
      // This note is not evidence of persistence: the trusted pageshow journal decides that.
      lifecycleWaitNotes.push({ expectedUrl, timeout: true, urlObserved: page.url() });
    }
  }
  async function snapshot() { return page.evaluate(() => {
    const model = JSON.parse(document.querySelector('[data-initial]').dataset.initial), fields = [...document.querySelectorAll('#f03-i01,#f03-i02,#f03-i03,#f03-i04')];
    return { documentId: window.__nativeAuditDocument, stateId: model.ui.stateId, resultStatus: model.resultStatus, totalCount: model.totalCount, raw: fields.map(n => [n.id, n.value]), appliedCriteria: model.appliedCriteria, rows: [...document.querySelectorAll('#search-rows tr')].map(n => n.innerText), selectedEmployeeId: model.selectedEmployeeId, selectedRadioCount: document.querySelectorAll('#search-rows input:checked').length, scrollTop: document.querySelector('.listwrap')?.scrollTop ?? null, modelScrollTop: model.scrollTop ?? null, inert: !!document.querySelector('.sp2-ui').inert };
  }); }
  try {
    await new Promise(resolve => server.listen(0, '127.0.0.1', resolve));
    context = await browser.newContext({ ignoreHTTPSErrors: true, viewport: { width: 1366, height: 768 } }); context.setDefaultTimeout(15000);
    await context.exposeBinding('__nativeAuditPageshow', (_, event) => events.push({ ...event, receivedAt: Date.now() }));
    await context.addInitScript(() => { window.__nativeAuditDocument = crypto.randomUUID(); addEventListener('pageshow', e => window.__nativeAuditPageshow({ documentId: window.__nativeAuditDocument, persisted: e.persisted, trusted: e.isTrusted, origin: location.origin, path: location.pathname, at: Date.now() })); });
    page = await context.newPage();
    page.on('pageerror', e => errors.push(e.message));
    page.on('dialog', async d => { if (d.type() === 'beforeunload') await d.accept(); else { errors.push('Unexpected native dialog: ' + d.type()); await d.dismiss(); } });
    page.on('request', r => requests.push({ method: r.method(), path: new URL(r.url()).pathname, navigation: r.isNavigationRequest(), at: Date.now() }));
    const base = 'http://127.0.0.1:' + server.address().port;
    await page.goto(base + '/a'); const controlDoc = await page.evaluate(() => window.__nativeAuditDocument);
    await page.goto(base + '/b'); await backOnce(base + '/a'); await page.waitForTimeout(250);
    control = { documentIdBefore: controlDoc, documentIdAfter: await page.evaluate(() => window.__nativeAuditDocument), events: events.filter(e => e.origin === base), launchConfiguration: { ignoreDefaultArgs: ['--disable-back-forward-cache'], actualCommandLineObserved: false } };
    control.persistedObserved = control.events.some(e => e.documentId === controlDoc && e.persisted && e.trusted);
    await page.goto(profile.url + '/account/login'); await page.locator('[data-item-id="F01-I01"]').fill('staff'); await page.locator('[data-item-id="F01-I02"]').fill(profile.staffPassword);
    await Promise.all([page.waitForURL(u => u.pathname === '/menu'), page.locator('[data-item-id="F01-I04"]').click()]); await ready();
    await page.goto(profile.url + '/employees'); await ready(); await page.locator('#f03-i01').fill('000001');
    const [searchResponse] = await Promise.all([page.waitForResponse(r => new URL(r.url()).pathname === '/employees/search' && r.request().method() === 'POST'), page.locator('#search-run').click()]); assert.equal(searchResponse.status(), 200);
    await page.waitForFunction(() => { const m = JSON.parse(document.querySelector('[data-initial]').dataset.initial); return m.resultStatus === 'Success' && m.rows.length > 0 && !document.querySelector('#search-run').disabled; });
    const [selectResponse] = await Promise.all([page.waitForResponse(r => new URL(r.url()).pathname === '/employees/select' && r.request().method() === 'POST'), page.locator('#search-rows input[type=radio]').first().check()]); assert.equal(selectResponse.status(), 200);
    const selectedResponseModel = await selectResponse.json(); assert.ok(selectedResponseModel && selectedResponseModel.selectedEmployeeId != null);
    await page.waitForFunction(selectedId => { const m = JSON.parse(document.querySelector('[data-initial]').dataset.initial); return m.selectedEmployeeId === selectedId && document.querySelectorAll('#search-rows input:checked').length === 1 && !document.querySelector('#search-run').disabled; }, selectedResponseModel.selectedEmployeeId);
    const before = await snapshot(), started = Date.now(), requestStart = requests.length, eventStart = events.length; assert.ok(before.appliedCriteria);
    await Promise.all([page.waitForURL(u => /\/employees\/\d+\/edit$/.test(u.pathname)), page.locator('#search-rows a').first().click()]); await ready();
    await backOnce(profile.url + '/employees');
    await page.waitForURL(u => u.pathname === '/employees'); await ready(); await page.waitForTimeout(700);
    const after = await snapshot(), observedEvents = events.slice(eventStart), persisted = observedEvents.some(e => e.documentId === before.documentId && e.path === '/employees' && e.persisted && e.trusted);
    const navigationGets = requests.slice(requestStart).filter(r => r.navigation && r.method === 'GET' && r.path === '/employees');
    actual = { before, after, nativePersistedSearchObserved: persisted, events: observedEvents, requests: requests.slice(requestStart), observationWindowMs: Date.now() - started, limitation: 'One actual back trial. The finite post-ready idle window is 700ms. No physical IME/clipboard, synthetic pageshow or unprepared EditDraft isolation claim.' };
    if (persisted) {
      const sameSnapshot = ['resultStatus', 'totalCount', 'raw', 'appliedCriteria', 'rows', 'selectedEmployeeId', 'selectedRadioCount', 'scrollTop', 'modelScrollTop'].every(k => JSON.stringify(before[k]) === JSON.stringify(after[k]));
      const properties = { validSnapshotRestored: sameSnapshot, newStateAllocated: before.stateId !== after.stateId, reloadLoopCount: Math.max(0, navigationGets.length - 1), uiEnabledAfterResume: !after.inert && await page.locator('#search-run').isEnabled() };
      const rawFile = path.join(out, 'actual.json'); fs.writeFileSync(rawFile, JSON.stringify({ control, actual }, null, 2) + '\n');
      observations.push({ ruleId: descriptor.id, target: descriptor.target, method: 'keyboard-operation', properties, evidence: [proof(rawFile)] });
      notMeasured.push({ ruleId: descriptor.id, properties: ['editDraftShared'], reason: 'A native persisted search path was entered, but an unsaved EditDraft isolation precondition was not prepared in this single trial.' });
    } else notMeasured.push({ ruleId: descriptor.id, properties: descriptor.propertyNames, reason: 'No trusted native pageshow.persisted=true was observed for the product search document. No synthetic event or nonpersisted back path is promoted to BFCache evidence.' });
    await page.screenshot({ path: path.join(out, 'after.png'), fullPage: true });
    actual.notRestoredReasons = await page.evaluate(() => performance.getEntriesByType('navigation').map(n => ({ type: n.type, notRestoredReasons: n.notRestoredReasons?.toJSON?.() ?? n.notRestoredReasons ?? null })));
    fs.writeFileSync(path.join(out, 'actual.json'), JSON.stringify({ control, actual }, null, 2) + '\n');
    // Add evidence after the final raw file has been written, never retain its previous digest.
    for (const o of observations) o.evidence = [proof(path.join(out, 'actual.json')), proof(path.join(out, 'after.png'))];
  } catch (e) { errors.push(String(e.message).replaceAll(profile.staffPassword, '[redacted]')); notMeasured.push({ ruleId: descriptor.id, properties: descriptor.propertyNames, reason: 'Trial did not finish; no missing property is synthesized.' }); }
  finally {
    await browser.close(); await new Promise(resolve => server.close(resolve));
    assert.equal(hashArtifact(path.join(owner, 'build/publish')).sha256, artifact.sha256); assert.equal(sha(contractFile), contractSha); assert.equal(sha(inputFile), inputSha); assert.equal(sha(__filename), source.sha256);
    const record = { schemaVersion: 1, projectId: 'sample-project2', profileId: 'CSharp_ASPNET', runId: read(contractFile).runId, status: observations.length ? 'PARTIAL_NATIVE_BFCACHE_ACTUALS' : 'NOT_VERIFIED_NATIVE_BFCACHE', artifact, contractSha256: contractSha, inputManifestSha256: inputSha, measurementSources: [source], fixture: { database: profile.database, url: profile.url }, control, actual, lifecycleWaitNotes, events, observations, notMeasured, errors, preparationNotes: ['Earlier setup-only runs stopped at unsupported Browser.getBrowserCommandLine and at a static-control DOMContentLoaded wait. No product Back was attempted in those runs; no earlier setup claim is adopted.'], formalScore: null };
    fs.writeFileSync(path.join(out, 'partial-observations.json'), JSON.stringify(record, null, 2) + '\n'); console.log(JSON.stringify({ status: record.status, positiveControlPersisted: control?.persistedObserved, productPersisted: actual?.nativePersistedSearchObserved, observations: observations.length, errors }));
  }
}
run().catch(e => { console.error(e.message); process.exitCode = 1; });
