"""Native Codex tool sessions with host-owned drafts and replayable submissions."""
from __future__ import annotations
from copy import deepcopy
import json
import uuid
import time
from . import contracts as c, investigation, candidate_amendment as amendment
from .native_contracts import ToolContracts, MAX_STATE_CHARACTERS
from .evidence_dialog import validate_delivery
from .native_mcp import Broker
from .native_evidence import run_batch, native_access, reply_size, MAX_BATCH_BYTES, replay_evidence
from .native_readiness import assess, require_followup_acknowledgement

VERSION = 'contextbase-native-tools/1'
TRANSPORT = 'codex-native-tools'
ORIGIN = 'host-recorded-native-tools'
BOOTSTRAP_POLICY = 'contextbase-native-bootstrap/2'
MAX_BOOTSTRAP_CHARS = 12000
ACQUISITION_POLICY = 'contextbase-native-acquisition/2'
FINAL_SCHEMA = c.obj({'submission_id': c.SHA256})


def _binding(source, index, task):
    return {'version': VERSION, 'task': deepcopy(task), 'snapshot': source.snapshot_id,
            'index': index.sha256, 'acquisitionPolicy': ACQUISITION_POLICY}


def _text_page(text, start, limit, metadata):
    """Return a complete JSON text slice that fits the serialized MCP budget."""
    def page(count):
        end = start + count
        return {**metadata, 'text': text[start:end],
                'next_offset': end if end < len(text) else None,
                'total_characters': len(text)}
    high = min(limit, max(0, len(text) - start))
    if reply_size(page(high)) <= MAX_BATCH_BYTES:
        return page(high)
    low = 0
    while low < high:
        middle = (low + high + 1) // 2
        if reply_size(page(middle)) <= MAX_BATCH_BYTES:
            low = middle
        else:
            high = middle - 1
    if low == 0:
        raise ValueError('Native text page metadata exceeds the reply capacity')
    return page(low)


def _readiness(answer, requirements):
    status = assess(answer, requirements)
    return {key: value for key, value in status.items() if key != 'blockingConditions'} | {
        'blockingConditionCount': len(status['blockingConditions']),
        'scope': 'Unconditional adoption blockers only; plan completion, source delivery and independent verification still apply. Inspect saved drafts for retained followups.'}


