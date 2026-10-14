import hashlib,json,subprocess
from pathlib import Path
HERE=Path(__file__).absolute().parent
old=HERE.parent/'split-retry-code-audit-r02/audit.py'
source=old.read_text(encoding='utf8').split("run('real-exclusive-positive'")[0]
ns={'__file__':str(HERE/'synthetic-harness.py')}
exec(compile(source,str(old),'exec'),ns)
g=ns['grader'];out=[]
def add(name,passed,**detail):out.append({'name':name,'passed':passed,**detail})
for kind in ('capsule','accepted-job','destination'):
    s,d=ns['fixture']('junction-'+kind);receipt=ns['closure_for'](s,'junction-'+kind);pin=ns['sha'](receipt)
    linked=(s/'capsule') if kind=='capsule' else ((s/'jobs/S001') if kind=='accepted-job' else d)
    target=linked.parent/(linked.name+'-actual')
    if linked.exists():linked.rename(target)
    else:target.mkdir()
    p=subprocess.run(['cmd','/c','mklink','/J',str(linked),str(target)],capture_output=True,text=True)
    assert p.returncode==0 and linked.is_junction()
    linked_reads=[];old_load=g.load;old_digest=g.digest
    def track(func,path):
        if Path(path).is_relative_to(linked):linked_reads.append(str(path))
        return func(path)
    g.load=lambda p:track(old_load,p);g.digest=lambda p:track(old_digest,p)
    try:
        ns['ns']['prepare_split'](s,d,20,receipt,pin);rejected=False;error=None
    except Exception as exc:rejected=True;error=str(exc)
    finally:g.load=old_load;g.digest=old_digest
    add('actual-junction-before-read-'+kind,rejected and not linked_reads,rejected=rejected,linkedReads=linked_reads,error=error)
s,d=ns['fixture']('receipt-after-validation-drift');receipt=ns['closure_for'](s,'receipt-after-validation-drift');pin=ns['sha'](receipt)
before=ns['ns']['inventory'](s);original=g.check_capsule
def drift(batch):
    result=original(batch)
    if batch==s:
        data=g.load(receipt);data['controllerExited']=False;ns['put'](receipt,data)
    return result
g.check_capsule=drift
try:
    ns['ns']['prepare_split'](s,d,20,receipt,pin);rejected=False;error=None
except Exception as exc:rejected=True;error=str(exc)
g.check_capsule=original
add('fixed-closure-receipt-after-validation-drift',rejected,rejected=rejected,error=error,receiptDrifted=ns['sha'](receipt)!=pin,sourceUnchanged=ns['ns']['inventory'](s)==before)
report={'scope':'INFRASTRUCTURE_CODE_AND_SYNTHETIC_ONLY','helperSha256':ns['pins']['helper'],'graderSha256':ns['pins']['grader'],'cases':out,'passed':sum(x['passed'] for x in out),'total':len(out),'productionMaterialReads':0,'actualPrepare':0,'provider':0,'actualJunctions':'owned synthetic fixture directories only','codePinsUnchanged':ns['pins']=={'helper':ns['sha'](ns['TARGET']),'grader':ns['sha'](ns['GRADER'])}}
ns['put'](HERE/'review.json',report)
print(json.dumps({'passed':report['passed'],'total':report['total'],'reportSha256':ns['sha'](HERE/'review.json'),'failures':[x['name'] for x in out if not x['passed']]}))
