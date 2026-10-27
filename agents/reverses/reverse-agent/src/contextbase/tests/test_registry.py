from __future__ import annotations
import json
import tempfile
import unittest
from pathlib import Path
from contextbase.registry import configure,resolve_profile,process_env,digest
from contextbase.discovery import probe
from contextbase.generic import extract


class IsolationTests(unittest.TestCase):
    def make(self):
        temp=tempfile.TemporaryDirectory();self.addCleanup(temp.cleanup);root=Path(temp.name);(root/'input').mkdir();return root
    def test_default_config(self):
        root=self.make();self.assertEqual(configure(root)['profile'],'auto')
    def test_target_code_never_imported(self):
        root=self.make();p=root/'input/a.py';p.write_text('raise RuntimeError("do not execute")\ndef f():\n return 1\n')
        cfg=configure(root);self.assertEqual(probe(root,cfg)['languages'],{'Python':1})
        self.assertEqual(extract(p.read_text(),'a.py','Python')['symbols'][0]['name'],'f')
    def test_input_cannot_overlap_src(self):
        root=self.make();(root/'src').mkdir();(root/'config').mkdir();(root/'config/project.toml').write_text('[project]\ninput="src"')
        with self.assertRaises(ValueError):configure(root)
    def test_detect_cross_language_stack(self):
        root=self.make()
        for name in ['old.vbp','Form.frm','lib.bas','data.accdb','Api.java','Api.csproj','View.vue','server.ts']:(root/'input'/name).write_text('placeholder')
        survey=probe(root,configure(root))
        for name in ['VB6','Access','Java','.NET','Vue']:self.assertIn(name,survey['families'])
        self.assertEqual(next(x for x in survey['inventory'] if x['path']=='data.accdb')['status'],'requires_export')
    def test_wrong_target_cannot_load_profile(self):
        root=self.make();d=root/'src-dynamic/example';d.mkdir(parents=True);(root/'input/a.vbp').write_text('different')
        (d/'manifest.json').write_text(json.dumps({'id':'example','schema_version':1,'trust':'repository-reviewed','anchors':[{'path':'a.vbp','sha256':digest(b'original')}]}))
        cfg=configure(root);self.assertIsNone(resolve_profile(root,cfg));cfg['profile']='example'
        with self.assertRaises(ValueError):resolve_profile(root,cfg)
    def test_matching_profile_is_data_only(self):
        root=self.make();d=root/'src-dynamic/example';d.mkdir(parents=True);(root/'input/a.vbp').write_text('original')
        (d/'manifest.json').write_text(json.dumps({'id':'example','schema_version':1,'trust':'repository-reviewed','anchors':[{'path':'a.vbp','sha256':digest(b'original')}]}))
        (d/'__init__.py').write_text('raise RuntimeError("must not import")')
        profile=resolve_profile(root,configure(root));self.assertEqual(profile['id'],'example')
        env=process_env(root,profile);self.assertNotIn(str(root/'input'),env['PYTHONPATH'])
    def test_plugin_path_escape_rejected(self):
        root=self.make()
        with self.assertRaises(ValueError):process_env(root,{'directory':str(root/'input')})
    def test_source_symlink_not_followed(self):
        root=self.make();(root/'secret.py').write_text('secret')
        try:(root/'input/link.py').symlink_to(root/'secret.py')
        except OSError:self.skipTest('symlinks unavailable')
        self.assertEqual(probe(root,configure(root))['inventory'][0]['status'],'excluded')
    def test_vue_properties_and_script(self):
        value='<template><input name="term" v-model="term" maxlength="20" required><button @click="search">Go</button></template>\n<script lang="ts">function search() { return 1; }</script>'
        a=extract(value,'Search.vue','Vue')
        self.assertEqual(a['items'][0]['length'],'20');self.assertEqual(a['items'][1]['role'],'operation')
        self.assertEqual(a['events'][0]['handler'],'search');self.assertEqual(a['symbols'][0]['name'],'search')
    def test_vb6_vba_text_does_not_claim_full_coverage(self):
        a=extract('Begin VB.CommandButton cmdSave\nEnd\nPrivate Sub cmdSave_Click()\nEnd Sub\n','Form.frm','VB6 form')
        self.assertEqual(a['items'][0]['role'],'operation');self.assertEqual(a['symbols'][0]['name'],'cmdSave_Click');self.assertEqual(a['status'],'partial')
    def test_java_dotnet_python_core_adapters(self):
        for language,path,text in [('Java','A.java','class A { public int Run(){ return 1; } }'),('C#','A.cs','class A { public int Run(){ return 1; } }'),('Python','a.py','def run():\n return 1')]:
            with self.subTest(language=language):self.assertTrue(extract(text,path,language)['symbols'])
    def test_access_binary_not_mistaken_for_text(self):
        root=self.make();(root/'input/db.mdb').write_bytes(b'\x00\xffJetDb')
        s=probe(root,configure(root));self.assertEqual(s['source_files'],1);self.assertEqual(s['inventory'][0]['status'],'requires_export')
    def test_json_only_manifest_requires_explicit_trust(self):
        root=self.make();p=root/'src-dynamic/unreviewed';p.mkdir(parents=True)
        (p/'manifest.json').write_text('{"id":"unreviewed","schema_version":1,"anchors":[]}')
        with self.assertRaises(ValueError):resolve_profile(root,configure(root))

if __name__=='__main__':unittest.main()
