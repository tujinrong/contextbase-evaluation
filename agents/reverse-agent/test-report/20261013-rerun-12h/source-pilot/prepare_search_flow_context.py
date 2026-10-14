"""Write revision instructions/metadata only, never manuscript prose or figures."""
from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

report = Path(__file__).resolve().parent
instructions = [
    "今回のAI改訂では、前稿の全文と完成済みfacts checkpointをデータとして再利用し、画面処理フローの可読性を改善する。元ソースの実行、原稿の手作業やPythonによる修繕は行わず、AIが全体の正本Markdownを返す。",
    "大きな処理図は番号付きサブフローへ分割する。全体の入口と出口、分割前後の接続先、各続き位置の識別子、および受け渡す状態を本文と図で対応させる。図を分割した結果、別図への参照だけで処理の順序や状態が不明にならないようにする。",
    "既存の事実・条件・分岐・catchの順序・接続先・結果code・保持する値・例外・未接続処理の区別・原文根拠をすべて維持する。可読性のために重要な条件や処理を一般化、切り捨て、図から黙って省略しない。",
    "各サブフローは推奨として幅1200px、高さ1600px程度で読める分量にする。これは可読性の目安であり、強制的な切り捨てや内容削減を許可しない。必要なら図の数を増やし、適切な工程境界で分ける。",
    "イベントの必須六見出しは順序付きh4のまま維持し、図は処理フローの見出し内で番号と目的を明記する。spec-meta、各章kind、10列の画面項目一覧、その入出力表記、その他の固有列、裸pipeの表を維持する。",
    "前稿の正しい本文、属性、根拠、状態差分、レイアウトおよび図以外の説明を不用意に書き換えない。変更した図に対応する接続説明以外の意味変更は、前稿の独立レビューにあるsource-backed欠陥の修正に限定する。"
]
common = {
    "classification": "SOURCE_ONLY_AI_FLOW_READABILITY_REVISION_SCOPE",
    "createdAt": datetime.now(timezone.utc).isoformat(),
    "instructions": instructions,
    "semanticProseAssembledByPython": False,
    "businessExpectedValuesIncluded": False,
    "readabilityObservationScope": "HASH_PINNED_CURRENT_SOURCE_ONLY_DRAFT_RENDER",
    "stateProjectionDeferredUntilFinalCanonicalSha": True,
}
basic = dict(common)
basic["observedDiagramSizes"] = [
    {"diagram": "diagram002", "width": 1350, "height": 2618},
    {"diagram": "diagram008", "width": 1949, "height": 3457},
    {"diagram": "diagram010", "width": 1880, "height": 2572},
]
basic["observation"] = "親担当の固定SHA基本設計05描画では上記寸法の大図があり、PDFの小全体図と拡大tileではラベルと線が境界をまたぎ読み筋を追いにくいため、AI正本側で図を分割する。"
detail = dict(common)
scope_path = report / "search-detail-05-local-repair-scope.json"
detail["previousPreparedLocalScopeFile"] = str(scope_path)
detail["previousPreparedLocalScopeSha256"] = hashlib.sha256(scope_path.read_bytes()).hexdigest()
detail["instructions"] = [*instructions,
    "詳細仕様の独立レビューmajorも同じ稿で修正する。静的HTMLのselectSortKeyでは初期studentNoだけをselectedにし、admissionDateのboolean selected属性を除去する。属性の存在を不在として読み替える直後の説明も矛盾がないように修正する。",
    "前稿の同日指定を許容する記載、Unknownの保存と削除の検索確認案内、接続された処理と未接続helperの区別を維持する。改訂対象はこのHTML属性欠陥と図の可読性・対応する接続説明の二領域である。旧準備版の『変更を属性だけに限定』はこの新しい二領域の指定へ更新される。",
]
for name, value in (("search-basic-06-flow-scope.json", basic),
                    ("search-detail-05-flow-scope.json", detail)):
    path = report / name
    with path.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)
        stream.write("\n")
    print(json.dumps({"scopeFile": str(path), "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}, ensure_ascii=False))