class Tools:
    """One task capability; the caller supplies immutable ownership and scope."""
    def __init__(self, source, index, task, context, check_current=None, validate_final=None):
        self.source, self.task, self.context = source, deepcopy(task), deepcopy(context)
        self.access = native_access(source, index, task)
        self.check = check_current or (lambda: None)
        self.validate_final = validate_final
        self.calls, self.pairs, self.events, self.units = [], [], [], []
        self.revision, self.operations, self.submission = 0, {}, None
        self.active = True
        self.amendment = None
        if task.get('amendmentPolicy') == amendment.NATIVE_VERSION and task['operation'] == 'extract':
            self.amendment = deepcopy(context['candidateAmendment'])
            amendment.validate_spec(self.amendment['seed'], task, self.amendment['spec'])

        self._contracts = ToolContracts(self.task, self.amendment)

    def schemas(self):
        return self._contracts.schemas()

    def handle(self, name, arguments):
        self._validate_call(name, arguments)
        result = self._apply(name, deepcopy(arguments))
        if reply_size(result) > MAX_BATCH_BYTES:
            raise ValueError('Native tool reply exceeds its serialized UTF-8 byte capacity')
        self.check()
        self.calls.append({'name': name, 'arguments': deepcopy(arguments), 'reply': deepcopy(result)})
        return result

    def _validate_call(self, name, arguments):
        if not self.active:
            raise ValueError('Native execution capability is revoked')
        if self.check() is False:
            raise ValueError('Native execution capability is revoked')
        self._contracts.validate(name, arguments)

    def _apply(self, name, args):
        if name in {'inventory', 'query', 'search', 'read'}:
            request = {'operation': name, **args}
            reply = self.access.handle(request)
            self.pairs.append({'request': request, 'reply': reply})
            return reply
        if name == 'evidence_batch':
            reply, pairs = run_batch(self.access, args['requests'], check_current=self.check)
            self.pairs.extend(pairs)
            return reply
        if name == 'contract_schema':
            return self._contracts.describe(args['contract'], args['category'])
        if name == 'analysis_state':
            return self._read_state(args)
        # Reads stay available after freezing; only identical mutations may retry.
        if self.submission is not None:
            return self._frozen_reply(name, args)
        if name == 'review_submit':
            return self._submit_review(args['review'])
        if name == 'submit_amendment':
            return self._submit_amendment(args)
        return self._mutate_draft(name, args)

    def _state_value(self, collection):
        if collection == 'task':
            return self.task
        if collection == 'context':
            return self.context
        if collection == 'plan':
            return {'units': self.units}
        if collection == 'submission':
            return self._submission_ref() if self.submission else None
        if collection == 'amendment':
            return _amendment_material(self.task, self.amendment)
        drafts = investigation.reduce_drafts(self.task, self.events) if self.events else {}
        if collection == 'drafts':
            return drafts
        return [{'key': row['key'], 'sha256': c.digest(row)}
                for row in sorted(drafts.get('records', []), key=lambda row: row['key'])]

    def _read_state(self, args):
        data = self._state_value(args['collection'])
        if 'field' in args:
            if not isinstance(data, dict) or args['field'] not in data:
                available = sorted(data) if isinstance(data, dict) else []
                raise ValueError('Unknown top-level field in analysis_state collection: ' + args['field']
                                 + '; available fields: ' + json.dumps(available))
            data = data[args['field']]
        text = json.dumps(data, ensure_ascii=False, sort_keys=True)
        return _text_page(text, args['offset'], args['limit'], {'revision': self.revision,
            **({'field': args['field']} if 'field' in args else {})})

    def _submission_ref(self):
        return {'submission_id': self.submission['id'],
                'content_sha256': self.submission['contentSha256']}

    def _frozen_reply(self, name, args):
        if name == 'submit_amendment' and self.submission.get('amendment') == {
                'patch': args['patch'], 'closures': args['closures']}:
            return {**self._submission_ref(),
                    'readiness': _readiness(self.submission['answer'], self.task['requirements'])}
        if name == 'review_submit' and args['review'] == self.submission['answer']:
            return self._submission_ref()
        if name in {'plan_update', 'draft_apply', 'submit_candidate'} and args.get('operation_id') in self.operations:
            old = self.operations[args['operation_id']]
            if old['arguments'] == args and old['name'] == name:
                return deepcopy(old['reply'])
        raise ValueError('Submission is frozen')

    def _submit_review(self, answer):
        c.validate_result(answer, self.task, self.source,
                          self.context.get('verificationView', {}).get('records', {}))
        return self._freeze(answer)

    def _submit_amendment(self, args):
        seed, spec = self.amendment['seed'], self.amendment['spec']
        patch = args['patch']
        require_followup_acknowledgement(self.task, patch, seed['followups'],
            retain_blocking_followups=args.get('retain_blocking_followups', False))
        answer = amendment.canonical_answer(seed, self.task, spec, patch, args['closures'])
        # Inherited claims remain untrusted inputs, never current delivery rights.
        fresh = {key: deepcopy(patch[key]) for key in ('factUsage', 'unknowns', 'followups', 'dispositions')}
        fresh.update(records=[row['record'] for row in patch['changes']], closures=args['closures'])
        validate_delivery(self.source, fresh, self.pairs)
        return self._freeze(answer, delta={'patch': patch, 'closures': args['closures']})

    def _mutate_draft(self, name, args):
        key = args['operation_id']
        if key in self.operations:
            old = self.operations[key]
            if old['arguments'] != args or old['name'] != name:
                raise ValueError('Operation identity reused with different content')
            return deepcopy(old['reply'])
        if args['expected_revision'] != self.revision:
            raise ValueError('Draft revision is obsolete')
        if name == 'plan_update':
            reply = self._update_plan(args['plan'])
        elif name == 'draft_apply':
            reply = self._apply_draft(args)
        else:
            reply = self._submit_candidate(args['closures'])
        self.revision += 1
        self.operations[key] = {'name': name, 'arguments': deepcopy(args), 'reply': deepcopy(reply)}
        return reply

    def _update_plan(self, plan):
        investigation.validate_plan(self.task, plan)
        units = plan['units']
        old = {unit['id']: unit for unit in self.units}
        proposed_ids = {unit['id'] for unit in units}
        if any(unit['id'] not in proposed_ids for unit in self.units) or any(
                unit['id'] in old and old[unit['id']] != unit for unit in units):
            raise ValueError('Existing planned units cannot be removed or changed')
        self.units = deepcopy(units)
        return {'revision': self.revision + 1}

    def _apply_draft(self, args):
        unit = next((unit for unit in self.units if unit['id'] == args['unit_id']), None)
        if unit is None:
            raise ValueError('Draft requires a planned unit')
        previous = investigation.reduce_drafts(self.task, self.events) if self.events else {}
        require_followup_acknowledgement(self.task, args['draft'], previous.get('followups', []),
            retain_blocking_followups=args.get('retain_blocking_followups', False))
        events = [*self.events, {'unit': unit, 'answer': args['draft']}]
        reduced = investigation.reduce_drafts(self.task, events)
        self.events = deepcopy(events)
        for added in args['draft']['addUnits']:
            if not any(unit['id'] == added['id'] for unit in self.units):
                self.units.append(deepcopy(added))
        return {'revision': self.revision + 1,
                'readiness': _readiness({'coverage': [], 'followups': reduced['followups']}, self.task['requirements'])}

    def _submit_candidate(self, closures):
        if not self.units:
            raise ValueError('Candidate requires an investigation plan')
        answer = investigation.canonical_answer(self.task, self.events, closures)
        finished = {event['unit']['id'] for event in self.events}
        if finished != {unit['id'] for unit in self.units}:
            raise ValueError('Every planned unit requires a completed draft')
        return self._freeze(answer)

    def _freeze(self, answer, *, delta=None):
        if delta is None:
            validate_delivery(self.source, answer, self.pairs)
        elif (self.amendment is None or answer != amendment.canonical_answer(
                self.amendment['seed'], self.task, self.amendment['spec'], delta['patch'], delta['closures'])):
            raise ValueError('Only a bound native amendment can inherit untrusted base claims')
        if self.validate_final:
            self.validate_final(answer)
        self.submission = {'answer': deepcopy(answer), 'draftRevision': self.revision,
                           'contentSha256': c.digest(answer)}
        if delta is not None:
            self.submission['amendment'] = deepcopy(delta)
        self.submission['id'] = c.digest(self.submission)
        reply = self._submission_ref()
        if self.task['operation'] == 'extract':
            reply['readiness'] = _readiness(answer, self.task['requirements'])
        return reply


