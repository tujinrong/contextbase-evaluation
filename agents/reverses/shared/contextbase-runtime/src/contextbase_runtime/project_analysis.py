"""Whole-source analysis: one continuous author session, separately verified.

Goal stages describe content dependencies, never a required number of agents.
"""
from copy import deepcopy

from . import catalog, contracts
from .agent import AnalysisAgent

VERSION = 'contextbase-project-result/1'
CATALOG_KINDS = frozenset({'system', 'function', 'entry', 'data', 'common', *catalog.EXTRA_KINDS})
KINDS = {'discovery': CATALOG_KINDS, 'relationship': {'relation'}, 'behavior': {'fact'}}


class ProjectAnalysisAgent(AnalysisAgent):
    name = 'project-analysis'
    stage = None
    catalog_policy = catalog.VERSION
    source_fact_policy = True
    record_kinds = CATALOG_KINDS | {'relation', 'fact'}
    instruction = '''Analyze the entire assigned original source scope, producing
evidence-backed structured facts, not specification prose. The original goal
obligations define required content and scope, not separate agent invocations.
Choose your investigation order and revisit source as needed in this session.
Build system, user-function, entry, data and common-processing catalogs; trace
relationships and behavior when those obligations are assigned. Count complete
user tasks rather than methods. Distinguish table definitions, references,
entities and DTOs. A relation must depend on a catalog record; a behavior fact
must depend on a relation. Those supporting records may be in this draft or in
the retained accepted view. Keep scope, ownership and dependency identities
explicit. Inspect configuration, registrations and omitted materials for gaps.
Trace values, conditions, order, exceptions, transactions and data changes from
original source. Distinguish static inference from observed source and runtime
evidence. Use indexed syntax facts and their limitations; when host semantic
bindings exist, reuse them instead of searching solely to rediscover a resolved
declaration. Keep unresolved targets and missing materials as explicit unknowns.
Save drafts as you investigate. Only the host and an independent verifier can
accept results.''' + catalog.EXTRACTION_RULES

    @classmethod
    def create(cls, source, work, request, *, native_mode=True, joint_analysis=True, **kwargs):
        if not native_mode or not joint_analysis or kwargs.get('handoff') is not None:
            raise ValueError('Project analysis requires native joint execution without legacy handoffs')
        return super().create(source, work, request, native_mode=True, joint_analysis=True, **kwargs)

    @classmethod
    def validate_request(cls, request):
        contracts.validate_request(request)

    def build_context(self, context):
        return {'executionScope': context['task']['executionScope'],
                'contentDependencies': 'Original goal requirements and record dependsOn; no fixed role count.',
                'classificationPolicy': catalog.VERSION,
                'retainedRecordsLocation': 'currentRecords',
                'sourceFactsLocation': 'ContextBase query tool',
                'completion': 'All selected obligations require coverage, evidence and explicit gaps.'}

    def validate_extraction(self, answer):
        super().validate_extraction(answer)
        known = dict(self.session.status()['records'])
        known.update({row['key']: row for row in answer.get('records', [])})
        obligations = self.session.obligations
        for row in answer.get('records', []):
            stage = obligations[row['ownerRequirement']]['stage']
            if row['kind'] not in KINDS[stage]:
                raise ValueError('Record kind disagrees with its original content obligation')
            expected = CATALOG_KINDS if stage == 'relationship' else {'relation'}
            if stage != 'discovery' and not any(
                    key in known and known[key]['kind'] in expected
                    and known[key]['ownerRequirement'] in obligations[row['ownerRequirement']]['requires']
                    for key in row['dependsOn']):
                raise ValueError('Relationship/behavior requires a record from its declared prerequisite')

    def run(self, *, requirements=None, timeout=1800, inline_sources=False, runner=None, compact=False):
        self._check_semantic_source()
        targets = self.session._select(requirements)
        state = self.session._state()
        if state['status'] not in {'active', 'complete'}:
            return {'status': state['status'], 'actions': [], 'session': self.status()}
        accepted = set(state['acceptedRequirements'])
        selected = [key for key in targets if key not in accepted]
        if not selected:
            return {'status': 'complete', 'actions': [], 'session': self.status()}
        missing = {dep for key in selected for dep in self.session.obligations[key]['requires']
                   if dep not in accepted and dep not in selected}
        if missing:
            return {'status': 'needs-prerequisites', 'missingRequirements': sorted(missing),
                    'actions': [], 'session': self.status()}
        attempt = self.session._attempt_key(state, selected)
        if attempt in state['attempts']:
            return {'status': 'needs-investigation', 'pending': state['attempts'][attempt],
                    'actions': [], 'session': self.status()}
        action, pending = self._execute_attempt(selected, attempt_key=attempt, timeout=timeout,
            inline_sources=inline_sources, runner=runner, compact=compact)
        return {'status': 'needs-investigation' if pending else 'complete',
                **({'pending': pending} if pending else {}), 'actions': [action], 'session': self.status()}

    def amend_candidate(self, from_work, candidate_id, verification_id, finding_ids=None, *,
                        replace_keys, timeout=1800, runner=None):
        """Seed an explicit candidate correction and independently recheck its full goal."""
        from .native_amendment import install
        seed, _ = install(self, from_work, candidate_id, verification_id, finding_ids,
                          replace_keys=replace_keys)
        return self.run(requirements=seed['requirements'], timeout=timeout, runner=runner)

    def export(self):
        self._check_semantic_source()
        self.session.source.verify()
        state = self.session._state()
        if set(state['acceptedRequirements']) != set(self.session.obligations):
            raise ValueError('Project publication requires every original obligation to be accepted')
        current = self.session._current(state)
        self.session._validate_records(current['records'])
        payload = {'schema': VERSION, 'producer': self.name,
                   'request': deepcopy(self.session.config['request']),
                   'snapshot': deepcopy(self.session.source.manifest),
                   'goalSha256': contracts.digest(self.session.config['request']['goal']),
                   'revision': state['revision'], 'catalogPolicy': catalog.VERSION,
                   'roleSpecs': deepcopy(self.session.config['roleSpecs']),
                   **{key: deepcopy(current[key]) for key in
                      ('records', 'unknowns', 'receipts', 'acceptedRequirements')}}
        envelope = {'sha256': contracts.digest(payload), 'payload': payload}
        validate_export(envelope)
        return envelope


