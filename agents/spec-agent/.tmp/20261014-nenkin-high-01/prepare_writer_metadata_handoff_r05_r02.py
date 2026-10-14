from pathlib import Path
import hashlib, json
ROOT = Path(r'D:/開発/contextbase-evaluation/agents/spec-agent/.tmp/20261014-nenkin-high-01')
REPORT = Path(r'D:/開発/contextbase-evaluation/agents/spec-agent/report/20261014-nenkin-high-01')
def ref(path,expected=None):
    result={'path':str(path),'sha256':hashlib.sha256(path.read_bytes()).hexdigest()}
    assert expected is None or result['sha256']==expected
    return result
old=REPORT/'author-execution-metadata-preparation-r05.json'
old_ref=ref(old,'50c19800d8797ca5638ff885f8813699401e7522a091108228eb97c099f80df8')
value=json.loads(old.read_bytes())
ref(ROOT/'nenkin_writer_driver_r05.py','6b8e5456d96fabfda1bf43b6c17b6155167726492b10c0f9145473f243ee102c')
ref(ROOT/'nenkin_writer_driver_r04.py','ce836766e61f5abad0fc4d2abfe11b3c6e6588f4dc8b9d46f62f913f0cd8e664')
value['previousPreparation']=old_ref
value['boundedProbes']=ref(REPORT/'independent-audit/writer-metadata-r05-bounded-probes-r03.json',
    '635595f3269bf50e2b68ad05fb4bf7139fcb7f0d31a8053807ce06a1c38bcc23')
value['independentCodeReview']=ref(REPORT/'independent-audit/writer-metadata-r05-independent-code-review-r01.json',
    '5002a883e75a2b51ecda580e8570ca1f9f1773072e71b8e02ccc7517ab847ec3')
value['independentPureCheckCount']=32
value['independentPureChecksPassed']=32
value['priorProbeCoverageGap']=ref(REPORT/'independent-audit/writer-metadata-r05-bounded-probes-r02.json',
    'a864df9a065feb8cd50b59217249271419d29d9e2530005766c63e3293b7f66d')
value['priorProbeCoverageGapReason']='r02 outside-record fixture mutated the written route path without updating the referenced path; FileNotFoundError did not demonstrate containment. r03 updates reference paths and counts only typed boundary/schema rejection errors.'
value['explicitLimitations']={
    'completionEvidence':'Owned current-run JSON path and SHA only. Evidence schema/documentId/accepted status association is not interpreted or validated by this optional metadata channel; root must use audited receipts.',
    'routing':'Normalized relative path/scope/format and report-only disposition only. Actual publication-layout mapping, existence, link correctness and cross-document collisions require final bundle checks.',
    'completionState':'RECORDED is descriptive operational metadata, not a qualification percentage, native fidelity result or application-runtime evidence.',
    'boundaries':'Supplement/reference pins are revalidated at observable wrapper composite generation and separate review before/after, final text pin and wave completion. No internal analysis/draft callbacks and no atomic/race-free proof.',
    'tests':'40 author-run synthetic boundary/schema checks plus 32 independent pure/path/context checks. Production activation, full prior-provider binding, generation, independent AI/native/formal qualification remain untested.'}
path=REPORT/'author-execution-metadata-preparation-r05-r02.json'
with path.open('x',encoding='utf-8',newline='\n') as f:
    json.dump(value,f,ensure_ascii=False,indent=2)
    f.write('\n')
print(json.dumps({'preparation':ref(path),'providerStarts':0},ensure_ascii=False))
