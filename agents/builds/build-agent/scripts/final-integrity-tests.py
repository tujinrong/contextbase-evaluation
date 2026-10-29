"""Exercise final-delivery verification against independent disposable repositories."""
from pathlib import Path
import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
sys.dont_write_bytecode = True
from output_layout import ensure_directory

HERE = Path(__file__).resolve().parent
SCRATCH = HERE.parent / '.tmp/final-integrity-tests'
ensure_directory(SCRATCH)


class FinalIntegrityTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix='fixture-', dir=SCRATCH)
        self.root = Path(self.temporary.name)
        tools = self.root / 'agents/builds/build-agent/scripts'
        tools.mkdir(parents=True)
        for name in ['check-output-layout.py', 'output_layout.py', 'project_scope.py']:
            shutil.copyfile(HERE / name, tools / name)
        self.write('.gitignore', '**/.tmp/\n')
        self.write('sample-project2/spec/README.md', '|方式ID|specRoot|sourceRoot|\n|---|---|---|\n|Access|sample-project2/spec/Access/|sample-project2/srcs/Access/|\n|CSharp_ASPNET|sample-project2/spec/CSharp_ASPNET/|sample-project2/srcs/CSharp_ASPNET/|\n')
        for profile in ['Access', 'CSharp_ASPNET']:
            self.write(f'sample-project2/spec/{profile}/README.md', '# Canonical input\n')
            self.write(f'sample-project2/srcs/{profile}/app.txt', 'authoritative source\n')
        self.git('init', '-q')
        self.git('add', '.')
        self.git('-c', 'user.name=Fixture', '-c', 'user.email=fixture@example.invalid', 'commit', '-qm', 'fixture baseline')
        for profile in ['Access', 'CSharp_ASPNET']:
            owner = f'sample-project2/srcs/{profile}'
            generation = f'{owner}/build/generation'
            metadata = {'projectId': 'sample-project2', 'profileId': profile, 'runId': 'current', 'inspectionOnly': False}
            inputs = {**metadata, 'files': [self.entry(f'sample-project2/spec/{profile}/README.md')]}
            structure = {**metadata, 'status': 'structure-check-passed'}
            self.write(f'{generation}/inputs.json', json.dumps(inputs))
            self.write(f'{generation}/structure.json', json.dumps(structure))
            artifacts = []
            if profile == 'Access':
                file = f'{owner}/build/CareerManagement.accdb'
                self.write(file, 'synthetic artifact for hash verification only')
                artifacts = [{**self.entry(file), 'kind': 'standalone-access-database'}]
            output = {**metadata, 'files': [self.entry(f'{owner}/app.txt')], 'artifacts': artifacts, 'delivery': [self.entry(f'{generation}/{name}.json') for name in ['inputs', 'structure']]}
            self.write(f'{generation}/outputs.json', json.dumps(output))

    def tearDown(self):
        self.temporary.cleanup()

    def write(self, file, content):
        target = self.root / file
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding='utf-8')

    def git(self, *arguments):
        subprocess.run(['git', *arguments], cwd=self.root, check=True, capture_output=True)

    def entry(self, file):
        return {'file': file, 'sha256': hashlib.sha256((self.root / file).read_bytes()).hexdigest()}

    def run_check(self, expected=0, profile=None):
        result = subprocess.run([sys.executable, '-X', 'utf8', str(self.root / 'agents/builds/build-agent/scripts/check-output-layout.py'), '--project', 'sample-project2', *(['--profile', profile] if profile else [])], capture_output=True, text=True, encoding='utf-8')
        self.assertEqual(result.returncode, expected, result.stdout + result.stderr)
        return json.loads((self.root / 'sample-project2/build/test-results/final-integrity.json').read_text('utf-8'))

    def test_registered_two_methods_and_product_specific_artifact(self):
        result = self.run_check()
        self.assertEqual([method['profileId'] for method in result['methods']], ['Access', 'CSharp_ASPNET'])
        self.assertFalse((self.root / 'sample-project1').exists())

    def test_selection_does_not_read_another_methods_manifest(self):
        self.write('sample-project2/srcs/CSharp_ASPNET/build/generation/outputs.json', 'not valid JSON')
        self.assertEqual(self.run_check(profile='Access')['status'], 'PASS')

    def test_changed_source_and_missing_record_invalidate_previous_success(self):
        self.run_check()
        self.write('sample-project2/srcs/Access/app.txt', 'changed source\n')
        self.assertTrue(any(item['code'] == 'HASH_MISMATCH' for item in self.run_check(1)['findings']))
        (self.root / 'sample-project2/srcs/Access/build/generation/inputs.json').unlink()
        self.assertTrue(any(item['code'] == 'MISSING_OR_INVALID_CURRENT_RECORD' for item in self.run_check(1)['findings']))

    def test_only_one_access_artifact_and_fixed_layout(self):
        file = self.root / 'sample-project2/srcs/Access/build/generation/outputs.json'
        value = json.loads(file.read_text('utf-8'))
        value['artifacts'] *= 2
        file.write_text(json.dumps(value), encoding='utf-8')
        self.assertTrue(any(item['code'] == 'EXACTLY_ONE_ACCESS_DELIVERY_REQUIRED' for item in self.run_check(1)['findings']))

    def test_access_seed_record_requires_hash_coverage_and_history_is_rejected(self):
        record = 'sample-project2/srcs/Access/build/seed-manifest.json'
        self.write(record, '{"releaseState":"verification-candidate"}\n')
        self.assertTrue(any(item['code'] == 'UNRECORDED_FINAL_FILE' for item in self.run_check(1)['findings']))
        file = self.root / 'sample-project2/srcs/Access/build/generation/outputs.json'
        value = json.loads(file.read_text('utf-8'))
        value['artifacts'].append(self.entry(record))
        file.write_text(json.dumps(value), encoding='utf-8')
        self.assertEqual(self.run_check()['status'], 'PASS')
        self.write('sample-project2/srcs/Access/build/seed-manifest-backup.json', '{}\n')
        self.assertTrue(any(item['code'] == 'UNEXPECTED_BUILD_HISTORY_OR_WORK' for item in self.run_check(1)['findings']))

    def test_new_test_fixture_is_authorized_but_existing_specification_is_protected(self):
        self.write('sample-project2/srcs/Access/tests/fixtures/boundary-fixture.json', '{"synthetic":true}\n')
        self.assertEqual(self.run_check()['status'], 'PASS')
        self.write('sample-project2/spec/Access/README.md', '# Changed protected input\n')
        self.assertTrue(any(item['code'] == 'PROTECTED_INPUT_CHANGED' for item in self.run_check(1)['findings']))

    def test_unregistered_profile_and_manifest_path_escape_are_rejected(self):
        result = subprocess.run([sys.executable, '-X', 'utf8', str(self.root / 'agents/builds/build-agent/scripts/check-output-layout.py'), '--project', 'sample-project2', '--profile', 'COBOL'], capture_output=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse((self.root / 'sample-project2/srcs/COBOL').exists())
        file = self.root / 'sample-project2/srcs/Access/build/generation/outputs.json'
        value = json.loads(file.read_text('utf-8'))
        value['files'].append({'file': '../outside', 'sha256': '0' * 64})
        file.write_text(json.dumps(value), encoding='utf-8')
        self.assertTrue(any(item['code'] == 'EXCLUDED_MANIFEST_ENTRY' for item in self.run_check(1)['findings']))


if __name__ == '__main__':
    unittest.main(verbosity=2)
