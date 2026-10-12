import unittest
from overviewgen.contexts import filter_display_mappings,layout_order

class ContextTests(unittest.TestCase):
    def test_same_name_other_model_is_not_confirmed(self):
        item={'is_column':True,'db':[{'object':'customer','column':'updated','path':'customer.vb','direction':'read'},{'object':'history','column':'updated','path':'history.vb','direction':'read'}]}
        filter_display_mappings(item,'history.vb')
        self.assertEqual([x['object'] for x in item['db']],['history'])
        self.assertEqual(len(item['db_candidates']),1)
    def test_unknown_context_preserves_candidates(self):
        item={'is_column':True,'db':[{'object':'data','column':'id','path':'x.vb','direction':'write'}]}
        filter_display_mappings(item,None)
        self.assertEqual(item['db'],[]);self.assertEqual(item['db_status'],'unresolved')
        self.assertEqual(len(item['db_candidates']),1)
    def test_right_aligned_button_after_left_button(self):
        nodes=[{'attrs':{},'line':1,'parent':None},{'attrs':{'Margin':'5,5,0,0'},'line':2,'parent':0},{'attrs':{'Style':'{StaticResource close}'},'line':3,'parent':0}]
        styles={'close':{'values':{'Margin':'5,5,5,5','HorizontalAlignment':'Right'},'base':'','handlers':[],'path':'s.xaml','line':1}}
        self.assertLess(layout_order({'nodes':nodes},{'node':1},styles),layout_order({'nodes':nodes},{'node':2},styles))

if __name__=='__main__':unittest.main()
