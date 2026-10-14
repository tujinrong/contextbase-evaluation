"""Create fresh candidate-only visibility/finite geometry delta; old files immutable."""
from pathlib import Path
HERE=Path(__file__).resolve().parent
gate=(HERE/'node_label_row_gate_r03.py').read_text(encoding='utf8')
gate=gate.replace('import re\n','import re\nimport math\n')
gate=gate.replace("    def handle_decl(self, decl):\n", "    def handle_pi(self, data):\n        raise NodeLabelProofError('Unsupported node-label processing instruction')\n\n    def handle_decl(self, decl):\n")
needle="def _contains(outer, inner, tolerance=1.5):\n"
insert="""def _rectangle(bounds):
    if not isinstance(bounds, dict):
        raise NodeLabelProofError('SVG rectangle missing')
    for key in ('x', 'y', 'width', 'height'):
        value = bounds.get(key)
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
            raise NodeLabelProofError('SVG rectangle contains nonfinite or nonnumeric coordinates')
    if bounds['width'] <= 0 or bounds['height'] <= 0:
        raise NodeLabelProofError('SVG rectangle has no positive visible area')


def _contains(outer, inner, tolerance=1.5):
    _rectangle(outer)
    _rectangle(inner)
"""
assert gate.count(needle)==1;gate=gate.replace(needle,insert)
needle="    expected = {}\n";assert gate.count(needle)==1;gate=gate.replace(needle,"    _rectangle(canvas)\n    expected = {}\n")
needle="        node = actual[key]\n";assert gate.count(needle)==1;gate=gate.replace(needle,"        node = actual[key]\n        _rectangle(node.get('bounds'))\n")
needle="            if _compact(text):\n";assert gate.count(needle)==1;gate=gate.replace(needle,"            _rectangle(bounds)\n            if _compact(text):\n                if row.get('effectiveVisible') is not True:\n                    raise NodeLabelProofError('SVG row effective ancestor/fill visibility not proven')\n")
target=HERE/'node_label_row_gate_r05.py';assert not target.exists();target.write_text(gate,encoding='utf8')
probe=(HERE/'probe_node_row_gate_r04.py').read_text(encoding='utf8')
probe=probe.replace('from node_label_row_gate_r03','from node_label_row_gate_r05').replace("OUT=HERE/'node-token-row-gate-probe-r04'","OUT=HERE/'node-token-row-gate-probe-r05'").replace("HERE/'node_label_row_gate_r03.py'","HERE/'node_label_row_gate_r05.py'")
old="opacity:getComputedStyle(r).opacity"
new="opacity:getComputedStyle(r).opacity,effectiveVisible:(()=>{const own=getComputedStyle(r);if(own.fill==='none'||Number(own.fillOpacity)<=0)return false;for(let a=r;a;a=a.parentElement){const s=getComputedStyle(a);if(s.display==='none'||s.visibility!=='visible'||!Number.isFinite(Number(s.opacity))||Number(s.opacity)<=0)return false;if(a===svg)break}return true})()"
assert probe.count(old)==1;probe=probe.replace(old,new)
target=HERE/'probe_node_row_gate_r05.py';assert not target.exists();target.write_text(probe,encoding='utf8')
tests=(HERE/'test_node_label_row_gate_r04.py').read_text(encoding='utf8').replace('from node_label_row_gate_r03','from node_label_row_gate_r05')
tests=tests.replace("'visibility':'visible','display':'inline','opacity':1}","'visibility':'visible','display':'inline','opacity':1,'effectiveVisible':True}")
tests=tests.replace("if __name__=='__main__':unittest.main(verbosity=2)","")
target=HERE/'test_node_label_row_gate_r05.py';assert not target.exists();target.write_text(tests,encoding='utf8')
