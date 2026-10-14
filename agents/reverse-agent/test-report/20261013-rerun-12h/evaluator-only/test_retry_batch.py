"""Validate immutable reuse and refusal to copy unfinished or tampered inference."""
from pathlib import Path
import json
import tempfile
import unittest
from unittest.mock import patch
import grader
import retry_batch


class RetryIntegrity(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.source, self.destination = self.root / 'before', self.root / 'retry'
        self.source.mkdir()
        self.seal = {'jobs': [{'shardId': 'ok', 'requestPath': 'requests/ok.json'},
                             {'shardId': 'bad', 'requestPath': 'requests/bad.json'}]}
        for name in ('batch.json', 'answer-schema.json', 'canonical-pin.json'):
            grader.save(self.source / name, self.seal if name == 'batch.json' else {})
        for job in self.seal['jobs']:
            grader.save(self.source / 'capsule' / job['requestPath'], {})
        grader.save(self.source / 'capsule/manifest.json', {'files': []})
        grader.save(self.source / 'jobs/ok/answer.txt', {'original': '0.01'} )
        grader.save(self.source / 'jobs/ok/result.json', {'status': 'PASSED',
            'answerSha256': grader.digest(self.source / 'jobs/ok/answer.txt')})
        grader.save(self.source / 'jobs/bad/result.json', {'status': 'CLI_FAILED'})
        self.check = patch.object(grader, 'check_capsule', side_effect=lambda path: (self.seal, path / 'capsule'))
        self.validate = patch.object(grader, 'validate_answer')
        self.check.start()
        self.validate.start()
        self.addCleanup(self.check.stop)
        self.addCleanup(self.validate.stop)

    def test_preserves_original_and_reuses_only_accepted_bytes(self):
        before = {p.relative_to(self.source).as_posix(): p.read_bytes() for p in self.source.rglob('*') if p.is_file()}
        self.assertEqual(retry_batch.prepare_retry(self.source, self.destination), {'reused': 1, 'retryJobs': 1})
        self.assertFalse((self.destination / 'jobs/bad').exists())
        self.assertEqual((self.destination / 'jobs/ok/answer.txt').read_bytes(), before['jobs/ok/answer.txt'])
        self.assertEqual(before, {p.relative_to(self.source).as_posix(): p.read_bytes() for p in self.source.rglob('*') if p.is_file()})
        record = grader.load(self.destination / 'retry-provenance.json')
        self.assertEqual(record['retryJobs'][0]['previousStatus'], 'CLI_FAILED')

    def test_tampered_accepted_answer_is_rejected_before_copy(self):
        grader.save(self.source / 'jobs/ok/answer.txt', {'edited': '1'}, exclusive=False)
        with self.assertRaisesRegex(ValueError, 'answer drift'):
            retry_batch.prepare_retry(self.source, self.destination)
        self.assertFalse(self.destination.exists())

    def test_unfinished_original_is_rejected_before_copy(self):
        (self.source / 'jobs/bad/result.json').unlink()
        with self.assertRaisesRegex(ValueError, 'every original job'):
            retry_batch.prepare_retry(self.source, self.destination)
        self.assertFalse(self.destination.exists())

    def test_completed_successful_batch_does_not_retry(self):
        grader.save(self.source / 'jobs/bad/answer.txt', {})
        grader.save(self.source / 'jobs/bad/result.json', {'status': 'PASSED',
            'answerSha256': grader.digest(self.source / 'jobs/bad/answer.txt')}, exclusive=False)
        with self.assertRaisesRegex(ValueError, 'No failed inference'):
            retry_batch.prepare_retry(self.source, self.destination)

    def test_failed_normalization_can_retry_without_regrading_accepted_rows(self):
        self.seal['documentIds'] = ['DOC']
        grader.save(self.source / 'jobs/bad/answer.txt', {})
        grader.save(self.source / 'jobs/bad/result.json', {'status': 'PASSED',
            'answerSha256': grader.digest(self.source / 'jobs/bad/answer.txt')}, exclusive=False)
        grader.save(self.source / 'normalization-jobs/DOC/result.json', {'status': 'FAILED'})
        self.assertEqual(retry_batch.prepare_retry(self.source, self.destination, True), {'reused': 2, 'retryJobs': 0})
        self.assertFalse((self.destination / 'normalization-jobs').exists())
        self.assertEqual(grader.load(self.destination / 'retry-provenance.json')['previousNormalizationFailures'][0]['documentId'], 'DOC')

    def test_successful_normalization_cannot_be_retried_to_seek_a_better_score(self):
        self.seal['documentIds'] = ['DOC']
        grader.save(self.source / 'jobs/bad/answer.txt', {})
        grader.save(self.source / 'jobs/bad/result.json', {'status': 'PASSED',
            'answerSha256': grader.digest(self.source / 'jobs/bad/answer.txt')}, exclusive=False)
        grader.save(self.source / 'normalization-jobs/DOC/result.json', {'status': 'PASSED'})
        with self.assertRaisesRegex(ValueError, 'No recorded normalization failure'):
            retry_batch.prepare_retry(self.source, self.destination, True)
        self.assertFalse(self.destination.exists())


if __name__ == '__main__':
    unittest.main()
