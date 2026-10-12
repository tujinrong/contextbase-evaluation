import unittest
from contextbase.itemlist import HEADERS, NA, normalize, render
from contextbase.markup_items import extract_markup


class ItemContractTests(unittest.TestCase):
    def test_exact_columns(self):
        self.assertEqual(10, len(HEADERS))
        self.assertEqual('| No | グループ | 項目名 | 種類 | 入出力 | DB連携項目 | 候補取得元 | 必須 | 形式・桁 | 説明 |', render([]).splitlines()[0])

    def test_operation_does_not_inherit_db_or_input_constraints(self):
        row = normalize({'name':'保存', 'type':'button', 'role':'operation', 'data':'誤ったDB', 'required':True, 'length':99}, 1)
        for key in ['io','db','choices','required','format']:
            self.assertEqual(NA, row[key])

    def test_display_is_not_required_input(self):
        row = normalize({'name':'氏名','type':'text','role':'display','required':True},1)
        self.assertEqual('O', row['io'])
        self.assertEqual(NA, row['required'])
        self.assertEqual('未確認', row['db'])

    def test_unknown_role_fails_closed(self):
        with self.assertRaises(ValueError):
            normalize({'name':'不明','type':'謎の部品'},1)

    def test_operation_input_is_rejected(self):
        with self.assertRaises(ValueError):
            normalize({'name':'保存','type':'button','io':'I'},1)

    def test_db_and_choices_are_separate(self):
        row=normalize({'name':'部署','type':'select','role':'input','db':'社員・部署番号','choices':'部署マスタ'},1)
        self.assertEqual('社員・部署番号',row['db'])
        self.assertEqual('部署マスタ',row['choices'])

    def test_escape_and_duplicate_captions(self):
        text=render([{'name':'参照','type':'button','role':'operation','description':'<script>x</script> | `x`\n次行'},
                     {'name':'参照','type':'button','role':'operation'}])
        self.assertIn('| 1 |',text)
        self.assertIn('| 2 |',text)
        self.assertNotIn('<script>',text)
        self.assertIn('&#124;',text)
        self.assertIn('&#96;',text)
        self.assertIn('<br>',text)

    def test_absent_attribute_is_not_business_optional(self):
        row=normalize({'name':'番号','type':'text','role':'input','required':False},1)
        self.assertIn('業務必須は未確認',row['required'])


class MarkupTests(unittest.TestCase):
    def test_razor_binding_label_model_required_range(self):
        markup='<h1>職員番号入力</h1>\n<label asp-for="StaffNo">職員番号</label>\n<input asp-for="StaffNo" maxlength="8">\n<button type="submit">決定</button>'
        model='[BindProperty]\n[Required]\n[Range(1,99999999)]\npublic int? StaffNo { get; set; }\nvoid OnGet(){StaffNo = 12;}'
        result=extract_markup(markup,'Staff.cshtml',model,'Staff.cshtml.cs')
        self.assertEqual(['職員番号入力','職員番号','決定'],[r['name'] for r in result['items']])
        row=result['items'][1]
        self.assertTrue(row['required'])
        self.assertEqual('input_output',row['role'])
        self.assertIn('99999999',row['length'])
        self.assertEqual(3,row['line'])
        self.assertEqual(2,len(row['evidence']))

    def test_comments_and_script_do_not_create_controls(self):
        markup='@* <input name="fake"> *@\n<!-- <button>fake</button> -->\n<script>let s="<input name=x>"</script>\n<input name="real">'
        result=extract_markup(markup,'x.cshtml')
        self.assertEqual(['real'],[x['name'] for x in result['items']])
        self.assertEqual(4,result['items'][0]['line'])

    def test_submit_reset_are_operations(self):
        result=extract_markup('<input type="submit" value="登録"><input type="reset" value="クリア">','x.html')
        self.assertEqual(['operation','operation'],[x['role'] for x in result['items']])

    def test_nested_label_and_button_caption(self):
        result=extract_markup('<label><input type="checkbox">同意する</label><button><span>保存</span></button>','x.html')
        self.assertEqual(['同意する','保存'],[x['name'] for x in result['items']])

    def test_readonly_and_disabled(self):
        result=extract_markup('<input aria-label="結果" readonly><input aria-label="固定" disabled>','x.html')
        self.assertEqual(['display','display'],[x['role'] for x in result['items']])

    def test_unknown_candidate_source_not_guessed(self):
        result=extract_markup('<select aria-label="店舗" asp-items="Model.Branches"></select>','x.cshtml')
        self.assertEqual('未確認',result['items'][0]['choices'])
        self.assertTrue(any('UI-CHOICES' in x for x in result['warnings']))

    def test_static_choices(self):
        result=extract_markup('<select aria-label="区分"><option>全件</option><option>有効</option></select>','x.html')
        self.assertEqual('固定候補：全件／有効',result['items'][0]['choices'])

    def test_hidden_and_partial_not_counted_as_main_controls(self):
        result=extract_markup('<input type="hidden" value="secret"><partial name="Shared"><input name="visible">','x.cshtml')
        self.assertEqual(1,len(result['items']))
        self.assertTrue(any('UI-HIDDEN' in x for x in result['warnings']))
        self.assertTrue(any('UI-PARTIAL' in x for x in result['warnings']))

    def test_commented_required_is_not_fact(self):
        result=extract_markup('<input asp-for="Code">','x.cshtml','// [Required]\npublic string Code {get;set;}','x.cs')
        self.assertEqual('未確認',result['items'][0]['required'])


