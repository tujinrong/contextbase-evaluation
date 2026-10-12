import tempfile,unittest
from pathlib import Path
from overviewgen.core import save,digest
from qualitygen.native_checks import validate,inputs

class NativeEvidenceTests(unittest.TestCase):
    def fixture(self,root):
        base=root/'pilot/TKL-011';rep=root/'report/pilot'
        for folder in ['spec-input','reference','reimplementation','harness']:(base/folder).mkdir(parents=True)
        save(base/'Pilot.vbproj','project');save(base/'NuGet.Config','nuget');save(base/'reimplementation/a.vb','source')
        save(base/'harness/test-plan.json',{'family_counts':{'sample':1}})
        value={'run_id':'case-id','status':'subset_pass','cases':1,'passed':1,'failed':0,'results':[{'case':'A','family':'sample','passed':True}]}
        save(rep/'native-result.json',value)
        binding={'run_id':'case-id','status':'executed','inputs':inputs(base),'result_sha256':digest((rep/'native-result.json').read_bytes())}
        save(rep/'execution-binding.json',binding)
        return base,rep,value,binding
    def test_valid_evidence(self):
        with tempfile.TemporaryDirectory() as t:
            r=Path(t);self.fixture(r);self.assertEqual(validate(r)['cases'],1)
    def test_source_changed_after_execution(self):
        with tempfile.TemporaryDirectory() as t:
            r=Path(t);b,p,v,m=self.fixture(r);save(b/'reimplementation/a.vb','changed')
            with self.assertRaises(ValueError):validate(r)
    def test_result_changed(self):
        with tempfile.TemporaryDirectory() as t:
            r=Path(t);b,p,v,m=self.fixture(r);v['passed']=99;save(p/'native-result.json',v)
            with self.assertRaises(ValueError):validate(r)
    def test_pending_not_passed(self):
        with tempfile.TemporaryDirectory() as t:
            r=Path(t);b,p,v,m=self.fixture(r);m['status']='pending';save(p/'execution-binding.json',m)
            with self.assertRaises(ValueError):validate(r)
    def test_wrong_run_identity(self):
        with tempfile.TemporaryDirectory() as t:
            r=Path(t);b,p,v,m=self.fixture(r);m['run_id']='another-run';save(p/'execution-binding.json',m)
            with self.assertRaises(ValueError):validate(r)
    def test_case_family_cannot_be_removed(self):
        with tempfile.TemporaryDirectory() as t:
            r=Path(t);b,p,v,m=self.fixture(r);v['results'][0]['family']='other';save(p/'native-result.json',v)
            m['result_sha256']=digest((p/'native-result.json').read_bytes());save(p/'execution-binding.json',m)
            with self.assertRaises(ValueError):validate(r)

if __name__=='__main__':unittest.main()
