"""Native-design geometry check, not a screenshot or font/input acceptance test."""
from pathlib import Path
import importlib.util,json
root=Path(__file__).resolve().parents[1]; spec=importlib.util.spec_from_file_location('forms',root/'src/forms/definitions.py'); forms=importlib.util.module_from_spec(spec); spec.loader.exec_module(forms)
checks=[]
def intersects(a,b): return a[0]<b[0]+b[2] and b[0]<a[0]+a[2] and a[1]<b[1]+b[3] and b[1]<a[1]+a[3]
for name,form in forms.FORMS.items():
    defects=[]
    for c in form['controls']:
        if c['kind'] not in (109,111,106): continue
        x=c.get('label_x',max(450,c['x']-2250)); w=c.get('label_w',min(2100,c['x']-x-150)); rect=(x,c['y']+30,w,430)
        for other in form['controls']:
            if other['kind']==123 or c.get('page')!=other.get('page'): continue
            if intersects(rect,(other['x'],other['y'],other['w'],other['h'])): defects.append(c['name']+' label / '+other['name'])
    checks.append({'id':name+'-field-labels','status':'PASS' if not defects else 'FAIL','defects':defects})
    for c in form['controls']:
        if c['kind']!=110: continue
        widths=list(map(int,c['widths'].split(';'))); expected=sum(widths)
        checks.append({'id':name+'.'+c['name']+'-headers','status':'PASS' if len(c.get('headers',[]))==c['columns'] and expected<=c['w'] else 'FAIL','visibleWidthsTwips':widths,'listWidthTwips':c['w']})
out={'checks':checks,'scope':'Twips rectangles and column/header mapping only; actual render is a separate root UI observation','formalScore':None}
(root/'build/test-results/layout.json').write_text(json.dumps(out,indent=2),encoding='utf-8'); print(json.dumps(out)); raise SystemExit(int(any(c['status']!='PASS' for c in checks)))
