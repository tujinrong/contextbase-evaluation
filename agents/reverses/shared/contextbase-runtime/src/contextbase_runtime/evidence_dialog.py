"""Host-owned evidence conversations with a canonical, independently checked end.

Round receipts prove what was supplied, not what the model understood. The
controller still validates and adopts the entire canonical proposal view.
"""
from __future__ import annotations

from copy import deepcopy
import hashlib
import json
import time

from . import contracts
from .evidence import EvidenceAccess, REQUEST_SCHEMA
from .sources import source_lines


VERSION = 'contextbase-evidence-dialog/1'
WINDOW_POLICY = {'schema': 'contextbase-evidence-window/1', 'maxChars': 524_288,
                 'ordering': 'recent-delivery-first'}
MAX_INPUT_CHARS = 1_048_576
INPUT_RESERVE_CHARS = 8_192
MAX_NOTES_CHARS = 12_000
POLICY = '''Host evidence conversation:
Return the versioned dialog envelope. Use action=requests for host evidence
queries and action=finish only for the complete canonical analysis answer.
Do not invoke a shell or any other tools. The host alone reads sealed source.
The request schema supports inventory, syntax-fact query, literal source search,
and exact source read. Nullable filters mean no filter; paginate explicitly.
Calls are syntax observations, not resolved semantic targets. A zero-match
query, a truncated page, and an unsupported capability do not prove absence.
Every final source citation must be covered by original text returned through
read/search in THIS task; query evidence pointers alone are not original text.
Every claimed fact ID must have been supplied by a query in THIS task.
Latest evidence and the bounded retainedEvidence window are visible in full.
The window preserves prior original text and facts when capacity permits a
joint comparison. evidenceWindow lists visible and evicted materials explicitly.
Evicted evidence remains available by repeating its recorded request; retrieval
from this same-task window is not new investigation progress.
Use workingNotes for your provisional investigation notes across rounds;
they are untrusted notes, not adopted facts or evidence. Update rather than
append notes, and reread earlier material when necessary to check a claim.
The complete goal, unknowns and candidate view remain the review obligation.
Do not skip retained records or unknowns because they are outside the latest
evidence page. Independently inspect registration points, reverse uses and
unexamined materials for omissions, not only the author's selected citations.
The delivery ledger is not a semantic coverage verdict. Preserve uncertainty
and all original output-contract obligations. For requests, answer must be null
and requests must be nonempty. For finish, requests must be empty and answer
must contain the complete canonical result, not a patch or an evidence summary.
Three consecutive request rounds without new original source lines, fact IDs,
or inventory materials stop the dialog. Changing filters or offsets alone is
not progress; oversized items and empty pages do not supply evidence.
'''


def _json(value):
    # ArtifactStore serializes object keys canonically. Use the same logical
    # ordering before the first call so a reopened transcript reproduces bytes.
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(',', ':'), allow_nan=False)


def _hash_text(value):
    return hashlib.sha256(value.encode('utf-8')).hexdigest()


def response_schema(task, result_schema):
    """Separate the retrieval protocol from the canonical business contract."""
    return contracts.obj({
        'protocol': {'type': 'string', 'const': VERSION},
        'taskId': {'type': 'string', 'const': task['id']},
        'action': {'type': 'string', 'enum': ['requests', 'finish']},
        'requests': {**contracts.arr(REQUEST_SCHEMA), 'maxItems': 8},
        'answer': {'anyOf': [deepcopy(result_schema), {'type': 'null'}]},
        'workingNotes': {'type': 'string', 'maxLength': MAX_NOTES_CHARS},
    })


def _binding(source, index, task, result_schema):
    if task.get('evidencePolicy') != VERSION:
        raise ValueError('Explicit evidence-dialog policy is required')
    if task.get('evidenceIndexSha256') != index.sha256:
        raise ValueError('Evidence dialog task belongs to another fact index')
    if task.get('snapshotId') != source.snapshot_id:
        raise ValueError('Evidence dialog task belongs to another source snapshot')
    if task.get('evidenceWindowPolicy') != WINDOW_POLICY:
        raise ValueError('Evidence dialog requires the exact supported evidence-window policy')
    return {'protocol': VERSION, 'taskId': task['id'], 'contextId': task['contextId'],
            'snapshotId': source.snapshot_id, 'indexSha256': index.sha256,
            'taskSha256': contracts.digest(task), 'resultSchemaSha256': contracts.digest(result_schema),
            'windowPolicy': deepcopy(task['evidenceWindowPolicy'])}


