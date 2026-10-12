import json,tempfile,unittest
from pathlib import Path
from qualitygen.spec_revision import EVENT_CONTRACT
from qualitygen.pilot_extension import generate_events

class EventContractTests(unittest.TestCase):
    def prepare(self,root,value):
        (root/'概要仕様書TKL-011_特別出版注文入力.md').write_text('```json\n'+json.dumps(value)+'\n```',encoding='utf-8')
    def test_no_source_dependency(self):
        with tempfile.TemporaryDirectory() as t:
            p=Path(t);self.prepare(p,EVENT_CONTRACT)
            r=generate_events(p,p/'result',Path(__file__).parents[1]/'templates')
            self.assertEqual(r['source_access'],'none');self.assertNotIn('@GUARDED@',(p/'result/Events.vb').read_text())
    def test_new_ignored_contract_field_not_silently_accepted(self):
        with tempfile.TemporaryDirectory() as t:
            p=Path(t);self.prepare(p,{**EVENT_CONTRACT,'truncate_ratio':True})
            with self.assertRaises(ValueError):generate_events(p,p/'result',Path(__file__).parents[1]/'templates')
    def test_unguarded_change_rejected(self):
        with tempfile.TemporaryDirectory() as t:
            p=Path(t);self.prepare(p,{**EVENT_CONTRACT,'guarded_events':['rate','discount','book','calculate']})
            with self.assertRaises(ValueError):generate_events(p,p/'result',Path(__file__).parents[1]/'templates')

if __name__=='__main__':unittest.main()
