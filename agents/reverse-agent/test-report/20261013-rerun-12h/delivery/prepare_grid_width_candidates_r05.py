"""Prepare width-only candidates and record actual focal views; no body authoring."""
from pathlib import Path
from datetime import datetime,timezone
import copy,hashlib,json
P=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
rp=P/'grid-columnwidth-probe-r04-excel/result.json';r=json.loads(rp.read_text(encoding='utf8'))
assert r['workbookBytesUnchanged'] and r['planBytesUnchanged'] and r['readOnly']
assert not r['saved'] and not r['cellsOrFormatsChanged'] and len(r['sheets'])==len(r['cells'])==14
pp=Path(r['plan']);plan=json.loads(pp.read_text(encoding='utf8'))
for a,b in zip(plan['cells'],r['cells']):
    assert (a['sheet'],a['cell'],a['value'])==(b['sheet'],b['cell'],b['value2']) and b['value2Type']=='System.String'
pins={str(rp):sha(rp),str(pp):sha(pp),r['workbook']:r['beforeSha256']};views=[]
for n,c in enumerate(r['sheets']):
    pins[c['png']]=c['pngSha256'];views.append({**c,'captureIndexZeroBased':n,'actuallyReviewed':True,'actuallyViewedBy':'delivery_tools','view':'original pixels'})
changes=[]
configs=[('registration-detail','model-assisted-registration-detail-r19-r01.json','f1b66ddcb1b0924cd9e0889d9ed9c8035963df69ccc7576b237ffb3c0178558d',21,12),
    ('code-design','model-assisted-code-design-r19-r01.json','8dc0471e51bab71502972e20c2b3b79b9c06b6e4f30aff6ced3e679f36ce6b70',41,4)]
for role,name,expected,column,width in configs:
    path=P/name;assert sha(path)==expected;pins[str(path)]=expected
    original=json.loads(path.read_text(encoding='utf8'));candidate=copy.deepcopy(original)
    sheet=next(s for s in candidate['documents'][0]['sheets'] if s['name']=='イベント仕様')
    assert sheet['columns']==120 and 'columnWidths' not in sheet
    sheet['columnWidths']=[2]*120;sheet['columnWidths'][column-1]=width
    restored=copy.deepcopy(candidate);del next(s for s in restored['documents'][0]['sheets'] if s['name']=='イベント仕様')['columnWidths']
    assert restored==original
    target=P/f'model-assisted-{role}-r19-r02-widthonly.json';assert not target.exists()
    target.write_text(json.dumps(candidate,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    changes.append({'role':role,'sourceModel':str(path),'sourceModelSha256':expected,'candidateModel':str(target),'candidateModelSha256':sha(target),
        'sheet':'イベント仕様','columnIndexOneBased':column,'before':2,'after':width,'restoringOnlyColumnGeometryExactlyEqualsOriginalModel':True,
        'allBodyLiteralsRowsMergeStylesTablesImagesOrderUnchanged':True})
assert all(sha(p)==h for p,h in pins.items())
record={'schema':'reverse-agent-column-geometry-projection/3','createdUtc':datetime.now(timezone.utc).isoformat(),
    'scope':'UNCHANGED_LITERAL_PINNED_GRID_COLUMN_WIDTH_ONLY_FOCAL_PROBE','actualNativeViews':views,'changes':changes,
    'findings':[{'fixture':'F1','sourceCell':'イベント仕様!U200','token':'EV-REG-001','widths':[2,4,8],'status':'HOLD_IDENTIFIER_WRAP'},
        {'fixture':'F1','sourceCell':'イベント仕様!U200','token':'EV-REG-001','widths':[12,24,60,160],'status':'PASS_FOCAL_WHOLE_IDENTIFIER_ONLY'},
        {'fixture':'F2','sourceCell':'イベント仕様!AO100','token':'1900-01-01','widths':[2],'status':'HOLD_DATE_HYPHEN_WRAP'},
        {'fixture':'F2','sourceCell':'イベント仕様!AO100','token':'1900-01-01','widths':[4,8,12,24,60,160],'status':'PASS_FOCAL_WHOLE_DATE_ONLY'}],
    'selectedWidthReason':'Smallest tested width preserving each entire focal token on one visible row. Full candidate review remains pending.',
    'beforeAfterPins':pins,'allPinsUnchanged':True,'oldHoldsPreserved':True,'clipboardTemporaryWriteSideEffect':True,'priorClipboardReadOrOutput':False,
    'excelSaved':False,'fullCandidateNativeReview':'PENDING','wholeApproval':False,'formalApproval':False,'published':False,'businessContentAuthored':False}
out=P/'grid-columnwidth-probe-r04-actual-review.json';assert not out.exists();out.write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print(json.dumps({'review':str(out),'reviewSha256':sha(out),'models':changes},ensure_ascii=False))
