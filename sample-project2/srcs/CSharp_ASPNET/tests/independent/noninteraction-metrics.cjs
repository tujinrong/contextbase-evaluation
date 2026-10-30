'use strict';

// Actual DOM measurements only. The caller passes property NAMES, never expected values/operators.
async function collectMetrics(page, { stateId, ruleDescriptors, componentDescriptors, preparation = {} }) {
  const rules = ruleDescriptors.map(r => ({ id: r.id, target: r.target, kind: r.kind, propertyNames: r.propertyNames }));
  const components = componentDescriptors.map(c => ({ id: c.id, selector: c.selector, state: c.state, textCapable: c.textCapable }));
  return page.evaluate(({ stateId, rules, components, preparation }) => {
    const observations = [], notMeasured = [], raw = [];
    const visible = n => {
      if (!n || !n.isConnected || !n.getClientRects().length) return false;
      const r = n.getBoundingClientRect();
      if (!(r.width > 0 && r.height > 0)) return false;
      for (let p = n; p; p = p.parentElement) { const s = getComputedStyle(p); if (p.hidden || s.display === 'none' || ['hidden', 'collapse'].includes(s.visibility) || Number(s.opacity) === 0) return false; }
      return true;
    };
    const rect = n => { const r = n.getBoundingClientRect(); return { x: r.x, y: r.y, width: r.width, height: r.height, right: r.right, bottom: r.bottom }; };
    const all = s => [...document.querySelectorAll(s)];
    const shown = s => all(s).filter(visible);
    const num = x => { const m = /^([+-]?(?:\d+(?:\.\d*)?|\.\d+))px$/.exec(String(x).trim()); if (!m) throw Error('Computed CSS dimension is not one px scalar: ' + x); return Number(m[1]); };
    const oneRect = s => { const a = shown(s); if (a.length !== 1) throw Error('Expected one actual visible node: ' + s); return rect(a[0]); };
    const uniform = a => { if (!a.length) throw Error('No actual members'); const v = a[0]; if (!a.every(x => JSON.stringify(x) === JSON.stringify(v))) throw Error('Nonuniform actual member values'); return v; };
    const overflow = () => Math.max(0, document.documentElement.scrollWidth - document.documentElement.clientWidth);
    function clipping(n) {
      const r = n.getBoundingClientRect();
      for (let p = n.parentElement; p && p !== document.body; p = p.parentElement) {
        const s = getComputedStyle(p), q = p.getBoundingClientRect();
        if (['hidden', 'clip'].includes(s.overflowX) && (r.left < q.left - 1 || r.right > q.right + 1)) return true;
        if (['hidden', 'clip'].includes(s.overflowY) && (r.top < q.top - 1 || r.bottom > q.bottom + 1)) return true;
      }
      return false;
    }
    for (const rule of rules) {
      if (rule.id.startsWith('NARROW.')) continue; // Separate six-case collection, never inferred here.
      const c = components.find(c => c.id === rule.target);
      if (!c || c.state !== stateId) continue;
      let members = [];
      try {
        const matched = all(c.selector), nodes = matched.filter(visible);
        members = matched.map(n => { const s = getComputedStyle(n); return { tag: n.tagName, id: n.id || null, item: n.dataset.itemId || null, visible: visible(n), rect: rect(n), rawCss: { borderRadius: s.borderRadius, padding: s.padding, outlineWidth: s.outlineWidth, backgroundColor: s.backgroundColor, color: s.color } }; });
        if (!nodes.length) throw Error('No visible actual member');
        const properties = {};
        for (const property of rule.propertyNames) {
          if (['widthPx', 'heightPx', 'controlHeightPx'].includes(property)) properties[property] = uniform(nodes.map(n => rect(n)[property === 'widthPx' ? 'width' : 'height']));
          else if (property === 'documentHorizontalOverflowPx') properties[property] = overflow();
          else if (property === 'mainUsableWidthPx') { const mains = shown('main'); if (mains.length !== 1) throw Error('No unique actual visible main'); const n = mains[0], s = getComputedStyle(n); properties[property] = n.clientWidth - num(s.paddingLeft) - num(s.paddingRight); }
          else if (property === 'loginPanelWidthPx') properties[property] = oneRect('.auth-panel').width;
          else if (property === 'loginIdWidthPx') properties[property] = oneRect('[data-item-id="F01-I01"]').width;
          else if (property === 'passwordWidthPx') properties[property] = oneRect('[data-item-id="F01-I02"]').width;
          else if (property === 'navWidthPx') properties[property] = oneRect('.nav').width;
          else if (property === 'headerHeightPx') properties[property] = oneRect('.header').height;
          else if (property === 'mainPaddingPx') { const n = shown('main')[0]; if (!n) throw Error('No main'); const s = getComputedStyle(n); properties[property] = uniform([s.paddingTop, s.paddingBottom, s.paddingLeft, s.paddingRight].map(num)); }
          else if (property === 'associatedControl') properties[property] = nodes.every(n => n instanceof HTMLLabelElement && n.control && n.htmlFor === n.control.id);
          else if (property === 'visibleLabel') properties[property] = nodes.every(n => !!n.textContent.trim() && visible(n) && !clipping(n));
          else if (property === 'present') properties[property] = nodes.length > 0;
          else if (property === 'pageHeadingVisible') properties[property] = shown('main h1').some(n => !!n.textContent.trim());
          else if (property === 'independentGroupHeadings') {
            // AUTH has one actual titled panel; grouped protected screens have h2 headings.
            const headings = nodes.flatMap(n => [...n.querySelectorAll(n.querySelector('.auth-panel') ? '.auth-panel h1' : 'h2')]).filter(visible);
            properties[property] = headings.length > 0 && headings.every(n => !!n.textContent.trim() && !n.closest('fieldset legend') && getComputedStyle(n).position !== 'absolute');
          } else if (property === 'headingBorderOverlapCount') {
            const headings = nodes.flatMap(n => [...n.querySelectorAll('h1,h2')]).filter(visible);
            properties[property] = headings.filter(h => {
              const r = h.getBoundingClientRect();
              for (let p = h.parentElement; p && !nodes.includes(p); p = p.parentElement) {
                const s = getComputedStyle(p), q = p.getBoundingClientRect();
                if ((num(s.borderTopWidth) && r.top < q.top + num(s.borderTopWidth) && r.bottom > q.top) || (num(s.borderBottomWidth) && r.bottom > q.bottom - num(s.borderBottomWidth) && r.top < q.bottom)) return true;
              }
              return false;
            }).length;
          } else if (property === 'truncatedRequiredControls') {
            const controls = nodes.flatMap(n => [...n.querySelectorAll('input:not([type="hidden"]),select,textarea,button,a')]).filter(n => visible(n) && !n.classList.contains('skip-link'));
            properties[property] = controls.filter(clipping).length;
          } else if (property === 'minimumRowHeightPx') {
            const rows = nodes.flatMap(n => n.tagName === 'TR' ? [n] : [...n.querySelectorAll('tbody tr')]).filter(visible);
            if (!rows.length) throw Error('No actual data rows');
            properties[property] = Math.min(...rows.map(n => rect(n).height));
          } else if (property === 'localScrollContainer') {
            properties[property] = nodes.every(n => { for (let p = n; p && p !== document.body; p = p.parentElement) { const s = getComputedStyle(p); if (['auto', 'scroll'].includes(s.overflowX) || ['auto', 'scroll'].includes(s.overflowY)) return p.clientWidth > 0 && p.clientHeight > 0; } return false; });
          } else if (property === 'backgroundColor' || property === 'color') properties[property] = uniform(nodes.map(n => getComputedStyle(n)[property]));
          else if (property === 'borderRadiusPx') properties[property] = uniform(nodes.flatMap(n => { const s = getComputedStyle(n); return [s.borderTopLeftRadius, s.borderTopRightRadius, s.borderBottomLeftRadius, s.borderBottomRightRadius].map(num); }));
          else if (property === 'focusOutlineWidthPx') properties[property] = uniform(nodes.map(n => num(getComputedStyle(n).outlineWidth)));
          else if (property === 'focusVisible') properties[property] = nodes.every(n => n === document.activeElement && n.matches(':focus-visible'));
          else if (property === 'selectedRowBackgroundColor') { const rows = nodes.flatMap(n => [...n.querySelectorAll('tr')]).filter(n => n.querySelector('input[type="radio"]:checked')); properties[property] = uniform(rows.map(n => getComputedStyle(n).backgroundColor)); }
          else if (property === 'selectionAlsoIdentifiedByText') {
            const rows = nodes.flatMap(n => [...n.querySelectorAll('tr')]).filter(n => n.querySelector('input[type="radio"]:checked'));
            const band = shown('[data-ui="selection"]')[0];
            properties[property] = rows.length === 1 && !!band && ['employeeNo', 'name'].every(col => { const text = rows[0].querySelector('[data-col="' + col + '"]')?.textContent.trim(); return !!text && band.textContent.includes(text); });
          } else if (property === 'employeeNumberVisible' || property === 'employeeNameVisible') {
            const key = property === 'employeeNumberVisible' ? 'F04-I01' : 'F04-I02'; const input = document.querySelector('[data-item-id="' + key + '"]');
            properties[property] = !!input && !!input.value && nodes.every(n => n.textContent.includes(input.value));
          } else if (property === 'modeVisible') properties[property] = nodes.every(n => /新規|編集/.test(n.textContent));
          else if (property === 'sameIdentityAcrossTabs') { if (typeof preparation.sameIdentityAcrossTabs !== 'boolean') throw Error('Actual before/after tab identity comparison absent'); properties[property] = preparation.sameIdentityAcrossTabs; }
          else if (property === 'fullValueReachable') { const result = preparation.fullValueResults?.[rule.target]; if (!result || typeof result.reachable !== 'boolean') throw Error('Control+End full-value operation not performed'); properties[property] = result.reachable; }
          else if (property === 'japaneseNoticeVisible') properties[property] = shown('[data-ui="error-message"]').some(n => /[\u3040-\u30ff\u3400-\u9fff]/u.test(n.textContent));
          else if (property === 'sharedShellVisible') properties[property] = shown('.brand').length > 0 && shown('main h1').length > 0 && shown('.nav').length > 0;
          else if (property === 'nextActionsVisible') properties[property] = shown('[data-ui-error] .actions a').some(n => !!n.getAttribute('href') && !!n.textContent.trim());
          else if (property === 'rawJsonVisible') { const text = document.body.innerText.trim(); properties[property] = /^[\[{]/.test(text) && /[\]}]$/.test(text); }
          else throw Error('Unsupported actual measurement property: ' + property);
        }
        observations.push({ ruleId: rule.id, target: rule.target, method: rule.kind === 'appearance' ? 'computed-style' : 'layout-measurement', properties });
        raw.push({ ruleId: rule.id, selector: c.selector, matchedCount: matched.length, visibleCount: nodes.length, members, headingInventory: nodes.flatMap(n => [...n.querySelectorAll('h1,h2')]).map(n => ({ tag: n.tagName, visible: visible(n), nonempty: !!n.textContent.trim(), rect: rect(n), position: getComputedStyle(n).position })) });
      } catch (e) { notMeasured.push({ ruleId: rule.id, target: rule.target, stateId, reason: e.message, members }); }
    }
    return { stateId, observations, notMeasured, raw };
  }, { stateId, rules, components, preparation });
}

module.exports = { collectMetrics };
