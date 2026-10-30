'use strict';

// Supplement only: never modifies the frozen337 observations or their three measurement sources.
const fs = require('node:fs'), path = require('node:path'), crypto = require('node:crypto'), assert = require('node:assert/strict');
const { pathToFileURL } = require('node:url');
const owner = path.resolve(__dirname, '../..'), repo = path.resolve(owner, '../../..');
const sha = f => crypto.createHash('sha256').update(fs.readFileSync(f)).digest('hex');
const read = f => JSON.parse(fs.readFileSync(f, 'utf8').replace(/^\uFEFF/, ''));
const rel = f => path.relative(owner, f).replaceAll('\\', '/');
const proof = f => ({ file: rel(f), sha256: sha(f) });
const contractFile = path.join(owner, 'tests/ui-contract.json'), contract = read(contractFile);
assert.equal(sha(contractFile), process.env.SP2_EXPECTED_UI_SHA, 'Explicit contract SHA is required');
// Kind, textCapable and all expected properties/operators are deliberately NOT measurement inputs.
const descriptors = contract.components.map(c => ({ id: c.id, selector: c.selector, state: c.state }));
const profile = read(path.join(owner, '.tmp/audit-runtime/profile.json'));
assert.equal(profile.database, 'SP2_WebFixture_AUDIT_R20261029'); assert.equal(profile.url, 'https://localhost:5183');
const frozenFiles = ['tests/independent/noninteraction-observations.cjs', 'tests/independent/noninteraction-metrics.cjs', 'tests/independent/font-collection.cjs', 'build/test-results/independent-ui/noninteraction/partial-observations.json'];
const frozen = frozenFiles.map(file => ({ file, sha256: sha(path.join(owner, file)) }));
const source = proof(__filename), out = path.join(owner, 'build/test-results/independent-ui/component-inventory');
fs.mkdirSync(out, { recursive: true });
const selector = id => descriptors.find(c => c.id === id).selector;

