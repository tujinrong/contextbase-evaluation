import unittest
from qualitygen.semantic_review import inspect_feature
from qualitygen.spec_revision import normalize_names

class VisibleTextTests(unittest.TestCase):
    def fixture(self):
        text='''## 2. 項目一覧

**合計：2項目**（入力・選択 1、表示 0、操作 1、内部・非表示 0）。

| 項目名 | タイプ | DB関連 | 必須 | 長さ | 概要説明 |
| --- | --- | --- | --- | --- | --- |
| 1. 名称 | 入力・選択／文字 | 顧客・名称［保存］ | 必須 | 20文字 | 顧客の名称を入力する。 |
| 2. 保存 | 操作／操作 | 対象外（処理はイベントで定義） | 対象外 | 対象外 | 保存を開始する。 |

## 3. イベント仕様

### 3.1 保存（A-EABC1）

- 顧客を保存する。

```mermaid
flowchart LR
 A[保存] --> B[顧客]
```

## 4. 補足説明
<!-- item:name order:1 role:input -->
<!-- item:save order:2 role:operation -->
'''
        f={'id':'A','items':[{'order':1,'name':'名称','role':'input','type':'文字','required':'必須','length':'20文字','db':[{'object':'customers','column':'name','direction':'write'}]},{'order':2,'name':'保存','role':'operation','type':'操作','required':'対象外','length':'対象外','db':[]}],'events':[{'id':'A-EABC1','db':[{'object':'customers','operation':'C'}]}]}
        reg={'objects':{'customers':{'logical_name':'顧客','columns':{'name':{'logical_name':'名称'}}}}}
        return text,f,reg
    def assertDetects(self,old,new,rule):
        text,f,reg=self.fixture();mutated=text.replace(old,new)
        self.assertNotEqual(text,mutated)
        self.assertIn(rule,{r['rule'] for r in inspect_feature(mutated,f,reg)})
    def test_valid_text(self):self.assertEqual(inspect_feature(*self.fixture()),[])
    def test_delete_visible_row_keep_markers(self):
        text,f,reg=self.fixture();text='\n'.join(l for l in text.splitlines() if not l.startswith('| 1.'))
        self.assertIn('VISIBLE-COUNT',{r['rule'] for r in inspect_feature(text,f,reg)})
    def test_change_label_keep_markers(self):self.assertDetects('| 1. 名称 |','| 1. 別の値 |','VISIBLE-ORDER-NAME')
    def test_change_role_keep_markers(self):self.assertDetects('操作／操作','入力・選択／文字','VISIBLE-ROLE-TYPE')
    def test_change_required(self):self.assertDetects('［保存］ | 必須 |','［保存］ | 任意 |','VISIBLE-REQUIRED')
    def test_change_length_unit(self):self.assertDetects('20文字','20バイト','VISIBLE-LENGTH')
    def test_delete_db_cell(self):self.assertDetects('顧客・名称［保存］','なし','VISIBLE-DB-MAPPING')
    def test_blank_description(self):self.assertDetects('顧客の名称を入力する。','','VISIBLE-DESCRIPTION')
    def test_missing_event_body_keep_id(self):self.assertDetects('### 3.1 保存（A-EABC1）','A-EABC1','VISIBLE-EVENT')
    def test_empty_event_steps(self):self.assertDetects('- 顧客を保存する。','顧客を保存する。','VISIBLE-EVENT-STEPS')
    def test_db_diagram_must_be_in_this_event(self):self.assertDetects('B[顧客]','B[他のデータ]','VISIBLE-EVENT-DB')
    def test_wrong_role_subtotal(self):self.assertDetects('入力・選択 1','入力・選択 2','VISIBLE-SUBTOTAL')
    def test_button_direct_column(self):self.assertDetects('対象外（処理はイベントで定義）','顧客・ID','VISIBLE-BUTTON')
    def test_multiline_logical_name_normalization(self):
        reg={'objects':{'t':{'logical_name':'顧客\n台帳','columns':{'c':{'logical_name':'タックシール用\n 名称'}}}}}
        normalize_names(reg);self.assertEqual(reg['objects']['t']['columns']['c']['logical_name'],'タックシール用 名称')
    def test_malformed_multiline_table_is_rejected(self):self.assertDetects('顧客・名称［保存］','顧客・\n名称［保存］','VISIBLE-COLUMNS')

if __name__=='__main__':unittest.main()
