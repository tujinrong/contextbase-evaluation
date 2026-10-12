import json
from pathlib import Path
import tempfile
import unittest
from contextbase.delivery_policy import ReviewLog

class DeliveryPolicyTests(unittest.TestCase):
    def test_inference_is_explicit_and_facts_preserved(self):
        with tempfile.TemporaryDirectory() as d:
            review=ReviewLog(Path(d))
            record={'path':'Staff.cshtml','items':[{'name':'番号','role':'input','type':'text','required':True,'length':'8桁'}]}
            doc=review.delivery(record);row=doc['items'][0]
            self.assertTrue(row['required']);self.assertEqual('8桁',row['length'])
            self.assertIn('仮定 Q-',row['db']);self.assertNotIn('db',record['items'][0])

    def test_qa_answer_survives_regeneration(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);log=ReviewLog(root);qid=log.add('a','画面','質問','仮定');log.save()
            path=root/'QA/questions.json';v=json.loads(path.read_text());v['questions'][0].update(answer='回答',status='answered');path.write_text(json.dumps(v))
            log=ReviewLog(root);self.assertEqual(qid,log.add('a','画面','質問','仮定'));log.save()
            q=json.loads(path.read_text())['questions'][0];self.assertEqual('回答',q['answer']);self.assertEqual('answered',q['status'])

    def test_changed_assumption_preserves_answer_and_marks_recheck(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);log=ReviewLog(root);qid=log.add('a','画面','質問','旧');log.questions[qid]['answer']='回答';log.save()
            log=ReviewLog(root);log.add('a','画面','質問','新');log.save()
            self.assertEqual('recheck',log.questions[qid]['status']);self.assertEqual('回答',log.questions[qid]['answer'])

    def test_reports_not_in_delivery(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);log=ReviewLog(root);log.delivery({'path':'x','warnings':['UI-DYNAMIC: dynamic']});log.save()
            self.assertTrue((root/'QA/仕様確認.md').exists());self.assertTrue((root/'report/incomplete/未完成事項.md').exists());self.assertFalse((root/'output').exists())

    def test_button_has_no_inferred_required_or_db(self):
        with tempfile.TemporaryDirectory() as d:
            row=ReviewLog(Path(d)).delivery({'path':'x','items':[{'name':'保存','role':'operation'}]})['items'][0]
            self.assertNotIn('db',row);self.assertNotIn('required',row)

if __name__=='__main__':unittest.main()
