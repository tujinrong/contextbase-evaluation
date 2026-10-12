"""Provider boundary regressions; all model processes are substituted fixtures."""
import copy
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

from contextbase.ai import provider


class ProviderTests(unittest.TestCase):
    def setUp(self):
        temp_root = Path(__file__).resolve().parents[3] / ".tmp"
        temp_root.mkdir(exist_ok=True)
        self.temp = tempfile.TemporaryDirectory(prefix="provider-unit-", dir=temp_root)
        self.root = Path(self.temp.name)
        self.workspace = self.root / "許可ソース"
        self.workspace.mkdir()
        (self.workspace / "snippet.txt").write_text("return menu;", encoding="utf-8")
        (self.workspace / "manifest.json").write_text('{"referenceSpecificationIncluded":false}', encoding="utf-8")
        self.job = self.root / "試行 新規"
        self.cli = self.root / "codex.exe"
        self.cli.write_bytes(b"fixture-not-executed")
        self.original = (self.workspace / "snippet.txt").read_bytes()
        self.resolve_patch = patch.object(provider, "resolve_cli", return_value=self.cli)
        self.resolve_patch.start()
        self.addCleanup(self.resolve_patch.stop)
        self.addCleanup(self.temp.cleanup)
        self.seen = []

    def fake(self, *, answer='{"text":"日本語"}', exit_code=0, events=None, stderr=b"", timeout=False, error=None):
        if events is None:
            events = [{"type": "turn.completed", "usage": {"input_tokens": 12, "output_tokens": 3}}]

        def execute(command, **kwargs):
            self.seen.append((command, kwargs))
            if error is not None:
                raise error
            for event in events:
                raw = event if isinstance(event, bytes) else json.dumps(event, ensure_ascii=False).encode("utf-8")
                kwargs["stdout"].write(raw + b"\n")
            kwargs["stderr"].write(stderr)
            kwargs["stdout"].flush()
            kwargs["stderr"].flush()
            if answer is not None:
                answer_path = Path(command[command.index("--output-last-message") + 1])
                answer_path.write_bytes(answer if isinstance(answer, bytes) else answer.encode("utf-8"))
            if timeout:
                raise subprocess.TimeoutExpired(command, kwargs["timeout"])
            return subprocess.CompletedProcess(command, exit_code)

        return execute

    def run_fake(self, fake=None, **kwargs):
        with patch.object(provider.subprocess, "run", side_effect=fake or self.fake()):
            result = provider.run_job(self.workspace, self.job, "日本語の根拠を説明してください。", **kwargs)
        self.assertEqual(self.original, (self.workspace / "snippet.txt").read_bytes())
        self.assertEqual(result, json.loads((self.job / "result.json").read_text(encoding="utf-8")))
        return result

    def test_success_is_one_ephemeral_read_only_process_with_user_model(self):
        result = self.run_fake()
        self.assertEqual("passed", result["metadata"]["status"])
        self.assertEqual({"text": "日本語"}, result["answer"])
        self.assertEqual(0, result["exit_code"])
        self.assertEqual({"input_tokens": 12, "output_tokens": 3}, result["usage"])
        self.assertEqual(1, len(self.seen))
        command, options = self.seen[0]
        self.assertIn("--ephemeral", command)
        self.assertEqual("read-only", command[command.index("--sandbox") + 1])
        self.assertIn('approval_policy="never"', command)
        self.assertIn("project_doc_max_bytes=0", command)
        self.assertIn("--json", command)
        self.assertNotIn("--model", command)
        self.assertNotIn("--ignore-user-config", command)
        self.assertFalse(options["shell"])
        self.assertEqual(self.workspace, options["cwd"])
        self.assertTrue(Path(command[command.index("--output-last-message") + 1]).is_absolute())

    def test_utf8_input_preserves_prompt_and_includes_common_boundary(self):
        self.run_fake()
        payload = self.seen[0][1]["input"]
        self.assertIsInstance(payload, bytes)
        self.assertFalse(payload.startswith(b"\xef\xbb\xbf"))
        decoded = payload.decode("utf-8")
        self.assertIn("日本語の根拠", decoded)
        self.assertIn("Never execute, import, evaluate", decoded)
        self.assertIn("spec-eval", decoded)
        self.assertIn("Do not write files or use network tools", decoded)
        self.assertIn("Do not download model weights", decoded)
        self.assertEqual(payload, (self.job / "prompt.txt").read_bytes())

    def test_reference_design_policy_keeps_source_only_and_assisted_distinct(self):
        self.run_fake()
        policy = self.seen[0][1]["input"].decode("utf-8")
        self.assertIn("In source-only jobs do not read reference specifications", policy)
        self.assertIn("current capsule manifest", policy)
        self.assertIn("trainingReferenceAuthorizedByUser=true", policy)
        self.assertIn("referenceSpecificationIncluded=true", policy)
        self.assertIn("referenceFiles", policy)
        self.assertIn("Distinguish intended design from source-observed implementation", policy)
        self.assertIn("Never treat", policy)
        self.assertIn("a reference design as execution evidence", policy)
        self.assertIn("expected answers, spec-eval", policy)

    def test_source_only_manifest_without_authorization_remains_source_only(self):
        result = self.run_fake()
        self.assertEqual("source-only", result["metadata"]["reference_mode"])
        self.assertFalse(result["metadata"]["training_reference_authorized"])

    def test_explicit_authorized_assisted_manifest_is_recorded(self):
        manifest = {"mode": "training-assisted", "trainingReferenceAuthorizedByUser": True,
                    "referenceSpecificationIncluded": True,
                    "referenceFiles": [{"path": "reference-designs/basic.md", "sha256": "a" * 64}]}
        (self.workspace / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
        result = self.run_fake()
        self.assertEqual("training-assisted", result["metadata"]["reference_mode"])
        self.assertTrue(result["metadata"]["training_reference_authorized"])

    def test_assisted_label_without_authorization_is_not_permission(self):
        manifest = {"mode": "training-assisted", "trainingReferenceAuthorizedByUser": False,
                    "referenceSpecificationIncluded": True, "referenceFiles": [{"path": "reference-designs/basic.md"}]}
        (self.workspace / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
        result = self.run_fake()
        self.assertEqual("source-only", result["metadata"]["reference_mode"])

    def test_reference_path_escape_is_rejected_before_cli(self):
        manifest = {"mode": "training-assisted", "trainingReferenceAuthorizedByUser": True,
                    "referenceSpecificationIncluded": True, "referenceFiles": [{"path": "reference-designs/../../outside.md"}]}
        (self.workspace / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
        result = self.run_fake()
        self.assertEqual("invalid_capsule_manifest", result["metadata"]["status"])
        self.assertEqual([], self.seen)

    def test_text_answer_is_preserved_byte_for_byte(self):
        raw = "  日本語の本文。\n\n"
        result = self.run_fake(self.fake(answer=raw))
        self.assertEqual(raw, result["answer"])
        self.assertEqual(raw.encode("utf-8"), (self.job / "answer.txt").read_bytes())

    def test_json_answer_is_not_rewritten_or_extracted_from_fences(self):
        raw = ' { "text" : "日本語", "nullable": null } \n'
        self.run_fake(self.fake(answer=raw))
        self.assertEqual(raw.encode("utf-8"), (self.job / "answer.txt").read_bytes())

    def test_structured_schema_is_validated_and_unchanged(self):
        schema = {"type": "object", "required": ["text"], "properties": {"text": {"type": "string"}}, "additionalProperties": False}
        before = copy.deepcopy(schema)
        result = self.run_fake(schema=schema)
        self.assertEqual("passed", result["metadata"]["status"])
        self.assertEqual(before, schema)
        self.assertEqual(before, json.loads((self.job / "schema.json").read_text(encoding="utf-8")))
        command = self.seen[0][0]
        self.assertEqual(str(self.job / "schema.json"), command[command.index("--output-schema") + 1])

    def test_schema_invalid_answer_is_failure_without_answer_rewrite(self):
        raw = '{"text":17}'
        result = self.run_fake(self.fake(answer=raw), schema={"type": "object", "properties": {"text": {"type": "string"}}})
        self.assertEqual("schema_invalid_answer", result["metadata"]["status"])
        self.assertEqual({"text": 17}, result["answer"])
        self.assertEqual(raw.encode(), (self.job / "answer.txt").read_bytes())
        self.assertEqual("type", result["metadata"]["schema_errors"][0]["validator"])

    def test_schema_invalid_input_never_starts_process(self):
        result = self.run_fake(schema={"type": "imaginary"})
        self.assertEqual("invalid_schema", result["metadata"]["status"])
        self.assertEqual([], self.seen)

    def test_external_schema_reference_is_rejected_without_network_lookup(self):
        result = self.run_fake(schema={"$ref": "https://example.invalid/schema.json"})
        self.assertEqual("invalid_schema", result["metadata"]["status"])
        self.assertEqual("external_schema_reference_forbidden", result["metadata"]["error_code"])
        self.assertEqual([], self.seen)

    def test_unresolved_local_schema_reference_is_recorded_as_failure(self):
        result = self.run_fake(schema={"$ref": "#/$defs/missing"})
        self.assertEqual("schema_validation_error", result["metadata"]["status"])

    def test_missing_jsonschema_dependency_fails_before_process(self):
        import builtins
        original_import = builtins.__import__

        def blocked_import(name, *args, **kwargs):
            if name == "jsonschema":
                raise ImportError("fixture dependency absent")
            return original_import(name, *args, **kwargs)

        with patch("builtins.__import__", side_effect=blocked_import):
            result = self.run_fake(schema={"type": "object"})
        self.assertEqual("provider_unavailable", result["metadata"]["status"])
        self.assertEqual("jsonschema_dependency_unavailable", result["metadata"]["error_code"])
        self.assertEqual([], self.seen)

    def test_schema_requires_json_without_fence_repair(self):
        raw = '```json\n{"text":"日本語"}\n```'
        result = self.run_fake(self.fake(answer=raw), schema={"type": "object"})
        self.assertEqual("invalid_answer_json", result["metadata"]["status"])
        self.assertEqual(raw, result["answer"])

    def test_nonfinite_json_is_not_accepted_as_structured_answer(self):
        result = self.run_fake(self.fake(answer='{"value":NaN}'), schema={"type": "object"})
        self.assertEqual("invalid_answer_json", result["metadata"]["status"])

    def test_duplicate_json_members_are_rejected_without_choosing_one_value(self):
        raw = '{"text":"first","text":"second"}'
        result = self.run_fake(self.fake(answer=raw), schema={"type": "object"})
        self.assertEqual("invalid_answer_json", result["metadata"]["status"])
        self.assertEqual(raw, result["answer"])

    def test_timeout_preserves_partial_events_and_has_no_fake_exit_code(self):
        result = self.run_fake(self.fake(answer=None, timeout=True, stderr=b"partial stderr"), timeout_seconds=0.25)
        self.assertEqual("timeout", result["metadata"]["status"])
        self.assertIsNone(result["exit_code"])
        self.assertIsNone(result["answer"])
        self.assertEqual(b"partial stderr", (self.job / "stderr.log").read_bytes())
        self.assertEqual(12, result["usage"]["input_tokens"])
        self.assertEqual(0.25, self.seen[0][1]["timeout"])

    def test_nonzero_exit_is_failure_even_with_valid_answer(self):
        result = self.run_fake(self.fake(exit_code=2, stderr=b"unsupported flag"))
        self.assertEqual("cli_failed", result["metadata"]["status"])
        self.assertEqual(2, result["exit_code"])
        self.assertEqual({"text": "日本語"}, result["answer"])
        self.assertEqual(1, len(self.seen))

    def test_success_exit_with_missing_answer_is_failure(self):
        result = self.run_fake(self.fake(answer=None))
        self.assertEqual("missing_answer", result["metadata"]["status"])

    def test_whitespace_answer_is_failure(self):
        result = self.run_fake(self.fake(answer=" \n"))
        self.assertEqual("missing_answer", result["metadata"]["status"])

    def test_invalid_answer_utf8_is_failure(self):
        result = self.run_fake(self.fake(answer=b"\xff\xfe"))
        self.assertEqual("invalid_answer_encoding", result["metadata"]["status"])

    def test_error_event_with_zero_exit_is_failure(self):
        result = self.run_fake(self.fake(events=[{"type": "turn.failed", "error": {"message": "fixture failure"}}]))
        self.assertEqual("failed_events", result["metadata"]["status"])
        self.assertEqual(1, len(result["metadata"]["error_events"]))
        self.assertIsNone(result["usage"])

    def test_item_error_is_not_silently_passed(self):
        result = self.run_fake(self.fake(events=[{"type": "item.completed", "item": {"type": "error"}}]))
        self.assertEqual("failed_events", result["metadata"]["status"])

    def test_invalid_event_json_is_failure_without_altering_raw_log(self):
        result = self.run_fake(self.fake(events=[b"not JSON"]))
        self.assertEqual("invalid_events", result["metadata"]["status"])
        self.assertEqual([1], result["metadata"]["invalid_event_lines"])
        self.assertEqual(b"not JSON\n", (self.job / "events.jsonl").read_bytes())

    def test_multiple_usage_observations_are_preserved_without_guessed_total(self):
        events = [{"type": "turn.completed", "usage": {"input_tokens": 5}}, {"type": "turn.completed", "usage": {"input_tokens": 7}}]
        result = self.run_fake(self.fake(events=events))
        self.assertEqual({"turns": [{"input_tokens": 5}, {"input_tokens": 7}]}, result["usage"])

    def test_absent_usage_is_null(self):
        result = self.run_fake(self.fake(events=[{"type": "item.completed", "item": {"type": "agent_message"}}]))
        self.assertEqual("passed", result["metadata"]["status"])
        self.assertIsNone(result["usage"])
        self.assertFalse(result["metadata"]["usage_reported"])

    def test_start_failure_preserves_error_type_without_dumping_environment(self):
        result = self.run_fake(self.fake(error=OSError("fixture failure")))
        self.assertEqual("provider_unavailable", result["metadata"]["status"])
        self.assertEqual("OSError", result["metadata"]["error_type"])
        self.assertTrue((self.job / "events.jsonl").exists())
        self.assertTrue((self.job / "stderr.log").exists())

    def test_unavailable_cli_is_recorded_without_synthetic_answer(self):
        with patch.object(provider, "resolve_cli", side_effect=FileNotFoundError("fixture CLI absent")):
            result = self.run_fake()
        self.assertEqual("provider_unavailable", result["metadata"]["status"])
        self.assertIsNone(result["answer"])
        self.assertIsNone(result["exit_code"])
        self.assertEqual([], self.seen)

    def test_secret_environment_is_not_serialized_into_metadata(self):
        with patch.dict(os.environ, {"OPENAI_API_KEY": "fixture-secret-never-print"}):
            result = self.run_fake()
        for filename in ("result.json", "prompt.txt", "events.jsonl", "stderr.log"):
            self.assertNotIn(b"fixture-secret-never-print", (self.job / filename).read_bytes())
        self.assertNotIn("environment", result["metadata"])

    def test_existing_job_directory_is_rejected_without_overwrite(self):
        self.job.mkdir()
        original = self.job / "answer.txt"
        original.write_text("keep", encoding="utf-8")
        with patch.object(provider.subprocess, "run") as execute:
            with self.assertRaises(FileExistsError):
                provider.run_job(self.workspace, self.job, "test")
            execute.assert_not_called()
        self.assertEqual("keep", original.read_text(encoding="utf-8"))

    def test_empty_existing_job_directory_is_also_rejected(self):
        self.job.mkdir()
        with self.assertRaises(FileExistsError):
            provider.run_job(self.workspace, self.job, "test")

    def test_missing_workspace_is_rejected_before_creating_job(self):
        with self.assertRaises(ValueError):
            provider.run_job(self.root / "missing", self.job, "test")
        self.assertFalse(self.job.exists())

    def test_invalid_timeout_is_rejected_without_side_effect(self):
        for value in (0, -1, float("nan"), float("inf"), True, "1"):
            with self.subTest(timeout=value), self.assertRaises((ValueError, TypeError)):
                provider.run_job(self.workspace, self.job, "test", timeout_seconds=value)
        self.assertFalse(self.job.exists())

    def test_symlink_job_parent_is_rejected(self):
        link = self.root / "link"
        try:
            link.symlink_to(self.workspace, target_is_directory=True)
        except OSError:
            self.skipTest("Host does not permit directory symlinks")
        with self.assertRaises(ValueError):
            provider.run_job(self.workspace, link / "job", "test")
        self.assertFalse((self.workspace / "job").exists())


class CliResolutionTests(unittest.TestCase):
    def setUp(self):
        temp_root = Path(__file__).resolve().parents[3] / ".tmp"
        temp_root.mkdir(exist_ok=True)
        self.temp = tempfile.TemporaryDirectory(prefix="provider-resolver-", dir=temp_root)
        self.root = Path(self.temp.name)
        self.cli = self.root / "codex.exe"
        self.cli.write_bytes(b"not executed")
        self.addCleanup(self.temp.cleanup)

    def test_explicit_absolute_cli_wins_without_touching_user_config(self):
        with patch.dict(os.environ, {"CONTEXTBASE_CODEX_CLI": str(self.cli)}), patch.object(provider.shutil, "which") as lookup:
            self.assertEqual(self.cli, provider.resolve_cli())
            lookup.assert_not_called()

    def test_relative_explicit_path_is_rejected(self):
        with patch.dict(os.environ, {"CONTEXTBASE_CODEX_CLI": "codex.exe"}):
            with self.assertRaises(ValueError):
                provider.resolve_cli()

    def test_missing_cli_does_not_have_fallback_success(self):
        with patch.dict(os.environ, {}, clear=True), patch.object(provider.shutil, "which", return_value=None):
            with self.assertRaises(FileNotFoundError):
                provider.resolve_cli()

    def test_shell_wrapper_is_rejected(self):
        wrapper = self.root / "codex.cmd"
        wrapper.write_text("not executed", encoding="utf-8")
        with patch.dict(os.environ, {"CONTEXTBASE_CODEX_CLI": str(wrapper)}):
            with self.assertRaises(ValueError):
                provider.resolve_cli()

    def test_installed_cli_symlink_resolves_to_single_tool(self):
        link = self.root / "linked-codex.exe"
        try:
            link.symlink_to(self.cli)
        except OSError:
            self.skipTest("Host does not permit file symlinks")
        with patch.dict(os.environ, {"CONTEXTBASE_CODEX_CLI": str(link)}):
            self.assertEqual(self.cli, provider.resolve_cli())

    def test_path_resolution_selects_single_native_executable(self):
        with patch.dict(os.environ, {}, clear=True), patch.object(provider.shutil, "which", return_value=str(self.cli)) as lookup:
            self.assertEqual(self.cli, provider.resolve_cli())
            self.assertEqual(1, lookup.call_count)


if __name__ == "__main__":
    unittest.main()
