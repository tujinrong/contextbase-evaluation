"""ZIP build/seed-SKIP workload; the companion PS1 owns native AppData guards."""
from pathlib import Path
import datetime as dt,importlib.util,json,sys
sys.dont_write_bytecode=True
SPEC=importlib.util.spec_from_file_location('zip_validation',Path(__file__).with_name('source-package-validation.py'))
v=importlib.util.module_from_spec(SPEC);SPEC.loader.exec_module(v)
OUT=v.ROOT/'build/test-results/source-package-preservation-workload.json'
def main():
    initial=v.read(v.OUT);assert initial['status']=='PASS_SOURCE_ONLY_BUILD_AND_OWNED_INITIALIZATION'
    original_measurements=initial['measurementSources']
    assert original_measurements[0]['sha256']==v.sha(Path(v.__file__))
    record={'schemaVersion':1,'projectId':'sample-project2','profileId':'CSharp_ASPNET','runId':v.RUN,'startedAt':dt.datetime.now(dt.timezone.utc).isoformat(),'status':'RUNNING','scope':'Supplement only: existing owned ZIP DB is not recreated; native PowerShell AppData observation surrounds the ordinary source-only build and seed SKIP','initialUserSecretsInterval':'NOT_MEASURED: initial Microsoft Store Python filesystem view returned exists=false; no native before/after SHA was captured in that initial interval','formalScore':None}
    error=None
    try:
        before=v.artifact(v.ROOT/'build/publish');assert before['sha256']==v.PUBLISH
        pack=v.read(v.ROOT/'build/generation/source-packages.json')['packages'][0]
        assert v.verify_package(pack)==92
        first=v.snapshot();assert first==initial['ordinaryInitialization']['afterSkippedSnapshot']
        assert first['owner']==v.OWNER
        v.run(['powershell','-NoProfile','-NonInteractive','-ExecutionPolicy','Bypass','-File','tools/Build.ps1'],v.ISOLATED)
        import os
        env={**os.environ,'SP2_CONNECTION_STRING':f'Server=.\\SQLEXPRESS;Database={v.DB};Integrated Security=True;Encrypt=True;TrustServerCertificate=True'}
        manifest=v.ISOLATED/'build/generation/seed-manifest.json';beforeManifest=v.sha(manifest)
        result=v.run(['dotnet','run','--project','tools/CareerManagement.Setup','-c','Release','--no-build','--','seed',v.DB],v.ISOLATED,env)
        assert 'SkippedExactMatch' in result
        after=v.snapshot();assert after==first and v.sha(manifest)==beforeManifest
        assert v.artifact(v.ROOT/'build/publish')==before
        freeze=v.read(v.ROOT/'build/generation/source-freeze.json')
        assert all(v.sha(v.ROOT/f['file'])==f['sha256'] for f in freeze['files'])
        record.update(status='PASS_SUPPLEMENTARY_BUILD_AND_SEED_SKIP',originalPublishUnchanged=True,frozen48ProductionFilesUnchanged=True,ownedDatabase=v.DB,owner=v.OWNER,databaseRecreated=False,dropOrResetExecuted=False,seedOutput=result,allTypedRowsAndSchemaUnchanged=first==after,seedManifestUnchanged=True,beforeSnapshot=first,afterSnapshot=after,measurementSources=[v.ref(Path(__file__)),v.ref(Path(v.__file__))],initialMeasurementSources=original_measurements)
    except Exception as e:
        error=type(e).__name__+': '+str(e);record.update(status='FAIL',error=error)
    finally:
        record.update(endedAt=dt.datetime.now(dt.timezone.utc).isoformat(),commands=v.COMMANDS);v.save(OUT,record)
    print(json.dumps({'status':record['status'],'error':error,'databaseRecreated':False,'record':str(OUT)},ensure_ascii=False))
    return int(error is not None)
if __name__=='__main__':raise SystemExit(main())
