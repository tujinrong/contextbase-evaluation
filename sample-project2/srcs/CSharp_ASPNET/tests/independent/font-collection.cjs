'use strict';

/** Read computed CSS fonts from an existing Page. No expected values or verdicts. */
async function collectFonts(page, { stateId, ruleDescriptors, componentDescriptors }) {
  if (!page || typeof page.evaluate !== 'function') throw new TypeError('An existing Page is required');
  if (typeof stateId !== 'string' || !stateId) throw new TypeError('stateId is required');
  if (!Array.isArray(ruleDescriptors) || !Array.isArray(componentDescriptors)) {
    throw new TypeError('Descriptor arrays are required');
  }
  // Whitelist the interface; never serialize a contract or an expectation object.
  const rules = ruleDescriptors.map(r => ({ id: r.id, target: r.target, propertyNames: r.propertyNames }));
  const components = componentDescriptors.map(c => ({
    id: c.id, selector: c.selector, state: c.state, kind: c.kind, textCapable: c.textCapable,
  }));
  return page.evaluate(({ stateId: state, rules, components }) => {
    const applies = c => c.state === state || (Array.isArray(c.state) && c.state.includes(state));
    const active = components.filter(applies);
    const fontNames = new Set(['fontFamily', 'fontSize', 'fontUnit']);
    const excluded = new Set(['SCRIPT', 'STYLE', 'TEMPLATE', 'NOSCRIPT', 'OPTION', 'OPTGROUP']);
    const cache = new Map();
    const observations = [];
    const notMeasured = [];

    function hidden(element, style, rect) {
      if (!element.isConnected || element.getClientRects().length === 0 || rect.width <= 0 || rect.height <= 0) return true;
      if (element.tagName === 'INPUT' && element.type === 'hidden') return true;
      for (let e = element; e; e = e.parentElement) {
        const css = e === element ? style : getComputedStyle(e);
        if (e.hidden || css.display === 'none' || css.visibility === 'hidden' || css.visibility === 'collapse' ||
            css.contentVisibility === 'hidden' || Number(css.opacity) === 0) return true;
      }
      return false;
    }

    function textCapability(element) {
      if (element.tagName === 'INPUT') {
        return !['checkbox', 'radio', 'hidden', 'range', 'color', 'image'].includes(element.type);
      }
      if (['BUTTON', 'SELECT', 'TEXTAREA', 'A'].includes(element.tagName)) return true;
      if (element.isContentEditable) return true;
      return Array.from(element.childNodes).some(n => n.nodeType === Node.TEXT_NODE && n.textContent.trim().length > 0);
    }

    function member(element) {
      const tag = element.tagName.toLowerCase();
      const css = getComputedStyle(element);
      const rect = element.getBoundingClientRect();
      const raw = css.fontSize;
      const parsed = /^([+-]?(?:\d+(?:\.\d*)?|\.\d+))([a-z%]+)$/i.exec(raw.trim());
      const number = parsed ? Number(parsed[1]) : null;
      const fontSize = Number.isFinite(number) ? number : null;
      const fontUnit = parsed ? parsed[2] : null;
      return {
        tag, nativeTag: tag, id: element.id || null,
        itemId: element.getAttribute('data-item-id'), role: element.getAttribute('role'),
        inputType: element.tagName === 'INPUT' ? element.type : null,
        textCapable: textCapability(element),
        visible: !hidden(element, css, rect),
        properties: { fontFamily: css.fontFamily, fontSize, fontUnit },
        rawFontSize: raw, fontWeight: css.fontWeight, lineHeight: css.lineHeight,
        rect: { x: rect.x, y: rect.y, width: rect.width, height: rect.height, top: rect.top, right: rect.right, bottom: rect.bottom, left: rect.left },
      };
    }

    function select(selector) {
      if (typeof selector !== 'string' || !selector.trim()) return { nodes: [], members: [], error: 'MISSING_SELECTOR' };
      if (cache.has(selector)) return cache.get(selector);
      let result;
      try {
        const nodes = Array.from(document.querySelectorAll(selector));
        const members = nodes.map(node => {
          try { return member(node); }
          catch (error) { return { tag: node.tagName.toLowerCase(), id: node.id || null, visible: false, measurementError: String(error.message || error) }; }
        });
        result = { nodes, members, error: null };
      } catch (error) {
        result = { nodes: [], members: [], error: 'INVALID_SELECTOR: ' + String(error.message || error) };
      }
      cache.set(selector, result);
      return result;
    }

    for (const rule of rules) {
      const allTargets = components.filter(c => c.id === rule.target);
      const targets = allTargets.filter(applies);
      if (allTargets.length && targets.length === 0) continue;
      if (targets.length !== 1) {
        notMeasured.push({ ruleId: rule.id, target: rule.target, reason: targets.length ? 'AMBIGUOUS_TARGET_DESCRIPTOR' : 'TARGET_NOT_FOUND_IN_STATE', matchedCount: 0, visibleCount: 0, members: [] });
        continue;
      }
      const target = targets[0];
      const selected = select(target.selector);
      const visible = selected.members.filter(m => m.visible);
      const base = { ruleId: rule.id, target: rule.target, matchedCount: selected.nodes.length, visibleCount: visible.length, members: selected.members };
      const reasons = [];
      if (selected.error) reasons.push(selected.error);
      if (!Array.isArray(rule.propertyNames) || rule.propertyNames.length === 0) reasons.push('MISSING_FONT_PROPERTY_NAMES');
      else if (rule.propertyNames.some(p => !fontNames.has(p))) reasons.push('UNSUPPORTED_FONT_PROPERTY');
      if (selected.members.some(m => m.measurementError)) reasons.push('MEMBER_MEASUREMENT_ERROR');
      if (selected.nodes.length === 0) reasons.push('NO_MATCHED_NODES');
      else if (visible.length === 0) reasons.push('NO_VISIBLE_NODES');
      if (visible.some(m => m.properties.fontSize === null || m.properties.fontUnit === null)) reasons.push('FONT_SIZE_NOT_PARSEABLE');
      if (visible.some(m => m.properties.fontUnit !== 'px')) reasons.push('COMPUTED_FONT_UNIT_NOT_PX');
      if (visible.length && ['fontFamily', 'fontSize', 'fontUnit'].some(p => new Set(visible.map(m => m.properties[p])).size !== 1)) reasons.push('NON_UNIFORM_VISIBLE_FONTS');
      if (reasons.length) {
        notMeasured.push({ ...base, reason: [...new Set(reasons)].join('; ') });
        continue;
      }
      observations.push({ ...base, method: 'computed-style', properties: { ...visible[0].properties } });
    }

    const rawInventory = [];
    for (const element of document.querySelectorAll('*')) {
      if (excluded.has(element.tagName) || element.closest('script,style,template,noscript') ||
          (element.tagName === 'INPUT' && element.type === 'hidden')) continue;
      const textCapable = textCapability(element);
      const glyphInput = element.tagName === 'INPUT' && ['checkbox', 'radio'].includes(element.type);
      if (!textCapable && !glyphInput) continue;
      let measured;
      try { measured = member(element); }
      catch (error) { continue; }
      if (!measured.visible) continue;
      // Only a direct selector match covers a text node. Ancestor coverage is insufficient.
      const directMatch = c => {
        const selected = select(c.selector);
        return !selected.error && selected.nodes.includes(element);
      };
      const matchedComponentIds = active.filter(directMatch).map(c => c.id);
      // Cross-state identity hints only. This neither emits a rule observation
      // nor establishes that any other state's preparation was performed.
      const matchedAllComponentIds = components.filter(directMatch).map(c => c.id);
      rawInventory.push({ ...measured, matchedComponentIds, matchedAllComponentIds });
    }
    return { stateId: state, observations, notMeasured, rawInventory };
  }, { stateId, rules, components });
}

module.exports = { collectFonts };
