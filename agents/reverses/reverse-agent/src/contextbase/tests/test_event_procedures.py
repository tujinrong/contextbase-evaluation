"""Independent small control trees expose same-line and branch-flattening errors."""
import unittest
from contextbase.detail.event_templates import Narrator, flow_model
from contextbase.detail.procedures import procedure_steps


def fixture(tree):
    e={'id':'E1','name':'登録','methods':[{'name':'post','path':'Demo.java','line':1,'end_line':99,'flow':tree,'steps':[]}]}
    n=Narrator({'items':[],'dependencies':[]},e,{})
    n.routes['LOGIN']='ログイン画面'
    return n,e


def action(name,line=1):
    return {'kind':'call','expression':'repo.'+name+'(model)','line':line,'calls':[{'name':'repo.'+name,'arguments':'model'}]}


def ret(value='LOGIN',line=1):
    return {'kind':'return','value':value,'expression':'return '+value,'line':line}


class EventProcedureTests(unittest.TestCase):
    def test_getter_null_is_described_as_unset(self):
        n,e=fixture([]);n.labels['branchNo']='店番'
        self.assertEqual('「店番」が未設定',n.condition('value.getBranchNo() == null'))

    def test_getter_length_zero_is_described_as_empty(self):
        n,e=fixture([]);n.labels['kanaName']='フリガナ'
        self.assertEqual('「フリガナ」が空',n.condition('value.getKanaName().length() == 0'))

    def test_same_line_condition_precedes_return(self):
        n,e=fixture([{'kind':'if','condition':'missing == null','line':1,'body':[ret()]},action('save',2)])
        steps=flow_model(n,e)['steps']
        self.assertEqual(['if','return','call'],[s['kind'] for s in steps])
        self.assertEqual(['1','1.1','2'],[s['number'] for s in steps])
        self.assertIn('条件成立時',steps[1]['description'])
        self.assertIn('後続手順は実行しない',steps[1]['description'])
        self.assertNotIn('ログイン画面',steps[0]['description'])

    def test_source_sequence_not_numeric_line_sort(self):
        n,e=fixture([action('insert',9),action('update',2)])
        self.assertEqual([9,2],[s['line'] for s in procedure_steps(n,e)])

    def test_else_is_explicit_not_second_unconditional_action(self):
        n,e=fixture([{'kind':'if','line':1,'condition':'exists != null','body':[action('update')],'else':[action('insert')]}])
        steps=procedure_steps(n,e)
        self.assertEqual(['1','1.1','1-別.1'],[s['number'] for s in steps])
        self.assertIn('条件成立時',steps[1]['description'])
        self.assertIn('条件不成立時',steps[2]['description'])

    def test_duplicate_same_line_calls_are_not_deduplicated(self):
        n,e=fixture([action('save'),action('save')]);s=procedure_steps(n,e)
        self.assertEqual(2,len(s));self.assertEqual(['1','2'],[v['number'] for v in s])

    def test_loop_body_and_after_are_separate(self):
        n,e=fixture([{'kind':'while','condition':'remaining != null','line':1,'body':[action('update')]},action('save',3)])
        steps=procedure_steps(n,e)
        self.assertIn('繰り返す',steps[0]['description'])
        self.assertEqual('繰返しの各回',steps[1]['branch'])
        self.assertEqual('',steps[2]['branch'])

    def test_try_finally_shown_once_with_early_exit_note(self):
        n,e=fixture([{'kind':'try','line':1,'body':[ret()]},{'kind':'catch','line':2,'condition':'Exception ex','body':[action('delete')]},{'kind':'finally','line':3,'body':[action('close')]}])
        steps=procedure_steps(n,e)
        self.assertEqual(1,sum(s['kind']=='finally' for s in steps))
        self.assertIn('共通後処理を行ってから',next(s['description'] for s in steps if s['kind']=='return'))
        self.assertIn('例外条件',next(s['description'] for s in steps if s['kind']=='catch'))

    def test_flat_steps_keep_guards(self):
        n,e=fixture([])
        e['methods'][0]['steps']=[dict(action('save'),guards=['valid != null'])]
        s=procedure_steps(n,e)[0]
        self.assertIn('条件「',s['description']);self.assertIn('平坦抽出',s['branch'])

    def test_empty_method_uses_unresolved_not_invented_save(self):
        n,e=fixture([]);s=procedure_steps(n,e)
        self.assertEqual('unresolved',s[0]['kind']);self.assertNotIn('保存',s[0]['description'])

    def test_nested_branches_have_unique_hierarchical_numbers(self):
        n,e=fixture([{'kind':'if','line':1,'condition':'a != null','body':[{'kind':'if','line':1,'condition':'b != null','body':[action('insert')],'else':[ret()]}]}])
        nums=[s['number'] for s in procedure_steps(n,e)]
        self.assertEqual(['1','1.1','1.1.1','1.1-別.1'],nums)


if __name__=='__main__':unittest.main()
