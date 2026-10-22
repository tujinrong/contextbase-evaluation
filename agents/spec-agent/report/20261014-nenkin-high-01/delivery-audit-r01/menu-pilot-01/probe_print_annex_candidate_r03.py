"""Small code/metadata-only review of the actual pagination remedy candidate."""
import ast,copy,hashlib,json,sys,types
from pathlib import Path
D=Path('D:/開発/contextbase-evaluation/agents/spec-agent/.tmp/20261014-nenkin-high-01/delivery')
Q=Path('D:/開発/contextbase-evaluation/agents/spec-agent/report/20261014-nenkin-high-01/delivery-audit-r01/menu-pilot-01')
def load(name):
    p=D/name;module_name='technical_probe_'+p.stem;mod=types.ModuleType(module_name);sys.modules[module_name]=mod;ns=mod.__dict__;ns['__file__']=str(p)
    exec(compile(p.read_bytes(),str(p),'exec'),ns);return ns
annex=load('prepare_native_print_annex_r02.py');connector=load('connect_print_metadata_v2_62_r04.py')
checks=[]
def reject(name,fn):
    try:fn()
    except (ValueError,TypeError,KeyError):checks.append({'name':name,'expected':'reject','actual':'reject'});return
    raise AssertionError('negative accepted: '+name)
sheet={'name':'章','role':'normal','columns':62,'lastRow':10,'gridColumnWidth':3,'printArea':'A1:BJ10',
       'operations':[{'range':'A1:BJ1','value':'T','style':'title'},{'range':'B3:BJ3','value':'P','style':'body'},{'range':'B10:BJ10','value':'Q','style':'body'}],
       'images':[{'kind':'diagram','id':'diagram-001','row':3,'height':100,'displayHeight':100,'sha256':'a'*64}],
       'rowHeights':{str(r):15 for r in range(1,11)}}
original={'documents':[{'documentId':'SYNTHETIC','sheets':[sheet]}]}
assert annex['print_projection'](original)[0][0]['printRanges']==['A1:BJ3','A9:BJ10']
checks.append({'name':'blank-only exclusion/order positive','expected':'accept','actual':'accept'})
for value in ('payload',''):
    altered=copy.deepcopy(original);altered['documents'][0]['sheets'][0]['operations'].append({'range':'B6:BJ6','value':value})
    reject('used image reservation row including blank operation '+repr(value),lambda a=altered:annex['print_projection'](a))
altered=copy.deepcopy(original);del altered['documents'][0]['sheets'][0]['rowHeights']['7']
reject('missing explicit row height',lambda:annex['print_projection'](altered))
receipt={'sourceModel':{'path':'synthetic','sha256':'b'*64},'directory':'synthetic','tiles':[]}
projected=copy.deepcopy(original);projected['nativePrintAnnex']={'schema':'native-print-annex/1','sourceModel':receipt['sourceModel'],'directory':'synthetic','originalSheetsUnchanged':True,'originalPrimaryPrintHoldRetained':True}
annex['append_only'](original,projected,receipt);checks.append({'name':'original sheet deep identity positive','expected':'accept','actual':'accept'})
for name,mutate in [('cell text drift',lambda p:p['documents'][0]['sheets'][0]['operations'][0].update(value='OTHER')),
                    ('source image SHA drift',lambda p:p['documents'][0]['sheets'][0]['images'][0].update(sha256='c'*64)),
                    ('normal columns drift',lambda p:p['documents'][0]['sheets'][0].update(columns=63)),
                    ('new business body field',lambda p:p.update(businessBody='added'))]:
    altered=copy.deepcopy(projected);mutate(altered)
    reject(name,lambda a=altered:annex['append_only'](original,a,receipt))
item={'ordinal':0,'name':'章','kind':'normal','columns':62,'lastRow':10,'printRanges':['A1:BJ3','A9:BJ10']}
assert connector['print_areas'](item)==item['printRanges'];checks.append({'name':'bounded ordered multi-area positive','expected':'accept','actual':'accept'})
for name,ranges in [('overlap',['A1:BJ3','A3:BJ10']),('narrow columns',['A1:BI3']),('no original header',['A2:BJ10']),('out of range',['A1:BJ11']),('reversed range',['A1:BJ3','A9:BJ8'])]:
    altered={**item,'printRanges':ranges};reject(name,lambda a=altered:connector['print_areas'](a))
