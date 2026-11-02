"""Public native project profiles preserve role settings and select joint execution."""
from contextlib import redirect_stdout
import io
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from contextbase_runtime.cli import main
from contextbase_runtime.config import ProjectProfile
from test_independent_agents import request


class NativeCLIConfigTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / 'source').mkdir()
        (self.root / 'request.json').write_text(json.dumps(request()), encoding='utf-8')
        (self.root / 'reader.md').write_text('Read complete source carefully.', encoding='utf-8')
        self.config = self.root / 'project.toml'
        self.write()

    def write(self, mode='native'):
        self.config.write_text('''schema = "contextbase-project/1"
default_profile = "sample"
[profiles.sample]
source = "source"
request = "request.json"
work = "work"
output = "output"
context_mode = "''' + mode + '''"
[profiles.sample.roles.analysis]
id = "source-reader"
instructions = "reader.md"
model = "test-model"
''', encoding='utf-8')

    def test_profile_resolves_role_relative_to_config(self):
        profile = ProjectProfile.load(self.config)
        self.assertEqual('source-reader', profile.role_specs['analysis']['id'])
        self.assertEqual(str((self.root / 'reader.md').resolve()), profile.role_specs['analysis']['instructions_path'])
        self.assertEqual('test-model', profile.role_specs['analysis']['model'])

    def test_roles_cannot_be_ignored_by_legacy_mode(self):
        self.write('full')
        with self.assertRaisesRegex(ValueError, 'Role profiles require native'):
            ProjectProfile.load(self.config)

    def test_profile_preserves_and_describes_role_capabilities(self):
        skill = self.root / 'skills' / 'source-reader' / 'SKILL.md'
        skill.parent.mkdir(parents=True)
        skill.write_text('---\nname: source-reader\ndescription: Read source.\n---\nUse evidence.\n', encoding='utf-8')
        with self.config.open('a', encoding='utf-8') as stream:
            stream.write('\n[profiles.sample.roles.analysis.capabilities]\n'
                         'skills = ["skills/source-reader/SKILL.md"]\n'
                         'web_search = "cached"\nsubagents = true\n')
        profile = ProjectProfile.load(self.config)
        capabilities = profile.role_specs['analysis']['capabilities']
        self.assertEqual(str(skill.resolve()), capabilities['skills'][0]['path'])
        self.assertEqual('cached', capabilities['web_search'])
        self.assertTrue(capabilities['subagents'])
        from contextbase_runtime.project_analysis import ProjectAnalysisAgent
        self.assertEqual(capabilities, profile.describe(ProjectAnalysisAgent)['roles']['analysis']['capabilities'])
        self.assertNotIn('capabilities', profile.role_specs['verification'])

    def test_project_init_selects_native_with_roles(self):
        calls = []
        class Agent:
            name = 'project-analysis'
            stage = None
            @classmethod
            def create(cls, *args, **kwargs):
                calls.append((args, kwargs))
                return SimpleNamespace(status=lambda: {'status': 'active'})
        with patch.object(ProjectProfile, 'bind'), redirect_stdout(io.StringIO()):
            code = main(Agent, ['init', '--config', str(self.config)])
        self.assertEqual(0, code)
        self.assertTrue(calls[0][1]['native_mode'])
        self.assertEqual('source-reader', calls[0][1]['role_specs']['analysis']['id'])

    def test_project_init_rejects_conflicting_legacy_mode(self):
        class Agent:
            name = 'project-analysis'
            stage = None
        with redirect_stdout(io.StringIO()) as output:
            code = main(Agent, ['init', '--source', str(self.root / 'source'),
                '--request', str(self.root / 'request.json'), '--work', str(self.root / 'work'), '--incremental'])
        self.assertEqual(1, code)
        self.assertIn('native role execution', output.getvalue())
