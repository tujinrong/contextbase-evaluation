"""Read-only closure/ABI/input checks; no DB or compiler success is inferred."""
from pathlib import Path
import re,json,hashlib,datetime,os,sys
ROOT=Path(__file__).resolve().parents[1]
report=Path(os.environ.get('COBOL_TEST_REPORT_DIR',ROOT/'test-report')).resolve();report.mkdir(parents=True,exist_ok=True)
run_id=os.environ.get('COBOL_RUN_ID','local-cobol')
prefix=report/f'{run_id}-{sys.argv[1]}-static'
if prefix.with_suffix('.json').exists():raise SystemExit('Existing report preserved')
results=[]
def check(name,good,detail):results.append({'id':name,'passed':bool(good),'detail':detail})
manifest=json.loads((ROOT/'build/input-manifest.json').read_text(encoding='utf-8'))
check('local-spec-lock',all(hashlib.sha256((ROOT/x['path']).read_bytes()).hexdigest()==x['sha256'] for x in manifest['inputs']),{'count':len(manifest['inputs']),'versions':sorted(set(x['version'] for x in manifest['inputs'] if x['version']))})
programs={p.stem:p.read_text(encoding='utf-8') for p in (ROOT/'cobol').glob('*.cob')}
ctext=(ROOT/'bridge/student_bridge.c').read_text(encoding='utf-8')
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
check('deferred-CGI-header','STOUTPUTBEGIN' in programs['STRENDER'] and 'STOUTPUTEND' in programs['STRENDER'], 'lookup I/O finishes before header is sent')
bad=[]
paths=[p for folder in ['cobol','copy','bridge','sql','assets','tools','deploy','database'] for p in (ROOT/folder).rglob('*') if p.is_file() and p.suffix in ['.cob','.cpy','.c','.h','.py','.mjs','.json','.sql','.md','.js','.css']]
paths += [ROOT/'README.md',ROOT/'IMPLEMENTATION.md',ROOT/'Makefile']
for p in paths:
 if '__pycache__' in p.parts or p.name=='static_check.py':continue
 s=p.read_text(encoding='utf-8')
 for pat in [r'srcs[/\\](?:Shared|Database|_tools|AS400_RPG|CSharp_ASPNET|Vue_CSharpAPI|AccessVBA|VB_NET|VB_WPF|CSharp_WPF)',r'ROOT\.parents\[1\]',r'project[^\n]*[\x22\x27]\.\./\.\./\.\.',r'(?i)spec-eval']:
  if re.search(pat,s):bad.append(p.relative_to(ROOT).as_posix()+': '+pat)
check('project-isolation',not bad,bad)
result={'runId':run_id,'inputManifest':'build/input-manifest.json','inputManifestSha256':hashlib.sha256((ROOT/'build/input-manifest.json').read_bytes()).hexdigest(),'recordedAt':datetime.datetime.now(datetime.timezone.utc).isoformat(),'profile':'static, not DB/runtime integration','passed':sum(x['passed'] for x in results),'total':len(results),'results':results}
prefix.with_suffix('.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
prefix.with_suffix('.raw.log').write_text('\n'.join(x['id']+' '+('PASS' if x['passed'] else 'FAIL')+' '+json.dumps(x['detail'],ensure_ascii=False) for x in results)+'\n',encoding='utf-8')
print(f"{result['passed']}/{result['total']} static checks passed")
raise SystemExit(0 if result['passed']==result['total'] else 1)