def run(source, index, store, task, context, instruction, provider, timeout,
        check_current=None, validate_final=None, role_spec=None):
    tools = Tools(source, index, task, context, check_current, validate_final)
    basis = _basis(source, index, task, context, role_spec)
    checkpoint_root = store.path('native-checkpoints/' + basis)
    recovered = None
    if checkpoint_root.exists() and task['operation'] == 'extract':
        candidates = sorted(checkpoint_root.glob('*.json'))
        if candidates:
            recovered = store.get('native-checkpoints/' + basis + '/' + candidates[-1].name)
            if recovered['basis'] != basis:
                raise ValueError('Native checkpoint basis changed')
            _recover(tools, recovered, source, index, store, basis)
    prefix = 'tasks/' + task['id'] + '/native/' + uuid.uuid4().hex
    setup = {'binding': _binding(source, index, task), 'context': context, 'instruction': instruction,
             'roleSpec': role_spec, 'resume': recovered,
             'bootstrapPolicy': BOOTSTRAP_POLICY, 'bootstrap': _bootstrap(task, context)}
    store.put(prefix + '/setup.json', setup)
    # Persist every completed tool call before returning its reply to Codex.
    original = tools.handle
    def invoke(name, arguments):
        reply = original(name, arguments)
        store.put(prefix + '/calls/' + str(len(tools.calls)).zfill(8) + '.json', tools.calls[-1])
        if name in {'plan_update', 'draft_apply'}:
            checkpoint = {'basis': basis, 'state': _state(tools), 'producerTask': deepcopy(task),
                          'callPrefix': prefix, 'callCount': len(tools.calls)}
            store.put('native-checkpoints/' + basis + '/' + str(time.time_ns()) + '-' + uuid.uuid4().hex + '.json', checkpoint)
        return reply
    try:
        with Broker(tools.schemas(), invoke) as broker:
            prompt = instruction + '\nUse the ContextBase MCP tools to investigate continuously. '
            prompt += 'The bootstrap below contains complete included task/material fields. Use those directly; retrieve omitted fields through its directory only as needed. Source citations and fact usage still require the evidence tools. Save drafts before finishing. '
            prompt += 'Use contract_schema for exact record/classification fields when needed; do not guess schema names. Your final response must contain only the submission_id returned by the submission tool.'
            if tools.amendment:
                prompt += (' This is an explicit limited amendment. Read analysis_state(collection=amendment, field=selectedRecords) for raw records and exact frozen versions, and field=issues for findings. Investigate those claims with current tools, submit only authorized replacements and dispositions through submit_amendment, plus fresh closures for every original obligation. The host preserves omitted base claims as untrusted input; do not reemit or rewrite the full candidate. Inspect other retained material only as needed to assess dependencies and closure. Old review judgments are not acceptance.')
            prompt += ' Prefer evidence_batch for independent source requests; it returns complete replies and an explicit remaining-request index. Inventory and index enumeration are navigation aids; select the facts needed to investigate and verify claims and omissions rather than mechanically dumping every indexed fact.'
            prompt += ' In Code Mode, use one ContextBase tool response per functions.exec cell, begin the cell with // @exec: {"max_output_tokens":262144}, and display every returned text content block in full. Do not combine several large tool responses into one cell output. Native replies are byte-bounded; follow their actual continuation pointers.'
            if recovered is not None:
                prompt += 'Validated saved plan and drafts exist; current draft revision is ' + str(tools.revision) + '. Continue those saved results; consult analysis_state(plan/drafts) before modifying them. '
            prompt += '\n' + json.dumps(setup['bootstrap'], ensure_ascii=False, sort_keys=True, separators=(',', ':'))
            response = provider(source.root, store.path(prefix + '/provider'), prompt, FINAL_SCHEMA, timeout,
                                role_spec=role_spec, tool_connection=broker.connection)
        if response.get('exit_code') != 0 or response.get('metadata', {}).get('status') != 'passed':
            raise RuntimeError('Native Codex provider failed; tool records retained')
        if tools.submission is None or response.get('answer') != {'submission_id': tools.submission['id']}:
            raise ValueError('Provider must return the host-frozen submission identity')
        manifest = {**setup, 'calls': tools.calls, 'submission': tools.submission}
        digest = c.digest(manifest)
        store.put('native-transcripts/' + digest + '.json', manifest)
        return {'exit_code': 0, 'answer': tools.submission['answer'], 'usage': response.get('usage'),
                'metadata': {'status': 'passed', 'responseOrigin': ORIGIN,
                             'nativeTranscriptSha256': digest, 'providerMetadata': response.get('metadata')}}
    finally:
        tools.active = False


