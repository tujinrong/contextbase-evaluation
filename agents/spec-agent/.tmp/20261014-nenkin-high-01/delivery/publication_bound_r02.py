"""Pinned allowlist staging and journaled directory publication; no prose rewriting.
Preparation defaults to metadata validation. Stage/swap require a root final grant.
Two same-volume renames are individually atomic, NOT an atomic pair. No deletion.
"""
from __future__ import annotations
import argparse,hashlib,json,os,re,shutil,stat
from pathlib import Path
from datetime import datetime,timezone
from urllib.parse import unquote,urlsplit

ROOT=Path(r'D:\開発\contextbase-evaluation')
WORK=ROOT/'agents/spec-agent/.tmp/20261014-nenkin-high-01'
REPORT=ROOT/'agents/spec-agent/report/20261014-nenkin-high-01'
TARGET=ROOT/'agents/reverse-agent/output'
INPUT=ROOT/'agents/reverse-agent/input'
BASELINE_SHA='b66ea84af2fc79b8980358717a92b01136e28e59adda00f4079fa17eb5235449'
BASELINE_PATH=REPORT/'independent-audit/output-inventory-publish-baseline-r01.json'
DENIED={'analysis','qa','answers','report','reports','test-report','jobs','cache','__pycache__','node_modules','.tmp','input','spec-eval','evaluator-only'}
EXT={'MD':'.md','HTML':'.html','PDF':'.pdf','XLSX':'.xlsx','ASSET':'.png'}
MAX_FILES=50000
def sha(raw):return hashlib.sha256(raw).hexdigest()
def require(ok,message):
    if not ok:raise ValueError('HOLD: '+message)
def unique_json(raw):
    def pairs(items):
        result={}
        for k,v in items:require(k not in result,'duplicate JSON key');result[k]=v
        return result
    return json.loads(raw,object_pairs_hook=pairs,parse_constant=lambda _:require(False,'nonfinite JSON'))
def relative(value):
    require(isinstance(value,str) and value and '\\' not in value and ':' not in value and not value.startswith('/') and not any(ord(c)<32 or ord(c)==127 for c in value),'canonical relative path')
    require(all(p not in {'','.','..'} and not p.endswith((' ','.')) for p in value.split('/')),'relative traversal/alias segment')
    require(not any(part.split('.')[0].casefold() in {'con','prn','aux','nul',*[f'com{i}' for i in range(1,10)],*[f'lpt{i}' for i in range(1,10)]} for part in value.split('/')),'Windows reserved device segment')
    require(Path(value).as_posix()==value,'relative spelling changed');return Path(value)
def safe(value):
    p=Path(value);require(p.is_absolute(),'explicit absolute path')
    require(not any(ord(c)<32 or ord(c)==127 for c in str(p)) and all(':' not in x for x in p.parts[1:]),'absolute colon/control')
    for node in (p,*p.parents):
        try:s=node.lstat()
        except FileNotFoundError:continue
        require(not stat.S_ISLNK(s.st_mode) and not(getattr(s,'st_file_attributes',0)&0x400),'linked/reparse path')
    require(p.resolve(strict=False)==p,'redirected or noncanonical resolution');return p
def within(path,roots):return any(path.is_relative_to(root) for root in roots)
def owned(value):
    p=safe(value);require(within(p,(WORK,REPORT)),'not within owned new run');return p
def hashfile(path):
    p=safe(path);require(p.is_file(),'ordinary pinned file required')
    digest=sha(p.read_bytes());safe(p);return digest
def pinned(record,roots=(WORK,REPORT)):
    require(isinstance(record,dict) and set(record)=={'path','sha256'},'exact file descriptor required')
    p=safe(record['path']);require(within(p,roots),'descriptor outside permitted roots')
    require(isinstance(record['sha256'],str) and re.fullmatch('[0-9a-f]{64}',record['sha256']),'64lower SHA pin required')
    require(hashfile(p)==record['sha256'],'pinned file drift: '+str(p));return p
def fresh_json(path,data):
    p=owned(path);safe(p.parent).mkdir(parents=True,exist_ok=True)
    with safe(p).open('x',encoding='utf-8',newline='\n') as h:json.dump(data,h,ensure_ascii=False,indent=2);h.write('\n')
