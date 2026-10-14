"""Serialize AI-authored responsibility mappings and quote verified input facts."""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]
HERE = Path(__file__).resolve().parent
CHECKLIST = HERE / "checklist.v1.json"
EXPECTED_CHECKLIST = "40e184c35018ec8efe31915a91c48ab35a4ebb70670e61bc8d35c7d0a4aa4242"
INPUTS = {
    "basic": ("agents/reverse-agent/.tmp/20261013-rerun-12h/source-only/jobs/search-basic-02/round-01/analysis-verified.json", "3e195b02da6d98db65fbb3ce3da2befcd8beb6a362846e6030baf3292a1d129c"),
    "detail": ("agents/reverse-agent/.tmp/20261013-rerun-12h/source-only/jobs/search-detail-02/round-01/analysis-verified.json", "9124c903b6cd0828d972a7f2582ab7f8b3a3b31c1556658bc474771b7409453d"),
}

# Status/scope/interpretation below are independent AI judgments, not computed scores.
# Each included row uses source-audit obligation ID, explicit source responsibility,
# and manually selected fact IDs. Quotes are copied from those pinned facts.
ROWS = [
    ("S-01", "含まれる", "含まれる", "検索初期状態と候補取得。条件なしGETはDB学生検索をせず、検索状態を作る", "F022 F026", "F007 F020 F035"),
    ("S-02", "含まれる", "含まれる", "検索/参照権限と新規・編集リンク。Viewer編集不可を遷移境界として確認", "F001 F003", "F001 F006 F041"),
    ("S-03", "含まれる", "含まれる", "検索条件の正規化とAND/区分IN/電話OR/削除除外。全12条件を保持", "F005 F006 F007 F012 F013 F035", "F011 F012 F013 F018 F019 F024"),
    ("S-04", "含まれる", "含まれる", "型付きparameter・LIKE escape・許可ソート・同値student_id順", "F017 F035", "F024 F025"),
    ("S-05", "含まれる", "含まれる", "年度/クラス/コード/日付/区分/長さの検索検査と段階を保持", "F008 F010 F013 F033", "F014 F016 F019 F023"),
    ("S-06", "含まれる", "含まれる", "検索候補は停止/期間外を除外しない。登録候補規則を転用していない", "F019 F020", "F021 F022 F023"),
    ("S-07", "含まれる", "含まれる", "未所属はUI値clearとサーバー同時指定拒否を区別。dynamic disabledなしも保持", "F009 F029 F030", "F015 F037"),
    ("S-08", "含まれる", "含まれる", "optionsは下書き候補の変更でApplied/LastResult保持、版比較/増分/検索なし", "F029", "F022 F037"),
    ("S-09", "含まれる", "含まれる", "Useの排他/版・Snapshot検索・成功時state更新、失敗と表示失敗の差", "F024 F027 F028 F034 F038", "F008 F009 F025 F036"),
    ("S-10", "矛盾", "含まれる", "4結果、TOP10001、超過は件数非公開/空items。基本F018の『一覧を表示しない』はtable領域非表示とも読めるが、Razorは空tbodyでもtableと11列headerを常時描画する。行がないと書けば整合", "F018 F036 F038", "F025 F027"),
    ("S-11", "含まれる", "含まれる", "PageはApplied再利用、未検索409、サイズ/ソート変更Page1、末尾外補正再検索", "F017 F031 F036", "F020 F025 F038"),
    ("S-12", "含まれる", "含まれる", "clearは既存context保持/条件結果消去/版+1/初期条件/学生検索なし", "F032", "F039"),
    ("S-13", "含まれる", "含まれる", "復帰GETは適用条件を再検索、state/版拒否、Appliedなしは未検索。Resume補正差も保持", "F043 F044", "F040 F045"),
    ("S-14", "含まれる", "含まれる", "乱数token/owner/session/任意tab/TTL/gate/revision、入力値非URL化、server memory", "F022 F023 F024 F040 F055", "F007 F008 F033 F041"),
    ("S-15", "含まれる", "含まれる", "11表示列、和暦/時刻、電話null、LEFT JOIN、住所2非表示、role操作を保持", "F015 F016", "F028 F030"),
    ("S-16", "含まれる", "含まれる", "局所WebFaultはstatus+ModelStateでunsearched、stateは保持。catch外はhost error", "F027 F028 F037 F039 F057", "F026 F027 F034 F036 F038"),
    ("R-01", "対象外", "対象外", "検索文書は新規遷移と登録権限が責務。新規登録全フィールド初期値は登録文書責務", "F003 F040", "F001 F041"),
    ("R-02", "含まれる", "含まれる", "遷移境界の非削除学生読込、404、復帰版、snapshot作成は責務。登録全フィールド逆変換は範囲外", "F040 F041", "F041 F042"),
    ("R-03", "含まれる", "含まれる", "検索からViewer参照への権限・fieldset無効を保持。登録title全表示は範囲外", "F001 F003", "F001 F041"),
    ("R-04", "含まれる", "含まれる", "検索復帰先の保護、snapshot所有者/session/対象/期限、版比較境界は責務。新規版なし全入力契約は範囲外", "F041 F045 F046", "F042 F043 F045"),
    ("R-05", "対象外", "対象外", "登録全業務項目正規化は登録責務。検索共有項目の正規化はS-03/S-05とfieldCatalogueで別に照合済", "F014", "F011 F012 F013 F018"),
    ("R-06", "対象外", "対象外", "元号入力検証は登録責務。検索の和暦出力はS-15、期間西暦検証はS-05として照合", "F016", "F028"),
    ("R-07", "対象外", "対象外", "登録cross-field検証イベントは登録責務。検索ERのnullable classを無条件未所属可能と拡張しないDDL補足は詳細F032にある", "F051", "F032"),
    ("R-08", "対象外", "対象外", "登録連絡先3項目/最低1検証は検索イベント外。電話OR検索はS-03に含まれる", "F012", "F018 F032"),
    ("R-09", "対象外", "対象外", "登録マスター選択可否の全規則は範囲外。保存再検証境界は付随記載され、検索の停止候補とは区別される", "F020 F047", "F022 F043"),
    ("R-10", "対象外", "対象外", "REG上位変更JSは登録イベント。検索に同挙動がないことは基本F030/詳細F022に明示", "F030", "F022"),
    ("R-11", "対象外", "対象外", "登録class選択と既存座席維持の全条件は登録責務。検索候補と保存確定の違いは素材にある", "F047", "F043"),
    ("R-12", "対象外", "対象外", "03/04保存時class期間重複は登録責務。検索文書に独立イベントとして要求しない", "F047", "F043"),
    ("R-13", "対象外", "対象外", "保存の定員取得は登録責務。検索Lookup(false)の0は未集計で人数表示なしと明示済", "F019 F047", "F021 F031"),
    ("R-14", "対象外", "対象外", "保存学籍番号不変と一意性検査イベントは登録責務。検索表示元属性として素材に残る", "F005 F046 F052", "F011 F032"),
    ("R-15", "対象外", "対象外", "旧終了区分の管理者訂正/理由は登録責務、検索からの復帰確定条件に不可欠な独立分岐ではない", "", ""),
    ("R-16", "含まれる", "含まれる", "検索復帰はSaved時だけなので保存version競合/notfound/where再照合/commit境界を保持。登録全エラーUIは範囲外", "F046 F048", "F043"),
    ("R-17", "含まれる", "含まれる", "検索復帰境界ではNoChangeがSavedではなく303/保存通知に進まないことが責務。全column比較の詳細は登録責務", "F045 F046", "F043 F045"),
    ("R-18", "対象外", "対象外", "同一人物候補のmatch SQLは登録責務。ConfirmationRequiredが303へ進まない点のみR-25で確認", "F045 F046", "F043"),
    ("R-19", "対象外", "対象外", "候補20件/再token/登録dialogの全状態は登録責務。検索本文の候補更新とは別である", "", ""),
    ("R-20", "対象外", "対象外", "登録token10分/hash/busy/消費は登録責務。memory vs DB境界のみDB一般観点で照合", "F002", "F002"),
    ("R-21", "対象外", "対象外", "登録重複確認取消は登録イベント。検索へ戻るdirty確認と混同しない", "F042", "F041"),
    ("R-22", "含まれる", "含まれる", "検索復帰がDB commit後Savedに依存するため、ReadCommitted/Gate/学生write+audit/commitを保持。Gate5秒等全保存運用は登録責務", "F034 F046 F048", "F025 F043"),
    ("R-23", "対象外", "対象外", "audit全列/全値は登録データ操作責務。学生とaudit同tx/commit済だけSavedという確定境界はR-22に含まれる", "F046 F049", "F043 F044"),
    ("R-24", "含まれる", "含まれる", "Savedだけ303、context/読込版、新context、flash10分/一回Take、復帰再検索", "F045 F050", "F040 F045"),
    ("R-25", "含まれる", "含まれる", "非Savedの303なし、編集へ残る/再読込/外側経路は責務。全登録field errorの再表示は登録文書責務", "F045 F048 F049", "F043 F044 F045"),
    ("R-26", "含まれる", "含まれる", "結果不明を成功扱いせず、再送せず検索確認、try外DB openの外側503を保持", "F048 F039", "F043 F034"),
    ("R-27", "対象外", "対象外", "入力clear/edit取消と最新再読込は登録イベント。検索clearと別でsnapshot Originalへ戻ることを基本F042が補足", "F042", "F041"),
    ("R-28", "含まれる", "含まれる", "検索復帰linkはdirty破棄確認で中止/継続、保存はしない。beforeunload等全編集挙動は登録責務", "F042 F030", "F041 F010"),
    ("R-29", "含まれる", "含まれる", "削除からの検索復帰確定条件として管理者/Confirmed/Reason/版/snapshot/復帰先を保持", "F049 F041", "F042 F044"),
    ("R-30", "含まれる", "含まれる", "論理削除commit/audit/Saved303、次検索除外、番号unique存続。物理削除と混同なし", "F049 F045 F052", "F044 F045 F032 F033"),
    ("R-31", "含まれる", "含まれる", "削除notfound/conflict/版上限/Unknown/SystemError、非Saved再Loadの追加404境界を保持", "F049", "F044"),
    ("C-01", "含まれる", "含まれる", "MVC実入口と未接続JSON/API helperを区別。宣言だけから公開APIを作らない", "F002 F056", "F002 F003"),
    ("C-02", "含まれる", "含まれる", "FormGuard許可property/prefix/extras/unknown/重複/checkbox例外、__Invariantを保持", "F025", "F004 F005"),
    ("C-03", "必須欠落", "必須欠落", "検索個人情報のHTTP共通境界に該当。CSRF/body制限は含まれるがcookie30分slide/Secure/HttpOnly/SameSiteStrict、CSP/nosniff/no-referrer/HTTPS redirectの具体設定は未収録。詳細はno-store等とだけ言及。補足素材の軽微な不足", "F025 F039", "F004 F034"),
    ("C-04", "含まれる", "含まれる", "応答未開始/WebFault status/他503/escapedHTML/検索復帰、API限定JSONを区別", "F039", "F026 F034"),
    ("C-05", "含まれる", "含まれる", "検索ERの学生/クラス/コード/分類FKとJOIN、nullableclass、状態はmemory/DB状態table未接続。audit全詳細は登録範囲外", "F051 F052 F053 F054 F055 F056", "F024 F030 F031 F032 F033"),
    ("C-06", "含まれる", "含まれる", "実接続/DB適用/認証運用/表示/例外/取消実行は未確認、static事実を合格へ拡張しない。評価loginの具体設定は検索機能の責務外", "F034 F039", "F004 F006 F025 F034"),
]

