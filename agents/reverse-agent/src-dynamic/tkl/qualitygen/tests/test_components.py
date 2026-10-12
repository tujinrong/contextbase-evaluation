from pathlib import Path
import unittest
from qualitygen.ui_components import enrich_layout

class ComponentTests(unittest.TestCase):
    def test_viewer_is_not_a_business_input(self):
        data={'records':{'a.xaml':{'nodes':[{'tag':'Viewer','attrs':{'x:Name':'rptv'},'line':6}]}}}
        text=enrich_layout('<main></main>',{'source':'a.xaml'},data)
        self.assertIn('data-component="rptv"',text)
        self.assertNotIn('data-item=',text)
    def test_invalid_quantity_uses_supplied_previous_amount(self):
        source=(Path(__file__).parents[1]/'templates/Rebuilt.vb.in').read_text()
        self.assertIn('previousAmount As Integer',source)
        self.assertNotIn('-987',source)

if __name__=='__main__':unittest.main()
