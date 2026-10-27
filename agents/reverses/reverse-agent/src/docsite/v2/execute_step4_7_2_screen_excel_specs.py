"""Local entry point for the migrated V2 step4.7.2 renderer.

Upstream: source-to-doc-v2/spec-tools/doc-tools/
execute_step4_7_2_screen_excel_specs.py@7bf3a20b. V2's dispatcher resolved
per-project templates and spawned render_document_xlsx.py. Here the existing
ContextBase CLI owns stage selection, rollback and reports; this adapter exposes
both a single Markdown conversion and whole output/md conversion, without
importing or executing another repository's project controllers.
"""
from ..excel import main

if __name__ == '__main__':
    raise SystemExit(main())
