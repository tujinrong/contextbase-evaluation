"""Normal evidence queries deliver compiler bindings without source-read grants."""
from copy import deepcopy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from contextbase_runtime import contracts, evidence_dialog
from contextbase_runtime.adapters import index_source
from contextbase_runtime.evidence import EvidenceAccess, MAX_REPLY_CHARS
from contextbase_runtime.facts import FactIndex
from contextbase_runtime.semantic_calls import SemanticCallIndex
from contextbase_runtime.sources import SourceAccess
from contextbase_runtime.storage import ArtifactStore


POLICY = 'contextbase-semantic-evidence/1'


def query(**changes):
    return {'operation': 'query', 'offset': 0, 'limit': 20, 'path': None,
            'kind': 'call', 'text': None, 'caller': 'Go', 'callee': None, 'route': None, **changes}


class SemanticEvidenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        home = Path(__file__).resolve().parents[1] / '.tmp'
        home.mkdir(exist_ok=True)
        cls.temporary = tempfile.TemporaryDirectory(prefix='semantic-evidence-', dir=home)
        cls.root = Path(cls.temporary.name)
        original = cls.root / 'input'
        original.mkdir()
        (original / 'App.csproj').write_text('<Project Sdk="Microsoft.NET.Sdk"><PropertyGroup>'
            '<TargetFramework>net10.0</TargetFramework></PropertyGroup></Project>')
        (original / 'A.cs').write_text('class A {\n static void Main() { new A().Go(); }\n'
            ' void Go() { Write(); Write(); Other(); }\n'
            ' void Write() {}\n void Other() {}\n}\n')
        cls.source = SourceAccess.create(original, cls.root / 'snapshot', project_id='semantic-evidence',
                                        allowed_paths=['.'], excluded_paths=[])
        cls.store = ArtifactStore(cls.root / 'cache')
        cls.index = FactIndex.open(cls.source, cls.store, parser=index_source)
        cls.semantic = SemanticCallIndex.open(cls.index, cls.store, project='App.csproj')
        cls.index.semantic_index = cls.semantic

    @classmethod
    def tearDownClass(cls):
        cls.temporary.cleanup()

    def setUp(self):
        self.task = {'id': self.id(), 'contextId': 'author', 'snapshotId': self.source.snapshot_id,
            'sourceFactsSha256': self.index.sha256, 'evidenceIndexSha256': self.index.sha256,
            'semanticPolicy': POLICY, 'semanticIndexSha256': self.semantic.sha256}
        self.access = EvidenceAccess(self.source, self.index, self.task)

    def test_query_delivers_exact_bindings_and_canonical_declarations(self):
        request = query(callee='Write', limit=1)
        reply = self.access.handle(request)
        self.access.verify_reply(request, reply)
        result = reply['result']
        self.assertEqual(self.semantic.sha256, reply['semanticIndexSha256'])
        self.assertEqual(self.index.query(callee='Write', kind='call')['facts'][:1], result['facts'])
        self.assertEqual('unresolved', result['facts'][0]['data']['resolution'])
        binding = result['semanticBindings'][0]
        self.assertEqual('resolved', binding['status'])
        self.assertEqual('A.Write', binding['declaredTarget']['qualifiedName'])
        self.assertFalse({'key', 'definitionKey', 'containingTypeKey'} & set(binding['declaredTarget']))
        self.assertFalse(binding['runtimeTargetConfirmed'])
        self.assertEqual(result['facts'][0]['id'], binding['callSiteId'])
        self.assertEqual([self.index.by_id[key] for key in binding['declaredTarget']['sourceSymbolIds']],
                         result['declarationFacts'])
        self.assertNotIn('sourceText', json.dumps(result))

    def test_pages_bind_only_returned_calls_and_are_replayable(self):
        request = query(limit=1)
        one = self.access.handle(request)
        ceiling = self.access._size(one) + 100
        ids = []
        request = query(limit=100)
        with patch('contextbase_runtime.evidence.MAX_REPLY_CHARS', ceiling):
            while True:
                reply = self.access.handle(request)
                self.assertEqual('ok', reply['status'])
                self.assertLessEqual(self.access._size(reply), ceiling)
                result = reply['result']
                self.assertEqual({r['id'] for r in result['facts']},
                                 {r['callSiteId'] for r in result['semanticBindings']})
                ids.extend(r['id'] for r in result['facts'])
                self.access.verify_reply(request, reply)
                if not result['truncated']:
                    break
                self.assertGreater(result['nextOffset'], request['offset'])
                request = {**request, 'offset': result['nextOffset']}
        self.assertEqual(3, len(ids))
        self.assertEqual(3, len(set(ids)))

    def test_missing_or_changed_semantic_binding_rejects_before_delivery(self):
        with self.assertRaisesRegex(ValueError, 'semantic'):
            EvidenceAccess(self.source, self.index, {**self.task, 'semanticIndexSha256': '0' * 64})
        raw = FactIndex(self.index.document, self.source)
        with self.assertRaisesRegex(ValueError, 'semantic'):
            EvidenceAccess(self.source, raw, self.task)
        with self.assertRaisesRegex(ValueError, 'semantic'):
            EvidenceAccess(self.source, self.index, {**self.task, 'semanticPolicy': 'unsupported'})
        with self.assertRaisesRegex(ValueError, 'semantic'):
            EvidenceAccess(self.source, self.index, {k: v for k, v in self.task.items() if k != 'semanticPolicy'})

    def test_legacy_query_neither_requires_nor_delivers_semantic_capability(self):
        task = {k: v for k, v in self.task.items() if not k.startswith('semantic')}
        raw = FactIndex(self.index.document, self.source)
        legacy = EvidenceAccess(self.source, raw, task).handle(query())
        self.assertNotIn('semanticIndexSha256', legacy)
        self.assertNotIn('semanticBindings', legacy['result'])
        self.assertNotIn('declarationFacts', legacy['result'])
        attached = EvidenceAccess(self.source, self.index, task).handle(query())
        self.assertEqual(legacy, attached)

    def test_declarations_grant_only_fact_references_not_original_text(self):
        request = query(callee='Write', limit=1)
        pair = {'request': request, 'reply': self.access.handle(request)}
        symbol = pair['reply']['result']['declarationFacts'][0]
        answer = {'factUsage': [{'factIds': [symbol['id']]}]}
        evidence_dialog.validate_delivery(self.source, answer, [pair])
        with self.assertRaisesRegex(ValueError, 'original text'):
            evidence_dialog.validate_delivery(self.source, {**answer, 'evidence': symbol['data']['evidence']}, [pair])
        verifier = EvidenceAccess(self.source, self.index, {**self.task, 'id': 'verifier', 'contextId': 'independent'})
        with self.assertRaisesRegex(ValueError, 'replay'):
            verifier.verify_reply(request, pair['reply'])

    def dialog(self, name, provider):
        task = {**self.task, 'id': name, 'evidencePolicy': evidence_dialog.VERSION,
                'evidenceWindowPolicy': deepcopy(evidence_dialog.WINDOW_POLICY)}
        schema = contracts.obj({'factUsage': contracts.arr(contracts.obj({'factIds': contracts.STRINGS}))})
        return evidence_dialog.run(self.source, self.index, ArtifactStore(self.root / name), task,
            {'task': task}, 'Check bindings.', schema, provider, 30)

    def test_dialog_retains_bindings_and_authorizes_delivered_declaration_facts(self):
        rounds = []
        declared = []
        def provider(source, output, prompt, schema, timeout):
            context = json.loads(prompt.split(evidence_dialog.POLICY + '\n', 1)[1])
            rounds.append(context)
            number = len(rounds)
            if number == 1:
                action, requests, answer = 'requests', [query(callee='Write', limit=1)], None
            elif number == 2:
                latest = context['evidenceDialog']['latestEvidence'][0]['reply']['result']
                declared.extend(f['id'] for f in latest['declarationFacts'])
                action, requests, answer = 'requests', [{'operation': 'read', 'path': 'A.cs', 'startLine': 1, 'endLine': 1}], None
            else:
                retained = context['evidenceDialog']['retainedEvidence']
                bindings = [m['binding'] for m in retained if m['kind'] == 'semantic']
                self.assertTrue(bindings)
                self.assertEqual(len(bindings), len({(m['projectId'], m['callSiteId']) for m in bindings}))
                self.assertTrue(set(declared).issubset({m['fact']['id'] for m in retained if m['kind'] == 'fact'}))
                action, requests, answer = 'finish', [], {'factUsage': [{'factIds': declared}]}
            return {'exit_code': 0, 'metadata': {'status': 'passed'}, 'answer': {
                'protocol': evidence_dialog.VERSION, 'taskId': context['task']['id'],
                'action': action, 'requests': requests, 'answer': answer, 'workingNotes': ''}}
        result = self.dialog('retain', provider)
        self.assertEqual(declared, result['answer']['factUsage'][0]['factIds'])

    def test_duplicate_semantic_queries_are_not_new_progress(self):
        calls = []
        def provider(source, output, prompt, schema, timeout):
            context = json.loads(prompt.split(evidence_dialog.POLICY + '\n', 1)[1])
            calls.append(context)
            if len(calls) > 1:
                visible = context['evidenceDialog']['evidenceWindow']['visibleMaterials']
                bindings = [m for m in visible if m['kind'] == 'semantic']
                self.assertTrue(bindings)
                self.assertEqual(len(bindings), len({(m['projectId'], m['callSiteId']) for m in bindings}))
            return {'exit_code': 0, 'metadata': {'status': 'passed'}, 'answer': {
                'protocol': evidence_dialog.VERSION, 'taskId': context['task']['id'],
                'action': 'requests', 'requests': [query(callee='Write', limit=1)],
                'answer': None, 'workingNotes': ''}}
        with self.assertRaisesRegex(ValueError, 'without progress'):
            self.dialog('repeat', provider)
        self.assertEqual(3, len(calls))

    def test_dialog_supplies_initial_bindings_without_a_model_query(self):
        calls = []
        def provider(source, output, prompt, schema, timeout):
            context = json.loads(prompt.split(evidence_dialog.POLICY + '\n', 1)[1])
            calls.append(context)
            initial = context['evidenceDialog']['latestEvidence']
            self.assertTrue(initial)
            self.assertTrue(context['evidenceDialog']['deliveryLedger'])
            declarations = [f['id'] for pair in initial for f in pair['reply']['result']['declarationFacts']]
            self.assertTrue(declarations)
            return {'exit_code': 0, 'metadata': {'status': 'passed'}, 'answer': {
                'protocol': evidence_dialog.VERSION, 'taskId': context['task']['id'],
                'action': 'finish', 'requests': [], 'answer': {'factUsage': [{'factIds': declarations}]},
                'workingNotes': ''}}
        self.dialog('initial', provider)
        self.assertEqual(1, len(calls))

    def test_conditional_registration_is_delivered_retained_and_fact_bound(self):
        with tempfile.TemporaryDirectory(prefix='di-', dir=self.root) as directory:
            root = Path(directory)
            original = root / 'input'
            original.mkdir()
            (original / 'App.csproj').write_text('<Project Sdk="Microsoft.NET.Sdk.Web"><PropertyGroup>'
                '<TargetFramework>net10.0</TargetFramework><OutputType>Library</OutputType>'
                '</PropertyGroup></Project>')
            (original / 'A.cs').write_text('using Microsoft.Extensions.DependencyInjection;\n'
                'interface IFoo { void Save(); } class Foo:IFoo { public void Save() {} }\n'
                'class Setup { void Register(IServiceCollection services) { services.AddScoped<IFoo>(sp=>new Foo()); }\n'
                'void Use(IFoo service) { service.Save(); } }\n')
            source = SourceAccess.create(original, root / 'snapshot', project_id='semantic-di',
                                         allowed_paths=['.'], excluded_paths=[])
            store = ArtifactStore(root / 'cache')
            index = FactIndex.open(source, store, parser=index_source)
            semantic = SemanticCallIndex.open(index, store, project='App.csproj')
            index.semantic_index = semantic
            task = {**self.task, 'id': 'di-task', 'snapshotId': source.snapshot_id,
                'sourceFactsSha256': index.sha256, 'evidenceIndexSha256': index.sha256,
                'semanticIndexSha256': semantic.sha256, 'evidencePolicy': evidence_dialog.VERSION,
                'evidenceWindowPolicy': deepcopy(evidence_dialog.WINDOW_POLICY)}
            access = EvidenceAccess(source, index, task)
            request = query(caller='Use', callee='Save')
            reply = access.handle(request)
            access.verify_reply(request, reply)
            registrations = reply['result']['registrationObservations']
            self.assertEqual(1, len(registrations))
            registration = registrations[0]
            self.assertTrue(registration['conditional'])
            self.assertFalse(registration['runtimeTargetConfirmed'])
            self.assertEqual('IFoo', registration['serviceType']['qualifiedName'])
            self.assertEqual(['Foo'], [t['qualifiedName'] for t in registration['implementationTypes']])
            canonical = reply['result']['registrationFacts']
            self.assertEqual([index.by_id[registration['callSiteId']]], canonical)
            self.assertEqual('call', canonical[0]['kind'])
            rounds = []
            def provider(source, output, prompt, schema, timeout):
                context = json.loads(prompt.split(evidence_dialog.POLICY + '\n', 1)[1])
                rounds.append(context)
                if len(rounds) == 1:
                    initial = context['evidenceDialog']['latestEvidence']
                    self.assertTrue(any(p['reply']['result']['registrationObservations'] for p in initial))
                    action, requests, answer = 'requests', [{'operation': 'read', 'path': 'A.cs', 'startLine': 1, 'endLine': 1}], None
                else:
                    retained = context['evidenceDialog']['retainedEvidence']
                    self.assertEqual(1, len([m for m in retained if m['kind'] == 'registration']))
                    action, requests, answer = 'finish', [], {'factUsage': [{'factIds': [canonical[0]['id']]}]}
                return {'exit_code': 0, 'metadata': {'status': 'passed'}, 'answer': {
                    'protocol': evidence_dialog.VERSION, 'taskId': task['id'],
                    'action': action, 'requests': requests, 'answer': answer, 'workingNotes': ''}}
            schema = contracts.obj({'factUsage': contracts.arr(contracts.obj({'factIds': contracts.STRINGS}))})
            evidence_dialog.run(source, index, store, task, {'task': task}, 'Check DI.', schema, provider, 30)

    def test_large_candidate_set_cannot_expand_automatic_initial_delivery(self):
        with tempfile.TemporaryDirectory(prefix='budget-', dir=self.root) as directory:
            root = Path(directory)
            original = root / 'input'
            original.mkdir()
            (original / 'App.csproj').write_text('<Project Sdk="Microsoft.NET.Sdk"><PropertyGroup>'
                '<TargetFramework>net10.0</TargetFramework></PropertyGroup></Project>')
            types = '\n'.join(f'class C{n} {{}}' for n in range(24))
            overloads = '\n'.join(f' static void Many(C{n} x) {{}}' for n in range(24))
            (original / 'A.cs').write_text(types + '\nclass A {\n'
                ' static void Main() { Many(default); Small(); }\n'
                ' static void Extra() { Small(); }\n static void Small() {}\n' + overloads + '\n}\n')
            source = SourceAccess.create(original, root / 'snapshot', project_id='semantic-budget',
                                         allowed_paths=['.'], excluded_paths=[])
            store = ArtifactStore(root / 'cache')
            index = FactIndex.open(source, store, parser=index_source)
            semantic = SemanticCallIndex.open(index, store, project='App.csproj')
            index.semantic_index = semantic
            task = {**self.task, 'id': 'budget-task', 'snapshotId': source.snapshot_id,
                'sourceFactsSha256': index.sha256, 'evidenceIndexSha256': index.sha256,
                'semanticIndexSha256': semantic.sha256, 'evidencePolicy': evidence_dialog.VERSION,
                'evidenceWindowPolicy': deepcopy(evidence_dialog.WINDOW_POLICY)}
            access = EvidenceAccess(source, index, task)
            large = access.handle(query(caller='Main', callee='Many'))
            self.assertEqual('ok', large['status'])
            self.assertEqual(24, len(large['result']['semanticBindings'][0]['candidates']))
            self.assertGreater(len(json.dumps(large, ensure_ascii=False, separators=(',', ':'))), 8000)
            def provider(source, output, prompt, schema, timeout):
                context = json.loads(prompt.split(evidence_dialog.POLICY + '\n', 1)[1])
                initial = context['evidenceDialog']['latestEvidence']
                self.assertLessEqual(len(json.dumps(initial, ensure_ascii=False, sort_keys=True, separators=(',', ':'))), 8000)
                groups = {(row['projectId'], row['callerId']) for pair in initial
                          for row in pair['reply']['result']['semanticBindings']}
                self.assertLessEqual(len(groups), 2)
                return {'exit_code': 0, 'metadata': {'status': 'passed'}, 'answer': {
                    'protocol': evidence_dialog.VERSION, 'taskId': task['id'],
                    'action': 'finish', 'requests': [], 'answer': {'factUsage': []}, 'workingNotes': ''}}
            schema = contracts.obj({'factUsage': contracts.arr(contracts.obj({'factIds': contracts.STRINGS}))})
            evidence_dialog.run(source, index, store, task, {'task': task}, 'Check packet budget.', schema, provider, 30)


if __name__ == '__main__':
    unittest.main()
