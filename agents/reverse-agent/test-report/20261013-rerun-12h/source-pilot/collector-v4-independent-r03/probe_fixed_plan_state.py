"""Record the fixed plan-handoff protection separately from isolated capsule-state hardening."""
from __future__ import annotations
import hashlib,json
from pathlib import Path
from datetime import datetime,timezone

HERE=Path(__file__).resolve().parent
original=HERE.parent/'collector-v4-independent-r01/probe_collector.py'
prefix=original.read_text(encoding='utf-8').split('\nRESULTS=[]\n',1)[0]
space={'__file__':str(__file__),'__name__':'synthetic_definitions_only'}
exec(compile(prefix,str(original)+' [definitions only]','exec'),space)
Fixture,store,disk_sha=space['Fixture'],space['store'],space['disk_sha']
rows=[]
for key,value in [('manifestSha256','0'*64),('mode','source-only')]:
    fixture=Fixture('main-fixed-plan-preserved-'+key)
    fixed_before=disk_sha(fixture.plan_handoff)
    fixed_constant=fixture.ns['PLAN_HANDOFF_SHA']
    fixture.state[key]=value
    error=None
    try:fixture.collect()
    except Exception as exc:error={'type':type(exc).__name__,'message':str(exc)}
    unchanged=disk_sha(fixture.plan_handoff)==fixed_before==fixed_constant
    rows.append({'name':fixture.name,'actual':'REJECT' if error else 'ACCEPT','expected':'REJECT',
                 'pass':error is not None and unchanged,'error':error,
                 'fixedPlanHandoffBytesAndConstantUnchanged':unchanged,
                 'reportExists':fixture.outreport.exists(),'outputExists':fixture.output.exists()})
    store(fixture.root/'trace.json',fixture.trace)
    print(json.dumps(rows[-1],ensure_ascii=False),flush=True)
for key,value in [('manifestSha256','0'*64),('mode','source-only')]:
    fixture=Fixture('verify-capsule-isolated-'+key)
    fixture.state[key]=value
    returned=fixture.ns['verify_capsule']()[1]
    rows.append({'name':fixture.name,'actual':'RETURNS_MISMATCHED_STATE','expected':'RETURNS_MISMATCHED_STATE',
                 'pass':returned[key]==value,'copyExecuted':False,
                 'interpretation':'Local defense-in-depth gap; fixed plan-handoff main guard independently blocks this mismatch'})
    store(fixture.root/'trace.json',fixture.trace)

helper=space['HELPER']
helper_after=disk_sha(helper)
if helper_after!=space['EXPECTED_SHA']:raise ValueError('Original approved helper bytes changed')
report={'schema':'collector-independent-fixed-plan-state-protection/1','createdAt':datetime.now(timezone.utc).isoformat(),
        'helper':str(helper),'helperSha256':helper_after,'oldHelperUnchanged':True,
        'cases':rows,'total':len(rows),'passed':sum(row['pass'] for row in rows),
        'actualBusinessMaterialsRead':0,'actualCollections':0,'providers':0,'applications':0,
        'scopeCorrection':'r01 two state counterexamples set the toy fixed plan-handoff SHA to the same mismatched state; they do not establish bypass of production fixed plan-handoff bytes',
        'semanticOrVisualApproval':False}
store(HERE/'review.json',report)
print(json.dumps({'review':str(HERE/'review.json'),'sha256':disk_sha(HERE/'review.json'),
                  'total':report['total'],'passed':report['passed']},ensure_ascii=False),flush=True)
