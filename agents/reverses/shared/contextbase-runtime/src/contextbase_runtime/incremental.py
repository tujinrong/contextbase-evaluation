"""Resumable investigation and review, with replayable composite provenance.

Drafts are never acceptance receipts. Each provider context owns its evidence;
the host reduces explicit submissions and applies the ordinary canonical gates.
"""
from __future__ import annotations

from copy import deepcopy
import hashlib
import json
import time
import uuid

from . import contracts as c, investigation, review_set
from .evidence import EvidenceAccess, EvidenceRequestError, REQUEST_SCHEMA, MAX_REPLY_CHARS
from .evidence_dialog import (_DeliveryProgress, _prior_materials,
                              _material_summary, validate_delivery, WINDOW_POLICY)
from .storage import ArtifactStore
from .material_window import collect_materials


VERSION = 'contextbase-incremental/1'
TRANSPORT = 'codex-ephemeral-incremental'
ORIGIN = 'host-assembled-incremental'
_MAX_INPUT = 1_048_576
_RESERVE = 8192
_COLLECTIONS = ['records', 'unknowns', 'factUsage', 'units', 'feedback', 'checkpoints']
_REQUEST = {'anyOf': [*deepcopy(REQUEST_SCHEMA['anyOf']),
    c.obj({'operation': {'type': 'string', 'const': 'listing'},
           'collection': {'type': 'string', 'enum': _COLLECTIONS},
           'offset': {'type': 'integer', 'minimum': 0},
           'limit': {'type': 'integer', 'minimum': 1, 'maximum': 100}}),
    c.obj({'operation': {'type': 'string', 'const': 'material'},
           'collection': {'type': 'string', 'enum': _COLLECTIONS}, 'key': c.TEXT,
           'offset': {'type': 'integer', 'minimum': 0},
           'limit': {'type': 'integer', 'minimum': 1, 'maximum': 12000}}),
]}
POLICY = '''Versioned incremental investigation protocol contextbase-incremental/1.
The current phase has a SMALL, explicitly assigned result schema. Return the
envelope, using requests to obtain sealed source/facts or paginated materials.
Only the host reads files. Do not run a shell, input code, SQL or other tools.
listing/material expose candidate/draft claims, NOT original source evidence.
retainedMaterials preserves prior candidate pages under their exact object
versions; retainedEvidence contains original text/facts only. Consult visible
retained pages before requesting them again. Cached claims confer no trust,
source delivery or new progress. Evicted pages remain explicitly retrievable.
Source citations require actual read/search delivery in this child task; fact
IDs require its own query delivery. Never treat query pointers as source text.
Use checkpoint to save a draft with remaining questions, or finish this phase.
Do not print the whole repository catalog or whole verification result. The
host assembles explicit submissions without inventing semantic conclusions.
Source facts observe syntax; unresolved calls and absent matches are not proof
of runtime targets or absence. Preserve unsupported/truncated/missing evidence.
Drafts are untrusted. Reviewers must seek counterexamples and omissions from
the original inventory/registrations, including outside the author's plan.
Complete-unit means investigation has ended under the current authorized inputs,
NOT that its facts are resolved or its original obligation is satisfied. It can
finish with blocking unknowns. Keep unavailable/forbidden-input questions as
typed unknowns/followups; do not reread known materials to pretend they can be
answered here. remainingQuestions names only specific executable next actions
within current permissions. Never remove/relabel an unknown merely to finish.
The obligation closure must acknowledge current unresolved blockers; an ended
unit never supplies supported coverage or acceptance. Do not invent counts.
Record key/owner/kind identity is stable. A changed record needs its exact
current normalized SHA in expectedVersions; deletion needs its SHA and reason.
Unknowns/followups persist after record changes. Pending unknownIds may name
existing exact workflow IDs or new unit-local unknown IDs, not invented IDs.
Repeated source delivery, wording changes and completion claims do not prove
progress. Notes are provisional; typed checkpoints hold durable understanding.
The host retains all material off-prompt and exposes explicit pagination. Read
related objects as needed; no visible subset narrows the original obligation.
'''


_CLOSURE_INLINE_CHARS = 262_144
_CLOSURE_POLICY = '''Author obligation closure, before independent verification:
Your only deliverable in this phase is the original obligation's coverage
declaration: supported, unresolved, or not-applicable, with reason and your own
original-source evidence. Use the complete obligation-closure package to see
the original scope, author-declared catalog, ended investigations and every
known unknown/followup. Ended units and object/fact counts do not imply coverage
or correctness. Future-stage questions remain open for their original targets;
never silently close or omit them because current unknowns happen to be empty.
Do not repeat a record-by-record audit of classifications, consumers, call
targets or factUsage here. Those judgments and a fresh whole-scope omission /
counterexample review belong to the following independent review_set tasks.
You may obtain targeted original source to support the scope declaration and
investigate a concrete gap. If a real contradiction or missing prerequisite
affects this obligation, declare unresolved; never claim supported just to end.
The package is unverified author material, not source delivery or a review
pass. Its citations and declaration hashes grant no read/fact authorization.
Positive closure citations must still have been read/searched in THIS child.
Do not regenerate or revise the catalog in this phase. Return the small closure
schema; the host retains the full drafts and runs all independent gates next.
'''


def _json(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(',', ':'), allow_nan=False)


def _basis(task):
    volatile = {'id', 'contextId', 'executionEpoch', 'rootTaskId'}
    return {key: deepcopy(value) for key, value in task.items() if key not in volatile}


def _collections(records=(), unknowns=(), usages=(), units=()):
    def mapping(rows, key):
        return deepcopy(rows) if isinstance(rows, dict) else {row[key]: deepcopy(row) for row in rows}
    return {'records': mapping(records, 'key'), 'unknowns': mapping(unknowns, 'id'),
            'factUsage': mapping(usages, 'recordKey'), 'units': mapping(units, 'id'),
            'feedback': {}, 'checkpoints': {}}


