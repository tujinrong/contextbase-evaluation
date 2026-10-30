'use strict';

// Independent actual final-publish collector. No product/source writes and no successful Save.
const fs = require('node:fs'), path = require('node:path'), crypto = require('node:crypto'), assert = require('node:assert/strict');
const { pathToFileURL } = require('node:url');
const { collectFonts } = require('./font-collection.cjs');
const { collectMetrics } = require('./noninteraction-metrics.cjs');
const owner = path.resolve(__dirname, '../..'), repo = path.resolve(owner, '../../..');
const sha = f => crypto.createHash('sha256').update(fs.readFileSync(f)).digest('hex');
const read = f => JSON.parse(fs.readFileSync(f, 'utf8').replace(/^\uFEFF/, ''));
const contractFile = path.join(owner, 'tests/ui-contract.json');
const original = read(contractFile);
assert.equal(sha(contractFile), process.env.SP2_EXPECTED_UI_SHA, 'Explicit frozen contract SHA required');
// Deliberate data boundary: nested expectation objects are discarded before measurements/state preparation.
const descriptors = original.rules.filter(r => r.kind !== 'interaction').map(r => ({ id: r.id, target: r.target, kind: r.kind, propertyNames: Object.keys(r.properties) }));
const components = original.components.map(c => ({ id: c.id, selector: c.selector, state: c.state, kind: c.kind, textCapable: c.textCapable }));
const profile = read(path.join(owner, '.tmp/audit-runtime/profile.json'));
assert.equal(profile.database, 'SP2_WebFixture_AUDIT_R20261029'); assert.equal(profile.url, 'https://localhost:5183');
const out = path.join(owner, 'build/test-results/independent-ui/noninteraction'); fs.mkdirSync(out, { recursive: true });
const sel = id => { const c = components.find(c => c.id === id); if (!c) throw Error('Unknown descriptor ' + id); return c.selector; };
const relative = f => path.relative(owner, f).replaceAll('\\', '/');
const evidence = f => ({ file: relative(f), sha256: sha(f) });
const text = n => Array.from(('監査😀あ\u3099漢字\n').repeat(Math.ceil(n / 7))).slice(0, n).join('');

