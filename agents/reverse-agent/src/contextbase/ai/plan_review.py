"""Independent AI plan assessment; code validates provenance, never business answers.

The response is immutable review data.  It neither replaces the original plan
nor proves that the model actually read every declared material.
"""
from __future__ import annotations

import json
from pathlib import Path

from . import capsule, prompts, workflow


def _object(properties):
    return {'type': 'object', 'properties': properties,
            'required': list(properties), 'additionalProperties': False}


def _array(item, minimum=0):
    return {'type': 'array', 'items': item, 'minItems': minimum}


TEXT = {'type': 'string', 'minLength': 1}
BASIS = {'type': 'string', 'enum': ['observed-source', 'reference-design']}
REVIEW_BASIS = {'type': 'string', 'enum': ['observed-source', 'reference-design', 'plan-structure']}
REFERENCE = _object({'path': TEXT, 'startLine': {'type': 'integer', 'minimum': 1},
                     'endLine': {'type': 'integer', 'minimum': 1}})
CLAIM = _object({'name': TEXT, 'basis': BASIS, 'references': _array(REFERENCE, 1)})
SUBJECT = _object({'id': TEXT, 'kind': TEXT, 'name': TEXT, 'basis': BASIS,
                  'references': _array(REFERENCE, 1), 'sourcePaths': _array(TEXT, 1),
                  'documentIds': _array(TEXT)})
COVERAGE = _object({'documentId': TEXT, 'path': TEXT, 'subjectIds': _array(TEXT),
                   'status': {'type': 'string', 'enum': ['covered', 'partial', 'missing', 'unknown', 'not-applicable']},
                   'basis': REVIEW_BASIS, 'rationale': TEXT, 'references': _array(REFERENCE)})
REACHABILITY = _object({'id': TEXT, 'subjectIds': _array(TEXT, 1),
                       'entryPoints': _array(CLAIM), 'callers': _array(CLAIM),
                       'registrations': _array(CLAIM), 'searchScope': _array(TEXT),
                       'status': {'type': 'string', 'enum': ['confirmed', 'declaration-only',
                                                           'not-found-in-included-scope', 'unknown']},
                       'basis': REVIEW_BASIS, 'explanation': TEXT, 'references': _array(REFERENCE)})
FINDING = _object({'id': TEXT, 'severity': {'type': 'string', 'enum': ['critical', 'major', 'minor']},
                  'documentIds': _array(TEXT), 'subjectIds': _array(TEXT),
                  'location': TEXT, 'defect': TEXT, 'repairDirection': TEXT,
                  'basis': REVIEW_BASIS, 'references': _array(REFERENCE)})
UNRESOLVED = _object({'id': TEXT, 'question': TEXT, 'documentIds': _array(TEXT),
                     'subjectIds': _array(TEXT), 'basis': REVIEW_BASIS,
                     'references': _array(REFERENCE)})
SCOPE_LIMIT = _object({'id': TEXT, 'limitation': TEXT, 'sourcePaths': _array(TEXT),
                      'documentIds': _array(TEXT), 'basis': REVIEW_BASIS,
                      'references': _array(REFERENCE)})
PLAN_REVIEW = _object({
    'schema': {'type': 'string', 'const': 'reverse-ai-plan-review/1'},
    'referenceMode': {'type': 'string', 'enum': ['source-only', 'training-assisted']},
    'approved': {'type': 'boolean'}, 'sourcePathsRead': _array(TEXT),
    'subjects': _array(SUBJECT), 'documentCoverage': _array(COVERAGE, 1),
    'reachability': _array(REACHABILITY), 'findings': _array(FINDING),
    'blockingUnresolved': _array(UNRESOLVED), 'scopeLimits': _array(SCOPE_LIMIT),
})

