"""Public syntax adapter contracts against hand-written, never executed sources."""

import hashlib
from pathlib import Path
import subprocess
import unittest
from unittest.mock import patch

from contextbase.analysis.adapters import index_source, index_source_isolated


FIXTURES = Path(__file__).parent / "fixtures" / "analysis"


def index(path, text):
    return index_source(path, text, source_sha256=hashlib.sha256(text.encode("utf-8")).hexdigest())


class AnalysisAdapterTests(unittest.TestCase):
    def test_two_language_business_fixtures_preserve_locations_and_unresolved_calls(self):
        for language, suffix, method in (("csharp", ".cs", "Save"), ("java", ".java", "save")):
            with self.subTest(language=language):
                results = []
                for fixture in sorted((FIXTURES / language).glob("*" + suffix)):
                    text = fixture.read_text(encoding="utf-8")
                    result = index(language + "/" + fixture.name, text)
                    self.assertEqual("complete", result["status"], result["diagnostics"])
                    self.assertTrue(result["backend"]["available"])
                    self.assertFalse(result["capabilities"]["semanticBinding"])
                    self.assertFalse(result["capabilities"]["dataFlow"])
                    for collection in ("symbols", "imports", "calls"):
                        for record in result[collection]:
                            e = record["evidence"][0]
                            self.assertEqual(result["path"], e["path"])
                            self.assertGreaterEqual(e["startLine"], 1)
                            self.assertLessEqual(e["endLine"], len(text.splitlines()))
                            self.assertEqual(hashlib.sha256(text.encode()).hexdigest(), e["sha256"])
                    results.append(result)
                symbols = [s for r in results for s in r["symbols"]]
                overloads = [s for s in symbols if s["name"] == method]
                self.assertEqual(3, len(overloads))
                self.assertEqual(3, len({s["id"] for s in overloads}))
                self.assertEqual(3, len({(s["scope"], s["signature"]) for s in overloads}))
                self.assertTrue(all("business" in s["qualifiedName"].lower() for s in overloads))
                constructors = [s for s in symbols if s["kind"] == "constructor"]
                self.assertEqual(1, len(constructors))
                self.assertIn("登録Service", constructors[0]["qualifiedName"])
                calls = [c for r in results for c in r["calls"]]
                self.assertTrue(any(c["receiver"] == "rules" for c in calls))
                self.assertTrue(any(c["name"] == method for c in calls))
                self.assertTrue(all(c["resolution"] == "unresolved" for c in calls))
                self.assertTrue(all("targetId" not in c for c in calls))
                registration = results[0]
                text = (FIXTURES / language / ("Registration" + suffix)).read_text(encoding="utf-8")
                for symbol in registration["symbols"]:
                    self.assertIn(symbol["name"], "\n".join(text.splitlines()[symbol["startLine"]-1:symbol["endLine"]]))

    def test_symbol_identity_survives_line_shift_and_body_edit(self):
        for path, first, second in (
            ("a.cs", "namespace N { class C { int F(int x) { return x; } } }",
             "\n\nnamespace N { class C { int F(int x) { return x + 1; } } }"),
            ("A.java", "package n; class C { int f(int x) { return x; } }",
             "\n\npackage n; class C { int f(int x) { return x + 1; } }"),
        ):
            with self.subTest(path=path):
                a, b = index(path, first), index(path, second)
                self.assertEqual("complete", a["status"])
                self.assertEqual([s["id"] for s in a["symbols"]], [s["id"] for s in b["symbols"]])
                self.assertNotEqual(a["symbols"][0]["startLine"], b["symbols"][0]["startLine"])
                self.assertNotEqual(a["symbols"][0]["evidence"], b["symbols"][0]["evidence"])

    def test_path_and_namespace_distinguish_identity(self):
        for path, text in (("A.cs", "namespace N { class C { void Save() {} } }"),
                           ("A.java", "package n; class C { void save() {} }")):
            with self.subTest(path=path):
                a = index(path, text)
                b = index("other/" + path, text)
                self.assertTrue(set(s["id"] for s in a["symbols"]).isdisjoint(s["id"] for s in b["symbols"]))
                altered = text.replace("namespace N", "namespace Other").replace("package n", "package other")
                c = index(path, altered)
                self.assertTrue(set(s["id"] for s in a["symbols"]).isdisjoint(s["id"] for s in c["symbols"]))

    def test_invalid_syntax_is_partial_with_original_line_evidence(self):
        for path, text in (("Broken.cs", "\nclass C { void Save( {"),
                           ("Broken.java", "\nclass C { void save( {")):
            with self.subTest(path=path):
                result = index(path, text)
                self.assertEqual("partial", result["status"])
                self.assertTrue(result["diagnostics"])
                self.assertTrue(all(d["evidence"] for d in result["diagnostics"]))

    def test_missing_parser_does_not_fall_back_to_guessing(self):
        with patch("contextbase.analysis.adapters._load_parser", side_effect=ImportError("missing grammar")):
            result = index("A.cs", "class A {}")
        self.assertEqual("unsupported", result["status"])
        self.assertEqual("parser-unavailable", result["diagnostics"][0]["code"])
        self.assertFalse(result["backend"]["available"])
        self.assertEqual([], result["symbols"])

    def test_missing_syntax_node_is_diagnosed(self):
        result = index("A.java", "class C { void m() { return; }")
        self.assertEqual("partial", result["status"])
        self.assertIn("missing-syntax", [d["code"] for d in result["diagnostics"]])

    def test_parser_failure_is_explicit(self):
        class BrokenParser:
            def parse(self, data):
                raise RuntimeError("parse failed")
        with patch("contextbase.analysis.adapters._load_parser", return_value=BrokenParser()):
            result = index("A.java", "class A {}")
        self.assertEqual("failed", result["status"])
        self.assertEqual([], result["symbols"])

    def test_resource_limits_do_not_return_silent_prefix(self):
        with patch("contextbase.analysis.adapters.MAX_SOURCE_BYTES", 8):
            result = index("A.cs", "class A {}")
        self.assertEqual("limit-exceeded", result["status"])
        self.assertEqual([], result["symbols"])
        with patch("contextbase.analysis.adapters.MAX_NODES", 2):
            result = index("A.java", "class A {}")
        self.assertEqual("limit-exceeded", result["status"])
        self.assertEqual([], result["symbols"])

    def test_unknown_format_and_invalid_hash(self):
        result = index("template.txt", "class A {}")
        self.assertEqual("unsupported", result["status"])
        self.assertFalse(result["capabilities"]["syntax"])
        result = index_source("A.cs", "class A {}", source_sha256="bad")
        self.assertEqual("failed", result["status"])
        self.assertEqual("invalid-source-hash", result["diagnostics"][0]["code"])

    def test_crlf_unicode_and_original_byte_hash(self):
        text = "// 説明\r\nnamespace 空間;\r\nclass 登録 { void 保存() {} }\r\n"
        original_hash = hashlib.sha256(text.encode("utf-16-le")).hexdigest()
        result = index_source("登録.cs", text, source_sha256=original_hash)
        self.assertEqual("complete", result["status"])
        method = next(s for s in result["symbols"] if s["name"] == "保存")
        self.assertEqual("空間.登録.保存", method["qualifiedName"])
        self.assertEqual(3, method["startLine"])
        self.assertEqual(original_hash, method["evidence"][0]["sha256"])

    def test_explicit_interface_members_do_not_collapse(self):
        text = "class C : I, J { void I.Save() {} void J.Save() {} }"
        result = index("C.cs", text)
        self.assertEqual("complete", result["status"])
        members = [s for s in result["symbols"] if s["name"] == "Save"]
        self.assertEqual(2, len(members))
        self.assertEqual(2, len({s["id"] for s in members}))

    def test_constructor_call_is_syntax_only(self):
        for path, text in (("A.cs", "class A { object Make() { return new Thing(1); } }"),
                           ("A.java", "class A { Object make() { return new Thing(1); } }")):
            with self.subTest(path=path):
                result = index(path, text)
                call = next(c for c in result["calls"] if c["kind"] == "construction")
                self.assertEqual("Thing", call["name"])
                self.assertEqual("unresolved", call["resolution"])
                self.assertIn("method", result["capabilities"]["symbolKinds"])

    def test_isolated_large_line_numbers_regression(self):
        # Point.row in py-tree-sitter 0.26.0 over-decrefs non-cached integers.
        # Exercise that structure using synthetic source, not pilot code.  The
        # worker contains a regression crash instead of killing unittest.
        for path, header, method in (("Large.cs", "namespace N; class Large {", "int F{0}(int x) {{ return x; }}"),
                                     ("Large.java", "package n; class Large {", "int f{0}(int x) {{ return x; }}")):
            with self.subTest(path=path):
                text = "\n" * 300 + header + "\n" + "\n".join(method.format(i) for i in range(160)) + "\n}\n"
                result = index_source_isolated(path, text, source_sha256=hashlib.sha256(text.encode()).hexdigest())
                self.assertEqual("complete", result["status"], result["diagnostics"])
                methods = [s for s in result["symbols"] if s["kind"] == "method"]
                self.assertEqual(160, len(methods))
                self.assertEqual(302, methods[0]["startLine"])
                self.assertEqual(461, methods[-1]["endLine"])

    def test_isolated_worker_crash_returns_failed(self):
        completed = subprocess.CompletedProcess([], 3221225477, stdout="", stderr="native crash")
        with patch("contextbase.analysis.adapters.subprocess.run", return_value=completed) as run:
            result = index_source_isolated("A.cs", "class A {}", source_sha256="a" * 64)
        self.assertEqual("failed", result["status"])
        self.assertEqual("parser-worker-exit", result["diagnostics"][0]["code"])
        self.assertIn("3221225477", result["diagnostics"][0]["message"])
        self.assertEqual([], result["symbols"])
        self.assertFalse(run.call_args.kwargs["shell"])

    def test_isolated_timeout_protocol_and_size_fail_closed(self):
        with patch("contextbase.analysis.adapters.subprocess.run", side_effect=subprocess.TimeoutExpired([], 0.1)):
            result = index_source_isolated("A.java", "class A {}", source_sha256="a" * 64, timeout_seconds=0.1)
        self.assertEqual("failed", result["status"])
        self.assertEqual("parser-operation-timeout", result["diagnostics"][0]["code"])
        with patch("contextbase.analysis.adapters.subprocess.run", return_value=subprocess.CompletedProcess([], 0, "{}", "")):
            result = index_source_isolated("A.java", "class A {}", source_sha256="a" * 64)
        self.assertEqual("failed", result["status"])
        self.assertEqual("parser-worker-protocol", result["diagnostics"][0]["code"])
        with patch("contextbase.analysis.adapters.MAX_SOURCE_BYTES", 8), patch("contextbase.analysis.adapters.subprocess.run") as run:
            result = index_source_isolated("A.cs", "class A {}", source_sha256="a" * 64)
        self.assertEqual("limit-exceeded", result["status"])
        run.assert_not_called()


if __name__ == "__main__":
    unittest.main()
