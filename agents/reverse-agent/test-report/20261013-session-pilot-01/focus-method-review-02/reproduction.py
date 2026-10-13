"""Synthetic method audit, without model/application execution or source edits."""
from datetime import datetime, timezone
import json
from pathlib import Path
import sys
import tempfile
from unittest.mock import patch

from bs4 import BeautifulSoup
from markdown_it import MarkdownIt
from contextbase.ai import provider, rendering
from contextbase.ai.validation import validate_document
from contextbase.tests.test_ai_validation import document, PATH


def main():
    report = Path(__file__).resolve().parent
    agent = report.parents[2]
    implementations = ['src/contextbase/ai/provider.py', 'src/contextbase/ai/workflow.py',
                       'src/contextbase/ai/prompts.py', 'src/contextbase/ai/rendering.py',
                       'src/contextbase/ai/validation.py', 'src/contextbase/ai/__main__.py']
    from contextbase.ai.capsule import sha256
    before = {name: sha256((agent/name).read_bytes()) for name in implementations}
    with tempfile.TemporaryDirectory(prefix='method-readonly-audit-', dir=agent/'.tmp') as temporary:
        root = Path(temporary).resolve()
        if not root.is_relative_to((agent/'.tmp').resolve()):
            raise ValueError('Synthetic scratch root escapes agent workspace')
        text = document() + '\n[共通契約](../共通/契約.md#入口)\n[同文書](#概要)\n[外部引用](https://example.invalid/docs)\n'
        markup = MarkdownIt('commonmark', {'html': True}).enable('table').render(text)
        derived, removed = rendering._sanitize(markup, root, root)
        def anchors(html):
            return [{'text': tag.get_text(), 'href': tag.get('href')}
                    for tag in BeautifulSoup(html, 'html.parser').find_all('a')]
        link = {'structureFindings': validate_document(text, PATH, expected_document_id='DEMO-001'),
                'originalAnchors': anchors(markup), 'derivedAnchors': anchors(derived), 'removed': removed}
        workspace = root/'workspace'; workspace.mkdir()
        job = root/'interrupted-job'
        interrupted = False
        with patch.object(provider, 'resolve_cli', return_value=Path(sys.executable)), \
             patch.object(provider.subprocess, 'run', side_effect=KeyboardInterrupt):
            try:
                provider.run_job(workspace, job, 'Synthetic input only; no source application or model execution.')
            except KeyboardInterrupt:
                interrupted = True
        interruption = {'interruptPropagated': interrupted, 'resultRecorded': (job/'result.json').exists(),
                        'retainedArtifacts': sorted(path.name for path in job.iterdir()),
                        'externalCliProcessesStarted': 0}
    baseline = agent.parents[1]/'test-project1/spec-analysis/CSharp_ASPNET/20261013-pilot-v2-r2/spec/detail'
    baselines = []
    parser = MarkdownIt('commonmark', {'html': True}).enable('table')
    for name in ('student-search.md', 'student-editor.md'):
        raw = (baseline/name).read_bytes()
        links = anchors(parser.render(raw.decode('utf-8')))
        baselines.append({'document': name, 'sha256': sha256(raw), 'anchors': links,
                          'affectedRelativeAnchorCount': sum(item['href'] is not None
                            and not item['href'].startswith(('#', 'http:', 'https:', 'mailto:')) for item in links)})
    after = {name: sha256((agent/name).read_bytes()) for name in implementations}
    result = {'schema': 'reverse-ai-method-audit-reproduction/1',
              'createdAt': datetime.now(timezone.utc).isoformat(), 'externalCliJobsStarted': 0,
              'relativeCitation': link, 'keyboardInterrupt': interruption,
              'existingAssistedBaselines': baselines,
              'implementationHashesBefore': before, 'implementationHashesAfter': after,
              'productionSourcesUnchanged': before == after}
    with (report/'reproduction-results.json').open('x', encoding='utf-8') as handle:
        json.dump(result, handle, ensure_ascii=False, indent=2); handle.write('\n')
    print(json.dumps(result, ensure_ascii=False))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
