"""Validate the frozen Web source archive and initialize one NEW owned ZIP DB."""
from pathlib import Path
import datetime as dt,hashlib,json,os,subprocess,sys,zipfile
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2]
REPO=ROOT.parents[2]
RUN='sp2-ui-regenerate-20261029'
DB='SP2_WebFixture_ZIP_FINAL_R20261030'
PUBLISH='aad4998ca745296c2b670bc2a1f2fdc3159ec5e4112c4f9123088521f24deca4'
ISOLATED=ROOT/'.tmp/source-isolation-final'
SCRATCH=ROOT/'.tmp/source-package-validation'
OUT=ROOT/'build/test-results/source-package-validation.json'
OWNER='sample-project2/CSharp_ASPNET/SP2-DEMO-01'
COMMANDS=[]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text('utf-8-sig'))
def save(p,d):
    p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n','utf8')
def ref(p):return {'file':p.relative_to(ROOT).as_posix(),'sha256':sha(p),'bytes':p.stat().st_size}
def run(command,cwd,env=None):
    result=subprocess.run(command,cwd=cwd,env=env,capture_output=True,timeout=240)
    stdout=result.stdout.decode('utf-8','replace');stderr=result.stderr.decode('utf-8','replace')
    record={'command':command,'cwd':str(cwd),'exitCode':result.returncode,'stdout':stdout,'stderr':stderr}
    COMMANDS.append(record);save(SCRATCH/'commands.json',COMMANDS)
    if result.returncode:raise RuntimeError('Command failed (see recorded exit/output): '+command[0])
    return stdout.strip()
def artifact(p):
    code="import {hashArtifact} from './agents/builds/build-agent/scripts/ui-conformance.mjs'; console.log(JSON.stringify(hashArtifact(process.argv[1])));"
    return json.loads(run(['node','--input-type=module','-e',code,str(p)],REPO))
def sql(query,database='master'):
    return run(['sqlcmd','-S','.\\SQLEXPRESS','-E','-N','-C','-d',database,'-b','-h','-1','-y','4096','-w','65535','-Q','SET NOCOUNT ON; '+query],ISOLATED)
def snapshot():
    tables={'m_app_user':'user_id','m_code_category':'category_id','m_code':'category_id,code','m_employee':'employee_id','t_career':'career_id'}
    props=["DB_NAME() AS databaseName","(SELECT CONVERT(nvarchar(200),value) FROM sys.extended_properties WHERE class=0 AND name=N'SP2Owner') AS owner","(SELECT COUNT(*) FROM sys.tables WHERE is_ms_shipped=0) AS tableCount","(SELECT COUNT(*) FROM sys.columns c JOIN sys.tables t ON t.object_id=c.object_id WHERE t.is_ms_shipped=0) AS columnCount"]
    for table,order in tables.items():
        props += [f'(SELECT COUNT(*) FROM dbo.[{table}]) AS [{table}_count]',f"CONVERT(varchar(64),HASHBYTES('SHA2_256',(SELECT * FROM dbo.[{table}] ORDER BY {order} FOR JSON PATH,INCLUDE_NULL_VALUES)),2) AS [{table}_rowsSha256]"]
    props += ["CONVERT(varchar(64),HASHBYTES('SHA2_256',(SELECT t.name AS tableName,c.name AS columnName,c.column_id,c.system_type_id,c.max_length,c.precision,c.scale,c.is_nullable,c.is_identity FROM sys.tables t JOIN sys.columns c ON c.object_id=t.object_id WHERE t.is_ms_shipped=0 ORDER BY t.name,c.column_id FOR JSON PATH,INCLUDE_NULL_VALUES)),2) AS schemaSha256"]
    return json.loads(sql('SELECT '+','.join(props)+' FOR JSON PATH,INCLUDE_NULL_VALUES,WITHOUT_ARRAY_WRAPPER;',DB))
