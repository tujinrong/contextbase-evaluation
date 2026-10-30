'use strict';
// Additional real operations in ONE newly owned Audit fixture. No product/expected/source edits.
const fs = require('node:fs'), path = require('node:path'), crypto = require('node:crypto'), assert = require('node:assert/strict');
const { execFileSync } = require('node:child_process'), { pathToFileURL } = require('node:url');
const owner = path.resolve(__dirname, '../..'), repo = path.resolve(owner, '../../..');
const read = f => JSON.parse(fs.readFileSync(f, 'utf8').replace(/^\uFEFF/, ''));
const sha = f => crypto.createHash('sha256').update(fs.readFileSync(f)).digest('hex');
const digest = x => crypto.createHash('sha256').update(JSON.stringify(x)).digest('hex');
const rel = f => path.relative(owner, f).replaceAll('\\', '/');
const proof = f => ({ file: rel(f), sha256: sha(f) });
const profileFile = path.join(owner, '.tmp/audit-additional-runtime/profile.json'), profile = read(profileFile);
assert.equal(profile.database, 'SP2_WebFixture_AUDIT_ADD_R20261030'); assert.equal(profile.url, 'https://localhost:5185');
const contractFile = path.join(owner, 'tests/ui-contract.json'), contract = read(contractFile);
assert.equal(sha(contractFile), process.env.SP2_EXPECTED_UI_SHA);
// Expected values/operators do not cross into observation collection.
const rules = new Map(contract.rules.map(r => [r.id, { id: r.id, target: r.target, propertyNames: Object.keys(r.properties) }]));
const out = path.join(owner, 'build/test-results/independent-additional-interactions'); fs.mkdirSync(out, { recursive: true });
const sqlcmd = 'C:/Program Files/Microsoft SQL Server/Client SDK/ODBC/180/Tools/Binn/SQLCMD.EXE';
function sql(query, isFault = false) {
  if (isFault) assert.ok(query === "EXEC sys.sp_rename N'dbo.m_employee',N'm_employee_AUDIT_READFAULT',N'OBJECT';" || query === "EXEC sys.sp_rename N'dbo.m_employee_AUDIT_READFAULT',N'm_employee',N'OBJECT';");
  else assert.match(query.trimStart(), /^SELECT\s/i, 'Only read queries except two explicit owned-fault renames');
  const guard = "SET NOCOUNT ON; IF DB_NAME()<>N'SP2_WebFixture_AUDIT_ADD_R20261030' THROW 51000,'Wrong audit DB',1; IF NOT EXISTS(SELECT 1 FROM sys.extended_properties WHERE class=0 AND name=N'SP2Owner' AND CONVERT(nvarchar(200),value)=N'sample-project2/CSharp_ASPNET/SP2-DEMO-01') THROW 51000,'Wrong fixture owner',1; ";
  const bytes = execFileSync(sqlcmd, ['-S', '.\\SQLEXPRESS', '-E', '-C', '-b', '-d', profile.database, '-u', '-y', '0', '-Q', guard + query], { windowsHide: true });
  return bytes.toString(bytes.includes(0) ? 'utf16le' : 'utf8').replace(/^\uFEFF/, '').trim();
}
const rows = query => {
  // SQL emits JSON as UTF16LE varbinary encoded to ASCII hex, avoiding native sqlcmd console codepages entirely.
  const value = sql("SELECT CONVERT(varchar(max),CONVERT(varbinary(max),COALESCE((" + query + " FOR JSON PATH,INCLUDE_NULL_VALUES),N'[]')),2);").replace(/\s/g, '');
  assert.match(value, /^(?:[0-9A-Fa-f]{2})+$/, 'Expected full ASCII hex JSON');
  return JSON.parse(Buffer.from(value, 'hex').toString('utf16le'));
};
const employee = no => { assert.match(no, /^\d{6}$/); return rows("SELECT * FROM dbo.m_employee WHERE employee_no='" + no + "'")[0]; };
const business = () => ({ employees: rows('SELECT * FROM dbo.m_employee ORDER BY employee_id'), careers: rows('SELECT * FROM dbo.t_career ORDER BY career_id') });
function counter() {
  return rows("SELECT q.execution_count,CONVERT(varchar(130),q.plan_handle,1) AS plan_token,q.statement_start_offset,q.statement_end_offset,CONVERT(varchar(33),q.creation_time,126) AS created FROM sys.dm_exec_query_stats q CROSS APPLY sys.dm_exec_sql_text(q.sql_handle)t CROSS APPLY sys.dm_exec_plan_attributes(q.plan_handle)a WHERE a.attribute='dbid' AND CONVERT(int,a.value)=DB_ID() AND t.text LIKE '%SELECT e.employee_id,e.employee_no%' AND t.text LIKE '%ORDER BY e.employee_no;%' AND t.text NOT LIKE '%sys.dm_exec_query_stats%'");
}
function delta(before, after) {
  const key = r => [r.plan_token, r.statement_start_offset, r.statement_end_offset, r.created].join('|');
  const b = new Map(before.map(r => [key(r), r.execution_count])), a = new Map(after.map(r => [key(r), r.execution_count]));
  if (!b.size || [...b].some(([k, v]) => !a.has(k) || a.get(k) < v)) return { verified: false, reason: 'SQL search cache empty/evicted/recreated; zero/one is not inferred', before, after };
  return { verified: true, executedSearchQueries: [...a.values()].reduce((x, y) => x + y, 0) - [...b.values()].reduce((x, y) => x + y, 0), before, after, method: 'DMV cumulative actual SQL-SEARCH executions in exact owned DB; all before plan+statement+creation keys remain present/nondecreasing' };
}

