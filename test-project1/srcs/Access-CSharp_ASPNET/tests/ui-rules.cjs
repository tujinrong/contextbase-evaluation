const fs = require('node:fs'), path = require('node:path'), assert = require('node:assert/strict');
const method = path.resolve(__dirname, '..');
const { chromium } = require(process.env.PLAYWRIGHT_MODULE ?? path.join(method, '.tmp/browser/node_modules/playwright-core'));
const base = process.env.TARGET_URL ?? 'http://127.0.0.1:5092';
const evidence = path.join(method, '.tmp/ui-rules');
fs.mkdirSync(evidence, { recursive: true });
const result = { schema: 'access-web-ui-rules/0.4', revision: 'compact-table-calendar', rules: ['AR028', 'AR029', 'AR030'], writeOperations: 0, trainingIterationsAdded: 0, deviceScope: 'Desktop PC only; smartphone support excluded by user', checks: [], measurements: [], failures: [], consoleErrors: [], formalScore: null };
let browser;
async function step(name, action) {
    try { await action(); result.checks.push({ name, status: 'PASS' }); }
    catch (error) { result.checks.push({ name, status: 'FAIL', message: error.message }); throw error; }
}
function executable() {
    if (process.env.CHROMIUM_EXECUTABLE) return process.env.CHROMIUM_EXECUTABLE;
    const cache = path.join(process.env.LOCALAPPDATA ?? '', 'ms-playwright');
    if (fs.existsSync(cache)) for (const dir of fs.readdirSync(cache).filter(n => /^chromium-\d+$/.test(n)).sort().reverse()) {
        const file = path.join(cache, dir, 'chrome-win64/chrome.exe'); if (fs.existsSync(file)) return file;
    }
}
async function newForm(page) {
    await page.goto(base + '/Students');
    await page.getByRole('link', { name: '新規登録', exact: true }).click();
    await page.locator('[data-editor-form]').waitFor();
}
async function geometry(page, kind) {
    return page.evaluate(kind => {
        const fields = [...document.querySelectorAll(kind === 'search' ? '.search-grid .field' : '.student-editor .field')];
        const groups = [...document.querySelectorAll('.search-grid,.basic-grid,.section-fields,.notes-section')];
        const rows = fields.flatMap(field => {
            const label = field.querySelector(':scope > label'), control = field.querySelector('input:not([type=hidden]):not([type=checkbox]),select,textarea');
            if (!label || !control) return [];
            const l = label.getBoundingClientRect(), c = control.getBoundingClientRect();
            return [{ id: control.id, group: groups.indexOf(field.closest('.search-grid,.basic-grid,.section-fields,.notes-section')), labelLeft: l.left, labelRight: l.right, labelTop: l.top, controlLeft: c.left, controlTop: c.top, controlRight: c.right, controlBottom: c.bottom, labelFor: label.htmlFor }];
        });
        const save = document.querySelector('.savebar')?.getBoundingClientRect();
        return { kind, viewport: { width: innerWidth, height: innerHeight }, browserZoom: visualViewport?.scale ?? 1, devicePixelRatio, pageWidth: document.documentElement.scrollWidth, rows, save: save ? { top: save.top, bottom: save.bottom } : null };
    }, kind);
}
function assertAligned(measurement) {
    assert.ok(measurement.rows.length >= (measurement.kind === 'search' ? 3 : 20));
    assert.ok(measurement.pageWidth <= measurement.viewport.width, 'page has horizontal overflow');
    for (const row of measurement.rows) {
        assert.equal(row.labelFor, row.id, row.id + ' label binding');
        assert.ok(row.labelRight <= row.controlLeft + 1, row.id + ' label must be left of control');
        assert.ok(Math.abs(row.labelTop - row.controlTop) < 13, row.id + ' label and control must share a row');
        assert.ok(row.controlRight <= measurement.viewport.width, row.id + ' overflows viewport');
    }
    const groups = new Map();
    for (const row of measurement.rows) {
        const key = row.group + ":" + Math.round(row.labelLeft);
        if (!groups.has(key)) groups.set(key, row.controlLeft);
        assert.ok(Math.abs(groups.get(key) - row.controlLeft) <= 1, row.id + ' control column is not aligned');
    }
}
async function keyboardDate(input, iso) {
    // Empty Chromium date segments advance automatically after enough digits.
    // Re-anchor each segment so this remains actual keyboard entry from empty.
    for (const [part, text] of iso.split('-').entries()) {
        await input.focus();
        for (let n = 0; n < 6; n++) await input.press('ArrowLeft');
        for (let n = 0; n < part; n++) await input.press('ArrowRight');
        await input.pressSequentially(text);
    }
}
async function nextCalendarDay(page, input, mouse = false) {
    if (mouse) {
        const box = await input.boundingBox();
        await input.click({ position: { x: box.width - 22, y: box.height / 2 } });
    } else {
        await input.focus();
        for (let n = 0; n < 6; n++) await input.press('ArrowLeft');
        // Native Japanese date input: year -> month -> day -> picker button.
        for (let n = 0; n < 3; n++) await page.keyboard.press('Tab');
        await page.keyboard.press('Space');
    }
    await page.keyboard.press('ArrowRight'); await page.keyboard.press('Enter');
}
(async () => {
    browser = await chromium.launch({ headless: true, ...(executable() ? { executablePath: executable() } : {}) });
    const context = await browser.newContext({ locale: 'ja-JP', timezoneId: 'Asia/Tokyo', ignoreHTTPSErrors: true, viewport: { width: 1366, height: 650 } });
    const page = await context.newPage(); page.on('pageerror', e => result.consoleErrors.push(e.message));
    page.on('dialog', d => d.accept());
    const forbiddenWrites = [];
    page.on('request', request => {
        if (request.method() === 'POST' && !request.url().includes('/Students/EditorOptions')) forbiddenWrites.push(request.url());
    });
    for (const width of [1366, 1280]) {
        await step(`${width}x650 search uses aligned label/value rows`, async () => {
            await page.setViewportSize({ width, height: 650 }); await page.goto(base + '/Students');
            const measure = await geometry(page, 'search'); assertAligned(measure); result.measurements.push(measure);
            await page.screenshot({ path: path.join(evidence, `search-${width}.png`), fullPage: true });
        });
        await step(`${width}x650 editor keeps all fields and primary actions compact`, async () => {
            await newForm(page); const measure = await geometry(page, 'editor'); assertAligned(measure);
            assert.ok(measure.rows.every(row => row.controlBottom <= 650), 'an editor field is below the target viewport');
            assert.ok(measure.save && measure.save.bottom <= 650, 'save actions are below the target viewport');
            assert.ok(measure.rows.every(row => row.controlBottom <= measure.save.top + 1), 'save actions cover an editor field');
            result.measurements.push(measure); await page.screenshot({ path: path.join(evidence, `editor-${width}.png`), fullPage: true });
        });
    }
    const birth = page.locator('#Input_BirthDate'), hint = page.locator('[data-birth-hint]');
    await step('date-only inputs use one calendar control with associated era hints', async () => {
        for (const id of ['Input_BirthDate', 'Input_AdmissionDate', 'Input_EnrollmentEndDate']) {
            const input = page.locator('#' + id); assert.equal(await input.getAttribute('type'), 'date');
            const description = await input.getAttribute('aria-describedby'); assert.ok(description);
            assert.equal(await page.locator('#' + description.split(' ')[0]).count(), 1);
        }
        assert.equal(await page.locator('select[name*="BirthDate"],input[name*="BirthDate."]').count(), 0);
    });
    await step('a past date can be entered with the real segmented keyboard control', async () => {
        await keyboardDate(birth, '1989-01-07'); assert.equal(await birth.inputValue(), '1989-01-07');
        assert.match(await hint.innerText(), /昭和64年1月7日/);
    });
    await step('native calendar opened with keyboard crosses Showa/Heisei correctly', async () => {
        await nextCalendarDay(page, birth); assert.equal(await birth.inputValue(), '1989-01-08');
        assert.match(await hint.innerText(), /平成元年1月8日/);
    });
    await step('native calendar icon and day selection cross Heisei/Reiwa correctly', async () => {
        await birth.fill('2019-04-30'); assert.match(await hint.innerText(), /平成31年4月30日/);
        await nextCalendarDay(page, birth, true); assert.equal(await birth.inputValue(), '2019-05-01');
        assert.match(await hint.innerText(), /令和元年5月1日/);
    });
    await step('calendar handles leap day and the non-leap century', async () => {
        await birth.fill('2000-02-28'); await nextCalendarDay(page, birth);
        assert.equal(await birth.inputValue(), '2000-02-29'); assert.match(await hint.innerText(), /平成12年2月29日/);
        await nextCalendarDay(page, birth); assert.equal(await birth.inputValue(), '2000-03-01');
        await birth.fill('1900-02-28'); await nextCalendarDay(page, birth); assert.equal(await birth.inputValue(), '1900-03-01');
    });
    await step('invalid keyboard date is not normalized to a different valid day', async () => {
        await keyboardDate(birth, '1900-02-29');
        assert.equal(await birth.inputValue(), ''); assert.equal(await birth.evaluate(e => e.validity.badInput), true);
        assert.match(await hint.innerText(), /日付を確認/);
    });
    await step('clear and required/optional constraints retain the one-input contract', async () => {
        await birth.fill('2000-06-03'); await birth.focus(); await birth.press('Delete');
        assert.equal(await birth.inputValue(), ''); assert.equal(await birth.evaluate(e => e.validity.valueMissing), true);
        assert.match(await hint.innerText(), /日付を選択|日付を確認/);
        assert.equal(await page.locator('#Input_EnrollmentEndDate').evaluate(e => e.required), false);
        await birth.fill('1899-12-31'); assert.equal(await birth.evaluate(e => e.validity.rangeUnderflow), true);
        const tomorrow = await birth.evaluate(e => { const d = new Date(e.max + 'T00:00:00Z'); d.setUTCDate(d.getUTCDate() + 1); return d.toISOString().slice(0, 10); });
        await birth.fill(tomorrow); assert.equal(await birth.evaluate(e => e.validity.rangeOverflow), true);
    });
    await step('admission and optional end-date hints follow edits and status clearing', async () => {
        await newForm(page);
        await page.locator('#Input_AdmissionDate').fill('2026-04-01');
        assert.equal(await page.locator('[data-japanese-date-for="Input_AdmissionDate"]').innerText(), '令和8年4月1日');
        await page.locator('#Input_EnrollmentStatusCode').selectOption('03');
        await page.waitForFunction(() => document.querySelector('[data-editor-form]').dataset.optionsState === 'ready');
        await page.locator('#Input_EnrollmentEndDate').fill('2026-10-01');
        assert.equal(await page.locator('[data-japanese-date-for="Input_EnrollmentEndDate"]').innerText(), '令和8年10月1日');
        await page.locator('#Input_EnrollmentStatusCode').selectOption('01');
        await page.waitForFunction(() => document.querySelector('[data-editor-form]').dataset.optionsState === 'ready');
        assert.equal(await page.locator('#Input_EnrollmentEndDate').inputValue(), '');
        assert.equal(await page.locator('#Input_EnrollmentEndDate').evaluate(e => e.readOnly), true);
        assert.equal(await page.locator('[data-japanese-date-for="Input_EnrollmentEndDate"]').innerText(), '未設定');
    });
    await step('server-loaded date has the matching Japanese era hint after reload', async () => {
        await page.goto(base + '/Students?Searched=true&StudentNo=TRN001&Statuses=01');
        await page.locator('tbody tr').filter({ hasText: 'TRN001' }).getByRole('link', { name: '編集', exact: true }).click();
        const value = await birth.inputValue();
        const expected = await birth.evaluate(e => new Intl.DateTimeFormat('ja-JP-u-ca-japanese', { era: 'long', year: 'numeric', month: 'long', day: 'numeric', timeZone: 'UTC' }).format(new Date(e.value + 'T00:00:00Z')));
        assert.match(value, /^\d{4}-\d{2}-\d{2}$/); assert.equal(await hint.innerText(), expected);
    });
    await step('1024px PC window keeps all fields and actions reachable', async () => {
        await page.setViewportSize({ width: 1024, height: 650 }); await newForm(page);
        assert.equal(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth), true);
        assert.equal(await page.locator('.student-editor .field label').count() >= 20, true);
        await page.getByRole('button', { name: '保存', exact: true }).scrollIntoViewIfNeeded();
        assert.ok(await page.getByRole('button', { name: '保存', exact: true }).isVisible());
        await page.screenshot({ path: path.join(evidence, 'editor-1024.png'), fullPage: true });
    });
    await step('Japanese era hint does not shift the selected date in other timezones', async () => {
        for (const timezoneId of ['America/Los_Angeles', 'Pacific/Auckland']) {
            const remote = await browser.newContext({ locale: 'ja-JP', timezoneId, ignoreHTTPSErrors: true });
            try { const target = await remote.newPage(); await newForm(target); await target.locator('#Input_BirthDate').fill('2019-05-01'); assert.equal(await target.locator('[data-birth-hint]').innerText(), '令和元年5月1日'); assert.equal(await target.locator('#Input_BirthDate').inputValue(), '2019-05-01'); }
            finally { await remote.close(); }
        }
    });
    assert.equal(result.consoleErrors.length, 0); assert.equal(forbiddenWrites.length, 0, 'test must not submit business writes');
    result.calendarInteraction = 'Actual Chromium native picker: keyboard Tab to calendar icon and Space, or mouse calendar icon; ArrowRight/Enter selects the next day. Not value-fill-only.';
})().catch(error => { result.failures.push(error.stack ?? error.message); process.exitCode = 1; }).finally(async () => {
    if (browser) await browser.close(); result.status = result.failures.length ? 'FAIL' : 'PASS';
    const report = process.env.UI_RULES_REPORT ?? path.join(method, 'build/test-results/ui-rules-browser.json');
    fs.writeFileSync(report, JSON.stringify(result, null, 2) + '\n');
    process.stdout.write(JSON.stringify({ status: result.status, checks: result.checks, failures: result.failures }, null, 2) + '\n');
});
