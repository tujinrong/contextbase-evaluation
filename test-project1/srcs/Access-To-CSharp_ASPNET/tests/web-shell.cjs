const fs = require('node:fs'), path = require('node:path'), assert = require('node:assert/strict');
const method = path.resolve(__dirname, '..');
const { chromium } = require(process.env.PLAYWRIGHT_MODULE ?? path.join(method, '.tmp/browser/node_modules/playwright-core'));
const base = process.env.TARGET_URL ?? 'http://127.0.0.1:5091';
const readerBase = process.env.READER_URL;
const evidence = path.join(method, '.tmp/web-shell');
fs.mkdirSync(evidence, { recursive: true });
const report = { schema: 'access-web-shell-browser/1.0', revision: 'web-group-sidebar', recordedDate: '2026-10-28', rules: ['AR028', 'AR029', 'AR030', 'AR031', 'AR032'], deviceScope: 'Desktop PC 1280x650 and 1366x650; smartphone excluded by user', provider: 'SqlServer (read-only screen verification)', writeOperations: 0, trainingIterationsAdded: 0, checks: [], measurements: [], failures: [], forbiddenRequests: [], pageErrors: [], resourceErrors: [], cspViolations: [], formalScore: null };
const fieldIds = ['StudentNo', 'StudentName', 'StudentNameKana', 'BirthDate', 'GenderCode', 'PostalCode', 'PrefectureCode', 'AddressLine1', 'AddressLine2', 'PhoneNumber', 'EmailAddress', 'AdmissionDate', 'EnrollmentStatusCode', 'EnrollmentEndDate', 'SchoolYear', 'GradeCode', 'ClassId', 'EmergencyContactName', 'RelationshipCode', 'EmergencyPhoneNumber', 'Remarks', 'OperationReason'];
let browser;
async function step(name, action) {
    try { await action(); report.checks.push({ name, status: 'PASS' }); }
    catch (error) { report.checks.push({ name, status: 'FAIL', message: error.message }); throw error; }
}
function executable() {
    if (process.env.CHROMIUM_EXECUTABLE) return process.env.CHROMIUM_EXECUTABLE;
    const cache = path.join(process.env.LOCALAPPDATA ?? '', 'ms-playwright');
    if (fs.existsSync(cache)) for (const dir of fs.readdirSync(cache).filter(name => /^chromium-\d+$/.test(name)).sort().reverse()) {
        const file = path.join(cache, dir, 'chrome-win64/chrome.exe');
        if (fs.existsSync(file)) return file;
    }
}
async function context() {
    const instance = await browser.newContext({ locale: 'ja-JP', timezoneId: 'Asia/Tokyo', viewport: { width: 1280, height: 650 }, ignoreHTTPSErrors: true });
    await instance.route('**/*', route => {
        if (!['GET', 'HEAD'].includes(route.request().method())) {
            report.forbiddenRequests.push({ method: route.request().method(), url: route.request().url() });
            return route.abort();
        }
        return route.continue();
    });
    await instance.exposeBinding('__recordShellCsp', (_, violation) => report.cspViolations.push(violation));
    await instance.addInitScript(() => document.addEventListener('securitypolicyviolation', event => {
        window.__recordShellCsp({ directive: event.effectiveDirective, blockedURI: event.blockedURI });
    }));
    instance.on('page', page => {
        page.on('pageerror', error => report.pageErrors.push(error.message));
        page.on('requestfailed', request => {
            const error = request.failure()?.errorText ?? '';
            if (!error.includes('ERR_ABORTED')) report.resourceErrors.push({ url: request.url(), error });
        });
    });
    return instance;
}
async function checkShell(page, active) {
    const nav = page.locator('.app-sidebar nav[aria-label="メインメニュー"]');
    assert.equal(await nav.count(), 1);
    assert.equal(await nav.locator('[aria-current="page"]').count(), 1);
    assert.equal(await nav.getByRole('link', { name: active, exact: true }).getAttribute('aria-current'), 'page');
    const measure = await page.evaluate(() => {
        const rect = element => { const b = element.getBoundingClientRect(); return { left: b.left, right: b.right, top: b.top, bottom: b.bottom, width: b.width, height: b.height }; };
        const sidebar = document.querySelector('.app-sidebar'), nav = sidebar.querySelector('nav'), main = document.querySelector('main');
        return { viewport: { width: innerWidth, height: innerHeight }, pageWidth: document.documentElement.scrollWidth, sidebar: rect(sidebar), main: rect(main), links: [...nav.querySelectorAll('a')].map(rect) };
    });
    assert.ok(measure.sidebar.left >= 0 && measure.sidebar.left < 20, 'sidebar must occupy the left side');
    assert.ok(measure.sidebar.width >= 120 && measure.sidebar.width <= 200, 'sidebar should preserve useful content width');
    assert.ok(measure.main.left >= measure.sidebar.right - 1, 'sidebar overlaps main content');
    assert.ok(measure.pageWidth <= measure.viewport.width, 'desktop document has horizontal overflow');
    for (let index = 1; index < measure.links.length; index++) {
        assert.ok(Math.abs(measure.links[index].left - measure.links[index - 1].left) <= 1, 'menu left edges are not aligned');
        assert.ok(measure.links[index].top >= measure.links[index - 1].bottom - 1, 'menu must be vertical');
    }
    report.measurements.push({ kind: 'sidebar', active, ...measure });
}
async function newForm(page) {
    await page.goto(base + '/Students');
    await page.getByRole('link', { name: '新規登録', exact: true }).click();
    await page.locator('[data-editor-form]').waitFor();
}
async function checkGroups(page) {
    const groups = await page.locator('section.editor-group').evaluateAll(sections => sections.map(section => {
        const heading = section.querySelector(':scope > h2[data-group-heading]');
        const fieldset = section.querySelector(':scope > fieldset');
        if (!heading || !fieldset) return { validStructure: false };
        const h = heading.getBoundingClientRect(), f = fieldset.getBoundingClientRect();
        return { validStructure: true, text: heading.textContent.replace(/\s+/g, ' ').trim(), headingId: heading.id, labelledBy: fieldset.getAttribute('aria-labelledby'), headingBottom: h.bottom, contentTop: f.top, headingLeft: h.left, contentLeft: f.left, fontWeight: Number(getComputedStyle(heading).fontWeight), legendCount: fieldset.querySelectorAll('legend').length, headingPosition: getComputedStyle(heading).position };
    }));
    assert.equal(groups.length, 5, 'all five business groups remain present');
    assert.match(groups[0].text, /01\s*基本情報/);
    for (const group of groups) {
        assert.ok(group.validStructure && group.headingId, 'group needs a separate heading above its content');
        assert.equal(group.labelledBy, group.headingId, 'disabled fieldset must retain its accessible group name');
        assert.equal(group.legendCount, 0, 'Access-style legend notch must not remain');
        assert.ok(group.headingBottom <= group.contentTop + 1, 'group heading overlaps the content border');
        assert.ok(Math.abs(group.headingLeft - group.contentLeft) <= 2, 'group heading and content should align');
        assert.ok(group.fontWeight >= 600, 'group heading must be bold');
        assert.notEqual(group.headingPosition, 'absolute', 'group heading should be normal document flow');
    }
    const controls = [];
    for (const id of fieldIds) {
        const control = page.locator('#Input_' + id);
        assert.equal(await control.count(), 1, 'missing business field ' + id);
        const box = await control.boundingBox();
        assert.ok(box && box.y >= 0 && box.y + box.height <= 650, id + ' falls below the standard PC viewport');
        controls.push({ id, ...box });
    }
    const save = await page.getByRole('button', { name: '保存', exact: true }).boundingBox();
    assert.ok(save && save.y >= 0 && save.y + save.height <= 650, 'save button is not within the PC viewport');
    report.measurements.push({ kind: 'group-headings', viewport: page.viewportSize(), groups, controls, save });
}
async function keyboardLink(page, name) {
    const target = page.locator('.app-sidebar nav').getByRole('link', { name, exact: true });
    const href = await target.getAttribute('href');
    let focused = false;
    for (let tab = 0; tab < 15; tab++) {
        await page.keyboard.press('Tab');
        focused = await target.evaluate(element => document.activeElement === element);
        if (focused) break;
    }
    assert.ok(focused, name + ' is not reachable by the real Tab key');
    await page.keyboard.press('Enter');
    await page.waitForURL(url => url.pathname === new URL(href, base).pathname);
}
(async () => {
    browser = await chromium.launch({ headless: true, ...(executable() ? { executablePath: executable() } : {}) });
    const admin = await context(), page = await admin.newPage();
    for (const width of [1280, 1366]) {
        await step(`${width}x650 left sidebar keeps navigation separate from search content`, async () => {
            await page.setViewportSize({ width, height: 650 });
            const response = await page.goto(base + '/Students');
            assert.equal(response.status(), 200);
            report.contentSecurityPolicyHeader ??= response.headers()['content-security-policy'] ?? null;
            await checkShell(page, '学生一覧');
            await page.screenshot({ path: path.join(evidence, `search-${width}.png`), fullPage: true });
        });
        await step(`${width}x650 independent bold group headings retain all fields and save actions`, async () => {
            await newForm(page); await checkShell(page, '学生一覧'); await checkGroups(page);
            await page.screenshot({ path: path.join(evidence, `editor-${width}.png`), fullPage: true });
        });
    }
    await step('real Tab and Enter navigation opens Masters with its current-menu state', async () => {
        await page.goto(base + '/Students'); await keyboardLink(page, 'マスタ管理');
        await page.getByRole('heading', { name: 'マスタ管理', exact: true }).waitFor();
        await checkShell(page, 'マスタ管理');
    });
    await step('sidebar keyboard return to Students preserves the correct selected section', async () => {
        await page.goto(base + '/Masters'); await keyboardLink(page, '学生一覧');
        await page.getByRole('heading', { name: '学生検索', exact: true }).waitFor();
        await checkShell(page, '学生一覧');
    });
    await step('new editor cancel returns to search without submitting business data', async () => {
        await newForm(page); await page.getByRole('link', { name: 'キャンセル', exact: true }).click();
        await page.getByRole('heading', { name: '学生検索', exact: true }).waitFor();
        await checkShell(page, '学生一覧');
    });
    await step('shared SQL student data still opens with calendar controls and era display', async () => {
        await page.goto(base + '/Students?Searched=true&StudentNo=TRN001&Statuses=01');
        const row = page.locator('tbody tr').filter({ hasText: 'TRN001' });
        assert.equal(await row.count(), 1); await row.getByRole('link', { name: '編集', exact: true }).click();
        assert.equal(await page.locator('#Input_BirthDate').getAttribute('type'), 'date');
        assert.match(await page.locator('[data-birth-hint]').innerText(), /平成/);
        await checkGroups(page);
    });
    if (readerBase) {
        await step('Reader sidebar hides administrative navigation and direct Masters remains forbidden', async () => {
            const reader = await context(), view = await reader.newPage();
            try {
                assert.equal((await view.goto(readerBase + '/Students')).status(), 200);
                await checkShell(view, '学生一覧');
                assert.equal(await view.locator('.app-sidebar nav').getByRole('link', { name: 'マスタ管理', exact: true }).count(), 0);
                assert.equal((await view.request.get(readerBase + '/Masters')).status(), 403);
            } finally { await reader.close(); }
        });
        await step('Reader detail retains disabled fields and accessible group names without save', async () => {
            const reader = await context(), view = await reader.newPage();
            try {
                await view.goto(readerBase + '/Students?Searched=true&StudentNo=TRN001&Statuses=01');
                await view.locator('tbody tr').filter({ hasText: 'TRN001' }).getByRole('link', { name: '参照', exact: true }).click();
                assert.equal(await view.locator('section.editor-group > fieldset[disabled]').count(), 5);
                assert.equal(await view.getByRole('button', { name: '保存', exact: true }).count(), 0);
                for (const id of fieldIds) assert.equal(await view.locator('#Input_' + id).isDisabled(), true, 'Reader field enabled: ' + id);
                const names = await view.locator('section.editor-group > fieldset').evaluateAll(fields => fields.map(field => ({ id: field.getAttribute('aria-labelledby'), heading: document.getElementById(field.getAttribute('aria-labelledby'))?.tagName })));
                assert.ok(names.every(name => name.id && name.heading === 'H2'));
                await view.screenshot({ path: path.join(evidence, 'reader-detail.png'), fullPage: true });
            } finally { await reader.close(); }
        });
    } else report.notRun = ['Reader role screen checks: READER_URL was not supplied'];
    await step('shell emits no script, resource or CSP violations and no business POST', async () => {
        assert.deepEqual(report.pageErrors, []); assert.deepEqual(report.resourceErrors, []);
        assert.deepEqual(report.cspViolations, []); assert.deepEqual(report.forbiddenRequests, []);
    });
    await admin.close();
})().catch(error => { report.failures.push(error.stack ?? error.message); process.exitCode = 1; }).finally(async () => {
    if (browser) await browser.close();
    report.status = report.failures.length ? 'FAIL' : 'PASS';
    const target = process.env.WEB_SHELL_REPORT ?? path.join(method, 'build/test-results/web-shell-browser.json');
    fs.writeFileSync(target, JSON.stringify(report, null, 2) + '\n');
    process.stdout.write(JSON.stringify({ status: report.status, checks: report.checks, failures: report.failures }, null, 2) + '\n');
});
