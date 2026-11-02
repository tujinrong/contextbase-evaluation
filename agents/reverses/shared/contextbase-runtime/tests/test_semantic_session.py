"""Optional semantic input is frozen at ordinary session/profile boundaries."""
import json
import base64
import hashlib
from pathlib import Path
import tempfile
import unittest
import zipfile
from unittest.mock import patch

from contextbase_runtime.config import ProjectProfile
from contextbase_runtime.controller import Session
from contextbase_runtime import contracts
from contextbase_runtime.semantic_support import initialize, initial_requests, initial_pairs, task_extensions


def request():
    return {'schema': contracts.VERSION, 'projectId': 'semantic-profile',
        'goal': {'id': 'inspect', 'question': 'Inspect source.', 'requirements': [
            {'id': 'catalog', 'stage': 'discovery', 'scope': 'source', 'question': 'List catalog.', 'requires': []},
            {'id': 'links', 'stage': 'relationship', 'scope': 'source', 'question': 'Connect catalog.', 'requires': ['catalog']}]},
        'allowedPaths': ['.'], 'excludedPaths': []}


class SemanticSessionTests(unittest.TestCase):
    def setUp(self):
        home = Path(__file__).resolve().parents[1] / '.tmp'
        home.mkdir(exist_ok=True)
        self.temp = tempfile.TemporaryDirectory(prefix='semantic-session-', dir=home)
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.source = self.root / 'source'
        self.source.mkdir()
        (self.source / 'App.csproj').write_text('<Project Sdk="Microsoft.NET.Sdk"><PropertyGroup>'
            '<TargetFramework>net10.0</TargetFramework></PropertyGroup></Project>')
        (self.source / 'App.cs').write_text('class App { void Run() { Save(); } void Save() {} }')
        self.options = {'project': 'App.csproj', 'configuration': 'Release'}

    def create(self, **kwargs):
        return Session.create(self.source, self.root / 'work', request(), **kwargs)

    def write_config(self, extra=''):
        path = self.root / 'contextbase.toml'
        (self.root / 'request.json').write_text(json.dumps(request()))
        path.write_text('schema="contextbase-project/1"\ndefault_profile="csharp"\n'
            '[profiles.csharp]\nsource="source"\nrequest="request.json"\n'
            'work="work"\noutput="results"\ncontext_mode="incremental"\n' + extra)
        return path

    def test_disabled_session_never_starts_semantic_host(self):
        with patch('contextbase_runtime.semantic_calls.SemanticCallIndex.open', side_effect=AssertionError('unexpected .NET')):
            session = self.create(incremental_mode=True)
            self.assertNotIn('semanticOptions', session.config)
            self.assertFalse(session.store.path('semantic-runtime.json').exists())
            self.assertEqual({}, task_extensions(session))

    def test_enabled_session_freezes_derived_index_and_preserves_raw_facts(self):
        session = self.create(incremental_mode=True, semantic_options=self.options)
        raw = session.fact_index()
        original = contracts.digest(raw.document)
        index = initialize(session)
        self.assertIs(index, raw.semantic_index)
        pointer = session.store.get('semantic-runtime.json')
        self.assertEqual(index.sha256, pointer['semanticIndexSha256'])
        self.assertEqual(raw.sha256, pointer['sourceFactsSha256'])
        self.assertEqual(original, contracts.digest(raw.document))
        self.assertTrue(all(f['data']['resolution'] == 'unresolved'
            for f in raw.by_id.values() if f['kind'] == 'call'))
        bound = task_extensions(session)
        self.assertEqual(index.sha256, bound['semanticIndexSha256'])
        reopened = Session.open(self.root / 'work')
        self.assertEqual(index.sha256, initialize(reopened).sha256)

    def test_semantic_full_mode_or_invalid_project_is_rejected_before_work(self):
        with self.assertRaisesRegex(ValueError, 'evidence|incremental'):
            self.create(semantic_options=self.options)
        self.assertFalse((self.root / 'work').exists())
        with self.assertRaises(ValueError):
            self.create(incremental_mode=True, semantic_options={'project': '../Other.csproj'})
        self.assertFalse((self.root / 'work').exists())
        with self.assertRaisesRegex(ValueError, 'configuration'):
            self.create(incremental_mode=True, semantic_options={'project': 'App.csproj', 'configuration': []})
        self.assertFalse((self.root / 'work').exists())

    def test_profile_pins_semantic_settings_and_leaves_disabled_binding_unchanged(self):
        path = self.write_config()
        disabled = ProjectProfile.load(path)
        self.assertIsNone(disabled.semantic_options)
        self.assertNotIn('semanticOptions', disabled.binding('discovery-agent'))
        self.write_config('semantic_project="App.csproj"\nsemantic_configuration="Debug"\n')
        enabled = ProjectProfile.load(path)
        self.assertEqual('Debug', enabled.semantic_options['configuration'])
        self.assertEqual('App.csproj', enabled.semantic_options_for('relationship')['project'])
        self.assertIsNone(enabled.semantic_options_for('behavior'))
        self.assertEqual(disabled.binding('discovery-agent'), enabled.binding('discovery-agent'))
        session = self.create(incremental_mode=True, semantic_options=enabled.semantic_options)
        dummy = type('Agent', (), {'stage': 'discovery', 'name': 'discovery-agent', 'session': session})()
        enabled.bind(dummy)
        self.write_config('semantic_project="App.csproj"\nsemantic_configuration="Release"\n')
        with self.assertRaisesRegex(ValueError, 'profile|semantic|Project'):
            ProjectProfile.load(path).validate_workspace(dummy)

    def test_changed_sealed_source_cannot_reopen_old_binding(self):
        session = self.create(incremental_mode=True, semantic_options=self.options)
        path = session.source.root / 'sources/App.cs'
        path.write_text(path.read_text() + '\nclass Added {}')
        with self.assertRaises(ValueError):
            Session.open(self.root / 'work')

    def test_missing_runtime_pointer_is_not_silently_recreated(self):
        session = self.create(incremental_mode=True, semantic_options=self.options)
        session.store.path('semantic-runtime.json').unlink()
        with self.assertRaisesRegex(ValueError, 'binding is missing'):
            Session.open(self.root / 'work')

    def test_changed_metadata_is_rejected_before_issuing_task_binding(self):
        from contextbase_runtime.dotnet_host import framework_references
        reference = Path(next(p for p in framework_references('net10.0') if Path(p).name == 'System.Runtime.dll'))
        package = self.root / '.nuget/packages/example/1.2.3'
        metadata = package / 'ref/net10.0/System.Runtime.dll'
        metadata.parent.mkdir(parents=True)
        metadata.write_bytes(reference.read_bytes())
        archive = package / 'example.1.2.3.nupkg'
        with zipfile.ZipFile(archive, 'w') as z:
            z.write(metadata, 'ref/net10.0/System.Runtime.dll')
        lock = {'dependencies': {'net10.0': {'Example': {'resolved': '1.2.3',
            'contentHash': base64.b64encode(hashlib.sha512(archive.read_bytes()).digest()).decode()}}}}
        (self.source / 'packages.lock.json').write_text(json.dumps(lock))
        project = self.source / 'App.csproj'
        project.write_text(project.read_text().replace('</Project>',
            '<ItemGroup><PackageReference Include="Example" Version="1.2.3"/></ItemGroup></Project>'))
        # Locate the fixture's local package cache; all metadata bytes and
        # compiler analysis remain real, with no generated target assembly.
        with patch('contextbase_runtime.semantic_project.Path.home', return_value=self.root):
            session = self.create(incremental_mode=True, semantic_options=self.options)
        metadata.write_bytes(b'changed metadata')
        with self.assertRaisesRegex(ValueError, 'metadata reference changed'):
            task_extensions(session)

    def test_bootstrap_queries_are_bounded_to_acquired_unit_paths(self):
        session = self.create(incremental_mode=True, semantic_options=self.options)
        raw = session.fact_index()
        task = {'id': 'child', **task_extensions(session)}
        requests = initial_requests(raw, task, {'paths': ['App.cs', '../outside.cs', 'Missing.cs']})
        self.assertEqual(1, len(requests))
        self.assertEqual('query', requests[0]['operation'])
        self.assertEqual('App.cs', requests[0]['path'])
        self.assertEqual('call', requests[0]['kind'])
        self.assertEqual(1, requests[0]['limit'])
        self.assertEqual('Save', requests[0]['callee'])
        self.assertLessEqual(len(requests), 2)

    def test_changed_helper_identity_rejects_query_and_new_task_binding(self):
        session = self.create(incremental_mode=True, semantic_options=self.options)
        index = initialize(session)
        from contextbase_runtime.dotnet_host import semantic_host_fingerprint
        changed = semantic_host_fingerprint()
        changed['helperSha256'] = '0' * 64
        with patch('contextbase_runtime.dotnet_host.semantic_host_fingerprint', return_value=changed):
            with self.assertRaisesRegex(ValueError, 'binding changed'):
                index.query(caller='Run')
            with self.assertRaisesRegex(ValueError, 'binding changed'):
                task_extensions(session)

    def test_initial_pairs_skip_oversized_call_and_do_not_pad_framework_calls(self):
        from contextbase_runtime.evidence import EvidenceAccess
        (self.source / 'App.cs').write_text('class App {\n void Large() { Save("' + 'x' * 12000 + '"); }\n'
            'void Small() { Save("small"); }\n void Save(string value) {}\n'
            'void PlatformOnly() { System.Console.WriteLine("framework"); }\n}')
        session = self.create(incremental_mode=True, semantic_options=self.options)
        raw = session.fact_index()
        task = {'id': 'child', 'contextId': 'child-context', **task_extensions(session)}
        access = EvidenceAccess(session.source, raw, task)
        requests = initial_requests(raw, task, {'paths': ['App.cs']})
        self.assertEqual(2, len(requests))
        self.assertTrue(all(r['callee'] == 'Save' and r['limit'] == 1 for r in requests))
        oversized = [access.handle(r) for r in requests]
        self.assertTrue(any(len(json.dumps({'request': r, 'reply': reply}, ensure_ascii=False,
            sort_keys=True, separators=(',', ':'))) > 8000 for r, reply in zip(requests, oversized)))
        pairs = initial_pairs(access, raw, task, {'paths': ['App.cs']})
        self.assertEqual(1, len(pairs))
        self.assertLessEqual(len(json.dumps(pairs, ensure_ascii=False, sort_keys=True, separators=(',', ':'))), 8000)
        selected = pairs[0]['reply']['result']['facts'][0]
        self.assertEqual('Save("small")', selected['data']['text'])

    def test_initial_query_offset_selects_source_call_after_metadata_namesake(self):
        from contextbase_runtime.evidence import EvidenceAccess
        (self.source / 'App.cs').write_text('class Sink { public void Add(string value) {} } '
            'class App { void Run(Sink sink) { new System.Collections.Generic.List<string>().Add("framework"); '
            'sink.Add("source"); } }')
        session = self.create(incremental_mode=True, semantic_options=self.options)
        raw = session.fact_index()
        task = {'id': 'child', 'contextId': 'child-context', **task_extensions(session)}
        requests = initial_requests(raw, task, {'paths': ['App.cs']})
        self.assertEqual(1, len(requests))
        self.assertEqual('Add', requests[0]['callee'])
        self.assertEqual(1, requests[0]['offset'])
        access = EvidenceAccess(session.source, raw, task)
        pairs = initial_pairs(access, raw, task, {'paths': ['App.cs']})
        self.assertEqual(1, len(pairs))
        self.assertEqual('sink.Add("source")', pairs[0]['reply']['result']['facts'][0]['data']['text'])


if __name__ == '__main__':
    unittest.main()