async function run() {
  const { hashArtifact } = await import(pathToFileURL(path.join(repo, 'agents/builds/build-agent/scripts/ui-conformance.mjs')));
  const artifact = hashArtifact(path.join(owner, 'build/publish')); assert.equal(artifact.sha256, process.env.SP2_EXPECTED_PUBLISH_SHA);
  const source = proof(__filename), inputFile = path.join(owner, 'build/generation/inputs.json'), inputSha = sha(inputFile);
  const baseline337 = proof(path.join(owner, 'build/test-results/independent-ui/noninteraction/partial-observations.json'));
  const baselineInventory = proof(path.join(owner, 'build/test-results/independent-ui/component-inventory-supplement.json'));
  const { chromium } = require(process.env.SP2_PLAYWRIGHT_MODULE || 'playwright-core');
  const browser = await chromium.launch({ executablePath: 'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe', headless: true });
  const cases = [], observations = [], notMeasured = [], errors = [], requests = [], dialogs = [], responses = [], pending = [];
  let context, page, warmPage, currentCase = '', phase = '', renamed = false;
  const count = (journal, start, name) => journal.slice(start).filter(r => r.path === name && r.method === 'POST').length;
  const raw = p => p.locator('#f03-i01,#f03-i02,#f03-i03,#f03-i04').evaluateAll(ns => Object.fromEntries(ns.map((n, i) => [['employeeNo', 'name', 'department', 'employmentStatus'][i], n.value])));
  const model = p => p.locator('[data-initial]').evaluate(n => JSON.parse(n.dataset.initial));
  async function ready(p = page) { await p.waitForFunction(() => { const n = document.querySelector('.sp2-ui'); return n && n.dataset.ready === 'true' && !n.inert && !n.hasAttribute('data-pending-init'); }); }
  async function go(url, p = page) { await p.goto(profile.url + url); await ready(p); }
  async function type(selector, value, p = page) { await p.locator(selector).click(); await p.keyboard.press('Control+A'); await p.keyboard.press('Backspace'); await p.keyboard.type(value); }
  async function clickResponse(selector, pathname, p = page) { const next = p.waitForResponse(r => new URL(r.url()).pathname === pathname && r.request().method() === 'POST'); await p.locator(selector).click(); return await next; }
  async function navigate(selector, pathname) { await Promise.all([page.waitForURL(u => u.pathname === pathname), page.locator(selector).click()]); await ready(); }
  async function api(pathname, payload, p = page) { return p.evaluate(async ({ pathname, payload }) => { const r = await fetch(pathname, { method: 'POST', credentials: 'same-origin', redirect: 'error', headers: { 'Content-Type': 'application/json', 'X-SP2-CSRF': document.querySelector('input[name="__RequestVerificationToken"]').value, 'X-SP2-User-Action': 'true' }, body: JSON.stringify(payload) }); return { status: r.status, body: await r.json() }; }, { pathname, payload }); }
  async function warmCounter() {
    if (warmPage) await warmPage.close(); warmPage = await context.newPage(); await go('/employees', warmPage); await type('#f03-i01', '000001', warmPage); assert.equal((await clickResponse('#search-run', '/employees/search', warmPage)).status(), 200); await warmPage.locator('#search-rows tr').waitFor();
    return counter();
  }
  async function roundtrip() { await navigate('#employee-new', '/employees/new'); await navigate('#employee-cancel', '/employees'); }
  async function emit(ruleId, properties, actual) {
    const file = path.join(out, ruleId + '.json'), image = path.join(out, ruleId + '.png');
    await page.screenshot({ path: image, fullPage: true }); fs.writeFileSync(file, JSON.stringify({ ruleId, properties, actual, requestScope: requests.filter(r => r.caseId === currentCase), responseScope: responses.filter(r => r.caseId === currentCase), dialogScope: dialogs.filter(d => d.caseId === currentCase) }, null, 2) + '\n');
    const r = rules.get(ruleId), evidence = [proof(file), proof(image)];
    observations.push({ ruleId, target: r.target, method: 'keyboard-operation', properties, evidence });
    const absent = r.propertyNames.filter(k => !Object.hasOwn(properties, k)); if (absent.length) notMeasured.push({ ruleId, properties: absent, reason: 'Only independently obtained properties are recorded; server-side original-state/copy proof belongs to the separate read-only observer case.', evidence });
    cases.push({ id: ruleId, status: absent.length ? 'PARTIAL_ACTUAL_RECORDED' : 'ACTUAL_RECORDED', evidence });
  }
  async function scenario(id, action) {
    currentCase = id; phase = 'prepare';
    try { await go('/employees'); await action(); }
    catch (e) { cases.push({ id, status: 'PRECONDITION_OR_EXECUTION_FAILURE', error: String(e.message).replaceAll(profile.staffPassword, '[redacted]') }); notMeasured.push({ ruleId: id, reason: 'Case did not finish; no missing value was synthesized.' }); }
  }
  try {
    context = await browser.newContext({ ignoreHTTPSErrors: true, viewport: { width: 1366, height: 768 } }); context.setDefaultTimeout(15000);
    await context.exposeBinding('__auditDialogOpen', (_, value) => { dialogs.push({ caseId: currentCase, phase, ...value, observedAt: Date.now() }); });
    await context.addInitScript(() => { const install = () => new MutationObserver(records => { for (const r of records) if (r.target.tagName === 'DIALOG' && r.attributeName === 'open' && r.oldValue === null) window.__auditDialogOpen({ path: location.pathname, type: 'html-dialog-open', nativeTag: 'dialog' }); }).observe(document.documentElement, { attributes: true, attributeOldValue: true, attributeFilter: ['open'], subtree: true }); if (document.documentElement) install(); else addEventListener('DOMContentLoaded', install, { once: true }); });
    context.on('page', p => {
      p.on('pageerror', e => errors.push(String(e.message)));
      p.on('dialog', async d => { if (d.type() === 'beforeunload') await d.accept(); else { dialogs.push({ caseId: currentCase, phase, path: new URL(p.url()).pathname, type: 'unexpected-' + d.type(), observedAt: Date.now() }); await d.dismiss(); } });
      p.on('request', r => requests.push({ caseId: currentCase, phase, method: r.method(), path: new URL(r.url()).pathname, observedAt: Date.now() }));
      p.on('response', r => { const pathname = new URL(r.url()).pathname; if (r.request().method() !== 'POST') return; const entry = { caseId: currentCase, phase, method: 'POST', path: pathname, status: r.status() }; responses.push(entry); if (['/employees/save', '/employees/cancel'].includes(pathname)) pending.push((async () => { try { const x = await r.json(), o = x.outcome || x; entry.outcomeKind = o.kind ?? null; entry.messageId = o.messageId ?? null; entry.commitState = o.commitState ?? x.navigation?.commitState ?? null; } catch { entry.jsonUnavailable = true; } })()); });
    });
    page = await context.newPage(); await page.goto(profile.url + '/account/login'); await type('[data-item-id="F01-I01"]', 'staff'); await type('[data-item-id="F01-I02"]', profile.staffPassword); await navigate('[data-item-id="F01-I04"]', '/menu');
    await scenario('DUI05.ph05-untouched', async () => {
      const entered = { employeeNo: '000002', name: ' 佐藤 ', department: '02', employmentStatus: '02' };
      await type('#f03-i01', entered.employeeNo); await type('#f03-i02', entered.name); await page.locator('#f03-i03').selectOption(entered.department); await page.locator('#f03-i04').selectOption(entered.employmentStatus);
      const beforeRaw = await raw(page), beforeStatus = (await model(page)).resultStatus, beforeCounter = await warmCounter(), start = requests.length, ds = dialogs.length; phase = 'new-cancel-window'; const began = Date.now(); await roundtrip(); await page.evaluate(() => new Promise(r => requestAnimationFrame(r)));
      const afterRaw = await raw(page), after = await model(page), sqlDelta = delta(beforeCounter, counter()), properties = { rawEmployeeNoPreserved: beforeRaw.employeeNo === entered.employeeNo && afterRaw.employeeNo === beforeRaw.employeeNo, rawNamePreserved: beforeRaw.name === entered.name && afterRaw.name === beforeRaw.name, rawDepartmentPreserved: beforeRaw.department === entered.department && afterRaw.department === beforeRaw.department, rawEmploymentPreserved: beforeRaw.employmentStatus === entered.employmentStatus && afterRaw.employmentStatus === beforeRaw.employmentStatus, statusPreserved: after.resultStatus === beforeStatus, saveRequests: count(requests, start, '/employees/save'), confirmationDialogs: dialogs.slice(ds).filter(d => d.phase === 'new-cancel-window').length };
      if (sqlDelta.verified) properties.automaticSearchRequests = sqlDelta.executedSearchQueries;
      await emit(currentCase, properties, { entered, beforeRaw, afterRaw, beforeStatus, afterStatus: after.resultStatus, sqlDelta, httpSearchRequests: count(requests, start, '/employees/search'), windowMs: Date.now() - began });
    });
    await scenario('DUI05.invalid-raw', async () => {
      const m = await model(page), u = m.ui, entered = { employeeNo: '12x', name: '  raw  ', department: ' ZZ ', employmentStatus: '' };
      const injected = await api('/employees/invalidate', { stateId: u.stateId, stateRevision: u.stateRevision, tabId: u.tabId, documentLease: u.documentLease, clientSequence: 1, raw: entered, scrollTop: 0 }); assert.equal(injected.status, 200);
      await page.evaluate(u => history.replaceState({ resumeRef: u.resumeRef, sourceTabId: u.sourceTabId }, '', '/employees'), injected.body.ui); await page.reload(); await ready(); const beforeRaw = await raw(page);
      const beforeCounter = await warmCounter(), start = requests.length; phase = 'untrusted-raw-new-cancel-window'; await roundtrip(); const afterRaw = await raw(page), sqlDelta = delta(beforeCounter, counter());
      const option = await page.locator('#f03-i03').evaluate(n => ({ value: n.value, selectedTemporary: n.selectedOptions[0]?.dataset.invalidRaw === 'true', normalChoicesContainRaw: [...n.options].filter(o => !o.dataset.invalidRaw).some(o => o.value === n.value) }));
      phase = 'explicit-search-validation-outside-counter-window'; assert.equal((await clickResponse('#search-run', '/employees/search')).status(), 422); await type('#f03-i01', ''); const rejected = await clickResponse('#search-run', '/employees/search'), rejectBody = await rejected.json();
      const properties = { partialNumberPreserved: beforeRaw.employeeNo === entered.employeeNo && afterRaw.employeeNo === entered.employeeNo, unknownSelectRawPreserved: beforeRaw.department === entered.department && afterRaw.department === entered.department, rawWhitespacePreserved: beforeRaw.name === entered.name && afterRaw.name === entered.name, unknownOptionExcludedFromNormalChoices: option.selectedTemporary && !option.normalChoicesContainRaw, searchUnknownOptionRejected: rejected.status() === 422 && rejectBody.outcome?.messageId === 'MSG-016' };
      if (sqlDelta.verified) properties.automaticSearchRequests = sqlDelta.executedSearchQueries;
      await emit(currentCase, properties, { precondition: 'Untrusted raw server state injected through the existing guarded endpoint; actual New/Cancel and temporary option rendering follow', entered, beforeRaw, afterRaw, option, sqlDelta, counterWindowHttpSearchRequests: requests.slice(start).filter(r => r.phase === 'untrusted-raw-new-cancel-window' && r.path === '/employees/search').length, explicitRejectStatus: rejected.status(), explicitRejectMessageId: rejectBody.outcome?.messageId });
    });
    await scenario('DUI05.new-save-return', async () => {
      await type('#f03-i01', '12x'); await type('#f03-i02', ' 未適用 '); await page.locator('#f03-i03').selectOption('02'); await page.locator('#f03-i04').selectOption('02'); const beforeRaw = await raw(page), before = await model(page);
      const beforeCounter = await warmCounter(), start = requests.length; phase = 'new-explicit-save-return-window'; await navigate('#employee-new', '/employees/new');
      const used = new Set(rows("SELECT employee_no FROM dbo.m_employee WHERE employee_no BETWEEN '970001' AND '970099'").map(r => r.employee_no)); const number = Array.from({ length: 99 }, (_, i) => String(970001 + i)).find(n => !used.has(n)); assert.ok(number);
      const name = '追加検査 社員'; for (const [s, v] of [['#f04-i01', number], ['#f04-i02', name], ['#f04-i03', 'ツイカケンサシャイン'], ['#f04-i06', '2020-01-01']]) await type(s, v); await page.locator('#f04-i04').selectOption('01');
      await navigate('#employee-save', '/employees'); const afterRaw = await raw(page), after = await model(page), sqlDelta = delta(beforeCounter, counter()), saved = employee(number), notice = await page.locator('#message').innerText();
      const properties = { dbSavedEmployee: saved?.employee_name === name, rawFourValuesPreserved: JSON.stringify(beforeRaw) === JSON.stringify(afterRaw), originStatusPreserved: before.resultStatus === after.resultStatus, savedNoticeVisible: /保存しました/.test(notice) };
      if (sqlDelta.verified) properties.automaticSearchRequests = sqlDelta.executedSearchQueries;
      await emit(currentCase, properties, { employeeNo: number, storedEmployeeName: saved?.employee_name, storedRevision: saved?.revision, beforeRaw, afterRaw, beforeStatus: before.resultStatus, afterStatus: after.resultStatus, sqlDelta, actualSavePosts: count(requests, start, '/employees/save'), httpSearchRequests: count(requests, start, '/employees/search'), notice });
    });
    await scenario('DUI11.tabs', async () => {
      const saved = employee('000001'), careers = rows("SELECT c.* FROM dbo.t_career c JOIN dbo.m_employee e ON e.employee_id=c.employee_id WHERE e.employee_no='000001' ORDER BY c.career_id"), beforeDigest = digest(business());
      await go('/employees/' + saved.employee_id + '/edit'); await type('#f04-i02', 'Audit未保存・別Tab禁止'); await page.locator('#careers-tab').click(); await page.locator('#career-rows button').first().click(); await page.waitForFunction(() => !document.querySelector('#f04-i17').disabled); await type('#f04-i17', 'Audit未反映・別Tab禁止');
      const original = await page.locator('[data-field],[data-career]').evaluateAll(ns => Object.fromEntries(ns.map(n => [n.dataset.itemId, n.value]))), originalState = await model(page), other = await context.newPage();
      try {
        await go('/employees/' + saved.employee_id + '/edit', other); const otherState = await model(other), otherName = await other.locator('#f04-i02').inputValue(); await other.locator('#careers-tab').click(); await other.locator('#career-rows button').first().click(); await other.waitForFunction(() => !document.querySelector('#f04-i17').disabled); const otherProject = await other.locator('#f04-i17').inputValue(), selectedModel = await model(other), selectedCareer = selectedModel.careers.find(c => c.clientRowKey === selectedModel.selectedClientRowKey), savedCareer = careers.find(c => String(c.career_id) === String(selectedCareer?.careerId));
        assert.ok(savedCareer, 'The actually selected career must match a stored row by primary key, not array position');
        const originalAfter = await page.locator('[data-field],[data-career]').evaluateAll(ns => Object.fromEntries(ns.map(n => [n.dataset.itemId, n.value]))), dbAfterDigest = digest(business());
        const draftShared = otherName === original['F04-I02'] || otherProject === original['F04-I17'];
        assert.equal(otherName, saved.employee_name); assert.equal(otherProject, savedCareer.project_name); assert.ok(originalState.editStateId !== otherState.editStateId && originalState.ui.documentLease !== otherState.ui.documentLease);
        await emit(currentCase, { draftSharedAcrossTabs: draftShared }, { sameAuthenticatedContext: page.context() === other.context(), actualOriginalName: original['F04-I02'], actualOriginalProject: original['F04-I17'], otherName, otherProject, selectedCareerId: selectedCareer.careerId, savedEmployeeName: saved.employee_name, savedCareerProject: savedCareer.project_name, independentEditStateAndLease: originalState.editStateId !== otherState.editStateId && originalState.ui.documentLease !== otherState.ui.documentLease, originalDomUnchanged: JSON.stringify(original) === JSON.stringify(originalAfter), businessDbUnchanged: beforeDigest === dbAfterDigest, scope: 'Unsaved EditDraft direct/new-tab isolation only; search-copy original server-state comparison is deliberately not inferred from DOM or attach200.' });
      } finally { await other.close(); }
    });
    await scenario('DUI11.state-expiry', async () => {
      const stored = employee('000001'), dbBefore = digest(business()); await go('/employees/' + stored.employee_id + '/edit'); const m = await model(page), u = m.ui;
      const envelope = { stateId: u.stateId, stateRevision: u.stateRevision, tabId: u.tabId, documentLease: u.documentLease, employee: m.employee, pending: m.pending, code: null, activeTab: m.activeTab, selectedClientRowKey: m.selectedClientRowKey };
      const cancelled = await api('/employees/cancel', { editStateId: u.stateId, stateRevision: u.stateRevision, rawUiEnvelope: envelope, confirmationId: null, choice: null, reloadOnly: false, returnToMenu: false }); assert.equal(cancelled.status, 200); assert.ok(cancelled.body.navigation);
      assert.equal((await context.request.get(profile.url + cancelled.body.navigation.url)).status(), 200); await type('#f04-i02', 'Audit失効後DOM保持'); const rawBefore = await page.locator('[data-field],[data-career]').evaluateAll(ns => Object.fromEntries(ns.map(n => [n.dataset.itemId, n.value]))), targetBefore = await page.locator('[data-ui="employee-identity"]').innerText();
      const start = requests.length, began = Date.now(); phase = 'one-explicit-save-then-explicit-reload-window'; const failure = await clickResponse('#employee-save', '/employees/save'), failureBody = await failure.json(); await page.locator('#message').filter({ hasText: '失効' }).waitFor();
      sql("EXEC sys.sp_rename N'dbo.m_employee',N'm_employee_AUDIT_READFAULT',N'OBJECT';", true); renamed = true;
      try { await page.locator('#employee-reload').click(); await page.locator('dialog[open]').waitFor(); await page.locator('dialog [data-part="discard"]').click(); await page.locator('#message').filter({ hasText: '読み込めません' }).waitFor(); }
      finally { sql("EXEC sys.sp_rename N'dbo.m_employee_AUDIT_READFAULT',N'm_employee',N'OBJECT';", true); renamed = false; }
      await page.waitForTimeout(700); const rawAfter = await page.locator('[data-field],[data-career]').evaluateAll(ns => Object.fromEntries(ns.map(n => [n.dataset.itemId, n.value]))), targetAfter = await page.locator('[data-ui="employee-identity"]').innerText(), saves = count(requests, start, '/employees/save'), actualMessageId = failureBody.outcome?.messageId;
      const cancelPosts = count(requests, start, '/employees/cancel');
      await emit(currentCase, { messageId: actualMessageId, currentRawRetained: JSON.stringify(rawBefore) === JSON.stringify(rawAfter), targetRetained: targetBefore === targetAfter, automaticReposts: saves - 1 + Math.max(0, cancelPosts - 2), canSave: await page.locator('#employee-save').isEnabled(), failedReloadKeepsOldDisplay: JSON.stringify(rawBefore) === JSON.stringify(rawAfter) && targetBefore === targetAfter }, { precondition: 'Existing state cancelled and one-use return consumed outside this live document; valid authentication remains', actualFailureStatus: failure.status(), actualFailureMessageId: actualMessageId, explicitSaveClicks: 1, observedSavePosts: saves, explicitReloadClicks: 1, explicitDiscardChoiceClicks: 1, observedCancelPosts: cancelPosts, counterMeaning: 'Save requests beyond the one explicit click plus Cancel requests beyond the explicit Reload and Discard-choice POSTs', observationWindowMs: Date.now() - began, rawBefore, rawAfter, targetBefore, targetAfter, fault: 'Exact owned DB m_employee temporarily renamed for the read; restored in finally', dbUnchanged: dbBefore === digest(business()) });
    });
  } finally {
    if (renamed) { sql("EXEC sys.sp_rename N'dbo.m_employee_AUDIT_READFAULT',N'm_employee',N'OBJECT';", true); renamed = false; }
    await Promise.allSettled(pending); await browser.close(); assert.equal(hashArtifact(path.join(owner, 'build/publish')).sha256, artifact.sha256); assert.equal(sha(contractFile), process.env.SP2_EXPECTED_UI_SHA); assert.equal(sha(inputFile), inputSha); assert.equal(sha(__filename), source.sha256); assert.equal(sha(path.join(owner, baseline337.file)), baseline337.sha256); assert.equal(sha(path.join(owner, baselineInventory.file)), baselineInventory.sha256);
    const record = { schemaVersion: 1, projectId: 'sample-project2', profileId: 'CSharp_ASPNET', runId: contract.runId, status: 'PARTIAL_ADDITIONAL_INDEPENDENT_INTERACTION_ACTUALS', artifact, contractSha256: sha(contractFile), inputManifestSha256: inputSha, measurementSources: [source], fixture: { database: profile.database, url: profile.url, profileSha256: sha(profileFile), ownership: 'Newly created owned Audit additional fixture only; old Author/Audit/DEMO untouched' }, observations, notMeasured, cases, errors, existing337Unchanged: baseline337, existingInventoryUnchanged: baselineInventory, scope: 'Actual headless Edge UI/HTTP/owned SQL metadata and row reads. SQL zero is recorded only with surviving before/after plan keys. All dialog openings and save/reload HTTP requests are counted, with explicit operation windows. Test-only owned DB read fault is restored; one new employee is explicitly saved in this new Audit fixture. No physicalIME/nativeBFCache/OSclipboard claim. No expected value/op is used as an actual.', formalScore: null };
    fs.writeFileSync(path.join(out, 'partial-observations.json'), JSON.stringify(record, null, 2) + '\n'); console.log(JSON.stringify({ status: record.status, cases: cases.map(c => ({ id: c.id, status: c.status, error: c.error })), observations: observations.length, notMeasured: notMeasured.length, errors }));
  }
}
run().catch(e => { console.error(e.message); process.exitCode = 1; });
