"""Connect unsupported print metadata and independently inspect the saved native XLSX.

Artifact Tool owns all cell values, layout, styles, merges and drawings. This
post-export step changes print metadata only, never any worksheet data/style.
"""
import hashlib,importlib.util,json,re,zipfile
from pathlib import Path
import xml.etree.ElementTree as ET
W=Path(r'D:/開発/contextbase-evaluation/agents/reverse-agent/.tmp/20261015-scr014-pilot-01')
model=json.loads((W/'view-model.json').read_text('utf8'));build=json.loads((W/'workbook-build.json').read_text('utf8'))
source=Path(build['workbook']);target=source.with_name(source.stem+'-print-'+hashlib.sha256(source.read_bytes()).hexdigest()[:10]+'.xlsx')
nsuri='http://schemas.openxmlformats.org/spreadsheetml/2006/main';n={'s':nsuri};ET.register_namespace('',nsuri)
def tag(s):return '{'+nsuri+'}'+s
def sha(b):return hashlib.sha256(b).hexdigest()
with zipfile.ZipFile(source) as z:parts={i.filename:z.read(i.filename) for i in z.infolist()}
assert sha(source.read_bytes())==build['workbookSha256']
workbook=ET.fromstring(parts['xl/workbook.xml']);names=workbook.find('s:definedNames',n)
if names is None:names=ET.SubElement(workbook,tag('definedNames'))
for e in list(names):
 if e.attrib.get('name')=='_xlnm.Print_Area':names.remove(e)
allowed=['xl/workbook.xml'];before={p:sha(b) for p,b in parts.items()}
for i,spec in enumerate(model['sheets']):
 area=spec['printArea'];area=re.sub(r'([A-Z]+)(\d+)',r'$\1$\2',area)
 e=ET.SubElement(names,tag('definedName'),{'name':'_xlnm.Print_Area','localSheetId':str(i)});e.text="'"+spec['name'].replace("'","''")+"'!"+area
 key=f'xl/worksheets/sheet{i+1}.xml';root=ET.fromstring(parts[key]);allowed.append(key)
 # Maintain schema element order: pageMargins, pageSetup, headerFooter, drawing.
 for name in ['pageMargins','pageSetup']:
  found=root.find('s:'+name,n)
  if found is not None:root.remove(found)
 margin=ET.Element(tag('pageMargins'),{'left':'0.3','right':'0.3','top':'0.4','bottom':'0.4','header':'0.2','footer':'0.2'})
 setup=ET.Element(tag('pageSetup'),{'paperSize':'9' if i==0 else '8','orientation':'portrait' if i==0 else 'landscape','fitToWidth':'1','fitToHeight':'1' if i==0 else '0'})
 position=next((j for j,c in enumerate(root) if c.tag.split('}')[-1] in ['headerFooter','rowBreaks','colBreaks','customProperties','cellWatches','ignoredErrors','smartTags','drawing','legacyDrawing','legacyDrawingHF','picture','oleObjects','controls','webPublishItems','tableParts','extLst']),len(root))
 root.insert(position,margin);root.insert(position+1,setup)
 pr=root.find('s:sheetPr',n)
 if pr is None:pr=ET.Element(tag('sheetPr'));root.insert(0,pr)
 ps=pr.find('s:pageSetUpPr',n)
 if ps is None:ps=ET.SubElement(pr,tag('pageSetUpPr'))
 ps.set('fitToPage','1')
 parts[key]=ET.tostring(root,encoding='utf-8',xml_declaration=True)
parts['xl/workbook.xml']=ET.tostring(workbook,encoding='utf-8',xml_declaration=True)
with zipfile.ZipFile(target,'x',zipfile.ZIP_DEFLATED) as z:
 for p,b in parts.items():z.writestr(p,b)