def replay(source, index, store, task, answer, transcript_sha256, validate_final=None):
    manifest = store.get('native-transcripts/' + str(transcript_sha256) + '.json')
    if c.digest(manifest) != transcript_sha256 or manifest['binding'] != _binding(source, index, task):
        raise ValueError('Native transcript binding changed')
    _validate_bootstrap(manifest)
    tools = Tools(source, index, task, manifest['context'], validate_final=validate_final)
    if manifest.get('resume'):
        _recover(tools, manifest['resume'], source, index, store,
                 _basis(source, index, task, manifest['context'], manifest.get('roleSpec')))
    _replay_calls(tools, manifest['calls'])
    if tools.submission != manifest['submission'] or tools.submission is None or tools.submission['answer'] != answer:
        raise ValueError('Native submission replay changed')


def _state(tools):
    return {'events': deepcopy(tools.events), 'units': deepcopy(tools.units),
            'revision': tools.revision, 'operations': deepcopy(tools.operations)}


def _restore(tools, state):
    investigation.validate_plan(tools.task, {'units': state['units']})
    investigation.reduce_drafts(tools.task, state['events'])
    tools.units, tools.events = deepcopy(state['units']), deepcopy(state['events'])
    tools.revision, tools.operations = state['revision'], deepcopy(state['operations'])


def _recover(tools, checkpoint, source, index, store, expected_basis):
    setup = store.get(checkpoint['callPrefix'] + '/setup.json')
    producer = checkpoint['producerTask']
    _validate_bootstrap(setup)
    actual_basis = _basis(source, index, producer, setup['context'], setup.get('roleSpec'))
    if checkpoint['basis'] != expected_basis or actual_basis != expected_basis:
        raise ValueError('Recovered native role, task or retained context basis changed')
    if setup['binding'] != _binding(source, index, producer):
        raise ValueError('Recovered native source binding changed')
    prior = Tools(source, index, producer, setup['context'])
    if setup.get('resume'):
        _recover(prior, setup['resume'], source, index, store, expected_basis)
    rows = [store.get(checkpoint['callPrefix'] + '/calls/' + str(number).zfill(8) + '.json')
            for number in range(1, checkpoint['callCount'] + 1)]
    _replay_calls(prior, rows)
    if _state(prior) != checkpoint['state']:
        raise ValueError('Recovered native draft changed')
    _restore(tools, checkpoint['state'])
    tools.access._assert_binding()