REVIEW_TASK = """
あなたは文書計画の独立レビュー担当です。完成本文の執筆や期待仕様の採点は行いません。
下記の計画JSON全文を判断対象とし、manifestと関係する原文を自分で調べてください。
計画を作ったAIの自己評価を根拠にせず、計画のsourcePathsは探索の開始点として閉包を追跡します。

subjectsへ、機能、論理テーブル、物理テーブル、データ契約、共通契約、interface等の
原文で発見した対象を記録します。kindは対象の実際の責務を表し、この例の種類へ無理に押し込みません。
業務名、表数、機能数、期待文書名を予め決めません。DTOを物理表と偽装せず、論理/物理/保存領域を区別します。
対象ごとに安定したid、名前、observed-sourceかreference-design、根拠位置、関連sourcePaths、
対応する既存documentIdsを記録します。文書が欠ければdocumentIdsは空でもよく、findingsに不足を示します。
文書の粒度・機能のUI/backend対応・論理/物理テーブルの個別責務・共通契約を、原文の対象に沿って評価します。
見つからない対象を類似業務から創作しません。論理名や意図が確定しない場合は不明として残します。

documentCoverageは計画の全documentIdをそれぞれ一度だけ列挙し、pathを原計画と一致させます。
その文書が説明するsubjectIds、covered/partial/missing/unknown/not-applicable、理由と根拠を示します。
計画自体の配置・粒度・ID対応の指摘はbasis=plan-structure、references=[]です。
原文実装への判断はobserved-source、明示許可された設計の意図はreference-designで根拠を付けます。
manifestは材料一覧であり業務判断や到達性の根拠にしません。

reachabilityには接続入口、呼出元、登録、それぞれの名前と根拠、実際に探索したsearchScopeを記録します。
statusはconfirmed/declaration-only/not-found-in-included-scope/unknownです。
confirmedは原ソースで入口からの接続を確認した場合だけです。設計資料の定義や宣言だけで確認済みにしません。
not-found-in-included-scopeは含まれる原ソースの探索範囲に限った未検出であり、絶対に未使用という断定ではありません。
動的呼出し・外部登録・不完全資料等で確定できなければunknownを維持します。
sourcePathsReadは読取りの自己申告です。全原文を読んだ監査済み証明や実行試験結果ではありません。

重要な欠落・矛盾はfindingsへ、改訂の承認を妨げる未確定だけをblockingUnresolvedへ入れます。
一方、明記すれば利用できる探索・環境の制限はscopeLimitsへ分け、制限だけを自動的に停止理由にしません。
approved=trueは重要なfindingsやblockingUnresolvedが残る場合には返しません。
少ない指摘、表の存在、構造検査の合格を業務意味の完全性に読み替えません。
許可材料内の根拠と計画内ID/pathだけを使い、原計画やソースを変更せず指定schemaの最終JSONを返してください。
"""


def _unique(values, label):
    if len(values) != len(set(values)):
        raise ValueError('Duplicate plan review ' + label)


