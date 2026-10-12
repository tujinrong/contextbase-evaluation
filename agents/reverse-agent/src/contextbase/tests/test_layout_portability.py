"""Generated text assets must retain their seals after Git LF normalization."""
from copy import deepcopy
from pathlib import Path
import tempfile
import unittest
from contextbase.detail.layout import projection
from contextbase.shared.store import seal, verify


class LayoutPortabilityTests(unittest.TestCase):
    def test_projection_canonicalizes_generated_text_not_input(self):
        sources = {
            'Pages/Example.cshtml': '<h1>例</h1>\r\n<input name="Code">',
            'wwwroot/css/site.css': 'body{color:black}\r\np{margin:0}\r',
        }
        original = deepcopy(sources)
        document, dependencies = projection('Pages/Example.cshtml', sources, [])
        self.assertNotIn('\r', document)
        self.assertIn('body{color:black}\np{margin:0}\n', document)
        self.assertEqual(original, sources)
        self.assertEqual(document, projection('Pages/Example.cshtml', sources, [])[0])
        self.assertEqual(['Pages/Example.cshtml', 'wwwroot/css/site.css'], dependencies)

    def test_generated_asset_seal_survives_lf_storage(self):
        sources = {'Pages/Example.cshtml': '<p>本文</p>\r\n',
                   'wwwroot/css/site.css': 'body{margin:0}\r\n'}
        document, _ = projection('Pages/Example.cshtml', sources, [])
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            asset = root / 'screen.html'
            asset.write_bytes(document.encode('utf-8'))
            before = seal(root, {'schema': 'test.generated-asset.v1'})
            asset.write_bytes(asset.read_bytes().replace(b'\r\n', b'\n').replace(b'\r', b'\n'))
            self.assertEqual(before['generation'], verify(root)['generation'])


if __name__ == '__main__':
    unittest.main()