def _material_reply(request, materials, child):
    c.validate(request, _REQUEST)
    if any(type(request[field]) is not int for field in ('offset', 'limit')):
        raise EvidenceRequestError('invalid-position',
            'Material pagination offset/limit require exact integers',
            'Use integer offset and limit from the listing/material contract.')
    values = materials[request['collection']]
    if request['operation'] == 'material':
        if request['key'] not in values:
            raise EvidenceRequestError('unknown-material', 'Unknown investigation material identity',
                'List this collection and use an exact returned key; missing claims are not source evidence.')
        item = values[request['key']]
        encoded = _json(item)
        offset = request['offset']
        end = min(len(encoded), offset + request['limit'])
        result = {'key': request['key'], 'sha256': c.digest(item), 'offset': offset,
                  'totalChars': len(encoded), 'bodyText': encoded[offset:end],
                  'truncated': end < len(encoded), 'nextOffset': end if end < len(encoded) else None}
    else:
        keys = sorted(values)
        selected = keys[request['offset']:request['offset'] + request['limit']]
        rows = [{'key': key, 'sha256': c.digest(values[key]),
                 **{field: values[key][field] for field in ('kind', 'name', 'ownerRequirement')
                    if field in values[key]}} for key in selected]
        while len(_json(rows)) > MAX_REPLY_CHARS - 2048 and rows:
            rows.pop()
        if selected and not rows:
            # Names can be unusually large; the full object remains pageable.
            rows = [{'key': selected[0], 'sha256': c.digest(values[selected[0]])}]
        end = request['offset'] + len(rows)
        result = {'items': rows, 'matchedCount': len(keys), 'returnedCount': len(rows),
                  'truncated': end < len(keys), 'nextOffset': end if end < len(keys) else None}
    reply = {'schema': VERSION, 'taskId': child['id'], 'contextId': child['contextId'],
             'snapshotId': child['snapshotId'], 'collection': request['collection'],
             'requestSha256': c.digest(request), 'status': 'ok', 'result': result,
             'resultSha256': c.digest(result)}
    reply['replySha256'] = c.digest(reply)
    if len(_json(reply)) > MAX_REPLY_CHARS:
        raise ValueError('Investigation material reply exceeds single-reply capacity')
    return reply


def _material_error_reply(request, error, child):
    """A failed candidate lookup is diagnostic, never candidate/source delivery."""
    result = {'error': {'code': error.code, 'message': str(error), 'correction': error.correction}}
    reply = {'schema': VERSION, 'taskId': child['id'], 'contextId': child['contextId'],
             'snapshotId': child['snapshotId'], 'collection': request['collection'],
             'requestSha256': c.digest(request), 'status': 'invalid-request', 'result': result,
             'resultSha256': c.digest(result)}
    reply['replySha256'] = c.digest(reply)
    return reply


def _schema(child, result_schema):
    return c.obj({'protocol': {'type': 'string', 'const': VERSION},
        'taskId': {'type': 'string', 'const': child['id']},
        'action': {'type': 'string', 'enum': ['requests', 'checkpoint', 'finish']},
        'requests': {**c.arr(_REQUEST), 'maxItems': 8},
        'answer': {'anyOf': [deepcopy(result_schema), {'type': 'null'}]},
        'workingNotes': {'type': 'string', 'maxLength': 12000}})


class _MaterialProgress:
    """Count object identities and newly delivered character intervals, not pages."""

    def __init__(self):
        self.objects, self.intervals = set(), {}

    def consume(self, pairs):
        changed = False
        for pair in pairs:
            if pair['reply']['status'] != 'ok':
                continue
            request, result = pair['request'], pair['reply']['result']
            if request['operation'] == 'listing':
                for item in result['items']:
                    identity = (request['collection'], item['key'], item['sha256'])
                    changed |= identity not in self.objects
                    self.objects.add(identity)
            elif request['operation'] == 'material' and result['bodyText']:
                identity = (request['collection'], result['key'], result['sha256'])
                start = result['offset']
                end = start + len(result['bodyText'])
                intervals = self.intervals.setdefault(identity, [])
                cursor = start
                for left, right in sorted(intervals):
                    if left > cursor:
                        break
                    cursor = max(cursor, right)
                changed |= cursor < end
                intervals.append((start, end))
                merged = []
                for left, right in sorted(intervals):
                    if merged and left <= merged[-1][1]:
                        merged[-1] = (merged[-1][0], max(merged[-1][1], right))
                    else:
                        merged.append((left, right))
                self.intervals[identity] = merged
        return changed


