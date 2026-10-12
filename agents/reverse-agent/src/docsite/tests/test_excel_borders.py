"""Border regressions for the supplied V2 cover and all worksheet margins."""
import io
import unittest
import zipfile
from copy import deepcopy
from xml.etree import ElementTree as ET

from docsite.excel_package import S, STYLES, package, verify
from docsite.v2.render_document_xlsx import markdown_model


MD = '''# 職員番号入力

## 表紙
| 項目 | 内容 |
| --- | --- |
| システム名 | 年金自動受取予約管理システム |
| 機能ID | 100008 |
| 画面名 | 職員番号入力 |

## 概要
### 概要説明
職員番号を入力する。

| 区分 | 内容 |
| --- | --- |
| 入力 | 職員番号 |

## 項目一覧
| No | グループ | 項目名 | 種類 | 入出力 | DB連携項目 | 候補取得元 | 必須 | 形式・桁 | 説明 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | 入力 | 職員番号 | TextBox | I | ‐ | ‐ | 必須 | 8桁 | 職員番号を入力する。 |

## イベント仕様
### 確認ボタン
入力を照合する。

## 補足説明
既存の記載内容を保持する。
'''


def read_styles(data, sheet_number=1):
    with zipfile.ZipFile(io.BytesIO(data)) as archive:
        styles = ET.fromstring(archive.read('xl/styles.xml'))
        sheet = ET.fromstring(archive.read(f'xl/worksheets/sheet{sheet_number}.xml'))
    borders = styles.find(f'{{{S}}}borders')
    xfs = styles.find(f'{{{S}}}cellXfs')
    cells = {c.get('r'): c for c in sheet.findall(f'{{{S}}}sheetData/{{{S}}}row/{{{S}}}c')}
    def edges(ref):
        node = cells.get(ref)
        xf = xfs[int(node.get('s', '0')) if node is not None else 0]
        border = borders[int(xf.get('borderId', '0'))]
        return {part.tag.rsplit('}', 1)[-1]: part.get('style') for part in border if part.get('style')}
    return styles, sheet, edges


def alter_member(data, member, edit):
    # Test-only corruption to exercise the independent read-back gate.
    stream = io.BytesIO()
    with zipfile.ZipFile(io.BytesIO(data)) as source, zipfile.ZipFile(stream, 'w') as target:
        for name in source.namelist():
            content = source.read(name)
            if name == member:
                node = ET.fromstring(content)
                edit(node)
                content = ET.tostring(node, encoding='utf-8', xml_declaration=True)
            target.writestr(name, content)
    return stream.getvalue()


