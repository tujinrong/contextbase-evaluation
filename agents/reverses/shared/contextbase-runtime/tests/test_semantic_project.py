import hashlib
import base64
import json
from pathlib import Path
import tempfile
import unittest
import zipfile

from contextbase_runtime.semantic_project import build_project_context


class SemanticProjectTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        reference = self.root / 'packs/Microsoft.NETCore.App.Ref/10.0.1/ref/net10.0/System.Runtime.dll'
        reference.parent.mkdir(parents=True)
        reference.write_bytes(b'trusted test metadata')
        self.reference = reference

    def context(self, texts):
        return build_project_context(texts, project='Web.csproj', dotnet_root=self.root, package_roots=[])

    def test_project_closure_and_exclusions_are_source_bound(self):
        texts = {'Web.csproj': '<Project Sdk="Microsoft.NET.Sdk"><PropertyGroup><TargetFramework>net10.0</TargetFramework><ImplicitUsings>enable</ImplicitUsings></PropertyGroup><ItemGroup><Compile Remove="Core/**/*.cs;tests/**/*.cs"/><ProjectReference Include="Core/Core.csproj"/></ItemGroup></Project>',
                 'Directory.Build.props': '<Project><PropertyGroup><DefaultItemExcludes>$(DefaultItemExcludes);**/build/**</DefaultItemExcludes><BaseOutputPath>$([MSBuild]::Anything())</BaseOutputPath></PropertyGroup></Project>',
                 'Core/Core.csproj': '<Project Sdk="Microsoft.NET.Sdk"><PropertyGroup><TargetFramework>net10.0</TargetFramework></PropertyGroup></Project>',
                 'Main.cs': 'class Main {}', 'Core/C.cs': 'class C {}', 'tests/T.cs': '', 'build/B.cs': ''}
        result = self.context(texts)
        projects = {p['id']: p for p in result['projects']}
        self.assertEqual(['Main.cs'], [f['path'] for f in projects['Web.csproj']['files']])
        self.assertEqual(['Core/C.cs'], [f['path'] for f in projects['Core/Core.csproj']['files']])
        self.assertTrue(projects['Web.csproj']['configurationComplete'])
        self.assertEqual(['Core/Core.csproj'], projects['Web.csproj']['projectReferences'])
        self.assertIn('System', projects['Web.csproj']['globalUsings'])
        self.assertIn('Directory.Build.props', [f['path'] for f in result['binding']['config']])

    def test_unknown_condition_is_incomplete_and_missing_package_is_explicit(self):
        result = self.context({'Web.csproj': '<Project Sdk="Microsoft.NET.Sdk"><PropertyGroup><TargetFramework>net10.0</TargetFramework><DefineConstants Condition="unknown">OTHER</DefineConstants></PropertyGroup><ItemGroup><PackageReference Include="Missing" Version="1.2.3"/></ItemGroup></Project>', 'A.cs': ''})
        self.assertFalse(result['projects'][0]['configurationComplete'])
        self.assertTrue(any('Missing' in d['message'] for d in result['projects'][0]['diagnostics']))

    def test_reference_and_config_bytes_change_binding(self):
        texts = {'Web.csproj': '<Project Sdk="Microsoft.NET.Sdk"><PropertyGroup><TargetFramework>net10.0</TargetFramework></PropertyGroup></Project>'}
        first = self.context(texts)['binding']
        self.reference.write_bytes(b'changed')
        second = self.context(texts)['binding']
        self.assertNotEqual(first['references'], second['references'])
        texts['Web.csproj'] = texts['Web.csproj'].replace('</Project>', '<ItemGroup><Compile Remove="A.cs"/></ItemGroup></Project>')
        self.assertNotEqual(first['config'], self.context(texts)['binding']['config'])

    def test_parent_outside_inventory_and_import_are_never_evaluated(self):
        result = self.context({'Web.csproj': '<Project Sdk="Microsoft.NET.Sdk"><PropertyGroup><TargetFramework>net10.0</TargetFramework></PropertyGroup><Import Project="../unsafe.targets"/></Project>'})
        self.assertFalse(result['projects'][0]['configurationComplete'])

    def package_context(self):
        package = self.root / 'packages/example/1.2.3'
        metadata = package / 'ref/net9.0/Example.dll'
        metadata.parent.mkdir(parents=True)
        metadata.write_bytes(b'archive metadata')
        archive = package / 'example.1.2.3.nupkg'
        with zipfile.ZipFile(archive, 'w') as z:
            z.write(metadata, 'ref/net9.0/Example.dll')
        lock = {'dependencies': {'net10.0': {'Example': {'resolved': '1.2.3', 'contentHash': base64.b64encode(hashlib.sha512(archive.read_bytes()).digest()).decode()}}}}
        texts = {'Web.csproj': '<Project Sdk="Microsoft.NET.Sdk"><PropertyGroup><TargetFramework>net10.0</TargetFramework></PropertyGroup><ItemGroup><PackageReference Include="Example" Version="1.2.3"/></ItemGroup></Project>',
                 'packages.lock.json': json.dumps(lock)}
        return texts, archive, metadata

    def test_package_metadata_is_locked_and_extracted_bytes_are_verified(self):
        texts, archive, metadata = self.package_context()
        def context():
            return build_project_context(texts, project='Web.csproj', dotnet_root=self.root, package_roots=[self.root / 'packages'])
        result = context()
        self.assertTrue(result['projects'][0]['configurationComplete'])
        selected = next(r for r in result['binding']['references'] if r.get('packageId') == 'Example')
        self.assertEqual('net9.0', selected['tfm'])
        self.assertTrue(selected['lockVerified'])
        metadata.write_bytes(b'tampered extracted metadata')
        result = context()
        self.assertFalse(result['projects'][0]['configurationComplete'])
        self.assertTrue(any('differs from archive' in d['message'] for d in result['projects'][0]['diagnostics']))
        metadata.write_bytes(b'archive metadata')
        with zipfile.ZipFile(archive, 'a') as z:
            z.writestr('new.txt', 'changed archive')
        self.assertFalse(context()['projects'][0]['configurationComplete'])

    def test_explicit_empty_reference_group_prevents_library_fallback(self):
        texts, archive, metadata = self.package_context()
        metadata.unlink()
        with zipfile.ZipFile(archive, 'w') as z:
            z.writestr('ref/net10.0/_._', '')
            z.writestr('lib/net10.0/Example.dll', b'must not become a compile reference')
        lock = json.loads(texts['packages.lock.json'])
        lock['dependencies']['net10.0']['Example']['contentHash'] = base64.b64encode(hashlib.sha512(archive.read_bytes()).digest()).decode()
        texts['packages.lock.json'] = json.dumps(lock)
        result = build_project_context(texts, project='Web.csproj', dotnet_root=self.root, package_roots=[self.root / 'packages'])
        self.assertTrue(result['projects'][0]['configurationComplete'])
        self.assertFalse(any(r.get('packageId') == 'Example' for r in result['binding']['references']))
        self.assertTrue(result['binding']['packages'][0]['lockVerified'])

    def test_configuration_symbols_and_compile_item_order(self):
        texts = {'Web.csproj': '<Project Sdk="Microsoft.NET.Sdk"><PropertyGroup><TargetFramework>net10.0</TargetFramework><AssemblyName>Other</AssemblyName><OutputType>Exe</OutputType></PropertyGroup><ItemGroup><Compile Remove="A.cs"/><Compile Include="A.cs"/></ItemGroup></Project>', 'A.cs': ''}
        release = self.context(texts)
        self.assertEqual('Other', release['projects'][0]['assemblyName'])
        self.assertEqual('console', release['projects'][0]['outputKind'])
        self.assertEqual(['A.cs'], [f['path'] for f in release['projects'][0]['files']])
        self.assertIn('TRACE', release['projects'][0]['defines'])
        self.assertNotIn('DEBUG', release['projects'][0]['defines'])
        debug = build_project_context(texts, project='Web.csproj', dotnet_root=self.root, package_roots=[], configuration='Debug')
        self.assertIn('DEBUG', debug['projects'][0]['defines'])
        self.assertNotEqual(release['binding'], debug['binding'])

    def test_missing_framework_reference_and_added_targets_are_explicit(self):
        texts = {'Web.csproj': '<Project Sdk="Microsoft.NET.Sdk"><PropertyGroup><TargetFramework>net10.0</TargetFramework></PropertyGroup></Project>'}
        self.reference.unlink()
        # An installed empty pack is not a valid reference set.
        self.assertFalse(self.context(texts)['projects'][0]['configurationComplete'])
        self.reference.write_bytes(b'restored')
        texts['Directory.Build.targets'] = '<Project><ItemGroup><Compile Include="B.cs"/></ItemGroup></Project>'
        result = self.context(texts)
        self.assertFalse(result['projects'][0]['configurationComplete'])
        self.assertIn('Directory.Build.targets', [f['path'] for f in result['binding']['config']])

    def test_missing_explicit_compile_input_is_not_an_empty_glob(self):
        template = '<Project Sdk="Microsoft.NET.Sdk"><PropertyGroup><TargetFramework>net10.0</TargetFramework></PropertyGroup><ItemGroup><Compile Include="{}"/></ItemGroup></Project>'
        missing = self.context({'Web.csproj': template.format('Missing.cs')})
        self.assertFalse(missing['projects'][0]['configurationComplete'])
        empty_glob = self.context({'Web.csproj': template.format('missing/**/*.cs')})
        self.assertTrue(empty_glob['projects'][0]['configurationComplete'])

    def test_omitted_source_requires_proven_project_exclusion(self):
        template = '<Project Sdk="Microsoft.NET.Sdk"><PropertyGroup><TargetFramework>net10.0</TargetFramework></PropertyGroup>{}</Project>'
        omitted = [{'path': 'tests', 'reason': 'excluded-directory'},
                   {'path': '.gitignore', 'reason': 'unsupported-text-material'},
                   {'path': 'obj', 'reason': 'excluded-directory'}]
        def context(items):
            return build_project_context({'Web.csproj': template.format(items)}, project='Web.csproj', dotnet_root=self.root, package_roots=[], omitted=omitted)
        self.assertFalse(context('')['projects'][0]['configurationComplete'])
        self.assertTrue(context('<ItemGroup><Compile Remove="tests/**/*.cs"/></ItemGroup>')['projects'][0]['configurationComplete'])
        self.assertFalse(context('<ItemGroup><Compile Remove="tests/*.cs"/></ItemGroup>')['projects'][0]['configurationComplete'])
        self.assertFalse(context('<ItemGroup><Compile Remove="tests/**/*.cs"/><Compile Include="tests/**/*.cs"/></ItemGroup>')['projects'][0]['configurationComplete'])

    def test_omitted_cs_file_inside_and_unrelated_project_subtree(self):
        texts = {'Web.csproj': '<Project Sdk="Microsoft.NET.Sdk"><PropertyGroup><TargetFramework>net10.0</TargetFramework></PropertyGroup><ItemGroup><Compile Remove="Core/**/*.cs"/><ProjectReference Include="Core/Core.csproj"/></ItemGroup></Project>',
                 'Core/Core.csproj': '<Project Sdk="Microsoft.NET.Sdk"><PropertyGroup><TargetFramework>net10.0</TargetFramework></PropertyGroup></Project>'}
        result = build_project_context(texts, project='Web.csproj', dotnet_root=self.root, package_roots=[], omitted=[{'path': 'Hidden.cs', 'reason': 'outside-allowed-paths'}])
        projects = {p['id']: p for p in result['projects']}
        self.assertFalse(projects['Web.csproj']['configurationComplete'])
        self.assertTrue(projects['Core/Core.csproj']['configurationComplete'])


if __name__ == '__main__':
    unittest.main()