def _context(base, number, notes, latest, pairs, instruction, schema, materials):
    from .provider import COMMON_POLICY
    # Reuse origin-aware source/fact deduplication, not the old dialog contract.
    source_latest = [pair for pair in latest if pair['request']['operation'] in
                     {'inventory', 'query', 'read', 'search'}]
    source_pairs = [pair for pair in pairs if pair['request']['operation'] in
                    {'inventory', 'query', 'read', 'search'}]
    visible, prior = _prior_materials(source_latest, source_pairs)
    candidate_visible, candidate_prior = collect_materials(latest, pairs, materials)

    def label(item):
        return {key: deepcopy(item[key]) for key in
                ('kind', 'collection', 'key', 'sha256', 'offset', 'totalChars', 'origin')}

    result = deepcopy(base)
    window = {'policy': deepcopy(WINDOW_POLICY), 'retainedChars': 0,
              'visibleMaterials': [_material_summary(row) for row in visible],
              'evictedMaterials': [],
              'candidateVisibleMaterials': [label(row) for row in candidate_visible],
              'candidateEvictedMaterials': [],
              'candidateTrust': 'Untrusted model/host claims; not original source delivery.'}
    result['evidenceDialog'] = {'protocol': VERSION, 'round': number, 'workingNotes': notes,
        'latestEvidence': deepcopy(latest), 'retainedEvidence': [], 'retainedMaterials': [],
        'evidenceWindow': window,
        'deliveryLedger': [{'request': pair['request'], 'replySha256': pair['reply']['replySha256']}
                           for pair in pairs]}
    if any(pair['reply']['status'] == 'invalid-request' for pair in latest):
        # Keep old successful contexts byte-compatible. This advice appears
        # only after a request failure; the bound receipts carry the details.
        result['evidenceDialog']['requestErrorRecovery'] = (
            'Correct invalid-request items using result.error.correction. Other ok items in the '
            'batch were delivered normally. Errors supply no evidence, facts or progress. '
            'query/search accept an exact acquired file or a canonical directory prefix ending '
            'in /. read requires an exact acquired file. Use inventory/listing to find identities; '
            'preserve unavailable-input gaps as unknowns rather than retrying invalid requests.')
    size = lambda value: len(instruction) + len(POLICY) + len(COMMON_POLICY) + len(_json(schema)) + len(_json(value)) + _RESERVE
    budget = max(0, min(WINDOW_POLICY['maxChars'], _MAX_INPUT - size(result) - 64))
    rank = {pair['reply']['replySha256']: index for index, pair in enumerate(pairs)}
    combined = [('source', row) for row in prior] + [('candidate', row) for row in candidate_prior]
    combined.sort(key=lambda item: rank[item[1]['replySha256'] if item[0] == 'source'
                                         else item[1]['origin']['replySha256']], reverse=True)
    used = 0
    for kind, row in combined:
        cost = len(_json(row)) + 1
        if used + cost <= budget:
            slot = 'retainedEvidence' if kind == 'source' else 'retainedMaterials'
            result['evidenceDialog'][slot].append(row)
            used += cost
            if kind == 'source':
                window['visibleMaterials'].append(_material_summary(row))
            else:
                window['candidateVisibleMaterials'].append(label(row))
        else:
            if kind == 'source':
                window['evictedMaterials'].append(_material_summary(row))
            else:
                window['candidateEvictedMaterials'].append(label(row))
    window['retainedChars'] = (len(_json(result['evidenceDialog']['retainedEvidence']))
                               + len(_json(result['evidenceDialog']['retainedMaterials'])) - 4)
    if size(result) > _MAX_INPUT:
        raise ValueError('Incremental unit exceeds single-call capacity; retain drafts and split its question')
    return result


