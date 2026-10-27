"""Bounded project/generator text acquisition never executes input material."""
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from contextbase_discovery import DiscoveryAgent
from contextbase_runtime.sources import SourceAccess
from test_independent_agents import request


class SourceMaterialTests(unittest.TestCase):
    def setUp(self):
        home = Path(__file__).resolve().parents[1] / '.tmp'
        home.mkdir(exist_ok=True)
        self.temporary = tempfile.TemporaryDirectory(prefix='source-materials-', dir=home)
        self.root = Path(self.temporary.name)
        self.source = self.root / 'source'
        self.source.mkdir()
        self.write('Program.cs', b'class Program {\n static void Main() {}\n}\n')

    def tearDown(self):
        self.temporary.cleanup()

    def write(self, relative, data):
        path = self.source / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
        return path

    def snapshot(self):
        return SourceAccess.create(self.source, self.root / 'snapshot', project_id='synthetic-materials',
                                   allowed_paths=['.'], excluded_paths=[])

    def test_solution_and_generator_text_enter_the_sealed_inventory_with_exact_evidence(self):
        materials = {
            'App.slnx': b'<Solution>\r\n <Project Path="App.csproj" />\r\n</Solution>\r\n',
            'database/generate.mjs': b'// Synthetic generator source only.\nexport const schema = "sample";\n'}
        for path, data in materials.items():
            self.write(path, data)
        access = self.snapshot()
        entries = {item['path']: item for item in access.manifest['files']}
        self.assertEqual({'Program.cs', *materials}, set(entries))
        for path, data in materials.items():
            with self.subTest(path=path):
                entry = entries[path]
                self.assertEqual(hashlib.sha256(data).hexdigest(), entry['sha256'])
                self.assertEqual(len(data), entry['bytes'])
                self.assertEqual(3 if path.endswith('.slnx') else 2, entry['lines'])
                self.assertEqual(data, (access.root / 'sources' / path).read_bytes())
                self.assertEqual(data.decode('utf-8'), access.read(path))
                ref = access.evidence(path, 1, entry['lines'])
                access.verify_evidence(ref)
                access.verify_evidence_many([ref, ref])

    def test_uppercase_solution_and_module_suffixes_are_acquired(self):
        self.write('Upper.SLNX', b'<Solution/>\n')
        self.write('GENERATE.MJS', b'export const value = 1;\n')
        access = self.snapshot()
        self.assertEqual({'Program.cs', 'Upper.SLNX', 'GENERATE.MJS'}, set(access.paths))
        access.verify_evidence(access.evidence('GENERATE.MJS'))
        access.verify_evidence(access.evidence('Upper.SLNX'))

    def test_new_suffixes_do_not_bypass_excluded_directories_or_private_material_rules(self):
        blocked = [self.write(path, b'\x00\xff') for path in (
            'spec/generate.mjs', 'spec-eval/generate.mjs', '.env/generate.mjs',
            'tests/generate.mjs', 'build/generate.mjs', 'app/.env.local.mjs',
            'spec/App.slnx', 'spec-eval/App.slnx', 'tests/App.slnx', 'build/App.slnx')]
        original = Path.read_bytes
        def guarded(path):
            self.assertNotIn(path, blocked, 'Excluded source material must be pruned before reading bytes')
            return original(path)
        with patch.object(Path, 'read_bytes', guarded):
            access = self.snapshot()
        self.assertEqual(['Program.cs'], access.paths)
        reasons = {item['reason'] for item in access.manifest['omitted']}
        self.assertTrue({'excluded-directory', 'instructions-or-local-secret'} <= reasons)
        for path in ('spec/generate.mjs', 'spec-eval/generate.mjs', '.env/generate.mjs',
                     'tests/generate.mjs', 'build/generate.mjs', 'app/.env.local.mjs'):
            with self.subTest(path=path), self.assertRaises(ValueError):
                access.evidence(path)

    def test_generator_is_only_copied_as_text_and_never_executed(self):
        sentinel = self.root / 'generator-was-executed'
        script = ('import { writeFileSync } from "node:fs";\n'
                  'writeFileSync(' + json.dumps(str(sentinel)) + ', "unexpected execution");\n'
                  'throw new Error("Synthetic input must never run");\n').encode('utf-8')
        self.write('generate.mjs', script)
        with patch('subprocess.run', side_effect=AssertionError('Input generator execution is forbidden')) as process:
            access = self.snapshot()
            self.assertEqual(script.decode('utf-8'), access.read('generate.mjs'))
            access.verify_evidence(access.evidence('generate.mjs'))
            process.assert_not_called()
        self.assertFalse(sentinel.exists())

    def test_discovery_classifies_modules_as_programs_and_solution_xml_as_configuration(self):
        self.write('App.slnx', b'<Solution/>\n')
        self.write('Other.SLNX', b'<Solution/>\n')
        self.write('database/generate.mjs', b'export const value = 1;\n')
        self.write('UPPER.MJS', b'export const other = 2;\n')
        agent = DiscoveryAgent.create(self.source, self.root / 'work', request())
        assignment = agent.build_context({'inventory': agent.session.source.manifest,
                                          'structure': {'indexSha256': 'a' * 64}})
        groups = assignment['resourcesToAccountFor']
        self.assertEqual({'Program.cs', 'database/generate.mjs', 'UPPER.MJS'}, set(groups['programs']))
        self.assertEqual({'App.slnx', 'Other.SLNX'}, set(groups['configuration']))
        self.assertEqual([], groups['resources'])

    def test_gitignore_support_is_not_expanded_by_the_two_suffix_change(self):
        self.write('.gitignore', b'ignored-output/\n')
        access = self.snapshot()
        self.assertEqual(['Program.cs'], access.paths)
        omitted = {item['path']: item['reason'] for item in access.manifest['omitted']}
        self.assertEqual('unsupported-text-material', omitted['.gitignore'])


if __name__ == '__main__':
    unittest.main()