def inventory(root):
    root=safe(root);require(root.is_dir(),'inventory directory required');result={}
    def walk(directory):
        safe(directory)
        with os.scandir(directory) as entries:
            for entry in sorted(entries,key=lambda e:e.name):
                path=safe(Path(entry.path));st=path.lstat()
                if stat.S_ISDIR(st.st_mode):walk(path)
                else:
                    require(stat.S_ISREG(st.st_mode),'unsupported inventory entry')
                    rel=path.relative_to(root).as_posix();relative(rel)
                    require(rel.casefold() not in {x.casefold() for x in result},'inventory casefold collision')
                    result[rel]=hashfile(path);require(len(result)<=MAX_FILES,'inventory bound exceeded')
    walk(root);return result
def identity(path):
    st=safe(path).stat();return (st.st_dev,st.st_ino)
def compare(root,expected):
    require(inventory(root)==expected,'full raw-byte inventory mismatch: '+str(root))
def load_baseline():
    require(hashfile(BASELINE_PATH)==BASELINE_SHA,'old output baseline drift')
    value=unique_json(BASELINE_PATH.read_bytes())
    require(value.get('schema')=='spec-agent-output-change-baseline/1' and safe(value['outputRoot'])==TARGET and value.get('exists') is True,'baseline identity')
    require(value.get('fileCount')==906 and len(value['files'])==906,'old906 baseline required');return value

def descriptor_shape(record):
    require(isinstance(record,dict) and set(record)=={'path','sha256'},'exact file descriptor required')
    require(isinstance(record.get('path'),str),'descriptor text path')
    require(isinstance(record.get('sha256'),str) and re.fullmatch('[0-9a-f]{64}',record['sha256']) is not None,'64lower SHA pin required')
    return safe(record['path'])