def _base_context(root_context, child, phase, unit, materials):
    manifest = root_context['inventory']
    # Complete source and candidate collections are pageable; no full view is
    # silently truncated or duplicated into every child prompt.
    task_fields = ('id', 'contextId', 'rootTaskId', 'stage', 'operation', 'requirements',
                   'goalRequirements', 'goalRequirementIds', 'snapshotId', 'candidate',
                   'viewSha256', 'sourceFactsSha256', 'catalogPolicy', 'recordKinds')
    task = {field: deepcopy(child[field]) for field in task_fields if field in child}
    targets = {}
    for collection, keys in (('records', (unit or {}).get('recordKeys', [])),
                             ('unknowns', (unit or {}).get('unknownIds', []))):
        rows = {key: materials[collection][key] for key in keys}
        targets[collection] = rows if len(_json(rows)) <= 20000 else {
            key: {'key': key, 'sha256': c.digest(row), 'delivery': 'listing/material pages'}
            for key, row in rows.items()}
        if phase == 'review' and len(_json(rows)) > 20000:
            for key, row in rows.items():
                targets[collection][key]['materialSha256'] = c.digest(row)
                if collection == 'records':
                    targets[collection][key]['recordSha256'] = row['version']
                else:
                    targets[collection][key]['unknownSha256'] = row['sha256']
    inventory = {key: deepcopy(value) for key, value in manifest.items() if key not in {'files', 'omitted'}}
    inventory.update(files=deepcopy(manifest['files'][:100]), fileCount=len(manifest['files']),
                     truncated=len(manifest['files']) > 100, omittedCount=len(manifest.get('omitted', [])))
    structure = root_context.get('structure', {})
    plan_map, map_size = [], 0
    for planned in materials['units'].values():
        # Small responsibility map prevents re-reading the whole plan merely
        # to distinguish this unit from its neighbours. Full definitions page.
        row = {field: planned[field] for field in ('id', 'requirement', 'question') if field in planned}
        if map_size + len(_json(row)) > 16000:
            break
        plan_map.append(row)
        map_size += len(_json(row))
    checkpoint = materials.get('checkpoints', {}).get((unit or {}).get('id'))
    result = {'task': task, 'request': root_context['request'], 'inventory': inventory,
        'structure': {key: deepcopy(structure[key]) for key in ('schema', 'snapshotId', 'indexSha256', 'counts') if key in structure},
        'incremental': {'phase': phase, 'unit': deepcopy(unit),
            'collections': {key: len(value) for key, value in materials.items()},
            'feedbackKeys': sorted(materials['feedback']),
            'continuation': deepcopy(checkpoint['summary']) if checkpoint else None,
            'planMap': {'units': plan_map, 'totalUnits': len(materials['units']),
                        'truncated': len(plan_map) < len(materials['units']),
                        'trust': 'Investigation responsibilities, not source or accepted facts.'},
            'trust': 'Draft/candidate materials are claims. Obtain original source independently.'},
        'reviewTargets': targets,
        'sourceDelivery': {'mode': 'host-incremental-requests',
                           'instruction': 'All sealed files remain available through inventory/query/search/read.'}}
    if phase == 'review':
        classifications = {item['key']: item['sha256'] for item in child.get('classificationBindings', [])}
        questions = {item['id']: item['sha256'] for item in child.get('unknownBindings', [])}
        result['reviewBindings'] = {
            'meaning': 'materialSha256 seals the complete pageable JSON object only. Copy recordSha256 '
                       'for recordChecks/classificationChecks and unknownSha256 for unknownChecks; '
                       'these expected review versions are different from materialSha256. Bindings '
                       'grant no source evidence, correctness judgment or independent acceptance.',
            'records': [{'key': key, 'materialSha256': c.digest(materials['records'][key]),
                         'recordSha256': materials['records'][key]['version']}
                        for key in (unit or {}).get('recordKeys', [])],
            'classifications': [{'key': key, 'materialSha256': c.digest(materials['records'][key]),
                                 'recordSha256': classifications[key]}
                                for key in (unit or {}).get('recordKeys', []) if key in classifications],
            'unknowns': [{'unknownId': key, 'materialSha256': c.digest(materials['unknowns'][key]),
                          'unknownSha256': questions[key]}
                         for key in (unit or {}).get('unknownIds', [])]}
    if phase == 'draft':
        result['incremental']['instruction'] = (
            'Continue from the exact checkpoint summary when present; inspect only its remaining '
            'executable actions and meaningful new gaps, rather than restarting the original question. '
            'Submitted record hashes describe prior unit proposals; sha256 bindings describe CURRENT '
            'merged records and are the CAS versions. Full checkpoint answers are pageable. '
            'Submit only new or explicitly revised records. End investigation with complete=true and '
            'remainingQuestions:[] when all currently executable actions are exhausted, even if an '
            'input gap remains as a typed blocking unknown. Preserve that unknown and let the original '
            'obligation closure and independent review judge the unresolved scope.')
    elif phase == 'closure':
        result['incremental']['instruction'] = (
            'Submit only the original obligation coverage declaration and known scope gaps; '
            'the following independent review_set checks each record and scope from source. '
            'Ended units are author claims, never supported coverage or acceptance. '
            'All unknowns and future followups remain open unless independently resolved.')
        package = materials['feedback'].get('obligation-closure')
        if package is not None:
            encoded = _json(package)
            block = {'schema': package['schema'], 'sha256': c.digest(package),
                     'totalChars': len(encoded), 'totalUtf8Bytes': len(encoded.encode('utf-8')),
                     'counts': deepcopy(package['counts']), 'collection': 'feedback',
                     'key': 'obligation-closure',
                     'trust': 'Unverified author claims; no source delivery or independent acceptance.'}
            if len(encoded) <= _CLOSURE_INLINE_CHARS and block['totalUtf8Bytes'] <= _CLOSURE_INLINE_CHARS:
                block.update(delivery='complete-inline', package=deepcopy(package))
            else:
                block.update(delivery='pageable', instruction=(
                    'The complete package exceeds inline capacity. Read feedback/obligation-closure '
                    'with material pages; totalChars and object hash bind all sections, including '
                    'every unknown and followup. Counts are not a substitute for omitted content.'))
            result['incremental']['obligationClosurePackage'] = block
    elif phase == 'review' and unit['kind'] == 'global':
        result['incremental']['instruction'] = 'Independently search original registrations, reverse uses, project membership, data definitions and unsupported materials for objects absent from the catalog and cross-unit contradictions. Local passes do not prove coverage.'
    return result


