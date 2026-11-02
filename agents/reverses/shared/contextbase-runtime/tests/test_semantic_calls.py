"""Compiler bindings joined to the unchanged, sealed source-fact identities."""
from contextlib import redirect_stdout
from copy import deepcopy
import base64
import hashlib
import io
import json
from pathlib import Path
import tempfile
import unittest
import zipfile

from contextbase_runtime.adapters import index_source
from contextbase_runtime.facts import FactIndex
from contextbase_runtime.sources import SourceAccess
from contextbase_runtime.storage import ArtifactStore
from contextbase_runtime.semantic_calls import SemanticCallIndex


class SemanticCallIndexTests(unittest.TestCase):
    def setUp(self):
        home = Path(__file__).resolve().parents[1] / '.tmp'
        home.mkdir(exist_ok=True)
        self.temporary = tempfile.TemporaryDirectory(prefix='semantic-calls-', dir=home)
        self.root = Path(self.temporary.name)
        self.input = self.root / 'input'
        self.input.mkdir()
        self.write('App.csproj', '<Project Sdk="Microsoft.NET.Sdk"><PropertyGroup>'
                   '<TargetFramework>net10.0</TargetFramework><ImplicitUsings>enable</ImplicitUsings>'
                   '</PropertyGroup><ItemGroup><ProjectReference Include="Core/Core.csproj"/>'
                   '<Compile Remove="Core/**/*.cs;Excluded/**/*.cs"/></ItemGroup></Project>')
        self.write('Core/Core.csproj', '<Project Sdk="Microsoft.NET.Sdk"><PropertyGroup>'
                   '<TargetFramework>net10.0</TargetFramework></PropertyGroup></Project>')
        self.write('Core/Service.cs', 'namespace Core; public interface IService { void Save(int n); }\n'
                   'public sealed class Service : IService { public void Save(int n) {} }\n')
        # BOM, CRLF and a supplementary character precede the exact span joins.
        self.write('App.cs', '\ufeffusing Core;\r\nclass App { const string Label="学生😀";\r\n'
                   ' void Run(IService s) { s.Save(1); Choose(1); Choose("x"); }\r\n'
                   ' void Choose(int n) {} void Choose(string n) {}\r\n'
                   ' void Late(dynamic x) { Choose(x); }\r\n}\r\n')
        self.write('Excluded/Fake.cs', 'class App { void Choose(int n) {} }')
        self.store = ArtifactStore(self.root / 'cache')
        self.sequence = 0

    def tearDown(self):
        self.temporary.cleanup()

    def write(self, relative, text):
        path = self.input / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(text.encode('utf-8'))

    def open(self, **kwargs):
        self.sequence += 1
        source = SourceAccess.create(self.input, self.root / ('snapshot' + str(self.sequence)),
            project_id='semantic-synthetic', allowed_paths=['.'], excluded_paths=[])
        facts = FactIndex.open(source, self.store, parser=index_source)
        return SemanticCallIndex.open(facts, self.store, project='App.csproj', **kwargs)

    def test_cross_project_interface_keeps_declaration_and_implementation_separate(self):
        index = self.open()
        row = index.query(caller='Run', callee='Save')['results'][0]
        self.assertEqual('resolved', row['status'])
        self.assertEqual('interface', row['dispatchKind'])
        self.assertEqual('Core.IService.Save', row['declaredTarget']['qualifiedName'])
        self.assertEqual(['Core.Service.Save'], [s['qualifiedName'] for s in row['implementationCandidates']])
        self.assertTrue(row['declaredTarget']['sourceSymbolIds'])
        self.assertFalse(row['runtimeTargetConfirmed'])
        self.assertEqual('pass', index.validate()['status'])
        self.assertTrue(all(f['data']['resolution'] == 'unresolved'
                            for f in index.facts.by_id.values() if f['kind'] == 'call'))

    def test_overloads_unicode_offsets_and_excluded_files(self):
        index = self.open()
        rows = index.query(caller='Run', callee='Choose')['results']
        self.assertEqual(2, len(rows))
        targets = [row['declaredTarget'] for row in rows]
        self.assertTrue(all(row['status'] == 'resolved' for row in rows))
        self.assertEqual(2, len({tuple(t['sourceSymbolIds']) for t in targets}))
        self.assertTrue(all(t['evidence'][0]['path'] == 'App.cs' for t in targets))
        excluded = index.query(path='Excluded/Fake.cs')
        self.assertEqual([], excluded['results'])
        self.assertNotIn('Excluded/Fake.cs', index.document['projects'][0]['sourcePaths'])

    def test_dynamic_arguments_are_never_resolved_by_method_name(self):
        index = self.open()
        row = index.query(caller='Late', callee='Choose')['results'][0]
        self.assertEqual('dynamic', row['status'])
        self.assertIsNone(row['declaredTarget'])

    def test_constructed_interfaces_select_only_matching_implementation_and_registration(self):
        project = self.input / 'App.csproj'
        self.write('App.csproj', project.read_text().replace('Microsoft.NET.Sdk"', 'Microsoft.NET.Sdk.Web"')
                   .replace('<TargetFramework>', '<OutputType>Library</OutputType><TargetFramework>'))
        self.write('Generic.cs', 'using Microsoft.Extensions.DependencyInjection; '
                   'interface I<T> { void Save(T value); } '
                   'class A:I<int> { public void Save(int value) {} } '
                   'class B:I<string> { public void Save(string value) {} } '
                   'class Setup { void Register(IServiceCollection s) { s.AddScoped<I<int>,A>(); '
                   's.AddScoped<I<string>,B>(); } void UseInt(I<int> s) { s.Save(1); } }')
        index = self.open()
        result = index.query(caller='UseInt', callee='Save')
        target = result['results'][0]
        self.assertEqual('resolved', target['status'])
        self.assertIn('I<int>', target['declaredTarget']['signature'])
        self.assertEqual(['A.Save'], [t['qualifiedName'] for t in target['implementationCandidates']])
        self.assertEqual(1, len(result['registrationObservations']))
        self.assertEqual(['A'], [t['qualifiedName'] for t in
                         result['registrationObservations'][0]['implementationTypes']])

    def test_signature_errors_do_not_become_confirmed_or_block_unrelated_calls(self):
        self.write('Broken.cs', 'class Broken { Missing Bad()=>null; void Good() {} '
                   'void RunBad() { Bad(); Good(); } }')
        index = self.open()
        bad = index.query(caller='RunBad', callee='Bad')['results'][0]
        good = index.query(caller='RunBad', callee='Good')['results'][0]
        self.assertEqual('candidates', bad['status'])
        self.assertEqual('resolved', bad['compilerStatus'])
        self.assertTrue(bad['bindingDiagnostics'])
        self.assertEqual('resolved', good['status'])

    def test_reference_bytes_and_archive_changes_are_rejected_before_query(self):
        from contextbase_runtime.dotnet_host import framework_references
        original = Path(next(p for p in framework_references('net10.0') if Path(p).name == 'System.Runtime.dll'))
        package = self.root / 'packages/example/1.2.3'
        metadata = package / 'ref/net10.0/System.Runtime.dll'
        metadata.parent.mkdir(parents=True)
        metadata.write_bytes(original.read_bytes())
        archive = package / 'example.1.2.3.nupkg'
        with zipfile.ZipFile(archive, 'w') as z:
            z.write(metadata, 'ref/net10.0/System.Runtime.dll')
        lock = {'dependencies': {'net10.0': {'Example': {'resolved': '1.2.3',
            'contentHash': base64.b64encode(hashlib.sha512(archive.read_bytes()).digest()).decode()}}}}
        self.write('packages.lock.json', json.dumps(lock))
        project = self.input / 'App.csproj'
        self.write('App.csproj', project.read_text().replace('</Project>',
            '<ItemGroup><PackageReference Include="Example" Version="1.2.3"/></ItemGroup></Project>'))
        index = self.open(package_roots=[self.root / 'packages'])
        metadata.write_bytes(b'changed metadata')
        with self.assertRaisesRegex(ValueError, 'metadata reference changed'):
            index.query(caller='Run')
        metadata.write_bytes(original.read_bytes())
        with zipfile.ZipFile(archive, 'a') as z:
            z.writestr('change.txt', 'changed archive')
        with self.assertRaisesRegex(ValueError, 'package archive changed'):
            index.query(caller='Run')

    def test_unchanged_snapshot_reuses_same_derived_document(self):
        first = self.open()
        again = SemanticCallIndex.open(first.facts, self.store, project='App.csproj')
        self.assertEqual(first.sha256, again.sha256)
        self.assertTrue(again.cache_hit)

    def test_source_new_file_and_project_changes_do_not_reuse_old_result(self):
        first = self.open()
        first.assert_current_source()
        self.write('New.cs', 'class New { void M() { System.Console.WriteLine("new"); } }')
        with self.assertRaisesRegex(ValueError, 'Current source differs'):
            first.assert_current_source()
        second = self.open()
        self.assertNotEqual(first.sha256, second.sha256)
        self.assertEqual(1, second.query(path='New.cs')['matchedCount'])
        project = self.input / 'App.csproj'
        self.write('App.csproj', project.read_text().replace('Excluded/**/*.cs', 'Excluded/**/*.cs;New.cs'))
        third = self.open()
        self.assertNotEqual(second.sha256, third.sha256)
        self.assertEqual(0, third.query(path='New.cs')['matchedCount'])

    def test_local_function_shadowing_uses_declaration_identity(self):
        self.write('Shadow.cs', 'class Shadow { void Pick(int x) {} void Go() { '
                   'void Pick(string x) {} Pick("local"); } }')
        index = self.open()
        row = index.query(caller='Shadow.Go', callee='Pick')['results'][0]
        self.assertEqual('resolved', row['status'])
        symbol = index.facts.by_id[row['declaredTarget']['sourceSymbolIds'][0]]
        self.assertEqual('local-function', symbol['data']['kind'])

    def test_snapshot_and_cache_tampering_are_rejected(self):
        index = self.open()
        path = next((self.root / 'cache/semantic-calls').glob('*.json'))
        envelope = json.loads(path.read_text(encoding='utf-8'))
        envelope['payload']['results'][0]['status'] = 'invented'
        path.write_text(json.dumps(envelope), encoding='utf-8')
        with self.assertRaisesRegex(ValueError, 'integrity mismatch'):
            SemanticCallIndex.open(index.facts, self.store, project='App.csproj')

    def test_query_limit_and_filters_retain_binding(self):
        index = self.open()
        result = index.query(caller='Run', limit=1)
        self.assertEqual(3, result['matchedCount'])
        self.assertEqual(1, result['returnedCount'])
        self.assertTrue(result['truncated'])
        self.assertEqual(index.sha256, result['indexSha256'])
        second = index.query(caller='Run', limit=1, offset=result['nextOffset'])
        third = index.query(caller='Run', limit=1, offset=second['nextOffset'])
        self.assertIsNone(third['nextOffset'])
        self.assertEqual(3, len({r['callSiteId'] for page in (result, second, third) for r in page['results']}))
        with self.assertRaises(ValueError):
            index.query(limit=0)
        with self.assertRaises(ValueError):
            index.query(path='../outside.cs')
        with self.assertRaises(ValueError):
            index.query(offset=-1)

    def test_all_independent_cli_types_expose_same_source_only_query(self):
        from contextbase_runtime.cli import main
        from contextbase_discovery import DiscoveryAgent
        from contextbase_relationship import RelationshipAgent
        from contextbase_behavior import BehaviorAgent
        index = self.open()
        for agent_type in (DiscoveryAgent, RelationshipAgent, BehaviorAgent):
            output = io.StringIO()
            with redirect_stdout(output):
                code = main(agent_type, ['semantic-calls', '--snapshot', str(index.facts.source.root),
                    '--project', 'App.csproj', '--work', str(self.root / 'cli'), '--caller', 'Run', '--limit', '1'])
            self.assertEqual(0, code, output.getvalue())
            result = json.loads(output.getvalue())
            self.assertEqual(3, result['matchedCount'])
            self.assertEqual(index.facts.sha256, result['sourceFactsSha256'])
        session = self.root / 'protected-session'
        session.mkdir()
        (session / 'session.json').write_text('{}')
        output = io.StringIO()
        with redirect_stdout(output):
            code = main(DiscoveryAgent, ['semantic-calls', '--snapshot', str(index.facts.source.root),
                '--project', 'App.csproj', '--work', str(session)])
        self.assertEqual(1, code)
        self.assertIn('separate from an existing Agent session', output.getvalue())


if __name__ == '__main__':
    unittest.main()
