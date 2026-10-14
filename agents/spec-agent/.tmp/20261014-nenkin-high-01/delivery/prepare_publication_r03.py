"""Seal staged receipts and keep journal failures from preventing rollback."""
import ast,hashlib,json
from pathlib import Path
D=Path(__file__).parent;O=Path(r'D:\開発\contextbase-evaluation\agents\spec-agent\report\20261014-nenkin-high-01\delivery-audit-r01')
p=D/'publication_bound_r02.py';raw=p.read_bytes();assert hashlib.sha256(raw).hexdigest()=='fb59aa3097f8284d08276cdf334b001c1d205781507b8863a2feb3fb63709a61';text=raw.decode().replace('\r\n','\n')
old="    receipt_path=safe(transaction/'stage-receipt.json');receipt=unique_json(receipt_path.read_bytes());require(receipt.get('planSha256')==plan_sha and receipt.get('status')=='STAGED_BYTES_VERIFIED_NOT_PUBLISHED','staged final binding')"
new="""    receipt_path=pinned(grant.get('stageReceipt'),roots=(WORK,))
    require(receipt_path==safe(transaction/'stage-receipt.json'),'root-approved exact stage receipt path')
    receipt=unique_json(receipt_path.read_bytes());require(receipt.get('planSha256')==plan_sha and receipt.get('status')=='STAGED_BYTES_VERIFIED_NOT_PUBLISHED','staged final binding')
    expected={f['target']:f['source']['sha256'] for f in files}
    manifest_sha=grant.get('stageManifestSha256');require(isinstance(manifest_sha,str) and re.fullmatch('[0-9a-f]{64}',manifest_sha),'root-inspected stage manifest SHA required')
    expected['manifest.json']=manifest_sha
    require(receipt.get('files')==expected,'stage receipt must match plan allowlist and root-inspected manifest exactly')
    for item in files:pinned(item['source'])"""
assert text.count(old)==1;text=text.replace(old,new)
old="""        except BaseException:
            event('FAILED',movedOld=moved_old,movedNew=moved_new)
            if moved_new:
                require(identity(TARGET)==new_id and not quarantine.exists(),'cannot quarantine a directory not owned by this candidate')
                safe(TARGET).rename(safe(quarantine));event('NEW_QUARANTINED')
            if moved_old:
                require(not TARGET.exists() and identity(backup)==old_id,'rollback target or backup ownership conflict')
                safe(backup).rename(safe(TARGET));compare(TARGET,baseline['files']);event('OLD_RESTORED')
            raise"""
new="""        except BaseException as primary:
            journal_errors=[]
            def recovery_event(name,**fields):
                try:event(name,**fields)
                except BaseException as error:journal_errors.append(str(error))
            recovery_event('FAILED',movedOld=moved_old,movedNew=moved_new)
            try:
                if moved_new:
                    require(identity(TARGET)==new_id and not quarantine.exists(),'cannot quarantine a directory not owned by this candidate')
                    safe(TARGET).rename(safe(quarantine));recovery_event('NEW_QUARANTINED')
                if moved_old:
                    require(not TARGET.exists() and identity(backup)==old_id,'rollback target or backup ownership conflict')
                    safe(backup).rename(safe(TARGET));compare(TARGET,baseline['files']);recovery_event('OLD_RESTORED')
            finally:
                if journal_errors:primary.add_note('Recovery journal errors do not suppress rollback: '+repr(journal_errors))
            raise"""
assert text.count(old)==1;text=text.replace(old,new)
ast.parse(text);out=D/'publication_bound_r03.py'
with out.open('xb') as h:h.write(text.encode())
assert p.read_bytes()==raw
result={'scope':'STAGE_RECEIPT_AND_RECOVERY_METADATA_REPAIR_ONLY','source':{'path':str(p),'sha256':hashlib.sha256(raw).hexdigest()},'candidate':{'path':str(out),'sha256':hashlib.sha256(out.read_bytes()).hexdigest()},'changes':['root-pinned stage receipt before publish','exact plan file allowlist plus root-inspected generated manifestSHA','source allowlist pins reread before publish','recovery logging errors cannot short-circuit rollback'],'actualOutputReads':0,'actualSourceReads':0,'actualStage':0,'actualSwap':0,'status':'PENDING_INDEPENDENT_PROBES','limits':['Physical rename/restore errors can still HOLD; preserve all existing backup/quarantine data.','Failure lock remains a receipt and must be explicitly handled by root before retry.']}
record=O/'publication-r03-preparation.json'
with record.open('x',encoding='utf-8') as h:json.dump(result,h,ensure_ascii=False,indent=2);h.write('\n')
print(json.dumps({'candidateSha256':result['candidate']['sha256'],'receiptSha256':hashlib.sha256(record.read_bytes()).hexdigest()}))