def _replay_calls(tools, calls):
    """Rebuild acquisitions inside one integrity fence, granting rights in order."""
    with replay_evidence(tools.access, check_current=tools.check) as acquire:
        for call in deepcopy(calls):
            if call['name'] in {'inventory', 'query', 'search', 'read', 'evidence_batch'}:
                tools._validate_call(call['name'], call['arguments'])
                reply, pairs = acquire(call['name'], call['arguments'])
                if reply != call['reply']:
                    raise ValueError('Evidence reply differs from its task-bound source replay')
                tools.pairs.extend(deepcopy(pairs))
                tools.calls.append(deepcopy(call))
            elif tools.handle(call['name'], call['arguments']) != call['reply']:
                raise ValueError('Native tool receipt replay changed')


def _basis(source, index, task, context, role_spec):
    stable_task = {key: value for key, value in task.items()
                   if key not in {'id', 'contextId', 'executionEpoch'}}
    return c.digest({'task': stable_task, 'role': role_spec,
        'source': source.snapshot_id, 'index': index.sha256,
        'retained': {key: context.get(key) for key in ('currentRecords', 'currentUnknowns')}})


def _bootstrap(task, context):
    """Deliver whole task/material fields, with bounded, explicit read pointers."""
    def size(value):
        return len(json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':')))
    def read_size(value):
        return len(json.dumps(value, ensure_ascii=False, sort_keys=True))
    def pointer(collection, field=None):
        return {'collection': collection, 'offset': 0, 'limit': MAX_STATE_CHARACTERS,
                **({'field': field} if field is not None else {})}
    fields = {key: value for key, value in context.items() if key != 'task'}
    if task.get('amendmentPolicy') == amendment.NATIVE_VERSION and task['operation'] == 'extract':
        material = _amendment_material(task, context['candidateAmendment'])
        fields['amendmentSummary'] = {key: value for key, value in material.items()
                                     if key not in {'baseRecords', 'unknowns', 'followups'}}
    directory = {'task': {'characters': read_size(task), 'read': pointer('task')},
                 'context': {key: {'characters': read_size(value), 'read': pointer('context', key)}
                             for key, value in sorted(fields.items())}}
    result = {'policy': BOOTSTRAP_POLICY, 'included': {}, 'directory': directory,
              'meaning': 'Task and unverified material only; not source/fact delivery or acceptance. '
                         'Included fields are complete. Read missing fields using directory pointers.'}
    if size(result) > MAX_BOOTSTRAP_CHARS:
        # A pathological number of field names gets an explicit whole-context pointer.
        result['directory']['context'] = {'characters': read_size(context), 'read': pointer('context'),
                                          'meaning': 'Retrieve full context to enumerate all fields.'}
    if 'amendmentSummary' in fields:
        directory['context'].pop('amendmentSummary')
        directory['amendment'] = {key: {'characters': read_size(value), 'read': pointer('amendment', key)}
                                  for key, value in material.items()}
    priority = ['task', 'amendmentSummary', 'verificationView', 'assignment', 'request', 'inventory', 'structure']
    values = {'task': task, **fields}
    for key in [*priority, *sorted(set(values) - set(priority))]:
        if key not in values:
            continue
        proposed = {**result, 'included': {**result['included'], key: values[key]}}
        if size(proposed) <= MAX_BOOTSTRAP_CHARS:
            result = proposed
    if size(result) > MAX_BOOTSTRAP_CHARS:
        raise ValueError('Native bootstrap directory exceeds its material limit')
    return result


def _amendment_material(task, retained):
    seed, spec = retained['seed'], retained['spec']
    records = {row['key']: row for row in seed['answer']['records']}
    return {'operationId': task['amendmentOperationId'], 'seedSha256': spec['seedSha256'],
            'baseCandidateSha256': seed['baseCandidateSha256'], 'replaceKeys': spec['replaceKeys'],
            'issues': seed['issues'], 'selectedRecords': {key: {
                'record': records[key], 'expectedVersion': seed['view']['records'][key]['version'],
                'factUsage': [row for row in seed['answer'].get('factUsage', []) if row['recordKey'] == key]}
                for key in spec['replaceKeys']},
            'unknowns': seed['view']['unknowns'], 'followups': seed['followups'],
            'baseRecords': records}


def _validate_bootstrap(setup):
    if (setup.get('bootstrapPolicy') != BOOTSTRAP_POLICY
            or setup.get('bootstrap') != _bootstrap(setup['binding']['task'], setup['context'])):
        raise ValueError('Native bootstrap policy or bound task/material projection changed')
