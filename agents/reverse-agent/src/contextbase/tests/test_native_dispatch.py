"""Native verification belongs to selected profiles, not a hard-coded client."""
import os
import subprocess
import tempfile
import unittest
from pathlib import Path
from contextbase.pipeline import negative_control_command


class NativeDispatchTests(unittest.TestCase):
    def execute(self, total, detected):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)
            (root/'different_target.py').write_text(f"def mutation_checks(root): return {{'total': {total}, 'detected': {detected}}}\n",encoding='utf-8')
            return subprocess.run(negative_control_command('different_target'),cwd=root,
                                  env={**os.environ,'PYTHONPATH':str(root)},capture_output=True)
    def test_selected_profile_controls_its_own_test_count(self):
        result=self.execute(2,2)
        self.assertEqual(result.returncode,0,result.stderr)
    def test_empty_native_controls_cannot_pass(self):
        self.assertNotEqual(self.execute(0,0).returncode,0)
    def test_invalid_native_module_is_rejected(self):
        with self.assertRaises(ValueError):negative_control_command('../input/code.py')

if __name__=='__main__':unittest.main()