async function collectInventory(page, stateId) {
  return page.evaluate(({ descriptors, stateId }) => {
    const visible = n => {
      if (!n || !n.isConnected || !n.getClientRects().length) return false;
      const r = n.getBoundingClientRect(); if (!(r.width > 0 && r.height > 0)) return false;
      for (let p = n; p; p = p.parentElement) { const s = getComputedStyle(p); if (p.hidden || s.display === 'none' || ['hidden', 'collapse'].includes(s.visibility) || Number(s.opacity) === 0) return false; }
      return true;
    };
    const selected = new Map();
    for (const c of descriptors) { try { selected.set(c.id, [...document.querySelectorAll(c.selector)]); } catch { selected.set(c.id, []); } }
    const active = descriptors.filter(c => c.state === stateId);
    const directIds = n => descriptors.filter(c => selected.get(c.id).includes(n)).map(c => c.id);
    const tuple = n => { const s = getComputedStyle(n); const parsed = /^([0-9.]+)(px)$/.exec(s.fontSize); return { fontFamily: s.fontFamily, fontSize: parsed ? Number(parsed[1]) : null, fontUnit: parsed ? parsed[2] : null }; };
    const native = n => ({ nativeTag: n.tagName.toLowerCase(), role: n.getAttribute('role'), inputType: n.tagName === 'INPUT' ? n.type : null, id: n.id || null, itemId: n.dataset.itemId || null, ui: n.dataset.ui || null, part: n.dataset.part || null, classNames: [...n.classList], visible: visible(n), directTextPresent: [...n.childNodes].some(x => x.nodeType === Node.TEXT_NODE && x.textContent.trim()), childTextPresent: [...n.querySelectorAll('*')].some(x => [...x.childNodes].some(t => t.nodeType === Node.TEXT_NODE && t.textContent.trim())), childElementCount: n.children.length, descendantElementCount: n.querySelectorAll('*').length, fontTuple: tuple(n) });
    const same = (a, b) => JSON.stringify(a) === JSON.stringify(b);
    function deriveKind(nodes) {
      if (!nodes.length) throw Error('No visible actual node');
      const every = p => nodes.every(p), n = nodes[0];
      if (every(n => n.classList.contains('sp2-ui'))) return 'Surface';
      if (every(n => n.getAttribute('role') === 'tablist')) return 'TabList';
      if (every(n => n.getAttribute('role') === 'tab')) return 'TabButton';
      if (every(n => n.getAttribute('role') === 'tabpanel')) return 'TabPage';
      if (every(n => n.tagName === 'DIALOG')) return 'Dialog';
      if (every(n => n.tagName === 'SUMMARY')) return 'Disclosure';
      if (every(n => n.tagName === 'INPUT' && n.type === 'checkbox')) return 'CheckBox';
      if (every(n => n.tagName === 'INPUT' && n.type !== 'checkbox' && n.type !== 'radio' || n.tagName === 'SELECT' || n.tagName === 'TEXTAREA')) return 'Field';
      if (every(n => n.tagName === 'LABEL')) return 'Label';
      if (every(n => n.classList.contains('brand'))) return 'Brand';
      if (every(n => n.classList.contains('crumb'))) return 'Breadcrumb';
      if (every(n => n.dataset.ui === 'employee-identity')) return 'EmployeeIdentity';
      if (every(n => n.dataset.ui === 'user' && !n.dataset.itemId)) return 'UserIdentity';
      if (every(n => n.dataset.ui === 'error-summary')) return 'ErrorSummary';
      if (every(n => n.dataset.ui === 'field-error')) return 'FieldErrors';
      if (every(n => n.tagName === 'P' && !!n.dataset.itemId)) return 'Label'; // Explicit business-item note, distinct from the grouped help collection.
      if (every(n => n.classList.contains('help') || n.classList.contains('nav-label'))) return 'HelpText';
      if (every(n => n.tagName === 'H1' || n.tagName === 'H2' && n.dataset.part === 'title')) return 'Heading';
      if (every(n => n.tagName === 'H2')) return 'GroupHeadings';
      if (every(n => n.tagName === 'TH')) return 'ColumnHeader';
      if (every(n => n.tagName === 'TD')) return 'TableCells';
      if (every(n => n.tagName === 'TABLE' || n.querySelector('table') && n.dataset.itemId)) return 'Table';
      if (every(n => n.tagName === 'UL' && n.id === 'career-rows')) return 'List';
      if (every(n => n.tagName === 'BUTTON')) return nodes.length > 1 && every(n => n.parentElement === nodes[0].parentElement && n.closest('dialog .actions')) ? 'Buttons' : 'Button';
      if (every(n => n.tagName === 'A')) {
        if (every(n => n.classList.contains('skip-link'))) return 'SkipLink';
        return nodes.length > 1 && every(n => n.parentElement === nodes[0].parentElement && n.closest('[data-ui-error] .actions')) ? 'Links' : 'Link';
      }
      if (every(n => n.dataset.part === 'message' || n.dataset.ui === 'error-message' || n.tagName === 'P' && n.closest('[data-ui-error]'))) return 'Message';
      if (every(n => n.dataset.itemId && ['SPAN', 'DIV'].includes(n.tagName) && (n.getAttribute('role') === 'status' || n.dataset.ui === 'user' || n.tagName === 'SPAN'))) return 'Label';
      if (nodes.length > 1 && every(n => n.classList.contains('crumb') || n.classList.contains('usertools') || n.closest('.usertools') || n.closest('.nav') || n.classList.contains('skip-link'))) return 'ShellText';
      throw Error('No limited native/role/semantic kind mapping for actual collection');
    }
    const components = [], notMeasured = [];
    for (const c of active) {
      const matched = selected.get(c.id), nodes = matched.filter(visible), members = matched.map(native);
      try {
        const kind = deriveKind(nodes);
        const textCapable = !['CheckBox', 'TabList'].includes(kind);
        if (['Surface', 'Table', 'List', 'TabPage', 'Dialog'].includes(kind) && !members.some(m => m.visible && (m.directTextPresent || m.childTextPresent))) throw Error('Container has no actually retained text child');
        components.push({ id: c.id, kind, textCapable, preparedState: stateId, selector: c.selector, matchedCount: matched.length, visibleCount: nodes.length, members, mappingBasis: 'Limited native tag/role/data attributes and actual child structure; expected kind/textCapable not supplied' });
      } catch (e) { notMeasured.push({ id: c.id, preparedState: stateId, selector: c.selector, reason: e.message, members }); }
    }
    const childOwnership = [], unresolved = [];
    for (const n of document.querySelectorAll('*')) {
      if (!visible(n) || ['SCRIPT', 'STYLE', 'TEMPLATE', 'NOSCRIPT', 'OPTION', 'OPTGROUP'].includes(n.tagName)) continue;
      const input = n.tagName === 'INPUT', glyph = input && ['checkbox', 'radio'].includes(n.type);
      const directText = [...n.childNodes].some(x => x.nodeType === Node.TEXT_NODE && x.textContent.trim());
      if (!(directText || ['BUTTON', 'SELECT', 'TEXTAREA', 'A'].includes(n.tagName) || input && n.type !== 'hidden')) continue;
      const direct = directIds(n), activeIds = active.filter(c => direct.includes(c.id)).map(c => c.id);
      if (direct.length) { childOwnership.push({ node: native(n), category: 'DIRECT_CURRENT_DOM_MATCH', directComponentIds: direct, activeComponentIds: activeIds, grantsOtherStateCoverage: false }); continue; }
      let ownerElement = null, mapping = null;
      if (n.matches('.sp2-ui[data-screen-id="F02"] main .panel > p:not(.help)')) { ownerElement = n.closest('.sp2-ui[data-screen-id="F02"]'); mapping = 'MENU_BODY_PARAGRAPH_TO_MENU_SURFACE'; }
      else if (n.matches('.crumb span')) { ownerElement = n.closest('.crumb'); mapping = 'BREADCRUMB_INLINE_TEXT_TO_BREADCRUMB'; }
      else if (n.matches('label .required')) { ownerElement = n.closest('label'); mapping = 'REQUIRED_MARK_TO_OWN_LABEL'; }
      else if (n.matches('[data-ui="employee-identity"] strong,[data-ui="employee-identity"] span')) { ownerElement = n.closest('[data-ui="employee-identity"]'); mapping = 'PARENT_IDENTITY_TEXT_TO_IDENTITY'; }
      else if (n.matches('#career-rows button,#career-rows button span')) { ownerElement = n.closest('#career-rows'); mapping = 'CAREER_ROW_BUTTON_PERIOD_TO_CAREER_LIST'; }
      else if (n.matches('#code-rows button')) { ownerElement = n.closest('[data-item-id="F06-I02"]'); mapping = 'CODE_ROW_BUTTON_TO_CODE_TABLE'; }
      else if (n.matches('[data-ui="error-summary"] strong,[data-ui="error-summary"] li,[data-ui="error-summary"] li a')) { ownerElement = n.closest('[data-ui="error-summary"]'); mapping = 'ERROR_SUMMARY_CHILD_TEXT_TO_SUMMARY'; }
      else if (glyph) { ownerElement = n.closest('[data-item-id="F03-I08"],[data-item-id="F06-I02"]'); mapping = 'NATIVE_NON_TEXT_SELECTION_GLYPH_TO_TABLE'; }
      const ownerIds = ownerElement ? directIds(ownerElement) : [];
      const childTuple = tuple(n), ownerTuple = ownerElement ? tuple(ownerElement) : null;
      const contained = !!ownerElement && ownerElement !== n && ownerElement.contains(n);
      const fontsMatch = !!ownerTuple && same(childTuple, ownerTuple);
      const entry = { node: native(n), mapping, ownerComponentIds: ownerIds, owner: ownerElement ? native(ownerElement) : null, containmentObserved: contained, childFontTuple: childTuple, ownerFontTuple: ownerTuple, tupleEqual: fontsMatch, textCapable: !glyph, grantsOtherStateCoverage: false };
      if (!mapping || !contained || !ownerIds.length || !glyph && !fontsMatch) unresolved.push({ ...entry, reason: !mapping ? 'NO_EXPLICIT_LOGICAL_OWNER' : !contained ? 'NO_ACTUAL_CONTAINMENT' : !ownerIds.length ? 'OWNER_HAS_NO_DECLARED_SELECTOR_MATCH' : 'CHILD_OWNER_FONT_TUPLE_DIFF' });
      else childOwnership.push(entry);
    }
    // Actual CSS media-query resolution. No devicePixelRatio*96 or assumed physical DPI.
    const probes = [], matches = value => { const query = '(min-resolution: ' + value + 'dpi)', result = matchMedia(query).matches; probes.push({ query, matches: result }); return result; };
    let low = 0, high = 16384, measured = null;
    if (matches(1) && !matches(high)) {
      low = 1; for (let i = 0; i < 42; i++) { const mid = (low + high) / 2; if (matches(mid)) low = mid; else high = mid; }
      // CSS query comparisons can have implementation tolerances. Derive rounded candidates from the measured transition,
      // then accept a point only if the browser itself confirms its exact-resolution query.
      const candidateQueries = []; let verified = null;
      for (let digits = 6; digits >= 0; digits--) { const candidate = Number(((low + high) / 2).toFixed(digits)), query = '(resolution: ' + candidate + 'dpi)', matches = matchMedia(query).matches; candidateQueries.push({ derivedDecimalPlaces: digits, valueDpi: candidate, query, matches }); if (matches) { verified = { candidate, query }; break; } }
      measured = { reportedCssResolutionDpi: verified?.candidate ?? null, minQueryTransitionLowerTrueDpi: low, minQueryTransitionUpperFalseDpi: high, transitionProbeIntervalDpi: high - low, candidateQueries, exactQuery: verified?.query ?? null, exactQueryMatches: !!verified, method: 'Actual min-resolution binary-search transition, rounded derived candidates, exact-resolution query verification', comparisonToleranceNote: 'The min-query transition can differ slightly from an exact-query point because of browser numeric comparison tolerance. Probe interval is not physical-monitor measurement precision.', physicalMonitorDpiGuaranteed: false };
    }
    const environment = { renderer: 'BROWSER', dpi: measured?.exactQueryMatches ? measured.reportedCssResolutionDpi : null, dpiMeaning: 'Browser-reported CSS resolution from actual media queries; not physical monitor DPI', dpiReason: measured?.exactQueryMatches ? null : 'No exact observed CSS resolution point; inspect measured bracket', scale: devicePixelRatio, scaleMeaning: 'Actual window.devicePixelRatio, reported device pixels per CSS pixel; physical OS display setting is unmeasured', cssResolution: measured, resolutionProbes: probes, devicePixelRatio, visualViewportScale: visualViewport?.scale ?? null, rootFontSize: getComputedStyle(document.documentElement).fontSize, viewport: { width: innerWidth, height: innerHeight, unit: 'px' }, viewportMeaning: 'CSS pixels', userAgent: navigator.userAgent, platform: navigator.platform, physicalMonitorDpi: null, physicalMonitorDpiReason: 'Headless browser CSS resolution is observable; physical monitor DPI is not measured' };
    return { stateId, components, notMeasured, childOwnership, unresolved, environment };
  }, { descriptors, stateId });
}

