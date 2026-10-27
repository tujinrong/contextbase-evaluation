"""Public single-agent runs and portable transfers; provider replies are synthetic."""
from copy import deepcopy
import importlib
import io
import json
from pathlib import Path
import shutil
import tempfile
import unittest
from contextlib import redirect_stdout
from unittest.mock import patch

from contextbase_runtime import catalog, contracts
from contextbase_runtime.handoff import source_binding
from contextbase_discovery import DiscoveryAgent
from contextbase_relationship import RelationshipAgent
from contextbase_behavior import BehaviorAgent


def request():
    return {'schema': contracts.VERSION, 'projectId': 'synthetic-independent-agents',
            'goal': {'id': 'inspect', 'question': 'Inspect registration from source.', 'requirements': [
                {'id': 'catalog', 'stage': 'discovery', 'scope': 'registration',
                 'question': 'List functions, data and common processing.', 'requires': []},
                {'id': 'links', 'stage': 'relationship', 'scope': 'registration',
                 'question': 'Trace their relationships.', 'requires': ['catalog']},
                {'id': 'rules', 'stage': 'behavior', 'scope': 'registration',
                 'question': 'Trace their conditions and effects.', 'requires': ['links']}]},
            'allowedPaths': ['.'], 'excludedPaths': []}


def add_fact_usage(context, answer):
    """Bind synthetic replies to host fact rows, including after fixture mutation."""
    task = context['task']
    if 'sourceFactsSha256' not in task:
        return answer
    answer['sourceFactsSha256'] = task['sourceFactsSha256']
    if task['operation'] == 'verify':
        entry = context['inventory']['files'][0]
        answer['factUsageCheck'] = {'status': 'pass', 'reason': 'Synthetic independent fact relevance check.',
            'evidence': [{'path': entry['path'], 'startLine': 1, 'endLine': 2, 'sha256': entry['sha256']}]}
        return answer
    structure = context['structure']
    facts = [dict(zip(structure[key]['columns'], row))
             for key in ('symbols', 'calls', 'entries', 'imports') for row in structure[key]['rows']]
    answer['factUsage'] = []
    for record in answer['records']:
        available = [fact['id'] for fact in facts if any(
            structure['files'][fact['file']]['path'] == ref['path']
            and fact['startLine'] <= ref['endLine'] and ref['startLine'] <= fact['endLine']
            for ref in record['evidence'])]
        answer['factUsage'].append({'recordKey': record['key'], 'factIds': available[:1],
            'reason': 'Synthetic overlapping source fact.' if available else 'No indexed fact overlaps this source evidence.'})
    return answer


def simulated_answer(context):
    task = context['task']
    entry = context['inventory']['files'][0]
    evidence = {'path': entry['path'], 'startLine': 1, 'endLine': 2, 'sha256': entry['sha256']}
    if task['operation'] == 'verify':
        answer = {'taskId': task['id'], 'candidateSha256': task['candidate'],
                'viewSha256': task['viewSha256'],
                'checks': [{'requirement': key, 'status': 'pass', 'reason': 'Synthetic verification.',
                            'evidence': [evidence]} for key in task['requirements']],
                'unknownChecks': [{'unknownId': item['id'], 'unknownSha256': item['sha256'],
                    'status': 'non-blocking', 'blocksRequirements': [], 'reason': 'Synthetic scope check.',
                    'evidence': [evidence]} for item in task['unknownBindings']],
                'findings': [], 'unknowns': []}
        if task.get('catalogPolicy') == catalog.VERSION:
            answer['classificationChecks'] = [
                {'key': item['key'], 'recordSha256': item['sha256'], 'status': 'pass',
                 'reason': 'Synthetic classification check.', 'evidence': [evidence]}
                for item in task['classificationBindings']]
            answer['scopeChecks'] = [
                {'scope': scope, 'status': 'pass', 'reason': 'Synthetic scope coverage check.', 'evidence': [evidence]}
                for scope in catalog.scopes(task)]
        return add_fact_usage(context, answer)
    obligations = {item['id']: item for item in task['goalRequirements']}
    records = [{'key': key + '.record', 'ownerRequirement': key,
        'kind': {'discovery': 'function', 'relationship': 'relation', 'behavior': 'fact'}[task['stage']],
        'name': key, 'statement': 'Synthetic source claim for ' + key, 'basis': 'observed-source',
        'evidence': [evidence], 'dependsOn': [dep + '.record' for dep in obligations[key]['requires']]}
        for key in task['requirements']]
    if task.get('catalogPolicy') == catalog.VERSION:
        for item in records:
            key = item['ownerRequirement']
            item['classification'] = {
                'category': 'main', 'scope': obligations[key]['scope'], 'area': 'Synthetic area',
                'actors': ['Synthetic operator'], 'businessObject': 'Synthetic record',
                'purpose': 'Process the record', 'trigger': 'Submit', 'outcome': 'Processed',
                'rationale': 'Observed source responsibility', 'alternative': 'Considered an internal operation',
                'entryRefs': [key + '.entry']}
        records += [{'key': key + '.entry', 'ownerRequirement': key, 'kind': 'entry', 'name': key + ' entry',
                     'statement': 'Synthetic source entry for ' + key, 'basis': 'observed-source',
                     'evidence': [evidence], 'dependsOn': [], 'classification': None}
                    for key in task['requirements']]
    return add_fact_usage(context, {'taskId': task['id'], 'records': records,
            'coverage': [{'requirement': key, 'status': 'supported',
                          'recordKeys': [key + '.record'] + ([key + '.entry'] if task.get('catalogPolicy') == catalog.VERSION else []),
                          'evidence': [evidence]} for key in task['requirements']],
            'unknowns': [], 'followups': []})


