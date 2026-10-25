"""Read-only closure/ABI/input checks; no DB or compiler success is inferred."""
import sys
sys.dont_write_bytecode = True
from pathlib import Path
import re,json,hashlib,datetime,os,sys
ROOT=Path(__file__).resolve().parents[1]
SPEC=ROOT.parent.parent/'spec'/ROOT.name
from output_paths import result_dir,write_json,write_latest
from evidence import compiled_inputs,binary_hashes
from checked_sources import checked_source_hashes
report=result_dir('static',os.environ.get('COBOL_TEST_REPORT_DIR'))
run_id=os.environ.get('COBOL_RUN_ID','local-cobol')
prefix=report/'static'
tested_checked=checked_source_hashes()
tested_inputs=compiled_inputs();tested_binaries=binary_hashes();tested_runner=hashlib.sha256(Path(__file__).read_bytes()).hexdigest();tested_manifest=hashlib.sha256((ROOT/'build/input-manifest.json').read_bytes()).hexdigest()
results=[]
def check(name,good,detail):results.append({'id':name,'passed':bool(good),'detail':detail})
manifest=json.loads((ROOT/'build/input-manifest.json').read_text(encoding='utf-8'))
check('local-spec-lock',bool(manifest['inputs']) and all((ROOT/x['path']).resolve().is_relative_to(SPEC.resolve()) and (ROOT/x['path']).is_file() and hashlib.sha256((ROOT/x['path']).read_bytes()).hexdigest()==x['sha256'] for x in manifest['inputs']),{'count':len(manifest['inputs']),'versions':sorted(set(x['version'] for x in manifest['inputs'] if x['version']))})
programs={p.stem:p.read_text(encoding='utf-8') for p in (ROOT/'cobol').glob('*.cob')}
ctext='\n'.join(p.read_text(encoding='utf-8') for p in (ROOT/'bridge').glob('*.c'))
cfuncs=set(re.findall(r'\b(?:int32_t|void)\s*\*?\s*(ST[A-Z0-9]+)\s*\(',ctext))
calls=sorted({x for text in programs.values() for x in re.findall(r'CALL\s+"([^"]+)"',text,re.I)})
missing=sorted(set(calls)-set(programs)-cfuncs)
check('CALL-closure',not missing,{'productionPrograms':len(programs),'calledTargets':calls,'unresolved':missing,'CFunctions':sorted(cfuncs)})
copies=sorted({x for text in programs.values() for x in re.findall(r'COPY\s+"([^"]+)"',text,re.I)})
check('COPY-closure',all((ROOT/'copy'/x).is_file() for x in copies),copies)
catalog=json.loads((ROOT/'tools/sql-contracts.json').read_text(encoding='utf-8'))
sqlids={p.stem for p in (ROOT/'sql').glob('*.sql')}
commandids={x for text in programs.values() for x in re.findall(r'MOVE\s+"([^"]+)"\s+TO\s+COMMAND-NAME',text)}
commandids.update(f'ST-LIST-{n}{d}' for n in range(1,5) for d in ['A','D'])
check('SQL-closure',commandids<=sqlids,{'catalogCount':len(sqlids),'requested':sorted(commandids),'unresolved':sorted(commandids-sqlids)})
check('SQL-parameter-declarations',len(catalog)==len(sqlids) and all(len(x['columnSizes'])==x['parameters']==(ROOT/x['path']).read_text(encoding='utf-8').count('?') and all(n>0 for n in x['columnSizes']) for x in catalog),{'contractCount':len(catalog),'sqlCount':len(sqlids),'eachCountAndColumnSizeChecked':True})
fields=(ROOT/'tools/abi-schema.json').read_text(encoding='utf-8');abi=json.loads(fields)
check('ABI-fixed-sizes',all(abi[k]==v for k,v in {'pointer':8,'ST_PARAM':24,'ST_DB_REQUEST':976,'ST_DB_RESULT':40,'ST_VALUE':1032}.items()),abi)
check('derived-relationship',all('relationship_category' in (ROOT/'sql'/x).read_text(encoding='utf-8') for x in ['ST-INSERT.sql','ST-UPDATE.sql']) and 'N-VALUE(25)' in programs['STDUP'], 'nullable classification included in persistence and confirmation input hash')
check('full-candidate-scan','PERFORM UNTIL EXIT' in programs['STDUP'] and 'DUP-COUNT <= 20' in programs['STDUP'] and 'K <= 2' in programs['STDUP'], 'all rows count/hash; first20 only copied for display')
check('pending-applied-split','SEARCH-PENDING' in programs['STSRCH'] and 'MOVE SEARCH-RAW TO ST-RAW' in programs['STSRCH'] and 'MOVE SEARCH-PENDING TO ST-RAW' in programs['STSRCH'], 'page/resume applies stored successful conditions and restores pending display values')
check('candidate-no-search-aggregate','COUNT_BIG' not in (ROOT/'sql/CLASS-LIST.sql').read_text() and 'COUNT_BIG' in (ROOT/'sql/CLASS-EDIT.sql').read_text(),'search/registration query variants')
check('native-Text-entry',all(x not in '\n'.join(programs.values()) for x in ['CALL "STHTTP"','CALL "STPOST"','<form','<option','STREDIRECT']), 'Product COBOL uses native Text events; legacy C decoder is not a product entry')
check('Windows-lifecycle',all(x in programs['STMAIN'] for x in ['STSAMPLEOPEN','STAUTH','STSAMPLECLOSE','STTERMOPEN','STTERMCLOSE']) and 'STSAMPLEOPEN' in programs['STMAINT'] and 'STSAMPLECLOSE' in programs['STMAINT'], 'Session/Console lifecycle is explicit; STAUTH checks session')
check('Text-raw-envelope','T-NAME-COUNT' in programs['STTEXTREQ'] and 'SEEN-SLOT' in programs['STTEXTREQ'] and 'STTEXTCHECK' in programs['STTEXTREQ'] and 'T-REQUEST NOT = T-SEQUENCE + 1' in programs['STTEXTREQ'], 'Named allowlists and raw/NULL/length validation precede dispatch')
check('Text-search-fields',all(x in programs['STTEXTREQ'] for x in ['studentNo','name','classId','statusCode']) and 'WHEN 42 WHEN 43 WHEN 44 WHEN 45' in programs['STTEXTREQ'], 'Four search conditions; repeated distinct status slots only')
check('Text-display-window','SEARCH-WINDOW' in programs['STSRCH'] and 'T-DISPLAY-WINDOW' in programs['STEVENT'] and 'T-PICK-COUNT < 6' in programs['STMLOOK'], '4-row result windows and 6-row candidate windows are separate from SQL pages')
check('Text-no-implicit-save','WHEN 13' in programs['STEVENT'] and 'T-SPECIAL-DATA(2)(1:1) = "Y"' in programs['STEVENT'] and 'WHEN 116' in programs['STEVENT'], 'Confirmation requires Y plus fresh F5; Enter does not dispatch save')
check('Text-preserve-raw','IF T-CHANGED NOT = 0' in programs['STEVENT'] and 'STTERMFULL' in programs['STEVENT'] and 'IF T-RC = 1' in programs['STEVENT'], 'Only changed ordinary input or explicit FULL Apply replaces raw')
bad=[]
paths=[p for folder in ['cobol','copy','bridge','sql','assets','tools','deploy','database'] for p in (ROOT/folder).rglob('*') if p.is_file() and p.suffix in ['.cob','.cpy','.c','.h','.py','.mjs','.json','.sql','.md','.js','.css']]
paths += [ROOT/'README.md',ROOT/'IMPLEMENTATION.md',ROOT/'Makefile']
for p in paths:
 if '__pycache__' in p.parts or p.name=='static_check.py':continue
 s=p.read_text(encoding='utf-8')
 for pat in [r'srcs[/\\](?:Shared|Database|_tools|AS400_RPG|CSharp_ASPNET|Vue_CSharpAPI|AccessVBA|VB_NET|VB_WPF|CSharp_WPF)',r'ROOT\.parents\[1\]',r'project[^\n]*[\x22\x27]\.\./\.\./\.\.',r'(?i)spec-eval']:
  if re.search(pat,s):bad.append(p.relative_to(ROOT).as_posix()+': '+pat)
