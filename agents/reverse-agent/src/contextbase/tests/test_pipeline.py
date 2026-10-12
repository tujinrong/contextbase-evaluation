from pathlib import Path
import tempfile,unittest
from unittest.mock import patch
from contextbase.pipeline import promote,hashes
from contextbase.registry import configure
from contextbase.discovery import probe
from contextbase.generic import generate
from docsite.publish import build,check

class PipelineTests(unittest.TestCase):
    def make(self):
        t=tempfile.TemporaryDirectory();self.addCleanup(t.cleanup);p=Path(t.name);(p/'input').mkdir();return p
    def test_all_input_files_including_build_assets_protected(self):
        p=self.make();(p/'input/bin').mkdir();(p/'input/bin/asset.dll').write_bytes(b'original')
        self.assertIn('bin/asset.dll',hashes(p/'input'))
    def test_replacement_requires_explicit_flag(self):
        p=self.make();(p/'output').mkdir();stage=p/'.contextbase-work/test';stage.mkdir(parents=True)
        with self.assertRaises(ValueError):promote(p,stage,False)
        self.assertTrue((p/'output').is_dir())
    def test_promotion_does_not_touch_input(self):
        p=self.make();(p/'input/a.vb').write_text('original');before=hashes(p/'input')
        (p/'output').mkdir();(p/'output/old.md').write_text('old')
        stage=p/'.contextbase-work/test';(stage/'output').mkdir(parents=True);(stage/'output/new.md').write_text('new')
        result=promote(p,stage,True)
        self.assertEqual(before,hashes(p/'input'));self.assertTrue((p/result['previous_copy']/'output/old.md').exists())
        self.assertTrue((p/'output/new.md').exists())
    def test_promotion_rolls_back_if_install_fails(self):
        p=self.make();(p/'output').mkdir();(p/'output/old.md').write_text('old');stage=p/'.contextbase-work/test';(stage/'output').mkdir(parents=True)
        original=Path.rename
        def fail(self,target):
            if self==stage/'output':raise OSError('injected failure')
            return original(self,target)
        with patch.object(Path,'rename',fail):
            with self.assertRaises(OSError):promote(p,stage,True)
        self.assertEqual((p/'output/old.md').read_text(),'old')
    def test_generic_end_to_end_has_no_previous_client_prose(self):
        p=self.make();(p/'input/Form.frm').write_text('Begin VB.TextBox txtCode\nEnd\nPrivate Sub Save_Click()\nEnd Sub\n')
        (p/'input/Search.vue').write_text('<template><input name="term" required><button @click="search">Search</button></template><script>function search(){return 1;}</script>')
        (p/'input/A.java').write_text('class A { public int get(){return 1;} }')
        cfg=configure(p);result=generate(p,cfg,probe(p,cfg));self.assertEqual(result['features'],3)
        build(p);report=check(p);self.assertFalse(report['errors'])
        for md in (p/'output/md').rglob('*.md'):
            self.assertNotIn('TKL',md.read_text());self.assertNotIn('特別出版',md.read_text())

if __name__=='__main__':unittest.main()
