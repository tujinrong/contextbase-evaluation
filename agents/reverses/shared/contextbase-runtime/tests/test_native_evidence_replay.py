"""Operation-local replay retains canonical receipts without per-call fences."""
import unittest
from unittest.mock import patch
import test_native_evidence as fixtures
from contextbase_runtime.native_evidence import replay_evidence, run_batch


class ReplayEvidenceTests(unittest.TestCase):
    setUp = fixtures.NativeBatchTests.setUp
    tearDown = fixtures.NativeBatchTests.tearDown

    def test_individual_and_batch_equal_live_with_constant_fences(self):
        requests=[fixtures.query(), {'operation':'read','path':'A.cs','startLine':1,'endLine':1},
                  {'operation':'search','path':None,'text':'Write','offset':0,'limit':20,'caseSensitive':False},
                  {'operation':'inventory','offset':0,'limit':20}]
        expected=[self.access.handle(r) for r in requests]
        batch=run_batch(self.access,requests[:2])
        with patch.object(self.access,'_assert_binding',wraps=self.access._assert_binding) as fence:
            with replay_evidence(self.access) as acquire:
                for request,reply in zip(requests,expected):
                    name=request['operation'];args={k:v for k,v in request.items() if k!='operation'}
                    self.assertEqual((reply,[{'request':request,'reply':reply}]),acquire(name,args))
                for _ in range(3):self.assertEqual(batch,acquire('evidence_batch',{'requests':requests[:2]}))
            self.assertEqual(2,fence.call_count)
        with self.assertRaisesRegex(RuntimeError,'closed'):acquire('query',{})

    def test_batch_prefix_and_multibyte_budget_unchanged(self):
        requests=[{'operation':'read','path':'unicode.txt','startLine':1,'endLine':1}]*8
        full,prefix=run_batch(self.access,requests)
        self.assertLess(len(prefix),len(requests))
        with replay_evidence(self.access) as acquire:
            actual=acquire('evidence_batch',{'requests':requests})
        self.assertEqual((full,prefix),actual)
        with replay_evidence(self.access) as acquire:
            with patch('contextbase_runtime.native_evidence.reply_size',side_effect=lambda value: 40000 if value.get('replies') else 100):
                reply,pairs=acquire('evidence_batch',{'requests':requests})
        self.assertEqual([],pairs);self.assertEqual(0,reply['next_request_index'])

    def test_source_and_index_mutation_detected_at_exit(self):
        path=self.source.root/'sources'/'A.cs';raw=path.read_bytes()
        try:
            with self.assertRaises(ValueError):
                with replay_evidence(self.access) as acquire:
                    acquire('query',{k:v for k,v in fixtures.query().items() if k!='operation'})
                    path.write_bytes(raw+b'// changed')
        finally:path.write_bytes(raw)
        original=self.index.document['snapshotId']
        try:
            with self.assertRaises(ValueError):
                with replay_evidence(self.access):self.index.document['snapshotId']='changed'
        finally:self.index.document['snapshotId']=original

    def test_cancellation_and_invalid_operation_do_not_return_receipts(self):
        checks=iter([True,False])
        with self.assertRaisesRegex(RuntimeError,'cancel'):
            with replay_evidence(self.access,check_current=lambda:next(checks,False)) as acquire:
                acquire('evidence_batch',{'requests':[fixtures.query()]})
        with replay_evidence(self.access) as acquire:
            with self.assertRaises(ValueError):acquire('draft_apply',{})
            with self.assertRaises(ValueError):acquire('query',{'operation':'read'})

    def test_invalid_request_receipt_matches_live_error(self):
        from contextbase_runtime.evidence import EvidenceRequestError
        request={'operation':'read','path':'missing.cs','startLine':1,'endLine':1}
        try:self.access.handle(request)
        except EvidenceRequestError as error:expected=self.access.error_reply(request,error)
        with replay_evidence(self.access) as acquire:
            reply,pairs=acquire('read',{k:v for k,v in request.items() if k!='operation'})
        self.assertEqual(expected,reply);self.assertEqual([{'request':request,'reply':reply}],pairs)