check('project-isolation',not bad,bad)
result={'checkedSourceHashes':tested_checked,'compiledInputs':tested_inputs,'binaryHashes':tested_binaries,'runnerSha256':tested_runner,'inputsUnchangedDuringTests':tested_checked==checked_source_hashes() and tested_inputs==compiled_inputs() and tested_binaries==binary_hashes() and tested_runner==hashlib.sha256(Path(__file__).read_bytes()).hexdigest() and tested_manifest==hashlib.sha256((ROOT/'build/input-manifest.json').read_bytes()).hexdigest(),'status':'PASSED' if all(x['passed'] for x in results) else 'FAILED','runId':run_id,'inputManifest':'build/input-manifest.json','inputManifestSha256':hashlib.sha256((ROOT/'build/input-manifest.json').read_bytes()).hexdigest(),'recordedAt':datetime.datetime.now(datetime.timezone.utc).isoformat(),'profile':'static, not DB/runtime integration','passed':sum(x['passed'] for x in results),'total':len(results),'results':results}
if not result['inputsUnchangedDuringTests']:result['status']='FAILED_OR_INPUT_CHANGED'
write_json(prefix.with_suffix('.json'),result)
write_latest(prefix.with_suffix('.raw.log'),'\n'.join(x['id']+' '+('PASS' if x['passed'] else 'FAIL')+' '+json.dumps(x['detail'],ensure_ascii=False) for x in results)+'\n')
print(f"{result['passed']}/{result['total']} static checks passed")
raise SystemExit(0 if result['status']=='PASSED' else 1)
