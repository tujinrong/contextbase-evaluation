from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from specgen.analyze import analyze
from specgen.common import decode_source, digest, safe_id
from specgen.engine import config, inventory, projects, run
from specgen.sql import sql_facts


class ParserTests(unittest.TestCase):
    def test_python_flow_and_nested_scope(self):
        code = 'def outer(x: int) -> int:\n    """増分を返す。"""\n    def inner():\n        return 99\n    if x < 0:\n        raise ValueError("x")\n    return x + 1\n'
        out = analyze(code, 'input/p/a.py', 'Python')
        outer, inner = out['symbols']
        self.assertEqual(outer['name'], 'outer')
        self.assertEqual(inner['name'], 'outer.inner')
        self.assertEqual([s['kind'] for s in outer['steps']], ['If', 'Raise', 'Return'])
        self.assertEqual(outer['steps'][0]['line'], 5)
        self.assertEqual(outer['returns'], 'int')

    def test_python_route_prefix(self):
        code = 'router = APIRouter(prefix="/api")\n@router.get("/orders")\ndef list_orders(limit:int=10):\n    return []\n'
        out = analyze(code, 'a.py', 'Python')
        route = out['symbols'][0]['routes'][0]
        self.assertEqual(route['path'], '/api/orders')
        self.assertEqual(route['line'], 2)

    def test_python_orm_explicit_only(self):
        out = analyze('class Order:\n    __tablename__="orders"\n    id=Column(Integer, primary_key=True, nullable=False)\n', 'a.py', 'Python')
        self.assertEqual(out['tables'][0]['name'], 'orders')
        self.assertEqual(out['tables'][0]['columns'][0]['nullable'], 'NOT NULL')
        self.assertFalse(analyze('class Order:\n    id:int\n', 'a.py', 'Python')['tables'])

    def test_syntax_error(self):
        self.assertEqual(analyze('def broken(:', 'a.py', 'Python')['status'], 'error')

    def test_brace_languages(self):
        cases = [
            ('Java', 'class Order { public int total(int n) { if(n<0) { throw new IllegalArgumentException(); } return n; } }'),
            ('C#', 'class Order { [HttpGet("orders")] public int total(int n) { return n; } }'),
            ('JavaScript', 'export function total(n) { const text="}"; return n; }'),
            ('TypeScript', 'export function total(n:number):number { return n; }'),
        ]
        for language, code in cases:
            with self.subTest(language=language):
                out = analyze(code, 'a', language)
                self.assertEqual(out['status'], 'partial')
                self.assertEqual(out['symbols'][0]['name'], 'total')
                self.assertTrue(out['warnings'])

    def test_arrow(self):
        out = analyze('const total = (n:number) => { return n+1; };', 'a.ts', 'TypeScript')
        self.assertEqual(out['symbols'][0]['name'], 'total')

    def test_decrement_does_not_hide_closing_brace(self):
        out = analyze('class X { int count(int n) { n--; return n; } }', 'a.java', 'Java')
        self.assertEqual(len(out['symbols']), 1)

    def test_sql_decimal_defaults_keys_and_comments(self):
        code = "-- CREATE TABLE fake(id int);\nCREATE TABLE orders (id INT NOT NULL, amount DECIMAL(12,2) DEFAULT 1.0, note TEXT DEFAULT 'a,b', PRIMARY KEY(id), FOREIGN KEY (id) REFERENCES parent(id));\nCREATE INDEX ix ON orders(id);"
        tables, _, warnings = sql_facts(code)
        self.assertEqual(len(tables), 1)
        self.assertEqual(len(tables[0]['columns']), 3)
        self.assertEqual(tables[0]['columns'][1]['type'], 'DECIMAL(12,2)')
        self.assertEqual(tables[0]['columns'][2]['default'], "'a,b'")
        self.assertTrue(tables[0]['columns'][0]['primary_key'])
        self.assertEqual(len(tables[0]['indexes']), 1)
        self.assertFalse(warnings)

    def test_sql_crud_and_literal_masking(self):
        _, refs, _ = sql_facts("SELECT 'FROM fake' FROM orders; INSERT INTO orders(id) VALUES(1); UPDATE orders SET id=2; DELETE FROM orders;")
        self.assertEqual({r['table'] for r in refs}, {'orders'})
        self.assertEqual({r['operation'] for r in refs}, {'C', 'R', 'U', 'D'})

    def test_sql_cte(self):
        _, refs, _ = sql_facts('WITH selected AS (SELECT * FROM orders) SELECT * FROM selected')
        self.assertEqual([r['table'] for r in refs], ['orders'])

    def test_alter_not_silently_applied(self):
        tables, _, warnings = sql_facts('CREATE TABLE a(id INT); ALTER TABLE a ADD name TEXT;')
        self.assertEqual(len(tables[0]['columns']), 1)
        self.assertTrue(warnings)

    def test_dynamic_sql_warning(self):
        out = analyze('def query(table):\n    return f"SELECT * FROM {table}"\n', 'a.py', 'Python')
        self.assertTrue(out['warnings'])
        self.assertFalse(out['tables'])

    def test_sql_keywords_inside_default_are_not_constraints(self):
        tables, refs, _ = sql_facts("CREATE TABLE a(note TEXT DEFAULT 'NOT NULL PRIMARY KEY', id INT REFERENCES b(id) ON UPDATE CASCADE);")
        column = tables[0]['columns'][0]
        self.assertFalse(column['primary_key'])
        self.assertEqual(column['nullable'], '未明記（DB方言依存）')
        self.assertEqual(column['default'], "'NOT NULL PRIMARY KEY'")
        self.assertFalse(refs)

    def test_java_named_route_annotation(self):
        out = analyze('class X { @GetMapping(path="/orders") public int total() { return 1; } }', 'a.java', 'Java')
        self.assertEqual(out['symbols'][0]['name'], 'total')

    def test_nullability_not_inferred_from_default_check_or_primary_key(self):
        tables, _, _ = sql_facts("CREATE TABLE a(id INT PRIMARY KEY, label TEXT DEFAULT NULL, amount INT CHECK(amount IS NOT NULL));")
        for column in tables[0]['columns']:
            self.assertEqual(column['nullable'], '未明記（DB方言依存）')

    def test_encoding(self):
        text = '日本語'
        self.assertEqual(decode_source(text.encode('cp932'))[0], text)
        self.assertEqual(decode_source(text.encode('utf-16'))[0], text)
        with self.assertRaises(ValueError):
            decode_source(b'\0\x01\x02')

    def test_safe_names(self):
        self.assertNotEqual(safe_id('a/b.py'), safe_id('a_b.py'))
        self.assertNotIn('/', safe_id('../../input'))


class EngineTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / 'input/p').mkdir(parents=True)
        self.source = self.root / 'input/p/orders.py'
        self.source.write_text('def total(x:int)->int:\n    """合計を返す。"""\n    return x\n', encoding='utf-8')
        self.cfgfile = self.root / 'specgen.toml'
        self.cfgfile.write_text('input="input"\noutput="output"\nqa="qa"\nreport="report"\nstate=".specgen-state"\n', encoding='utf-8')
        self.cfg = config(self.root, 'specgen.toml')

    def generate(self, **kwargs):
        return run(self.root, self.cfg, **kwargs)

    def test_generate_all_documents_and_source_unchanged(self):
        original = self.source.read_bytes()
        result = self.generate()
        self.assertEqual(result['exit_code'], 0)
        for name in ['基本設計書.md', '詳細仕様書.md', 'テーブル仕様書.md']:
            self.assertEqual(len(list((self.root / 'output').rglob(name))), 1)
        doc = next((self.root / 'output').rglob('詳細仕様書.md')).read_text(encoding='utf-8')
        self.assertIn('#L1-L3', doc)
        self.assertIn('return x', doc)
        self.assertEqual(self.source.read_bytes(), original)

    def test_warm_resume_and_no_doc_rewrite(self):
        self.generate()
        files = list((self.root / 'output').rglob('*.md'))
        before = {p: p.stat().st_mtime_ns for p in files}
        result = self.generate()
        self.assertEqual(result['cached'], 1)
        self.assertEqual(result['parsed'], 0)
        self.assertEqual(before, {p: p.stat().st_mtime_ns for p in files})

    def test_changed_source_is_reparsed(self):
        self.generate()
        self.source.write_text('def next_value(x):\n    return x+1\n', encoding='utf-8')
        result = self.generate()
        self.assertEqual(result['parsed'], 1)
        self.assertEqual(result['cached'], 0)

    def test_failed_file_is_retried(self):
        self.source.write_text('def bad(:', encoding='utf-8')
        self.assertEqual(self.generate()['errors'], 1)
        self.assertEqual(self.generate()['cached'], 0)
        self.source.write_text('def good():\n    return 1\n', encoding='utf-8')
        self.assertEqual(self.generate()['errors'], 0)

    def test_corrupt_cache_recovers(self):
        self.generate()
        cache = next((self.root / '.specgen-state/files').glob('*.json'))
        cache.write_text('invalid JSON', encoding='utf-8')
        self.assertEqual(self.generate()['parsed'], 1)

    def test_manual_edits_protected_and_force(self):
        self.generate()
        doc = next((self.root / 'output').rglob('基本設計書.md'))
        doc.write_text('手動編集', encoding='utf-8')
        result = self.generate()
        self.assertEqual(result['status'], 'conflict')
        self.assertEqual(doc.read_text(encoding='utf-8'), '手動編集')
        self.assertEqual(self.generate(force=True)['exit_code'], 0)
        self.assertNotEqual(doc.read_text(encoding='utf-8'), '手動編集')

    def test_excluded_symlink_and_dependency(self):
        (self.root / 'input/p/node_modules').mkdir()
        (self.root / 'input/p/node_modules/bad.js').write_text('!bad!', encoding='utf-8')
        outside = self.root / 'outside.py'
        outside.write_text('raise RuntimeError("must not run")', encoding='utf-8')
        try:
            (self.root / 'input/p/link.py').symlink_to(outside)
        except OSError:
            self.skipTest('Symlink privilege unavailable on this system')
        result = self.generate()
        self.assertEqual(result['parsed'], 1)
        report = (self.root / 'report/p/解析報告.md').read_text(encoding='utf-8')
        self.assertIn('symlink', report)
        self.assertIn('除外ディレクトリ', report)

    def test_input_never_executed(self):
        target = self.root / 'should_not_exist'
        self.source.write_text(f'from pathlib import Path\nPath({str(target)!r}).touch()\ndef hello():\n    pass\n', encoding='utf-8')
        self.generate()
        self.assertFalse(target.exists())

    def test_empty_and_strict(self):
        self.source.unlink()
        result = self.generate(strict=True)
        self.assertEqual(result['status'], 'empty')
        self.assertEqual(result['exit_code'], 1)
        self.assertFalse(list((self.root / 'output').rglob('基本設計書.md')))

    def test_nested_project_and_feature_mapping(self):
        (self.root / 'input/p/backend').mkdir()
        self.source.rename(self.root / 'input/p/backend/orders.py')
        self.cfg['projects'] = [dict(name='backend', path='p/backend')]
        self.cfg['features'] = [dict(id='orders', name='受注', project='backend', paths=['**/*.py'])]
        self.generate()
        self.assertTrue((self.root / 'output/backend/機能/orders/基本設計書.md').exists())

    def test_invalid_overlapping_roots(self):
        self.cfgfile.write_text('input="input"\noutput="input/generated"\n', encoding='utf-8')
        with self.assertRaises(ValueError):
            config(self.root, 'specgen.toml')

    def test_limit_and_strict_partial(self):
        self.cfg['max_file_bytes'] = 4
        self.assertEqual(self.generate()['exit_code'], 1)
        self.cfg['max_file_bytes'] = 10000
        self.source.unlink()
        (self.root / 'input/p/a.cs').write_text('class X { int a(){return 1;} }', encoding='utf-8')
        self.assertEqual(self.generate(strict=True)['exit_code'], 1)

    def test_lock_and_release(self):
        lock = self.root / '.specgen-state.lock'
        lock.write_text('another process', encoding='utf-8')
        with self.assertRaises(ValueError):
            self.generate()
        lock.unlink()
        self.generate()
        self.assertFalse(lock.exists())

    def test_interruption_retains_cache(self):
        with patch('specgen.engine.group_features', side_effect=KeyboardInterrupt):
            with self.assertRaises(KeyboardInterrupt):
                self.generate()
        self.assertTrue(list((self.root / '.specgen-state/files').glob('*.json')))
        self.assertEqual(self.generate()['cached'], 1)

    def test_output_symlink_cannot_overwrite_input(self):
        self.generate()
        folder = self.root / 'output/p/機能'
        import shutil
        shutil.rmtree(folder)
        try:
            folder.symlink_to(self.root / 'input/p', target_is_directory=True)
        except OSError:
            self.skipTest('Symlink privilege unavailable on this system')
        with self.assertRaises(ValueError):
            self.generate(force=True)

    def test_tampered_cleanup_manifest_cannot_delete_input(self):
        self.generate()
        target = self.root / 'input/p/business.md'
        target.write_text('source document', encoding='utf-8')
        manifest = self.root / '.specgen-state/outputs.json'
        data = json.loads(manifest.read_text(encoding='utf-8'))
        data['input/p/business.md'] = digest(target.read_bytes())
        manifest.write_text(json.dumps(data), encoding='utf-8')
        self.generate(clean=True)
        self.assertTrue(target.exists())

    def test_valid_json_but_corrupt_cache_is_rebuilt(self):
        self.generate()
        cache = next((self.root / '.specgen-state/files').glob('*.json'))
        data = json.loads(cache.read_text(encoding='utf-8'))
        data['analysis'] = 'invalid'
        cache.write_text(json.dumps(data), encoding='utf-8')
        self.assertEqual(self.generate()['parsed'], 1)

    def test_edited_run_report_sets_failure_exit(self):
        self.generate()
        (self.root / 'report/実行結果.json').write_text('manual edit', encoding='utf-8')
        result = self.generate()
        self.assertEqual(result['exit_code'], 1)
        self.assertEqual(result['status'], 'conflict')

    def test_clean_only_owned_unchanged_files(self):
        self.generate()
        old = next((self.root / 'output').rglob('基本設計書.md'))
        custom = self.root / 'output/custom.md'
        custom.write_text('user', encoding='utf-8')
        self.source.unlink()
        self.generate(clean=True)
        self.assertFalse(old.exists())
        self.assertTrue(custom.exists())


if __name__ == '__main__':
    unittest.main()
