'use strict';
// Small independent HTML fixture: verifies collection semantics, not the product UI.
const assert = require('node:assert/strict');
const { collectMetrics } = require('./noninteraction-metrics.cjs');
const { chromium } = require(process.env.SP2_PLAYWRIGHT_MODULE || 'playwright-core');
(async () => {
  const browser = await chromium.launch({ executablePath: 'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe', headless: true });
  try {
    const page = await browser.newPage();
    await page.setContent('<style>input{height:23px;box-sizing:border-box}.b{height:37px;border-radius:10%}.hidden{display:none}</style><main><label for="a">A</label><input id="a"><input id="b" class="b"><input class="hidden"><label for="missing">B</label></main>');
    const components = [{ id: 'mixed', selector: 'input', state: 'fixture' }, { id: 'label', selector: 'label', state: 'fixture' }, { id: 'empty', selector: '.absent', state: 'fixture' }, { id: 'radius', selector: '#b', state: 'fixture' }, { id: 'main', selector: 'main', state: 'fixture' }];
    const result = await collectMetrics(page, { stateId: 'fixture', componentDescriptors: components, ruleDescriptors: [
      { id: 'mixed-height', target: 'mixed', kind: 'dimensions', propertyNames: ['controlHeightPx'] },
      { id: 'all-labels', target: 'label', kind: 'render', propertyNames: ['associatedControl'] },
      { id: 'absent', target: 'empty', kind: 'dimensions', propertyNames: ['widthPx'] },
      { id: 'unknown', target: 'label', kind: 'render', propertyNames: ['pretend'] },
      { id: 'percent-radius', target: 'radius', kind: 'appearance', propertyNames: ['borderRadiusPx'] },
      { id: 'empty-headings', target: 'main', kind: 'render', propertyNames: ['independentGroupHeadings'] },
    ] });
    assert.equal(result.observations.find(o => o.ruleId === 'all-labels').properties.associatedControl, false, 'A broken later label must not hide behind the first good label');
    assert.equal(result.notMeasured.find(n => n.ruleId === 'mixed-height').members.length, 3, 'All matched including hidden are retained');
    assert.match(result.notMeasured.find(n => n.ruleId === 'mixed-height').reason, /Nonuniform/);
    assert.match(result.notMeasured.find(n => n.ruleId === 'absent').reason, /No visible/);
    assert.match(result.notMeasured.find(n => n.ruleId === 'unknown').reason, /Unsupported/);
    assert.match(result.notMeasured.find(n => n.ruleId === 'percent-radius').reason, /not one px scalar/);
    assert.equal(result.observations.find(n => n.ruleId === 'empty-headings').properties.independentGroupHeadings, false);
    await page.setContent('<div id="surface">No main</div>');
    const noMain = await collectMetrics(page, { stateId: 'fixture', componentDescriptors: [{ id: 'surface', state: 'fixture', selector: '#surface' }], ruleDescriptors: [{ id: 'main-absent', target: 'surface', kind: 'dimensions', propertyNames: ['mainUsableWidthPx'] }] });
    assert.match(noMain.notMeasured[0].reason, /No unique actual visible main/);
    console.log(JSON.stringify({ status: 'PASS_SYNTHETIC_COLLECTOR_SEMANTICS', assertions: 8, productExecuted: false }));
  } finally { await browser.close(); }
})().catch(e => { console.error(e.message); process.exitCode = 1; });
