import tempfile
from pathlib import Path
import unittest
from unittest.mock import patch
from contextbase_runtime.roles import normalize_roles, validate_roles

class RoleTests(unittest.TestCase):
    def test_custom_role_preserves_bytes_and_detects_changes(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            path = root / 'role.md'
            path.write_bytes(b'Analyze carefully.\r\n')
            with patch.dict('os.environ', {'CODEX_HOME': str(root)}):
                roles = normalize_roles({'analysis': {'id': 'reader', 'instructions': 'role.md', 'model': 'test-model'}}, root)
            self.assertEqual('reader', roles['analysis']['id'])
            self.assertEqual('Analyze carefully.\r\n', roles['analysis']['instructions_text'])
            validate_roles(roles)
            path.write_text('Changed', encoding='utf-8')
            with self.assertRaises(ValueError):
                validate_roles(roles)

    def test_user_choices_are_snapshotted_without_secrets(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / 'config.toml').write_text('model="user-model"\nmodel_reasoning_effort="high"\nsecret="not-recorded"\n', encoding='utf-8')
            with patch.dict('os.environ', {'CODEX_HOME': str(root)}):
                roles = normalize_roles()
            self.assertEqual('user-model', roles['analysis']['model'])
            self.assertNotIn('not-recorded', str(roles))

    def test_custom_provider_is_not_silently_replaced(self):
        with self.assertRaises(ValueError):
            normalize_roles({'analysis': {'model_provider': 'private'}})

    def test_role_capabilities_are_explicit_and_preserve_legacy_snapshots(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            skill = root / 'review/SKILL.md'
            skill.parent.mkdir()
            skill.write_text('---\nname: source-review\ndescription: Review fixture.\n---\nRead source.\n',
                             encoding='utf-8')
            with patch.dict('os.environ', {'CODEX_HOME': str(root)}):
                legacy = normalize_roles()
                selected = normalize_roles({'analysis': {'capabilities': {
                    'skills': ['review/SKILL.md'], 'web_search': 'cached', 'subagents': True}}}, root)
            self.assertNotIn('capabilities', legacy['analysis'])
            self.assertEqual(legacy, validate_roles(legacy))
            self.assertNotIn('capabilities', selected['verification'])
            policy = selected['analysis']['capabilities']
            self.assertEqual('cached', policy['web_search'])
            self.assertEqual(str(skill.resolve()), policy['skills'][0]['path'])
            self.assertEqual(selected, validate_roles(selected))
            skill.write_text('Changed Skill.', encoding='utf-8')
            with self.assertRaises(ValueError):
                validate_roles(selected)
            self.assertEqual(selected, validate_roles(selected, check_file=False))

    def test_unsupported_role_capability_fails_explicitly(self):
        with self.assertRaisesRegex(ValueError, 'Unsupported role capabilities: shell'):
            normalize_roles({'analysis': {'capabilities': {'shell': True}}})