def _check(check_current):
    if check_current is not None and check_current() is False:
        raise ValueError('Evidence dialog task is no longer current')


def _evidence(value):
    if isinstance(value, dict):
        if set(value) == {'path', 'startLine', 'endLine', 'sha256'}:
            yield value
        else:
            for child in value.values():
                yield from _evidence(child)
    elif isinstance(value, list):
        for child in value:
            yield from _evidence(child)


def _delivered(pairs):
    source_refs, fact_ids = [], set()
    for pair in pairs:
        request, reply = pair['request'], pair['reply']
        result = reply['result']
        if reply['status'] != 'ok':
            continue
        if request['operation'] == 'read' and result.get('evidence'):
            source_refs.append(result['evidence'])
        elif request['operation'] == 'search':
            source_refs.extend(row['evidence'] for row in result['matches'])
        elif request['operation'] == 'query':
            fact_ids.update(row['id'] for row in result['facts'])
    return source_refs, fact_ids


def _covers(ref, supplied):
    intervals = sorted((row['startLine'], row['endLine']) for row in supplied
                       if row['path'] == ref['path'] and row['sha256'] == ref['sha256'])
    cursor = ref['startLine']
    for start, end in intervals:
        if start > cursor:
            return False
        if end >= cursor:
            cursor = end + 1
        if cursor > ref['endLine']:
            return True
    return False


class _DeliveryProgress:
    """Count newly delivered data, independent of how a query was spelled."""

    def __init__(self):
        self.source_refs = []
        self.fact_ids = set()
        self.materials = set()

    def consume(self, pairs):
        source_refs, fact_ids = _delivered(pairs)
        materials = {(row['materialKind'], row['path']) for pair in pairs
                     if pair['request']['operation'] == 'inventory' and pair['reply']['status'] == 'ok'
                     for row in pair['reply']['result']['materials']}
        changed = bool(fact_ids - self.fact_ids or materials - self.materials)
        for ref in source_refs:
            if not _covers(ref, self.source_refs):
                changed = True
                self.source_refs.append(ref)
        # Keep an interval union: overlapping search/read pages are the same
        # source delivery, while an extension containing new lines is progress.
        groups = {}
        for ref in self.source_refs:
            groups.setdefault((ref['path'], ref['sha256']), []).append((ref['startLine'], ref['endLine']))
        self.source_refs = []
        for (path, sha256), intervals in groups.items():
            merged = []
            for start, end in sorted(intervals):
                if merged and start <= merged[-1][1] + 1:
                    merged[-1] = (merged[-1][0], max(merged[-1][1], end))
                else:
                    merged.append((start, end))
            self.source_refs.extend({'path': path, 'sha256': sha256, 'startLine': start, 'endLine': end}
                                    for start, end in merged)
        self.fact_ids.update(fact_ids)
        self.materials.update(materials)
        return changed


def validate_delivery(source, answer, pairs):
    """Require real host-supplied text, never equate it with semantic approval."""
    refs = list(_evidence(answer))
    source.verify_evidence_many(refs)
    supplied, facts = _delivered(pairs)
    for ref in refs:
        if not _covers(ref, supplied):
            raise ValueError('Final citation was not supplied as original text in this task: ' + ref['path'])
    for usage in answer.get('factUsage', []):
        if not set(usage['factIds']).issubset(facts):
            raise ValueError('Final fact usage contains facts not supplied in this task')


def _summary(pair):
    request, reply = pair['request'], pair['reply']
    result = reply['result']
    return {'request': deepcopy(request), 'replySha256': reply['replySha256'],
            'status': reply['status'],
            'page': {key: deepcopy(result[key]) for key in
                     ('matchedCount', 'returnedCount', 'truncated', 'nextOffset', 'nextLine') if key in result}}


def _materials(pairs):
    """Project receipts into origin-labelled material, without changing source."""
    for pair in pairs:
        request, reply = pair['request'], pair['reply']
        if reply['status'] != 'ok':
            continue
        result = reply['result']
        origin = {'replySha256': reply['replySha256']}
        if request['operation'] == 'read' and result.get('evidence'):
            yield {**origin, 'kind': 'source', 'evidence': deepcopy(result['evidence']),
                   'sourceText': result['sourceText']}
        elif request['operation'] == 'search':
            for row in result['matches']:
                yield {**origin, 'kind': 'source', 'evidence': deepcopy(row['evidence']),
                       'sourceText': row['sourceText']}
        elif request['operation'] == 'query':
            for fact in result['facts']:
                yield {**origin, 'kind': 'fact', 'fact': deepcopy(fact)}
        elif request['operation'] == 'inventory':
            for material in result['materials']:
                yield {**origin, 'kind': 'inventory', 'material': deepcopy(material)}


