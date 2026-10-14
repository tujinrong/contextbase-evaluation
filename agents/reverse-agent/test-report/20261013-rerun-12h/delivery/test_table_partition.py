import unittest
from bs4 import BeautifulSoup
from export_pdf import partition_markdown_tables

def fixture():
    raw='<!doctype html><html><head></head><body><h1>原順序</h1><table data-renderer-markdown="" data-renderer-columns="2"><colgroup><col style="width:24%"/><col style="width:76%"/></colgroup><thead><tr><th>ID</th><th>値</th></tr></thead><tbody><tr><td>001</td><td>=literal</td></tr><tr><td>2</td><td>1.0<br/>次行</td></tr><tr><td>3</td><td>元文字</td></tr></tbody></table><table><tr><td>画面表</td></tr></table></body></html>'
    # The trusted renderer canonicalizes fragments with this same serializer.
    return str(BeautifulSoup(raw,'html.parser'))

class TablePartitionTests(unittest.TestCase):
    def test_literal_rows_and_order_and_unmarked_table_unchanged(self):
        source=fixture();result,records=partition_markdown_tables(source,2)
        before=BeautifulSoup(source,'html.parser');after=BeautifulSoup(result,'html.parser')
        self.assertEqual([str(r) for r in before.select('table[data-renderer-markdown] tbody tr')],
                         [str(r) for r in after.select('table[data-renderer-markdown] tbody tr')])
        self.assertEqual(len(after.select('table[data-renderer-markdown]')),2)
        self.assertEqual(str(before.select('table')[-1]),str(after.select('table')[-1]))
        self.assertEqual(records[0]['parts'][1]['firstOriginalBodyRow'],3)
    def test_spanning_cell_refused(self):
        with self.assertRaisesRegex(ValueError,'Spanning'):
            partition_markdown_tables(fixture().replace('<td>001','<td rowspan="2">001'),2)
    def test_missing_marker_refused(self):
        with self.assertRaisesRegex(ValueError,'No parser-owned'):
            partition_markdown_tables('<html><table><tr><td>未確認表</td></tr></table></html>',2)

if __name__=='__main__':unittest.main()
