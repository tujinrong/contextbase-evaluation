"""Serialize independent AI review of the explicitly authorized draft SHA."""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

from record_analysis_comparison_01 import EXPECTED_CHECKLIST, ROWS, FIELD_ROWS

ROOT = Path(__file__).resolve().parents[5]
HERE = Path(__file__).resolve().parent
DRAFT = "test-project1/spec-analysis/CSharp_ASPNET/20261013-rerun-12h/source-only/drafts/search-basic-02/round-01/基本設計書/01_学生検索画面.md"
EXPECTED_DRAFT = "0ab365e4e26027ed78823df0c5e1c9f6844d65619e4abcdfadf18fd39314fa53"

# Explicit line mappings are AI judgments after reading all 637 draft lines.
OBLIGATION_LINES = {
    "S-01": [(213,234),(620,622)], "S-02": [(21,29),(104,106)],
    "S-03": [(132,143),(551,569)], "S-04": [(145,146),(569,569)],
    "S-05": [(132,143),(245,246)], "S-06": [(535,547)],
    "S-07": [(107,107),(138,138),(323,325)], "S-08": [(296,327)],
    "S-09": [(184,207),(238,251),(288,290)], "S-10": [(104,126),(576,579)],
    "S-11": [(331,374)], "S-12": [(378,399)], "S-13": [(403,432)],
    "S-14": [(159,161),(620,629)], "S-15": [(148,158)],
    "S-16": [(209,209),(286,290),(372,372)],
    "R-01": [(437,450)], "R-02": [(437,468)], "R-03": [(23,23),(106,106)],
    "R-04": [(476,477),(623,623)], "R-05": [(614,616)], "R-06": [(151,151)],
    "R-07": [(589,608)], "R-08": [], "R-09": [(479,479)], "R-10": [(325,325)],
    "R-11": [(479,479)], "R-12": [(479,479)], "R-13": [(479,479),(545,545)],
    "R-14": [(132,132),(480,480),(601,601)], "R-15": [],
    "R-16": [(478,481),(520,527)], "R-17": [(480,480),(522,523)],
    "R-18": [(494,495)], "R-19": [], "R-20": [], "R-21": [(470,470)],
    "R-22": [(478,485),(525,525)], "R-23": [(525,525)],
    "R-24": [(482,483),(430,430),(529,529)], "R-25": [(516,529)],
    "R-26": [(511,529)], "R-27": [(470,470)], "R-28": [(457,470)],
    "R-29": [(477,477)], "R-30": [(481,483),(601,601)], "R-31": [(520,529)],
    "C-01": [(168,178),(635,635)], "C-02": [(180,182)], "C-03": [(162,162),(180,180),(209,209)],
    "C-04": [(209,209)], "C-05": [(589,608),(620,627)], "C-06": [(12,14),(35,37),(608,608)],
}
FIELD_LINES = {
    "search.condition.student-no": [(63,63),(132,132)],
    "search.condition.name": [(64,64),(133,133)],
    "search.condition.kana": [(65,65),(134,134)],
    "search.condition.year": [(66,66),(135,135)],
    "search.condition.grade": [(67,67),(136,136)],
    "search.condition.class": [(68,68),(137,137)],
    "search.condition.unassigned": [(69,69),(107,107),(138,138)],
    "search.condition.status": [(70,76),(139,139)],
    "search.condition.prefecture": [(77,77),(140,140)],
    "search.condition.phone": [(78,78),(141,141)],
    "search.condition.admission-from": [(79,79),(142,142)],
    "search.condition.admission-to": [(80,80),(143,143)],
    "search.grid": [(95,96),(148,158)],
    "search.paging": [(90,96),(144,147)],
    "search.internal-state": [(53,60),(159,162),(622,622)],
    "register.internal-state": [(476,477),(623,623)],
}
DIAGRAMS = [
    ("D-01", "Use排他/所有者/session/tab/TTL/revision", 186, 205, ["S-09","S-14"]),
    ("D-02", "初期表示", 221, 232, ["S-01"]),
    ("D-03", "検索/4結果/局所catchと外側catch", 253, 284, ["S-03","S-05","S-09","S-10","S-16"]),
    ("D-04", "候補更新/未所属/上位クラス保持解除", 305, 321, ["S-07","S-08"]),
    ("D-05", "Page/Applied/ソート/末尾補正/例外", 342, 370, ["S-11"]),
    ("D-06", "clear/状態消去と表示失敗", 386, 397, ["S-12"]),
    ("D-07", "Resume/Appliedなし/再検索/通知", 412, 428, ["S-13"]),
    ("D-08", "登録・参照/復帰版/snapshot/dirty戻り", 446, 466, ["R-02","R-04","R-28"]),
    ("D-09", "保存削除/DBcommit/非Saved/Unknown/303", 487, 514, ["R-16","R-17","R-22","R-24","R-25","R-26","R-30","R-31"]),
    ("D-10", "検索関連FK/任意class/複合categoryコード", 591, 597, ["C-05"]),
]


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def main() -> None:
    target = HERE / "document-comparison-01.json"
    if target.exists():
        raise SystemExit("Existing independent document comparison must not be overwritten")
    checklist_path = HERE / "checklist.v1.json"
    if sha(checklist_path.read_bytes()) != EXPECTED_CHECKLIST:
        raise ValueError("Locked source checklist changed")
    draft_path = ROOT / DRAFT
    if sha(draft_path.read_bytes()) != EXPECTED_DRAFT:
        raise ValueError("Authorized draft SHA changed")
    checklist = json.loads(checklist_path.read_text(encoding="utf-8"))
    lines = draft_path.read_text(encoding="utf-8-sig").splitlines()

    def quote(start: int, end: int) -> dict:
        if not 1 <= start <= end <= len(lines):
            raise ValueError("Invalid draft quote range")
        text = "\n".join(lines[start-1:end]) + "\n"
        return {"path": DRAFT, "sha256": EXPECTED_DRAFT, "startLine": start, "endLine": end, "quote": text, "lineRangeSha256": sha(text.encode("utf-8")), "rangeEncoding": "UTF-8 no BOM/LF join/final LF"}

    obligation_ids = {row["id"] for row in checklist["obligations"]}
    if set(OBLIGATION_LINES) != obligation_ids:
        raise ValueError("All 53 source obligations must be classified")
    row_by_id = {row[0]: row for row in ROWS}
    comparisons = []
    for original in checklist["obligations"]:
        audit_id = original["id"]
        old = row_by_id[audit_id]
        status = "対象外" if old[1] == "対象外" else "必須欠落" if audit_id == "C-03" else "含まれる"
        reason = old[3]
        if audit_id == "S-10":
            reason = "本文110行の上限超過差分と95-96行の静的HTMLは、空tbody/11列header/無効pagerを正確に保持。解析AC-01の一覧領域非表示という曖昧さは稿では解消。4結果/totalCount/時刻表示も119-126行で整合"
        if audit_id == "C-03":
            reason = "CSRF入口と外側errorは本文にある。cookie属性と30分slide、no-store/CSP/nosniff/no-referrer/HTTPS redirectの具体原設定は全637行で未記載。解析AC-02からの補足不足が継続"
        if audit_id == "C-06":
            reason = "文書属性はobserved-source/DDL宣言を区別、静的投影は実撮影ではないと明示。稼働DB適用やproductionAuth/性能/例外の実証にはならない。未実機はこの独立報告にも明示"
        comparisons.append({"auditId": audit_id, "status": status, "responsibilityAndJudgment": reason, "sourceRequirement": original["requirement"], "sourceEvidenceIds": original["evidenceRefs"], "draftCitations": [quote(s,e) for s,e in OBLIGATION_LINES[audit_id]]})
    fields = []
    for original in checklist["fieldCatalogue"]:
        audit_id = original["id"]
        included = audit_id in FIELD_LINES
        fields.append({"auditId": audit_id, "sourceDomId": original.get("sourceDomId"), "status": "含まれる" if included else "対象外", "responsibility": "検索DOM/DTO/DB/長さ/初期値、または検索復帰hidden境界" if included else "登録全項目・管理表示・削除理由は登録文書責務", "sourceEvidenceIds": original["evidenceRefs"], "draftCitations": [quote(s,e) for s,e in FIELD_LINES.get(audit_id,[])]})
    diagrams = [{"id": i, "subject": label, "auditIds": ids, "status": "含まれる", "judgment": "本文と接続された原ソースの条件/結果を保持。完成画像の視覚・読みやすさは未レビュー", "draftCitation": quote(s,e), "renderedImageReviewed": False} for i,label,s,e,ids in DIAGRAMS]
    issues = [
        {"id":"DC-01","severity":"low","kind":"必須欠落","auditId":"C-03","subject":"HTTP共通設定の補足不足","finding":"原WebHostSetup:14,22,25のcookie属性/期間、no-store/CSP/nosniff/no-referrer/HTTPS redirectが本文にない。CSRFと例外境界は存在する。主要検索処理の欠落ではない","sourceEvidenceIds":["web-host"],"draftCitations":[quote(180,182),quote(209,209)],"minimalSourceBackedRevision":"HTTP共通境界の具体設定をsource位置と共に補足。production認証やDB適用の成功保証を追加しない"},
        {"id":"DC-02","severity":"low","kind":"図の曖昧さ","auditId":"R-26","subject":"Unknown判定のAND/OR括弧","finding":"図511行は『書込開始済みかつcommit試行済みまたはrollback不成功』と括弧なし。本文522行のwriteStarted && (commitAttempted || !rolledBack)は正確で、図も同じ意味と定義している。図単独ではwrite=false/rollback失敗をUnknownと読めるので括弧で自己完結させる","sourceEvidenceIds":["service-save-write","service-delete"],"draftCitations":[quote(511,513),quote(522,522)],"minimalSourceBackedRevision":"図判定を『書込開始済み AND（commit試行済み OR rollback不成功）』へ明確化"},
        {"id":"DC-03","severity":"low","kind":"説明の限定不足","auditId":"C-05","subject":"任意所属と在籍区分CHECKの区別","finding":"589行『学生の所属は任意』とERのnullable関係はSQL列/FKのnullabilityとして正しいが、DDL ck_student_datesでは01/02はclass_id必須、03/04は任意。本文にこの限定がない。検索『未所属』を全区分で成立可能と拡張しないため、SQL宣言として補足が望ましい","sourceEvidenceIds":["ddl-constraints","normalizer-relations"],"draftCitations":[quote(589,597),quote(608,608)],"minimalSourceBackedRevision":"class_id列はNULL可、在学/休学はCHECKと保存検証で必須、卒業/退学は任意という条件をER説明に追加"}
    ]
    counts = {s: sum(row["status"]==s for row in comparisons) for s in ("矛盾","必須欠落","含まれる","対象外")}
    report = {
        "schema":"reverse-source-document-comparison/1", "projectId":"test-project1", "technology":"CSharp_ASPNET", "documentId":"CSHARP_ASPNET-BAS-STU-01", "recordedAtUtc":datetime.now(timezone.utc).isoformat(),
        "checklist":{"path":checklist_path.relative_to(ROOT).as_posix(),"sha256":EXPECTED_CHECKLIST}, "draft":{"path":DRAFT,"sha256":EXPECTED_DRAFT,"lineCount":len(lines)},
        "method":"AI read all 637 authorized draft lines including static HTML, tables, 9 flowcharts and 1 ER diagram, and manually compared the locked 53 obligations/40 field groups/visual materials. Quote script only checked pinned SHAs/ID completeness/ranges and copied exact document quotations. No code, prompt, original facts, checklist or draft edited.",
        "boundaries":{"originalSpecRead":False,"specEvalRead":False,"scoresReadOrProduced":False,"oldDraftRead":False,"renderedImagesReviewed":False,"applicationOrDbExecuted":False,"analysisQuotesReadBeforeDocument":True,"knownStructuralFailureAcceptance":"採用不可。親Agent既知のspec-meta書式/イベント下位見出し/矩形表不備を意味照合の合格へ置換しない"},
        "summary":{"importantSemanticDefects":[],"majorSearchFieldsEventsBranchesUnitsMemoryDbBoundaryPreserved":True,"obligationCounts":counts,"fieldGroupsClassified":len(fields),"flowchartsMeaningCompared":9,"erDiagramsMeaningCompared":1,"minorIssues":3,"analysisAC01ResolvedInDraft":True,"analysisAC02Persists":True,"adoptionApproved":False},
        "issues":issues,"obligationComparisons":comparisons,"fieldComparisons":fields,"diagramComparisons":diagrams,
        "visualMaterialReview":[
            {"auditId":"V-01","status":"含まれる","finding":"初期非Viewer静的HTML、source12条件/11列/20件asc/未検索/無効pager。実データでない差込placeholderと非実行routeを明示","draftCitations":[quote(35,37),quote(50,100)],"renderedImageReviewed":False},
            {"auditId":"V-02","status":"含まれる","finding":"正常一覧は取得行/件数/時刻/操作活性の状態差分表と一覧11行定義。描画用live行データは創作していない","draftCitations":[quote(108,108),quote(123,123),quote(148,158)],"renderedImageReviewed":False},
            {"auditId":"V-03","status":"含まれる","finding":"0件/超過/検証エラー/未検索の表示差分、通知/error aria-live、pager無効、source外側HTML拒否を区別","draftCitations":[quote(109,112),quote(119,126),quote(209,209),quote(286,290)],"renderedImageReviewed":False},
            {"auditId":"V-04","status":"対象外","finding":"登録全画像は登録責務。検索Viewer差分/新規非表示/参照labelは106行にあり、遷移と戻りは3.8へ保持","draftCitations":[quote(106,106),quote(435,470)],"renderedImageReviewed":False},
            {"auditId":"V-05","status":"対象外","finding":"登録重複dialog等全画像は登録責務。検索への影響は非Saved303なし/Unknown検索確認/Conflict後再読込境界を3.9へ保持","draftCitations":[quote(495,513),quote(527,529)],"renderedImageReviewed":False},
            {"auditId":"V-06","status":"含まれる","finding":"検索6イベントと共有Use、遷移dirty、保存削除確定とERの意味材料を確認。画像の切れ/重なり/可読性は親の稿SHA固定renderとnative確認待ち","draftCitations":[quote(186,205),quote(591,597)],"renderedImageReviewed":False}
        ],
        "sourceEvidenceCatalogue":checklist["evidenceCatalogue"],
        "nextBoundary":"現稿は構造不備で採用不可。新稿は別SHAで本文/図を再照合し、rootが固定render/native画像確認を行う。現稿画像合格や既存レポート合格を新稿へ流用しない。"
    }
    target.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8",newline="\n")
    print(json.dumps({"path":str(target),"sha256":sha(target.read_bytes()),"counts":counts,"importantSemanticDefects":0,"minorIssues":3,"renderedImagesReviewed":False},ensure_ascii=False))


if __name__ == "__main__":
    main()
