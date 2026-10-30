"""Rebind only Pending API input/output paths to an owned staging build.

The original driver, VBA suite, authority inputs, contract and business
expectations remain unchanged. This wrapper is API-only, never native UI proof.
"""
from pathlib import Path
import argparse,datetime as dt,hashlib,importlib.util,json,os,stat,sys
sys.dont_write_bytecode=True
CANONICAL=Path(__file__).resolve().parents[2]
REPO=CANONICAL.parents[2]
BOUNDARY=CANONICAL/'.tmp/active-control-guard'
DRIVER=CANONICAL/'tests/independent/pending_api.py'
SUITE=CANONICAL/'tests/independent/PendingApiSuite.bas'
DRIVER_SHA='0ea9db711211d8c885a275af8a00930fd3c6139cafd086cf4cc835cd3fb47500'
SUITE_SHA='73c4b326d17c7828018713d0f3a691d39d853ad532fceda957ddcc6c62b75a59'
ARTIFACT_SHA='0810e210184e8b0db2f5868743f61daf26e56fc8a7fe71b1cd501b4543435481'
SEED_SHA='6cd654e09ebf3cc20e52f7cd0e9b718819737cf07d36933acf79c8a028160db4'
INPUT_SHA='779271c32c63058605c9b61955180cf8a5fd4dfe04e0aa51e1406bff8b6a65c2'
CONTRACT_SHA='2bec42d155e91ab26c9d704fb44537ddd95ec5ae3f2937b9a524467dbb79a018'
ALLOWED_GLOBALS=('ARTIFACT','SEED','OWNER','WORK','OUT','EXPECTED','SEED_SHA')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def identity(p):return {'file':p.relative_to(REPO).as_posix(),'sha256':sha(p),'bytes':p.stat().st_size}
def ordinary_path(path,kind,must_exist=True):
    path=Path(os.path.abspath(path))
    assert path.is_relative_to(BOUNDARY.absolute()),'staging path escapes the owned boundary'
    assert path!=BOUNDARY,'the shared staging boundary is not an input/output target'
    for parent in [path,*path.parents]:
        if not parent.exists():continue
        info=parent.lstat()
        assert not stat.S_ISLNK(info.st_mode) and not (getattr(info,'st_file_attributes',0)&0x400),'linked/reparse path denied'
        if parent==BOUNDARY:break
    assert path.resolve()==path,'resolved staging path differs'
    if must_exist:assert path.is_file() if kind=='file' else path.is_dir()
    return path
def pending_output_path(path,kind):
    path=ordinary_path(path,kind,False)
    first=path.relative_to(BOUNDARY).parts[0]
    assert first.startswith('pending-'),'writes must remain under a pending-* owned path'
    return path
def canonical_guards():
    files=[CANONICAL/'build/CareerManagement.accdb',CANONICAL/'build/seed-manifest.json',CANONICAL/'build/generation/inputs.json',CANONICAL/'tests/ui-contract.json',CANONICAL/'build/source.zip',CANONICAL/'build/test-results/independent-pending-api.json',DRIVER,SUITE]
    files.extend(p for p in (CANONICAL/'src').rglob('*') if p.is_file())
    return {p.relative_to(REPO).as_posix():sha(p) for p in files}
