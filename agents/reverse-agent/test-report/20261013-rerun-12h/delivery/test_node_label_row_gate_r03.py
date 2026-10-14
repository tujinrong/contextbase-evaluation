from test_node_label_row_gate_r01 import NodeRows
from node_label_row_gate_r03 import bind_svg_node_ids, NodeLabelProofError
import unittest


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
