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
