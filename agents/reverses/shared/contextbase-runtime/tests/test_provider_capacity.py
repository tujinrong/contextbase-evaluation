"""The observed CLI character limit is caught before any model is launched."""
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from contextbase_runtime import provider


class ProviderCapacityTests(unittest.TestCase):
    def setUp(self):
        root = Path(__file__).resolve().parents[1] / '.tmp'
        root.mkdir(exist_ok=True)
        self.temporary = tempfile.TemporaryDirectory(prefix='provider-capacity-', dir=root)
        self.root = Path(self.temporary.name)
        self.source = self.root / 'snapshot'
        self.source.mkdir()

    def tearDown(self):
        self.temporary.cleanup()

    def test_oversized_input_preserves_prompt_and_never_starts_cli(self):
        prompt = '原文\r\n' + 'a' * provider.MAX_PROMPT_CHARS
        job = self.root / 'oversized'
        with patch.object(provider, 'resolve_cli') as resolve, patch.object(provider.subprocess, 'run') as launch:
            result = provider.run_job(self.source, job, prompt, None, 10)
        self.assertEqual('input_too_large', result['metadata']['status'])
        resolve.assert_not_called()
        launch.assert_not_called()
        saved = (job / 'prompt.txt').read_bytes().decode('utf-8')
        self.assertTrue(saved.endswith(prompt))
        self.assertEqual(len(saved), result['metadata']['input_characters'])
        self.assertEqual(result, json.loads((job / 'result.json').read_text(encoding='utf-8')))
        self.assertIsNone(result['answer'])

    def test_unicode_is_counted_as_characters_and_small_input_reaches_cli_resolution(self):
        job = self.root / 'unicode'
        prompt = '日' * (provider.MAX_PROMPT_CHARS // 2)
        with patch.object(provider, 'resolve_cli', side_effect=OSError('test-no-cli')) as resolve:
            result = provider.run_job(self.source, job, prompt, None, 10)
        resolve.assert_called_once()
        self.assertEqual('provider_unavailable', result['metadata']['status'])
        self.assertEqual('cli_resolution_failed', result['metadata']['error_code'])
        self.assertLess(result['metadata']['input_characters'], provider.MAX_PROMPT_CHARS)
        self.assertGreater((job / 'prompt.txt').stat().st_size, provider.MAX_PROMPT_CHARS)


if __name__ == '__main__':
    unittest.main()