class IndependentAgentTests(unittest.TestCase):
    def setUp(self):
        root = Path(__file__).resolve().parents[4] / '.tmp'
        root.mkdir(exist_ok=True)
        self.temporary = tempfile.TemporaryDirectory(prefix='independent-agents-', dir=root)
        self.root = Path(self.temporary.name)
        self.source = self.root / 'source'
        self.source.mkdir()
        (self.source / 'Registration.cs').write_text(
            'class Registration {\n bool Save(int value) { return value > 0; }\n}\n', encoding='utf-8')
        self.calls = []

    def tearDown(self):
        self.temporary.cleanup()

    def provider(self, workspace, job, prompt, schema, timeout):
        context = json.loads(prompt[prompt.index('{"request":'):])
        self.calls.append(context)
        return {'exit_code': 0, 'metadata': {'status': 'passed'}, 'answer': simulated_answer(context)}

    def run_agent(self, agent, provider=None, **kwargs):
        with patch('contextbase_runtime.provider.run_job', side_effect=provider or self.provider):
            return agent.run(inline_sources=True, **kwargs)

    def discovery(self, provider=None):
        agent = DiscoveryAgent.create(self.source, self.root / 'discovery', request())
        self.assertEqual('complete', self.run_agent(agent, provider)['status'])
        return agent

    def test_three_real_agent_classes_only_extract_their_own_layer(self):
        agents = [DiscoveryAgent, RelationshipAgent, BehaviorAgent]
        handoff = None
        fingerprints = {}
        for agent_type in agents:
            agent = agent_type.create(self.source, self.root / agent_type.stage, request(), handoff=handoff)
            self.assertEqual('complete', self.run_agent(agent)['status'])
            handoff = agent.export()
            self.assertEqual(fingerprints, handoff['payload']['premises'])
            fingerprints[agent.stage] = handoff['sha256']
        extracts = [c for c in self.calls if c['task']['operation'] == 'extract']
        self.assertEqual(['discovery', 'relationship', 'behavior'], [c['task']['stage'] for c in extracts])
        self.assertEqual(8, len({c['task']['contextId'] for c in self.calls}))
        self.assertIn('resourcesToAccountFor', extracts[0]['assignment'])
        self.assertIn('verifiedCatalog', extracts[1]['assignment'])
        self.assertIn('verifiedRelationships', extracts[2]['assignment'])
        self.assertEqual(['catalog', 'links', 'rules'], handoff['payload']['acceptedRequirements'])
        self.assertEqual(4, len(handoff['payload']['records']))

    def test_old_or_incomplete_lineage_cannot_be_imported(self):
        envelope = self.discovery().export()
        for index, change in enumerate((
                lambda p: p.update(schema='contextbase-handoff/1'),
                lambda p: p.pop('premises'),
                lambda p: p.update(premises={'discovery': '0' * 64}))):
            damaged = deepcopy(envelope)
            change(damaged['payload'])
            damaged['sha256'] = contracts.digest(damaged['payload'])
            with self.assertRaises(ValueError):
                RelationshipAgent.create(self.source, self.root / ('bad-lineage-' + str(index)),
                                         request(), handoff=damaged)

    def test_later_agents_without_handoff_do_not_run_an_upstream_agent(self):
        for agent_type, missing in [(RelationshipAgent, 'catalog'), (BehaviorAgent, 'links')]:
            agent = agent_type.create(self.source, self.root / agent_type.stage, request())
            result = self.run_agent(agent)
            self.assertEqual('needs-prerequisites', result['status'])
            self.assertEqual([missing], result['missingRequirements'])
        self.assertEqual([], self.calls)

    def test_producer_work_and_source_can_disappear_after_export(self):
        first = self.discovery()
        envelope = first.export()
        copy = self.root / 'different-source-path'
        shutil.copytree(self.source, copy)
        first.work.rename(self.root / 'unavailable-producer-work')
        self.source.rename(self.root / 'unavailable-producer-source')
        relation = RelationshipAgent.create(copy, self.root / 'relationship', request(), handoff=envelope)
        self.assertEqual([], relation.status()['acceptedRequirements'])
        self.assertTrue(relation.status()['pendingHandoff'])
        self.assertEqual('complete', self.run_agent(relation)['status'])
        self.assertEqual('external-reverified', relation.status()['receipts']['catalog']['origin'])
        serialized = json.dumps(relation.export())
        self.assertNotIn(str(first.work).replace('\\', '\\\\'), serialized)
        self.assertNotIn('sourceRoot', envelope['payload']['source'])

    def test_receiver_rechecks_prerequisites_and_can_reject_a_prior_pass(self):
        envelope = self.discovery().export()
        relation = RelationshipAgent.create(self.source, self.root / 'relation', request(), handoff=envelope)
        def fail(*args):
            result = self.provider(*args)
            result['answer']['checks'][0]['status'] = 'fail'
            return result
        result = self.run_agent(relation, fail)
        self.assertEqual('needs-prerequisites', result['status'])
        self.assertEqual([], relation.status()['acceptedRequirements'])
        self.assertEqual('verify', self.calls[-1]['task']['operation'])
        count = len(self.calls)
        self.assertEqual('needs-prerequisites', self.run_agent(relation)['status'])
        self.assertEqual(count, len(self.calls))

    def test_injected_verifier_cannot_activate_external_premises(self):
        envelope = self.discovery().export()
        relation = RelationshipAgent.create(self.source, self.root / 'relation', request(), handoff=envelope)
        result = relation.run(runner=self.provider, inline_sources=True)
        self.assertEqual('needs-prerequisites', result['status'])
        self.assertEqual([], relation.status()['acceptedRequirements'])

    def test_injected_author_and_manual_submit_cannot_be_adopted(self):
        agent = DiscoveryAgent.create(self.source, self.root / 'discovery', request())
        self.assertEqual('needs-investigation', agent.run(runner=self.provider, inline_sources=True)['status'])
        self.assertEqual([], agent.status()['acceptedRequirements'])
        task = agent.session.prepare('discovery')
        candidate = agent.session.submit(task['id'], simulated_answer(agent.session._context(task, True)))
        with patch('contextbase_runtime.provider.run_job', side_effect=self.provider):
            agent.session.verify(candidate['id'], inline_sources=True)
        with self.assertRaisesRegex(ValueError, 'provenance'):
            agent.session.adopt(candidate['id'])

    def test_handoff_damage_owner_dependency_source_and_goal_are_rejected(self):
        envelope = self.discovery().export()
        changes = [lambda e: e.update(sha256='0' * 64),
                   lambda e: e['payload']['records']['catalog.record'].update(ownerRequirement='links'),
                   lambda e: e['payload']['records']['catalog.record'].update(version='0' * 64),
                   lambda e: e['payload']['source']['files'][0].update(sha256='0' * 64),
                   lambda e: e['payload']['request']['goal'].update(question='Different goal')]
        for index, change in enumerate(changes):
            damaged = deepcopy(envelope)
            change(damaged)
            if index:
                damaged['sha256'] = contracts.digest(damaged['payload'])
            with self.assertRaises(ValueError):
                RelationshipAgent.create(self.source, self.root / ('bad-' + str(index)), request(), handoff=damaged)

    def test_unknowns_remain_bound_and_receiver_must_judge_every_one(self):
        def with_unknown(*args):
            result = self.provider(*args)
            if 'coverage' in result['answer']:
                result['answer']['unknowns'] = [{'id': 'deployment', 'question': 'Deployment not observed.',
                    'relatedRequirements': ['catalog', 'links'], 'blocksRequirements': [],
                    'scopeReason': 'Static registration scope only.'}]
            return result
        envelope = self.discovery(with_unknown).export()
        original = deepcopy(envelope['payload']['unknowns'])
        relation = RelationshipAgent.create(self.source, self.root / 'relation', request(), handoff=envelope)
        self.assertEqual('complete', self.run_agent(relation)['status'])
        self.assertEqual(set(original), set(relation.status()['unknowns']))
        self.assertEqual(set(original), {i['id'] for i in self.calls[-3]['task']['unknownBindings']})

    def test_wrong_agent_cannot_open_or_extract_another_agents_work(self):
        first = self.discovery()
        with self.assertRaisesRegex(ValueError, 'different agent'):
            RelationshipAgent(first.work)
        with self.assertRaisesRegex(ValueError, 'only extracts'):
            first.session.prepare('relationship')

    def test_relationship_and_behavior_require_record_dependencies(self):
        envelope = self.discovery().export()
        relation = RelationshipAgent.create(self.source, self.root / 'relation', request(), handoff=envelope)
        def detached(*args):
            result = self.provider(*args)
            for record in result['answer'].get('records', []):
                record['dependsOn'] = []
            return result
        with self.assertRaisesRegex(ValueError, 'catalog record'):
            self.run_agent(relation, detached)

    def test_export_is_self_contained_and_forged_audit_is_not_authority(self):
        envelope = self.discovery().export()
        envelope['payload']['audit'] = [{'candidateSha256': '0' * 64, 'stage': 'discovery',
                                        'requirements': ['catalog'], 'origin': 'forged-pass',
                                        'followups': [], 'verificationSummaries': []}]
        envelope['sha256'] = contracts.digest(envelope['payload'])
        relation = RelationshipAgent.create(self.source, self.root / 'relation', request(), handoff=envelope)
        self.assertEqual([], relation.status()['acceptedRequirements'])
        self.assertEqual('complete', self.run_agent(relation)['status'])
        self.assertIn('externalPremises', self.calls[-3])

    def test_each_cli_init_status_missing_prerequisites_and_export(self):
        req = self.root / 'request.json'
        req.write_text(json.dumps(request()), encoding='utf-8')
        handoff = None
        for module, stage in [('contextbase_discovery', 'discovery'),
                              ('contextbase_relationship', 'relationship'), ('contextbase_behavior', 'behavior')]:
            main = importlib.import_module(module + '.__main__').main
            work = self.root / stage
            args = ['init', '--source', str(self.source), '--request', str(req), '--work', str(work)]
            if handoff:
                args += ['--handoff', str(handoff)]
            with redirect_stdout(io.StringIO()) as stream:
                self.assertEqual(0, main(args))
            self.assertEqual(stage, json.loads(stream.getvalue())['stage'])
            with patch('contextbase_runtime.provider.run_job', side_effect=self.provider), redirect_stdout(io.StringIO()):
                self.assertEqual(0, main(['run', '--work', str(work), '--inline-sources']))
            handoff = self.root / (stage + '.json')
            with redirect_stdout(io.StringIO()):
                self.assertEqual(0, main(['export', '--work', str(work), '--output', str(handoff)]))
                self.assertEqual(1, main(['export', '--work', str(work), '--output', str(handoff)]))

    def test_behavior_rejects_catalog_in_place_of_relationship_handoff(self):
        envelope = self.discovery().export()
        with self.assertRaisesRegex(ValueError, 'relationship handoff'):
            BehaviorAgent.create(self.source, self.root / 'behavior', request(), handoff=envelope)

    def test_dependency_version_tampering_is_rejected_in_behavior(self):
        envelope = self.discovery().export()
        relation = RelationshipAgent.create(self.source, self.root / 'relation', request(), handoff=envelope)
        self.run_agent(relation)
        envelope = relation.export()
        envelope['payload']['records']['links.record']['dependencies'][0]['version'] = '0' * 64
        envelope['sha256'] = contracts.digest(envelope['payload'])
        with self.assertRaisesRegex(ValueError, 'version'):
            BehaviorAgent.create(self.source, self.root / 'behavior', request(), handoff=envelope)

    def test_missing_fields_and_false_unknown_hash_are_contract_errors(self):
        envelope = self.discovery().export()
        del envelope['payload']['records']['catalog.record']['evidence']
        envelope['sha256'] = contracts.digest(envelope['payload'])
        with self.assertRaisesRegex(ValueError, 'contract'):
            RelationshipAgent.create(self.source, self.root / 'bad-field', request(), handoff=envelope)
        envelope = self.discovery_export_from_existing()
        envelope['payload']['unknowns']['q'] = {'id': 'q', 'sha256': '0' * 64, 'owners': ['catalog'],
            'content': {'id': 'q', 'question': 'Unknown.', 'relatedRequirements': ['catalog'],
                        'blocksRequirements': [], 'scopeReason': 'Not yet known.'}}
        envelope['sha256'] = contracts.digest(envelope['payload'])
        with self.assertRaisesRegex(ValueError, 'unknown binding'):
            RelationshipAgent.create(self.source, self.root / 'bad-question', request(), handoff=envelope)

    def discovery_export_from_existing(self):
        return DiscoveryAgent(self.root / 'discovery').export()

    def test_resealed_omission_does_not_override_a_locally_found_blocker(self):
        envelope = self.discovery().export()
        # A digest cannot authenticate completeness. The local reviewer must still
        # inspect source and can introduce a blocker omitted by the producer.
        envelope['payload']['unknowns'] = {}
        envelope['sha256'] = contracts.digest(envelope['payload'])
        relation = RelationshipAgent.create(self.source, self.root / 'relation', request(), handoff=envelope)
        def discovers_blocker(*args):
            result = self.provider(*args)
            result['answer']['unknowns'] = [{'id': 'omitted', 'question': 'Missing registration.',
                'relatedRequirements': ['catalog'], 'blocksRequirements': ['catalog'],
                'scopeReason': 'This omission affects the claimed catalog.'}]
            return result
        self.assertEqual('needs-prerequisites', self.run_agent(relation, discovers_blocker)['status'])
        self.assertEqual([], relation.status()['acceptedRequirements'])

    def test_partial_scope_handoff_does_not_unlock_a_different_scope(self):
        req = request()
        for item in deepcopy(req['goal']['requirements']):
            item['id'] += '-other'
            item['scope'] = 'other'
            item['requires'] = [key + '-other' for key in item['requires']]
            req['goal']['requirements'].append(item)
        first = DiscoveryAgent.create(self.source, self.root / 'discovery', req)
        self.run_agent(first, requirements=['catalog'])
        relation = RelationshipAgent.create(self.source, self.root / 'relation', req, handoff=first.export())
        result = self.run_agent(relation, requirements=['links-other'])
        self.assertEqual('needs-prerequisites', result['status'])
        self.assertEqual(['catalog-other'], result['missingRequirements'])
        self.assertEqual(['catalog'], relation.status()['acceptedRequirements'])

    def followup_provider(self, *, resolve=False):
        def provider(*args):
            result = self.provider(*args)
            context = self.calls[-1]
            if context['task']['operation'] == 'extract' and context['task']['stage'] == 'discovery':
                result['answer']['followups'] = [{'stage': 'relationship',
                    'question': 'Trace the registration entry to its save method.',
                    'paths': ['Registration.cs'], 'requirement': 'links'}]
            if resolve and context['task']['operation'] == 'verify':
                for decision in result['answer']['unknownChecks']:
                    if decision['unknownId'].startswith('followup:') and 'links' in context['task']['requirements']:
                        decision['status'] = 'resolved'
                        decision['reason'] = 'The relationship answers this question in original source.'
            return result
        return provider

    def test_future_followup_is_explicitly_resolved_then_handed_to_behavior(self):
        first = self.discovery(self.followup_provider(resolve=True))
        envelope = first.export()
        self.assertEqual(1, len(envelope['payload']['followups']))
        relation = RelationshipAgent.create(self.source, self.root / 'relation', request(), handoff=envelope)
        self.assertEqual('complete', self.run_agent(relation, self.followup_provider(resolve=True))['status'])
        envelope = relation.export()
        self.assertEqual([], envelope['payload']['followups'])
        self.assertTrue(any(item['followups'] for item in envelope['payload']['audit']))
        self.assertTrue(any(key.startswith('followup:') for key in envelope['payload']['unknowns']))
        not_resolved = BehaviorAgent.create(self.source, self.root / 'non-resolved-behavior', request(), handoff=envelope)
        self.assertEqual('needs-prerequisites', self.run_agent(not_resolved)['status'])
        self.assertEqual([], not_resolved.status()['acceptedRequirements'])
        behavior = BehaviorAgent.create(self.source, self.root / 'behavior', request(), handoff=envelope)
        self.assertEqual('complete', self.run_agent(behavior, self.followup_provider(resolve=True))['status'])

    def test_nonblocking_followup_is_not_silently_closed_by_target_acceptance(self):
        envelope = self.discovery(self.followup_provider()).export()
        relation = RelationshipAgent.create(self.source, self.root / 'relation', request(), handoff=envelope)
        result = self.run_agent(relation)
        self.assertEqual('needs-investigation', result['status'])
        self.assertEqual(['catalog'], relation.status()['acceptedRequirements'])
        with self.assertRaisesRegex(ValueError, 'accepted result'):
            relation.export()
        with patch('contextbase_runtime.provider.run_job', side_effect=self.followup_provider(resolve=True)):
            self.assertEqual('complete', relation.retry(result['pending']['candidate'], inline_sources=True)['status'])
        self.assertEqual([], relation.export()['payload']['followups'])

    def test_receiver_can_explicitly_resolve_an_active_followup_from_source(self):
        envelope = self.discovery(self.followup_provider()).export()
        active = deepcopy(envelope['payload']['followups'])
        relation = RelationshipAgent.create(self.source, self.root / 'relation', request(), handoff=envelope)
        self.assertEqual('complete', self.run_agent(relation, self.followup_provider(resolve=True))['status'])
        envelope = relation.export()
        # An untrusted/older producer may still send an active question with
        # otherwise accepted claims. It grants no authority at the receiver.
        envelope['payload']['followups'] = active
        envelope['sha256'] = contracts.digest(envelope['payload'])
        self.assertEqual(1, len(envelope['payload']['followups']))
        behavior = BehaviorAgent.create(self.source, self.root / 'behavior', request(), handoff=envelope)
        self.assertEqual('complete', self.run_agent(behavior, self.followup_provider(resolve=True))['status'])
        self.assertEqual([], behavior.export()['payload']['followups'])

    def test_final_behavior_cannot_complete_with_an_unresolved_inherited_question(self):
        envelope = self.discovery().export()
        relation = RelationshipAgent.create(self.source, self.root / 'relation', request(), handoff=envelope)
        def future_behavior(*args):
            result = self.provider(*args)
            context = self.calls[-1]
            if context['task']['operation'] == 'extract' and context['task']['stage'] == 'relationship':
                result['answer']['followups'] = [{'stage': 'behavior', 'question': 'Check the rejection condition.',
                    'paths': ['Registration.cs'], 'requirement': 'rules'}]
            return result
        self.assertEqual('complete', self.run_agent(relation, future_behavior)['status'])
        behavior = BehaviorAgent.create(self.source, self.root / 'behavior', request(), handoff=relation.export())
        result = self.run_agent(behavior)
        self.assertEqual('needs-investigation', result['status'])
        self.assertEqual(['catalog', 'links'], behavior.status()['acceptedRequirements'])
        self.assertNotEqual('complete', behavior.status()['status'])
        def resolved(*args):
            response = self.provider(*args)
            for check in response['answer'].get('unknownChecks', []):
                if check['unknownId'].startswith('followup:'):
                    check['status'] = 'resolved'
            return response
        with patch('contextbase_runtime.provider.run_job', side_effect=resolved):
            self.assertEqual('complete', behavior.retry(result['pending']['candidate'], inline_sources=True)['status'])
        self.assertEqual([], behavior.export()['payload']['followups'])

    def test_active_followup_cannot_omit_its_question_binding(self):
        envelope = self.discovery(self.followup_provider()).export()
        envelope['payload']['unknowns'] = {}
        envelope['sha256'] = contracts.digest(envelope['payload'])
        with self.assertRaisesRegex(ValueError, 'bound question'):
            RelationshipAgent.create(self.source, self.root / 'relation', request(), handoff=envelope)

    def test_cli_retry_reinvestigates_rejected_first_draft_with_feedback(self):
        from contextbase_discovery.__main__ import main
        first = DiscoveryAgent.create(self.source, self.root / 'discovery', request())
        def rejects(*args):
            result = self.provider(*args)
            if 'checks' in result['answer']:
                result['answer']['checks'][0]['status'] = 'fail'
            return result
        blocked = self.run_agent(first, rejects)
        self.assertEqual('needs-investigation', blocked['status'])
        candidate = blocked['pending']['candidate']
        count = len(self.calls)
        self.assertEqual('needs-investigation', self.run_agent(first)['status'])
        self.assertEqual(count, len(self.calls))
        with patch('contextbase_runtime.provider.run_job', side_effect=self.provider), redirect_stdout(io.StringIO()) as stream:
            self.assertEqual(0, main(['retry', '--work', str(first.work), '--feedback', candidate,
                                      '--inline-sources']))
        self.assertEqual('complete', json.loads(stream.getvalue())['status'])
        self.assertEqual(candidate, self.calls[-2]['task']['feedback'])
        self.assertIn('feedback', self.calls[-2])
        self.assertEqual(['catalog'], first.status()['acceptedRequirements'])

    def test_rejected_retry_persists_latest_pending_and_reopened_run_does_not_repeat(self):
        agent = DiscoveryAgent.create(self.source, self.root / 'discovery', request())

        def rejects(*args):
            result = self.provider(*args)
            if 'checks' in result['answer']:
                result['answer']['checks'][0]['status'] = 'fail'
            return result

        first = self.run_agent(agent, rejects)
        with patch('contextbase_runtime.provider.run_job', side_effect=rejects):
            retried = agent.retry(first['pending']['candidate'], inline_sources=True)
        self.assertEqual('needs-investigation', retried['status'])
        self.assertEqual(4, len(self.calls))
        self.assertEqual(first['pending']['candidate'], self.calls[-2]['task']['feedback'])
        self.assertNotEqual(first['pending']['candidate'], retried['pending']['candidate'])
        self.assertEqual(retried['actions'][0], {key: retried['pending'][key]
            for key in ('agent', 'requirements', 'candidate', 'verification')})

        reopened = DiscoveryAgent(agent.work)
        state = reopened.status()
        self.assertEqual([], state['acceptedRequirements'])
        self.assertEqual([retried['pending']], list(state['attempts'].values()))
        self.assertEqual(retried['pending']['reason'], state['stopReason'])
        count = len(self.calls)
        stopped = self.run_agent(reopened)
        self.assertEqual('needs-investigation', stopped['status'])
        self.assertEqual(retried['pending'], stopped['pending'])
        self.assertEqual([], stopped['actions'])
        self.assertEqual(count, len(self.calls))

    def test_retry_rejects_unknown_or_accepted_feedback_before_provider(self):
        agent = self.discovery()
        candidate = self.calls[-1]['task']['candidate']
        count = len(self.calls)
        with patch('contextbase_runtime.provider.run_job', side_effect=self.provider):
            with self.assertRaisesRegex(ValueError, 'known candidate'):
                agent.retry('unknown-candidate', inline_sources=True)
            with self.assertRaisesRegex(ValueError, 'Explicitly revise'):
                agent.retry(candidate, inline_sources=True)
        self.assertEqual(count, len(self.calls))


if __name__ == '__main__':
    unittest.main()
