"""Create fresh synthetic visibility fixtures; no main/frozen/body edits."""
from pathlib import Path
import hashlib
P=Path(__file__).resolve().parent
old=P/'measure_node_rows_r05.js'
new=P/'measure_node_rows_r06.js'
assert not new.exists()
s=old.read_text(encoding='utf8')
anchor="    if (own.fill === 'none' || !Number.isFinite(Number(own.fillOpacity)) || Number(own.fillOpacity) <= 0) return false;"
assert s.count(anchor)==1
replacement="""    const fill = own.fill.trim().toLowerCase();
    const rgba = /^rgba\\(.*[,/]\\s*([0-9.]+)%?\\s*\\)$/.exec(fill);
    if (fill === 'none' || fill === 'transparent' ||
        (rgba && (!Number.isFinite(Number(rgba[1])) || Number(rgba[1]) <= 0)) ||
        !Number.isFinite(Number(own.fillOpacity)) || Number(own.fillOpacity) <= 0) return false;"""
new.write_text(s.replace(anchor,replacement),encoding='utf8')
old_probe=(P/'probe_effective_node_visibility_r05.py').read_text(encoding='utf8')
old_cases="cases=[('normal','','',False),('ancestor-opacity-zero','opacity:0','',True),('inherited-fill-none','fill:none','',True),('ancestor-hidden','visibility:hidden','',True),('ancestor-display-none','display:none','',True),('explicit-visible-fill-override','fill:none','fill:black',False),('ancestor-partial-opacity','opacity:0.4','',False)]"
assert old_probe.count(old_cases)==1
for version,expected in [('r05-gap',False),('r06',True)]:
    target=P/f'probe_effective_node_fill_{version}.py'
    assert not target.exists()
    text=old_probe.replace("OUT=HERE/'node-effective-visibility-probe-r05.json'",f"OUT=HERE/'node-effective-fill-probe-{version}.json'")
    text=text.replace(old_cases,f"cases=[('fill-transparent','','fill:transparent',{expected}),('fill-rgba-alpha-zero','','fill:rgba(17,34,51,0)',{expected}),('fill-rgba-partial','','fill:rgba(17,34,51,0.4)',False)]")
    if version=='r06':text=text.replace("MEASURE=HERE/'measure_node_rows_r05.js'","MEASURE=HERE/'measure_node_rows_r06.js'")
    target.write_text(text,encoding='utf8')
print({'measurementSha256':hashlib.sha256(new.read_bytes()).hexdigest()})
