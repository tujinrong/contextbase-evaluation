svg => {
  const rect = node => {
    const r = node.getBoundingClientRect();
    return {x:r.x,y:r.y,width:r.width,height:r.height};
  };
  const visible = row => {
    const own = getComputedStyle(row);
    const fill = own.fill.trim().toLowerCase();
    const rgba = /^rgba\(.*[,/]\s*([0-9.]+)%?\s*\)$/.exec(fill);
    if (fill === 'none' || fill === 'transparent' ||
        (rgba && (!Number.isFinite(Number(rgba[1])) || Number(rgba[1]) <= 0)) ||
        !Number.isFinite(Number(own.fillOpacity)) || Number(own.fillOpacity) <= 0) return false;
    for (let ancestor=row; ancestor; ancestor=ancestor.parentElement) {
      const style=getComputedStyle(ancestor);
      if (style.display === 'none' || style.visibility !== 'visible' ||
          !Number.isFinite(Number(style.opacity)) || Number(style.opacity) <= 0) return false;
      if (ancestor === svg) break;
    }
    return true;
  };
  return {canvas:rect(svg),nodes:[...svg.querySelectorAll('g.node')].map(node => ({
    id:node.id,bounds:rect(node),rows:[...node.querySelectorAll('tspan.text-outer-tspan')].map(row => ({
      text:row.textContent,bounds:rect(row),display:getComputedStyle(row).display,
      visibility:getComputedStyle(row).visibility,opacity:getComputedStyle(row).opacity,
      fill:getComputedStyle(row).fill,fillOpacity:getComputedStyle(row).fillOpacity,
      effectiveVisible:visible(row)
    }))
  }))};
}
