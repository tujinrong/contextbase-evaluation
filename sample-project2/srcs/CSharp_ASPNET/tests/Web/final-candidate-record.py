"""Bind current candidate records. Missing UI observations stay missing; no expected values are copied."""
from pathlib import Path
import json,hashlib,datetime,subprocess,shutil,re
ROOT=Path(__file__).resolve().parents[2];REPO=ROOT.parents[2];RUN='sp2-ui-regenerate-20261029'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def write(p,obj):
    p=Path(p);p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
def proof(p):return {'file':str(Path(p).relative_to(ROOT)).replace('\\','/'),'sha256':sha(p)}
def artifact():return json.loads(subprocess.check_output(['node','--input-type=module','-e',"import {hashArtifact} from './agents/builds/build-agent/scripts/ui-conformance.mjs';console.log(JSON.stringify(hashArtifact('sample-project2/srcs/CSharp_ASPNET/build/publish')));"],cwd=REPO,text=True))
def meta(content):
    m=re.search(rb'<!--\s*spec-meta:\s*(\{.*?\})\s*-->',content,re.S);return json.loads(m[1]) if m else {}
def main():
    inputs=ROOT/'build/generation/inputs.json';input_sha=sha(inputs);art=artifact();contract=ROOT/'tests/ui-contract.json';now=datetime.datetime.now(datetime.timezone.utc).isoformat()
    copies=[]
    for folder in ('browser-smoke','history','functional','boundaries'):
        src=ROOT/'.tmp/build-agent'/folder;rec=read(src/'result.json');assert rec['runId']==RUN and rec['artifactSha256']==art['sha256'];assert all(r['status']=='PASS' for r in rec['results']) and not rec['pageErrors']
        dest=ROOT/'build/test-results/ui-regeneration'/folder;dest.mkdir(parents=True,exist_ok=True)
        members=[]
        for p in sorted(src.iterdir()):
            # Failed-attempt images stay scratch; final success screenshots/workbook are retained.
            if p.is_file() and not p.name.startswith('failure-') and p.suffix in ('.json','.png','.xlsx'):
                shutil.copyfile(p,dest/p.name);members.append(proof(dest/p.name))
        copies.append({'scope':folder,'executionRecord':proof(dest/'result.json'),'files':members,'cases':len(rec['results']),'artifactSha256':rec['artifactSha256']})
    write(ROOT/'build/test-results/ui-regeneration/records.json',{'runId':RUN,'recordedAt':now,'artifact':art,'inputManifestSha256':input_sha,'contractSha256':sha(contract),'suites':copies,'note':'All cases are real headless browser/HTTP/owned SQL checks; native BFCache/IME/clipboard not inferred from these passes.','formalScore':None})
    baseline=read(ROOT/'.tmp/build-agent/source-baseline.json');preserved=[];changed=[]
    for p in baseline['files']:
        file=ROOT/p['file'];current=sha(file) if file.is_file() else None;row={**p,'currentSha256':current,'unchanged':current==p['sha256']};(preserved if row['unchanged'] else changed).append(row)
    protected=[p for p in preserved+changed if p['file'].startswith(('database/','fixtures/','src/CareerManagement.Infrastructure/Authentication/','src/CareerManagement.Infrastructure/Reports/')) or p['file'].endswith('Properties/launchSettings.json')]
    assert all(p['unchanged'] for p in protected),'Protected auth/DB/report/fixture/user config source changed'
    write(ROOT/'build/test-results/source-preservation.json',{'runId':RUN,'sourceBaselineRecordedAt':baseline['recordedAt'],'protectedFiles':protected,'unchangedFiles':preserved,'uiImplementationChangedFiles':changed,'existingDemoDdlOrSeedExecuted':False,'debugUserSecretsModified':False,'formalScore':None})
    spec=ROOT.parents[1]/'spec/CSharp_ASPNET';changes=[]
    for p in sorted(spec.rglob('*.md')):
        rel=p.relative_to(REPO).as_posix();after=p.read_bytes();current=meta(after)
        prior=subprocess.run(['git','show','HEAD:'+rel],cwd=REPO,capture_output=True);before=prior.stdout if prior.returncode==0 else None;old=meta(before) if before else {}
        changes.append({'file':rel,'documentId':current.get('documentId'),'beforeVersion':old.get('version'),'beforeSha256':hashlib.sha256(before).hexdigest() if before is not None else None,'afterVersion':current.get('version'),'afterSha256':hashlib.sha256(after).hexdigest(),'changed':before!=after,'reason':'User-authorized high-quality UI basic/detail regeneration and explicit DQA-UI05 transport refinement; inherited business/auth/DB/report decisions retained.' if before!=after else 'Unchanged adopted specification input inherited exactly.'})
    assert len(changes)==43
    write(ROOT/'build/generation/spec-update.json',{'projectId':'sample-project2','profileId':'CSharp_ASPNET','runId':RUN,'classification':'user-requested-ui-change','userInstruction':'外部レビューを反映してAgentを改善しsample-project2のAccess/CSharp_ASPNETを基本設計→詳細設計→実装の順で高品質UIへ再生成する。利用者確定の認証・DB・保存・業務条件を継承する。','recordedAt':now,'headAtRecord':subprocess.check_output(['git','rev-parse','HEAD'],cwd=REPO,text=True).strip(),'scope':'Own canonical specification exact HEAD-before/current-frozen-after inventory, basic and detail including adopted technical correction; unrelated auth/VS run not reused.','allCanonicalSpecifications':True,'changes':changes,'formalScore':None})
    audit=read(ROOT/'.tmp/build-agent/nuget-audit.json');vulnerabilities=[(p.get('path'),f.get('framework'),package) for p in audit.get('projects',[]) for f in p.get('frameworks',[]) for package in f.get('topLevelPackages',[])+f.get('transitivePackages',[]) if package.get('vulnerabilities')]
    assert not vulnerabilities
    write(ROOT/'build/test-results/nuget-audit.json',{'runId':RUN,'recordedAt':now,'status':'PASS_NO_REPORTED_VULNERABILITIES','command':'dotnet list CareerManagement.slnx package --vulnerable --include-transitive --format json','vulnerabilities':vulnerabilities,'raw':audit,'formalScore':None})
    cycles=[]
    descriptions={1:('Initial generated UI and normal business checks','Independent F06 narrow viewport found 58/128px document overflow; root also reviewed busy, GET Japanese error shell and resume initialization ordering.','Use minmax(0,1fr)/min-width0, input locking, meaningful GET error state and resume-before-history-write.'),2:('Boundary/competition/failure business tests and independent targeted browser/SQL review','Unapplied current career/SQL rollback/Unknown and delayed inputs checked; cookie-loss CSRF precedence and tab-switch focus loss found in extended tests.','Pre-CSRF unauthenticated401 classification; restore selected tab focus after async switch.'),3:('Full business regression, four browser suites and final-artifact DOM/font measurement','Independent font collection found four container own-font values at16px instead of adopted14px. Native BFCache not entered and physical IME/clipboard not executed.','Apply existing UI font token to list containers/count; keep absent native coverage unmeasured and gate rejected as appropriate.')}
    for n in (1,2,3):
        r=read(ROOT/f'build/test-results/self-cycle-{n}.json');assert r['runId']==RUN and r['inputManifestSha256']==input_sha and r['passed'] and r['failed']==0
        focus,findings,fix=descriptions[n];cycles.append({'cycle':n,'inputManifestSha256':r['inputManifestSha256'],'scope':focus,'businessChecks':len(r['tests']),'businessEvidence':proof(ROOT/f'build/test-results/self-cycle-{n}.json'),'testedRuntimeArtifacts':r['testedRuntimeArtifacts'],'findings':findings,'corrections':fix,'regression':'Read current suite/source/artifact-specific evidence; earlier candidate passes are not reassigned to final candidate.','finalCandidateBrowserEvidence':proof(ROOT/'build/test-results/ui-regeneration/records.json') if n==3 else None,'formalAcceptance':'NOT_EXECUTED'})
    freeze=read(ROOT/'build/generation/source-freeze.json')
    for item in freeze['files']:assert sha(ROOT/item['file'])==item['sha256']
    for cycle in cycles:
        cycle['sourceVersionPolicy']='Earlier intermediate source files were not archived; exact loaded application/infrastructure DLL hashes identify tested code. Full final source hashes are claimed only for the final cycle.'
        cycle['sourceFiles']=freeze['files'] if cycle['cycle']==3 else []
        cycle['testSources']=[proof(ROOT/name) for name in ('tests/CareerManagement.Tests/Program.cs','tests/CareerManagement.Tests/CareerManagement.Tests.csproj')]
    write(ROOT/'build/test-results/quality-cycles.json',{'runId':RUN,'quality':'high','requestedCycles':3,'recordedAt':now,'cycles':cycles,'finalCandidateArtifact':art,'notExecuted':['Physical Windows IME/clipboard','Native BFCache persisted path not entered','SQL Server2022 physical host','Formal Pilot/user acceptance/scoring'],'formalScore':None})
    print(json.dumps({'artifact':art,'suites':sum(x['cases'] for x in copies),'specifications':len(changes),'cycles':len(cycles)}))
if __name__=='__main__':main()
