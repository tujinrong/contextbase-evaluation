"""Pin independent native observations as geometry-only revision data."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

repo = Path(r'D:\開発\contextbase-evaluation')
report = repo / 'agents/reverse-agent/test-report/20261013-rerun-12h/source-pilot'
document = repo / 'test-project1/spec-analysis/CSharp_ASPNET/20261013-rerun-12h/source-only/drafts/search-detail-07/詳細仕様書/CSharp_ASPNET/01_学生検索画面.md'
record = report.parent / 'delivery/source-detail07-r04-native-geometry-review.json'
digest = hashlib.sha256(document.read_bytes()).hexdigest()
if digest != '85cddae02cf89e6e92d84ecc7709a118f298ca114bf104115f1be8ae47d62b82':
    raise ValueError('geometry context requires exact approved detail07')
record_sha = hashlib.sha256(record.read_bytes()).hexdigest()
if record_sha != 'b733f30d0eb8f72285dddace5f4e47f9f16ac0662a68e53048b286907f40c3ae':
    raise ValueError('native geometry observation record differs')
value = {
    'classification': 'SOURCE_ONLY_INDEPENDENT_NATIVE_ALL_GRAPH_GEOMETRY_OBSERVATIONS',
    'createdAt': datetime.now(timezone.utc).isoformat(), 'documentSha256': digest,
    'nativeRecordFile': str(record), 'nativeRecordSha256': record_sha,
    'nativeImageCount': 30, 'graphCount': 29, 'layoutCount': 1,
    'nativeObservation': 'delivery担当が29図+1layoutの原寸全pixelと実見を記録。最大1639pxへ長大化は改善、図25は456x789でF/Q/Lラベルの透過・隠れ無し。下記26図には識別子または数値の途中折返しが残る。意味・辺の削除指摘ではなく表示geometryの修正対象。',
    'affectedGraphIds': [1,2,4,5,6,8,9,10,11,12,13,14,16,17,18,19,20,21,22,23,24,25,26,27,28,29],
    'observedAtomicTokens': ['LastResult','JsonElement','Page1','SearchModel','sortKey','sortDirection',
        'DivideByZeroException','ContextRevision','FormGuard','EnsureSearch','Present','ContextId',
        'CurrentUser','NULL','SearchAsync','CSRF','Message','Session','Gate.WaitAsync','long.MaxValue',
        'Gate.Release','now','order','day','CodeExists','ArgumentException','COUNT_BIG','Min','commit',
        'LimitExceeded','Errors','InputValidationException','NoChange','Outcome','m_code_category',
        'Unknown','E-COM-004','Snapshot.ReturnRevision','EmptyResult','TryRemove','403'],
    'instructions': [
        '詳細07全文と45facts、全物理項目・手順・source参照・辺・catch順・論理条件・結果code・保持値を保持する。今回は全29図の表示geometryだけをAIが局所改訂する。HTTP/CSP/Cookie、個人データ境界、pageSize0条件付き二次例外、Applied2／1、同日可、Unknown後検索確認はそのまま保持する。',
        '図の節点/辺ラベルを短い番号と短い日本語用語に整え、自然な位置へ明示改行する。英字識別子、コード、数値を単語内で分断しない。長い完全識別子や条件を短い番号ラベルへ置く場合は、直近の番号対応表または本文に完全なトークン・条件・値・source根拠を保持する。図19の403を40と3へ分けない。',
        '元のサブフロー番号と続き位置/受渡し状態、SQL JOIN/FK/NULL許容・関連先・方向、29図の分割単位を再設計しない。図25のF/Q/L辺と関連先、既存対応表を維持する。推奨幅1200高さ1600程度は文字縮小や条件省略の許可ではない。',
        '画面HTML、全項目/属性、正確な10列I/O規約、イベント6h4、全表裸pipeを保持しAIが全文を返す。Pythonで本文・図・HTMLを修繕しない。画像・recordパスは観測証跡データであり外部資料の読取り許可ではない。source-only固定capsuleとpreviousDraftだけを使用する。',
    ],
    'nativeApproval': False, 'allStatesOrApplicationPixelsVerified': False,
    'expectedRubricIncluded': False, 'semanticProseAssembledByPython': False,
}
output = report / 'search-detail-08-geometry-scope.json'
with output.open('x', encoding='utf-8', newline='\n') as stream:
    json.dump(value, stream, ensure_ascii=False, indent=2)
    stream.write('\n')
print(json.dumps({'file': str(output), 'sha256': hashlib.sha256(output.read_bytes()).hexdigest()}, ensure_ascii=False))