def validate(plan,grant,plan_sha):
    require(plan.get('schema')=='spec-agent-publication-plan/1' and plan.get('outputRoot')==str(TARGET),'exact publication plan target')
    require(grant.get('schema')=='spec-agent-publication-grant/1' and grant.get('planSha256')==plan_sha and grant.get('allowStage') is True,'root stage grant required')
    require(plan.get('referenceMode')=='source-only' and grant.get('sourceSnapshotManifestSha256')==plan.get('sourceSnapshotManifestSha256'),'source-only capsule binding')
    require(re.fullmatch('[0-9a-f]{64}',plan.get('sourceSnapshotManifestSha256','')) is not None,'dynamic sourcecap SHA required')
    require(plan.get('complete') is True and grant.get('complete') is True,'empty or incomplete bundle is HOLD')
    require(all(grant.get(k) is True for k in ('sourceReviewed','textCoverageReviewed','actualNativeReviewed','reviewedIndexReady')),'all final root gates required')
    docs=plan.get('documents');require(isinstance(docs,list) and docs and len(docs)<=5000,'explicit nonempty documents required')
    layout=plan.get('layout');require(isinstance(layout,dict) and set(layout)=={'MD','HTML','PDF','XLSX'},'four explicit format prefixes required')
    for value in layout.values():
        if value:relative(value)
    approved=grant.get('approvedDocumentIds')
    require(isinstance(approved,list) and approved and all(isinstance(i,str) and i for i in approved) and len(approved)==len(set(approved)),'root-approved exact document set required')
    protected_roots=[safe(v['root']) for v in plan.get('protectedInventories',[])]
    files=[];ids=set();targets=set()
    for doc in docs:
        require(isinstance(doc.get('documentId'),str) and doc['documentId'],'explicit document ID required')
        cp=relative(doc['canonicalDocumentPath']);require(cp.suffix=='.md','canonical MD suffix');require(doc.get('documentId') not in ids,'duplicate document ID');ids.add(doc['documentId'])
        require(doc.get('category')!='analysis-report','report-only document is not a published specification')
        require(doc.get('complete') is True and doc.get('reviewed') is True and doc.get('generated') is True,'plan-only/unreviewed document cannot stage')
        selected=doc.get('files');require(isinstance(selected,list) and selected,'explicit artifact allowlist')
        seen=set()
        for item in selected:
            kind=item.get('kind');require(kind in EXT,'unsupported artifact type')
            target=relative(item['target']);require(not any(p.casefold() in DENIED for p in target.parts),'report/cache/QA destination prohibited')
            source=descriptor_shape(item['source']);require(within(source,(WORK,REPORT)),'artifact outside this new run')
            require(not any(source.is_relative_to(root) for root in protected_roots),'protected original/capsule source cannot be a generated artifact')
            require(not any(p.casefold() in DENIED for p in source.relative_to(WORK if source.is_relative_to(WORK) else REPORT).parts[:-1]),'analysis/QA/report artifacts are not publishable')
            if kind=='MD':require(source.is_relative_to(WORK),'analysis MD in REPORT is not publishable')
            require(source.suffix.lower()==EXT[kind] and target.suffix.lower()==EXT[kind],'artifact suffix mismatch')
            if kind!='ASSET':
                expected=Path(layout[kind])/cp.with_suffix(EXT[kind]);require(target==expected,'canonical stem/hierarchy mismatch');require(kind not in seen,'duplicate document format');seen.add(kind)
            require(target.as_posix().casefold() not in targets and target.as_posix() not in {'index.md','manifest.json'},'duplicate/reserved destination')
            targets.add(target.as_posix().casefold());files.append({**item,'documentId':doc['documentId']})
        require(seen=={'MD','HTML','PDF','XLSX'},'all four completed forms required')
    require(ids==set(approved),'published documents differ from root-approved exact set')
    index=plan.get('index');require(isinstance(index,dict) and index.get('target')=='index.md' and index.get('reviewed') is True,'reviewed AI rootindex required')
    index_source=descriptor_shape(index['source'])
    require(index_source.is_relative_to(WORK),'root index source must be new WORK');require(index_source.suffix=='.md','root index Markdown required')
    require(not any(p.casefold() in DENIED for p in index_source.relative_to(WORK).parts[:-1]),'root index must not be a raw answer/report/analysis file')
    require(not any(index_source.is_relative_to(root) for root in protected_roots),'root index cannot come from protected source')
    files.append({'kind':'INDEX','target':'index.md','source':index['source']})
    protected=plan.get('protectedInventories');require(isinstance(protected,list) and len(protected)==2,'oldsource345 and newcap179 proofs required')
    names={v.get('role') for v in protected};require(names=={'original-input','source-capsule'},'exact protected inventory roles')
    for item in protected:
        descriptor_shape(item['inventory'])
        root=safe(item['root'])
        if item['role']=='original-input':require(root==INPUT and item.get('count')==345,'original input345 identity')
        else:require(root.is_relative_to(WORK) and item.get('count')==179 and item.get('sourceSnapshotManifestSha256')==plan['sourceSnapshotManifestSha256'],'newcap179 identity')
        require(not root.is_relative_to(TARGET) and not TARGET.is_relative_to(root),'protected root overlaps output')
    transaction=owned(plan['transactionRoot']);require(transaction.is_relative_to(WORK/'publication'),'transaction must be own WORK/publication')
    require(transaction.drive==TARGET.drive,'same-volume renames required')
    require(all(not transaction.is_relative_to(safe(v['root'])) and not safe(v['root']).is_relative_to(transaction) for v in protected),'transaction overlaps protected source')
    require(grant.get('oldOutputBaselineSha256')==BASELINE_SHA,'root grant must bind old906 baseline')
    return files,transaction

def protected_checks(plan):
    proofs=[]
    for item in plan['protectedInventories']:
        path=pinned(item['inventory']);record=unique_json(path.read_bytes())
        require(record.get('schema')=='protected-file-inventory/1' and record.get('root')==item['root'],'protected inventory binding')
        require(record.get('fileCount')==item['count'] and len(record['files'])==item['count'],'protected full inventory count')
        compare(Path(item['root']),record['files']);proofs.append({'role':item['role'],'inventorySha256':item['inventory']['sha256'],'fileCount':item['count']})
    return proofs

