"""Canonical evidence batching has a real serialized MCP UTF-8 byte budget."""
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from contextbase_runtime.adapters import index_source
from contextbase_runtime.evidence import EvidenceAccess
from contextbase_runtime.facts import FactIndex
from contextbase_runtime.sources import SourceAccess
from contextbase_runtime.storage import ArtifactStore
from contextbase_runtime.native_evidence import run_batch


def query(**changes):
    return {'operation':'query','offset':0,'limit':100,'path':None,'kind':'call',
            'text':None,'caller':None,'callee':None,'route':None,**changes}


class NativeBatchTests(unittest.TestCase):
    def setUp(self):
        home=Path(__file__).resolve().parents[1]/'.tmp';home.mkdir(exist_ok=True)
        self.tmp=tempfile.TemporaryDirectory(dir=home);root=Path(self.tmp.name)
        source=root/'input';source.mkdir()
        (source/'A.cs').write_text('class A { void Go() { Write(); } void Write() {} }\n',encoding='utf-8')
        (source/'unicode.txt').write_text('\u8cc7\u6599\U0001f4a0'*1000+'\n',encoding='utf-8')
        self.source=SourceAccess.create(source,root/'snapshot',project_id='native-batch',allowed_paths=['.'],excluded_paths=[])
        self.index=FactIndex.open(self.source,ArtifactStore(root/'cache'),parser=index_source)
        self.task={'id':'native-query','contextId':'native-context','snapshotId':self.source.snapshot_id}
        self.access=EvidenceAccess(self.source,self.index,self.task)

    def tearDown(self):self.tmp.cleanup()

    def test_multibyte_result_budget_counts_full_encoded_mcp_result(self):
        requests=[{'operation':'read','path':'unicode.txt','startLine':1,'endLine':1}]
        from contextbase_runtime.native_mcp import tool_result,encode_message
        full,_=run_batch(self.access,requests,lambda:True)
        payload=encode_message(tool_result(full))
        self.assertLess(len(payload.decode('utf-8')),6500)
        self.assertGreater(len(payload),6500)
        reply,pairs=run_batch(self.access,requests,lambda:True,max_bytes=6500)
        self.assertEqual([],pairs)
        self.assertEqual(0,reply['next_request_index'])
        from contextbase_runtime.native_mcp import tool_result,encode_message
        self.assertLessEqual(len(encode_message(tool_result(reply))),6500)

    def test_batch_replies_are_exact_canonical_and_fenced_once(self):
        requests=[query(),{'operation':'read','path':'A.cs','startLine':1,'endLine':1}]
        with patch.object(self.access,'handle',side_effect=AssertionError('batch must not enter per-item fences')):
            reply,pairs=run_batch(self.access,requests,lambda:True)
        self.assertIsNone(reply['next_request_index'])
        self.assertEqual(2,len(pairs))
        self.assertEqual(reply['replies'],pairs)
        for pair in pairs:self.access.verify_reply(pair['request'],pair['reply'])
        from contextbase_runtime.native_mcp import tool_result,encode_message
        self.assertLessEqual(len(encode_message(tool_result(reply))),32768)

    def test_prefix_boundary_is_whole_and_unreturned_requests_have_no_receipts(self):
        from contextbase_runtime.native_mcp import tool_result,encode_message
        requests=[{'operation':'read','path':'unicode.txt','startLine':1,'endLine':1},query()]
        full,pairs=run_batch(self.access,requests,lambda:True)
        budget=len(encode_message(tool_result(full)))-128
        partial,returned=run_batch(self.access,requests,lambda:True,max_bytes=budget)
        self.assertEqual(1,partial['next_request_index'])
        self.assertEqual(pairs[:1],returned)
        self.assertEqual(returned,partial['replies'])
        self.assertLessEqual(len(encode_message(tool_result(partial))),budget)

    def test_batch_limit_cancel_and_source_mutation_reject(self):
        with self.assertRaises(ValueError):run_batch(self.access,[query()]*9,lambda:True)
        with self.assertRaises(ValueError):run_batch(self.access,[{'operation':'inventory','offset':0,'limit':1}],lambda:True)
        checks=iter([True,True,False])
        with self.assertRaisesRegex(RuntimeError,'cancel'):
            run_batch(self.access,[query(),query()],lambda:next(checks,False))
        path=self.source.root/'sources'/'A.cs';raw=path.read_bytes();response=self.access._response
        def mutate(request,**kwargs):
            result=response(request,**kwargs);path.write_bytes(raw+b'// mutation');return result
        try:
            with patch.object(self.access,'_response',side_effect=mutate):
                with self.assertRaises(ValueError):run_batch(self.access,[query()],lambda:True)
        finally:path.write_bytes(raw)

    def test_http_broker_uses_identical_tool_result_encoding(self):
        from contextbase_runtime.native_mcp import Broker, tool_result, encode_message
        from test_native_mcp import rpc
        requests=[{'operation':'read','path':'unicode.txt','startLine':1,'endLine':1}]
        value,_=run_batch(self.access,requests,lambda:True)
        with Broker([{'name':'batch','description':'Fixture batch','inputSchema':{'type':'object'}}],lambda name,args:value) as broker:
            result=rpc(broker.connection,'tools/call',{'name':'batch','arguments':{}})['result']
        self.assertEqual(tool_result(value),result)
        self.assertEqual(encode_message(tool_result(value)),encode_message(result))
        self.assertLessEqual(len(encode_message(result)),131072)