def validate_export(envelope):
    """Validate a result artifact; this does not grant an external artifact trust."""
    if (not isinstance(envelope, dict) or set(envelope) != {'sha256', 'payload'}
            or envelope['sha256'] != contracts.digest(envelope['payload'])):
        raise ValueError('Project result fingerprint mismatch')
    payload = envelope['payload']
    if (set(payload) != {'schema', 'producer', 'request', 'snapshot', 'goalSha256', 'revision',
                         'catalogPolicy', 'roleSpecs', 'records', 'unknowns', 'receipts', 'acceptedRequirements'}
            or payload['schema'] != VERSION or payload['producer'] != ProjectAnalysisAgent.name
            or payload['catalogPolicy'] != catalog.VERSION):
        raise ValueError('Invalid project result contract')
    contracts.validate_request(payload['request'])
    from .roles import validate_roles
    validate_roles(payload['roleSpecs'], check_file=False)
    obligations = {row['id']: row for row in payload['request']['goal']['requirements']}
    if (payload['goalSha256'] != contracts.digest(payload['request']['goal'])
            or set(payload['acceptedRequirements']) != set(obligations)
            or set(payload['receipts']) != set(obligations)):
        raise ValueError('Project result must cover the complete original goal')
    catalog.validate_records(payload['records'], obligations, strict=True, unknown_ids=set(payload['unknowns']))
    for key, row in payload['records'].items():
        owner = row['ownerRequirement']
        body = {k: v for k, v in row.items() if k not in {'id', 'version'}}
        if (row['key'] != key or row['version'] != contracts.digest(body)
                or row['kind'] not in KINDS[obligations[owner]['stage']]
                or row['id'] != contracts.record_id(payload['request']['projectId'], row['kind'], key)):
            raise ValueError('Project record identity or version changed')
        if [dep['key'] for dep in row['dependencies']] != row['dependsOn']:
            raise ValueError('Project record dependencies changed')
        for dep in row['dependencies']:
            target = payload['records'].get(dep['key'])
            if (target is None or dep['version'] != target['version']
                    or obligations[target['ownerRequirement']]['scope'] != obligations[owner]['scope']):
                raise ValueError('Project record prerequisite changed')
    for key, receipt in payload['receipts'].items():
        expected = {dep: payload['receipts'][dep]['contentSha256'] for dep in obligations[key]['requires']}
        if receipt['requires'] != expected:
            raise ValueError('Project obligation prerequisite changed')
