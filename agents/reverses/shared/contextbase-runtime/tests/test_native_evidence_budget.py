"""Native evidence budgets preserve complete items and canonical legacy output."""
from copy import deepcopy
import json
from pathlib import Path
import tempfile
import unittest
from contextbase_runtime.evidence import EvidenceAccess
from contextbase_runtime.facts import FactIndex
from contextbase_runtime.adapters import index_source
from contextbase_runtime.sources import SourceAccess
from contextbase_runtime.storage import ArtifactStore
from contextbase_runtime.native_mcp import tool_result,encode_message


class NativeEvidenceBudgetTests(unittest.TestCase):
    def setUp(self):
        home=Path(__file__).resolve().parents[1]/'.tmp';home.mkdir(exist_ok=True)
        self.tmp=tempfile.TemporaryDirectory(dir=home);root=Path(self.tmp.name)
        source=root/'input';source.mkdir()
        self.lines=('\u8cc7\u6599\U0001f4a0'*100+' "\\value"\n')*100
        (source/'lines.txt').write_text(self.lines,encoding='utf-8',newline='')
        (source/'oversized.txt').write_text('\U0001f4a0'*10000+'\n',encoding='utf-8')
        self.source=SourceAccess.create(source,root/'snapshot',project_id='native-budget',allowed_paths=['.'],excluded_paths=[])
        self.index=FactIndex.open(self.source,ArtifactStore(root/'cache'),parser=index_source)
        self.task={'id':'budget','contextId':'native','snapshotId':self.source.snapshot_id}

    def tearDown(self):self.tmp.cleanup()

    def test_native_utf8_pages_keep_complete_lines_and_reproduce_receipts(self):
        from contextbase_runtime.native_evidence import native_access,reply_size
        native=native_access(self.source,self.index,self.task)
        request={'operation':'read','path':'lines.txt','startLine':1,'endLine':None}
        legacy=EvidenceAccess(self.source,self.index,self.task).handle(request)
        first=native.handle(request)
        self.assertLess(first['result']['returnedCount'],legacy['result']['returnedCount'])
        self.assertNotIn('replyPolicy',legacy)
        self.assertEqual(28672,first['replyPolicy']['maxReplyBytes'])
        chunks=[]
        while True:
            reply=native.handle(request)
            self.assertLessEqual(reply_size(reply),28672)
            native.verify_reply(request,reply)
            chunks.append(reply['result']['sourceText'])
            if not reply['result']['truncated']:break
            self.assertGreater(reply['result']['nextLine'],request['startLine'])
            request={**request,'startLine':reply['result']['nextLine']}
        self.assertEqual(self.lines,''.join(chunks))
        self.assertEqual(legacy,EvidenceAccess(self.source,self.index,self.task).handle({'operation':'read','path':'lines.txt','startLine':1,'endLine':None}))

    def test_oversized_unicode_line_has_no_source_receipt_or_progress(self):
        from contextbase_runtime.native_evidence import native_access,reply_size
        request={'operation':'read','path':'oversized.txt','startLine':1,'endLine':None}
        legacy=EvidenceAccess(self.source,self.index,self.task).handle(request)
        self.assertEqual('ok',legacy['status'])
        reply=native_access(self.source,self.index,self.task).handle(request)
        self.assertEqual('oversized-item',reply['status'])
        self.assertEqual(0,reply['result']['returnedCount'])
        self.assertEqual(1,reply['result']['nextLine'])
        self.assertIsNone(reply['result']['evidence'])
        self.assertEqual('',reply['result']['sourceText'])
        self.assertLessEqual(reply_size(reply),28672)


class NativeSemanticBudgetTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from test_semantic_evidence import SemanticEvidenceTests
        SemanticEvidenceTests.setUpClass.__func__(cls)

    @classmethod
    def tearDownClass(cls):cls.temporary.cleanup()

    def test_query_capacity_includes_complete_semantic_diagnostics(self):
        from contextbase_runtime.semantic_calls import SemanticCallIndex
        from contextbase_runtime.native_evidence import native_access,reply_size
        from test_semantic_evidence import query
        document=deepcopy(self.semantic.document)
        for row in document['results']:
            row['status']='candidates'
            row['compilerStatus']='unresolved'
            row['bindingDiagnostics'].append('\u8b66\u544a'*1400)
        semantic=SemanticCallIndex(document,self.index)
        self.index.semantic_index=semantic
        task={'id':'native-semantic-budget','contextId':'context','snapshotId':self.source.snapshot_id,
              'sourceFactsSha256':self.index.sha256,'semanticPolicy':'contextbase-semantic-evidence/1','semanticIndexSha256':semantic.sha256}
        request=query(limit=100)
        legacy=EvidenceAccess(self.source,self.index,task).handle(request)
        native=native_access(self.source,self.index,task)
        reply=native.handle(request)
        self.assertLess(reply['result']['returnedCount'],legacy['result']['returnedCount'])
        self.assertLessEqual(reply_size(reply),28672)
        self.assertEqual(reply['result']['returnedCount'],len(reply['result']['semanticBindings']))
        self.assertTrue(all('\u8b66\u544a'*1400 in row['bindingDiagnostics']for row in reply['result']['semanticBindings']))
        native.verify_reply(request,reply)
        self.assertFalse(any(row['runtimeTargetConfirmed']for row in reply['result']['semanticBindings']))
