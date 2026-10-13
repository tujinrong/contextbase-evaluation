"""Synthetic structure mutations, independent of domain and reference designs."""
import copy
import json
import unittest

from contextbase.ai.validation import validate_document


PATH = "基本設計書/機能.md"


def document(*, path=PATH, sheets=None, body=None, **extra):
    meta = {"schema": "spec-md/1.0", "documentId": "DEMO-001", "version": "1.0", "path": path,
            "sheets": sheets if sheets is not None else [
                {"heading": "概要", "kind": "GRID", "sheet": "01_概要"},
                {"heading": "項目一覧", "kind": "LIST", "sheet": "02_項目一覧", "key": ["ID"]},
                {"heading": "イベント仕様", "kind": "GRID", "sheet": "03_イベント仕様"}]}
    meta.update(extra)
    if body is None:
        body = """## 概要

任意の責務を説明する。

## 項目一覧

| ID | 名称 | 説明 |
| --- | --- | --- |
| 01 | 値A | 一行目<br>二行目 |
| 02 | 値B | 文字列 &#124; を保持する |

## イベント仕様

### 初期表示

任意の状態を説明する。
"""
    return "<!-- spec-meta: " + json.dumps(meta, ensure_ascii=False) + " -->\n# 機能\n\n" + body


class StructuralTests(unittest.TestCase):
    def codes(self, content, path=PATH):
        findings = validate_document(content, path)
        for finding in findings:
            self.assertEqual({"severity", "code", "detail", "location"}, set(finding))
            self.assertEqual("ERROR", finding["severity"])
            self.assertTrue(finding["detail"])
            self.assertTrue(finding["location"].startswith(path + ":"))
        return {finding["code"] for finding in findings}

    def test_valid_document_and_br_are_accepted_without_rewrite(self):
        text = document()
        original = copy.copy(text)
        self.assertEqual([], validate_document(text, PATH))
        self.assertEqual(original, text)

    def test_domain_words_are_not_required_for_structure(self):
        text = document().replace("任意の責務を説明する。", "blorp")
        self.assertEqual(set(), self.codes(text))

    def test_bound_document_identity_accepts_exact_match_without_rewriting(self):
        text = document()
        self.assertEqual([], validate_document(text, PATH, expected_document_id="DEMO-001"))
        self.assertEqual(document(), text)
        self.assertEqual([], validate_document(text, PATH))
        self.assertEqual([], validate_document(text, PATH, expected_document_id=None))

    def test_other_valid_metadata_identity_is_rejected_only_when_binding_is_supplied(self):
        text = document(documentId="OTHER-001")
        self.assertEqual([], validate_document(text, PATH))
        findings = validate_document(text, PATH, expected_document_id="DEMO-001")
        self.assertEqual(["META_DOCUMENT_ID"], [finding["code"] for finding in findings])
        self.assertEqual("ERROR", findings[0]["severity"])
        self.assertEqual(PATH + ":1", findings[0]["location"])
        self.assertEqual(document(documentId="OTHER-001"), text)

    def test_expected_identity_uses_real_metadata_not_body_or_fenced_example(self):
        text = document(documentId="OTHER-001")
        correct_meta = document().split("\n", 1)[0]
        text += "\nDEMO-001\n\n```md\n" + correct_meta + "\n```\n"
        findings = validate_document(text, PATH, expected_document_id="DEMO-001")
        self.assertEqual(["META_DOCUMENT_ID"], [finding["code"] for finding in findings])

    def test_identity_matching_is_exact_case_sensitive_and_does_not_trim(self):
        for value in ("demo-001", " DEMO-001", "DEMO-001 "):
            with self.subTest(value=value):
                findings = validate_document(document(documentId=value), PATH, expected_document_id="DEMO-001")
                self.assertIn("META_DOCUMENT_ID", {finding["code"] for finding in findings})
        self.assertEqual([], validate_document(document(documentId="機能-01"), PATH, expected_document_id="機能-01"))

    def test_missing_metadata_identity_is_not_accepted_by_expected_identity(self):
        text = document().replace('"documentId": "DEMO-001", ', "")
        findings = validate_document(text, PATH, expected_document_id="DEMO-001")
        self.assertTrue({"META_FIELD", "META_DOCUMENT_ID"} <= {finding["code"] for finding in findings})

    def test_invalid_expected_identity_arguments_do_not_create_a_false_valid_document(self):
        for value in (True, 7, [], {}):
            with self.subTest(value=value), self.assertRaises(TypeError):
                validate_document(document(), PATH, expected_document_id=value)
        for value in ("", " \t"):
            with self.subTest(value=value), self.assertRaises(ValueError):
                validate_document(document(), PATH, expected_document_id=value)

    def test_missing_meta_is_an_error(self):
        self.assertIn("META_COUNT", self.codes(document().split("\n", 1)[1]))

    def test_meta_inside_fence_is_only_an_example(self):
        meta_line = document().split("\n", 1)[0]
        self.assertIn("META_COUNT", self.codes("# 例\n\n```md\n" + meta_line + "\n```\n"))

    def test_multiple_meta_comments_are_rejected(self):
        text = document()
        self.assertIn("META_COUNT", self.codes(text + "\n" + text.split("\n", 1)[0]))

    def test_invalid_meta_json_is_rejected(self):
        self.assertIn("META_JSON", self.codes("<!-- spec-meta: {broken} -->\n# タイトル\n"))

    def test_duplicate_json_members_are_not_silently_overwritten(self):
        text = document().replace('"version": "1.0"', '"version": "1.0", "version": "2.0"')
        self.assertIn("META_JSON", self.codes(text))

    def test_meta_after_title_is_rejected(self):
        text = "# 別のタイトル\n" + document()
        self.assertIn("META_POSITION", self.codes(text))

    def test_missing_required_meta_field_is_rejected(self):
        text = document().replace('"documentId": "DEMO-001", ', "")
        self.assertIn("META_FIELD", self.codes(text))

    def test_unsupported_meta_schema_is_rejected(self):
        self.assertIn("META_SCHEMA", self.codes(document(schema="other/1")))

    def test_malformed_meta_schema_type_returns_findings_instead_of_crashing(self):
        self.assertIn("META_SCHEMA", self.codes(document(schema=[])))

    def test_malformed_meta_kind_type_returns_findings_instead_of_crashing(self):
        self.assertIn("META_KIND", self.codes(document().replace('"kind": "LIST"', '"kind": {}')))

    def test_meta_path_must_equal_planned_path(self):
        self.assertIn("META_PATH", self.codes(document(path="共通/別.md")))

    def test_unsafe_output_paths_are_rejected(self):
        for path in ("../spec.md", "/spec.md", "C:/spec.md", "a\\spec.md", "a//spec.md", "a/NUL.md", "a/b?.md", "a/../b.md", "a/spec.md "):
            with self.subTest(path=path):
                self.assertIn("DOC_PATH", self.codes(document(path=path), path))

    def test_missing_sheet_declarations_are_rejected(self):
        self.assertIn("META_SHEETS", self.codes(document(sheets=[])))

    def test_undeclared_chapter_is_rejected(self):
        self.assertIn("CHAPTER_MAPPING", self.codes(document() + "\n## 別章\n説明\n"))

    def test_declared_but_missing_chapter_is_rejected(self):
        self.assertIn("CHAPTER_MAPPING", self.codes(document().replace("## イベント仕様", "### イベント仕様")))

    def test_duplicate_h2_is_rejected_but_event_subheadings_may_repeat(self):
        self.assertIn("HEADING_DUPLICATE", self.codes(document() + "\n## 概要\n"))
        self.assertEqual(set(), self.codes(document() + "\n### 二番目\n#### 処理概要\n説明\n### 三番目\n#### 処理概要\n説明\n"))

    def test_chapter_order_matches_declaration(self):
        text = document().replace('"heading": "概要"', '"heading": "仮"').replace('"heading": "イベント仕様"', '"heading": "概要"').replace('"heading": "仮"', '"heading": "イベント仕様"')
        self.assertIn("CHAPTER_ORDER", self.codes(text))

    def test_sheet_names_are_unique_case_insensitively(self):
        self.assertIn("SHEET_DUPLICATE", self.codes(document().replace('"03_イベント仕様"', '"01_概要"')))

    def test_sheet_name_limits_and_forbidden_characters(self):
        for name in ("x" * 32, "bad/name", "bad[name]", "'name", "name'"):
            with self.subTest(name=name):
                self.assertIn("SHEET_NAME", self.codes(document().replace('"01_概要"', json.dumps(name))))

    def test_unknown_chapter_kind_is_rejected(self):
        self.assertIn("META_KIND", self.codes(document().replace('"kind": "LIST"', '"kind": "UNKNOWN"')))

    def test_fenced_h2_is_not_a_real_main_chapter(self):
        self.assertEqual(set(), self.codes(document() + "\n```md\n## 仮の章\n```\n"))

    def test_common_and_database_document_chapters_can_differ(self):
        sheets = [{"heading": "契約", "kind": "GRID", "sheet": "契約"},
                  {"heading": "格納構造", "kind": "LIST", "sheet": "格納構造", "key": ["物理名"]}]
        body = "## 契約\n\n契約説明\n\n## 格納構造\n\n| 物理名 | 型 |\n| --- | --- |\n| example_id | integer |\n"
        self.assertEqual([], validate_document(document(path="DB定義/table.md", sheets=sheets, body=body), "DB定義/table.md"))

    def test_ragged_source_row_cannot_pass_parser_padding(self):
        self.assertIn("LIST_RECTANGLE", self.codes(document().replace("| 02 | 値B | 文字列 &#124; を保持する |", "| 02 | 値B |")))

    def test_extra_source_cells_cannot_be_truncated(self):
        self.assertIn("LIST_RECTANGLE", self.codes(document().replace("| 01 | 値A | 一行目<br>二行目 |", "| 01 | 値A | 説明 | 余分 |")))

    def test_duplicate_declared_keys_are_rejected(self):
        self.assertIn("LIST_KEY_DUPLICATE", self.codes(document().replace("| 02 |", "| 01 |")))

    def test_empty_key_is_rejected(self):
        self.assertIn("LIST_KEY_EMPTY", self.codes(document().replace("| 02 |", "|  |")))

    def test_zero_and_leading_zero_keys_remain_different_strings(self):
        self.assertEqual(set(), self.codes(document().replace("| 02 |", "| 1 |")))

    def test_key_identity_uses_visible_text_without_numeric_coercion(self):
        self.assertEqual(set(), self.codes(document().replace("| ID | 名称 | 説明 |", "| `ID` | 名称 | 説明 |")))
        self.assertIn("LIST_KEY_DUPLICATE", self.codes(document().replace("| 02 |", "| **01** |")))

    def test_escaped_pipe_keys_use_actual_table_rendering_identity(self):
        text = document().replace("| 01 |", r"| `A\|B` |").replace("| 02 |", r"| A\|B |")
        self.assertIn("LIST_KEY_DUPLICATE", self.codes(text))

    def test_missing_declared_key_column_is_rejected(self):
        self.assertIn("LIST_KEY", self.codes(document().replace('"key": ["ID"]', '"key": ["missing"]')))

    def test_grid_code_pipe_overflow_is_detected_without_rewriting(self):
        text=document()+'\n| Trigger | Condition | Outcome |\n| --- | --- | --- |\n| T | `alpha || beta` | Result sentinel |\n'
        before=text.encode('utf-8')
        self.assertIn('TABLE_CELL_OVERFLOW',self.codes(text))
        self.assertEqual(before,text.encode('utf-8'))

    def test_escaped_grid_code_pipe_keeps_condition_and_result(self):
        text=document()+'\n| Trigger | Condition | Outcome |\n| --- | --- | --- |\n'+r'| T | `alpha \|\| beta` | Result sentinel |'+'\n'
        self.assertEqual(set(),self.codes(text))
        from markdown_it import MarkdownIt
        rendered=MarkdownIt('commonmark').enable('table').render(text)
        self.assertIn('<code>alpha || beta</code>',rendered)
        self.assertIn('<td>Result sentinel</td>',rendered)

    def test_grid_padding_and_fenced_example_are_not_overflow(self):
        text=document()+'\n| A | B |\n| --- | --- |\n| Value |\n\n```md\n| A | B |\n| --- | --- |\n| T | `alpha || beta` | extra |\n```\n'
        self.assertNotIn('TABLE_CELL_OVERFLOW',self.codes(text))

    def test_duplicate_declared_key_columns_are_rejected(self):
        self.assertIn("LIST_KEY", self.codes(document().replace('"key": ["ID"]', '"key": ["ID", "ID"]')))

    def test_missing_table_is_rejected(self):
        text = document().replace("| ID | 名称 | 説明 |\n| --- | --- | --- |\n| 01 | 値A | 一行目<br>二行目 |\n| 02 | 値B | 文字列 &#124; を保持する |", "説明のみ")
        self.assertIn("LIST_TABLE_COUNT", self.codes(text))

    def test_invalid_delimiter_cannot_be_a_declared_list_table(self):
        self.assertIn("LIST_TABLE_COUNT", self.codes(document().replace("| --- | --- | --- |", "| abc | --- | --- |")))

    def test_duplicate_or_empty_headers_are_rejected(self):
        self.assertIn("LIST_HEADERS", self.codes(document().replace("| ID | 名称 | 説明 |", "| ID | ID | 説明 |")))
        self.assertIn("LIST_HEADERS", self.codes(document().replace("| ID | 名称 | 説明 |", "| ID |  | 説明 |")))

    def test_second_table_in_list_is_rejected(self):
        extra = "\n| ID | 名称 |\n| --- | --- |\n| 03 | 追加 |\n\n"
        self.assertIn("LIST_TABLE_COUNT", self.codes(document().replace("## イベント仕様", extra + "## イベント仕様")))

    def test_prose_heading_and_code_in_list_are_rejected(self):
        for extra in ("説明文", "### 小見出し", "```text\nコード\n```", "<!-- 隠した説明 -->"):
            with self.subTest(extra=extra):
                self.assertIn("LIST_EXTRA_CONTENT", self.codes(document().replace("## イベント仕様", extra + "\n\n## イベント仕様")))

    def test_html_and_markdown_images_in_list_cells_are_rejected(self):
        for extra in ("<b>太字</b>", "<br class='x'>", "![図](assets/a.png)"):
            with self.subTest(extra=extra):
                self.assertIn("LIST_INLINE_CONTENT", self.codes(document().replace("一行目<br>二行目", extra)))

    def test_default_first_column_key_and_empty_data_table_are_valid(self):
        text = document().replace(', "key": ["ID"]', "")
        self.assertEqual(set(), self.codes(text))
        text = document().replace("| 01 | 値A | 一行目<br>二行目 |\n| 02 | 値B | 文字列 &#124; を保持する |\n", "")
        self.assertEqual(set(), self.codes(text))

    def test_composite_key_is_unique_by_tuple(self):
        sheets = [{"heading": "一覧", "kind": "LIST", "sheet": "一覧", "key": ["ID", "種別"]}]
        body = "## 一覧\n\n| ID | 種別 |\n| --- | --- |\n| 01 | A |\n| 01 | B |\n"
        self.assertEqual(set(), self.codes(document(sheets=sheets, body=body)))
        self.assertIn("LIST_KEY_DUPLICATE", self.codes(document(sheets=sheets, body=body.replace("| 01 | B |", "| 01 | A |"))))

    def test_table_layout_explicitly_maps_two_sections_to_one_sheet(self):
        text = document(schema="spec-md/1.1", layout="TABLE", sheets=[{"sheet": "example_table"}],
                        sections=[{"heading": "ヘッダー", "kind": "HEADER"}, {"heading": "項目詳細", "kind": "LIST", "key": ["No"]}],
                        columns=["No", "物理名"], body="## ヘッダー\n\n| 情報 | 内容 |\n| --- | --- |\n| 名称 | 例 |\n\n## 項目詳細\n\n| No | 物理名 |\n| --- | --- |\n| 1 | example_id |\n")
        self.assertEqual(set(), self.codes(text))
        self.assertIn("TABLE_COLUMNS", self.codes(text.replace('"columns": ["No", "物理名"]', '"columns": ["No", "別名"]')))

    def test_relative_links_inside_publication_root_are_valid(self):
        self.assertEqual(set(), self.codes(document() + "\n[共通](../共通/契約.md)\n![画面](assets/screen.png)\n[公式](https://example.invalid/docs)\n"))

    def test_local_unsafe_reference_paths_are_rejected(self):
        for target in ("../../secret.md", "/absolute.md", "C:/secret.md", "file:///secret.md", "javascript:alert(1)", "//host/file.md", "%2e%2e/%2e%2e/secret.md", "../spec-eval/answer.md", "a%5Cb.md", "https:../../secret.md"):
            with self.subTest(target=target):
                self.assertIn("REFERENCE_PATH", self.codes(document() + f"\n[参照]({target})\n"))

    def test_html_reference_paths_and_active_handlers_are_rejected(self):
        self.assertIn("REFERENCE_PATH", self.codes(document() + '\n<img src="../../secret.png">\n'))
        self.assertIn("REFERENCE_PATH", self.codes(document() + '\n<style>.x{background:url(../../secret.png)}</style>\n'))
        for markup in ('<script>alert(1)</script>', '<iframe src="https://example.invalid"></iframe>', '<button onclick="run()">操作</button>'):
            with self.subTest(markup=markup):
                self.assertIn("HTML_ACTIVE", self.codes(document() + "\n" + markup + "\n"))

    def test_static_screen_html_is_valid_in_grid(self):
        self.assertEqual(set(), self.codes(document() + '\n<div data-item-id="I1"><label>項目<input readonly></label></div>\n'))

    def test_submission_targets_are_active_even_when_the_url_is_a_valid_citation(self):
        for markup in ('<form action="https://example.invalid/post"><button>操作</button></form>',
                       '<button formaction="https://example.invalid/post">操作</button>',
                       '<form action="#local"><input></form>'):
            with self.subTest(markup=markup):
                self.assertIn("HTML_ACTIVE", self.codes(document() + "\n" + markup + "\n"))

    def test_button_override_submission_path_is_checked(self):
        self.assertIn("REFERENCE_PATH", self.codes(document() + '\n<button formaction="/remote">操作</button>\n'))

    def test_inert_source_route_annotation_retains_static_link_and_button_state(self):
        markup = '<form data-source-action="/original" data-source-method="post"><button type="button">操作</button></form><a href="#local" data-source-route="/original">遷移</a>'
        self.assertEqual(set(), self.codes(document() + "\n" + markup + "\n"))

    def test_inert_utf8_and_viewport_metadata_are_valid(self):
        self.assertEqual(set(), self.codes(document() + '\n<meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">\n'))

    def test_redirect_or_conflicting_metadata_is_active(self):
        for markup in ('<meta http-equiv="refresh" content="0;url=https://example.invalid">',
                       '<meta charset="utf-8" http-equiv="refresh" content="0;url=https://example.invalid">',
                       '<meta charset="shift_jis" charset="utf-8">'):
            with self.subTest(markup=markup):
                self.assertIn("HTML_ACTIVE", self.codes(document() + "\n" + markup + "\n"))

    def test_inert_html_comment_url_example_is_not_a_reference(self):
        self.assertEqual(set(), self.codes(document() + '\n<!-- Example: url(../../secret.png) -->\n'))

    def test_css_comments_and_string_values_are_not_url_references(self):
        markup = '<style>.x{content:"url(../../secret.png)"}/* background:url(../../secret.png) */</style>'
        self.assertEqual(set(), self.codes(document() + "\n" + markup + "\n"))

    def test_actual_style_attribute_url_is_still_checked(self):
        markup = '<div style="background:url(../../secret.png)">表示</div>'
        self.assertIn("REFERENCE_PATH", self.codes(document() + "\n" + markup + "\n"))

    def test_code_examples_do_not_activate_paths_or_html(self):
        self.assertEqual(set(), self.codes(document() + '\n```html\n<script src="../../secret.js"></script>\n```\n'))

    def test_mermaid_presence_is_not_semantic_approval(self):
        self.assertEqual(set(), self.codes(document() + "\n```mermaid\ngraph TD\n A --> B\n```\n"))
        self.assertIn("META_COUNT", self.codes("# 未宣言\n```mermaid\ngraph TD\n A --> B\n```\n"))


if __name__ == "__main__":
    unittest.main()