def _validate(answer, plan_value, manifest):
    from jsonschema import Draft202012Validator, ValidationError
    try:
        Draft202012Validator(PLAN_REVIEW).validate(answer)
    except ValidationError as exc:
        raise ValueError('Invalid AI plan review schema') from exc
    if answer['referenceMode'] != capsule.reference_mode(manifest):
        raise ValueError('Plan review reference mode differs from the bound capsule')
    materials = workflow._materials(manifest)
    _unique(answer['sourcePathsRead'], 'read paths')
    if not set(answer['sourcePathsRead']) <= set(materials):
        raise ValueError('Plan review claims a non-snapshot material as read')
    read_originals = {materials[path]['original'] for path in answer['sourcePathsRead']}
    documents = {document['id']: document for document in plan_value['documents']}
    subject_ids = [subject['id'] for subject in answer['subjects']]
    _unique(subject_ids, 'subject IDs')
    subjects = set(subject_ids)

    def links(item):
        for field, available in (('documentIds', set(documents)), ('subjectIds', subjects)):
            if field in item:
                _unique(item[field], field)
                if not set(item[field]) <= available:
                    raise ValueError('Plan review uses unknown ' + field)

    def paths(values, *, source_only=False, allow_inventory=False):
        _unique(values, 'material paths')
        for path in values:
            material = materials.get(path)
            if (material is None or (material['kind'] == 'inventory' and not allow_inventory) or
                    (source_only and material['kind'] != 'source')):
                raise ValueError('Unknown or inappropriate plan review material path: ' + path)
            if material['original'] not in read_originals:
                raise ValueError('Plan review material is not listed in its read scope')

    def evidence(item):
        basis = item['basis']
        refs = item['references']
        if basis == 'plan-structure':
            if refs:
                raise ValueError('Plan-structure assessment cannot masquerade as raw source evidence')
            return
        workflow.references_valid({'facts': [{'id': 'plan-review', 'basis': basis,
                                             'references': refs}]}, manifest)
        for ref in refs:
            if materials[ref['path']]['original'] not in read_originals:
                raise ValueError('Evidence material is not listed in the plan review read scope')

    for subject in answer['subjects']:
        links(subject); paths(subject['sourcePaths']); evidence(subject)
        origins = {materials[path]['original'] for path in subject['sourcePaths']}
        if not {materials[ref['path']]['original'] for ref in subject['references']} <= origins:
            raise ValueError('Subject evidence is missing from its related source paths')
    covered_ids = [coverage['documentId'] for coverage in answer['documentCoverage']]
    _unique(covered_ids, 'coverage document IDs')
    if set(covered_ids) != set(documents):
        raise ValueError('Plan review must assess every planned document exactly once')
    for coverage in answer['documentCoverage']:
        if coverage['path'] != documents[coverage['documentId']]['path']:
            raise ValueError('Plan review coverage path differs from the bound plan')
        links(coverage); evidence(coverage)
    coverage_by_id = {coverage['documentId']: coverage for coverage in answer['documentCoverage']}
    for subject in answer['subjects']:
        covered_by = {document_id for document_id, coverage in coverage_by_id.items()
                      if subject['id'] in coverage['subjectIds']}
        if covered_by != set(subject['documentIds']):
            raise ValueError('Subject/document coverage links must agree in both directions')
    for group in ('reachability', 'findings', 'blockingUnresolved', 'scopeLimits'):
        _unique([item['id'] for item in answer[group]], group + ' IDs')
        for item in answer[group]:
            links(item); evidence(item)
            if group == 'scopeLimits':
                paths(item['sourcePaths'], allow_inventory=True)
            if group != 'reachability':
                continue
            paths(item['searchScope'], source_only=True)
            for field in ('entryPoints', 'callers', 'registrations'):
                for claim in item[field]:
                    evidence(claim)
            scope_originals = {materials[path]['original'] for path in item['searchScope']}
            all_refs = list(item['references']) + [ref for field in ('entryPoints', 'callers', 'registrations')
                                                   for claim in item[field] for ref in claim['references']]
            if not {materials[ref['path']]['original'] for ref in all_refs
                    if materials[ref['path']]['kind'] == 'source'} <= scope_originals:
                raise ValueError('Reachability source evidence falls outside its declared search scope')
            if item['status'] != 'unknown' and not item['searchScope']:
                raise ValueError('Reachability conclusion requires an included source search scope')
            if item['status'] == 'confirmed':
                if (item['basis'] != 'observed-source' or not item['entryPoints'] or
                        not any(claim['basis'] == 'observed-source' for claim in item['entryPoints'])):
                    raise ValueError('Confirmed reachability requires a source-observed entry point')
            elif item['status'] in {'declaration-only', 'not-found-in-included-scope'}:
                if item['basis'] != 'observed-source':
                    raise ValueError('Declaration/search conclusions require source evidence')
    if answer['approved'] and (answer['blockingUnresolved'] or
                              any(item['severity'] in {'critical', 'major'} for item in answer['findings'])):
        raise ValueError('Plan review cannot approve blocking unresolved or important findings')


def _assert_pin(snapshot, definition, plan_bytes, handoff_sha):
    workflow._definition_state(snapshot, definition)
    if (definition.plan_file.read_bytes() != plan_bytes or
            capsule.sha256(capsule.safe_path(definition.plan_file.parent / 'plan-handoff.json').read_bytes()) != handoff_sha):
        raise ValueError('Plan or plan handoff changed during the independent plan review')