def _material_summary(material):
    result = {'kind': material['kind'], 'replySha256': material['replySha256']}
    if material['kind'] == 'source':
        result['evidence'] = deepcopy(material['evidence'])
    elif material['kind'] == 'fact':
        result['factId'] = material['fact']['id']
    else:
        result.update({key: material['material'][key] for key in ('materialKind', 'path')})
    return result


def _uncovered(ref, covered):
    """Return disjoint original LF intervals not already visible at this origin."""
    remaining = [(ref['startLine'], ref['endLine'])]
    for prior in covered:
        if prior['path'] != ref['path'] or prior['sha256'] != ref['sha256']:
            continue
        next_remaining = []
        for start, end in remaining:
            if prior['endLine'] < start or end < prior['startLine']:
                next_remaining.append((start, end))
                continue
            if start < prior['startLine']:
                next_remaining.append((start, prior['startLine'] - 1))
            if prior['endLine'] < end:
                next_remaining.append((prior['endLine'] + 1, end))
        remaining = next_remaining
    return remaining


def _prior_materials(latest, pairs):
    """Newest prior delivery wins; same text at another origin stays separate."""
    visible = list(_materials(latest))
    source_refs = [item['evidence'] for item in visible if item['kind'] == 'source']
    facts = {item['fact']['id'] for item in visible if item['kind'] == 'fact'}
    inventory = {(item['material']['materialKind'], item['material']['path'])
                 for item in visible if item['kind'] == 'inventory'}
    latest_ids = {pair['reply']['replySha256'] for pair in latest}
    prior = []
    for pair in reversed(pairs):
        if pair['reply']['replySha256'] in latest_ids:
            continue
        for material in reversed(list(_materials([pair]))):
            if material['kind'] == 'source':
                ref = material['evidence']
                rows = source_lines(material['sourceText'])
                if len(rows) != ref['endLine'] - ref['startLine'] + 1:
                    raise ValueError('Retained original text does not match its LF evidence range')
                for start, end in _uncovered(ref, source_refs):
                    subref = {**ref, 'startLine': start, 'endLine': end}
                    prior.append({**material, 'evidence': subref,
                                  'sourceText': ''.join(rows[start - ref['startLine']:end - ref['startLine'] + 1])})
                    source_refs.append(subref)
            elif material['kind'] == 'fact':
                identifier = material['fact']['id']
                if identifier not in facts:
                    prior.append(material)
                    facts.add(identifier)
            else:
                key = (material['material']['materialKind'], material['material']['path'])
                if key not in inventory:
                    prior.append(material)
                    inventory.add(key)
    return visible, prior


def _round_context(context, number, notes, latest, pairs, instruction, schema, window_policy):
    result = deepcopy(context)
    visible, candidates = _prior_materials(latest, pairs)
    window = {'policy': deepcopy(window_policy), 'effectiveMaxChars': window_policy['maxChars'],
              'retainedChars': 0, 'visibleMaterials': [_material_summary(item) for item in visible],
              'evictedMaterials': [_material_summary(item) for item in candidates]}
    result['evidenceDialog'] = {
        'protocol': VERSION, 'round': number, 'workingNotes': notes,
        'latestEvidence': deepcopy(latest), 'retainedEvidence': [], 'evidenceWindow': window,
        'deliveryLedger': [_summary(pair) for pair in pairs],
        'ledgerMeaning': 'Delivery only; neither reading nor semantic coverage is established by this ledger.',
    }
    # Account for the complete immutable view, notes, both ledgers, latest pages,
    # provider framing and schema first. Leave a small margin for decimal-size
    # metadata changes while selecting prior pages in linear serialization work.
    budget = max(0, min(window_policy['maxChars'], MAX_INPUT_CHARS - _input_size(instruction, result, schema) - 64))
    window['effectiveMaxChars'] = budget
    retained, selected, used = [], set(), 2
    for ordinal, material in enumerate(candidates):
        cost = len(_json(material)) + (1 if retained else 0)
        if used + cost <= budget:
            retained.append(material)
            selected.add(ordinal)
            used += cost
    result['evidenceDialog']['retainedEvidence'] = retained
    window['retainedChars'] = len(_json(retained)) if retained else 0
    window['visibleMaterials'].extend(_material_summary(candidates[i]) for i in sorted(selected))
    window['evictedMaterials'] = [_material_summary(item) for i, item in enumerate(candidates) if i not in selected]
    # The final capacity check is authoritative. Latest pages and review
    # obligations are never removed to manufacture room for the cache.
    _prompt(instruction, result, schema)
    return result


