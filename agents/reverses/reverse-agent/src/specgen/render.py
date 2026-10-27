"""Japanese Markdown. Extracted facts and unverified business interpretation stay separate."""
from __future__ import annotations

import os
from pathlib import Path
from urllib.parse import quote
from typing import Any
from .common import safe_id, snippet


def esc(value: Any) -> str:
    import html
    return html.escape(str(value), quote=False).replace("|", "&#124;").replace("`", "&#96;").replace("[", "&#91;").replace("]", "&#93;").replace("\n", "<br>")


def table(headers: list[str], rows: list[list[Any]]) -> str:
    if not rows:
        return "該当する情報は静的解析では抽出されていません（存在しないことを意味しません）。\n"
    return "| " + " | ".join(headers) + " |\n| " + " | ".join("---" for _ in headers) + " |\n" + "\n".join(
        "| " + " | ".join(esc(v) for v in row) + " |" for row in rows) + "\n"


def evidence(root: Path, dest: Path, path: str, line: int, end: int | None = None) -> str:
    location = f"{path}:L{line}" + (f"-L{end}" if end and end != line else "")
    url = quote(os.path.relpath(root / path, dest.parent).replace(os.sep, "/"), safe="/")
    return f"[{esc(location)}]({url}#L{line}" + (f"-L{end}" if end and end != line else "") + ")"


def header(title: str) -> str:
    return f"# {esc(title)}\n\n> 自動生成・静的解析版。記載は実装上の宣言・コード断片に基づき、業務要件の確定版ではありません。\n> 未確定事項は対応する qa を参照してください。原本ソースは変更・実行していません。\n\n"


def render_tables(root: Path, dest: Path, declarations: list[dict], refs: list[dict]) -> str:
    out = header("テーブル仕様書")
    out += "## 1. 対象と読み方\n\nCREATE TABLE / 明示ORM宣言を記録します。マイグレーション適用後の最終スキーマではありません。同名の宣言は出典別に残します。列名から論理名・業務上の意味を推測しません。NULL未明記とNULL許可は区別します。\n\n"
    out += "## 2. CRUD参照\n\nC=INSERT、R=FROM/JOIN参照、U=UPDATE、D=DELETE。文字列の存在は実行を保証せず、動的SQL・ORM経由の操作は完全には検出しません。\n\n"
    out += table(["表", "操作", "根拠位置"], [[r["table"], r["operation"], f"{r['path']}:L{r['line']}"] for r in refs]) + "\n"
    declared = {t["name"] for t in declarations}
    for name in sorted({r["table"] for r in refs} - declared):
        out += f"- `{esc(name)}`: 参照はありますが、このプロジェクトから一致する定義を抽出できていません。列・キー・制約は未確定です。\n"
    if not declarations:
        out += "\n## 3. 定義\n\n定義を抽出できていません。DBを使用していないという判定ではありません。DDL・マイグレーション・対応するORM定義の所在を確認してください。\n"
    for n, item in enumerate(declarations, 1):
        out += f"\n## 3.{n}. {esc(item['name'])}\n\n宣言種別: {esc(item['origin'])}\n\n根拠: " + evidence(root, dest, item["path"], item["line"], item["end_line"]) + "\n\n"
        out += table(["列名", "宣言型", "NULL指定", "PK明示", "既定値", "根拠行"],
                     [[c["name"], c["type"], c["nullable"], "あり" if c["primary_key"] else "未検出", c["default"], c["line"]] for c in item["columns"]])
        out += "\n### 列定義・制約\n\n" + table(["列", "元の定義（長い場合は省略）"], [[c["name"], c["definition"]] for c in item["columns"]])
        out += "\n" + table(["テーブル制約"], [[c] for c in item["constraints"]])
        out += "\n### インデックス\n\n" + table(["宣言"], [[c] for c in item["indexes"]])
        out += "\n論理名、コード値の意味、保持期間、件数、DB固有の実効制約は未確定です。\n"
    return out


