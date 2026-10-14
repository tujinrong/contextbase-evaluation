"""Bind exactly the two native images inspected by /root, without approving the full gate."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

report = Path(__file__).resolve().parents[1]
agent = report.parents[1]
snapshot = agent / '.tmp/20261013-rerun-12h/training-assisted/snapshot'
render = report / 'render/assisted-search-basic-r01'
sha = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()
pins = json.loads((render / 'render-pins.json').read_text(encoding='utf-8'))
md = Path(pins['source'])
if sha(md) != 'f3388bf9e052e789b762fa90449118192777cf88a0cd6c1f13444b067aebd589':
    raise ValueError('The actually inspected draft has changed')
if pins['referenceMode'] != 'training-assisted' or sha(snapshot / 'manifest.json') != pins['sourceSnapshotManifestSha256']:
    raise ValueError('Wrong mode or source capsule')
images = [render / name for name in ('layout-001.png', 'diagram-009.png')]
if any(sha(path) not in json.dumps(pins, ensure_ascii=False) for path in images):
    raise ValueError('Images differ from renderer seal')
resources = [snapshot / 'sources' / name for name in (
    'Views/Students/Search.cshtml', 'Views/Shared/_Layout.cshtml', 'wwwroot/css/site.css')]
record = {
    'schema': 'reverse-agent-native-visual-review/1', 'documentId': pins['documentId'],
    'referenceMode': pins['referenceMode'], 'canonicalDocumentPath': str(md.resolve()),
    'canonicalRelativePath': pins['canonicalDocumentPath'], 'documentSha256': sha(md),
    'sourceSnapshotSha256': sha(snapshot / 'manifest.json'),
    'reviewScope': 'STATIC_PROJECTION_VS_SOURCE_RESOURCES', 'originalApplicationExecuted': False,
    'reviewedImages': [{'path': str(path.resolve()), 'sha256': sha(path)} for path in images],
    'reviewedSourceResources': [{'path': str(path.resolve()), 'sha256': sha(path)} for path in resources],
    'modesReviewed': ['INITIAL_SEARCH_EDITOR_UNSEARCHED'],
    'findings': [
        {'severity': 'INFO', 'detail': '初期Editorの静的投影で2列12条件、11一覧見出し、未検索、無効pagerを原ビュー・共有CSSと比較。実アプリ画面ではない。'},
        {'severity': 'ERROR', 'detail': 'clearフロー図のラベル折返しがCSRFと401の途中を分割しており読みづらい。'},
        {'severity': 'ERROR', 'detail': 'この候補は項目一覧10列の検査未通過。別のAI改訂が進行中。'},
        {'severity': 'PENDING', 'detail': '他状態・残る14図・全本文画像は未閲覧。原設計PNGは未閲覧。'}],
    'approved': False, 'reviewer': '/root', 'reviewedAt': datetime.now(timezone.utc).isoformat(),
    'pixelEquivalenceToRunningApplicationVerified': False, 'formalQualityGatePassed': False,
}
with (report / 'visual-review/assisted-search-basic-r01-partial.json').open('x', encoding='utf-8', newline='\n') as stream:
    json.dump(record, stream, ensure_ascii=False, indent=2)
    stream.write('\n')
print(json.dumps({'imagesActuallyReviewed': len(images), 'approved': False}))