def protected():
    paths=[ROOT/'.tmp/runtime/profile.json',ROOT/'.tmp/ui-regenerate-runtime/profile.json',ROOT/'.tmp/audit-runtime/profile.json',ROOT/'src/CareerManagement.Web/Properties/launchSettings.json',Path(os.environ['APPDATA'])/'Microsoft/UserSecrets/sample-project2-CareerManagement.Web-46b7ea90-705d-4b68-a0ea-d681622fe9ae/secrets.json']
    return [{'name':str(p.relative_to(ROOT)) if p.is_relative_to(ROOT) else 'existing Web user-secrets','exists':p.is_file(),'sha256':sha(p) if p.is_file() else None} for p in paths]
def verify_package(pack):
    assert sha(ROOT/'build/source.zip')==pack['sha256']
    names=set()
    with zipfile.ZipFile(ROOT/'build/source.zip') as archive:
        for e in pack['entries']:
            name=e['file'];names.add(name)
            assert not any(p.casefold() in {'.tmp','tests','spec','spec-eval','build','bin','obj'} for p in Path(name).parts)
            assert 'launchSettings' not in name and 'Configure-DemoDebug' not in name
            assert sha(ROOT/name)==e['sourceSha256']
            assert hashlib.sha256(archive.read(name)).hexdigest()==e['sha256']
            assert sha(ISOLATED/name)==e['sha256']
        assert names==set(archive.namelist())
        assert 'tools/Build.ps1' in names and 'BUILD.md' in names
        assert '$RunTests' not in archive.read('tools/Build.ps1').decode('utf8')
        assert 'uiConformance' not in json.loads(archive.read('profile.json'))
    return len(names)