def feature_docs(root: Path, directory: Path, feature: dict, declarations: list[dict]) -> dict[str, str]:
    files = feature["files"]
    symbols = [(f, s) for f in files for s in f["symbols"]]
    refs = [dict(c, path=f["path"]) for f in files for c in f["crud"]]
    names = {r["table"] for r in refs} | {t["name"] for f in files for t in f["tables"]}
    related = [t for t in declarations if t["name"] in names]
    basic_path, detail_path = directory / "基本設計書.md", directory / "詳細仕様書.md"
    basic = header(feature["name"] + " — 基本設計書")
    basic += "## 1. 機能の概要\n\n" + esc(feature.get("summary") or "業務目的は設定に未記載です。下記のコメント由来の説明・実装を確認してください。") + "\n\n"
    basic += f"機能ID: `{esc(feature['id'])}` / 分類: {esc(feature['origin'])}\n\n"
    basic += "## 2. 対象ソースと責務\n\n" + table(["ソース", "言語", "解析状態", "SHA-256"], [[f["path"], f["language"], f["status"], f["sha256"]] for f in files])
    basic += "\n" + table(["実装単位", "説明（コメント由来）"], [[s["name"], s["summary"] or "説明なし／未確定"] for _, s in symbols])
    basic += "\n## 3. 入口・インターフェース\n\n" + table(["実装単位", "入力宣言", "出力宣言"], [[s["name"], "; ".join(s["parameters"]) or "引数宣言なし", s["returns"]] for _, s in symbols])
    basic += "\n" + table(["実装単位", "HTTP method", "ルート宣言"], [[s["name"], r["method"], r["path"]] for _, s in symbols for r in s["routes"]])
    basic += "\n## 4. 処理・依存先\n\n呼出名はソース上の表記です。実際の呼出先の型・ファイルを確定したコールグラフではありません。\n\n"
    basic += table(["実装単位", "呼出名"], [[s["name"], ", ".join(dict.fromkeys(c["name"] for c in s["calls"])) or "未抽出"] for _, s in symbols])
    basic += "\n## 5. 使用データ\n\n" + table(["表", "操作", "根拠"], [[r["table"], r["operation"], f"{r['path']}:L{r['line']}"] for r in refs])
    basic += "\n詳細は [テーブル仕様書](テーブル仕様書.md) を参照してください。\n\n## 6. 例外・認可・トランザクション\n\n"
    basic += table(["実装単位", "注釈・decorator（意味の確定は要確認）"], [[s["name"], "; ".join(s["annotations"]) or "未抽出"] for _, s in symbols])
    basic += "\n権限、業務エラーの意味、トランザクション境界、排他制御、性能要件は断定しません。抽出できた条件・例外処理は [詳細仕様書](詳細仕様書.md) に記録します。\n\n## 7. 根拠\n\n"
    for f, s in symbols:
        basic += "- " + evidence(root, basic_path, f["path"], s["line"], s["end_line"]) + "\n"
    detailed = header(feature["name"] + " — 詳細仕様書")
    detailed += "## 読み方\n\n処理表は静的な出現順です。分岐した全行が順番に実行されるという意味ではありません。字下げ深さはPythonで抽出し、他言語の深さは未解析です。動的値・外部ライブラリ内部・未抽出の処理は未確定です。\n"
    for n, (f, s) in enumerate(symbols, 1):
        detailed += f"\n## {n}. {esc(s['name'])}\n\n" + evidence(root, detail_path, f["path"], s["line"], s["end_line"]) + "\n\n"
        detailed += table(["項目", "内容"], [["種別", s["kind"]], ["シグネチャ", s["signature"]], ["説明", s["summary"] or "未記載"], ["引数", "; ".join(s["parameters"]) or "宣言なし"], ["戻り値", s["returns"]]])
        detailed += "\n### 処理・条件・例外\n\n" + table(["順", "行", "深さ", "種別", "式・処理"], [[i, step["line"], step["depth"], step["kind"], step["text"]] for i, step in enumerate(s["steps"], 1)])
        detailed += "\n### 呼出箇所\n\n" + table(["呼出名", "行"], [[c["name"], c["line"]] for c in s["calls"]])
    if not symbols:
        detailed += "\n関数・メソッドを抽出できていません。SQL定義専用または未対応構文の可能性があります。解析報告を確認してください。\n"
    return {"基本設計書.md": basic, "詳細仕様書.md": detailed,
            "テーブル仕様書.md": render_tables(root, directory / "テーブル仕様書.md", related, refs)}


def qa_doc(feature: dict) -> str:
    out = f"# {esc(feature['name'])} — 確認事項\n\n未回答の項目を確定仕様として扱わないでください。\n\n"
    out += table(["ID", "質問", "選択肢", "回答"], [
        ["Q-01", "この機能のファイル境界は正しいですか", "A: このまま / B: 分割 / C: 統合（設定featuresを修正）", "未回答"],
        ["Q-02", "業務目的・正常系・例外系の説明を確定できますか", "A: コメントを正式採用 / B: 業務資料が必要 / C: 担当者確認", "未回答"],
        ["Q-03", "認可・排他・トランザクションの定義元はどこですか", "A: 対象ソース / B: 共通基盤・設定 / C: 運用 / D: 不明", "未回答"],
        ["Q-04", "物理テーブル定義の正本は何ですか", "A: スキーマDDL / B: 適用済みmigration / C: ORM / D: DB管理資料 / E: DB不使用", "未回答"],
        ["Q-05", "動的SQL・DI・生成コード・外部サービスに未解析部分はありますか", "A: あり（場所記載） / B: なしと確認済み / C: 未確認", "未回答"]])
    warnings = [[f["path"], w] for f in feature["files"] for w in f["warnings"]]
    return out + "\n## 検出された制限・警告\n\n" + table(["ソース", "内容"], warnings)