def linkcheck(stage,files):
    """Parsing only. Broken/excluded links HOLD; never repair an AI index or body."""
    from markdown_it import MarkdownIt
    from bs4 import BeautifulSoup
    available={f['target'] for f in files}|{'manifest.json'};issues=[];checked=0
    parser=MarkdownIt('commonmark',{'html':True}).enable('table')
    def reference(origin,value):
        nonlocal checked
        checked+=1;url=urlsplit(value)
        if url.scheme in {'http','https'}:return
        if url.scheme=='data' and value.startswith('data:image/png;base64,'):return
        if url.scheme or url.netloc or '\\' in value:issues.append({'file':origin,'link':value,'reason':'unsupported absolute/scheme'});return
        decoded=unquote(url.path)
        if not decoded:
            if url.fragment:issues.append({'file':origin,'link':value,'reason':'fragment requires explicit anchor proof'})
            return
        target=Path(os.path.normpath(str(Path(origin).parent/decoded))).as_posix()
        if target not in available:issues.append({'file':origin,'link':value,'reason':'not in actual explicit bundle; no report/analysis fallback'})
        elif url.fragment:issues.append({'file':origin,'link':value,'reason':'fragment requires explicit anchor proof'})
    for item in files:
        if item['kind'] not in {'MD','INDEX','HTML'}:continue
        path=safe(stage/relative(item['target']));text=path.read_text(encoding='utf-8-sig')
        if item['kind']=='HTML':fragments=[text]
        else:
            fragments=[]
            for token in parser.parse(text):
                for child in token.children or []:
                    if child.type in {'link_open','image'}:
                        value=child.attrGet('href' if child.type=='link_open' else 'src')
                        if value:reference(item['target'],value)
                    elif child.type=='html_inline':fragments.append(child.content)
                if token.type=='html_block':fragments.append(token.content)
        for fragment in fragments:
            soup=BeautifulSoup(fragment,'html.parser')
            for tag in soup.find_all(True):
                for key in ('href','src'):
                    if tag.get(key):reference(item['target'],tag[key])
    return {'checkedLinks':checked,'issues':issues,'bodyRewritten':False,'networkRequested':False}

def stage_bundle(plan,grant,plan_sha):
    files,transaction=validate(plan,grant,plan_sha);baseline=load_baseline();compare(TARGET,baseline['files']);protected=protected_checks(plan)
    require(not transaction.exists(),'fresh transaction root required');transaction.mkdir(parents=True);stage=transaction/'stage';stage.mkdir()
    expected={}
    for item in files:
        source=pinned(item['source']);destination=safe(stage/relative(item['target']));safe(destination.parent).mkdir(parents=True,exist_ok=True)
        require(not destination.exists(),'fresh target only');shutil.copyfile(source,destination)
        require(hashfile(destination)==item['source']['sha256'] and hashfile(source)==item['source']['sha256'],'copied file bytes drift')
        expected[item['target']]=item['source']['sha256']
    links=linkcheck(stage,files);fresh_json(transaction/'link-check.json',links);require(not links['issues'],'AI index/body needs revision against actual bundle metadata')
    manifest={'schema':'spec-agent-published-artifacts/1','agentIdentity':plan.get('agentIdentity'),'referenceMode':plan['referenceMode'],'sourceSnapshotManifestSha256':plan['sourceSnapshotManifestSha256'],'planSha256':plan_sha,'documentCount':len(plan['documents']),'documents':[{'documentId':d['documentId'],'canonicalDocumentPath':d['canonicalDocumentPath']} for d in plan['documents']],'files':[{'path':f['target'],'kind':f['kind'],'sha256':f['source']['sha256'],'documentId':f.get('documentId')} for f in files],'oldOutputBaselineSha256':BASELINE_SHA,'protectedInventoryPins':protected,'sourceUnknownsResolvedByFormatter':False,'businessProseAuthoredByFormatter':False}
    fresh_json(stage/'manifest.json',manifest);expected['manifest.json']=hashfile(stage/'manifest.json');compare(stage,expected)
    for item in files:pinned(item['source'])
    protected_checks(plan);compare(TARGET,baseline['files'])
    receipt={'schema':'spec-agent-staged-bundle/1','planSha256':plan_sha,'stageRoot':str(stage),'directoryIdentity':identity(stage),'files':expected,'linkIssues':0,'status':'STAGED_BYTES_VERIFIED_NOT_PUBLISHED','actualPublication':False}
    fresh_json(transaction/'stage-receipt.json',receipt);return receipt