async function run() {
  const { hashArtifact } = await import(pathToFileURL(path.join(repo, 'agents/builds/build-agent/scripts/ui-conformance.mjs')));
  const artifact = hashArtifact(path.join(owner, 'build/publish')); assert.equal(artifact.sha256, process.env.SP2_EXPECTED_PUBLISH_SHA, 'Explicit immutable publish SHA required');
  const { chromium } = require(process.env.SP2_PLAYWRIGHT_MODULE || 'playwright-core');
  const browser = await chromium.launch({ executablePath: process.env.SP2_EDGE_PATH || 'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe', headless: true });
  const records = [], observations = new Map(), missing = new Map(), errors = [], cases = [], identity = {}, fullValueResults = {}, saveResponses = [], pendingResponseChecks = [];
  const sourceFiles = [__filename, path.join(__dirname, 'noninteraction-metrics.cjs'), path.join(__dirname, 'font-collection.cjs')];
  const measurementSources = sourceFiles.map(f => ({ file: relative(f), sha256: sha(f) }));
  let context, publicContext, page, editPath;
  const item = id => page.locator(sel(id));
  const redact = s => String(s).replaceAll(profile.adminPassword, '[redacted]').replaceAll(profile.staffPassword, '[redacted]');
  async function resize(width) { await page.setViewportSize({ width, height: 768 }); await page.evaluate(() => new Promise(resolve => requestAnimationFrame(() => requestAnimationFrame(resolve)))); }
  async function ready(screen) {
    await page.locator(sel(screen + '.surface')).waitFor();
    await page.waitForFunction(s => { const n = document.querySelector(s); return n && n.dataset.ready === 'true' && !n.inert; }, sel(screen + '.surface'));
  }
  async function navigate(url, screen) { await page.goto(profile.url + url); if (screen) await ready(screen); }
  async function responseClick(id, pathname) {
    const pending = page.waitForResponse(r => new URL(r.url()).pathname === pathname && r.request().method() === 'POST');
    await item(id).click(); const r = await pending; return r.status();
  }
  async function selectedSearch() {
    await navigate('/employees', 'F03');
    assert.equal(await responseClick('F03-I05', '/employees/search'), 200);
    const radio = page.locator(sel('F03-I08')).locator('input[type="radio"]').first(); await radio.waitFor(); await radio.check();
    editPath = await item('F03-I11').first().getAttribute('href'); assert.ok(editPath && editPath.startsWith('/employees/'));
    await item('F03-I05').focus(); await page.keyboard.press('Tab'); await page.keyboard.press('Shift+Tab');
  }
  async function edit(career = false) {
    await navigate(editPath, 'F04');
    identity.basic = await page.locator('.target[data-ui="employee-identity"]').innerText();
    if (career) { await page.locator('[role="tab"][data-tab="career"]').click(); await page.locator('#career-rows button').first().click(); await item('F04-I14').waitFor({ state: 'visible' }); identity.career = await page.locator('.target[data-ui="employee-identity"]').innerText(); }
  }
  async function codes() {
    await navigate('/codes', 'F06'); await page.locator('#code-rows button').first().click(); await item('F06-I04').waitFor({ state: 'visible' });
    await page.waitForFunction(s => !document.querySelector(s).disabled, sel('F06-I04'));
  }
  async function fullValue(id, scalars) {
    const node = item(id), sample = text(scalars); await node.fill(sample); await node.focus(); await page.keyboard.press('Control+End');
    // Ctrl+End makes the end caret visible but can leave bottom padding unscrolled; an actual wheel operation checks full scrollbar reach separately.
    await node.hover(); await page.mouse.wheel(0, 100000); await page.evaluate(() => new Promise(resolve => requestAnimationFrame(() => requestAnimationFrame(resolve))));
    fullValueResults[id] = await node.evaluate((n, sample) => ({ reachable: n.value === sample && n.selectionEnd === n.value.length && n.scrollTop + n.clientHeight >= n.scrollHeight - 2, retainedExactSample: n.value === sample, scalarLength: Array.from(n.value).length, utf16Length: n.value.length, selectionEnd: n.selectionEnd, scrollTop: n.scrollTop, scrollHeight: n.scrollHeight, clientHeight: n.clientHeight }), sample);
  }
  async function prepare(state) {
    await resize(1366);
    if (state === 'login') { await navigate('/account/login'); await item('F01-I01').waitFor(); await Promise.all([page.waitForLoadState('domcontentloaded'), item('F01-I04').click()]); await item('F01-I03').waitFor(); return; }
    if (state === 'menu-admin' || state === 'menu-admin-narrow') { await navigate('/menu', 'F02'); }
    else if (state === 'search-selected' || state === 'search-selected-narrow' || state === 'export-generating' || state === 'search-validation') {
      await selectedSearch();
      if (state === 'search-validation') { await item('F03-I01').fill('1'); assert.equal(await responseClick('F03-I05', '/employees/search'), 422); await page.locator('[data-ui="error-summary"]').waitFor(); }
    } else if (state.startsWith('edit-') || state.startsWith('employee-')) {
      await edit(state === 'edit-career' || state === 'employee-pending-confirmation');
      if (state === 'edit-basic') for (const id of ['F04-I07', 'F04-I08', 'F04-I09', 'F04-I10']) await fullValue(id, 1000);
      if (state === 'edit-career') for (const [id, length] of [['F04-I18', 1000], ['F04-I19', 1000], ['F04-I20', 1000], ['F04-I21', 500], ['F04-I22', 200]]) await fullValue(id, length);
      if (state === 'employee-validation') { await item('F04-I02').fill(''); assert.equal(await responseClick('F04-I28', '/employees/save'), 422); await page.locator('[data-ui="error-summary"]').waitFor(); }
      if (state === 'employee-discard') { await item('F04-I02').fill('独立監査・取消用'); await item('F04-I29').click(); await page.locator('dialog[open]').waitFor(); }
      if (state === 'employee-pending-confirmation') { await item('F04-I17').fill('独立監査・未反映'); await item('F04-I25').click(); await page.locator('dialog[open]').waitFor(); }
    } else if (state.startsWith('code') || state === 'codes-selected-narrow') {
      await codes();
      if (state === 'code-validation') { await item('F06-I04').fill(''); assert.equal(await responseClick('F06-I09', '/codes/save'), 422); await page.locator('[data-ui="error-summary"]').waitFor(); }
      if (state === 'code-discard') { await item('F06-I04').fill('独立監査・取消用'); await item('F06-I10').click(); await page.locator('dialog[open]').waitFor(); }
      if (state === 'code-stop-confirmation') { await item('F06-I06').uncheck(); await item('F06-I09').click(); await page.locator('dialog[open]').waitFor(); }
    } else if (state === 'get-error') { const response = await page.goto(profile.url + '/employees/9223372036854775807/edit'); assert.equal(response.status(), 404); await page.locator('[data-ui-error]').waitFor(); }
    else throw Error('No state preparation ' + state);
    if (state.endsWith('-narrow')) { await resize(390); const summary = page.locator('.nav summary'); await summary.waitFor(); if (!(await page.locator('.nav details').evaluate(n => n.open))) { await summary.click(); await page.waitForFunction(() => document.querySelector('.nav details').open); } }
    await page.evaluate(() => window.scrollTo(0, 0));
  }
  async function capture(state, variant = null) {
    const activeRules = descriptors.filter(r => components.find(c => c.id === r.target)?.state === state && !r.id.startsWith('NARROW.'));
    const fonts = await collectFonts(page, { stateId: state, ruleDescriptors: activeRules.filter(r => r.kind === 'font'), componentDescriptors: components });
    const metrics = await collectMetrics(page, { stateId: state, ruleDescriptors: activeRules.filter(r => r.kind !== 'font'), componentDescriptors: components, preparation: { fullValueResults, sameIdentityAcrossTabs: identity.basic && identity.career ? identity.basic === identity.career : null } });
    const fileStem = state + (variant ? '-' + variant : '');
    const screenshotFile = path.join(out, fileStem + '.png'); await page.screenshot({ path: screenshotFile, fullPage: true });
    const rawFile = path.join(out, fileStem + '.json');
    const env = await page.evaluate(() => ({ userAgent: navigator.userAgent, platform: navigator.platform, devicePixelRatio, viewport: { width: innerWidth, height: innerHeight }, rootFontSize: getComputedStyle(document.documentElement).fontSize, visualViewportScale: window.visualViewport?.scale ?? null }));
    fs.writeFileSync(rawFile, JSON.stringify({ state, variant, environment: env, preparation: { fullValueResults, sameIdentityAcrossTabs: identity.basic && identity.career ? identity.basic === identity.career : null }, fonts, metrics }, null, 2) + '\n');
    const proof = [evidence(rawFile), evidence(screenshotFile)];
    for (const o of [...fonts.observations, ...metrics.observations]) { if (!observations.has(o.ruleId)) observations.set(o.ruleId, { ruleId: o.ruleId, target: o.target, method: o.method, properties: o.properties, evidence: proof }); missing.delete(o.ruleId); }
    for (const n of [...fonts.notMeasured, ...metrics.notMeasured]) if (!observations.has(n.ruleId)) missing.set(n.ruleId, { ...n, evidence: proof });
    records.push({ state, variant, activeRuleCount: activeRules.length, collected: fonts.observations.length + metrics.observations.length, notMeasured: fonts.notMeasured.length + metrics.notMeasured.length, evidence: proof });
  }
  async function reachability() {
    const results = [];
    const targets = page.locator('main button,main a,main input:not([type="hidden"]),main select,main textarea,.usertools button,.nav a');
    for (let i = 0; i < await targets.count(); i++) {
      const n = targets.nth(i); if (!(await n.isVisible())) continue;
      const base = await n.evaluate(n => ({ tag: n.tagName, id: n.id || null, item: n.dataset.itemId || null, disabled: !!n.disabled, tabIndex: n.tabIndex }));
      if (base.disabled) { results.push({ ...base, excluded: 'Disabled in actual selected state' }); continue; }
      await n.scrollIntoViewIfNeeded(); await n.focus();
      results.push(await n.evaluate((n, base) => { const r = n.getBoundingClientRect(), x = Math.min(innerWidth - 1, Math.max(0, r.x + r.width / 2)), y = Math.min(innerHeight - 1, Math.max(0, r.y + r.height / 2)), hit = document.elementFromPoint(x, y); return { ...base, focused: document.activeElement === n, centerWithinViewport: r.x + r.width / 2 >= 0 && r.x + r.width / 2 < innerWidth && r.y + r.height / 2 >= 0 && r.y + r.height / 2 < innerHeight, centerHit: !!hit && (n === hit || n.contains(hit)), rect: { x: r.x, y: r.y, width: r.width, height: r.height } }; }, base));
    }
    return results;
  }
  async function narrow(screen, normalState) {
    const samples = [];
    for (const dimension of [1366, 1280, 768, 390, 320, 'text200at1366']) {
      await prepare(normalState); await resize(typeof dimension === 'number' ? dimension : 1366);
      const textScale = dimension === 'text200at1366' ? await page.evaluate(() => { const n = document.documentElement, before = parseFloat(getComputedStyle(n).fontSize); n.style.fontSize = (before * 2) + 'px'; return { method: 'CSS root-font enlargement; not browser page zoom/physical DPI', beforePx: before, afterPx: parseFloat(getComputedStyle(n).fontSize) }; }) : null;
      let disclosure = { applicable: false }, nav = [];
      const summary = page.locator('.nav summary');
      if (await summary.count() && await summary.isVisible()) { const details = page.locator('.nav details'); const before = await details.evaluate(n => n.open); await summary.focus(); await page.keyboard.press('Enter'); await page.waitForFunction(before => document.querySelector('.nav details').open !== before, before); const changed = await details.evaluate(n => n.open); if (!changed) { await summary.focus(); await page.keyboard.press('Enter'); await page.waitForFunction(() => document.querySelector('.nav details').open); } disclosure = { applicable: true, before, afterFirstEnter: changed, finalOpen: await details.evaluate(n => n.open), keyboardToggled: before !== changed }; }
      const actions = await reachability();
      const geometry = await page.evaluate(() => ({ width: innerWidth, height: innerHeight, clientWidth: document.documentElement.clientWidth, scrollWidth: document.documentElement.scrollWidth, overflow: Math.max(0, document.documentElement.scrollWidth - document.documentElement.clientWidth), protectedNavCount: document.querySelectorAll('.nav a').length }));
      nav = actions.filter(a => a.tag === 'A' && !a.excluded);
      const screenshotFile = path.join(out, screen + '-' + dimension + '.png'); await page.screenshot({ path: screenshotFile, fullPage: true });
      samples.push({ id: typeof dimension === 'number' ? dimension + 'x768' : dimension, geometry, textScale, disclosure, actions, actualEnabledCount: actions.filter(a => !a.excluded).length, reachable: actions.filter(a => !a.excluded).every(a => a.focused && a.centerWithinViewport && a.centerHit), navReachable: nav.length > 0 && nav.every(a => a.focused && a.centerWithinViewport && a.centerHit), evidence: [evidence(screenshotFile)] });
    }
    const rule = descriptors.find(r => r.id === 'NARROW.' + screen), properties = {};
    for (const p of rule.propertyNames) {
      const m = /^overflowAt(1366|1280|768|390|320)Px$/.exec(p);
      if (m) properties[p] = samples.find(s => s.id === m[1] + 'x768').geometry.overflow;
      else if (p === 'overflowAtText200Percent') properties[p] = samples.find(s => s.id === 'text200at1366').geometry.overflow;
      else if (p === 'requiredCaseCoverage') properties[p] = samples.map(s => s.id).join('|');
      else if (p === 'majorActionsReachable') properties[p] = samples.every(s => s.actualEnabledCount > 0 && s.reachable);
      else if (p === 'navDisclosureOperable') properties[p] = samples.filter(s => s.disclosure.applicable).length > 0 && samples.filter(s => s.disclosure.applicable).every(s => s.disclosure.keyboardToggled && s.disclosure.finalOpen);
      else if (p === 'navReachableAtEveryRequiredViewport') properties[p] = samples.every(s => s.navReachable);
      else if (p === 'publicPageHasNoProtectedNav') properties[p] = samples.every(s => s.geometry.protectedNavCount === 0);
      else throw Error('Unsupported narrow property ' + p);
    }
    const rawFile = path.join(out, screen + '-viewport-matrix.json'); fs.writeFileSync(rawFile, JSON.stringify({ screen, samples }, null, 2) + '\n');
    observations.set(rule.id, { ruleId: rule.id, target: rule.target, method: 'layout-measurement', properties, evidence: [evidence(rawFile), ...samples.flatMap(s => s.evidence)] });
    cases.push({ screen, samples: samples.map(s => ({ id: s.id, overflow: s.geometry.overflow, reachable: s.reachable, navReachable: s.navReachable })), evidence: [evidence(rawFile)] });
  }
  try {
    publicContext = await browser.newContext({ ignoreHTTPSErrors: true, viewport: { width: 1366, height: 768 } });
    context = await browser.newContext({ ignoreHTTPSErrors: true, viewport: { width: 1366, height: 768 } });
    // Explicit fixture cleanup between independent states; these browser beforeunload accepts are not app Cancel evidence.
    for (const c of [publicContext, context]) { c.setDefaultTimeout(10000); c.on('page', p => {
      p.on('dialog', async d => { if (d.type() === 'beforeunload') await d.accept(); else { errors.push('Unexpected browser dialog dismissed: ' + d.type()); await d.dismiss(); } });
      p.on('response', r => { const pathname = new URL(r.url()).pathname; if (r.request().method() !== 'POST' || !['/employees/save', '/codes/save'].includes(pathname)) return;
        pendingResponseChecks.push((async () => { const record = { path: pathname, status: r.status() }; try { const body = await r.json(); const outcome = body.outcome || body; record.outcomeKind = outcome.kind ?? null; record.commitState = outcome.commitState ?? null; record.confirmationPresent = !!body.confirmation; if (record.outcomeKind === 'Success' && record.commitState === 'Committed') errors.push('Unexpected committed Save in noninteraction collector'); } catch { record.outcomeUnparsed = true; } saveResponses.push(record); })());
      });
    }); }
    page = await publicContext.newPage(); page.on('pageerror', e => errors.push(redact(e.message))); await prepare('login'); await capture('login'); await narrow('F01', 'login');
    await page.close(); page = await context.newPage(); page.on('pageerror', e => errors.push(redact(e.message)));
    await navigate('/account/login'); await item('F01-I01').fill('admin'); await item('F01-I02').fill(profile.adminPassword); await Promise.all([page.waitForURL(u => u.pathname === '/menu'), item('F01-I04').click()]);
    await selectedSearch();
    for (const state of [...new Set(components.map(c => c.state))].filter(s => s !== 'login')) {
      try {
        await prepare(state);
        if (state === 'export-generating') {
          // Delay outbound export request only to sample the existing waiting UI. No claim about server generation/Cancel semantics.
          let release, arrived, completed; const gate = new Promise(r => release = r), reached = new Promise(r => arrived = r), handled = new Promise(r => completed = r);
          await page.route('**/employees/export', async route => { try { arrived(); await gate; await route.abort('aborted'); } finally { completed(); } });
          try { await item('F03-I12').click(); await reached; await page.locator('#export-cancel').waitFor(); await capture(state); }
          finally { release(); await handled; await page.unroute('**/employees/export'); }
        } else {
          await capture(state);
          // The same real notice control is sampled in an actual visible error variant; no claim that the normal empty notice was visible.
          if (state === 'menu-admin') { await navigate('/menu?denied=1', 'F02'); await capture(state, 'visible-notice'); }
          if (state === 'search-selected') { await item('F03-I01').fill('12x'); assert.equal(await responseClick('F03-I05', '/employees/search'), 422); await item('F03-I09').waitFor(); await capture(state, 'visible-notice'); }
          if (state === 'edit-basic') { await item('F04-I02').fill(''); assert.equal(await responseClick('F04-I28', '/employees/save'), 422); await item('F04-I11').waitFor(); await capture(state, 'visible-notice'); }
          if (state === 'codes-selected') { await item('F06-I04').fill(''); assert.equal(await responseClick('F06-I09', '/codes/save'), 422); await item('F06-I12').waitFor(); await capture(state, 'visible-notice'); }
        }
        await page.close(); page = await context.newPage(); page.on('pageerror', e => errors.push(redact(e.message)));
      } catch (e) {
        const reason = redact(e.message); records.push({ state, preparationFailed: reason });
        for (const r of descriptors.filter(r => components.find(c => c.id === r.target)?.state === state)) if (!observations.has(r.id)) missing.set(r.id, { ruleId: r.id, target: r.target, stateId: state, reason: 'STATE_PREPARATION: ' + reason });
        await page.close(); page = await context.newPage();
      }
    }
    for (const [screen, state] of [['F02', 'menu-admin'], ['F03', 'search-selected'], ['F04', 'edit-basic'], ['F06', 'codes-selected']]) {
      try { await narrow(screen, state); }
      catch (e) { const rule = descriptors.find(r => r.id === 'NARROW.' + screen); missing.set(rule.id, { ruleId: rule.id, target: rule.target, reason: 'VIEWPORT_PREPARATION: ' + redact(e.message) }); }
    }
  } finally {
    await Promise.allSettled(pendingResponseChecks);
    await browser.close(); assert.equal(hashArtifact(path.join(owner, 'build/publish')).sha256, artifact.sha256, 'Publish changed during measurement');
    assert.equal(sha(contractFile), process.env.SP2_EXPECTED_UI_SHA, 'Contract changed during measurement');
    for (const source of measurementSources) assert.equal(sha(path.join(owner, source.file)), source.sha256, 'Measurement source changed during collection: ' + source.file);
    for (const r of descriptors) if (!observations.has(r.id) && !missing.has(r.id)) missing.set(r.id, { ruleId: r.id, target: r.target, reason: 'No actual prepared state observation' });
    const record = { schemaVersion: 1, profileId: 'CSharp_ASPNET', runId: original.runId, status: 'PARTIAL_ACTUAL_NONINTERACTION_COLLECTION', artifact, contractSha256: sha(contractFile), inputManifestSha256: sha(path.join(owner, 'build/generation/inputs.json')), scope: 'Actual headless Edge DOM/CSS and browser-key operations on dedicated Audit fixture. Properties are measurements, not conformance verdicts. Save POSTs target validation rejection/confirmation only; actual status/outcome is recorded below. No physical IME/Windows UI/BFCache/Excel proof. Delayed export samples outbound waiting state only. Text200 uses measured root-font enlargement, not browser page zoom. Browser beforeunload is accepted only as explicit independent-state cleanup, not an app Cancel observation.', measurementSources, saveResponses, intendedRuleIds: descriptors.map(r => r.id), observations: [...observations.values()], notMeasured: [...missing.values()].filter(n => !observations.has(n.ruleId)), states: records, viewportCases: cases, errors, formalScore: null };
    fs.writeFileSync(path.join(out, 'partial-observations.json'), JSON.stringify(record, null, 2) + '\n');
    console.log(JSON.stringify({ status: record.status, intended: descriptors.length, measured: record.observations.length, notMeasured: record.notMeasured.length, errors: errors.length, states: records.map(s => ({ state: s.state, collected: s.collected, notMeasured: s.notMeasured, preparationFailed: s.preparationFailed })) }));
  }
}
if (require.main === module) run().catch(e => { console.error(e.message); process.exitCode = 1; });
module.exports = { run };