for height in [1,778,1069,1200,1251,1713,1721]:
    starts=annex['origins'](height);assert starts[0]==0 and starts[-1]+900>=height
    assert all(a+900-b>=320 for a,b in zip(starts,starts[1:]))
checks.append({'name':'native tile complete extent and minimum320px overlap','expected':'accept','actual':'accept'})
def functions(path):return {n.name:ast.dump(n,include_attributes=False) for n in ast.parse(path.read_bytes()).body if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef))}
old=functions(D/'connect_print_metadata_v2_62_r03.py');new=functions(D/'connect_print_metadata_v2_62_r04.py')
changes=sorted(k for k,v in old.items() if new[k]!=v);assert changes==['connect_bytes','main','patch_workbook']
assert set(new)-set(old)=={'print_areas','validate_annex_plan'}
baseline=(D/'build_xlsx_v2_62_r06.mjs').read_text(encoding='utf8');candidate=(D/'build_xlsx_v2_62_r07.mjs').read_text(encoding='utf8')
start=candidate.index('const ANNEX_HELPER=');end=candidate.index('if(model.formatProfile?',start)
inverse=candidate[:start]+candidate[end:]
inverse=inverse.replace(',nativePrintAnnex:annexVerified','').replace('  await verifyPrintAnnex();\n','')
inverse=inverse.replace('await readImage(image);',"await readPinned(image.path,image.sha256,'image');")
inverse=inverse.replace('const bytes=await readImage(image);',"const bytes=await readPinned(image.path,image.sha256,'image');")
assert inverse==baseline
source_model=D/'menu-pilot-01/model.json';model_raw=source_model.read_bytes();assert hashlib.sha256(model_raw).hexdigest()=='60d95146cd9ea57e1afb618926147be954ef1aaa7cefb3dbe7c7f6099a162d48'
model=json.loads(model_raw);actual=annex['print_projection'](model)
report={'schema':'print-annex-candidate-code-metadata-review/1','scope':'CODE_AND_METADATA_ONLY','checks':checks,'checksPassed':len(checks),
        'actualModelSha256':hashlib.sha256(model_raw).hexdigest(),'actual425OriginalOperationsCovered':sum(len(s['operations']) for d in model['documents'] for s in d['sheets'])==425,
        'actualSourcePrintProjection':actual,'actualTilesPlanned':sum(len(annex['origins'](i['height'])) for d in model['documents'] for s in d['sheets'] for i in s['images'] if i['kind']=='diagram'),
        'builderInverseRestoresOriginal6Bytes':True,'connectorModifiedFunctions':changes,'legacyXmlParserSpliceZipRewriterUnchangedAst':True,
        'files':[{ 'path':str(D/n),'sha256':hashlib.sha256((D/n).read_bytes()).hexdigest()} for n in ['prepare_native_print_annex_r02.py','build_xlsx_v2_62_r07.mjs','connect_print_metadata_v2_62_r04.py','verify_original_sheets_append_only_r01.py']],
        'actualPngCropsPrepared':False,'actualArtifactWorkbookAuthoring':False,'providerExecuted':False,'markerExecuted':False,'nativeQualification':False,
        'limitations':['Actual overlapping PNG crops, original-sheet XLSX equality and all actual Excel print pages remain unperformed.',
                       'Full pixel coverage does not prove every label is whole in a printed tile; actual original-size print review is mandatory.',
                       'Sparse Print_Area must actually omit only image-reservation rows while retaining all425 source cells; no success is inferred from metadata.']}
out=Q/'print-annex-candidate-code-metadata-review-r03.json';assert not out.exists();out.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print(json.dumps({'path':str(out),'sha256':hashlib.sha256(out.read_bytes()).hexdigest(),'checks':len(checks),'actualTilesPlanned':report['actualTilesPlanned']},ensure_ascii=False))
