"""The deliverable can be checked without shipping application code or plugins."""
from __future__ import annotations

from contextlib import redirect_stderr, redirect_stdout
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from contextbase.__main__ import main
from contextbase.registry import configure


class PublicationCliTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        md = self.root / 'output/md'
        (md / '基本設計書').mkdir(parents=True)
        (md / '機能一覧.md').write_text(
            '# 機能一覧\n\n[参照](基本設計書/見本.md)\n', encoding='utf-8')
        (md / '基本設計書/見本.md').write_text(
            '# 見本\n\n## 内容\n\n説明を維持する。\n\n| 項目 | 必須 |\n| --- | --- |\n| ID | 必須 |\n', encoding='utf-8')
        (self.root / 'config').mkdir()
        (self.root / 'config/project.toml').write_text(
            '[project]\nid="sample"\ninput="input"\nprofile="missing-plugin"\nrepository=""\n',
            encoding='utf-8')

    def invoke(self, command):
        buffer = io.StringIO()
        with redirect_stdout(buffer):
            status = main([command, '--root', str(self.root)])
        return status, json.loads(buffer.getvalue())

    def test_build_and_check_without_input_or_dynamic_profile(self):
        self.assertFalse((self.root / 'input').exists())
        self.assertFalse((self.root / 'src-dynamic').exists())
        with patch('contextbase.__main__.resolve_profile', side_effect=AssertionError('must not select profile')):
            status, result = self.invoke('build')
            self.assertEqual(status, 0)
            self.assertEqual(result['html_documents'], 2)
            status, result = self.invoke('check')
            self.assertEqual(status, 0)
            self.assertEqual(result['status'], 'pass')
            self.assertEqual(result['html_pages_including_index'], 3)
        self.assertFalse((self.root / 'input').exists())

    def test_no_config_uses_publication_defaults_without_input(self):
        (self.root / 'config/project.toml').unlink()
        self.assertEqual(self.invoke('build')[0], 0)
        self.assertEqual(self.invoke('check')[0], 0)

    def test_probe_still_requires_source(self):
        with redirect_stderr(io.StringIO()), self.assertRaises(SystemExit) as error:
            self.invoke('probe')
        self.assertEqual(error.exception.code, 1)

    def test_rebuild_rejects_missing_input_without_touching_publication(self):
        self.invoke('build')
        target = self.root / 'output/html/基本設計書/見本.html'
        before = target.read_bytes()
        with redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
            self.invoke('rebuild')
        self.assertEqual(before, target.read_bytes())
        self.assertFalse((self.root / '.contextbase-work').exists())

    def test_input_validation_default_remains_strict(self):
        with self.assertRaisesRegex(ValueError, 'Input directory does not exist'):
            configure(self.root)
        self.assertEqual(configure(self.root, require_input=False)['id'], 'sample')

    def test_path_validation_is_not_disabled(self):
        (self.root / 'config/project.toml').write_text('[project]\ninput="../outside"\n', encoding='utf-8')
        with self.assertRaisesRegex(ValueError, 'Unsafe input'):
            configure(self.root, require_input=False)

    def test_check_reports_visible_content_loss_without_source(self):
        self.invoke('build')
        target = self.root / 'output/html/基本設計書/見本.html'
        target.write_text(target.read_text(encoding='utf-8').replace('説明を維持する。', '改変'), encoding='utf-8')
        status, result = self.invoke('check')
        self.assertEqual(status, 1)
        self.assertIn('visible_content_changed', {e['rule'] for e in result['errors']})

    def test_repeated_publication_remains_idempotent(self):
        self.invoke('build')
        status, result = self.invoke('build')
        self.assertEqual(status, 0)
        self.assertEqual(result['written'], 0)


if __name__ == '__main__':
    unittest.main()
