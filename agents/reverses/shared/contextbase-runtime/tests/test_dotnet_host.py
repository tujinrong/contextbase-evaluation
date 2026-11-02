"""Compiler front-end contract: input assemblies are never emitted or executed."""
import unittest
import base64
import hashlib
from pathlib import Path
import tempfile
import zipfile

from contextbase_runtime.dotnet_host import framework_references, package_content_hashes, run_semantic_host


class SemanticHostTests(unittest.TestCase):
    def test_unsigned_package_hash_tracks_changed_archive_without_loading_code(self):
        with tempfile.TemporaryDirectory() as directory:
            package = Path(directory) / 'fixture.nupkg'
            for value in ['first', 'changed']:
                with zipfile.ZipFile(package, 'w') as archive:
                    archive.writestr('data.txt', value)
                expected = base64.b64encode(hashlib.sha512(package.read_bytes()).digest()).decode()
                self.assertEqual(package_content_hashes([package])[str(package.resolve())], expected)

    def _project(self, text):
        return {'id': 'Example', 'files': [{'path': 'Example.cs', 'text': text}],
                'references': framework_references('net10.0'), 'projectReferences': [],
                'languageVersion': '14', 'defines': [], 'nullable': 'enable',
                'globalUsings': [], 'configurationComplete': True}

    def test_cross_project_overload_has_exact_declared_target(self):
        core = {'id': 'Core', 'files': [{'path': 'Core.cs', 'text':
            'public class Service { public int Pick(int x)=>x; public string Pick(string x)=>x; }'}],
            'references': framework_references('net10.0'), 'projectReferences': [],
            'languageVersion': '14', 'defines': [], 'nullable': 'enable',
            'globalUsings': [], 'configurationComplete': True}
        web = {**core, 'id': 'Web', 'projectReferences': ['Core'], 'files': [
            {'path': 'Web.cs', 'text': 'class Web { int Go(Service s)=>s.Pick(1); }'}]}
        result = run_semantic_host({'projects': [core, web], 'rootProject': 'Web'})
        project = next(p for p in result['projects'] if p['id'] == 'Web')
        call = project['calls'][0]
        self.assertEqual(call['compilerStatus'], 'resolved')
        self.assertEqual(call['declaredTarget']['qualifiedName'], 'Service.Pick')
        self.assertIn('int', call['declaredTarget']['signature'])
        self.assertEqual(call['declaredTarget']['declarations'][0]['path'], 'Core.cs')
        self.assertEqual(call['bindingDiagnostics'], [])

    def test_interface_target_and_implementation_are_separate_unicode_locations(self):
        text = ('// 日本語 😀\r\ninterface IService { void Save(); }\r\n'
                'class Store : IService { public void Save() {} }\r\n'
                'class Caller { void Go(IService service) { service.Save(); } }')
        result = run_semantic_host({'projects': [self._project(text)], 'rootProject': 'Example'})
        call = result['projects'][0]['calls'][0]
        self.assertEqual(call['compilerStatus'], 'resolved')
        self.assertEqual(call['dispatchKind'], 'interface')
        self.assertEqual(call['declaredTarget']['qualifiedName'], 'IService.Save')
        self.assertEqual([t['qualifiedName'] for t in call['implementationCandidates']], ['Store.Save'])
        self.assertEqual(text.encode()[call['startByte']:call['endByte']], b'service.Save()')
        declaration = call['declaredTarget']['declarations'][0]
        self.assertEqual(text.encode()[declaration['startByte']:declaration['endByte']], b'void Save();')

    def test_dynamic_argument_is_not_a_static_target(self):
        text = 'class C { void Pick(int x) {} void Go(dynamic value) { Pick(value); } }'
        result = run_semantic_host({'projects': [self._project(text)], 'rootProject': 'Example'})
        call = result['projects'][0]['calls'][0]
        self.assertEqual(call['compilerStatus'], 'dynamic')
        self.assertIsNone(call['declaredTarget'])

    def test_missing_signature_type_is_reported_for_an_apparent_binding(self):
        text = 'class C { Missing Pick()=>null; void Go() { Pick(); } }'
        result = run_semantic_host({'projects': [self._project(text)], 'rootProject': 'Example'})
        call = result['projects'][0]['calls'][0]
        self.assertEqual(call['compilerStatus'], 'resolved')
        self.assertIn('error-type', [d['id'] for d in call['bindingDiagnostics']])

    def test_console_top_level_and_module_initializer_are_only_analyzed(self):
        text = ('C.Pick(1); class C { public static int Pick(int x)=>x; '
                '[System.Runtime.CompilerServices.ModuleInitializer] '
                'public static void Start()=>throw new System.Exception("must never execute"); }')
        project = {**self._project(text), 'outputKind': 'console'}
        result = run_semantic_host({'projects': [project], 'rootProject': 'Example'})
        self.assertEqual([d for d in result['projects'][0]['diagnostics'] if d['severity'] == 'error'], [])
        call = result['projects'][0]['calls'][0]
        self.assertEqual(call['declaredTarget']['signature'], 'C.Pick(int)')

    def test_di_registration_requires_framework_symbol_and_never_confirms_runtime(self):
        text = ('using Microsoft.Extensions.DependencyInjection; interface IFoo { void Save(); } class Foo:IFoo { public void Save() {} } '
                'class Fake { public void AddScoped<T,U>() {} } '
                'class Setup { void Go(IServiceCollection services, Fake fake) { '
                'services.AddScoped<IFoo,Foo>(); services.AddScoped<IFoo>(sp=>new Foo()); '
                'fake.AddScoped<IFoo,Foo>(); } void Use(IFoo foo) { foo.Save(); } }')
        project = {**self._project(text), 'references': framework_references('net10.0', aspnet=True)}
        result = run_semantic_host({'projects': [project], 'rootProject': 'Example'})
        registrations = result['projects'][0]['registrations']
        self.assertEqual(len(registrations), 2)
        for row in registrations:
            self.assertTrue(row['conditional'])
            self.assertFalse(row['runtimeTargetConfirmed'])
            self.assertEqual(row['serviceType']['name'], 'IFoo')
            self.assertEqual([t['name'] for t in row['implementationTypes']], ['Foo'])
        self.assertEqual([row['factory'] for row in registrations], [False, True])
        save_call = next(row for row in result['projects'][0]['calls']
                         if row['declaredTarget'] and row['declaredTarget']['qualifiedName'] == 'IFoo.Save')
        self.assertEqual(registrations[1]['serviceType']['key'], save_call['declaredTarget']['containingTypeKey'])
        self.assertIsNone(registrations[1]['serviceType']['containingTypeKey'])

    def test_constructed_interface_implementations_and_di_keys_do_not_collapse(self):
        text = ('using Microsoft.Extensions.DependencyInjection; '
                'interface I<T> { void Save(T value); } '
                'class A:I<int> { public void Save(int value) {} } '
                'class B:I<string> { public void Save(string value) {} } '
                'class Setup { void Configure(IServiceCollection s) { s.AddScoped<I<int>,A>(); '
                's.AddScoped<I<string>,B>(); } void Go(I<int> s) { s.Save(1); } }')
        project = {**self._project(text), 'references': framework_references('net10.0', aspnet=True)}
        result = run_semantic_host({'projects': [project], 'rootProject': 'Example'})['projects'][0]
        call = next(row for row in result['calls'] if row['dispatchKind'] == 'interface')
        self.assertEqual(call['declaredTarget']['signature'], 'I<int>.Save(int)')
        self.assertEqual([row['signature'] for row in call['implementationCandidates']], ['A.Save(int)'])
        matches = [row for row in result['registrations']
                   if row['serviceType']['key'] == call['declaredTarget']['containingTypeKey']]
        self.assertEqual(len(matches), 1)
        self.assertEqual(matches[0]['implementationTypes'][0]['signature'], 'A')
        self.assertNotEqual(result['registrations'][0]['serviceType']['key'], result['registrations'][1]['serviceType']['key'])

    def test_generic_method_keeps_bound_signature_and_shared_source_definition(self):
        text = 'class C { T Echo<T>(T value)=>value; void Go() { Echo(1); Echo("a"); } }'
        result = run_semantic_host({'projects': [self._project(text)], 'rootProject': 'Example'})['projects'][0]
        first, second = [row['declaredTarget'] for row in result['calls']]
        self.assertEqual(first['signature'], 'C.Echo<int>(int)')
        self.assertEqual(second['signature'], 'C.Echo<string>(string)')
        self.assertNotEqual(first['key'], second['key'])
        self.assertEqual(first['definitionKey'], second['definitionKey'])
        self.assertEqual(first['declarations'], second['declarations'])
        location = first['declarations'][0]
        self.assertEqual(text.encode()[location['startByte']:location['endByte']], b'T Echo<T>(T value)=>value;')


if __name__ == '__main__':
    unittest.main()
