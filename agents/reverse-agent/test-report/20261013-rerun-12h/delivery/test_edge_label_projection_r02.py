"""Synthetic reviewer-facing lexer/reversibility tests; no material/provider IO."""
import unittest
from dataclasses import replace
from edge_label_projection_r02 import *

class EdgeProjectionTests(unittest.TestCase):
 def check(self,text,labels,insert=True):
  p=project_flowchart_edges(text)
  self.assertEqual(len(p.labels),labels)
  self.assertEqual(reverse_projection(p),text)
  q=project_flowchart_edges(p.text)
  self.assertEqual(q.text,p.text);self.assertFalse(q.insertions)
  if insert:self.assertTrue(p.insertions)
  else:self.assertFalse(p.insertions)
  for item in p.insertions:
   self.assertTrue(any(l.contentStart<=item.sourceOffset<=l.contentEnd for l in p.labels))
  return p
 def test_plain_pipe(self):
  p=self.check('flowchart TD\n A -->|検証InputValidationException・ArgumentException| B\n',1)
  self.assertIn('検証<br/>InputValidationException<br/>・<br/>ArgumentException',p.text)
 def test_plain_long_label(self):
  p=self.check('graph LR\n A -- 条件ArgumentException又は10001件 --> B',1)
  self.assertIn('条件<br/>ArgumentException<br/>又は<br/>10001<br/>件',p.text)
 def test_quoted_pipe(self):
  p=self.check('flowchart TB\n A -->|"検査ArgumentException | text-->literal"| B',1)
  self.assertEqual(p.text.count('|'),3);self.assertIn('"検査<br/>ArgumentException',p.text)
 def test_quoted_long_arrow_strings(self):
  p=self.check('flowchart TB\n A -- "条件ArgumentException --> | --> text" --> B',1)
  self.assertEqual(p.text.count('-->'),3)
 def test_nested_node_shapes_ignored(self):
  text='flowchart TB\n A(["nodeArgumentException -->|foo| B"]) -->|検査ErrorCode| B[("keep--->|X| C")]\n'
  p=self.check(text,1)
  self.assertIn('A(["nodeArgumentException -->|foo| B"])',p.text)
  self.assertIn('B[("keep--->|X| C")]',p.text)
 def test_all_shapes_ignored(self):
  for shape in ['[labelArgumentException]','((labelArgumentException))','{{labelArgumentException}}','[(labelArgumentException)]','[/labelArgumentException/]','[\\labelArgumentException\\]']:
   with self.subTest(shape=shape):self.check('flowchart TD\n A'+shape+' --> B',0,False)
 def test_modern_node_property_shape_ignored(self):
  p=self.check('flowchart LR\n A@{shape: rect, label: "名ArgumentException -->|X| B"} -->|数10001件| B',1)
  self.assertIn('label: "名ArgumentException -->|X| B"',p.text)
 def test_authored_breaks_preserved(self):
  text='flowchart TB\n A -->|"条件<br/>ArgumentException<BR />と<br>10001件"| B'
  p=self.check(text,1)
  self.assertIn('条件<br/>ArgumentException<BR />と<br>10001<br/>件',p.text)
 def test_whitespace_words_no_changes(self):
  self.check('flowchart TB\n A -->|AlphaIdentifier BetaIdentifier 10001| B',1,False)
 def test_single_identifier_left_for_actual_row_check(self):
  self.check('flowchart TB\n A -->|AnOversizedIndivisibleIdentifier| B',1,False)
 def test_entities_are_opaque(self):
  p=self.check('flowchart TD\n A -->|"条件ArgumentException&amp;名前&#124;#quot;数10001"| B',1)
  for entity in ['&amp;','&#124;','#quot;']:self.assertEqual(p.text.count(entity),1)
 def test_quotes_and_escape_preserved(self):
  text=r'flowchart TD'+ '\n'+r' A -->|"条件ArgumentException \"quoted|literal\""| B'
  self.check(text,1)
 def test_comment_content_and_inline_comment(self):
  text='flowchart TD\n%% A -->|条件ArgumentException| B\n A -->|数10001件| B %% C -- 条件ErrorCode --> D\n'
  p=self.check(text,1);self.assertIn('%% A -->|条件ArgumentException| B',p.text);self.assertIn('%% C -- 条件ErrorCode --> D',p.text)
 def test_percent_inside_quoted_label(self):
  self.check('flowchart TD\n A -->|"条件ArgumentException %% literal"| B',1)
 def test_yaml_init_comment_handling(self):
  text='---\ntitle: "A -->|条件ArgumentException| B"\nconfig:\n  flowchart:\n    wrappingWidth: 320\n---\n%%{init: {"themeCSS":"A -->|条件ArgumentException| B"}}%%\n%% comment\nflowchart TD\n A -->|条件ErrorCode| B'
  p=self.check(text,1);self.assertEqual(p.text[:text.index('flowchart TD')],text[:text.index('flowchart TD')])
 def test_directive_after_header_ignored(self):
  text='flowchart TD\n%%{init: {"x":"A -->|条件ErrorCode| B"}}%%\n A -->|数10001件| B'
  self.check(text,1)
 def test_metadata_subgraph_titles_ignored(self):
  text='flowchart TD\nsubgraph SG[タイトルArgumentException -->|foo| X]\n A -->|条件ErrorCode| B\nend\nclassDef foo fill:red;\nlinkStyle 0 stroke:red\nclick A "https://test/ArgumentException"\n'
  p=self.check(text,1);self.assertIn('SG[タイトルArgumentException -->|foo| X]',p.text)
 def test_nonflow_diagrams_unchanged(self):
  for kind in ['sequenceDiagram','erDiagram','stateDiagram-v2','classDiagram','gantt','journey','pie','mindmap']:
   with self.subTest(kind=kind):
    p=self.check(kind+'\n A -->|条件ArgumentException| B',0,False);self.assertFalse(p.supportedDiagram)
 def test_multiple_edges_same_line(self):
  self.check('flowchart LR; A -->|条件ErrorCode| B -->|数10001件| C; D -- 条件ValidationException --> E',3)
 def test_branch_and_bidirectional_pipe_operators(self):
  for arrow in ['-->','--->','---','-.->','==>','<-->','--o','--x']:
   with self.subTest(arrow=arrow):self.check('flowchart LR\n A '+arrow+'|条件ErrorCode| B',1)
 def test_label_with_arrow_like_string_as_quoted_pipe(self):
  self.check('flowchart TD\n A -->|"選択ErrorCode --> A[outer] -- inner --> B | preserve"| B',1)
 def test_nodes_and_label_order_preserved(self):
  text='flowchart TD\n A[名ErrorCode] -->|条件FirstCode| B{判定SecondCode}\n B -- 条件ThirdCode --> C((終了FourthCode))'
  p=self.check(text,2);self.assertIn('A[名ErrorCode]',p.text);self.assertIn('B{判定SecondCode}',p.text);self.assertIn('C((終了FourthCode))',p.text)
 def test_markdown_label_not_projected(self):
  self.check('flowchart TD\n A -->|"`条件ArgumentException`"| B',1,False)
 def test_numeric_dot_path_tokens(self):
  p=self.check('flowchart TD\n A -->|数1.0条件Foo.Bar又はFoo/Bar値10001| B',1)
  for token in ['1.0','Foo.Bar','Foo/Bar','10001']:self.assertIn(token,p.text)
 def test_empty_labels(self):self.check('flowchart TD\n A -->|| B',1,False)
 def test_fail_closed_unterminated_quote(self):
  with self.assertRaises(ProjectionError):project_flowchart_edges('flowchart TD\n A -->|"条件ArgumentException| B')
 def test_fail_closed_unterminated_shape(self):
  with self.assertRaises(ProjectionError):project_flowchart_edges('flowchart TD\n A[Name -->|条件ErrorCode| B')
 def test_fail_closed_unterminated_pipe(self):
  with self.assertRaises(ProjectionError):project_flowchart_edges('flowchart TD\n A -->|条件ErrorCode B')
 def test_fail_closed_mixed_label_quotes(self):
  with self.assertRaises(ProjectionError):project_flowchart_edges('flowchart TD\n A -->|条件"ArgumentException"| B')
 def test_fail_closed_yaml_and_init(self):
  for text in ['---\ntitle: x\nflowchart TD\n A --> B','%%{init:{}\nflowchart TD\n A --> B']:
   with self.subTest(text=text):
    with self.assertRaises(ProjectionError):project_flowchart_edges(text)
 def test_receipt_tampering_rejected(self):
  p=self.check('flowchart TD\n A -->|条件ErrorCode| B',1)
  with self.assertRaises(ProjectionError):reverse_projection(replace(p,text=p.text+'x'))
 def test_visible_rows_accept_whole_tokens(self):
  self.assertTrue(validate_visible_rows(['InputValidationException','ArgumentException','10001'],['InputValidationException','・ArgumentException','10001件']))
 def test_visible_rows_fail_oversized_indivisible(self):
  with self.assertRaises(IndivisibleTokenError):validate_visible_rows(['VeryLongIndivisibleIdentifier'],['VeryLongIndivisible','Identifier'])
 def test_visible_rows_multiplicity(self):
  with self.assertRaises(IndivisibleTokenError):validate_visible_rows(['ArgumentException','ArgumentException'],['ArgumentException','Argument','Exception'])
 def test_visible_rows_whole_token_boundary(self):
  with self.assertRaises(IndivisibleTokenError):validate_visible_rows(['ID','ID_Long'],['I','D','ID_Long'])
 def test_signed_numeric_tokens_not_split(self):
  p=self.check('flowchart TD\n A -->|値-1.0と+2.5又は-1e-3| B',1)
  for token in ['-1.0','+2.5','-1e-3']:self.assertIn(token,p.text)
  self.assertTrue(validate_visible_rows(['-1.0','+2.5','-1e-3'],['値','-1.0','と','+2.5','又は','-1e-3']))
 def test_semantic_signature_refusal(self):
  self.assertTrue(validate_semantic_signature({'edgeLabels':['text --> literal']},{'edgeLabels':['text --> literal']}))
  with self.assertRaises(ProjectionError):validate_semantic_signature({'edgeLabels':['text -- literal']},{'edgeLabels':['text --> literal']})

if __name__=='__main__':unittest.main()