def _input_size(instruction, context, schema):
    from .provider import COMMON_POLICY
    prompt = instruction + '\n' + POLICY + '\n' + _json(context)
    return len(prompt) + len(COMMON_POLICY) + len(_json(schema)) + INPUT_RESERVE_CHARS


def _prompt(instruction, context, schema):
    # This is a single-call capacity, not a total investigation budget.
    if _input_size(instruction, context, schema) > MAX_INPUT_CHARS:
        raise ValueError('Evidence dialog input exceeds the single-call capacity; retain progress and split the task')
    return instruction + '\n' + POLICY + '\n' + _json(context)


def _wrapper(response, schema):
    if response.get('exit_code') != 0 or response.get('metadata', {}).get('status') != 'passed':
        raise RuntimeError('Evidence provider failed; raw round artifacts were preserved')
    wrapper = response.get('answer')
    contracts.validate(wrapper, schema)
    if wrapper['action'] == 'requests':
        if not wrapper['requests'] or wrapper['answer'] is not None:
            raise ValueError('Evidence requests require nonempty requests and a null canonical answer')
    elif wrapper['requests'] or wrapper['answer'] is None:
        raise ValueError('Evidence finish requires an empty request list and a canonical answer')
    return wrapper


def run(source, index, store, task, context, instruction, result_schema, provider, timeout,
        check_current=None):
    """Run a trusted provider chain; the final response is explicitly assembled."""
    started = time.perf_counter()
    prefix = 'tasks/' + task['id'] + '/evidence'
    binding = _binding(source, index, task, result_schema)
    _check(check_current)
    access = EvidenceAccess(source, index, task)
    if context.get('sourceDelivery', {}).get('mode') == 'complete-originals':
        raise ValueError('Evidence mode must not also inline complete original source')
    schema = response_schema(task, result_schema)
    transport_schema = contracts.transport_schema(task, schema)
    store.put(prefix + '/setup.json', {'binding': binding, 'context': context,
                                      'instruction': instruction, 'resultSchema': result_schema})
    pairs, latest, rounds, notes = [], [], [], ''
    progress = _DeliveryProgress()
    previous, number, repeated = contracts.digest(binding), 1, 0
    usage = {}
    try:
        while True:
            _check(check_current)
            current = _round_context(context, number, notes, latest, pairs, instruction,
                                     transport_schema, task['evidenceWindowPolicy'])
            prompt = _prompt(instruction, current, transport_schema)
            store.put(prefix + f'/round-{number:04d}-context.json', current)
            response = provider(source.root, store.path('tasks/' + task['id'] + f'/provider/round-{number:04d}'),
                                prompt, transport_schema, timeout)
            store.put(prefix + f'/round-{number:04d}-response.json', response)
            _check(check_current)
            wrapper = _wrapper(response, schema)
            latest = []
            for request in wrapper['requests']:
                _check(check_current)
                reply = access.handle(request)
                _check(check_current)
                latest.append({'request': deepcopy(request), 'reply': reply})
            new_delivery = progress.consume(latest)
            record = {'bindingSha256': contracts.digest(binding), 'number': number,
                      'previousRoundSha256': previous, 'contextSha256': contracts.digest(current),
                      'promptSha256': _hash_text(prompt), 'responseSha256': contracts.digest(response),
                      'pairs': latest, 'newDelivery': new_delivery}
            store.put(prefix + f'/round-{number:04d}.json', record)
            previous = contracts.digest(record)
            rounds.append({'number': number, 'sha256': previous})
            for key, value in (response.get('usage') or {}).items():
                if type(value) in (int, float):
                    usage[key] = usage.get(key, 0) + value
            if wrapper['action'] == 'finish':
                answer = wrapper['answer']
                contracts.validate(answer, result_schema)
                validate_delivery(source, answer, pairs)
                _check(check_current)
                transcript = {'binding': binding, 'rounds': rounds,
                              'canonicalAnswerSha256': contracts.digest(answer)}
                store.put(prefix + '/transcript.json', transcript)
                return {'exit_code': 0, 'answer': answer, 'usage': usage or None,
                        'metadata': {'status': 'passed', 'responseOrigin': 'host-assembled-evidence-dialog',
                                     'evidenceTranscriptSha256': contracts.digest(transcript),
                                     'canonicalAnswerSha256': contracts.digest(answer),
                                     'rounds': number, 'seconds': time.perf_counter() - started}}
            repeated = 0 if new_delivery else repeated + 1
            pairs.extend(latest)
            if repeated >= 3:
                raise ValueError('Evidence dialog continued without progress in delivered evidence')
            notes = wrapper['workingNotes']
            number += 1
    except (Exception, KeyboardInterrupt) as exc:
        store.put(prefix + '/failure.json', {'binding': binding, 'round': number,
                  'completedRounds': rounds, 'errorType': type(exc).__name__, 'error': str(exc)})
        raise