class ModelGraphTests(unittest.TestCase):
    def test_nested_boolean_type_and_required(self):
        page = "[BindProperty] public Entry Input {get;set;}\nvoid OnGet(){ Input = new(); }"
        child = "public bool Selected {get;set;}\n[Required] public string Name {get;set;}"
        model = {"Entry": (child, "Models/Entry.cs")}
        markup = '<label><input asp-for="Input.Selected">選択</label><label asp-for="Input.Name">名前</label><input asp-for="Input.Name">'
        rows = extract_markup(markup,'Edit.cshtml',page,'Edit.cshtml.cs',model)['items']
        self.assertEqual('CheckBox',rows[0]['type'])
        self.assertEqual('input_output',rows[0]['role'])
        self.assertTrue(rows[1]['required'])
        self.assertEqual('Models/Entry.cs',rows[1]['evidence'][1]['path'])

    def test_conditional_readonly_is_not_permanent_output(self):
        page = '[BindProperty] public string Name {get;set;} void OnGet(){Name="sample";}'
        result=extract_markup('<input asp-for="Name" readonly="@Model.Locked">','Edit.cshtml',page,'Edit.cshtml.cs')
        row=result['items'][0]
        self.assertEqual('input_output',row['role'])
        self.assertIn('条件により編集不可',row['description'])

    def test_razor_false_differs_from_literal_html_false(self):
        a=extract_markup('<input name="Code" readonly="@false">','x.cshtml')['items'][0]
        b=extract_markup('<input name="Code" readonly="false">','x.html')['items'][0]
        self.assertEqual('input',a['role'])
        self.assertEqual('display',b['role'])

    def test_explicit_type_wins_over_model_inference(self):
        page='[BindProperty] public int Code {get;set;}'
        row=extract_markup('<input asp-for="Code" type="text">','x.cshtml',page,'x.cs')['items'][0]
        self.assertEqual('TextBox',row['type'])

    def test_required_word_in_message_is_not_required_attribute(self):
        page='[Display(Name="Required")] public string Code {get;set;}'
        row=extract_markup('<input asp-for="Code">','x.cshtml',page,'x.cs')['items'][0]
        self.assertEqual('未確認',row['required'])

    def test_nested_cycle_is_bounded(self):
        page='[BindProperty] public Entry Input {get;set;}'
        model={'Entry':('public Entry Child {get;set;} public bool Selected {get;set;}','Entry.cs')}
        rows=extract_markup('<input asp-for="Input.Selected">','x.cshtml',page,'x.cs',model)['items']
        self.assertEqual('CheckBox',rows[0]['type'])


    def test_string_assignment_is_not_execution_evidence(self):
        page='[BindProperty] public string Code {get;set;} string Description = "Code = sample";'
        row=extract_markup('<input asp-for="Code">','x.cshtml',page,'x.cs')['items'][0]
        self.assertEqual('input',row['role'])

    def test_static_razor_title_is_preserved(self):
        result=extract_markup('@{ ViewData["Title"] = "職員番号入力"; }<input name="x">','Staff.cshtml')
        self.assertEqual('職員番号入力',result['title'])


if __name__=='__main__': unittest.main()
