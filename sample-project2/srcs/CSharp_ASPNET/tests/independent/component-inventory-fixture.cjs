'use strict';
const assert = require('node:assert/strict');
const { collectInventory } = require('./component-inventory-supplement.cjs');
const { chromium } = require(process.env.SP2_PLAYWRIGHT_MODULE || 'playwright-core');
(async () => {
  const browser = await chromium.launch({ executablePath: 'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe', headless: true });
  try {
    const page = await browser.newPage();
    await page.setContent('<style>.sp2-ui{font:16px Arial}.crumb{font:14px Arial}</style><div class="sp2-ui" data-screen-id="F02"><main><div class="crumb"><span>crumb</span></div><section class="panel"><p id="same">same16</p><p id="different" style="font-size:18px">different18</p></section><p id="orphan">No blanket coverage</p></main></div>');
    const x = await collectInventory(page, 'menu-admin');
    assert.equal(x.components.find(c => c.id === 'F02.surface').kind, 'Surface');
    assert.equal(x.childOwnership.find(c => c.node.id === 'same').tupleEqual, true);
    assert.equal(x.unresolved.find(c => c.node.id === 'different').reason, 'CHILD_OWNER_FONT_TUPLE_DIFF');
    assert.equal(x.unresolved.find(c => c.node.id === 'orphan').reason, 'NO_EXPLICIT_LOGICAL_OWNER');
    assert.ok(x.components.every(c => c.preparedState === 'menu-admin'));
    assert.ok(!x.components.some(c => c.id === 'COMMON.getError.surface'), 'Generic other-state direct selector must not grant component coverage');
    assert.ok(x.environment.resolutionProbes.length > 20);
    await page.setContent('<div class="sp2-ui" data-screen-id="F06"><p class="help" data-item-id="F06-I07">Explicit business note</p><div data-ui="error-summary"><ul><li><a href="#field">A field error</a></li></ul></div></div>');
    const code = await collectInventory(page, 'codes-selected');
    assert.equal(code.components.find(c => c.id === 'F06-I07').kind, 'Label');
    assert.ok(code.childOwnership.some(c => c.node.nativeTag === 'a' && c.mapping === 'ERROR_SUMMARY_CHILD_TEXT_TO_SUMMARY' && c.tupleEqual));
    assert.ok(code.components.every(c => c.preparedState === 'codes-selected'));
    console.log(JSON.stringify({ status: 'PASS_SYNTHETIC_COMPONENT_INVENTORY', assertions: 10, measuredCssResolution: x.environment.cssResolution, productExecuted: false }));
  } finally { await browser.close(); }
})().catch(e => { console.error(e.message); process.exitCode = 1; });
