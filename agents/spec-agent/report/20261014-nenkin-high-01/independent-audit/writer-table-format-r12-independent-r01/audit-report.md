# Independent writer table-format r12 audit

Status: PASS_TECHNICAL_CODE_ONLY. 66/66 code-only cases passed.

Input SHA256:
- nenkin_writer_driver_r11.py: be2a1a686eae3058226c6f630af17a9d5c1cfc2c0e6c1d7f259dd9db52f2dcfb
- nenkin_writer_driver_r12_candidate.py: 530cd857d4e6246251570ecc5f76da75a53f8152edbccf8a9382a1695701e5a1
- nenkin_table_format_supplement_schema_r01.json: f52cfc32df8d28074d2fdcf2cf5bf289e60745fd9f754ee6bf3adf88837fb9a9

AST: 23 original functions unchanged; 6 changed (recheck, prepare, scoped_review, text_pin, run, main); 3 added (with_table_format_metadata, table_format_selection, table_format_revision_context); 3 constants added. Original imports, non-function nodes, existing SCHEMAS constants and entry guard unchanged.

The extracted pure functions were tested with synthetic virtual pin, plan and file metadata. Scope includes two canonical table kinds, exact IDs/paths, schema/policy identity, false authority flags, conflicting pins, binding and recheck drift, restricted selection, and retention of full original/prior revision context.

The policy contains the cell fact retention, table-only HEADER/detail LIST, external h3/paragraph/fence/diagram exclusions, and planned GRID reference state distinctions. This is a review of generic policy text, not proof of actual Markdown or source fact compliance.

Actual provider executions: 0. Actual source/plan/context/capsule/raw/Markdown/supplement/evaluation/production job/frozen runtime reads or executions: 0. Actual driver module, binding/bootstrap/main/prepare/run/review/text_pin executions: 0. Generic jsonschema dependency was imported.

Limitations:
- No business/source semantic accuracy, native fidelity, 95-point score, formal evaluation, actual Markdown compliance, generation success or AI review approval was tested or granted.
- Policy text is checked as inert canonical-format instructions only; retention of all actual source facts and tables remains an AI generation/review obligation.
- No actual recheck binding, provider, production job, existing text-pin schema file or frozen runtime module was read/imported/executed. Existing schema constants and all original core AST were compared only.
- safe/raw/load/sha and binding were replaced solely in extracted functions by a PureWindowsPath virtual filesystem and synthetic fixtures; native filesystem symlink handling and races were not tested.
- Before/after pin checks do not prove atomicity, race freedom or internal analysis/draft callback checks.
- The policy and preserved revision context use shallow copies; intended metadata references remain shared, and this audit grants no deep immutability proof.

See audit-results.json for each test, and audit_runner.py for the isolated harness.

Dependency setup note: an optional local vendor installation was interrupted after parent supplied generic dependency paths. That vendor was not imported by this audit. Optional recursive cleanup was automatically rejected as "blocked by policy" with no more specific reason; vendor is retained under this audit output directory.