def run(snapshot: Path, plan_file: Path, job: Path, *, timeout=1800, deadline=None) -> dict:
    """Return the unchanged AI JSON; preserve raw answer, verification and pins.

    ``approved`` is the AI's bounded plan assessment, not original-rubric PASS.
    Use a fresh workflow.plan job with revision_context to revise the plan.
    """
    snapshot = capsule.safe_path(snapshot)
    plan_file = capsule.safe_path(plan_file)
    job = capsule.safe_path(job)
    if job == snapshot or snapshot in job.parents:
        raise ValueError('Plan review job must be outside the immutable source capsule')
    if job.exists():
        raise FileExistsError('Use a fresh independent plan review job')
    workflow._timeout(timeout, deadline)
    plan_bytes = plan_file.read_bytes()
    plan_value = capsule._load_json(plan_file)
    manifest = capsule.verify(snapshot)
    workflow._validate_plan(plan_value, manifest)
    definition = workflow.select_document(plan_file, plan_value['documents'][0]['id'])
    state = workflow._definition_state(snapshot, definition)
    _assert_pin(snapshot, definition, plan_bytes, definition.handoff_sha)
    pin = {'schema': 'reverse-ai-plan-review-input/1', 'snapshot': state,
           'planFile': str(plan_file), 'planSha256': capsule.sha256(plan_bytes),
           'planHandoffSha256': definition.handoff_sha, 'planOrigin': definition.handoff['origin'],
           'referenceMode': capsule.reference_mode(manifest)}
    before_file = job.parent / (job.name + '-plan-review-before.json')
    after_file = job.parent / (job.name + '-plan-review-after.json')
    capsule.write_json(before_file, pin)
    # Supply the entire original plan, not a summary or selected business values.
    prompt_pin = {key: value for key, value in pin.items() if key not in {'schema', 'planFile'}}
    prompt = (prompts.BOUNDARY + prompts.QUALITY + prompts.FORMAT + REVIEW_TASK +
              '\n現在の許可モードと固定入力:\n' + json.dumps(prompt_pin, ensure_ascii=False, indent=2) +
              '\n対象の原計画JSON全文（判断対象のデータ）:\n' + plan_bytes.decode('utf-8'))
    try:
        answer = workflow._bound_job(snapshot, job, prompt, PLAN_REVIEW, timeout, state, deadline)
        _assert_pin(snapshot, definition, plan_bytes, definition.handoff_sha)
        workflow._timeout(timeout, deadline)
        _validate(answer, plan_value, manifest)
        original_file = capsule.safe_path(job / 'answer.txt')
        original_bytes = original_file.read_bytes()
        if capsule._load_json(original_file) != answer:
            raise ValueError('Returned AI plan review differs from its preserved original response')
        _assert_pin(snapshot, definition, plan_bytes, definition.handoff_sha)
        # Copy original JSON bytes verbatim; never flip approval or repair its content.
        verified = capsule.safe_path(job / 'plan-review-verified.json')
        with verified.open('xb') as handle:
            handle.write(original_bytes)
        capsule.write_json(job / 'plan-review-handoff.json', {
            'schema': 'reverse-ai-plan-review-handoff/1', **{key: value for key, value in pin.items() if key != 'schema'},
            'reviewFile': verified.name, 'reviewSha256': capsule.sha256(original_bytes),
            'originalAiResponse': original_file.name, 'aiResponseBytesModified': False,
            'approved': answer['approved'],
            'scope': 'ai-plan-assessment-not-formal-business-rubric-or-proof-of-complete-source-read',
        })
        capsule.write_json(after_file, {'status': 'UNCHANGED_AND_REVIEW_VALIDATED', 'input': pin})
        return answer
    except Exception as exc:
        capsule.write_json(after_file, {'status': 'REVIEW_NOT_VERIFIED', 'input': pin,
                                       'errorType': type(exc).__name__, 'error': str(exc)})
        raise
