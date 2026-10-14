import unittest
from node_label_row_gate_r03 import prove_node_rows, NodeLabelProofError, literal_label


class NodeRows(unittest.TestCase):
    def fixture(self, literal, rows, **changes):
        vertex = {'id':'A','domId':'flowchart-A-0','text':literal,'labelType':'text'}
        vertex.update(changes)
        actual = {'id':'flowchart-A-0','bounds':{'x':0,'y':0,'width':500,'height':300},
                  'rows':[{'text':t,'bounds':{'x':10,'y':10+i*20,'width':300,'height':16},
                           'visibility':'visible','display':'inline','opacity':1} for i,t in enumerate(rows)]}
        return [vertex], [actual], {'x':0,'y':0,'width':600,'height':400}

    def good(self, literal, rows, **changes):
        return prove_node_rows(*self.fixture(literal, rows, **changes))

    def bad(self, literal, rows, **changes):
        with self.assertRaises(NodeLabelProofError): self.good(literal, rows, **changes)

    def test_words_are_not_fused(self): self.good('Alpha Beta', ['Alpha','Beta'])
    def test_authored_break(self): self.good('Alpha<br/>Beta', ['Alpha','Beta'])
    def test_whole_identifier(self): self.good('ModelStateの422を保持', ['ModelStateの422を保持'])
    def test_split_identifier(self): self.bad('ArgumentException', ['Argument','Exception'])
    def test_split_number(self): self.bad('日本語422を保持', ['日本語42','2を保持'])
    def test_split_version(self): self.bad('version1.0', ['version1.','0'])
    def test_split_underscore(self): self.bad('m_student', ['m_','student'])
    def test_hyphen_token(self): self.bad('STU-001', ['STU-','001'])
    def test_oversized(self): self.bad('A'*180, ['A'*60]*3)
    def test_literal_change(self): self.bad('422', ['423'])
    def test_extra_character(self): self.bad('422', ['422!'])
    def test_missing_character(self): self.bad('422', ['42'])
    def test_entity(self): self.good('A &amp; B', ['A & B'])
    def test_non_bmp(self): self.good('開始😀 Identifier2', ['開始😀','Identifier2'])
    def test_markup_unknown(self): self.bad('<b>Alpha</b>', ['Alpha'])
    def test_br_attributes(self): self.bad('A<br class="x">B', ['A','B'])
    def test_markdown_unknown(self): self.bad('**Alpha**', ['Alpha'], labelType='markdown')
    def test_icon_unknown(self): self.bad('Alpha', ['Alpha'], icon='mdi:person')
    def test_duplicate_source(self):
        v,a,c=self.fixture('Alpha',['Alpha'])
        with self.assertRaises(NodeLabelProofError):prove_node_rows(v+v,a,c)
    def test_duplicate_actual(self):
        v,a,c=self.fixture('Alpha',['Alpha'])
        with self.assertRaises(NodeLabelProofError):prove_node_rows(v,a+a,c)
    def test_missing_actual(self):
        v,a,c=self.fixture('Alpha',['Alpha'])
        with self.assertRaises(NodeLabelProofError):prove_node_rows(v,[],c)
    def test_hidden_row(self):
        v,a,c=self.fixture('Alpha',['Alpha']);a[0]['rows'][0]['visibility']='hidden'
        with self.assertRaises(NodeLabelProofError):prove_node_rows(v,a,c)
    def test_zero_opacity(self):
        v,a,c=self.fixture('Alpha',['Alpha']);a[0]['rows'][0]['opacity']=0
        with self.assertRaises(NodeLabelProofError):prove_node_rows(v,a,c)
    def test_outside_node(self):
        v,a,c=self.fixture('Alpha',['Alpha']);a[0]['rows'][0]['bounds']['x']=450
        with self.assertRaises(NodeLabelProofError):prove_node_rows(v,a,c)
    def test_outside_canvas(self):
        v,a,c=self.fixture('Alpha',['Alpha']);c['width']=100
        with self.assertRaises(NodeLabelProofError):prove_node_rows(v,a,c)




from node_label_row_gate_r03 import bind_svg_node_ids
class Bindings(unittest.TestCase):
    def test_safe_svg_namespace(self):
        vertex={'id':'A','domId':'flowchart-A-0'}
        result=bind_svg_node_ids([vertex],[{'id':'rowprobe-flowchart-A-2'}],'rowprobe')
        self.assertEqual(result[0]['domId'],'rowprobe-flowchart-A-2')
        self.assertEqual(result[0]['parserDomId'],'flowchart-A-0')
        self.assertEqual(vertex['domId'],'flowchart-A-0')
    def test_identifier_hyphen_and_digits(self):
        self.assertEqual(bind_svg_node_ids([{'id':'A-2'}],[{'id':'p-flowchart-A-2-19'}],'p')[0]['id'],'A-2')
    def test_wrong_namespace(self):
        with self.assertRaises(NodeLabelProofError):bind_svg_node_ids([{'id':'A'}],[{'id':'q-flowchart-A-0'}],'p')
    def test_similar_identifier(self):
        with self.assertRaises(NodeLabelProofError):bind_svg_node_ids([{'id':'A'}],[{'id':'p-flowchart-AB-0'}],'p')
    def test_ambiguous_id(self):
        with self.assertRaises(NodeLabelProofError):bind_svg_node_ids([{'id':'A'}],[{'id':'p-flowchart-A-0'},{'id':'p-flowchart-A-1'}],'p')
    def test_unmapped_visible_node(self):
        with self.assertRaises(NodeLabelProofError):bind_svg_node_ids([{'id':'A'}],[{'id':'p-flowchart-A-0'},{'id':'p-flowchart-B-1'}],'p')
    def test_duplicate_parsed_id(self):
        with self.assertRaises(NodeLabelProofError):bind_svg_node_ids([{'id':'A'},{'id':'A'}],[{'id':'p-flowchart-A-0'}],'p')


if __name__=='__main__':unittest.main(verbosity=2)