def _dialog(source, index, store, task, root_context, phase, unit, materials,
            instruction, result_schema, provider, timeout, check_current, cached=None, rejection=None):
    """One bounded unit; completed calls retain their original identities on resume."""
    if phase == 'closure':
        # Keep all completed plan/draft/review prompts and schemas unchanged.
        # Only a not-yet-completed closure receives the narrower phase policy.
        instruction += '\n' + _CLOSURE_POLICY
    if cached:
        saved_setup = store.get('calls/' + cached + '/setup.json')
        rejection = saved_setup.get('rejection')
    materials = deepcopy(materials)
    if rejection:
        prior = store.get('calls/' + rejection['call'] + '/complete.json')
        raw = store.get('calls/' + rejection['call'] + f"/round-{len(prior['rounds']):04d}.json")
        materials['feedback']['rejected-unit'] = {
            'error': rejection['error'], 'call': rejection['call'],
            'trust': 'Rejected response, not evidence or acceptance.',
            'answer': raw['response']['answer']['answer']}
    if cached is None:
        child = {**deepcopy(task), 'id': uuid.uuid4().hex, 'contextId': uuid.uuid4().hex,
                 'rootTaskId': task['id']}
        call_id = child['id']
        prefix = 'calls/' + call_id
        base = _base_context(root_context, child, phase, unit, materials)
        setup = {'schema': VERSION, 'basis': _basis(task), 'task': child,
                 'phase': phase, 'unit': unit, 'materials': materials,
                 'context': base, 'instruction': instruction, 'resultSchema': result_schema,
                 'rejection': rejection}
        check_current()
        store.put(prefix + '/setup.json', setup)
    else:
        call_id = cached
        prefix = 'calls/' + call_id
        setup = store.get(prefix + '/setup.json')
        child = setup['task']
        base = _base_context(root_context, child, phase, unit, materials)
        if (setup['schema'] != VERSION or setup['basis'] != _basis(task)
                or _basis(child) != _basis(task) or setup['phase'] != phase or setup['unit'] != unit
                or setup['materials'] != materials or setup['context'] != base
                or setup['instruction'] != instruction or setup['resultSchema'] != result_schema):
            raise ValueError('Incremental continuation or frozen review binding changed')
    access = EvidenceAccess(source, index, child)
    schema = _schema(child, result_schema)
    wire_schema = c.transport_schema(child, schema)
    previous = c.digest(setup)
    latest, pairs, notes, pointers = [], [], '', []
    progress, material_progress, repeated = _DeliveryProgress(), _MaterialProgress(), 0
    number = 1
    completed = store.get(prefix + '/complete.json') if cached else None
    while True:
        check_current()
        context = _context(base, number, notes, latest, pairs, instruction, wire_schema, materials)
        prompt = instruction + '\n' + POLICY + '\n' + _json(context)
        if cached:
            row = store.get(prefix + f'/round-{number:04d}.json')
            response = row['response']
            if row['context'] != context or row['promptSha256'] != hashlib.sha256(prompt.encode('utf-8')).hexdigest():
                raise ValueError('Incremental prompt or context replay changed')
        else:
            job = store.path(prefix + f'/provider/round-{number:04d}')
            response = provider(source.root, job, prompt, wire_schema, timeout)
            store.put(prefix + f'/round-{number:04d}-response.json', response)
            check_current()
        if response.get('exit_code') != 0 or response.get('metadata', {}).get('status') != 'passed':
            raise RuntimeError('Incremental provider failed; completed draft/review checkpoints were retained')
        wrapper = response.get('answer')
        c.validate(wrapper, schema)
        if wrapper['action'] == 'requests':
            if not wrapper['requests'] or wrapper['answer'] is not None:
                raise ValueError('Incremental requests require nonempty requests and no answer')
        elif wrapper['requests'] or wrapper['answer'] is None:
            raise ValueError('Incremental checkpoint/finish requires an answer and no requests')
        elif wrapper['action'] == 'checkpoint' and phase != 'draft':
            raise ValueError('Only investigation drafts support intermediate checkpoints')
        latest = []
        for request in wrapper['requests']:
            check_current()
            if request['operation'] in {'listing', 'material'}:
                try:
                    reply = _material_reply(request, materials, child)
                except EvidenceRequestError as error:
                    reply = _material_error_reply(request, error, child)
            else:
                try:
                    reply = access.handle(request)
                except EvidenceRequestError as error:
                    reply = access.error_reply(request, error)
            latest.append({'request': deepcopy(request), 'reply': reply})
        record = {'previousSha256': previous, 'number': number, 'context': context,
                  'promptSha256': hashlib.sha256(prompt.encode('utf-8')).hexdigest(),
                  'response': response, 'pairs': latest}
        if cached:
            if record != row or completed['rounds'][number - 1] != c.digest(record):
                raise ValueError('Incremental source deliveries or provider trace changed')
        else:
            check_current()
            store.put(prefix + f'/round-{number:04d}.json', record)
        previous = c.digest(record)
        pointers.append(previous)
        if wrapper['action'] != 'requests':
            answer = wrapper['answer']
            c.validate(answer, result_schema)
            validate_delivery(source, answer, [pair for pair in pairs if pair['request']['operation'] in
                                              {'inventory', 'query', 'read', 'search'}])
            result = {'schema': VERSION, 'call': call_id, 'rounds': pointers,
                      'answerSha256': c.digest(answer), 'action': wrapper['action']}
            if cached and completed != result:
                raise ValueError('Incremental completed invocation binding changed')
            check_current()
            if not cached:
                store.put(prefix + '/complete.json', result)
            return answer, call_id
        new_data = progress.consume([pair for pair in latest if pair['request']['operation'] in
                                     {'inventory', 'query', 'read', 'search'}])
        new_data |= material_progress.consume(latest)
        repeated = 0 if new_data else repeated + 1
        if repeated >= 3:
            raise ValueError('Incremental unit made no source, material or draft progress; split or clarify its question')
        pairs.extend(latest)
        notes = wrapper['workingNotes']
        number += 1


def _checkpoint_materials(task, events, reduced, units):
    """Expose exact prior proposals separately from the current merged versions."""
    result = {}
    current = {row['key']: row for row in reduced['records']}
    for unit in units:
        prior = [event['answer'] for event in events if event['unit']['id'] == unit['id']]
        if not prior:
            continue
        submissions = {record['key']: record for answer in prior for record in answer['records']}
        questions = [row for row in reduced['unknowns'] if row['id'].startswith(unit['id'] + ':')]
        result[unit['id']] = {'summary': {
            'schema': 'contextbase-unit-continuation/1',
            'previousAnswerSha256': c.digest(prior[-1]),
            'remainingQuestions': deepcopy(prior[-1]['remainingQuestions']),
            'recordKeys': list(submissions),
            'recordBindings': [{'key': key,
                'sha256': c.digest(current[key]) if key in current else None,
                'submittedSha256': c.digest(submitted)} for key, submitted in submissions.items()],
            'unknownIds': [row['id'] for row in questions],
            'unknownBindings': [{'id': row['id'], 'sha256': c.digest(row)} for row in questions],
            'currentMergedRecordsSha256': c.digest(reduced['records']),
            'completionMeaning': 'Ended authorized investigation, not resolved facts or accepted obligation.'},
            'lastAnswer': deepcopy(prior[-1])}
    return result


