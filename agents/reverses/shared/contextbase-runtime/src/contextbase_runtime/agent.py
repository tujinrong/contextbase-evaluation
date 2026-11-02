"""Shared lifecycle for independently owned, single-layer analysis agents.

This module does not import or launch an extraction agent. Its caller supplies
the concrete agent, which owns the task scope, prompt and context projection.
"""
from __future__ import annotations

from copy import deepcopy
import inspect
from pathlib import Path

from . import contracts, catalog
from .controller import AcceptanceError, Session


class AgentWorkspace(Session):
    def __init__(self, work, agent):
        self.agent = agent
        super().__init__(work)

    def _prepare(self, stage, operation, requirements, candidate, origin, feedback=None, *, compact=False):
        if operation == 'extract' and stage != self.agent.stage:
            raise ValueError('This agent only extracts its configured scope: ' + str(self.agent.stage))
        return super()._prepare(stage, operation, requirements, candidate, origin, feedback, compact=compact)

    def _task_extensions(self, task, view):
        records = (view or {}).get('records', {})
        modern = (getattr(self.agent, 'catalog_policy', None) == catalog.VERSION or
                  (task['operation'] == 'verify' and self._catalog_policy()))
        extensions = super()._task_extensions(task, view)
        if modern:
            extensions.update({'catalogPolicy': catalog.VERSION,
                    'classificationBindings': catalog.bindings(records) if task['operation'] == 'verify' else []}
            )
        if task['operation'] == 'extract' and task['origin'] != 'external-handoff':
            extensions['recordKinds'] = sorted(self.agent.record_kinds)
        if getattr(self.agent, 'source_fact_policy', False):
            extensions['sourceFactsSha256'] = self.fact_index().sha256
        if task['origin'] != 'external-handoff':
            from .repair import extensions as repair_extensions
            extensions.update(repair_extensions(self, task))
            from .amendment_runtime import extensions as amendment_extensions
            extensions.update(amendment_extensions(self, {**task, **extensions}))
        if self.config.get('semanticOptions'):
            from .semantic_support import task_extensions
            extensions.update(task_extensions(self))
        from .facts import USAGE_POLICY
        if extensions.get('factUsagePolicy') == USAGE_POLICY and task['operation'] == 'verify':
            proposal = self.store.get('candidates/' + task['candidate'] + '.json')
            extensions['sourceOnlyRecordKeys'] = sorted(row['recordKey']
                for row in proposal['answer'].get('factUsage', [])
                if row.get('indexedEvidence') == 'not-applicable')
        return extensions

    def _catalog_policy(self):
        if getattr(self.agent, 'catalog_policy', None) == catalog.VERSION:
            return catalog.VERSION
        if self.store.path('incoming.json').exists():
            return self.store.get('incoming.json')['payload'].get('catalogPolicy')
        return None

    def _instruction(self, task):
        if task['operation'] == 'extract':
            from .facts import instruction as fact_instruction
            from .repair import POLICY as REPAIR_POLICY
            from .candidate_amendment import POLICY as AMENDMENT_POLICY
            fact_policy = fact_instruction(task, evidence=bool(task.get('evidencePolicy') or task.get('incrementalPolicy') or task.get('nativeToolsPolicy')))
            return self.agent.instruction + self._semantic_instruction(task) + ('\n' + fact_policy if task.get('sourceFactsSha256') else '') + ('\n' + REPAIR_POLICY if task.get('repairSeedSha256') else '') + ('\n' + AMENDMENT_POLICY if task.get('amendmentPolicy') else '') + '''
Follow-up paths name acquired files from task.authorizedSourcePaths only.
For missing or omitted materials, preserve the requested names in the question
and unknown, using paths:[] unless an acquired file actually supports the query.
Do not fabricate an anchor. Follow-up stage and requirement must match an
original goal obligation in the assigned scope; requirement may be null.'''
        from .facts import instruction as fact_instruction
        fact_policy = fact_instruction(task, verification=True, evidence=bool(task.get('evidencePolicy') or task.get('incrementalPolicy') or task.get('nativeToolsPolicy')))
        return super()._instruction(task) + self._semantic_instruction(task) + ('\n' + fact_policy if task.get('sourceFactsSha256') else '') + (catalog.VERIFICATION_RULES
            if task.get('catalogPolicy') == catalog.VERSION else '') + '''\nQuestions whose ID starts with followup:
are explicit investigation requests. Mark one resolved with exact source evidence
only after its question has been answered. A non-blocking judgment permits work
in a narrower scope but does not close the investigation request. Historical
acceptance of the target requirement alone is not proof of resolution.'''

    def _incremental_instruction(self, task):
        from .facts import instruction as fact_instruction
        if task['operation'] == 'extract':
            from .candidate_amendment import POLICY as AMENDMENT_POLICY
            return (self.agent.instruction + self._semantic_instruction(task) + ('\n' + fact_instruction(task, evidence=True) if task.get('sourceFactsSha256') else '')
                    + ('\n' + AMENDMENT_POLICY if task.get('amendmentPolicy') else '')
                    + '\nPreserve original scope/owner and return only this phase schema. '
                    'Followup paths must name acquired files; missing materials use paths:[].')
        return (super()._incremental_instruction(task) + self._semantic_instruction(task)
                + ('\n' + catalog.EXTRACTION_RULES if task.get('catalogPolicy') == catalog.VERSION else '')
                + ('\n' + fact_instruction(task, evidence=True, verification=True) if task.get('sourceFactsSha256') else '')
                + '\nThe current host unit alone assigns returned record/unknown/scope/check arrays. '
                  'Root requirements remain complete and the host exhaustively assigns all other units. '
                  'Independently resolve inherited followup questions from source; historical acceptance '
                  'and non-blocking judgments do not prove a followup was answered.')

    @staticmethod
    def _semantic_instruction(task):
        if not task.get('semanticPolicy'):
            return ''
        from .semantic_support import POLICY
        return '\n' + POLICY

    def _validate_incremental_answer(self, task, answer):
        if task['operation'] == 'extract':
            self.agent.validate_extraction(answer)
            if task.get('sourceFactsSha256'):
                self.fact_index().validate_usage(answer, task['sourceFactsSha256'])
        return super()._validate_incremental_answer(task, answer)

    def _context(self, task, inline_sources):
        context = super()._context(task, inline_sources)
        context['agent'] = {'name': self.agent.name, 'stage': self.agent.stage}
        context['currentUnknowns'] = deepcopy(self._current(self._state())['unknowns'])
        if task.get('semanticPolicy'):
            from .semantic_support import capabilities
            context['semanticAnalysis'] = capabilities(self)
        if task.get('amendmentPolicy'):
            from . import amendment_runtime
            seed, spec = amendment_runtime.installed(self, task)
            if task['operation'] == 'extract':
                context['candidateAmendment'] = {'seed': deepcopy(seed), 'spec': deepcopy(spec)}
            else:
                proposal = self.store.get('candidates/' + task['candidate'] + '.json')
                author = self.store.get('tasks/' + proposal['taskId'] + '/request.json')
                context['amendmentAudit'] = amendment_runtime.audit(self, author)
        if task['operation'] == 'extract':
            context['assignment'] = self.agent.build_context(context)
            if task.get('repairSeedSha256'):
                from .repair import context as repair_context
                context['rejectedDraftRepair'] = repair_context(self.store.get('repair-seed.json'), task)
        elif self.store.get('candidates/' + task['candidate'] + '.json')['provenance']['kind'] == 'external-handoff':
            context['externalPremises'] = {
                'trust': 'Untrusted external claims; historical checks grant no authority.',
                'instruction': 'Recheck completeness, omissions, unknowns and all prerequisites '
                               'against original source before allowing this agent to use them.'}
        if task['operation'] == 'verify':
            proposal = self.store.get('candidates/' + task['candidate'] + '.json')
            if proposal['provenance'].get('proposalOrigin') == 'repaired-rejected-draft':
                seed = self.store.get('repair-seed.json')
                author_task = self.store.get('tasks/' + proposal['taskId'] + '/request.json')
                raw = self.store.get('tasks/' + proposal['taskId'] + '/transport.json')['answer']
                from .wire import CompactWire
                patch = CompactWire(author_task).decode_response(raw) if author_task.get('wireBinding') else raw
                selected = {item['key'] for item in seed['records']}
                context['repairAudit'] = {
                    'trust': 'Rejected seed has no approval. Independently recheck the entire combined view, '
                             'including omissions and unchanged claims; the patch alone is insufficient.',
                    'seedSha256': author_task['repairSeedSha256'],
                    'originalFailure': seed['originalFailure'],
                    'selectedOriginalRecords': [item for item in seed['answer']['records'] if item['key'] in selected],
                    'patch': patch, 'combinedAnswerSha256': contracts.digest(proposal['answer'])}
        return context

    def _record(self, task, answer, provenance):
        if task['operation'] == 'extract':
            self.agent.validate_extraction(answer)
            if task.get('sourceFactsSha256'):
                contracts.validate(answer, contracts.result_schema(task))
                self.fact_index().validate_usage(answer, task['sourceFactsSha256'])
        return super()._record(task, answer, provenance)

    def _check_adoption(self, view, answer):
        if getattr(self.agent, 'source_fact_policy', False):
            if (answer.get('sourceFactsSha256') != self.fact_index().sha256
                    or answer.get('factUsageCheck', {}).get('status') != 'pass'):
                raise AcceptanceError('Independent source-fact usage verification must pass')
            if any(row['status'] != 'pass'
                   for row in answer['factUsageCheck'].get('sourceOnlyChecks', [])):
                raise AcceptanceError('Independent source-only applicability verification must pass')
        modern = self._catalog_policy() == catalog.VERSION
        if modern:
            try:
                catalog.validate_records(view['records'], self.obligations, strict=True)
                bound = {item['key']: item['sha256'] for item in catalog.bindings(view['records'])}
                actual = {item['key']: item['recordSha256'] for item in answer.get('classificationChecks', [])}
                if bound != actual:
                    raise ValueError('Classification acceptance view binding changed')
                expected_scopes = {self.obligations[key]['scope'] for key in view['acceptedRequirements']
                                   if self.obligations[key]['stage'] == 'discovery'}
                if expected_scopes != {item['scope'] for item in answer.get('scopeChecks', [])}:
                    raise ValueError('Classification acceptance scopes changed')
                catalog.require_resolved(view, answer)
            except ValueError as exc:
                raise AcceptanceError(str(exc)) from exc
        decisions = {item['unknownId']: item for item in answer['unknownChecks']}
        accepted = set(view['acceptedRequirements'])
        for key, question in view['unknowns'].items():
            if (key.startswith('followup:') and
                    set(question['content']['relatedRequirements']) & accepted and
                    decisions[key]['status'] != 'resolved'):
                raise AcceptanceError('An inherited investigation request for an accepted obligation '
                                      'must be independently resolved from source')

    def _proposal_view(self, state, task, answer):
        view = super()._proposal_view(state, task, answer)
        if task['origin'] == 'external-handoff':
            incoming = self.store.get('incoming.json')
            # Preserve global question identities and ownership across workspaces.
            view['unknowns'] = deepcopy(incoming['payload']['unknowns'])
        else:
            from .handoff import followup_question
            proposals = [self.store.get('candidates/' + key + '.json') for key in state['candidates']]
            for proposal in [*proposals, {'answer': answer, 'requirements': task['requirements']}]:
                for note in proposal['answer']['followups']:
                    question = followup_question(note, proposal['requirements'])
                    view['unknowns'].setdefault(question['id'], question)
        if self._catalog_policy() == catalog.VERSION:
            unknown_ids = set(view['unknowns'])
            catalog.validate_records(view['records'], self.obligations, strict=True, unknown_ids=unknown_ids)
        return view