class ExcelBorderTests(unittest.TestCase):
    def setUp(self):
        self.model = markdown_model(MD, '基本設計書_100008_職員番号入力.md')
        self.data = package(self.model)

    def test_default_format_is_borderless_general(self):
        styles, _, edges = read_styles(self.data)
        xf = styles.find(f'{{{S}}}cellXfs')[0]
        for key in ('borderId', 'fillId', 'numFmtId', 'fontId'):
            self.assertEqual('0', xf.get(key))
        self.assertEqual(0, STYLES['blank'])
        self.assertEqual({}, edges('XFD1048576'))

    def test_all_worksheet_margins_have_no_borders(self):
        for index, spec in enumerate(self.model['sheets'], 1):
            _, _, edges = read_styles(self.data, index)
            for ref in ('AV999', 'BK1', 'ZZ500', 'XFD1048576'):
                self.assertEqual({}, edges(ref), (spec['name'], ref))
        _, _, edges = read_styles(self.data)
        for ref in ('N6', 'AV6', 'AV7', 'AV28', 'AU37', 'A37'):
            self.assertEqual({}, edges(ref), ref)

    def test_cover_right_boundary_and_bottom_corners(self):
        _, _, edges = read_styles(self.data)
        self.assertEqual({'right': 'double'}, edges('AU7'))
        self.assertEqual({'right': 'double', 'bottom': 'double'}, edges('AU9'))
        self.assertEqual({'right': 'thin', 'bottom': 'thin'}, edges('AU14'))
        self.assertEqual({'right': 'thin', 'bottom': 'thin'}, edges('AU28'))

    def test_cover_merge_anchor_matches_v2_outline_convention(self):
        _, _, edges = read_styles(self.data)
        self.assertEqual(dict.fromkeys(('left', 'right', 'top', 'bottom'), 'double'), edges('O6'))
        self.assertEqual({'top': 'double'}, edges('P6'))
        self.assertEqual({'left': 'double'}, edges('O7'))
        self.assertEqual({}, edges('P7'))
        self.assertEqual({}, edges('AT8'))

    def test_cover_gaps_and_company_are_not_framed(self):
        _, _, edges = read_styles(self.data)
        for ref in ('O10', 'AU10', 'O11', 'AU11', 'O21', 'AU21', 'O29', 'AU29'):
            self.assertEqual({}, edges(ref), ref)

    def test_normal_item_table_borders_are_preserved(self):
        _, _, edges = read_styles(self.data, 3)
        full = dict.fromkeys(('left', 'right', 'top', 'bottom'), 'thin')
        for ref in ('A3', 'J3'):
            self.assertEqual(full, edges(ref))
        self.assertEqual({}, edges('K2'))
        self.assertEqual({}, edges('A1'))  # Unframed list title.

    def test_header_merge_keeps_only_outer_edges(self):
        _, _, edges = read_styles(self.data, 2)
        self.assertEqual({'top': 'medium', 'bottom': 'double'}, edges('B1'))
        self.assertEqual({'right': 'thin', 'top': 'medium', 'bottom': 'double'}, edges('J1'))
        self.assertEqual({'left': 'medium'}, edges('A2'))

    def test_explicit_styles_outside_print_area_are_clipped(self):
        model = deepcopy(self.model)
        model['sheets'][0]['cell_styles']['A1'] = 'body'
        _, _, edges = read_styles(package(model))
        self.assertEqual({}, edges('A1'))
        self.assertTrue(verify(package(model), model)['borders_verified'])

    def test_default_border_corruption_is_rejected(self):
        def corrupt(styles):
            xfs = styles.find(f'{{{S}}}cellXfs')
            xfs[0].set('borderId', xfs[STYLES['body']].get('borderId'))
        data = alter_member(self.data, 'xl/styles.xml', corrupt)
        with self.assertRaisesRegex(ValueError, 'Default cell style'):
            verify(data, self.model)

    def test_missing_right_edge_is_rejected(self):
        def corrupt(sheet):
            for cell in sheet.findall(f'{{{S}}}sheetData/{{{S}}}row/{{{S}}}c'):
                if cell.get('r') == 'AU7':
                    cell.set('s', str(STYLES['blank']))
        data = alter_member(self.data, 'xl/worksheets/sheet1.xml', corrupt)
        with self.assertRaisesRegex(ValueError, 'merged border'):
            verify(data, self.model)

    def test_explicit_margin_border_is_rejected(self):
        def corrupt(sheet):
            for cell in sheet.findall(f'{{{S}}}sheetData/{{{S}}}row/{{{S}}}c'):
                if cell.get('r') == 'A1':
                    cell.set('s', str(STYLES['body']))
        data = alter_member(self.data, 'xl/worksheets/sheet1.xml', corrupt)
        with self.assertRaisesRegex(ValueError, 'outside the document range'):
            verify(data, self.model)

    def test_row_and_column_inherited_borders_are_rejected(self):
        for dimension in ('row', 'col'):
            def corrupt(sheet):
                node = sheet.find(f'{{{S}}}sheetData/{{{S}}}row') if dimension == 'row' else sheet.find(f'{{{S}}}cols/{{{S}}}col')
                node.set('s' if dimension == 'row' else 'style', str(STYLES['body']))
            data = alter_member(self.data, 'xl/worksheets/sheet1.xml', corrupt)
            with self.assertRaisesRegex(ValueError, 'row/column default'):
                verify(data, self.model)

    def test_text_and_print_settings_remain_intact(self):
        result = verify(self.data, self.model)
        self.assertTrue(result['borders_verified'])
        self.assertEqual(5, result['sheets'])
        with zipfile.ZipFile(io.BytesIO(self.data)) as z:
            book = ET.fromstring(z.read('xl/workbook.xml'))
            print_areas = [n.text for n in book.find(f'{{{S}}}definedNames') if n.get('name') == '_xlnm.Print_Area']
            self.assertEqual("'表紙'!$O$6:$AU$36", print_areas[0])

    def test_unmerged_table_padding_does_not_inherit_body_borders(self):
        from docsite.excel_model import markdown_model as legacy_model
        model = legacy_model('# Example\n\n|A|B|C|\n|---|---|---|\n|1|2|3|\n\n|D|E|\n|---|---|\n|4|5|', 'x.md')
        data = package(model)
        for i, sheet in enumerate(model['sheets'], 1):
            _, _, edges = read_styles(data, i)
            for row, spec in enumerate(sheet['rows'], 1):
                if not spec['values']:
                    for column in ('A', 'B', 'C'):
                        self.assertEqual({}, edges(f'{column}{row}'))
        self.assertTrue(verify(data, model)['borders_verified'])


    def test_explicit_three_pattern_contract(self):
        from docsite.excel_package import border_pattern
        self.assertEqual(['cover','normal','list','normal','normal'],
                         [border_pattern(s) for s in self.model['sheets']])
        checks = verify(self.data, self.model)['border_checks']
        self.assertEqual(['cover','normal','list','normal','normal'],
                         [s['pattern'] for s in checks])

    def test_normal_has_medium_outer_frame_on_all_four_sides(self):
        from docsite.excel_package import col
        for i in (2,4,5):
            spec = self.model['sheets'][i-1]
            last = len(spec['rows'])
            _, _, edges = read_styles(self.data, i)
            for row in range(1,last+1):
                self.assertEqual('medium', edges(f'A{row}').get('left'))
                self.assertEqual('medium', edges(f'BJ{row}').get('right'))
            for column in range(1,63):
                self.assertEqual('medium', edges(f'{col(column)}1').get('top'))
                self.assertEqual('medium', edges(f'{col(column)}{last}').get('bottom'))
            for ref in (f'A{last+1}',f'BJ{last+1}','BK1',f'BK{last}'):
                self.assertEqual({}, edges(ref), (spec['name'],ref))

    def test_normal_frame_does_not_become_an_internal_grid(self):
        _, _, edges = read_styles(self.data, 2)
        self.assertEqual({}, edges('B2'))
        self.assertEqual({}, edges('BI2'))
        self.assertEqual({'left':'medium'}, edges('A2'))
        self.assertEqual({'right':'medium'}, edges('BJ2'))

    def test_reference_cover_company_rule_and_no_global_rectangle(self):
        _, _, edges = read_styles(self.data)
        for ref in ('O36','P36','AU36'):
            self.assertEqual({'top':'thin'}, edges(ref))
        for ref in ('N36','AV36','O35','AU35','O37'):
            self.assertEqual({}, edges(ref))

    def test_reference_list_header_and_unbordered_title_and_trailing_rows(self):
        _, _, edges = read_styles(self.data, 3)
        for ref in ('A2','B2','J2'):
            self.assertEqual({'left':'medium','right':'medium','top':'medium'},edges(ref))
        for ref in ('A1','J1','K2',f"A{len(self.model['sheets'][2]['rows'])}"):
            self.assertEqual({},edges(ref))

    def test_missing_normal_right_or_bottom_frame_fails(self):
        last = len(self.model['sheets'][1]['rows'])
        for target in ('BJ2',f'BJ{last}',f'B{last}'):
            def corrupt(sheet):
                for c in sheet.findall(f'{{{S}}}sheetData/{{{S}}}row/{{{S}}}c'):
                    if c.get('r') == target:
                        c.set('s', str(STYLES['blank']))
            bad = alter_member(self.data, 'xl/worksheets/sheet2.xml', corrupt)
            with self.assertRaisesRegex(ValueError,'medium outer frame'):
                verify(bad,self.model)

    def test_frame_follows_actual_row_count_not_pilot_coordinates(self):
        from docsite.excel_package import col
        short = markdown_model('# x\n\n## 概要\ntext','x.md')
        long = markdown_model('# x\n\n## 概要\n'+
                              '\n\n'.join('段落'+str(i) for i in range(90)),'x.md')
        self.assertGreater(len(long['sheets'][1]['rows']),len(short['sheets'][1]['rows']))
        for model in (short,long):
            data=package(model);self.assertTrue(verify(data,model)['borders_verified'])
            last=len(model['sheets'][1]['rows'])
            _,_,edges=read_styles(data,2)
            self.assertEqual('medium',edges(f'BJ{last}')['bottom'])
            self.assertEqual({},edges(f'BJ{last+1}'))

    def test_catalog_isolation_and_determinism(self):
        other=markdown_model('# other\n\n## その他\nExample','other.md')
        package(other)
        self.assertEqual(self.data,package(self.model))

    def test_unknown_border_pattern_fails_closed(self):
        model=deepcopy(self.model)
        model['sheets'][0]['border_pattern']='surprise'
        with self.assertRaisesRegex(ValueError,'Unknown Excel border'):
            package(model)

if __name__ == '__main__':
    unittest.main()