def _closure_package(task, context, units, events, reduced):
    """Project complete author declarations, without deriving a coverage verdict.

    Kept under the existing feedback collection to preserve the request wire
    enum and every already-completed non-closure invocation on continuation.
    All references below point to claims; actual read/query rights remain in
    the child task's recorded evidence requests alone.
    """
    records = {**context.get('currentRecords', {}),
               **{row['key']: row for row in reduced['records']}}
    unknowns = {**context.get('currentUnknowns', {}),
                **{row['id']: row for row in reduced['unknowns']}}
    usages = {row['recordKey']: row for row in reduced['factUsage']}
    catalog_rows = []
    for key in sorted(records):
        record = records[key]
        classification = record.get('classification')
        row = {field: deepcopy(record[field]) for field in
               ('key', 'name', 'kind', 'ownerRequirement', 'basis', 'evidence', 'dependsOn')
               if field in record}
        row.update(sha256=c.digest(record),
                   classification={field: deepcopy(value) for field, value in classification.items()
                                   if field not in {'rationale', 'alternative'}} if classification else None,
                   fullRecord={'collection': 'records', 'key': key})
        if record['kind'] == 'system':
            row['statement'] = record['statement']
        catalog_rows.append(row)
    unit_rows = []
    for unit in units:
        answers = [event['answer'] for event in events if event['unit']['id'] == unit['id']]
        last = answers[-1] if answers else None
        submitted = {row['key']: row for answer in answers for row in answer['records']}
        unit_rows.append({**{field: deepcopy(unit[field]) for field in
                            ('id', 'requirement', 'question', 'paths')},
                          'investigationEnded': bool(last and last['complete'] and not last['remainingQuestions']),
                          'lastAnswerSha256': c.digest(last) if last is not None else None,
                          'remainingQuestions': deepcopy(last['remainingQuestions']) if last else [unit['question']],
                          'recordKeys': sorted(submitted),
                          'recordBindings': [{'key': key,
                              'sha256': c.digest(records[key]) if key in records else None,
                              'submittedSha256': c.digest(submitted[key])} for key in sorted(submitted)]})
    fact_declarations = [{'recordKey': key, 'recordSha256': c.digest(records[key]),
                          'declarationPresent': key in usages,
                          'declaredFactIdCount': len(usages[key]['factIds']) if key in usages else None,
                          'declarationSha256': c.digest(usages[key]) if key in usages else None,
                          'fullDeclaration': {'collection': 'factUsage', 'key': key} if key in usages else None}
                         for key in sorted(records)]
    manifest = context['inventory']
    followup_claims = {}
    prior = context.get('feedback', {}).get('candidate', {}).get('answer', {}).get('followups', [])
    for row in [*reduced['followups'], *context.get('handoffQuestions', []), *prior]:
        followup_claims.setdefault(c.digest(row), deepcopy(row))
    followups = [{'sha256': version, 'content': row} for version, row in followup_claims.items()]
    return {'schema': 'contextbase-obligation-closure/1',
            'trust': 'Unverified author declarations. Unit completion, counts and hashes are not '
                     'supported coverage, source delivery, fact-usage approval or independent acceptance.',
            'goal': deepcopy(context['request']['goal']),
            'assignedRequirements': list(task['requirements']),
            'catalogSha256': c.digest(records), 'units': unit_rows, 'catalog': catalog_rows,
            'unknowns': [{'id': key, 'sha256': c.digest(value), 'content': deepcopy(value)}
                         for key, value in sorted(unknowns.items())],
            'followups': followups, 'factUsageIndexSha256': task.get('sourceFactsSha256'),
            'factUsage': fact_declarations,
            'input': {'snapshotId': task['snapshotId'], 'manifestContentSha256': c.digest(manifest),
                      'allowedPaths': deepcopy(context['request']['allowedPaths']),
                      'excludedPaths': deepcopy(context['request']['excludedPaths']),
                      'acquiredFiles': deepcopy(manifest['files']),
                      'omitted': deepcopy(manifest['omitted'])},
            'counts': {'units': len(unit_rows),
                       'endedInvestigations': sum(row['investigationEnded'] for row in unit_rows),
                       'records': len(catalog_rows), 'unknowns': len(unknowns),
                       'followups': len(followups), 'factUsageDeclarations': len(usages),
                       'acquiredFiles': len(manifest['files']), 'omittedMaterials': len(manifest['omitted'])}}


