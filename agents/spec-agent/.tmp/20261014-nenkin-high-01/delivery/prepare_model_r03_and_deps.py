"""Prepare complete blank-cover slots and bind authorized analysis-only parser dependencies."""
import ast,hashlib,importlib,json,os,sys
from pathlib import Path
from datetime import datetime,timezone
sys.dont_write_bytecode=True
R=Path(r'D:\開発\contextbase-evaluation')
D=R/'agents/spec-agent/.tmp/20261014-nenkin-high-01/delivery'
O=R/'agents/spec-agent/report/20261014-nenkin-high-01/delivery-audit-r01'
DEPS=R/'agents/reverse-agent/.tmp/20261013-rerun-12h/engine-runtime-deps'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert os.environ.get('PYTHONPATH')==str(DEPS)
assert all('input' not in Path(p).parts for p in sys.path if p)
loaded={}
for name in ('bs4','markdown_it','mdurl','soupsieve','typing_extensions'):
    module=importlib.import_module(name);p=Path(module.__file__).resolve()
    assert p.is_relative_to(DEPS.resolve()),(name,p)
    folder=p.parent if p.name=='__init__.py' else p
    files={}
    for q in (sorted(folder.rglob('*')) if folder.is_dir() else [folder]):
        if q.is_file() and '__pycache__' not in q.parts and q.suffix not in {'.pyc','.pyo'}:
            assert not q.is_symlink() and not(getattr(q.lstat(),'st_file_attributes',0)&0x400)
            files[str(q)]=sha(q)
    loaded[name]={'loadedFile':str(p),'loadedFileSha256':sha(p),'version':getattr(module,'__version__',None),'nonCacheFiles':files}
from importlib.metadata import version
versions={name:version(name) for name in ('beautifulsoup4','markdown-it-py','mdurl','soupsieve','typing_extensions')}
dep_record={'schema':'spec-agent-analysis-only-dependency-receipt/1','createdUtc':datetime.now(timezone.utc).isoformat(),'python':sys.executable,'pythonVersion':sys.version,'pythonPath':os.environ['PYTHONPATH'],'inputInPythonPath':False,'authorizedMissingCapability':'Markdown token parsing and inert HTML extraction only; no XLSX authoring','modules':loaded,'distributionVersions':versions,'dependencyDirectoryModified':False,'artifactJsAuthorUsesTheseDependencies':False,'businessInputRead':False,'providerExecuted':False,'artifactToolExecuted':False,'markerExecuted':False}
dp=O/'analysis-dependencies-r01.json'
with dp.open('x',encoding='utf-8') as f:json.dump(dep_record,f,ensure_ascii=False,indent=2);f.write('\n')
src=D/'delivery_model_v2_62_r02.py';before=sha(src);text=src.read_text(encoding='utf-8')
old='for i, values in enumerate(attrs[:3]):';new="for i, values in enumerate((attrs + [['',''],['',''],['','']])[:3]):"
assert text.count(old)==1
text=text.replace(old,new,1);ast.parse(text)
target=D/'delivery_model_v2_62_r03.py'
with target.open('x',encoding='utf-8') as f:f.write(text)
spec=importlib.util.spec_from_file_location('format_model_probe_only',target);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
def markdown(count):
    meta={'schema':'spec-md/1.0','documentId':'TOY-001','version':'1.0','path':'toy.md','sheets':[{'heading':'概要','kind':'GRID','sheet':'01_概要'},{'heading':'項目一覧','kind':'LIST','sheet':'02_項目一覧'}]}
    prefix='<!-- spec-meta: '+json.dumps(meta,ensure_ascii=False)+' -->\n# Synthetic fixture\n'
    if count:
        prefix+='\n| key | value |\n| --- | --- |\n'+''.join('| field'+str(i)+' | '+['001','1.0','令和06年04月01日'][i]+' |\n' for i in range(count))
    return prefix+'\n## 概要\nSynthetic body.\n\n## 項目一覧\n| '+ ' | '.join(str(i) for i in range(10))+' |\n| '+' | '.join('---' for _ in range(10))+' |\n| '+' | '.join(['001','=1+1','令和06年04月01日','1.0',"'x",'@x','+01','-01','9223372036854775807','a&#124;b'])+' |\n'
reference=json.loads((R/'agents/reverse-agent/src/docsite/v2/reference_format.json').read_text(encoding='utf-8'))
expected=set(reference['sheets']['表紙']['merges']);assert len(expected)==14
tests=[]
for count in range(4):
    md=markdown(count);entry={'documentId':'TOY-001','canonicalDocumentPath':'toy.md','rawMarkdown':md,'images':[],'markdown':'synthetic-only','markdownSha256':hashlib.sha256(md.encode()).hexdigest(),'renderDirectory':'synthetic-only','renderPinsSha256':'0'*64,'renderManifestSha256':'1'*64}
    doc=m.document_model(entry);cover=doc['sheets'][0]
    assert {op['range'] for op in cover['operations']}==expected
    assert all(op['value']=='' for op in cover['operations'][-7:])
    assert cover['printArea']=='O6:AU36' and doc['sheets'][1]['columns']==62 and doc['sheets'][2]['itemList'] is True
    assert [op['value'] for op in doc['sheets'][2]['operations']][10:]==['001','=1+1','令和06年04月01日','1.0',"'x",'@x','+01','-01','9223372036854775807','a|b']
    tests.append({'name':'actual-parser-synthetic-preamble-'+str(count)+'-always14-merges-and-literals','pass':True})
assert sha(src)==before
assert all(sha(Path(p))==h for module in loaded.values() for p,h in module['nonCacheFiles'].items())
record={'schema':'spec-agent-blank-cover-completeness/1','createdUtc':datetime.now(timezone.utc).isoformat(),'source':str(src),'sourceSha256':before,'candidate':str(target),'candidateSha256':sha(target),'delta':{'old':old,'new':new},'sourceFileUnchanged':True,'expectedV2CoverMerges':sorted(expected),'tests':tests,'pass':len(tests),'actualMarkdownParserExecutedOnSyntheticOnly':True,'analysisDependencyReceipt':str(dp),'analysisDependencyReceiptSha256':sha(dp),'dependencyFilesUnchanged':True,'businessInputRead':False,'providerExecuted':False,'artifactToolExecuted':False,'markerExecuted':False,'actualXlsxCreated':False,'outputModified':False}
p=O/'model-r03-cover-parser-probes.json'
with p.open('x',encoding='utf-8') as f:json.dump(record,f,ensure_ascii=False,indent=2);f.write('\n')
print(json.dumps({'path':str(p),'sha256':sha(p),'modelSha256':sha(target),'depsReceiptSha256':sha(dp),'pass':len(tests)},ensure_ascii=False))
