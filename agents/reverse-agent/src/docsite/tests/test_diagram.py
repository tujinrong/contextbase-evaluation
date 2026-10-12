import unittest
from bs4 import BeautifulSoup
from docsite.diagram import parse,render

class DiagramTests(unittest.TestCase):
    def test_database_node_and_read_write_edges(self):
        g=parse('flowchart LR\n F["保存"]\n D[("顧客")]\n D -->|参照| F\n F -->|更新| D\n')
        self.assertEqual(g['nodes']['D']['shape'],'cylinder');self.assertEqual(len(g['edges']),2)
        self.assertEqual(g['edges'][0]['label'],'参照')
    def test_deferred_registration_is_dashed(self):
        g=parse('flowchart LR\n E -. 登録のみ .-> C["後続処理"]')
        self.assertTrue(g['edges'][0]['dashed']);self.assertEqual(g['edges'][0]['label'],'登録のみ')
    def test_unsupported_mermaid_is_not_silently_dropped(self):
        with self.assertRaises(ValueError):parse('sequenceDiagram\n A->>B: request')
    def test_click_directive_is_rejected(self):
        with self.assertRaises(ValueError):parse('flowchart LR\n A["画面"]\n click A "https://example.com"')
    def test_conflicting_label_rejected(self):
        with self.assertRaises(ValueError):parse('flowchart LR\n A["保存"]\n A["検索"]')
    def test_svg_has_all_nodes_edges_and_namespaced_ids(self):
        s=render('flowchart LR\n A["入力"] --> B["保存"]','test1')
        soup=BeautifulSoup(s,'html.parser')
        self.assertEqual(len(soup.select('g.node')),2);self.assertEqual(len(soup.select('g.edge')),1)
        self.assertTrue(all(x['id'].startswith('test1-') for x in soup.find_all(id=True)))

if __name__=='__main__':unittest.main()