def _drive(task, context, invoke, validate_final=None):
    """Replay the same phase machine for execution, continuation and adoption."""
    if task['operation'] == 'verify':
        view = context['verificationView']
        units = review_set.make_units(task, view)
        usages = context['candidate']['answer'].get('factUsage', [])
        materials = _collections(view['records'], view['unknowns'], usages, units)
        answers = []
        for unit in units:
            answer = invoke('review', unit, materials, review_set.unit_schema(task, view, unit))
            try:
                review_set.validate_unit(task, view, unit, answer)
            except ValueError as exc:
                invoke.reject(exc)
                raise
            invoke.commit()
            answers.append(answer)
        return review_set.aggregate(task, view, units, answers)
    retained = context.get('currentRecords', {})
    old_unknowns = context.get('currentUnknowns', {})
    plan = invoke('plan', None, _collections(retained, old_unknowns), investigation.plan_schema(task))
    try:
        investigation.validate_plan(task, plan)
    except ValueError as exc:
        invoke.reject(exc)
        raise
    invoke.commit()
    units, events, latest = deepcopy(plan['units']), [], {}
    unchanged, repairs, failed_basis = 0, 0, None
    turns = {}
    repeated_failure, unproductive_expansions = 0, 0
    while True:
        eligible = [item for item in units if item['id'] not in latest or
                    not latest[item['id']]['complete'] or latest[item['id']]['remainingQuestions']]
        # Deterministic fair passes: each planned unit gets a turn before an
        # unfinished earlier unit repeats. Continuation/replay follow the same.
        unit = min(eligible, key=lambda item: turns.get(item['id'], 0)) if eligible else None
        if unit is None:
            if set(latest) != {item['id'] for item in units}:
                raise ValueError('Investigation has unfinished planned units')
            reduced = investigation.reduce_drafts(task, events)
            materials = _collections({**retained, **{row['key']: row for row in reduced['records']}},
                {**old_unknowns, **{row['id']: row for row in reduced['unknowns']}}, reduced['factUsage'], units)
            materials['feedback']['obligation-closure'] = _closure_package(task, context, units, events, reduced)
            closures = []
            for key in task['requirements']:
                closure = invoke('closure', {'requirement': key}, materials, investigation.closure_schema(task, key))
                if closure['status'] != 'unresolved' and not closure['evidence']:
                    error = ValueError('A positive obligation closure requires original-source evidence')
                    invoke.reject(error)
                    raise error
                invoke.commit()
                closures.append(closure)
            result = investigation.canonical_answer(task, events, closures)
            try:
                if validate_final is not None:
                    validate_final(result)
            except ValueError as exc:
                # Mechanical failures return to explicit, model-authored local
                # corrections. No host guesses or full-catalog regeneration.
                same_failure = (failed_basis is not None and failed_basis[0] == str(exc)
                                and not investigation.structural_progress(failed_basis[1], reduced))
                repeated_failure = repeated_failure + 1 if same_failure else 1
                failed_basis = (str(exc), deepcopy(reduced))
                if repeated_failure >= 3:
                    raise ValueError('Incremental reconciliation repeated without structural progress: ' + str(exc)) from exc
                repairs += 1
                for key in task['requirements']:
                    units.append({'id': 'repair-' + str(repairs) + '-' + c.digest(key)[:12],
                        'requirement': key, 'paths': [],
                        'question': 'Correct this mechanical candidate error only in your owned records, '
                            'using exact CAS versions and source evidence. Preserve all unknowns and '
                            'other records; use listing/material to locate affected identities. Error: ' + str(exc)[:2048]})
                investigation.validate_plan(task, {'units': units})
                continue
            return result
        before = investigation.reduce_drafts(task, events)
        records = {**retained, **{row['key']: row for row in before['records']}}
        materials = _collections(records, {**old_unknowns, **{row['id']: row for row in before['unknowns']}},
                                  before['factUsage'], units)
        materials['checkpoints'] = _checkpoint_materials(task, events, before, units)
        answer = invoke('draft', unit, materials, investigation.draft_schema(task, unit))
        proposed = [*events, {'unit': deepcopy(unit), 'answer': answer}]
        try:
            after = investigation.reduce_drafts(task, proposed)
            next_units = deepcopy(units)
            for added in answer['addUnits']:
                existing = next((item for item in next_units if item['id'] == added['id']), None)
                if existing is not None and existing != added:
                    raise ValueError('Planned unit identity cannot be silently replaced')
                if existing is None:
                    next_units.append(deepcopy(added))
            investigation.validate_plan(task, {'units': next_units})
        except ValueError as exc:
            invoke.reject(exc)
            raise
        progressed = investigation.structural_progress(before, after)
        if progressed:
            unchanged = 0
            unproductive_expansions = 0
        else:
            # An ended finite empty check needs no further turn. Repeated
            # unfinished work accumulates across units, never by unit identity.
            if not answer['complete'] or answer['remainingQuestions']:
                unchanged += 1
            # Finite, preplanned empty checks may be legitimate. Dynamically
            # inventing fresh unit IDs is not durable understanding progress.
            unproductive_expansions += len({item['id'] for item in next_units} -
                                            {item['id'] for item in units})
        if unchanged >= 3 or unproductive_expansions >= 3:
            error = ValueError('Incremental investigation repeated or expanded without structural progress')
            invoke.reject(error)
            raise error
        invoke.commit()
        units = next_units
        turns[unit['id']] = turns.get(unit['id'], 0) + 1
        events, latest[unit['id']] = proposed, answer


