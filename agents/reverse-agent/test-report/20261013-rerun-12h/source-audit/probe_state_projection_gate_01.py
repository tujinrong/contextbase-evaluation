"""Probe only helper function/class definitions; never execute its AI CLI body."""
import ast
import hashlib
from html.parser import HTMLParser
import json
from pathlib import Path
import sys
from datetime import datetime, timezone
from markdown_it import MarkdownIt
import tinycss2

ROOT=Path(__file__).resolve().parents[5]
HERE=Path(__file__).resolve().parent
HELPER=ROOT/'agents/reverse-agent/test-report/20261013-rerun-12h/source-pilot/prepare_state_projection.py'
EXPECTED='006df8a6091fe3f4fe0118263242877aaf0fa77cab476e4932ba0559e444b9ab'
RECEIPT=ROOT/'agents/reverse-agent/test-report/20261013-rerun-12h/source-pilot/runtime-code-source-04.json'
data=HELPER.read_bytes()
assert hashlib.sha256(data).hexdigest()==EXPECTED, 'helper changed; review a new SHA separately'
freeze=json.loads(RECEIPT.read_text(encoding='utf8'))
runtime=Path(freeze['destination'])
actual={p.relative_to(runtime).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in runtime.rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.suffix.lower() not in {'.pyc','.pyo'}}
assert actual==freeze['files'], 'source04 runtime files changed'
sys.path.insert(0,str(runtime))
from contextbase.ai import capsule
names={'reject_css_resources','check_css','InertHtml','canonical_path','heading_ranges','validate_canonical_location'}
tree=ast.parse(data.decode('utf8'),filename=str(HELPER))
defs=[n for n in tree.body if isinstance(n,(ast.FunctionDef,ast.ClassDef)) and n.name in names]
assert {n.name for n in defs}==names
namespace={'HTMLParser':HTMLParser,'tinycss2':tinycss2,'MarkdownIt':MarkdownIt,'Path':Path,'capsule':capsule}
exec(compile(ast.Module(body=defs,type_ignores=[]),str(HELPER),'exec'),namespace)
def html_probe(label,html,expect_reject):
    try:
        parser=namespace['InertHtml']();parser.feed(html);parser.close();rejected=False;reason=None
    except ValueError as error:
        rejected=True;reason=str(error)
    return {'label':label,'html':html,'expectedRejection':expect_reject,'actualRejected':rejected,'matchesExpected':rejected==expect_reject,'reason':reason}
html_tests=[
 ('self-contained-static', '<!doctype html><html><head><style>body{color:#243448}</style></head><body><form inert><button type="button">検索</button></form></body></html>',False),
 ('script', '<script>alert(1)</script>',True),
 ('source-url-attribute', '<img src="https://example.invalid/x.png">',True),
 ('form-not-inert', '<form><button type="button">検索</button></form>',True),
 ('submit-input', '<input type="submit">',True),
 ('css-url-escaped', '<style>body{background:u\\72l("https://example.invalid/x.png")}</style>',True),
 ('css-import-escaped', '<style>@\\69mport "https://example.invalid/x.css";</style>',True),
 ('css-image-set-string-resource', '<style>body{background-image:image-set("https://example.invalid/x.png" 1x)}</style>',True),
 ('meta-refresh-duplicate-attribute', '<meta http-equiv="refresh" http-equiv="x" content="0;url=https://example.invalid/">',True),
]
html_results=[html_probe(*row) for row in html_tests]
paths={
 'basic05':ROOT/'test-project1/spec-analysis/CSharp_ASPNET/20261013-rerun-12h/source-only/drafts/search-basic-05/基本設計書/01_学生検索画面.md',
 'detail04':ROOT/'test-project1/spec-analysis/CSharp_ASPNET/20261013-rerun-12h/source-only/drafts/search-detail-04/詳細仕様書/CSharp_ASPNET/01_学生検索画面.md',
}
approved=ROOT/'test-project1/spec-analysis/CSharp_ASPNET/20261013-rerun-12h/source-only/drafts'
path_results=[]
for key,path in paths.items():
    namespace['canonical_path'](path,approved);path_results.append({'case':key,'result':'allowed exact source-only canonical path'})
try:
    namespace['canonical_path'](HERE/'document-comparison-03.summary.md',approved)
except ValueError as error:
    path_results.append({'case':'outside-approved-root','result':'rejected','reason':str(error)})
else:raise AssertionError('out-of-role path accepted')
documents=[]
for key,path in paths.items():
    content=path.read_text(encoding='utf8');documents.append({'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'headingRanges':namespace['heading_ranges'](content)})
first=documents[0]; heading=next(h for h in first['headingRanges'] if h['heading']=='概要')
valid={'documentSha256':first['sha256'],'heading':heading['heading'],'headingLine':heading['headingLine'],'startLine':heading['headingLine']+1,'endLine':heading['headingLine']+2}
namespace['validate_canonical_location'](valid,documents)
location_results=[{'case':'existing-exact-heading-and-lines','result':'allowed'}]
for key,value in [('heading','nonexistent-heading'),('headingLine',heading['headingLine']+1),('documentSha256','0'*64),('endLine',heading['endLine']+1)]:
    invalid={**valid,key:value}
    try:namespace['validate_canonical_location'](invalid,documents)
    except ValueError as error:location_results.append({'case':'invalid-'+key,'result':'rejected','reason':str(error)})
    else:raise AssertionError('invalid canonical location accepted: '+key)
assert hashlib.sha256(HELPER.read_bytes()).hexdigest()==EXPECTED, 'helper changed during function probes'
output={
 'schema':'reverse-source-projection-gate-probe/1','recordedAtUtc':datetime.now(timezone.utc).isoformat(),
 'helper':{'path':HELPER.relative_to(ROOT).as_posix(),'sha256':EXPECTED},
 'runtimeReceipt':{'path':RECEIPT.relative_to(ROOT).as_posix(),'sha256':hashlib.sha256(RECEIPT.read_bytes()).hexdigest(),'frozenFilesVerified':len(actual),'importedCapsuleFromSource04':str(capsule.__file__)},
 'scope':{'functionDefinitionsOnly':sorted(names),'argparseTopLevelExecuted':False,'aiProviderCalled':False,'applicationDbOrDeploymentExecuted':False,'htmlRenderedOrNetworkFetched':False,'helperOrDraftEdited':False,'originalSpecEvalTrainingAssistedRead':False},
 'htmlGateCases':html_results,'pathCases':path_results,'canonicalLocationCases':location_results,
 'findings':['CSS image-set() string resource is accepted by helper gate', 'duplicate meta http-equiv refresh is accepted because dict(attrs) uses the last value'],
 'limitation':'Mechanical rejection tests only. Browser network or navigation effects were not executed. Strict renderer sanitizer and independent source/canonical meaning/native visual checks remain required. Other top-level path/job/provenance checks were read statically, not invoked as an AI job.'
}
target=HERE/'state-projection-gate-probe-01.json'
assert not target.exists(), 'do not overwrite an independent probe'
target.write_text(json.dumps(output,ensure_ascii=False,indent=2)+'\n',encoding='utf8',newline='\n')
print(json.dumps({'output':str(target),'sha256':hashlib.sha256(target.read_bytes()).hexdigest(),'htmlCases':len(html_results),'unexpectedAcceptances':[row['label'] for row in html_results if not row['matchesExpected']],'runtimeFilesVerified':len(actual),'canonicalLocationCases':len(location_results)},ensure_ascii=False))