async function run() {
  const { hashArtifact } = await import(pathToFileURL(path.join(repo, 'agents/builds/build-agent/scripts/ui-conformance.mjs')));
  const artifact = hashArtifact(path.join(owner, 'build/publish')); assert.equal(artifact.sha256, process.env.SP2_EXPECTED_PUBLISH_SHA);
  const { chromium } = require(process.env.SP2_PLAYWRIGHT_MODULE || 'playwright-core');
  const browser = await chromium.launch({ executablePath: 'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe', headless: true });
  const states = [], observed = new Map(), errors = [], saveResponses = [], pending = [];
  let page, context, publicContext, editPath;
  const item = id => page.locator(selector(id));
  async function resize(width) { await page.setViewportSize({ width, height: 768 }); await page.evaluate(() => new Promise(r => requestAnimationFrame(() => requestAnimationFrame(r)))); }
  async function ready(screen) { await page.waitForFunction(s => { const n = document.querySelector(s); return n && n.dataset.ready === 'true' && !n.inert; }, selector(screen + '.surface')); }
  async function go(url, screen) { await page.goto(profile.url + url); if (screen) await ready(screen); }
  async function clickResponse(id, pathname) { const next = page.waitForResponse(r => new URL(r.url()).pathname === pathname && r.request().method() === 'POST'); await item(id).click(); return (await next).status(); }
  async function search() {
    await go('/employees', 'F03'); assert.equal(await clickResponse('F03-I05', '/employees/search'), 200);
    const next = page.waitForResponse(r => new URL(r.url()).pathname === '/employees/select' && r.request().method() === 'POST'); await page.locator('[data-item-id="F03-I08"] input[type="radio"]').first().check(); assert.equal((await next).status(), 200);
    editPath = await item('F03-I11').first().getAttribute('href'); assert.ok(editPath?.startsWith('/employees/'));
  }
  async function edit(career = false) { await go(editPath, 'F04'); if (career) { await page.locator('[role="tab"][data-tab="career"]').click(); await page.locator('#career-rows button').first().click(); await page.waitForFunction(() => !document.querySelector('[data-item-id="F04-I14"]').disabled); } }
  async function codes() { await go('/codes', 'F06'); await page.locator('#code-rows button').first().click(); await page.waitForFunction(() => !document.querySelector('[data-item-id="F06-I04"]').disabled); }
  async function prepare(state) {
    await resize(1366);
    if (state === 'login') { await go('/account/login'); await item('F01-I04').click(); await item('F01-I03').waitFor(); return; }
    if (state.startsWith('menu-admin')) await go('/menu?denied=1', 'F02');
    else if (state.startsWith('search-') || state === 'export-generating') { await search(); if (state === 'search-validation') { await item('F03-I01').fill('12x'); assert.equal(await clickResponse('F03-I05', '/employees/search'), 422); await page.locator('[data-ui="error-summary"]').waitFor(); } }
    else if (state.startsWith('edit-') || state.startsWith('employee-')) {
      await edit(['edit-career', 'employee-pending-confirmation'].includes(state));
      if (state === 'employee-validation') { await item('F04-I02').fill(''); assert.equal(await clickResponse('F04-I28', '/employees/save'), 422); await page.locator('[data-ui="error-summary"]').waitFor(); }
      if (state === 'employee-discard') { await item('F04-I02').fill('独立所属監査'); await item('F04-I29').click(); await page.locator('dialog[open]').waitFor(); }
      if (state === 'employee-pending-confirmation') { await item('F04-I17').fill('独立未反映監査'); await item('F04-I25').click(); await page.locator('dialog[open]').waitFor(); }
    } else if (state.startsWith('code')) {
      await codes();
      if (state === 'code-validation') { await item('F06-I04').fill(''); assert.equal(await clickResponse('F06-I09', '/codes/save'), 422); await page.locator('[data-ui="error-summary"]').waitFor(); }
      if (state === 'code-discard') { await item('F06-I04').fill('独立所属監査'); await item('F06-I10').click(); await page.locator('dialog[open]').waitFor(); }
      if (state === 'code-stop-confirmation') { await item('F06-I06').uncheck(); await item('F06-I09').click(); await page.locator('dialog[open]').waitFor(); }
    } else if (state === 'get-error') { assert.equal((await page.goto(profile.url + '/employees/9223372036854775807/edit')).status(), 404); await page.locator('[data-ui-error]').waitFor(); }
    else throw Error('Unprepared state ' + state);
    if (state.endsWith('-narrow')) { await resize(390); if (!(await page.locator('.nav details').evaluate(n => n.open))) await page.locator('.nav summary').click(); await page.waitForFunction(() => document.querySelector('.nav details').open); }
  }
  async function capture(state, variant = '') {
    const result = await collectInventory(page, state), stem = state + (variant ? '-' + variant : '');
    const file = path.join(out, stem + '.json'), shot = path.join(out, stem + '.png');
    fs.writeFileSync(file, JSON.stringify({ ...result, variant }, null, 2) + '\n'); await page.screenshot({ path: shot, fullPage: true });
    const evidence = [proof(file), proof(shot)];
    for (const c of result.components) if (!observed.has(c.id)) observed.set(c.id, { ...c, evidence });
    states.push({ state, variant, observed: result.components.length, notMeasured: result.notMeasured, unresolved: result.unresolved, childOwnershipCount: result.childOwnership.length, environment: result.environment, evidence });
  }
  try {
    publicContext = await browser.newContext({ ignoreHTTPSErrors: true, viewport: { width: 1366, height: 768 } }); context = await browser.newContext({ ignoreHTTPSErrors: true, viewport: { width: 1366, height: 768 } });
    for (const c of [publicContext, context]) { c.setDefaultTimeout(10000); c.on('page', p => {
      p.on('pageerror', e => errors.push(String(e.message).replaceAll(profile.adminPassword, '[redacted]')));
      p.on('dialog', async d => { if (d.type() === 'beforeunload') await d.accept(); else { errors.push('Unexpected browser dialog dismissed: ' + d.type()); await d.dismiss(); } });
      p.on('response', r => { const pathname = new URL(r.url()).pathname; if (r.request().method() !== 'POST' || !['/employees/save', '/codes/save'].includes(pathname)) return; pending.push((async () => { const record = { path: pathname, status: r.status() }; try { const body = await r.json(), outcome = body.outcome || body; record.outcomeKind = outcome.kind ?? null; record.commitState = outcome.commitState ?? null; if (record.commitState === 'Committed') errors.push('Unexpected committed Save'); } catch { record.outcomeUnparsed = true; } saveResponses.push(record); })()); });
    }); }
    page = await publicContext.newPage(); await prepare('login'); await capture('login'); await page.close();
    page = await context.newPage(); await go('/account/login'); await item('F01-I01').fill('admin'); await item('F01-I02').fill(profile.adminPassword); await Promise.all([page.waitForURL(u => u.pathname === '/menu'), item('F01-I04').click()]); await search(); await page.close();
    for (const state of [...new Set(descriptors.map(c => c.state))].filter(s => s !== 'login')) {
      page = await context.newPage();
      try {
        await prepare(state);
        if (state === 'export-generating') {
          let release, reached, finished; const gate = new Promise(r => release = r), arrived = new Promise(r => reached = r), handled = new Promise(r => finished = r);
          await page.route('**/employees/export', async route => { try { reached(); await gate; await route.abort('aborted'); } finally { finished(); } });
          try { await item('F03-I12').click(); await arrived; await page.locator('#export-cancel').waitFor(); await capture(state); } finally { release(); await handled; await page.unroute('**/employees/export'); }
        } else {
          await capture(state);
          if (state === 'search-selected') { await item('F03-I01').fill('12x'); assert.equal(await clickResponse('F03-I05', '/employees/search'), 422); await item('F03-I09').waitFor(); await capture(state, 'visible-notice'); }
          if (state === 'edit-basic') { await item('F04-I02').fill(''); assert.equal(await clickResponse('F04-I28', '/employees/save'), 422); await item('F04-I11').waitFor(); await capture(state, 'visible-notice'); }
          if (state === 'codes-selected') { await item('F06-I04').fill(''); assert.equal(await clickResponse('F06-I09', '/codes/save'), 422); await item('F06-I12').waitFor(); await capture(state, 'visible-notice'); }
        }
      } catch (e) { states.push({ state, preparationFailed: String(e.message).replaceAll(profile.adminPassword, '[redacted]') }); }
      finally { await page.close(); }
    }
  } finally {
    await Promise.allSettled(pending); await browser.close();
    assert.equal(hashArtifact(path.join(owner, 'build/publish')).sha256, artifact.sha256); assert.equal(sha(contractFile), process.env.SP2_EXPECTED_UI_SHA); assert.equal(sha(__filename), source.sha256);
    for (const item of frozen) assert.equal(sha(path.join(owner, item.file)), item.sha256, 'Frozen337 source/evidence changed');
    const missing = descriptors.filter(c => !observed.has(c.id)).map(c => ({ id: c.id, state: c.state, reason: 'No supported actual native mapping in prepared state' }));
    const record = { schemaVersion: 1, projectId: 'sample-project2', profileId: 'CSharp_ASPNET', runId: contract.runId, status: 'PARTIAL_ACTUAL_COMPONENT_INVENTORY_SUPPLEMENT', artifact, contractSha256: sha(contractFile), inputManifestSha256: sha(path.join(owner, 'build/generation/inputs.json')), measurementSources: [source], frozen337SourcesUnchanged: frozen, components: [...observed.values()], notMeasured: missing, environment: states.find(s => s.environment)?.environment || null, states, errors, saveResponses, scope: 'Actual native tags/roles/data attributes and explicit child-owner containment/font equality. No expected kind/textCapable/property values are measurement inputs. Only active prepared states grant component coverage. Other-state direct matches identify current DOM ownership without granting that state coverage. CSS resolution is browser-reported via media queries; physical monitor DPI/OS display scale are unmeasured. No successful Save is intended; actual Save outcomes are recorded. Export waiting UI is sampled through outbound request delay only.', formalScore: null };
    const file = path.join(owner, 'build/test-results/independent-ui/component-inventory-supplement.json'); fs.writeFileSync(file, JSON.stringify(record, null, 2) + '\n');
    console.log(JSON.stringify({ status: record.status, observedComponents: observed.size, missing: missing.length, unresolvedChildren: states.reduce((a, s) => a + (s.unresolved?.length || 0), 0), preparationFailures: states.filter(s => s.preparationFailed).length, errors: errors.length }));
  }
}
if (require.main === module) run().catch(e => { console.error(e.message); process.exitCode = 1; });
module.exports = { collectInventory, run };