def main():
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ['artifact','manifest','build-source-root','scratch','output']:parser.add_argument('--'+name,required=True,type=Path)
    args=parser.parse_args()
    artifact=ordinary_path(args.artifact,'file');manifest=ordinary_path(args.manifest,'file');source_root=ordinary_path(args.build_source_root,'dir')
    scratch=pending_output_path(args.scratch,'dir');output=pending_output_path(args.output,'file')
    assert not scratch.exists() and not output.exists(),'fresh scratch and output paths required'
    assert output!=artifact and output!=manifest and not scratch.is_relative_to(source_root),'test writes may not enter the build source tree'
    assert sha(DRIVER)==DRIVER_SHA and sha(SUITE)==SUITE_SHA
    assert sha(CANONICAL/'build/CareerManagement.accdb')==ARTIFACT_SHA
    assert sha(CANONICAL/'build/seed-manifest.json')==SEED_SHA
    assert sha(CANONICAL/'build/generation/inputs.json')==INPUT_SHA
    assert sha(CANONICAL/'tests/ui-contract.json')==CONTRACT_SHA
    adopted=json.loads(manifest.read_text('utf8'));artifact_sha=sha(artifact);manifest_sha=sha(manifest)
    assert adopted['artifactSha256']==artifact_sha,'artifact is not the compiled manifest artifact'
    source_map=adopted['source'];assert isinstance(source_map,dict) and source_map,'missing build source map'
    for name,value in source_map.items():
        source_file=ordinary_path(source_root/name,'file')
        assert source_file.is_relative_to(source_root) and sha(source_file)==value,'build source map mismatch'
    # The original driver imports this helper before OWNER is rebound. Require
    # byte identity so its recorded staging helper is the actual imported code.
    assert sha(source_root/'tools/data_integrity.py')==sha(CANONICAL/'tools/data_integrity.py')
    before=canonical_guards();wrapper_sha=sha(Path(__file__))
    bindings={'ARTIFACT':artifact,'SEED':manifest,'OWNER':source_root,'WORK':scratch,'OUT':output,'EXPECTED':artifact_sha,'SEED_SHA':manifest_sha}
    assert tuple(bindings)==ALLOWED_GLOBALS
    spec=importlib.util.spec_from_file_location('unchanged_pending_api_driver',DRIVER)
    driver=importlib.util.module_from_spec(spec);spec.loader.exec_module(driver)
    fixed_names=['REPO','INPUTS','CONTRACT','SUITE','INPUT_SHA','CONTRACT_SHA']
    fixed={name:getattr(driver,name) for name in fixed_names}
    for name,value in bindings.items():setattr(driver,name,value)
    assert all(getattr(driver,name)==value for name,value in fixed.items())
    assert driver.REPO==REPO and driver.SUITE==SUITE
    scratch.mkdir(parents=True,exist_ok=False);output.parent.mkdir(parents=True,exist_ok=True)
    status=0;unexpected=None
    try:
        driver.main()
    except SystemExit as e:status=int(e.code or 0)
    except BaseException as e:status=1;unexpected={'type':type(e).__name__,'detail':str(e)[:300]}
    finally:
        after=canonical_guards()
        retained=before==after and sha(DRIVER)==DRIVER_SHA and sha(SUITE)==SUITE_SHA and sha(Path(__file__))==wrapper_sha
        binding_retained=sha(artifact)==artifact_sha and sha(manifest)==manifest_sha and all(sha(source_root/name)==value for name,value in source_map.items())
        record=json.loads(output.read_text('utf8')) if output.exists() else {'status':'FAIL_OR_INCONCLUSIVE','issues':[{'code':'NO_DRIVER_RECORD'}],'formalScore':None,'nativePass':False}
        record['stagingWrapper']={'source':identity(Path(__file__)),'originalDriver':identity(DRIVER),'unchangedSuite':identity(SUITE),'finishedAt':dt.datetime.now(dt.timezone.utc).isoformat(),'scope':'Reuse unchanged Pending API checks against a compiled staging artifact. No source/spec/contract/business-expectation modification and no native UI observation.','allowedGlobalRebindings':{k:str(v) for k,v in bindings.items()},'unchangedAuthorityGlobals':{k:str(v) for k,v in fixed.items()},'canonicalBefore':before,'canonicalAfter':after,'canonicalPreserved':retained,'stagingArtifactManifestAndSourceMapPreserved':binding_retained,'authorityAndBusinessExpectationsChanged':False,'nativeUiMeasured':False,'artifactIdentityIsMeasuredCompileManifestBindingNotUiExpectation':True}
        if unexpected:record.setdefault('issues',[]).append({'code':'WRAPPER_EXECUTION_EXCEPTION',**unexpected})
        if not retained or not binding_retained:record.setdefault('issues',[]).append({'code':'WRAPPER_PRESERVATION_FAILED'})
        if unexpected or not retained or not binding_retained:record['status']='FAIL_OR_INCONCLUSIVE';status=1
        record['formalScore']=None;record['nativePass']=False
        output.write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n','utf8')
        print(json.dumps({'record':str(output),'sha256':sha(output),'status':record['status'],'canonicalPreserved':retained,'stagingBindingPreserved':binding_retained},ensure_ascii=False),flush=True)
    raise SystemExit(status)
if __name__=='__main__':main()