FIELD_ROWS = [
    ("search.condition.student-no", "F005", "F011"),
    ("search.condition.name", "F006", "F012"),
    ("search.condition.kana", "F007", "F013"),
    ("search.condition.year", "F008 F033", "F014 F022 F023"),
    ("search.condition.grade", "F008 F033", "F014 F022 F023"),
    ("search.condition.class", "F008 F033", "F014 F022 F023"),
    ("search.condition.unassigned", "F009 F030", "F015"),
    ("search.condition.status", "F010", "F016"),
    ("search.condition.prefecture", "F011", "F017"),
    ("search.condition.phone", "F012", "F018"),
    ("search.condition.admission-from", "F013", "F019"),
    ("search.condition.admission-to", "F013", "F019"),
    ("search.grid", "F015 F016", "F028"),
    ("search.paging", "F017 F031 F036", "F020 F025 F038"),
    ("search.internal-state", "F022 F023 F024", "F007 F008"),
    ("register.internal-state", "F041 F045 F046", "F042 F043 F045"),
]

VISUAL_ROWS = [
    ("V-01", "含まれる", "初期画面の状態・順序・12条件・11列・活性。画像自体は生成前で未レビュー", "F004 F018 F026", "F010 F020 F027 F035"),
    ("V-02", "含まれる", "正常一覧/formatter/role/paging材料あり。図や画像の実出力は未レビュー", "F015 F016 F017 F018", "F020 F027 F028"),
    ("V-03", "含まれる", "異常・0件・超過・未検索を区別する材料あり。基本一覧非表示表現だけS-10で軽微指摘", "F018 F027 F028 F039", "F027 F034 F036"),
    ("V-04", "対象外", "登録全画面は検索文書責務外。Viewer遷移とsnapshot/戻り境界のみ対象", "F003 F040 F041", "F041 F042"),
    ("V-05", "対象外", "登録dialog/validation/conflict/unknown全画像は登録文書責務。非Saved復帰拒否と検索確認だけ対象", "F045 F048 F049", "F043 F044 F045"),
    ("V-06", "含まれる", "検索6イベント+共通入口+復帰確定境界+DB関係のdiagram材料あり。基本は節点文章、詳細はMermaidを含む。図本文意味の完成検査はwriter後", "F027 F029 F031 F032 F043 F051 F057", "F032 F034 F035 F036 F037 F038 F039 F040 F045"),
]


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    target = HERE / "analysis-comparison-01.json"
    if target.exists():
        raise SystemExit("Existing independent comparison must not be overwritten")
    if sha(CHECKLIST) != EXPECTED_CHECKLIST:
        raise ValueError("Checklist changed after independent lock")
    checklist = json.loads(CHECKLIST.read_text(encoding="utf-8"))
    analyses = {}
    for key, (path, expected) in INPUTS.items():
        if sha(ROOT / path) != expected:
            raise ValueError(f"Input fact SHA changed: {key}")
        analyses[key] = json.loads((ROOT / path).read_text(encoding="utf-8"))
    catalogs = {section: {row["id"]: row for row in checklist[section]} for section in ("obligations", "fieldCatalogue", "visualChecks")}

    def cite(key: str, fact_ids: str) -> list[dict]:
        facts = analyses[key]["facts"]
        indexed = {f["id"]: (i, f) for i, f in enumerate(facts)}
        result = []
        for fact_id in fact_ids.split():
            i, fact = indexed[fact_id]
            statement = fact["statement"]
            # Exact first prose paragraph, no rephrasing. Flowchart full text remains in pinned input.
            quote = statement.split("\n")[0]
            result.append({"factId": fact_id, "jsonPointer": f"/facts/{i}/statement", "quote": quote, "referencesFromFact": fact["references"]})
        return result

    def evidence(record: dict) -> list[dict]:
        return [{"evidenceId": ref, **checklist["evidenceCatalogue"][ref]} for ref in record["evidenceRefs"]]

    judgments = []
    for audit_id, basic_status, detail_status, reason, basic_ids, detail_ids in ROWS:
        original = catalogs["obligations"][audit_id]
        judgments.append({"auditId": audit_id, "sourceRequirement": original["requirement"], "responsibilityAndJudgment": reason, "basic": {"status": basic_status, "factCitations": cite("basic", basic_ids)}, "detail": {"status": detail_status, "factCitations": cite("detail", detail_ids)}, "sourceEvidence": evidence(original)})
    if {row[0] for row in ROWS} != set(catalogs["obligations"]):
        raise ValueError("Not all 53 source obligations classified")

    field_map = {row[0]: row for row in FIELD_ROWS}
    fields = []
    for original in checklist["fieldCatalogue"]:
        audit_id = original["id"]
        if audit_id in field_map:
            _, basic_ids, detail_ids = field_map[audit_id]
            status = "含まれる"
            scope = "検索項目のDOM/DTO/DB/初期値/長さ単位/意味を照合" if audit_id.startswith("search.") else "検索遷移のsnapshot/復帰先/版境界だけ対象。全登録hidden契約は登録文書責務"
        else:
            basic_ids = detail_ids = ""
            status = "対象外"
            scope = "登録画面全項目・管理表示・削除理由は登録文書責務。共有検索項目の保存属性は対応するsearch項目で確認"
        fields.append({"auditId": audit_id, "sourceDomId": original.get("sourceDomId"), "responsibility": scope, "basic": {"status": status, "factCitations": cite("basic", basic_ids)}, "detail": {"status": status, "factCitations": cite("detail", detail_ids)}, "sourceEvidence": evidence(original)})

    visual = []
    for audit_id, status, note, basic_ids, detail_ids in VISUAL_ROWS:
        visual.append({"auditId": audit_id, "status": status, "materialJudgment": note, "basicFactCitations": cite("basic", basic_ids), "detailFactCitations": cite("detail", detail_ids), "sourceEvidence": evidence(catalogs["visualChecks"][audit_id]), "renderedImageReviewed": False})

    counts = {key: {status: sum(row[key]["status"] == status for row in judgments) for status in ("矛盾", "必須欠落", "含まれる", "対象外")} for key in ("basic", "detail")}
    report = {
        "schema": "reverse-source-analysis-comparison/1", "projectId": "test-project1", "technology": "CSharp_ASPNET", "features": ["student-search"], "recordedAtUtc": datetime.now(timezone.utc).isoformat(),
        "stage": "analysis-material-only-before-writing", "originalSpecificationsRead": False, "evaluationExpectationsRead": False, "previousOrCurrentDocumentDraftRead": False, "sourceOrPromptOrFactsEdited": False, "specificationScoreProduced": False,
        "checklist": {"path": CHECKLIST.relative_to(ROOT).as_posix(), "sha256": EXPECTED_CHECKLIST},
        "inputs": {key: {"path": path, "sha256": expected, "documentId": analyses[key]["documentId"], "factCount": len(analyses[key]["facts"])} for key, (path, expected) in INPUTS.items()},
        "method": "AI read all 57 basic and 45 detailed statements plus unresolved/coverage notes. AI manually classified each locked obligation against search-document responsibility, including only registration details necessary for navigation/return/commit boundaries. Script copied exact fact prose and locked evidence metadata and validated SHAs/complete ID mapping; it did not judge business coverage or calculate specification scores.",
        "summary": {"importantDefects": [], "majorSearchFieldsEventsBranchesUnitsAndMemoryDbBoundaryPreserved": True, "obligationCounts": counts, "reviewedFieldGroups": len(fields), "diagramMaterialChecks": len(visual), "runtimeAndRenderingNotVerified": True},
        "issues": [
            {"id": "AC-01", "severity": "low", "kind": "矛盾", "document": "basic", "auditId": "S-10", "factId": "F018", "actualFactQuote": "tooManyでは条件追加の警告を出し、件数と一覧を表示しない。", "sourceFinding": "Search.cshtml:7はtooManyメッセージだけを条件分岐、:8のtable/thead/pagerフォームは結果状態に関わらず描画する。items[]なので結果行はない。基本F036/F038と詳細F027は空Itemsを保持しており、table領域非表示という解釈を避ければ整合する", "minimalSourceBackedClarification": "上限超過は空の結果行、件数と検索日時を表示せず、11列headerを持つ一覧領域と無効pagerは残る", "sourceEvidence": [checklist["evidenceCatalogue"]["search-grid"], checklist["evidenceCatalogue"]["search-dom"]]},
            {"id": "AC-02", "severity": "low", "kind": "必須欠落", "documents": ["basic", "detail"], "auditId": "C-03", "sourceFinding": "CSRF/本文制限は両素材にあるが、WebHostSetup:14のcookie30分slide/Secure/HttpOnly/SameSiteStrict、:22のCSP/nosniff/no-referrer、:25のHTTPS redirect具体設定が未収録。詳細F034はno-store等という一般記述。主要検索動作・独立分岐は欠落していない", "minimalSourceBackedClarification": "補足のHTTP共通境界で原設定値をsource-attributedに記述。認証運用/DB適用を稼働保証として追加しない", "sourceEvidence": [checklist["evidenceCatalogue"]["web-host"]]}
        ],
        "obligationComparisons": judgments, "fieldComparisons": fields, "visualAndDiagramMaterialComparisons": visual,
        "unknownsReview": {"status": "未確認を未確認として保持", "observations": ["未実機/未DB適用、認証運用、dynamicdisabled不足、options版省略、GET tab任意、Resume補正差、memory多node/restart、try外DB失敗、未接続JSONhelperは両素材に保持", "登録dialog外観やtoken一回性の詳細は検索責務外で対象外。登録稿照合へ持ち越す"], "basicUnresolvedQuotes": analyses["basic"]["unresolved"], "detailUnresolvedQuotes": analyses["detail"]["unresolved"]},
        "nextBoundary": "この記録は解析素材の網羅性である。本文LIST、イベント6見出し、Mermaidの完成意味、初期/正常/異常/Viewer材料の本文残存と画像はwriter後に別稿SHAで独立レビューする。"
    }
    target.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps({"output": str(target), "sha256": sha(target), "obligationCounts": counts, "fieldGroups": len(fields), "importantDefects": 0, "minorIssues": 2}, ensure_ascii=False))


if __name__ == "__main__":
    main()
