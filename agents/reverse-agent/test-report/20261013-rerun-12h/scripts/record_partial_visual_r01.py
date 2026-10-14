"""Record a native inspection already performed; no semantic approval inferred."""
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

REPORT = Path(__file__).resolve().parents[1]
AGENT = REPORT.parents[1]
REPO = AGENT.parents[1]
SNAPSHOT = AGENT / '.tmp/20261013-rerun-12h/source-only/snapshot'
RENDER = REPORT / 'render/search-basic-r01'

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    pins = json.loads((RENDER / 'render-pins.json').read_text(encoding='utf-8'))
    md = Path(pins['source'])
    image = RENDER / 'layout-001.png'
    if sha(md) != pins['sourceSha256']:
        raise ValueError('Draft changed after native inspection')
    if sha(image) != '3d7858bb070157031053c2c86d52d79e5f34fb147cc8977a455e5416cda745ec':
        raise ValueError('Inspected image changed')
    resources = [SNAPSHOT / 'sources' / relative for relative in (
        'Views/Students/Search.cshtml', 'Views/Shared/_Layout.cshtml',
        'wwwroot/css/site.css')]
    result = {
        'schema': 'reverse-agent-native-visual-review/1',
        'documentId': 'CSHARP_ASPNET-BAS-STU-01',
        'canonicalDocumentPath': str(md.resolve()),
        'canonicalRelativePath': '基本設計書/01_学生検索画面.md',
        'documentSha256': sha(md),
        'sourceSnapshotSha256': sha(SNAPSHOT / 'manifest.json'),
        'reviewScope': 'STATIC_PROJECTION_VS_SOURCE_RESOURCES',
        'originalApplicationExecuted': False,
        'reviewedImages': [{'path': str(image.resolve()), 'sha256': sha(image)}],
        'reviewedSourceResources': [{'path': str(p.resolve()), 'sha256': sha(p)} for p in resources],
        'modesReviewed': ['INITIAL_UNSEARCHED_EDITOR'],
        'findings': [
            {'severity': 'INFO', 'detail': '初期Editorの12検索条件、2列配置、11一覧見出し、空tbody、無効pagerを原画面資源と照合。画像は読め、表示領域で重なりは見られない。'},
            {'severity': 'PENDING', 'detail': '正常検索・0件・上限超過・Viewer等の状態と10図のnative画像比較は未実施。'},
            {'severity': 'ERROR', 'detail': '初稿の構造検証がERRORであり、この記録は採用判定ではない。'}],
        'approved': False,
        'reviewer': '/root',
        'reviewedAt': datetime.now(timezone.utc).isoformat(),
        'pixelEquivalenceToRunningApplicationVerified': False,
        'formalQualityGatePassed': False,
    }
    output = REPORT / 'visual-review/search-basic-r01-partial.json'
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open('x', encoding='utf-8') as stream:
        json.dump(result, stream, ensure_ascii=False, indent=2)
        stream.write('\n')
    print(json.dumps({'record': str(output), 'approved': False, 'imagesActuallyReviewed': 1}))

if __name__ == '__main__':
    main()
