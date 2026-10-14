"""Serialize the AI-authored source-only semantic review of detailed R1.

The maps and judgments are manual review results. This script only pins inputs,
validates complete stable-ID accounting, and copies exact evidence quotations.
"""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

from record_analysis_comparison_01 import EXPECTED_CHECKLIST, ROWS

ROOT = Path(__file__).resolve().parents[5]
HERE = Path(__file__).resolve().parent
SNAPSHOT = ROOT / "agents/reverse-agent/.tmp/20261013-rerun-12h/source-only/snapshot"
DRAFT = "test-project1/spec-analysis/CSharp_ASPNET/20261013-rerun-12h/source-only/drafts/search-detail-02/round-01/詳細仕様書/CSharp_ASPNET/01_学生検索画面.md"
EXPECTED_DRAFT = "23cdaa90a44f3e55b1bd174d6e9e8762ad083526418d3f08b2932958ba8f6875"

# Manually selected passages after AI read all 954 lines, including all diagrams.
OBLIGATION_LINES = {
    "S-01": [(444,488)], "S-02": [(37,39),(135,139),(768,768)],
    "S-03": [(157,168),(330,347)], "S-04": [(330,353),(369,390)],
    "S-05": [(157,168),(314,324)], "S-06": [(285,308)],
    "S-07": [(139,139),(149,151),(163,163),(559,564)],
    "S-08": [(551,597)], "S-09": [(250,279),(498,506),(543,549)],
    "S-10": [(140,145),(398,398),(852,861)], "S-11": [(599,660)],
    "S-12": [(664,704)], "S-13": [(708,758)],
    "S-14": [(169,171),(227,281),(948,950)], "S-15": [(176,187),(842,850)],
    "S-16": [(221,225),(543,549),(658,660)],
    "R-01": [(58,59),(766,768)], "R-02": [(764,772)],
    "R-03": [(37,37),(768,768)], "R-04": [(776,782),(807,834)],
    "R-05": [(865,875)], "R-06": [(167,168),(846,846)],
    "R-07": [(897,897),(938,942)], "R-08": [(166,166),(894,894)],
    "R-09": [(786,786)], "R-10": [(149,151)],
    "R-11": [(786,786)], "R-12": [(905,905)],
    "R-13": [(304,304),(906,906)], "R-14": [(788,788),(888,888)],
    "R-15": [(786,786)], "R-16": [(786,788),(796,801)],
    "R-17": [(801,801),(813,815)], "R-18": [(786,786)],
    "R-19": [], "R-20": [], "R-21": [],
    "R-22": [(786,792)], "R-23": [(788,790)],
    "R-24": [(805,834)], "R-25": [(794,803),(813,815)],
    "R-26": [(794,803),(811,832)], "R-27": [],
    "R-28": [(770,772),(834,834)], "R-29": [(774,782),(790,790)],
    "R-30": [(790,790),(805,809),(898,898)], "R-31": [(790,801)],
    "C-01": [(41,65)], "C-02": [(191,203)], "C-03": [(193,197),(221,225)],
    "C-04": [(205,225)], "C-05": [(881,954)],
    "C-06": [(24,27),(67,73),(877,879),(944,954)],
}
FIELD_LINES = {
    "search.condition.student-no": [(99,99),(157,157)],
    "search.condition.name": [(100,100),(158,158)],
    "search.condition.kana": [(101,101),(159,159)],
    "search.condition.year": [(102,102),(160,160)],
    "search.condition.grade": [(103,103),(161,161)],
    "search.condition.class": [(104,104),(162,162)],
    "search.condition.unassigned": [(105,105),(139,139),(163,163)],
    "search.condition.status": [(106,112),(164,164)],
    "search.condition.prefecture": [(113,113),(165,165)],
    "search.condition.phone": [(114,114),(166,166)],
    "search.condition.admission-from": [(115,115),(167,167),(322,322),(345,345)],
    "search.condition.admission-to": [(116,116),(168,168),(322,322),(346,346)],
    "search.grid": [(126,127),(176,187),(844,848)],
    "search.paging": [(124,127),(172,175)],
    "search.internal-state": [(90,96),(169,171),(235,279)],
    "register.internal-state": [(768,782),(807,834)],
}
DIAGRAMS = [
    ("D-01", "MVC共通入口/認証/CSRF/局所catchと外側catch", 205,219,["C-01","C-02","C-04"]),
    ("D-02", "Useの排他/所有者/session/tab/TTL/版", 261,279,["S-09","S-14"]),
    ("D-03", "サービス検索/入力検証/コード実在/SQL/上限/例外", 410,440,["S-03","S-04","S-05","S-10","S-16"]),
    ("D-04", "初期表示/初期条件/候補/未検索/外側例外", 461,478,["S-01"]),
    ("D-05", "検索POST/ModelState/Use/状態更新/表示失敗", 510,537,["S-09","S-10","S-16"]),
    ("D-06", "候補更新/未所属/上位クラス保持解除/未適用", 568,585,["S-07","S-08"]),
    ("D-07", "Page/適用条件/ソート変更/末尾補正/例外", 619,650,["S-11"]),
    ("D-08", "Clear/既存context/条件結果消去/期限延長", 681,696,["S-12"]),
    ("D-09", "Resume/適用なし/再検索/読込版/通知消費順", 726,746,["S-13"]),
    ("D-10", "保存削除/Savedと非Saved/303/読込版/通知", 811,832,["R-16","R-17","R-24","R-25","R-26","R-30","R-31"]),
    ("D-11", "DDLのFKと検索・候補SQLのJOINを別表示", 925,936,["C-05"]),
]


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def main() -> None:
    target = HERE / "document-comparison-02.json"
    if target.exists():
        raise SystemExit("Existing independent document comparison must not be overwritten")
    checklist_path = HERE / "checklist.v1.json"
    if sha(checklist_path.read_bytes()) != EXPECTED_CHECKLIST:
        raise ValueError("Locked source checklist changed")
    draft_path = ROOT / DRAFT
    if sha(draft_path.read_bytes()) != EXPECTED_DRAFT:
        raise ValueError("Authorized detailed R1 SHA changed")
    checklist = json.loads(checklist_path.read_text(encoding="utf-8"))
    lines = draft_path.read_text(encoding="utf-8-sig").splitlines()
    source_integrity = []
    for path in sorted({row["path"] for row in checklist["evidenceCatalogue"].values()}):
        ref = next(row for row in checklist["evidenceCatalogue"].values() if row["path"] == path)
        raw = SNAPSHOT / "sources" / path
        indexed = SNAPSHOT / "indexed" / (path + ".txt")
        if sha(raw.read_bytes()) != ref["sourceSha256"] or sha(indexed.read_bytes()) != ref["indexedSha256"]:
            raise ValueError("Locked source/indexed bytes changed: " + path)
        source_integrity.append({"path":path,"sourceSha256":ref["sourceSha256"],"indexedSha256":ref["indexedSha256"],"matchesLockedChecklist":True})

    def quote(start: int, end: int) -> dict:
        if not 1 <= start <= end <= len(lines):
            raise ValueError("Invalid draft quote range")
        text = "\n".join(lines[start-1:end]) + "\n"
        return {"path":DRAFT,"sha256":EXPECTED_DRAFT,"startLine":start,"endLine":end,"quote":text,"lineRangeSha256":sha(text.encode("utf-8")),"rangeEncoding":"UTF-8 no BOM/LF join/final LF"}

    def source_quote(evidence_id: str, start: int, end: int) -> dict:
        ref = checklist["evidenceCatalogue"][evidence_id]
        path = SNAPSHOT / "sources" / ref["path"]
        source_lines = path.read_text(encoding="utf-8-sig").splitlines()
        if not ref["start"] <= start <= end <= ref["end"]:
            raise ValueError("Source quote must stay inside locked evidence range")
        text = "\n".join(source_lines[start-1:end]) + "\n"
        return {"evidenceId":evidence_id,"path":path.relative_to(ROOT).as_posix(),"sha256":ref["sourceSha256"],"startLine":start,"endLine":end,"quote":text,"lineRangeSha256":sha(text.encode("utf-8")),"rangeEncoding":"UTF-8 no BOM/LF join/final LF"}

    obligation_ids = {row["id"] for row in checklist["obligations"]}
    if set(OBLIGATION_LINES) != obligation_ids:
        raise ValueError("All 53 source obligations must be classified")
    responsibility = {row[0]:row[3] for row in ROWS}
    outside = {row[0] for row in ROWS if row[1] == "対象外"}
    comparisons = []
    for original in checklist["obligations"]:
        audit_id = original["id"]
        status = "対象外" if audit_id in outside else "含まれる"
        reason = responsibility[audit_id]
        if audit_id == "S-05":
            status = "矛盾"
            reason = "大部分の検証段階/単位/実在検査は整合するが、168行の終了日『開始以下にならない』はto>fromを要求し、source122行のfrom>to拒否（等日許容）に矛盾。167/322行と345/346行は原ソース通りで、同じ稿の項目表と処理説明も不一致。DC-04を重要欠陥として記録"
        if audit_id == "R-26":
            status = "必須欠落"
            reason = "796-803行はUnknownのAND/OR条件、catch順、try外接続、非Saved303なしを正確に保持。しかし全954行に結果不明後の再送/再保存を避けて検索確認する案内がない。検索へ戻る確定境界の利用者行動としてDC-05を重要欠落に記録。登録token全詳細を検索文書へ拡大要求しない"
        if audit_id == "C-03":
            status = "必須欠落"
            reason = "CSRF/body/値数とno-store/nosniff/no-referrer/CSP名は193-225行にある。Cookie30分slide/Secure/HttpOnly/SameSiteStrict、HTTPS redirect、CSP selfとframe-ancestors noneの具体値が全954行で未収録。AC-02は一部改善したが共通HTTP補足の軽微不足が残る"
        if audit_id == "C-05":
            reason = "FK実線と読取JOIN点線、NULL可能なclassと在学/休学の所属必須CHECKを938-942行で限定。memory辞書とt_runtime_state未接続、DBロールとWebRoleを別に説明。基本R1のDC-03相当の限定不足は詳細R1ではない"
        if audit_id == "C-06":
            reason = "observed-source/DDL宣言/未接続保守と静的HTML投影/実撮影/DB適用・認証運用・実性能を区別。今回原ソースから新たな稼働成功や取消実証を推定しない"
        comparisons.append({"auditId":audit_id,"status":status,"responsibilityAndJudgment":reason,"sourceRequirement":original["requirement"],"sourceEvidenceIds":original["evidenceRefs"],"draftCitations":[quote(s,e) for s,e in OBLIGATION_LINES[audit_id]]})
    fields = []
    for original in checklist["fieldCatalogue"]:
        audit_id = original["id"]
        included = audit_id in FIELD_LINES
        fields.append({"auditId":audit_id,"sourceDomId":original.get("sourceDomId"),"status":"矛盾" if audit_id == "search.condition.admission-to" else "含まれる" if included else "対象外","responsibility":"検索DOM/DTO/DB/長さ/初期値、または検索復帰hidden境界" if included else "登録全項目・管理表示・削除理由は登録文書責務","judgment":"項目表168行の等日排除だけDC-04。処理説明322行とSQL346行は等日許容" if audit_id == "search.condition.admission-to" else "当該責務の原ソース属性と整合" if included else "検索責務外","sourceEvidenceIds":original["evidenceRefs"],"draftCitations":[quote(s,e) for s,e in FIELD_LINES.get(audit_id,[])]})
    diagrams = []
    for diagram_id, subject, start, end, audit_ids in DIAGRAMS:
        judgment = "本文と接続された原ソースの条件・結果・例外境界を保持。完成画像の視覚・読みやすさは未レビュー"
        if diagram_id == "D-03":
            judgment = "検索判定図は正しい処理説明322行に対応。日付168行の誤制約とは不一致で、DC-04は図/実装側を変えず項目説明を直す"
        if diagram_id == "D-10":
            judgment = "Savedだけ303、既存読込版と新Entry、復帰拒否、Applied有無、通知Takeと表示失敗順は整合。非SavedノードだけではUnknown後の検索確認案内を補えずDC-05が残る"
        if diagram_id == "D-11":
            judgment = "DDL FKとSQL JOINを異なる線で表示。nullableclassは940行の区分依存CHECKと一緒に説明され、全区分任意所属へ拡張していない"
        diagrams.append({"id":diagram_id,"subject":subject,"auditIds":audit_ids,"status":"含まれる","judgment":judgment,"draftCitation":quote(start,end),"renderedImageReviewed":False})
    issues = [
        {"id":"DC-04","severity":"medium","important":True,"kind":"矛盾","auditId":"S-05","fieldAuditId":"search.condition.admission-to","subject":"入学日終了の表制約が同日検索を排除","finding":"詳細R1の168行『両端指定時は開始以下にならないこと』はto>fromとなり、元ソース122行のfrom>toだけ拒否（from=toは許容）と矛盾。同稿167/322行と345/346行の説明・SQLは正しいため局所の表文言誤り","sourceCitations":[source_quote("service-search-validation",120,122),source_quote("service-search-sql",149,150)],"draftCitations":[quote(167,168),quote(322,322),quote(345,346)],"impact":"同一入学日だけを絞る検索の受入条件を誤る","minimalSourceBackedRevision":"終了日は開始日以上（同日可）と明記。処理条件や原ソースを変更しない"},
        {"id":"DC-05","severity":"medium","important":True,"kind":"必須欠落","auditId":"R-26","subject":"保存結果不明後の再送回避と検索確認案内","finding":"Unknownの判定/非Saved/303なしは796-803行にあるが、全稿に『再送せず検索して確認』『再保存の前に検索で確認』に相当する結果不明後の利用者行動がない。検索復帰境界の意味材料として必要","sourceCitations":[source_quote("service-save-write",319,323),source_quote("presentation-result",28,30)],"draftCitations":[quote(794,803),quote(811,834)],"impact":"DB確定の成否が不明なまま保存を再送する誤った手順を防ぐ案内が仕様材料に残らない","minimalSourceBackedRevision":"Unknown時は成功/失敗を断定せず、再保存/再送の前に検索で結果を確認する案内と根拠を検索復帰境界へ補足。登録全token・確認dialogを検索文書へ追加しない"},
        {"id":"DC-06","severity":"low","important":False,"kind":"必須欠落","auditId":"C-03","subject":"Cookie/HTTPS/CSP具体設定の補足不足","finding":"no-store/nosniff/no-referrer/CSP名、CSRF/body/値数は記載され解析AC-02より改善。Cookie30分slide/Secure/HttpOnly/SameSiteStrict、HTTPS redirect、CSP self+frame-ancestors noneの具体設定が未記載","sourceCitations":[source_quote("web-host",14,15),source_quote("web-host",22,25)],"draftCitations":[quote(193,197),quote(221,225)],"impact":"主要検索動作ではなく共通HTTP設定の軽微補足不足","minimalSourceBackedRevision":"原設定の具体値とsource位置を共通HTTP補足へ追加。production認証成功や適用済み保証を推定しない"},
    ]
    counts = {status:sum(row["status"] == status for row in comparisons) for status in ("矛盾","必須欠落","含まれる","対象外")}
    field_counts = {status:sum(row["status"] == status for row in fields) for status in ("矛盾","必須欠落","含まれる","対象外")}
    report = {
        "schema":"reverse-source-document-comparison/1","projectId":"test-project1","technology":"CSharp_ASPNET","documentId":"CSHARP_ASPNET-DET-CSharp_ASPNET-SCR-STU-001","recordedAtUtc":datetime.now(timezone.utc).isoformat(),
        "stage":"old-R1-audit-only-not-canonical","checklist":{"path":checklist_path.relative_to(ROOT).as_posix(),"sha256":EXPECTED_CHECKLIST},"draft":{"path":DRAFT,"sha256":EXPECTED_DRAFT,"lineCount":len(lines)},
        "method":"Independent AI read all 954 authorized detailed R1 lines, including static HTML, field/SQL/state tables and 11 Mermaid diagrams, and manually compared every locked source obligation/field group/visual material. Script only validates SHA/ID completeness and copies exact quotations. No original spec/evaluation/score or unapproved other draft was read, and no code/prompt/facts/source/checklist/draft was edited.",
        "boundaries":{"originalSpecRead":False,"specEvalRead":False,"scoresReadOrProduced":False,"unrelatedOldDraftRead":False,"renderedImagesReviewed":False,"applicationOrDbExecuted":False,"analysisReviewedBeforeDraft":True,"allowedPreviouslyReviewedDraft":"basic R1 comparison-01 only, not acceptance evidence for this detailed R1","canonicalAdoptionRequested":False,"knownStructuralFailureAcceptance":"R1既知構造不備による採用不可と今回のsource意味指摘を別に保持。search03修正稿には別SHA監査が必要"},
        "summary":{"importantSemanticDefects":["DC-04","DC-05"],"majorSearchFieldsEventsBranchesUnitsMemoryDbBoundaryMostlyPreserved":True,"obligationCounts":counts,"fieldGroupCounts":field_counts,"fieldGroupsClassified":len(fields),"mermaidDiagramsMeaningCompared":11,"eventAndCommonFlowcharts":10,"fkAndJoinRelationDiagrams":1,"minorIssues":1,"renderedImagesReviewed":False,"adoptionApproved":False},
        "issues":issues,"obligationComparisons":comparisons,"fieldComparisons":fields,"diagramComparisons":diagrams,
        "visualMaterialReview":[
            {"auditId":"V-01","status":"含まれる","finding":"Viewer初期静的HTML、12条件/11列header/20件asc/未検索/無効pagerと非Viewer新規差分。placeholderは実データ/実撮影と扱わない","draftCitations":[quote(67,145)],"renderedImageReviewed":False},
            {"auditId":"V-02","status":"含まれる","finding":"正常一覧の件数/日時/role操作/行11列formatter/pager境界は差分と表で保持。固定サンプルを実DB行へ偽装していない","draftCitations":[quote(137,138),quote(142,142),quote(172,187),quote(844,859)],"renderedImageReviewed":False},
            {"auditId":"V-03","status":"含まれる","finding":"0件/超過/検証異常/未検索・blanktbody/header・pagerとARIA/error/通知・保持結果と表示結果の相違を保持。host拒否HTMLは正常一覧と別","draftCitations":[quote(140,145),quote(543,549),quote(852,861)],"renderedImageReviewed":False},
            {"auditId":"V-04","status":"対象外","finding":"登録全画像は登録責務。Viewer検索/参照遷移/fieldsetdisabledとdirty戻り材料は検索境界へ保持","draftCitations":[quote(137,138),quote(766,772)],"renderedImageReviewed":False},
            {"auditId":"V-05","status":"必須欠落","finding":"登録dialogや全エラー画像は登録責務だが、検索に関わるUnknown後の検索確認案内はDC-05として欠落。非Saved303なし/読込版拒否/保存後再Load境界は保持","draftCitations":[quote(794,803),quote(811,834)],"renderedImageReviewed":False},
            {"auditId":"V-06","status":"含まれる","finding":"検索6イベント、MVC/Use/SearchAsync共通3図、復帰確定図、FK/JOIN図の意味をsourceと照合。図の切れ/重なり/文字可読性は親の稿SHA固定render/native確認へ分離","draftCitations":[quote(410,440),quote(811,832),quote(925,946)],"renderedImageReviewed":False},
        ],
        "sourceEvidenceCatalogue":checklist["evidenceCatalogue"],"sourceIntegrityChecks":source_integrity,
        "nextBoundary":"この旧R1をcanonical採用しない。search03最新稿は別SHAで同じ固定基準へ再照合し、rootのSHA固定render/native画像確認結果も別に記録する。旧R1の検査結果を新稿合格として流用しない。",
    }
    target.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8",newline="\n")
    # Also prove all read-only pinned inputs remain byte-identical after recording.
    if sha(checklist_path.read_bytes()) != EXPECTED_CHECKLIST or sha(draft_path.read_bytes()) != EXPECTED_DRAFT:
        raise ValueError("Pinned input changed during report recording")
    print(json.dumps({"path":str(target),"sha256":sha(target.read_bytes()),"counts":counts,"fieldCounts":field_counts,"importantSemanticDefects":2,"minorIssues":1,"sourcePairsReverified":len(source_integrity),"renderedImagesReviewed":False},ensure_ascii=False))


if __name__ == "__main__":
    main()