def run(source, index, store, task, context, instruction, provider, timeout, check_current,
        validate_final=None):
    if task.get('incrementalPolicy') != VERSION or task.get('reviewSetPolicy') != review_set.VERSION:
        raise ValueError('An explicit versioned incremental/review-set contract is required')
    started = time.perf_counter()
    if context.get('task') != task:
        raise ValueError('Incremental root context must belong to its exact issued task')
    store.put('tasks/' + task['id'] + '/context.json', context)
    basis = _basis(task)
    prefix = 'workflows/' + c.digest(basis)
    work = ArtifactStore(store.path(prefix))
    check_current()
    if not work.path('state.json').exists():
        work.save_state({'schema': VERSION, 'basis': basis, 'trace': [], 'rejections': {}})
    checkpoint = work.get('state.json')
    if checkpoint['schema'] != VERSION or checkpoint['basis'] != basis:
        raise ValueError('Incremental checkpoint basis changed')
    trace, used, pending = list(checkpoint['trace']), [], {}
    feedback = {}
    if context.get('feedback'):
        feedback['previous-candidate'] = context['feedback']['candidate']
        feedback.update({'verification-' + str(n): row
                         for n, row in enumerate(context['feedback']['verifications'])})
    feedback.update({'handoff-question-' + str(n): row
                     for n, row in enumerate(context.get('handoffQuestions', []))})
    def invoke(phase, unit, materials, result_schema):
        number = len(used)
        cached = trace[number] if number < len(trace) else None
        materials = deepcopy(materials)
        materials['feedback'].update(feedback)
        answer, call_id = _dialog(source, index, work, task, context, phase, unit, materials,
                                  instruction, result_schema, provider, timeout, check_current, cached,
                                  checkpoint.get('rejections', {}).get(str(number)))
        pending.update(call=call_id, cached=cached)
        return answer
    def commit():
        call_id, cached = pending.pop('call'), pending.pop('cached')
        if not cached:
            with work.transaction() as state:
                check_current()
                if state['basis'] != basis or state['trace'] != used:
                    raise ValueError('Another incremental continuation changed this checkpoint')
                state['trace'] = [*used, call_id]
                state.setdefault('rejections', {}).pop(str(len(used)), None)
                work.save_state(state)
        used.append(call_id)
    def reject(error):
        with work.transaction() as state:
            check_current()
            state.setdefault('rejections', {})[str(len(used))] = {
                'call': pending['call'], 'error': type(error).__name__ + ': ' + str(error)[:2048]}
            work.save_state(state)
    invoke.commit, invoke.reject = commit, reject
    answer = _drive(task, context, invoke, validate_final)
    if len(used) < len(trace):
        raise ValueError('Incremental continuation left unmatched completed invocations')
    check_current()
    manifest = {'schema': VERSION, 'reviewSetPolicy': review_set.VERSION,
        'basis': basis, 'workflow': prefix, 'trace': used, 'context': context,
        'instruction': instruction, 'answerSha256': c.digest(answer)}
    store.put('tasks/' + task['id'] + '/incremental.json', manifest)
    new_usage, phase_counts = {}, {}
    for position, pointer in enumerate(used):
        setup = work.get('calls/' + pointer + '/setup.json')
        phase_counts[setup['phase']] = phase_counts.get(setup['phase'], 0) + 1
        if position < len(trace):
            continue
        completed = work.get('calls/' + pointer + '/complete.json')
        for number in range(1, len(completed['rounds']) + 1):
            response = work.get('calls/' + pointer + f'/round-{number:04d}.json')['response']
            for key, value in (response.get('usage') or {}).items():
                if type(value) in (int, float):
                    new_usage[key] = new_usage.get(key, 0) + value
    return {'exit_code': 0, 'answer': answer,
            'usage': new_usage or None,
            'metadata': {'status': 'passed', 'responseOrigin': ORIGIN,
                         'incrementalTranscriptSha256': c.digest(manifest),
                         'completedInvocations': len(used), 'phaseInvocations': phase_counts,
                         'reusedInvocations': min(len(trace), len(used)),
                         'usageScope': 'New validated component calls only; rejected/faulted calls retain their raw usage separately.',
                         'seconds': time.perf_counter() - started}}


def status(store):
    """Diagnostic checkpoint progress; these counts confer no acceptance."""
    directory = store.path('workflows')
    if not directory.exists():
        return []
    result = []
    for path in sorted(directory.iterdir()):
        work = ArtifactStore(path)
        if not work.path('state.json').exists():
            continue
        state = work.get('state.json')
        units, latest, counts = {}, {}, {}
        for pointer in state['trace']:
            prefix = 'calls/' + pointer
            setup = work.get(prefix + '/setup.json')
            completed = work.get(prefix + '/complete.json')
            answer = work.get(prefix + f"/round-{len(completed['rounds']):04d}.json")['response']['answer']['answer']
            phase = setup['phase']
            counts[phase] = counts.get(phase, 0) + 1
            if phase == 'plan':
                units.update({unit['id']: unit for unit in answer['units']})
            elif phase == 'draft':
                units[setup['unit']['id']] = setup['unit']
                units.update({unit['id']: unit for unit in answer['addUnits']})
                latest[setup['unit']['id']] = answer
        finished = [key for key, answer in latest.items()
                    if answer['complete'] and not answer['remainingQuestions']]
        result.append({'workflow': path.name, 'stage': state['basis']['stage'],
            'operation': state['basis']['operation'], 'requirements': state['basis']['requirements'],
            'completedDraftUnits': finished, 'remainingDraftUnits': sorted(set(units) - set(finished)),
            'unitCompletionMeaning': 'Authorized investigation ended; blocking unknowns may remain.',
            'phaseInvocations': counts, 'rejectedPositions': list(state.get('rejections', {})),
            'trust': 'Unadopted checkpoints. Acceptance is represented only by session receipts.'})
    return result


def replay(source, index, store, task, answer, transcript_sha256, validate_final=None):
    manifest = store.get('tasks/' + task['id'] + '/incremental.json')
    if (manifest['schema'] != VERSION or manifest['reviewSetPolicy'] != review_set.VERSION
            or task.get('incrementalPolicy') != VERSION
            or manifest['basis'] != _basis(task) or c.digest(manifest) != transcript_sha256
            or manifest['context'].get('task') != task
            or manifest['context'] != store.get('tasks/' + task['id'] + '/context.json')
            or manifest['answerSha256'] != c.digest(answer)
            or manifest['workflow'] != 'workflows/' + c.digest(_basis(task))):
        raise ValueError('Incremental composite provenance binding changed')
    work = ArtifactStore(store.path(manifest['workflow']))
    used = []
    def invoke(phase, unit, materials, result_schema):
        if len(used) >= len(manifest['trace']):
            raise ValueError('Incremental composite omitted a required invocation')
        pointer = manifest['trace'][len(used)]
        materials = deepcopy(materials)
        root_context = manifest['context']
        if root_context.get('feedback'):
            materials['feedback']['previous-candidate'] = root_context['feedback']['candidate']
            materials['feedback'].update({'verification-' + str(n): row
                for n, row in enumerate(root_context['feedback']['verifications'])})
        materials['feedback'].update({'handoff-question-' + str(n): row
            for n, row in enumerate(root_context.get('handoffQuestions', []))})
        result, call_id = _dialog(source, index, work, task, manifest['context'], phase, unit,
            materials, manifest['instruction'], result_schema, None, None, lambda: None, pointer)
        used.append(call_id)
        return result
    invoke.commit = lambda: None
    invoke.reject = lambda error: None
    rebuilt = _drive(task, manifest['context'], invoke, validate_final)
    if rebuilt != answer or used != manifest['trace']:
        raise ValueError('Incremental deterministic materialization differs from the canonical answer')
