"""Save source excerpts for a bounded AI privacy clarification, without authoring prose."""
from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

report = Path(__file__).resolve().parent
repo = report.parents[4]
snapshot = repo / "agents/reverse-agent/.tmp/20261013-rerun-12h/source-only/snapshot"
manifest_bytes = (snapshot / "manifest.json").read_bytes()
manifest_sha = hashlib.sha256(manifest_bytes).hexdigest()
if manifest_sha != "2f64e2211b1fcd7850203927fc75b5a7f2ce37457cc2afe88c8065d9f931273b":
    raise ValueError("source-only manifest differs from the sealed pilot pin")
manifest = json.loads(manifest_bytes.decode("utf-8"))
registered = {entry["path"]: entry["sha256"] for entry in manifest["files"]}
ranges = {
    "Infrastructure/SearchContextStore.cs": [(9, 15)],
    "Views/Students/Search.cshtml": [(4, 8)],
    "Views/Students/Edit.cshtml": [(6, 6), (10, 10), (13, 13)],
    "Views/Shared/_MessagePanel.cshtml": [(3, 3)],
    "Views/Shared/_Layout.cshtml": [(1, 1)],
    "Web/Controllers/StudentsController.cs": [(38, 38)],
    "Infrastructure/WebHostSetup.cs": [(23, 23), (27, 27)],
    "Core/SqlServerStudentService.cs": [(234, 234), (306, 307), (319, 322), (385, 390), (396, 396), (410, 416)],
    "Core/StudentNormalizer.cs": [(47, 57)],
    "appsettings.json": [(1, 1)],
}
records = []
for name, sections in ranges.items():
    path = snapshot / "sources" / name
    data = path.read_bytes()
    digest = hashlib.sha256(data).hexdigest()
    if registered.get(name) != digest:
        raise ValueError("privacy supplement source differs from the sealed manifest")
    lines = data.decode("utf-8").splitlines()
    records.append({"path": "sources/" + name, "sha256": digest,
                    "sections": [{"startLine": start, "endLine": end,
                                  "rawLines": [{"line": n, "text": lines[n - 1]} for n in range(start, end + 1)]}
                                 for start, end in sections]})
value = {
    "classification": "SOURCE_ONLY_RAW_PERSONAL_DATA_BOUNDARY_LOCAL_AI_SUPPLEMENT_SCOPE",
    "createdAt": datetime.now(timezone.utc).isoformat(), "snapshotManifestSha256": manifest_sha,
    "rawSourceRecords": records,
    "instructions": [
        "既存の正しい全文と完成factsを維持し、個人データの受渡し・出力・監査境界について原ソースが表す範囲を既存補足説明へAIが局所的に補足する。実行・ネットワーク・参考設計・評価期待値を使わず、固定された原source行だけを根拠に全文Markdownを返す。",
        "検索条件のPOST受信、serverのApplied/LastResult保持、生成される学生URLのstudentIdおよびcontext鍵を追う。検索氏名・電話・住所をこれらコード生成URLや検索専用cookieに載せる処理が観測できるかを確認する。入力者が任意に作るURL、全cookie、全ルートに個人情報がないという保証へ拡張しない。SignInAsyncに渡すclaimsとの区別も保持する。",
        "一覧、編集、共通メッセージ、共通headerが通常のRazor記法で値を出すこと、および手組エラーHTMLがメッセージへHtmlEncodeを適用する境界を確認する。必要なら全manifest rawに明示Raw出力の有無を照合する。依存frameworkや実HTMLを実行していないため、実稼働の安全性を証明した表現にしない。",
        "監査の実メソッド、INSERT列、changed_columnsへ変更列名配列をSerializeする引数、および自由記述Reasonを追う。変更列の前後値を渡す処理と列名配列を混同せず、Reasonやactor/targetを含む監査全体に個人情報がないと保証しない。Textの長さ・制御文字・改行・trimとPII伏字は区別する。",
        "必要ならapp-specificの通常障害ログ出力とappsettingsのログレベルを原source全体で照合する。出力処理の未観測をframework/provider/運用ログの無出力・個人情報なしへ拡張しない。固定案内と受付IDも実コードの受渡し範囲として記載する。",
        "番号付きサブフローと対応本文、全分岐/例外/catch順/保持値/結果code、10列画面項目、同日可、Unknownの復帰案内、必須六h4とメタデータ・原文根拠を落とさない。今回の補足以外の正しい本文と図を不用意に変更しない。",
    ],
    "semanticProseAssembledByPython": False, "expectedRubricIncluded": False,
    "applicationOrSqlExecuted": False,
}
output = report / "personal-data-source-supplement-scope.json"
with output.open("x", encoding="utf-8", newline="\n") as stream:
    json.dump(value, stream, ensure_ascii=False, indent=2)
    stream.write("\n")
print(json.dumps({"scope": str(output), "sha256": hashlib.sha256(output.read_bytes()).hexdigest(),
                  "sourceFiles": len(records)}, ensure_ascii=False))
