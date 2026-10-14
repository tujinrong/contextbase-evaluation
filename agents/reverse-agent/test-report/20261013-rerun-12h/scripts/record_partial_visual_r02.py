"""Bind previously performed native inspections; explicitly keep the full gate pending."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

REPORT = Path(__file__).resolve().parents[1]
AGENT = REPORT.parents[1]
SNAPSHOT = AGENT / '.tmp/20261013-rerun-12h/source-only/snapshot'
RENDER = REPORT / 'render/search-basic-r02'

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    pins = json.loads((RENDER / 'render-pins.json').read_text(encoding='utf-8'))
    md = Path(pins['source'])
    if sha(md) != 'ef7967cf6f086e0475f7a747709afb3abdc1bd7e6813afa5d524956a6d8c3a21':
        raise ValueError('Native-inspected draft changed')
    images = [RENDER / name for name in ('layout-001.png', 'diagram-009.png', 'diagram-012.png')]
    declared = json.dumps(pins, ensure_ascii=False)
    for image in images:
        if sha(image) not in declared:
            raise ValueError('Native image differs from the sealed renderer output')
    resources = [SNAPSHOT / 'sources' / name for name in (
        'Views/Students/Search.cshtml', 'Views/Shared/_Layout.cshtml', 'wwwroot/css/site.css',
        'Infrastructure/SearchContextStore.cs', 'database/001_schema.sql')]
    record = {'schema': 'reverse-agent-native-visual-review/1',
        'documentId': 'CSHARP_ASPNET-BAS-STU-01', 'referenceMode': 'source-only',
        'canonicalDocumentPath': str(md.resolve()), 'canonicalRelativePath': '基本設計書/01_学生検索画面.md',
        'documentSha256': sha(md), 'sourceSnapshotSha256': sha(SNAPSHOT / 'manifest.json'),
        'reviewScope': 'STATIC_PROJECTION_VS_SOURCE_RESOURCES', 'originalApplicationExecuted': False,
        'reviewedImages': [{'path': str(image.resolve()), 'sha256': sha(image)} for image in images],
        'reviewedSourceResources': [{'path': str(resource.resolve()), 'sha256': sha(resource)} for resource in resources],
        'modesReviewed': ['NORMAL_SEARCH_EDITOR_FIRST_PAGE_WITH_NEXT'],
        'findings': [
            {'severity': 'INFO', 'detail': '通常検索Editorの静的投影を原ビュー・共有レイアウト・CSSと比較。12条件の2列配置、11一覧見出し、前ページ無効・次ページ有効を確認。表示値は文書で宣言した投影用placeholder。'},
            {'severity': 'INFO', 'detail': 'DB関連図とUse保持状態の図を原サイズで表示して線・ラベルの重なりと読める範囲を確認。全文の意味承認を行っていない。'},
            {'severity': 'PENDING', 'detail': '残る状態、10図、文書全体のnative比較は未完了。'},
            {'severity': 'ERROR', 'detail': 'この候補の項目一覧は新しい10列検査を通過していない。最終採用と別の途中記録。'}],
        'approved': False, 'reviewer': '/root', 'reviewedAt': datetime.now(timezone.utc).isoformat(),
        'pixelEquivalenceToRunningApplicationVerified': False, 'formalQualityGatePassed': False}
    destination = REPORT / 'visual-review/search-basic-r02-partial.json'
    with destination.open('x', encoding='utf-8') as output:
        json.dump(record, output, ensure_ascii=False, indent=2)
        output.write('\n')
    print({'imagesActuallyReviewed': len(images), 'approved': False})

if __name__ == '__main__':
    main()