def publish(plan,grant,plan_sha):
    files,transaction=validate(plan,grant,plan_sha)
    require(grant.get('allowPublication') is True and grant.get('mechanism')=='JOURNALED_TWO_RENAMES' and grant.get('acknowledgeTransientOutputAbsence') is True,'root must acknowledge reversible non-atomic pair')
    receipt_path=safe(transaction/'stage-receipt.json');receipt=unique_json(receipt_path.read_bytes());require(receipt.get('planSha256')==plan_sha and receipt.get('status')=='STAGED_BYTES_VERIFIED_NOT_PUBLISHED','staged final binding')
    stage=safe(transaction/'stage');backup=safe(transaction/'backup');quarantine=safe(transaction/'failed-new')
    require(stage==Path(receipt['stageRoot']) and identity(stage)==tuple(receipt['directoryIdentity']),'owned stage identity');compare(stage,receipt['files'])
    baseline=load_baseline();compare(TARGET,baseline['files']);protected_checks(plan)
    require(not backup.exists() and not quarantine.exists(),'fresh backup/quarantine only');old_id=identity(TARGET);new_id=identity(stage)
    journal=owned(transaction/'swap-journal.jsonl')
    def event(name,**fields):
        with safe(journal).open('a',encoding='utf-8') as h:h.write(json.dumps({'utc':datetime.now(timezone.utc).isoformat(),'event':name,**fields})+'\n');h.flush();os.fsync(h.fileno())
    lock=owned(WORK/'publication'/'publisher.lock');moved_old=False;moved_new=False
    with lock.open('x',encoding='utf-8') as lock_handle:
        lock_handle.write(json.dumps({'planSha256':plan_sha,'pid':os.getpid(),'rootGrantRequired':True}));lock_handle.flush()
        try:
            event('PREPARED',oldIdentity=old_id,newIdentity=new_id,pairAtomic=False)
            compare(TARGET,baseline['files']);require(identity(TARGET)==old_id,'old target identity changed')
            safe(TARGET).rename(safe(backup));moved_old=True;event('OLD_RENAMED')
            require(identity(backup)==old_id,'backup identity mismatch');compare(backup,baseline['files']);require(not TARGET.exists(),'target unexpectedly recreated')
            safe(stage).rename(safe(TARGET));moved_new=True;event('NEW_RENAMED')
            require(identity(TARGET)==new_id,'new target identity mismatch');compare(TARGET,receipt['files']);protected_checks(plan);compare(backup,baseline['files']);event('COMMITTED')
        except BaseException:
            event('FAILED',movedOld=moved_old,movedNew=moved_new)
            if moved_new:
                require(identity(TARGET)==new_id and not quarantine.exists(),'cannot quarantine a directory not owned by this candidate')
                safe(TARGET).rename(safe(quarantine));event('NEW_QUARANTINED')
            if moved_old:
                require(not TARGET.exists() and identity(backup)==old_id,'rollback target or backup ownership conflict')
                safe(backup).rename(safe(TARGET));compare(TARGET,baseline['files']);event('OLD_RESTORED')
            raise
    # Keep the lock receipt; subsequent execution cannot silently publish again.
    return {'status':'PUBLISHED_BYTES_MATCHED','outputRoot':str(TARGET),'backupRoot':str(backup),'pairAtomic':False,'rollbackPerformed':False,'businessBodyRewritten':False}

def main():
    p=argparse.ArgumentParser();p.add_argument('--plan',type=Path,required=True);p.add_argument('--plan-sha256',required=True);p.add_argument('--grant',type=Path,required=True);p.add_argument('--grant-sha256',required=True);p.add_argument('--action',choices=('validate-metadata','stage','publish'),default='validate-metadata')
    args=p.parse_args();plan_path=pinned({'path':str(args.plan),'sha256':args.plan_sha256});grant_path=pinned({'path':str(args.grant),'sha256':args.grant_sha256})
    plan=unique_json(plan_path.read_bytes());grant=unique_json(grant_path.read_bytes());files,transaction=validate(plan,grant,args.plan_sha256)
    if args.action=='stage':result=stage_bundle(plan,grant,args.plan_sha256)
    elif args.action=='publish':result=publish(plan,grant,args.plan_sha256)
    else:result={'status':'METADATA_VALIDATION_ONLY','explicitFileCount':len(files),'transactionRoot':str(transaction),'actualStage':False,'actualPublish':False}
    require(hashfile(plan_path)==args.plan_sha256 and hashfile(grant_path)==args.grant_sha256,'plan/grant changed');print(json.dumps(result,ensure_ascii=False))
if __name__=='__main__':main()
