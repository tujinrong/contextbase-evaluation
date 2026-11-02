"""Source-reviewed declaration targets for the Native student-delete example.

This is an eighteen-call acceptance sample, not whole-program accuracy or a
runtime/SQL test. Expected raw declaration IDs were reviewed independently of
Roslyn. No target is built, emitted, loaded or executed.
"""
from collections import Counter
from pathlib import Path
import tempfile
import unittest

from contextbase_runtime.facts import FactIndex
from contextbase_runtime.semantic_calls import SemanticCallIndex
from contextbase_runtime.sources import SourceAccess
from contextbase_runtime.storage import ArtifactStore


# Call-site IDs include the source file hash and exact syntax span; declaration
# IDs include path, lexical identity, kind and complete syntactic signature.
EXPECTED = [
    ('b86f41a5550d89c1b3c31f0ffa6f4d19a2e00f10611d83450a500889aee69a82', 'f438a78d794f8c4b984811b7b1b99eda4ca868429196e42aed5df63a3d7305ca'),
    ('a8c3846ece936a1895edc6c6aceb595c8bb7688a6567c6776129a97747218bad', 'b55075d17e9cc7e159d612f4979c8224837b25219e4cc986efbb9de1ed2cb0c7'),
    ('6f77b1a6b18743b0ddba7fa400be1050388725d6311469757ea1fbab3a90d9ba', 'e206cc26829c05a62a9b14d9cb8904660f1ce9ce75606db1dfb6ccd334cc1bb4'),
    ('fb600b048d222d4947288674c87333a27dde4dd02afffcfe5226c6c5fecc2f9e', '10cc878fcbf910c793707e7b62e768cd95e97975e4f842b4c3696c220d6de840'),
    ('64c973c542c52ca84cb7fed9b86fd0fba230ea6b77162bb316a8561a1ad34808', '0b6e7e47b8b6db4d151e7c76b398e3f7434a1562b0ae24b6d847f550234d8e70'),
    ('7f8dc69354c1d30b222d6c8f75654bda32e522a2c213c75a14e0b101dc96068c', 'f5ecd7db9981da0c4d9af3cb10cc80b5133e97fe28ed022b6fe39f5dd71b1839'),
    ('cbed799f52ecdf98e7ad468bf2b84794e923cb2429cf2a28a4b2f301836e3939', '4e01704bc118c7a2dbdfbde1095575bbf1ae16263c46280fcb3792e7cabf51a0'),
    ('b3313657815ab6b99bdbe0e163979b99284247fd2da085b5dc2d077d2a0714ce', '32a4b44e7975eb81439deeec31f73696428edba986802af665852e133defd6fa'),
    ('50cfef3f12ceb1a104453017b4ad55f9da26b51f7e147871122766b1a79dd382', 'dc804f57698398a3b51181bb61afb9122e345cedaef22f63ede0421ad58917e5'),
    ('75d9ab670329da520303cadcba5f72dd606f4abe7e53fd5045e4f8df572b8020', '14af2a48d69cf34821fcb51b21bb71363d4e7abc713ef0eb6f1d691858d2370a'),
]


class StudentSemanticChainTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        home = Path(__file__).resolve().parents[1] / '.tmp'
        home.mkdir(exist_ok=True)
        cls.temp = tempfile.TemporaryDirectory(prefix='student-semantic-', dir=home)
        cls.root = Path(cls.temp.name)
        source = Path(__file__).resolve().parents[5] / 'sample-project1/srcs/CSharp_ASPNET'
        if not source.is_dir():
            raise unittest.SkipTest('Repository student example is required for real-chain acceptance')
        cls.source = SourceAccess.create(source, cls.root / 'snapshot', project_id='student-semantic-acceptance',
                                        allowed_paths=['.'], excluded_paths=['.tmp'])
        cls.store = ArtifactStore(cls.root / 'cache')
        cls.facts = FactIndex.open(cls.source, cls.store)
        cls.index = SemanticCallIndex.open(cls.facts, cls.store, project='StudentManagement.Web.csproj')

    @classmethod
    def tearDownClass(cls):
        cls.temp.cleanup()

    def test_eighteen_reviewed_calls_have_exact_source_declarations(self):
        expected = [('call:' + call, 'symbol:' + symbol) for call, symbol in EXPECTED]
        # The remaining eight call sites include two separate rollback branches.
        targets = {
            'User': '3f6b2cc4a841bfd67e368458be0535ce7d4cafe3891218ad1cfbe04f980e9465',
            'Text': '4cae5ae003daa404df49dc8a685af664fbfbcbf49c94bc529f36bfdf5c6686a6',
            'Open': '08203dde79030f68407a160db6a9a4c7b35189c77a8515bfa11656d977fb5c71',
            'Gate': '81ebf995d4a12dc4f1a6c313bdefdaa3ed6dedff1fdd3649b41e9013f28db914',
            'Audit': 'e1441dc2683009383def56bf0a1779b8c57980e74c222a2c22c12fc22f6c1d4c',
            'Rollback': 'ee2c968654dca6c77728f01a1884b16887d916f3b70dd71e7de89e2b669bedb9',
        }
        core = self.facts.query(caller='StudentManagement.Core.SqlServerStudentService.DeleteAsync', kind='call')['facts']
        selected = [r for r in core if r['data']['name'] in targets]
        self.assertEqual(Counter({'User': 1, 'Text': 1, 'Open': 1, 'Gate': 1, 'Audit': 1, 'Rollback': 2}),
                         Counter(r['data']['name'] for r in selected))
        expected += [(r['id'], 'symbol:' + targets[r['data']['name']]) for r in selected]
        command = self.facts.query(caller='StudentManagement.Core.SqlServerStudentService.Audit',
                                   kind='call', callee='Command')['facts']
        self.assertEqual(1, len(command))
        expected.append((command[0]['id'], 'symbol:0ca48295ad61b70c2b5badc825240819a79396c03c0f8c76b3fb488b5087b6d9'))
        self.assertEqual(18, len(expected))
        actual = {r['callSiteId']: r for r in self.index.document['results']}
        for call_id, symbol_id in expected:
            with self.subTest(call=call_id):
                row = actual[call_id]
                target = self.index.document['symbols'][row['declaredTargetKey']]
                self.assertEqual('resolved', row['status'])
                self.assertEqual([symbol_id], target['sourceSymbolIds'])
                raw = self.facts.by_id[symbol_id]
                self.assertEqual(raw['data']['evidence'], target['evidence'])
                self.assertEqual([(raw['path'], raw['data']['startByte'], raw['data']['endByte'])],
                    [(d['path'], d['startByte'], d['endByte']) for d in target['declarations']])

    def test_interface_dispatch_keeps_conditional_registration_evidence(self):
        result = self.index.query(caller='StudentManagement.Web.WebStudentCoordinator.Delete', callee='DeleteAsync')
        call = result['results'][0]
        self.assertEqual('interface', call['dispatchKind'])
        self.assertEqual('StudentManagement.Core.IStudentService.DeleteAsync', call['declaredTarget']['qualifiedName'])
        self.assertEqual(['StudentManagement.Core.SqlServerStudentService.DeleteAsync'],
                         [t['qualifiedName'] for t in call['implementationCandidates']])
        registrations = result['registrationObservations']
        self.assertEqual(1, len(registrations))
        self.assertEqual('Infrastructure/WebHostSetup.cs', registrations[0]['evidence'][0]['path'])
        self.assertTrue(registrations[0]['factory'])
        self.assertTrue(registrations[0]['conditional'])
        self.assertFalse(registrations[0]['runtimeTargetConfirmed'])
        self.assertEqual(['StudentManagement.Core.SqlServerStudentService'],
                         [t['qualifiedName'] for t in registrations[0]['implementationTypes']])

    def test_compilation_context_matches_two_projects_and_has_no_errors(self):
        self.assertEqual([7, 21], sorted(len(p['sourcePaths']) for p in self.index.document['projects']))
        for project in self.index.document['projects']:
            self.assertTrue(project['configurationComplete'])
            self.assertEqual([], [d for d in project['compilerDiagnostics'] if d['severity'] == 'error'])


if __name__ == '__main__':
    unittest.main()
