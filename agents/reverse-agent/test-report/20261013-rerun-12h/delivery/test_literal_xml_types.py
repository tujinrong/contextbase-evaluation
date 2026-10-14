"""Reject actual numeric/formula coercion while accepting exporter string cells."""
import unittest
from xml.etree import ElementTree as ET
from verify_xlsx import S, values

class LiteralXmlTypes(unittest.TestCase):
    def sheet(self, cell):
        return ET.fromstring(f'<worksheet xmlns="{S}"><sheetData><row r="1">{cell}</row></sheetData></worksheet>')

    def test_exported_literal_string_preserves_leading_zero(self):
        self.assertEqual(values(self.sheet('<c r="A1" t="str"><v>001</v></c>'), {}), {'A1': '001'})

    def test_formula_looking_literal_stays_text(self):
        self.assertEqual(values(self.sheet('<c r="A1" t="str"><v>=SUM(A1:A2)</v></c>'), {}), {'A1': '=SUM(A1:A2)'})

    def test_numeric_or_date_coercion_rejected(self):
        for kind in ('n', 'd', 'b'):
            with self.subTest(kind=kind), self.assertRaises(ValueError):
                values(self.sheet(f'<c r="A1" t="{kind}"><v>001</v></c>'), {})

    def test_formula_cached_string_rejected(self):
        with self.assertRaises(ValueError):
            values(self.sheet('<c r="A1" t="str"><f>SUM(A2:A3)</f><v>001</v></c>'), {})

    def test_blank_formatted_cell_remains_empty(self):
        self.assertEqual(values(self.sheet('<c r="A1" s="1"/>'), {}), {})

if __name__ == '__main__':
    unittest.main()
