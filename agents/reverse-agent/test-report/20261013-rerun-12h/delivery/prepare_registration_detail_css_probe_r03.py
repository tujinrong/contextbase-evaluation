"""Prepare a fresh code-only viewport/minimum-column-width probe from fixed prior code."""
from pathlib import Path
import hashlib, json
P=Path(__file__).resolve().parent
src=P/'probe_registration_detail_firstcol_r02.py'
assert hashlib.sha256(src.read_bytes()).hexdigest()=='bd989a23493d8a2fff286380a2d865eeabafaba2bcb01132144e8a2fc9964992'
code=src.read_text(encoding='utf8')
old='CSS=\'table[data-renderer-markdown]:not([data-renderer-columns="1"]):not([data-renderer-columns="2"]) th:first-child,table[data-renderer-markdown]:not([data-renderer-columns="1"]):not([data-renderer-columns="2"]) td:first-child{min-width:12em}\''
new='CSS=\'table[data-renderer-markdown]:not([data-renderer-columns="1"]):not([data-renderer-columns="2"]) th,table[data-renderer-markdown]:not([data-renderer-columns="1"]):not([data-renderer-columns="2"]) td{min-width:8em}table[data-renderer-markdown]:not([data-renderer-columns="1"]):not([data-renderer-columns="2"]) th:first-child,table[data-renderer-markdown]:not([data-renderer-columns="1"]):not([data-renderer-columns="2"]) td:first-child{min-width:12em}\''
assert code.count(old)==1;code=code.replace(old,new)
for old,new in [("'width':1440","'width':2400"),("dims['width']>1440","dims['width']>2400"),("data-delivery-firstcol-probe=\"1\"","data-delivery-firstcol-probe=\"3\"")]:
 assert old in code;code=code.replace(old,new)
measurement="""   token_rows=page.evaluate('''() => {
     const found=[];
     for(const cell of document.querySelectorAll('table[data-renderer-markdown]:not([data-renderer-columns="1"]):not([data-renderer-columns="2"]) th,table[data-renderer-markdown]:not([data-renderer-columns="1"]):not([data-renderer-columns="2"]) td')) {
       const walker=document.createTreeWalker(cell,NodeFilter.SHOW_TEXT);
       for(let node;node=walker.nextNode();) {
         for(const match of node.textContent.matchAll(/(?:[A-Za-z_][A-Za-z0-9_]*|[0-9]+)(?:[-.](?:[A-Za-z_][A-Za-z0-9_]*|[0-9]+))+/g)) {
           const range=document.createRange();range.setStart(node,match.index);range.setEnd(node,match.index+match[0].length);
           const rects=[...range.getClientRects()].filter(r=>r.width>0&&r.height>0);
           const tops=[...new Set(rects.map(r=>Math.round(r.top*10)/10))];
           if(tops.length>1)found.push({token:match[0],cellText:cell.textContent,visibleRowTops:tops,rects:rects.map(r=>({x:r.x,y:r.y,width:r.width,height:r.height}))});
         }
       }
     }
     return found;
   }''')
"""
assert code.count('  finally:browser.close()')==1;code=code.replace('  finally:browser.close()',measurement+'  finally:browser.close()')
code=code.replace("'firstColumnMeasurements':measurements,","'firstColumnMeasurements':measurements,'wholeHyphenDotTokenWrapDiagnostics':token_rows,")
out=P/'probe_registration_detail_columns_r03.py';assert not out.exists();out.write_text(code,encoding='utf8')
compile(code,str(out),'exec')
print(json.dumps({'path':str(out),'sha256':hashlib.sha256(out.read_bytes()).hexdigest(),'bodyAuthored':False,'mainChanged':False}))
