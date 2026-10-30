"""Encoding-boundary regressions; no expected values are read from UI output."""
from pathlib import Path
import re
import sys
import tempfile
import unittest

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
from vba_text import read_vba_source, vbe_text


def literal_value(expression):
    """Independent restricted evaluator for the transport's literal grammar."""
    atoms = re.findall(r'"(?:[^"\r\n]|"")*"|ChrW\(&H[0-9A-F]+\)', expression)
    values = []
    for atom in atoms:
        values.append(atom[1:-1].replace('""', '"') if atom.startswith('"')
                      else chr(int(atom[7:-1], 16)))
    return ''.join(values).encode('utf-16-le', errors='surrogatepass').decode('utf-16-le')


class VbaEncodingTests(unittest.TestCase):
    def test_japanese_runtime_value(self):
        for value in ('社員登録・編集［新規］', '氏名カナ', 'ｱｲｳ', 'g/j/p/q/y 0123', '有', '～〜－−', '😀'):
            with self.subTest(value=value):
                text = vbe_text('value = "' + value + '"')
                text.encode('ascii')
                self.assertEqual(literal_value(text.split('=', 1)[1]), value)

    def test_quote_and_apostrophe_in_literal(self):
        value = '会社 "A" の O\'Brien'
        result = vbe_text('value = "' + value.replace('"', '""') + '"')
        self.assertEqual(literal_value(result.split('=', 1)[1]), value)

    def test_comment_does_not_become_code(self):
        self.assertEqual(vbe_text("' 日本語 \"comment\""), "' \\u65e5\\u672c\\u8a9e \"comment\"")
        self.assertTrue(vbe_text('Rem 日本語').startswith('Rem \\u65e5'))
        self.assertIn("'", vbe_text('value="日本語" \' comment "x"'))

    def test_ascii_is_unchanged(self):
        self.assertEqual(vbe_text('Option Explicit\nvalue = "abc"\n'), 'Option Explicit\r\nvalue = "abc"\r\n')

    def test_no_cr_cr_lf(self):
        self.assertEqual(vbe_text('x\r\ny\rz\n'), 'x\r\ny\r\nz\r\n')

    def test_single_character_has_invertible_string_expression(self):
        self.assertEqual(vbe_text('x="有"'), 'x=("" & ChrW(&H6709))')

    def test_long_japanese_literal_has_safe_physical_lines(self):
        value = '基本情報・職務' * 15
        result = vbe_text('value="' + value + '"')
        self.assertLessEqual(max(map(len, result.splitlines())), 902)
        self.assertIn(' & _\r\n', result)
        self.assertEqual(literal_value(result.split('=', 1)[1]), value)

    def test_non_ascii_const_and_identifier_rejected(self):
        for text in ('Const name="日本語"', 'Attribute VB_Description = "日本語"', 'Dim 日本語 As String'):
            with self.subTest(text=text), self.assertRaises(ValueError):
                vbe_text(text)

    def test_invalid_source_rejected(self):
        for text in ('x="unclosed', 'x=\x00', 'x="\ud800"'):
            with self.subTest(text=repr(text)), self.assertRaises((ValueError, UnicodeError)):
                vbe_text(text)

    def test_cp932_file_roundtrip_and_bom_rejection(self):
        parent = ROOT / '.tmp/japanese-encoding/unit'
        parent.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=parent) as owned:
            target = Path(owned) / 'source.bas'
            expected = 'Option Explicit\r\nvalue="基本情報・職務"\r\n'
            target.write_bytes(expected.encode('cp932'))
            self.assertEqual(read_vba_source(target), expected)
            for bom in (b'\xef\xbb\xbf', b'\xff\xfe', b'\xfe\xff'):
                target.write_bytes(bom + b'abc')
                with self.assertRaises(ValueError):
                    read_vba_source(target)

    def test_all_production_sources(self):
        sources = sorted((ROOT / 'src/modules').glob('*.bas')) + sorted((ROOT / 'src/classes').glob('*.cls'))
        self.assertEqual(len(sources), 33)
        for path in sources:
            with self.subTest(path=path.name):
                vbe_text(read_vba_source(path)).encode('ascii', errors='strict')


if __name__ == '__main__':
    unittest.main(verbosity=2)
