"""Adopted amendment reporting through the public publication preparation seam."""
import unittest

from contextbase_discovery.reporting import prepare_report
import test_amendment_runtime as runtime_fixture


class AmendmentReportingTests(unittest.TestCase):
    def setUp(self):
        self.runtime = runtime_fixture.AmendmentRuntimeTests()
        self.runtime.setUp()

    def tearDown(self):
        self.runtime.tearDown()

    def test_report_separates_old_issue_author_declaration_and_fresh_independent_verdict(self):
        self.assertEqual('complete', self.runtime.amend()['status'])
        agent = self.runtime.agent
        destination = self.runtime.root / 'report-staging'
        final = self.runtime.root / 'formal-report'
        envelope = agent.export()
        summary = prepare_report(agent, envelope, destination, final)
        review = (destination / 'review.md').read_text(encoding='utf-8')
        self.assertIn('改訂指摘と処置', review)
        self.assertIn('旧指摘は調査入力', review)
        self.assertIn('Synthetic issue, not a real verifier.', review)
        self.assertIn(self.runtime.fixture.verification_id, review)
        seed = agent.session.store.get('amendment-seed.json')
        self.assertIn(seed['baseCandidateSha256'], review)
        self.assertIn(seed['issues'][0]['sourceCandidateSha256'], review)
        self.assertIn('作者処置（未信頼の申告）', review)
        self.assertIn('変更した', review)
        self.assertIn('Synthetic issue disposition.', review)
        self.assertIn('今回の独立判定', review)
        self.assertIn('合格', review)
        self.assertIn('Fresh independent source check.', review)
        self.assertIn('#L1', review)
        self.assertEqual(envelope['sha256'], summary['formalSha256'])
        self.assertEqual(7, len(summary['files']))


if __name__ == '__main__':
    unittest.main()
