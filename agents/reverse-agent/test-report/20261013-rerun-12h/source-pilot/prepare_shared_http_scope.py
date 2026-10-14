"""Save raw source excerpts and revision instructions, never specification prose."""
from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

report = Path(__file__).resolve().parent
repo = report.parents[4]
snapshot = repo / "agents/reverse-agent/.tmp/20261013-rerun-12h/source-only/snapshot"
source = snapshot / "sources/Infrastructure/WebHostSetup.cs"
data = source.read_bytes()
digest = hashlib.sha256(data).hexdigest()
if digest != "1304d095062127ae7cbfb107dd3c88ce1a55f3f940b49e017bff45adf9eb51f8":
    raise ValueError("pinned common HTTP source differs from independent audit evidence")
lines = data.decode("utf-8").splitlines()
value = {
    "classification": "SOURCE_ONLY_RAW_HTTP_CONFIGURATION_LOCAL_AI_SUPPLEMENT_SCOPE",
    "createdAt": datetime.now(timezone.utc).isoformat(),
    "sourceFile": str(source), "sourceSha256": digest,
    "references": [{"path": "sources/Infrastructure/WebHostSetup.cs", "startLine": n, "endLine": n}
                   for n in (14, 15, 22, 25)],
    "rawSourceLines": [{"line": n, "text": lines[n - 1]} for n in (14, 15, 22, 25)],
    "instructions": [
        "今回の局所AI改訂では、前稿と完成factsを維持し、固定したWebHostSetup.csの実設定だけを既存の補足説明章へ補足する。原コードの意味をAIが根拠付きで文章または表へ記載し、全文のMarkdownを返す。Pythonや手作業で本文を追加・修繕しない。",
        "認証Cookieの名前、SecurePolicy、HttpOnly、SameSite、ExpireTimeSpan、SlidingExpiration、CSRFのHeaderNameおよびCookie保護、共通レスポンスヘッダーの具体値とCSP directive、HTTPS/StaticFiles/Routing/Authentication/Authorizationの登録順を原文どおり確認する。Cookie/API拒否やCSRFの既存記載を維持し、条件や効果を一般化しない。",
        "コードに登録された設定であることと実稼働・利用者の認証経路・Cookie配布の確認を区別し、DBへの適用、運用認証、原プログラムの実機動作を保証した記載へ拡張しない。設定値は参考設計や評価期待値から取らず、この原ソースだけを根拠にする。",
        "直前の番号付きサブフロー、続き位置と受け渡し状態、全条件/分岐/catch順、10列の画面項目一覧、同日可、Unknownの復帰指示、六h4見出し、文書ID/path/meta/kindおよび既存根拠を保持する。補足のために全体を再設計せず、正しい本文と図を不用意に書き換えない。",
    ],
    "semanticProseAssembledByPython": False,
    "expectedRubricIncluded": False,
    "originalSourceExecuted": False,
}
output = report / "shared-http-source-supplement-scope.json"
with output.open("x", encoding="utf-8", newline="\n") as stream:
    json.dump(value, stream, ensure_ascii=False, indent=2)
    stream.write("\n")
print(json.dumps({"scope": str(output), "sha256": hashlib.sha256(output.read_bytes()).hexdigest(), "sourceSha256": digest}, ensure_ascii=False))
