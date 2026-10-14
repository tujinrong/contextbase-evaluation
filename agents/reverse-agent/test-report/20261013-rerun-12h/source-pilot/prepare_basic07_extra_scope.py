"""Pin independent source findings and native geometry observations as revision data."""
from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

report = Path(__file__).resolve().parent
repo = report.parents[4]
base = repo / "agents/reverse-agent/.tmp/20261013-rerun-12h/source-only"
review_file = base / "jobs/search-detail-05-review/review-verified.json"
review_data = review_file.read_bytes()
review = json.loads(review_data.decode("utf-8"))
if review["documentId"] != "CSHARP_ASPNET-DET-CSharp_ASPNET-SCR-STU-001":
    raise ValueError("source findings must come from the pinned current source-only search review")
image = report.parent / "render/search-basic-r04/diagram-010.png"
pins = report.parent / "render/search-basic-r04/render-pins.json"
pins_value = json.loads(pins.read_text(encoding="utf-8"))
image_sha = hashlib.sha256(image.read_bytes()).hexdigest()
if image_sha != "f709ab7deba9e6cfc0dc7dff89c961044e8ee0b6a14a271b4ab803c447db27a7" or pins_value["sourceSha256"] != "8751f6474def2b8bbfe5c29fedfcb8418368cb2d703845611ca2f957fd3a2463":
    raise ValueError("current native geometry observations must match the pinned basic06 manuscript")
geometry = {
    "classification": "SOURCE_ONLY_CURRENT_NATIVE_DIAGRAM_LABEL_GEOMETRY_SCOPE",
    "createdAt": datetime.now(timezone.utc).isoformat(),
    "documentSha256": pins_value["sourceSha256"], "renderPinsFile": str(pins),
    "renderPinsSha256": hashlib.sha256(pins.read_bytes()).hexdigest(),
    "inspectedNativeImage": str(image), "imageSha256": image_sha,
    "inspectedDimensions": {"width": 665, "height": 1306},
    "nativeObservation": "rootと作者担当が同じnative imageを閲覧し、GETがG/ET、解放と経路が単語途中で改行されていることを確認した。意味・全25図・全状態の合格とは扱わない。",
    "instructions": [
        "現basic06の25図の意味、分割単位、続き位置、状態受渡し、分岐条件、catch順、結果codeと本文対応を維持する。図全体を再設計しない。",
        "図ラベルは短い番号や用語と自然な改行位置で局所的に整える。GET、解放、経路など一語を文字途中で折り返さず、必要なら語の前後に明示改行を置く。短い図ラベルへ移す際も条件や保持値を削らず、番号を対応本文・条件表へ結ぶ。",
        "幅1200px高さ1600px程度の推奨を維持し、文字を小さくして押し込む、強制切り捨て、重要説明や接続線の省略はしない。共通HTTP/個人データ/再表示のsource-backed補足を優先する。",
    ], "semanticProseAssembledByPython": False, "expectedRubricIncluded": False,
    "allNativeDiagramsOrStatesVerified": False,
}
redisplay = {
    "classification": "SOURCE_ONLY_SHARED_SEARCH_REDISPLAY_REVIEW_SCOPE",
    "createdAt": datetime.now(timezone.utc).isoformat(),
    "independentReviewFile": str(review_file), "independentReviewSha256": hashlib.sha256(review_data).hexdigest(),
    "sourceBackedFindings": review["findings"],
    "verification": "作者担当が封印rawのController13-16、service107-108、View8の整数除算、Present21、HostSetup23を読取り照合し、指摘の代入・条件・式と一致を確認。原App/DB/Frameworkは非実行。",
    "instructions": [
        "同じ検索画面を説明する基本設計にも、前記source-backed指摘が該当する記載を原文から確認し、論理上の画面再表示・最終応答として局所補足する。詳細仕様は型・物理式の説明を担う。根拠と役割を区別し、原稿の不足を別画像へ移して合格にしない。",
        "pageSize=0がバインド後アクションへ届く条件の経路に限定する。サービス検証拒否、局所422、受信0のモデル代入、View整数除算による描画例外、応答開始前なら外側503・開始後なら同catch対象外を追う。未実行のbinder変換やframework応答開始時点を確定しない。全不正pageSizeが必ず503になるとは記載しない。",
        "未検索表示のページ番号は初期/クリア時の既定1と、既存Appliedを保持した再表示を区別する。後者では保持ページ2、件数を0扱いした全頁1による2／1が生じ得る。保持する条件とリビジョン、反映と失敗の順序を落とさない。",
    ], "semanticProseAssembledByPython": False, "expectedRubricIncluded": False,
}
for name, value in (("search-basic-07-geometry-scope.json", geometry),
                    ("search-shared-redisplay-source-scope.json", redisplay)):
    path = report / name
    with path.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)
        stream.write("\n")
    print(json.dumps({"scope": str(path), "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}, ensure_ascii=False))
