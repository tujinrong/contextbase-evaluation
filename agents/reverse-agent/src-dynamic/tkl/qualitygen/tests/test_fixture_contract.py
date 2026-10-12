from pathlib import Path
import json,tempfile,unittest
from qualitygen.pilot import normalize_fixtures

class FixtureTypesTests(unittest.TestCase):
    def setup_files(self,root):
        (root/'harness').mkdir()
        (root/'harness/Program.vb').write_text('Dim row = New Dictionary(Of String,Object) From {{"sell_kbn",1}}')
        (root/'harness/EventHarness.vb').write_text('Dim row = New Dictionary(Of String,Object) From {{"sell_kbn",2}}')
        (root/'README.md').write_text('dotnet run --project pilot/TKL-011/Pilot.vbproj --configuration Release -- report/pilot/native-result.json\npython -m qualitygen --finalize-pilot')
    def test_scalar_type_is_explicit_and_deterministic(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);self.setup_files(root);normalize_fixtures(root)
            a=(root/'harness/Program.vb').read_text();normalize_fixtures(root)
            self.assertEqual(a,(root/'harness/Program.vb').read_text());self.assertIn('CShort(1)',a)
            self.assertFalse(json.loads((root/'harness/fixture-contract.json').read_text())['physical_database_types_confirmed'])
    def test_new_native_command_is_documented(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);self.setup_files(root);normalize_fixtures(root)
            self.assertIn('python -m qualitygen.native_checks',(root/'README.md').read_text())
            self.assertNotIn('dotnet run',(root/'README.md').read_text())
    def test_unknown_fixture_shape_stops_generation(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);self.setup_files(root);(root/'harness/Program.vb').write_text('new format')
            with self.assertRaises(ValueError):normalize_fixtures(root)

if __name__=='__main__':unittest.main()
