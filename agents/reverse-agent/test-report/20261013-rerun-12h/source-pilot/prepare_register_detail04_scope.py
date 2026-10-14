"""Pin structural and existing source-scope metadata for the AI revision."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

report = Path(__file__).resolve().parent
inventory_file = report / 'candidate-inventory-r11-1234.json'
inventory = json.loads(inventory_file.read_text(encoding='utf-8'))
matches = [item for item in inventory['documents'] if item['documentId'] == 'CSHARP_ASPNET-DET-CSharp_ASPNET-SCR-STU-002'
           and item['documentSha256'] == 'e4862e102fb67e68c099948242b472cceeebdfa7f0d3da30c7c67206d272e872']
if len(matches) != 1:
    raise ValueError('structure metadata must bind the exact saved register detailed manuscript')
audit = {'documents': [{'documentId': matches[0]['documentId'], 'documentSha256': matches[0]['documentSha256'],
                        'findings': matches[0]['currentStructureFindings']}],
         'originalInventorySha256': hashlib.sha256(inventory_file.read_bytes()).hexdigest()}
http_file = report / 'shared-http-source-supplement-scope.json'
http_data = http_file.read_bytes()
scope = {
    'classification': 'SOURCE_ONLY_REGISTER_DETAILED_LOCAL_REPAIR_WITH_COMMON_SOURCE_CONFIGURATION',
    'createdAt': datetime.now(timezone.utc).isoformat(), 'documentSha256': matches[0]['documentSha256'],
    'instructions': [
        '75factsと登録詳細R1全文・既存項目属性・根拠・分岐・関連表を保持する。previousIndependentReviewのmajor2、minor1と構造指摘をAIが修正し、全文を返す。',
        '画面項目一覧はNo、グループ、項目名、種類、入出力、DB連携項目、候補取得元、必須、形式・桁、説明の正確な10列へ既存属性を配置する。入出力はI,O,I／O,‐。元の物理項目名、HTML属性、DTO/DB対応、NULL・長さ・候補取得元、条件付き必須、説明・根拠を切り捨てない。',
        '原Views/Students/Edit.cshtml:8–13の選択可能条件、disabled、既存値保持と終了区分の期間重複を実際の非実行HTML投影と状態差分に対応させる。boolean trueは属性名又は空、falseは属性を省略する。実HTTP接続・JSは追加しない。',
        '論理削除図の応答未開始と例外種別の判定を分け、WebFault.Statusを保持する枝と一般例外503の枝を一致させる。応答開始後のcatch境界を拡張しない。AddScoped登録とfactoryのサービス生成時の検査を区別する。',
        '下記共通HTTP設定scopeは原sourceに固定した事実である。必要な具体値を登録画面の補足へ対応させ、配備・運用・認証やDB実適用の保証を追加しない。既に正しく記載した情報は保持する。',
        '図は条件、catch順、結果code、受け渡し値と続き位置を保持し、短い番号/用語と意図した改行で長い識別子の途中折れを避ける。イベント6h4と全表裸pipeを維持する。Pythonで本文・図・業務HTMLを組み立てない。',
    ],
    'commonSourceScope': {'file': str(http_file), 'sha256': hashlib.sha256(http_data).hexdigest(),
                         'value': json.loads(http_data)},
    'expectedRubricIncluded': False, 'semanticProseAssembledByPython': False, 'adopted': False,
}
for name, value in [('remaining-register-detail-04-structure.json', audit), ('remaining-register-detail-04-scope.json', scope)]:
    path = report / name
    with path.open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)
        stream.write('\n')
    print(json.dumps({'file': str(path), 'sha256': hashlib.sha256(path.read_bytes()).hexdigest()}, ensure_ascii=False))
