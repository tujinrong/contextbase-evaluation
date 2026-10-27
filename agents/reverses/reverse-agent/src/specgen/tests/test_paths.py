"""Regression: canonicalize root aliases before comparing descendant paths."""
from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from specgen.engine import config, inventory, projects, run


class RootPathTests(unittest.TestCase):
    def test_noncanonical_root_is_accepted_without_weakening_containment(self):
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp)
            (base / "parent").mkdir()
            actual = base / "repo"
            (actual / "input/p").mkdir(parents=True)
            (actual / "input/p/app.py").write_text("def hello():\n    return 1\n", encoding="utf-8")
            (actual / "specgen.toml").write_text('input="input"\noutput="output"\n', encoding="utf-8")
            # This exercises alias normalization on every OS without symlink privilege.
            alias = base / "parent" / ".." / "repo"
            cfg = config(alias, "specgen.toml")
            project = projects(alias, cfg)[0]
            self.assertEqual(inventory(alias, project, cfg)[0]["path"], "input/p/app.py")
            self.assertEqual(run(alias, cfg)["exit_code"], 0)
            self.assertEqual(run(alias, cfg)["cached"], 1)
            with self.assertRaises(ValueError):
                config(alias, "../outside.toml")


if __name__ == "__main__":
    unittest.main()