def main():
    SCRATCH.mkdir(parents=True,exist_ok=True)
    initial=dt.datetime.now(dt.timezone.utc).isoformat();error=None
    record={'schemaVersion':1,'projectId':'sample-project2','profileId':'CSharp_ASPNET','runId':RUN,'startedAt':initial,'status':'RUNNING','formalScore':None,'commands':COMMANDS}
    save(OUT,record)
    try:
        freeze=read(ROOT/'build/generation/source-freeze.json')
        assert len(freeze['files'])==48
        assert all(sha(ROOT/e['file'])==e['sha256'] for e in freeze['files'])
        before=artifact(ROOT/'build/publish');assert before['sha256']==PUBLISH
        guards=protected()
        inputs=read(ROOT/'build/generation/inputs.json');assert inputs['runId']==RUN
        assert all(sha(REPO/e['file'])==e['sha256'] for e in inputs['files'])
        packs=read(ROOT/'build/generation/source-packages.json');assert packs['runId']==RUN
        pack=packs['packages'][0];members=verify_package(pack)
        record.update(archive=ref(ROOT/'build/source.zip'),members=members,sourceFreeze=ref(ROOT/'build/generation/source-freeze.json'),inputManifest=ref(ROOT/'build/generation/inputs.json'),sourceProfile=ref(ROOT/'profile.json'),originalPublish=before)
        sdk=run(['dotnet','--version'],ISOLATED)
        buildOutput=run(['powershell','-NoProfile','-NonInteractive','-ExecutionPolicy','Bypass','-File','tools/Build.ps1'],ISOLATED)
        rebuilt=artifact(ISOLATED/'build/publish')
        absent=json.loads(sql("SELECT DB_ID(N'"+DB+"') AS databaseId FOR JSON PATH,INCLUDE_NULL_VALUES,WITHOUT_ARRAY_WRAPPER;"))
        assert absent['databaseId'] is None,'ZIP DB already exists: stopped without reuse/reset'
        env={**os.environ,'SP2_CONNECTION_STRING':f'Server=.\\SQLEXPRESS;Database={DB};Integrated Security=True;Encrypt=True;TrustServerCertificate=True'}
        setup=['dotnet','run','--project','tools/CareerManagement.Setup','-c','Release','--no-build','--']
        created=run(setup+['create',DB],ISOLATED,env)
        empty=snapshot();assert empty['owner']==OWNER and empty['tableCount']==5 and empty['columnCount']==48
        assert all(empty[t+'_count']==0 for t in ('m_app_user','m_code_category','m_code','m_employee','t_career'))
        save(SCRATCH/'creation.json',{'runId':RUN,'database':DB,'owner':empty['owner'],'createdAt':dt.datetime.now(dt.timezone.utc).isoformat(),'newDatabaseCreated':True,'ordinaryPackagedSetup':True})
        seeded=run(setup+['seed',DB],ISOLATED,env);first=snapshot()
        expected={'m_app_user':2,'m_code_category':3,'m_code':9,'m_employee':3,'t_career':3}
        assert first['owner']==OWNER and all(first[t+'_count']==n for t,n in expected.items())
        manifest=ISOLATED/'build/generation/seed-manifest.json';seedSha=sha(manifest)
        skipped=run(setup+['seed',DB],ISOLATED,env);second=snapshot()
        assert 'SkippedExactMatch' in skipped and first==second and sha(manifest)==seedSha
        save(ROOT/'build/test-results/source-package-seed-manifest.json',read(manifest))
        assert verify_package(pack)==members
        assert all(sha(ROOT/e['file'])==e['sha256'] for e in freeze['files'])
        assert artifact(ROOT/'build/publish')==before and protected()==guards
        record.update(status='PASS_SOURCE_ONLY_BUILD_AND_OWNED_INITIALIZATION',sdkVersion=sdk,buildEntry='tools/Build.ps1 (archive production-only transform)',buildExitCode=0,rebuiltPublish=rebuilt,binaryIdenticalToCanonical=rebuilt['sha256']==before['sha256'],originalPublishUnchanged=True,frozenProductionFilesUnchanged=True,protectedProfileAndUserSettingsUnchanged=True,protectedInputs=guards,sourceOnlyExclusions=['original specification','UI contract/expected values/tests','existing .tmp profiles/configuration','local launchSettings/user-secrets','undeclared debug tools'],ordinaryInitialization={'database':DB,'newDatabaseConfirmedAbsent':True,'createOutput':created,'emptySnapshot':empty,'seedOutput':seeded,'seededSnapshot':first,'secondSeedOutput':skipped,'afterSkippedSnapshot':second,'typedAllRowHashesAndSchemaUnchanged':True,'seedManifestSha256Unchanged':True,'seedManifest':ref(ROOT/'build/test-results/source-package-seed-manifest.json'),'dropOrResetExecuted':False,'fixtureTrustException':'Only explicit local SP2_WebFixture_ owned ZIP database; Encrypt=True/IntegratedSecurity=True; ordinary non-fixture certificate policy unchanged'},measurementSources=[ref(Path(__file__)),{'file':'agents/builds/build-agent/scripts/package-source.py','sha256':sha(REPO/'agents/builds/build-agent/scripts/package-source.py')}],scope='Actual source-only normal locked restore/build/publish and ordinary packaged Setup create/seed/SkippedExactMatch on one new exact DB. Existing app/DB/profile/user settings untouched; no product UI acceptance inferred.',notExecuted=['Original final-publish UI acceptance from rebuilt binaries','Physical IME/BFCache/Windows native interaction','Excel/Office verification','Production installation/certificate environment','Formal scoring/acceptance'])
    except Exception as exc:
        error=type(exc).__name__+': '+str(exc);record.update(status='FAIL',error=error)
    finally:
        record.update(endedAt=dt.datetime.now(dt.timezone.utc).isoformat(),commands=COMMANDS);save(OUT,record)
    print(json.dumps({'status':record['status'],'members':record.get('members'),'error':error,'record':str(OUT)},ensure_ascii=False))
    return int(error is not None)
if __name__=='__main__':raise SystemExit(main())