def replay(source, index, store, task, answer, transcript_sha256):
    """Rebuild the provider/receipt chain before host adoption; never re-infer."""
    prefix = 'tasks/' + task['id'] + '/evidence'
    setup = store.get(prefix + '/setup.json')
    result_schema = setup['resultSchema']
    if result_schema != contracts.transport_schema(task):
        raise ValueError('Evidence canonical result schema is not the current task contract')
    binding = _binding(source, index, task, result_schema)
    transcript = store.get(prefix + '/transcript.json')
    if (setup['binding'] != binding or transcript['binding'] != binding
            or contracts.digest(transcript) != transcript_sha256
            or transcript['canonicalAnswerSha256'] != contracts.digest(answer)):
        raise ValueError('Evidence transcript binding changed')
    access = EvidenceAccess(source, index, task)
    schema = response_schema(task, result_schema)
    transport_schema = contracts.transport_schema(task, schema)
    pairs, latest, notes = [], [], ''
    progress, repeated = _DeliveryProgress(), 0
    previous = contracts.digest(binding)
    finished = False
    for number, pointer in enumerate(transcript['rounds'], 1):
        if pointer['number'] != number or finished:
            raise ValueError('Evidence transcript round order changed')
        record = store.get(prefix + f'/round-{number:04d}.json')
        current = store.get(prefix + f'/round-{number:04d}-context.json')
        response = store.get(prefix + f'/round-{number:04d}-response.json')
        expected = _round_context(setup['context'], number, notes, latest, pairs, setup['instruction'],
                                  transport_schema, task['evidenceWindowPolicy'])
        prompt = _prompt(setup['instruction'], expected, transport_schema)
        if (current != expected or record['bindingSha256'] != contracts.digest(binding)
                or record['number'] != number or record['previousRoundSha256'] != previous
                or record['contextSha256'] != contracts.digest(current)
                or record['promptSha256'] != _hash_text(prompt)
                or record['responseSha256'] != contracts.digest(response)
                or contracts.digest(record) != pointer['sha256']):
            raise ValueError('Evidence round execution chain changed')
        wrapper = _wrapper(response, schema)
        latest = record['pairs']
        if len(latest) != len(wrapper['requests']):
            raise ValueError('Evidence request/receipt count changed')
        for request, pair in zip(wrapper['requests'], latest):
            if pair['request'] != request:
                raise ValueError('Evidence request identity changed')
        access.verify_replies((pair['request'], pair['reply']) for pair in latest)
        new_delivery = progress.consume(latest)
        if type(record.get('newDelivery')) is not bool or record['newDelivery'] != new_delivery:
            raise ValueError('Evidence delivery progress differs from its replay')
        if wrapper['action'] == 'finish':
            if wrapper['answer'] != answer:
                raise ValueError('Evidence final answer differs from the raw provider wrapper')
            validate_delivery(source, answer, pairs)
            finished = True
        else:
            repeated = 0 if new_delivery else repeated + 1
            if repeated >= 3:
                raise ValueError('Evidence transcript continued without progress in delivered evidence')
            pairs.extend(latest)
            notes = wrapper['workingNotes']
        previous = contracts.digest(record)
    if not finished:
        raise ValueError('Evidence transcript has no canonical final response')
