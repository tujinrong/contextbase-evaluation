"""Fresh raw review/preparation and wave-integrity interface guards only."""
import ast
import hashlib
import json
from pathlib import Path
BASE = Path(__file__).parent
OLD = BASE / 'nenkin_writer_driver_r02.py'
NEW = BASE / 'nenkin_writer_driver_r03.py'
source = OLD.read_text(encoding='utf-8')
def replace(old, new):
    global source
    assert source.count(old) == 1, old[:100]
    source = source.replace(old, new)

replace("grant_path, grant = fixed_grant(grant_path, grant_sha)\n    snapshot =", "grant_path, grant = fixed_grant(grant_path, grant_sha)\n    from contextbase.ai import provider\n    snapshot =")
replace("require(load(review_file.parent / 'answer.txt') == review and rh['originalAiResponse'] == 'answer.txt',\n        'Verified plan review differs from unchanged raw AI answer')",
'''require(raw(review_file.parent / 'answer.txt') == raw(review_file) and rh['originalAiResponse'] == 'answer.txt',
        'Verified plan review differs from unchanged raw AI answer bytes')
    raw_review, unused_prompt, provider_pins = provider_evidence(snapshot, review_file.parent, plan_review.PLAN_REVIEW, state)
    require(raw_review == review and rh['runtimeReceiptSha256'] == RECEIPT_SHA, 'Plan review provider/runtime differs')
    fixed_review_input = {'schema': 'reverse-ai-plan-review-input/1', 'snapshot': state,
        'planFile': str(plan), 'planSha256': sha(plan), 'planHandoffSha256': sha(handoff),
        'planOrigin': first.handoff['origin'], 'referenceMode': 'source-only',
        'executionContext': str(context_file), 'executionContextSha256': context_sha}
    prep_file = inside(REPORT / 'independent-plan-review' / review_file.parent.name / 'preparation.json', REPORT)
    require(sha(prep_file) == hash_arg(rh['scopePreparationSha256']), 'Scoped plan review preparation bytes differ')
    prepared = load(prep_file)
    helper = inside(prepared['helper'], WORK)
    require(helper.parent == safe(WORK) and re.fullmatch(r'review_plan_with_scope_r[0-9]{2}\.py', helper.name) is not None and
        sha(helper) == hash_arg(prepared['helperSha256']), 'Scoped review helper path/hash differs')
    expected_runtime = {'receiptSha256': RECEIPT_SHA, 'runtimeRoot': str(safe(RUNTIME)),
        'runtimeFileCount': 128, 'runtimeFiles': runtime['files'],
        'loadedImports': {name: {'path': x['path'], 'sha256': x['sha256']} for name, x in runtime['receiptImports'].items()},
        'criticalModules': {name: {'path': x['path'], 'sha256': x['sha256']} for name, x in runtime['criticalModules'].items()}}
    require(prepared['schema'] == 'spec-agent-scoped-plan-review-preparation/1' and prepared['agentRole'] == 'AG-SPEC' and
        prepared['reviewerRole'] == 'independent-plan-review' and prepared['providerStarted'] is False and
        prepared['coreOrFrozenPromptModified'] is False and prepared['businessProseAuthored'] is False and
        prepared['deadline'] == DEADLINE and type(prepared['timeout']) is int and 1 <= prepared['timeout'] <= 2400 and
        safe(prepared['job']) == review_file.parent and prepared['input'] == fixed_review_input and
        prepared['runtime'] == expected_runtime and
        prepared['schemaSha256'] == digest(json.dumps(plan_review.PLAN_REVIEW, sort_keys=True).encode()),
        'Scoped independent plan-review preparation identity/runtime/input differs')
    prepared_prompt = inside(prepared['promptFile'], prep_file.parent)
    require(prepared_prompt == safe(prep_file.parent / 'prepared-prompt.txt') and
        sha(prepared_prompt) == hash_arg(prepared['promptSha256']), 'Prepared plan-review prompt bytes differ')
    require(raw(review_file.parent / 'prompt.txt') ==
        (provider.COMMON_POLICY + '\\nUser task (within that boundary):\\n').encode('utf-8') + raw(prepared_prompt),
        'Actual plan-review scope prompt differs from its pinned preparation')
    require(bp == {'input': fixed_review_input, 'runtime': expected_runtime, 'preparationSha256': sha(prep_file)} and
        ap == {'status': 'UNCHANGED_AND_REVIEW_VALIDATED', 'input': fixed_review_input,
            'runtime': expected_runtime, 'preparationSha256': sha(prep_file)},
        'Scoped plan review did not finish with exact approved preparation/runtime')
    artifacts.extend([prep_file, prepared_prompt, helper, *[Path(p) for p in provider_pins]])''')
replace("require(job.name in {'analysis', 'analysis-repair', 'draft', 'independent-review'}, 'Unknown prior provider stage')",
        "require(job.name in {'analysis', 'analysis-repair', 'draft', 'independent-review'} or\n        (job.parent == safe(WORK / 'jobs') and re.fullmatch(r'independent-plan-review-[0-9]{2}', job.name) is not None),\n        'Unknown prior provider stage')")
replace("return answer, raw(paths[3]).decode('utf-8'), {str(p): sha(p) for p in paths}",
        "# JSON metadata markers use universal-newline text parsing; raw prompt bytes remain pinned.\n    return answer, safe(paths[3]).read_text(encoding='utf-8'), {str(p): sha(p) for p in paths}")
replace("require(review_prompt.split('\\n原稿本文:\\n', 1)[1].split('\\n構造検査の指摘（意味の正確さを採点した結果ではありません）:\\n', 1)[0] == content.decode('utf-8'),",
        "review_prompt_raw = raw(generation / 'independent-review/prompt.txt').decode('utf-8')\n    require(review_prompt_raw.split('\\n原稿本文:\\n', 1)[1].split('\\n構造検査の指摘（意味の正確さを採点した結果ではありません）:\\n', 1)[0] == content.decode('utf-8'),")
replace("'businessProseAssembledByPython': False}\n    recheck(pin)\n    check_schema('text-pin', result)",
        "'businessProseAssembledByPython': False,\n        'waveIntegrityVerificationRequiredForCollection': True,\n        'waveVerification': {'before': str(safe(generation.parent / 'author-inputs-before.json')),\n            'beforeSha256': sha(generation.parent / 'author-inputs-before.json'),\n            'after': str(safe(generation.parent / 'author-inputs-after.json')),\n            'result': str(safe(generation.parent / 'author-wave-result.json'))},\n        'finalSpecificationBundleApproved': False}\n    recheck(pin)\n    check_schema('text-pin', result)")
replace("'mode': 'source-only', 'capsule': pin['snapshot'], 'seconds': round(time.monotonic() - started, 3),",
        "'mode': 'source-only', 'capsule': pin['snapshot'], 'seconds': round(time.monotonic() - started, 3),\n        'preparation': str(preparation), 'preparationSha256': preparation_sha, 'input': pin,\n        'waveIntegrityVerified': True, 'inputsAfter': str(safe(job_root / 'author-inputs-after.json')),\n        'inputsAfterSha256': sha(job_root / 'author-inputs-after.json'),")
ast.parse(source)
with NEW.open('x', encoding='utf-8', newline='\n') as out:
    out.write(source)
print(json.dumps({'path': str(NEW), 'sha256': hashlib.sha256(NEW.read_bytes()).hexdigest(),
    'providerStarted': False}, ensure_ascii=False))
