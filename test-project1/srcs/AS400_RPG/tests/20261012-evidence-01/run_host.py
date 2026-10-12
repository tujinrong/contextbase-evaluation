"""Evidence-only adapter: run the existing host tester without changing metadata."""
from pathlib import Path
import argparse, hashlib, json, sys

BASE = Path(__file__).resolve().parents[2]
parser = argparse.ArgumentParser()
parser.add_argument('--report-dir', type=Path, required=True)
args = parser.parse_args()
report = args.report_dir.resolve()
report.mkdir(parents=True, exist_ok=True)
origin = BASE / 'tools/test_host.py'
source = origin.read_text(encoding='utf-8')
replacements = {
    "exe=B/'build/STUNICODE_TEST.exe'": "exe=B/'build/20261012-evidence-01/STUNICODE_TEST.exe'",
    "(B/'metadata/spec-inputs.json').write_text": "(R/'rpg-input-manifest.json').write_text",
    "(B/'metadata/test-status.json').write_text": "(R/'rpg-test-status.json').write_text",
}
for before, after in replacements.items():
    if source.count(before) != 1:
        raise RuntimeError('Original harness changed; explicit adaptation requires review: ' + before)
    source = source.replace(before, after)
(BASE / 'build/20261012-evidence-01').mkdir(parents=True, exist_ok=True)
record = report / 'harness-adaptation.json'
with record.open('x', encoding='utf-8') as target:
    json.dump({'runId': '20261012-evidence-01', 'origin': 'tools/test_host.py',
               'originSha256': hashlib.sha256(origin.read_bytes()).hexdigest(),
               'adaptations': replacements, 'runtimeSourcesChanged': False}, target, ensure_ascii=False, indent=2)
    target.write('\n')
sys.argv = [str(origin), '--run-id', '20261012-evidence-01', '--report-dir', str(report)]
exec(compile(source, str(origin), 'exec'), {'__file__': str(origin), '__name__': '__main__'})
