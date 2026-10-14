"""Fresh plan04 scheduling metadata, retaining all plan03 reservations."""
import ast
import hashlib
import json
from pathlib import Path
BASE=Path(__file__).parent
OLD=BASE/'prepare_author_schedule_metadata_r02.py'
source=OLD.read_text(encoding='utf-8')
source=source.replace("BASE/'jobs/plan-03/plan-verified.json'","BASE/'jobs/plan-04/plan-verified.json'")
source=source.replace('f302f6d345e87add5a9ac4ef6b0d19f9708dfcb9bdd3c92e3d411795e9d8146d','e14b5e5acd96aed44c800209efbe452d094cb595f7d57da097b8c9a4a7bc9ee3')
source=source.replace("ledger_path=safe(REPORT/'author-wave-allocation-ledger-r01.json')", "ledger_path=safe(REPORT/'author-wave-allocation-ledger-r02.json')")
source=source.replace("REPORT/'author-run-recipes-r01.json'", "REPORT/'author-run-recipes-r02.json'")
source=source.replace("recipe_path=safe(REPORT/'author-run-recipes-r02.json')", "recipe_path=safe(REPORT/'author-run-recipes-r03.json')")
old="definitions={d['id']:d for d in docs}\npilot_ids="
new="""definitions={d['id']:d for d in docs}
old_ledger_path=safe(REPORT/'author-wave-allocation-ledger-r01.json')
require(sha(old_ledger_path)=='59874fba7c4dbc8f766f56d2f3cfdd332e85db762dfb546aa144de78aa5bdfa0','Old ledger changed')
require(sha(REPORT/'author-run-recipes-r02.json')=='08b1cbb113b05a5ec05b9818d1b6ecaa02c017ab53302e3c836d0435a0071bd3','Old recipe changed')
old_ledger=load(old_ledger_path)
require(old_ledger['consumedWaves']==0 and old_ledger['activationIssued'] is False and
        all(x['allocationConsumed'] is False and x['providerStarted'] is False for x in old_ledger['allocations']),
        'Prior reservations have actual allocation/execution evidence; cannot reuse their numbers')
old_definitions={d['id']:d for x in old_ledger['allocations'] for d in x['documents']}
require(len(old_definitions)==63 and definitions==old_definitions,'Plan04 exact ID/kind/path tuples differ from reserved plan03')
handoff=safe(PLAN.parent/'plan-handoff.json')
require(sha(handoff)=='2815a418a728f5ba8e71ec8a8d0cf7308b1920ecdf283b6ec9288e0831b68660','Plan04 handoff changed')
pilot_ids="""
assert source.count(old)==1
source=source.replace(old,new)
old="ledger={'schema':"
new="""require([(x['wave'],x['documents']) for x in allocations]==
        [(x['wave'],x['documents']) for x in old_ledger['allocations']], 'Plan04 wave allocation mapping differs')
allocation_comparison={'previousLedger':str(old_ledger_path),'previousLedgerSha256':sha(old_ledger_path),
    'previousPlan':old_ledger['plan'],'previousPlanSha256':old_ledger['planSha256'],
    'currentPlan':str(safe(PLAN)),'currentPlanSha256':PLAN_SHA,'currentPlanHandoffSha256':sha(handoff),
    'exactIdKindPathTuplesEqual':True,'waveDocumentReservationsEqual':True,
    'comparisonDocumentCount':63,'actualConsumedOldWaves':0,'onlyUnexecutedReservationsRebound':True,
    'businessResponsibilitiesOrSourceContentReused':False}
ledger={'schema':"""
assert source.count(old)==1
source=source.replace(old,new)
source=source.replace("'status':'METADATA_RESERVATIONS_ONLY','maximumWaveNumber':99", "'status':'METADATA_RESERVATIONS_ONLY','allocationComparison':allocation_comparison,'maximumWaveNumber':99")
source=source.replace("'plan':str(safe(PLAN)),'planSha256':PLAN_SHA,'planReviewApproved':False,'activationIssued':False,\n    'deadline'", "'plan':str(safe(PLAN)),'planSha256':PLAN_SHA,'planHandoffSha256':sha(handoff),\n    'allocationComparison':allocation_comparison,'planReviewApproved':False,'activationIssued':False,\n    'deadline'")
source=source.replace("require(sha(PLAN)==PLAN_SHA and sha(DRIVER)==recipe['driverSha256'],'Fixed metadata drift during scheduling')", "require(sha(PLAN)==PLAN_SHA and sha(DRIVER)==recipe['driverSha256'] and\n    sha(handoff)==allocation_comparison['currentPlanHandoffSha256'] and\n    sha(old_ledger_path)==allocation_comparison['previousLedgerSha256'],'Fixed metadata drift during scheduling')")
ast.parse(source)
exec(compile(source,str(__file__),'exec'),{'__file__':str(__file__),'__name__':'__main__'})
