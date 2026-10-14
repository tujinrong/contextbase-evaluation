"""Bind code/format references, not business inputs."""
import hashlib,json,os
from pathlib import Path
from datetime import datetime,timezone
R=Path(r'D:\開発\contextbase-evaluation')
D=R/'agents/spec-agent/.tmp/20261014-nenkin-high-01/delivery'
O=R/'agents/spec-agent/report/20261014-nenkin-high-01/delivery-audit-r01'
def sha(p):
    p=Path(os.path.abspath(p))
    for q in (p,*p.parents):
        if q.is_symlink() or (q.exists() and getattr(q.lstat(),'st_file_attributes',0)&0x400):raise ValueError('Linked path')
    return hashlib.sha256(p.read_bytes()).hexdigest()
refs={
    'routing':'AGENTS.md','agent-role':'agents/spec-agent/AGENT.md','v2-user-baseline':'agents/reverse-agent/AGENTS.md',
    'md-contract-project120':'docs/MD構造・Excel変換規約.md','v2-original-layout-metadata':'agents/reverse-agent/src/docsite/v2/reference_format.json',
    'v2-measured-geometry-code':'agents/reverse-agent/src/docsite/v2/upstream_layout.py','v2-legacy-author-code-read-only':'agents/reverse-agent/src/docsite/v2/render_document_xlsx.py',
    'v2-border-readback-code':'agents/reverse-agent/src/docsite/excel_package.py',
    'artifact-builder-origin':'agents/reverse-agent/test-report/20261013-rerun-12h/delivery/build_xlsx_r18.mjs',
    'mechanical-model-origin':'agents/reverse-agent/test-report/20261013-rerun-12h/delivery/delivery_model_r18_r02.py',
    'independent-readback-origin':'agents/reverse-agent/test-report/20261013-rerun-12h/delivery/verify_xlsx_r18_r02.py'}
pins=[{'role':role,'path':str(R/relative),'sha256':sha(R/relative)} for role,relative in refs.items()]
local=[D/'delivery_model_v2_62_r01.py',D/'build_xlsx_v2_62_r01.mjs',D/'format-profile-v2-62-r01.json',O/'candidate-preparation.json',O/'model-guard-probes-r01.json',O/'audit.md']
data={'schema':'spec-agent-format-provenance/1','createdUtc':datetime.now(timezone.utc).isoformat(),'role':'AG-SPEC','runId':'20261014-nenkin-high-01','formatProfileId':'v2-62-user-selected','formatProfilePath':str(D/'format-profile-v2-62-r01.json'),'formatProfileSha256':sha(D/'format-profile-v2-62-r01.json'),'referencePins':pins,'candidateAndAuditPins':{str(p):sha(p) for p in local},'effectiveContract':{'cover':'O6:AU36','normal':'A:BJ 62 columns, width3','itemList':'A:J ten columns, headerrow1, no data merges/splitting','tableException':'TABLE spec-md/1.1 one sheet, nine literal columns','docs120Changed':False,'userSelected62OverrideExplicit':True},'dependencyStatus':{'artifactToolAuthor':'loader Node/node_modules only; not executed','mechanicalMarkdownParser':'Bundled Python markdown_it/bs4 absent; runtime-only pinned parsing dependency connection pending','actualMarkdownParserExecuted':False},'validation':{'geometrySyntheticCases':10,'modelGuardSyntheticCases':16,'actualWorkbookCreated':False,'nodeSyntaxCheck':'PASS','businessInputRead':False,'providerExecuted':False,'markerExecuted':False,'outputModified':False},'printMetadata':'fresh metadata-only helper preparation; no actual XLSX application','wholeApproval':False}
p=O/'format-provenance-r01.json'
with p.open('x',encoding='utf-8') as f:json.dump(data,f,ensure_ascii=False,indent=2);f.write('\n')
assert all(sha(Path(x['path']))==x['sha256'] for x in pins)
print(json.dumps({'path':str(p),'sha256':sha(p)},ensure_ascii=False))