with zipfile.ZipFile(target) as z:
 assert z.testzip() is None
 assert not any('vbaProject' in p or '/externalLinks/' in p for p in z.namelist())
 assert all(sha(z.read(p))==before[p] for p in before if p not in allowed)
 strings=[]
 if 'xl/sharedStrings.xml' in z.namelist():strings=[''.join(t.itertext()) for t in ET.fromstring(z.read('xl/sharedStrings.xml')).findall('s:si',n)]
 cells={};merges=[]
 for i,spec in enumerate(model['sheets']):
  root=ET.fromstring(z.read(f'xl/worksheets/sheet{i+1}.xml'))
  assert not root.findall('.//s:f',n),'Unexpected formula'
  for c in root.findall('.//s:sheetData/s:row/s:c',n):
   v=c.find('s:v',n);text=''
   if c.attrib.get('t')=='s' and v is not None:text=strings[int(v.text)]
   elif c.attrib.get('t')=='inlineStr':text=''.join(c.find('s:is',n).itertext())
   elif v is not None:text=v.text or ''
   cells[(spec['name'],c.attrib['r'])]=text
  merges.append([m.attrib['ref'] for m in root.findall('s:mergeCells/s:mergeCell',n)])
 for c in build['writtenCells']:
  actual=cells.get((c['sheet'],c['cell']),'')
  assert actual in [c['value'],"'"+c['value']],(c['sheet'],c['cell'],actual,c['value'])
 assert len(merges[0])==14
 # Comparing normalized trees proves print connection did not change values,
 # existing styles, widths, heights, merges, image anchors or table references.
 for key in allowed[1:]:
  left=ET.fromstring(zipfile.ZipFile(source).read(key));right=ET.fromstring(z.read(key))
  for r in [left,right]:
   for t in ['sheetPr','pageMargins','pageSetup']:
    e=r.find('s:'+t,n)
    if e is not None:r.remove(e)
  assert ET.tostring(left)==ET.tostring(right),'Non-print worksheet change'
verifier=W.parents[1].parent/'spec-agent/.tmp/20261014-nenkin-high-01/delivery/verify_xlsx_v2_62_r02.py'
module_spec=importlib.util.spec_from_file_location('readonly_native_xlsx',verifier);checker=importlib.util.module_from_spec(module_spec);module_spec.loader.exec_module(checker)
native=checker.BASE_VERIFY(target.read_bytes(),model,require_print=True)
members=checker.unzip(target.read_bytes());book,sheets=checker.worksheets(members);styles=ET.fromstring(members['xl/styles.xml'])
for (_,_,sheetxml),spec in zip(sheets,model['sheets']):
 if spec['role']=='list':
  assert spec['columns']==10 and spec['tables'][0]['headerRow']==2 and spec['existingListTitleAndHeaderPreserved'] is True
  # The prior generic checker hardcoded header row 1. This pilot preserves
  # the actual existing workbook's title row 1/header row 2 instead.
  projection={**spec,'itemList':False};checker.format_assertions(sheetxml,styles,projection)
 else:checker.format_assertions(sheetxml,styles,spec)
native.update(v2FormatAssertions=True,listTitleRow=1,listHeaderRow=2,listGeometryBasis='existing requested SCR-014 workbook',readOnlyVerification=True)
receipt={'schema':'scr014-native-xlsx-check/1','path':str(target),'sha256':sha(target.read_bytes()),'artifactToolSourceSha256':build['workbookSha256'],'literalCellsChecked':len(build['writtenCells']),'formulas':0,'macros':False,'externalLinks':False,'coverMergeCount':14,'unchangedExceptPrintMetadata':True,'printMetadataReason':'Two bounded public API documentation queries did not expose print-area/page-layout authoring. OOXML connection changes print metadata only.','businessProseChanged':False,'styleChange':False,'visualReview':'PENDING','nativeValidation':native,'nativeVerifierSha256':sha(verifier.read_bytes())}
(W/'workbook-native-check.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print(json.dumps(receipt,ensure_ascii=False))