class AnalysisAgent:
    """Resource, verification and persistence mechanics; subclasses own analysis."""

    stage: str
    name: str
    instruction: str
    record_kinds: frozenset[str]

    def __init__(self, work: Path):
        self.work = Path(work)
        self.session = AgentWorkspace(self.work, self)
        binding = self.session.store.get('agent.json')
        if binding != self.binding():
            raise ValueError('Workspace belongs to a different agent or agent implementation')

    @classmethod
    def binding(cls):
        files = {name: Path(__file__).with_name(name).read_text(encoding='utf-8')
                 for name in ('agent.py', 'handoff.py', 'cli.py', 'config.py', 'catalog.py')}
        files['implementation'] = Path(inspect.getfile(cls)).read_text(encoding='utf-8')
        return {'schema': 'contextbase-agent/1', 'name': cls.name, 'stage': cls.stage,
                'implementationSha256': contracts.digest(files)}

    @classmethod
    def create(cls, source, work, request, *, handoff=None, evidence_mode=False, incremental_mode=False,
               native_mode=False, joint_analysis=False, role_specs=None, semantic_options=None):
        contracts.validate_request(request)
        cls.validate_request(request)
        if semantic_options is not None and cls.stage not in {'discovery', 'relationship', None}:
            raise ValueError('Normal semantic evidence is currently supported by Discovery and Relationship only')
        if cls.stage == 'discovery' and handoff is not None:
            raise ValueError('Discovery starts from source and does not accept upstream handoffs')
        session = Session.create(Path(source), Path(work), request, evidence_mode=evidence_mode,
                                 incremental_mode=incremental_mode, native_mode=native_mode,
                                 joint_analysis=joint_analysis, role_specs=role_specs, semantic_options=semantic_options)
        session.store.put('agent.json', cls.binding())
        agent = cls(work)
        if handoff is not None:
            from .handoff import receive
            receive(agent, handoff)
        return agent

    @classmethod
    def validate_request(cls, request):
        if not any(item['stage'] == cls.stage for item in request['goal']['requirements']):
            raise ValueError('Request has no obligations for ' + cls.stage)

    def validate_extraction(self, answer):
        if any(record.get('kind') not in self.record_kinds for record in answer.get('records', [])):
            raise ValueError(self.name + ' returned a record outside its analysis responsibility')

    def build_context(self, context):
        raise NotImplementedError

    def status(self):
        state = self.session.status()
        owned = self.session._select(None, self.stage)
        accepted = set(state['acceptedRequirements'])
        return {**state, 'agent': self.name, 'stage': self.stage,
                'agentRequirements': owned,
                'remainingAgentRequirements': [key for key in owned if key not in accepted],
                'pendingHandoff': self.session.store.path('incoming.json').exists()
                    and not bool(state['revision'])}

    def _execute_attempt(self, requirements, *, timeout, inline_sources, runner, compact,
                         feedback=None, attempt_key=None):
        if self.session.config.get('nativeToolsPolicy') and runner is None:
            from .native_environment import scope
            environment = None
            try:
                with scope(excluded_roots=(self.session.store.root, self.session.source.root)) as environment:
                    return self._execute_attempt_scoped(requirements, timeout=timeout,
                        inline_sources=inline_sources, runner=runner, compact=compact,
                        feedback=feedback, attempt_key=attempt_key)
            finally:
                if environment is not None:
                    self.session.store.put('native-environments/' + environment.identifier + '.json', environment.report())
        return self._execute_attempt_scoped(requirements, timeout=timeout,
            inline_sources=inline_sources, runner=runner, compact=compact,
            feedback=feedback, attempt_key=attempt_key)

    def _execute_attempt_scoped(self, requirements, *, timeout, inline_sources, runner, compact,
                         feedback=None, attempt_key=None):
        """Extract, independently verify and adopt once, retaining a rejected result."""
        proposed = None
        if (self.session.config.get('incrementalPolicy') or self.session.config.get('nativeToolsPolicy')) and feedback is None:
            # A transport failure in verification must not re-extract the
            # already frozen candidate. Resumed review uses the same view.
            state = self.session._state()
            expected_origin = ('host-composed' if self.session.config.get('incrementalPolicy') else 'host-executed') if runner is None else 'injected-test-transport'
            for key in reversed(state['candidates']):
                saved = self.session.store.get('candidates/' + key + '.json')
                if (saved['stage'] == self.stage and saved['requirements'] == requirements
                        and saved['baseVersion'] == state['version']
                        and saved['baseRevision'] == state['revision']
                        and saved['feedback'] is None
                        and saved['provenance'].get('kind') == expected_origin):
                    self.session._replay_evidence(
                        self.session.store.get('tasks/' + saved['taskId'] + '/request.json'), saved)
                    proposed = {'id': key, 'result': deepcopy(saved['answer'])}
                    break
        if proposed is None:
            proposed = self.session.execute(self.stage, requirements=requirements, feedback=feedback,
                                            timeout=timeout, inline_sources=inline_sources,
                                            runner=runner, compact=compact)
        from .amendment_runtime import unresolved
        open_issues = unresolved(self.session, proposed['id'])
        if open_issues:
            action = {'agent': self.name, 'requirements': requirements,
                      'candidate': proposed['id'], 'verification': None}
            pending = {**action, 'reason': 'Selected current amendment issues remain unresolved; '
                       'full independent review has not started.', 'unresolvedIssues': open_issues,
                       'followups': proposed['result']['followups'], 'findings': []}
            with self.session.store.transaction() as latest:
                key = attempt_key if attempt_key is not None else self.session._attempt_key(latest, requirements)
                latest['attempts'][key] = pending
                latest['stopReason'] = pending['reason']
                self.session.store.save_state(latest)
            return action, pending
        if self.session.config.get('nativeToolsPolicy'):
            from .native_readiness import assess
            candidate = self.session.store.get('candidates/' + proposed['id'] + '.json')
            readiness = assess(proposed['result'], candidate['view']['acceptedRequirements'])
            if not readiness['readyForReview']:
                action = {'agent': self.name, 'requirements': requirements,
                          'candidate': proposed['id'], 'verification': None}
                pending = {**action, 'reason': readiness['reason'], 'readiness': readiness,
                           'followups': proposed['result']['followups'], 'findings': []}
                with self.session.store.transaction() as latest:
                    key = attempt_key if attempt_key is not None else self.session._attempt_key(latest, requirements)
                    latest['attempts'][key] = pending
                    latest['stopReason'] = pending['reason']
                    self.session.store.save_state(latest)
                return action, pending
        verified = self.session.verify(proposed['id'], timeout=timeout,
                                       inline_sources=inline_sources, runner=runner, compact=compact)
        action = {'agent': self.name, 'requirements': requirements,
                  'candidate': proposed['id'], 'verification': verified['id']}
        try:
            self.session.adopt(proposed['id'])
        except AcceptanceError as exc:
            pending = {**action, 'reason': str(exc), 'followups': proposed['result']['followups'],
                       'findings': verified['result']['findings']}
            with self.session.store.transaction() as latest:
                # run pins its key before execution; explicit retry binds it only
                # after rejection, using the state protected by this transaction.
                key = attempt_key if attempt_key is not None else self.session._attempt_key(latest, requirements)
                latest['attempts'][key] = pending
                latest['stopReason'] = str(exc)
                self.session.store.save_state(latest)
            return action, pending
        return action, None

    def run(self, *, requirements=None, timeout=1800, inline_sources=False, runner=None, compact=False):
        self._check_semantic_source()
        targets = self.session._select(requirements, self.stage)
        state = self.session._state()
        if state['status'] not in {'active', 'complete'}:
            return {'status': state['status'], 'actions': [], 'session': self.status()}
        if self.session.store.path('incoming.json').exists() and not state['revision']:
            from .handoff import revalidate
            result = revalidate(self, timeout=timeout, inline_sources=inline_sources, runner=runner)
            if result is not None:
                return result
        actions = []
        while True:
            state = self.session._state()
            accepted = set(state['acceptedRequirements'])
            remaining = set(targets) - accepted
            if not remaining:
                return {'status': 'complete', 'actions': actions, 'session': self.status()}
            missing = {dep for key in remaining for dep in self.session.obligations[key]['requires']
                       if dep not in accepted}
            ready = [key for key in targets if key in remaining
                     and set(self.session.obligations[key]['requires']).issubset(accepted)]
            if not ready:
                return {'status': 'needs-prerequisites', 'missingRequirements': sorted(missing),
                        'actions': actions, 'session': self.status()}
            scope = self.session.obligations[ready[0]]['scope']
            selected = [key for key in ready if self.session.obligations[key]['scope'] == scope]
            attempt = self.session._attempt_key(state, selected)
            if attempt in state['attempts']:
                return {'status': 'needs-investigation', 'pending': state['attempts'][attempt],
                        'actions': actions, 'session': self.status()}
            action, pending = self._execute_attempt(selected, attempt_key=attempt, timeout=timeout,
                                                    inline_sources=inline_sources, runner=runner, compact=compact)
            actions.append(action)
            if pending is not None:
                return {'status': 'needs-investigation', 'pending': pending,
                        'actions': actions, 'session': self.status()}

    def _check_semantic_source(self):
        if self.session.config.get('semanticOptions'):
            from .semantic_support import initialize
            index = initialize(self.session)
            index.validate()
            index.assert_current_source()

    def export(self):
        self._check_semantic_source()
        from .handoff import export
        return export(self)

    def repair(self, from_work, task_id, record_keys, *, timeout=1800,
               inline_sources=False, runner=None, compact=False):
        """Explicit repair of selected records in a rejected draft, then full verification."""
        from .repair import install
        seed = install(self, from_work, task_id, record_keys)
        return self.run(requirements=seed['originalTask']['requirements'], timeout=timeout,
                        inline_sources=inline_sources, runner=runner, compact=compact)

    def amend_candidate(self, bundle, verification_id, finding_ids=None, *, replace_keys,
                        add_kinds, timeout=1800, inline_sources=False, runner=None, compact=False):
        """Import an untrusted frozen candidate in fresh D work, then amend and reverify."""
        if self.stage != 'discovery' or inline_sources or compact:
            raise ValueError('Candidate amendment requires Discovery incremental request mode')
        from .amendment_seed import install
        seed, _ = install(self, bundle, verification_id, finding_ids,
                          replace_keys=replace_keys, add_kinds=add_kinds)
        return self.run(requirements=seed['requirements'], timeout=timeout,
                        inline_sources=False, runner=runner, compact=False)

    def retry(self, feedback, *, requirements=None, timeout=1800, inline_sources=False, runner=None, compact=False):
        """One explicit source re-investigation; never clear a blocked run implicitly."""
        self._check_semantic_source()
        state = self.session._state()
        if feedback not in state['candidates']:
            raise ValueError('Retry requires a known candidate from this agent')
        prior = self.session.store.get('candidates/' + feedback + '.json')
        if prior['stage'] != self.stage or prior['provenance']['kind'] == 'external-handoff':
            raise ValueError('Retry feedback must belong to this agent, not an external premise')
        selected = self.session._select(requirements or prior['requirements'], self.stage)
        if set(selected) & set(state['acceptedRequirements']):
            raise ValueError('Explicitly revise accepted obligations before retrying their extraction')
        action, pending = self._execute_attempt(selected, feedback=feedback, timeout=timeout,
                                                inline_sources=inline_sources, runner=runner, compact=compact)
        if pending is not None:
            return {'status': 'needs-investigation', 'pending': pending,
                    'actions': [action], 'session': self.status()}
        return {'status': 'complete', 'actions': [action], 'session': self.status()}
