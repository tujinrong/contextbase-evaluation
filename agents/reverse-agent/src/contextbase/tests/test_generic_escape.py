from pathlib import Path
import tempfile,unittest
from contextbase.generic import generate
from docsite.publish import build,check

class GenericEscapeTests(unittest.TestCase):
    def test_source_html_is_text_without_disabling_safety(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);(root/'input').mkdir()
            (root/'input/a.py').write_text('def render():\n    """Return <form><input onfocus="unsafe"></form>."""\n    return 1\n')
            cfg={'id':'generic','input':'input'};survey={'inventory':[{'path':'a.py','status':'selected','language':'Python'}],'languages':{'Python':1}}
            result=generate(root,cfg,survey);self.assertEqual(result['errors'],0)
            # No runtime source HTML is passed to the converter as an active tag.
            build(root);self.assertEqual(check(root)['status'],'pass')
    def test_canonical_profile_selection_does_not_import_input(self):
        import json,hashlib
        from contextbase.registry import resolve_profile
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);(root/'input').mkdir();(root/'input/package.json').write_text('{}')
            p=root/'src-dynamic/new';p.mkdir(parents=True)
            (p/'manifest.json').write_text(json.dumps({'schema_version':1,'id':'new','trust':'repository-reviewed','anchors':[{'path':'package.json','sha256':hashlib.sha256(b'{}').hexdigest()}],'pipeline':'canonical','generation_module':'newgen','test_suites':[]}))
            (root/'input/newgen.py').write_text('raise AssertionError("never execute")')
            self.assertEqual(resolve_profile(root,{'profile':'auto','input':'input'})['id'],'new')

if __name__=='__main__':unittest.main()
