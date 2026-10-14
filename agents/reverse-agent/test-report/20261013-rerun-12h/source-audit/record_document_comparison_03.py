"""Record AI review of basic05/detail04; no application or DB execution.

All coverage decisions and line selections below were made by the independent
source reviewer. The program copies quotations and checks integrity only.
"""
from __future__ import annotations
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]
HERE = Path(__file__).resolve().parent
SNAPSHOT = ROOT / "agents/reverse-agent/.tmp/20261013-rerun-12h/source-only/snapshot"
CHECKLIST_SHA = "40e184c35018ec8efe31915a91c48ab35a4ebb70670e61bc8d35c7d0a4aa4242"
DRAFTS = {
    "basic05": ("test-project1/spec-analysis/CSharp_ASPNET/20261013-rerun-12h/source-only/drafts/search-basic-05/基本設計書/01_学生検索画面.md", "1f307707bebcb621f7c0e7f895cec8e2a5c386c98c96aa5821c7e9619f0f6778"),
    "detail04": ("test-project1/spec-analysis/CSharp_ASPNET/20261013-rerun-12h/source-only/drafts/search-detail-04/詳細仕様書/CSharp_ASPNET/01_学生検索画面.md", "658617eb1367817031128eef12fbd51d50b758e04dff14f01997f14eacb1c785"),
}
OUTSIDE = {"R-01","R-05","R-06","R-07","R-08","R-09","R-10","R-11","R-12","R-13","R-14","R-15","R-18","R-19","R-20","R-21","R-23","R-27"}
# Each pair is (basic05 line ranges, detail04 line ranges).
LINES = {
 "S-01": ([(180,223)],[(166,213)]), "S-02": ([(19,21),(95,95),(599,601)],[(18,22),(106,107),(818,820)]),
 "S-03": ([(124,135),(233,245),(294,318)],[(123,134),(629,665)]), "S-04": ([(294,318)],[(645,698)]),
 "S-05": ([(124,135),(238,245),(314,322)],[(123,134),(631,643),(706,708)]), "S-06": ([(367,377),(860,874)],[(602,627)]),
 "S-07": ([(97,97),(130,130),(336,342),(377,377)],[(108,115),(129,129),(290,294)]),
 "S-08": ([(328,377)],[(282,334)]), "S-09": ([(233,286),(322,326),(911,933)],[(223,280),(562,600)]),
 "S-10": ([(96,116),(316,322)],[(110,113),(702,708),(750,757)]), "S-11": ([(379,441)],[(336,405)]),
 "S-12": ([(443,485)],[(407,456)]), "S-13": ([(487,536)],[(458,518)]),
 "S-14": ([(151,154),(168,174),(900,937)],[(32,38),(135,137),(562,600),(808,812)]),
 "S-15": ([(140,155),(886,894)],[(142,153),(738,748)]), "S-16": ([(322,326),(441,441),(939,949)],[(274,280),(399,405),(540,560)]),
 "R-01": ([(540,555)],[(816,820)]), "R-02": ([(540,601)],[(816,820)]), "R-03": ([(21,21),(599,599)],[(20,20),(818,818)]),
 "R-04": ([(551,587),(611,613),(935,935)],[(818,826)]), "R-05": ([(892,894)],[(738,744)]),
 "R-06": ([(143,143),(888,888)],[(145,145),(746,748)]), "R-07": ([(827,856)],[(798,802)]),
 "R-08": ([(133,133),(832,832)],[(132,132),(800,800)]), "R-09": ([(615,617)],[(828,830)]),
 "R-10": ([(377,377)],[(115,115)]), "R-11": ([(616,616)],[(830,830)]), "R-12": ([(616,616)],[(830,830)]),
 "R-13": ([(616,616),(870,870)],[(621,623),(830,830)]), "R-14": ([(615,615),(618,618)],[(832,832)]),
 "R-15": ([(615,615)],[(828,828)]), "R-16": ([(615,619),(708,725)],[(828,850)]),
 "R-17": ([(617,617),(646,646),(717,725)],[(830,830),(848,850)]), "R-18": ([(700,702)],[(828,830)]),
 "R-19": ([(700,702)],[(828,830)]), "R-20": ([(700,702),(937,937)],[(808,808),(828,830)]),
 "R-21": ([],[]), "R-22": ([(614,623),(698,702)],[(828,836)]), "R-23": ([(702,702),(807,807)],[(832,836)]),
 "R-24": ([(620,623),(651,656),(727,727),(904,909)],[(860,896)]),
 "R-25": ([(708,727),(811,813)],[(838,858)]), "R-26": ([(670,681),(706,725),(782,813)],[(838,858),(862,892)]),
 "R-27": ([(601,601)],[]), "R-28": ([(553,553),(573,601)],[(818,820)]), "R-29": ([(733,747)],[(822,826),(834,836)]),
 "R-30": ([(741,747),(801,807),(835,835)],[(834,836),(860,896)]), "R-31": ([(741,813)],[(834,858)]),
 "C-01": ([(164,178),(945,947)],[(24,44)]), "C-02": ([(233,234),(896,898)],[(524,534)]),
 "C-03": ([(154,154),(164,164),(896,898),(943,945)],[(162,162),(524,528),(540,560)]),
 "C-04": ([(943,945)],[(540,560)]), "C-05": ([(817,856),(900,909),(935,937)],[(763,812)]),
 "C-06": ([(11,13),(31,35),(837,856),(882,884),(941,947)],[(24,28),(50,54),(759,761),(804,812),(856,858)]),
}
FIELDS = {
 "search.condition.student-no":(124,123),"search.condition.name":(125,124),"search.condition.kana":(126,125),
 "search.condition.year":(127,126),"search.condition.grade":(128,127),"search.condition.class":(129,128),
 "search.condition.unassigned":(130,129),"search.condition.status":(131,130),"search.condition.prefecture":(132,131),
 "search.condition.phone":(133,132),"search.condition.admission-from":(134,133),"search.condition.admission-to":(135,134),
 "search.grid":((140,155),(142,153)),"search.paging":((136,139),(138,141)),
 "search.internal-state":((151,154),(135,137)),"register.internal-state":((551,555),(818,826)),
}
DIAGRAMS = {
 "basic05": [(199,211,"初期"),(249,284,"検索"),(348,363,"候補下書き"),(400,429,"ページ補正"),(462,473,"クリア"),(507,524,"検索復帰"),(559,585,"遷移・読込版・dirty戻り"),(627,679,"保存・確定・303・例外"),(687,692,"処理参照/書込の関係"),(751,795,"論理削除・確定・303・例外"),(841,848,"DDL FK/nullableclass"),(913,931,"共有Use排他/状態/版/期限")],
 "detail04": [(184,199,"初期"),(236,264,"検索"),(300,318,"候補下書き"),(356,389,"ページ補正"),(426,442,"クリア"),(477,500,"検索復帰"),(540,554,"MVC共通入口"),(579,596,"共有Use"),(710,734,"SearchAsync検証/SQL/例外"),(765,777,"FK実線とSQL JOIN点線"),(862,890,"Saved/Unknown/非Saved/303/版/通知")],
}
NOTES = {
 "S-03":"全12条件のAND、在籍IN、電話の括弧内OR、削除除外、正規化と表示値を保持",
 "S-05":"両稿でfrom<=to（同日可）を保持。年度/クラス/コード/区分/長さと検査段階も整合し、旧DC-04は解消",
 "S-06":"停止/期間外候補を検索で除外せず、登録保存側の許可規則とは区別",
 "S-08":"候補更新は受信下書きと選択解除。Applied/LastResult/Revisionを変えず、Use/Gate/期限延長なし",
 "S-09":"状態の所有者/session/任意Tab/TTL/文字列版/排他を保持。成功後の表示失敗を状態更新前へ戻さない",
 "S-10":"未検索/成功0件/通常/上限超過、totalCount/時刻/空tbodyと常設11列header、操作活性を分ける",
 "S-11":"サイズ/並び変更はPage1。末尾補正は条件Pageを変えて別Snapshotで再検索する",
 "S-13":"Resumeは再検索し、Appliedを変更せず、SQL内部補正と画面page差を明示。版照合後に通知Take",
 "S-14":"URLは検索Context/版/学生識別値、検索個人条件はPOSTとメモリ保持。暗号化DB永続化へ拡張しない。ログのPII無出力まで保証しない",
 "R-24":"Savedだけ303、既存Snapshot読込版と新Entry版を別保持。DB確定/303/復帰/通知表示を別到達段階にする",
 "R-26":"一般catchのみwriteStarted AND (commitAttempted OR !rolledBack)。結果不明時は再保存前に検索確認。詳細は画面接続FieldErrorと未接続JSON helperの文言を区別。旧DC-05は解消",
 "C-03":"CSRF/body等はあるが、Cookie属性・30分slide/HTTPS/CSP具体値が欠落。basicは保護headers自体を未記載、detailは名称のみ。既存の共通補足不足が継続",
 "C-05":"検索関連FKとSQL JOIN、学生/auditの確定、メモリ状態を保持。basicのnullableclass説明には01/02所属必須CHECKの具体限定不足が残る。詳細798行は明示",
 "C-06":"観測ソース/DDL/静的投影/未接続helperを区別。今回アプリ/DB/login/多重要求/実機画面を実行確認しておらず、その成功を主張しない",
}


def sha(data):
    return hashlib.sha256(data).hexdigest()


def main():
    target=HERE/"document-comparison-03.json"
    if target.exists(): raise SystemExit("Do not overwrite independent review")
    cp=HERE/"checklist.v1.json"
    assert sha(cp.read_bytes())==CHECKLIST_SHA
    c=json.loads(cp.read_text(encoding="utf8"))
    assert set(LINES)=={x["id"] for x in c["obligations"]}
    doclines={}
    for key,(path,pinned) in DRAFTS.items():
        data=(ROOT/path).read_bytes(); assert sha(data)==pinned
        doclines[key]=data.decode("utf-8-sig").splitlines()
    def quote(key,start,end):
        path,pinned=DRAFTS[key]; lines=doclines[key]
        assert 1<=start<=end<=len(lines)
        text="\n".join(lines[start-1:end])+"\n"
        return {"path":path,"sha256":pinned,"startLine":start,"endLine":end,"quote":text,"lineRangeSha256":sha(text.encode("utf8")),"rangeEncoding":"UTF-8 no BOM/LF join/final LF"}
    def src(path,start,end):
        f=SNAPSHOT/"sources"/path;data=f.read_bytes();lines=data.decode("utf-8-sig").splitlines()
        assert 1<=start<=end<=len(lines)
        text="\n".join(lines[start-1:end])+"\n"
        return {"path":f.relative_to(ROOT).as_posix(),"sha256":sha(data),"startLine":start,"endLine":end,"quote":text,"lineRangeSha256":sha(text.encode("utf8")),"rangeEncoding":"UTF-8 no BOM/LF join/final LF"}
    known={x["path"]:x for x in c["evidenceCatalogue"].values()}
    inventory=[]
    for p in sorted((SNAPSHOT/"sources").rglob("*")):
        if not p.is_file():continue
        rel=p.relative_to(SNAPSHOT/"sources").as_posix();data=p.read_bytes(); indexed=SNAPSHOT/"indexed"/(rel+".txt")
        digest=sha(data);idigest=sha(indexed.read_bytes()) if indexed.is_file() else None
        if rel in known:
            assert digest==known[rel]["sourceSha256"] and idigest==known[rel]["indexedSha256"]
        inventory.append({"path":rel,"sourceSha256":digest,"indexedSha256":idigest,"bytes":len(data),"lineCount":len(data.decode("utf-8-sig").splitlines()),"matchesPriorLockedChecklist":True if rel in known else None,"priorLockedChecklistEvidence":rel in known})
    assert len(inventory)==41 and len(known)==25
    obligations=[]
    for original in c["obligations"]:
        aid=original["id"];status="対象外" if aid in OUTSIDE else "必須欠落" if aid=="C-03" else "含まれる"
        reason="登録全項目/重複確認操作/保守の業務詳細は検索文書の独立責務外。検索へ影響する共有属性または復帰確定境界だけ要求" if aid in OUTSIDE else NOTES.get(aid,"当該検索または検索復帰責務の条件・分岐・結果が、手動選択引用で原ソースへ対応する")
        obligations.append({"auditId":aid,"sourceRequirement":original["requirement"],"sourceEvidenceIds":original["evidenceRefs"],"manualResponsibilityAndJudgment":reason,**{key:{"status":status,"draftCitations":[quote(key,s,e) for s,e in LINES[aid][i]]} for i,key in enumerate(DRAFTS)}})
    fields=[]
    for original in c["fieldCatalogue"]:
        aid=original["id"];include=aid in FIELDS;row={"auditId":aid,"sourceDomId":original.get("sourceDomId"),"sourceEvidenceIds":original["evidenceRefs"]}
        for i,key in enumerate(DRAFTS):
            rg=FIELDS[aid][i] if include else None; rg=(rg,rg) if isinstance(rg,int) else rg
            row[key]={"status":"含まれる" if include else "対象外","draftCitations":[quote(key,*rg)] if rg else [],"responsibility":"検索DOM/DTO/DB/長さ単位/初期値または復帰hidden境界" if include else "登録全項目/管理表示/理由欄は登録責務"}
        fields.append(row)
    issues=[
      {"id":"DC-07","severity":"low","important":False,"state":"existing-source-gap-persists","auditId":"C-03","subject":"共通HTTP保護設定の具体値不足","finding":"basic05全949行にはno-store/nosniff/no-referrer/CSP設定そのものがない。detail04の556行は名前だけでCSP具体値なし。両稿にCookie30分slide/SecureAlways/HttpOnly/SameSiteStrict、HTTPS redirectの記載がない","sourceCitations":[src("Infrastructure/WebHostSetup.cs",14,15),src("Infrastructure/WebHostSetup.cs",22,25)],"draftCitations":[quote("basic05",943,945),quote("detail04",524,560)],"minimalSourceBackedRevision":"凍結active06/05は変更せず後続AI改訂または共通補足へ原設定とsource位置を追記。DB適用やproduction認証成功を推定しない"},
      {"id":"DC-08","severity":"low","important":False,"state":"known-diagram-ambiguity-persists","auditId":"R-26","subject":"基本図のUnknown条件が括弧なし","finding":"basic05図670/782はAND/OR括弧なし。直後681/797と715行がwriteStarted AND (commitAttempted OR rollback不成功)を正しく限定し、書込未開始はSystemErrorとするため新たな重要誤りとはしない。詳細846行は括弧付き","sourceCitations":[src("Core/SqlServerStudentService.cs",319,323),src("Core/SqlServerStudentService.cs",415,416)],"draftCitations":[quote("basic05",670,681),quote("basic05",782,797),quote("detail04",846,846)],"minimalSourceBackedRevision":"図判定自体にも『書込開始済み AND（commit試行済み OR rollback不成功）』の括弧を付ける"},
      {"id":"DC-09","severity":"low","important":False,"state":"known-basic-nullability-limitation-persists","auditId":"C-05","subject":"基本ERの任意所属の区分依存CHECK限定不足","finding":"basic05の827/839/845はNULL可能な列/FKとして正しい。856行に在籍区分・日付・所属のCHECKがあるとだけ述べ、01/02はclass必須という具体条件を省く。detail04の798行は正確な限定を保持している","sourceCitations":[src("database/001_schema.sql",198,200)],"draftCitations":[quote("basic05",827,827),quote("basic05",839,856),quote("detail04",798,802)],"minimalSourceBackedRevision":"基本のER説明へ在学/休学は所属必須、卒業/退学は任意というsource CHECK限定を添える"},
    ]
    diagrams={key:[{"subject":label,"draftCitation":quote(key,s,e),"manualMeaningJudgment":"当該責務のsource条件/結果/例外を本文と合わせ保持。basic Unknown条件の図単独の曖昧さはDC-08へ、nullableclass限定不足はDC-09へ記録。画像可読性は別検査","renderedImageReviewed":False} for s,e,label in ranges] for key,ranges in DIAGRAMS.items()}
    counts={key:{status:sum(x[key]["status"]==status for x in obligations) for status in ("矛盾","必須欠落","含まれる","対象外")} for key in DRAFTS}
    report={
      "schema":"reverse-source-document-comparison/1","projectId":"test-project1","technology":"CSharp_ASPNET","recordedAtUtc":datetime.now(timezone.utc).isoformat(),"stage":"source-only-basic05-detail04-before-newer-revisions",
      "checklist":{"path":cp.relative_to(ROOT).as_posix(),"sha256":CHECKLIST_SHA},"drafts":{key:{"path":path,"sha256":pinned,"lineCount":len(doclines[key])} for key,(path,pinned) in DRAFTS.items()},
      "method":"AI read all 949 basic05 and 896 detail04 lines; manually compared 53 locked source obligations, 40 field groups, 23 diagrams and six visual material responsibilities. Python records quotations, hashes, completeness and inventory only; it does not author specification body, execute ASP.NET/SQL/deployment scripts, or compute a specification score.",
      "boundaries":{"originalSpecRead":False,"specEvalRead":False,"trainingAssistedRead":False,"scoresReadOrProduced":False,"newerBasic06OrDetail05Read":False,"codePromptFactsDraftSourceChecklistEdited":False,"applicationDbDeploymentExecuted":False,"nativeImageReviewPerformed":False,"knownGeometryAndSelectedFalse":"parent-known; no geometry retest or visual acceptance claim","priorReviewResultsReusedAsNewPass":False},
      "summary":{"newImportantSourceBackedSemanticDefects":[],"sameDayDateConditionPreserved":True,"unknownUserGuidancePreserved":True,"majorSearchBoundariesPreserved":True,"obligationCounts":counts,"fieldGroupsClassified":40,"mermaidDiagramsMeaningCompared":{"basic05":12,"detail04":11},"existingMinorGaps":3,"canonicalAdoptionOrVisualPassClaimed":False},
      "issues":issues,"obligationComparisons":obligations,"fieldComparisons":fields,"diagramComparisons":diagrams,
      "resolvedEarlierIssues":[{"id":"DC-04","result":"resolved-at-authorized-SHAs","sourceCitations":[src("Core/SqlServerStudentService.cs",120,122)],"draftCitations":[quote("basic05",134,135),quote("detail04",133,134),quote("detail04",637,637)]},{"id":"DC-05","result":"resolved-at-authorized-SHAs","sourceCitations":[src("Core/SqlServerStudentService.cs",320,322),src("Core/SqlServerStudentService.cs",415,416)],"draftCitations":[quote("basic05",723,727),quote("detail04",852,858),quote("detail04",862,892)]}],
      "piiGuardReview":{"observed":"検索個人条件はPOST、往復URLは識別値、所有者/session/任意Tab検査とメモリ保持。no-store/Cookie/HTTPS/CSP原設定は存在するが文書へ十分収録されていない","sourceCitations":[src("Views/Students/Search.cshtml",4,8),src("Infrastructure/SearchContextStore.cs",9,14),src("Infrastructure/WebHostSetup.cs",14,25)],"draftCitations":[quote("basic05",168,174),quote("basic05",904,911),quote("detail04",32,38),quote("detail04",808,812)],"unknown":"Logging設定はWarningに限定されるが、framework/server/実環境ログのPII無出力、DB暗号化、運用上のアクセス隔離は未実証。t_runtime_stateのencrypted_payloadからWeb保存の暗号化を推定しない"},
      "visualMaterialReview":[{"auditId":x["id"],"status":"対象外" if x["id"]=="V-04" else "責務範囲の材料が含まれる","manualJudgment":"初期/正常/0件/超過/異常/Viewer差分、検索6イベント・復帰確定・関係図を両稿で照合。登録全画面/dialogは責務外。Unknown後の検索確認材料は詳細図にも保持。静的HTMLや図のnative画像合格は主張しない","renderedImageReviewed":False} for x in c["visualChecks"]],
      "sourceEvidenceCatalogue":c["evidenceCatalogue"],"rawSourceInventory":inventory,
      "sourceSealScope":{"parentDeclaredSealedSnapshot":True,"globalManifestSealRead":False,"allRawFilesEnumeratedAndHashed":41,"priorLockedRawIndexedPairsVerified":25,"remaining16":"Small connected model/filter/layout/config/build declarations and MasterMaintenance were inspected. Deployment/verification/package-lock files were inspected for declared role/runtime boundary by scoped searches, not executed or used as business expectations. Their current hashes are newly recorded; no independent previous 41-file seal was read."},
      "communications":{"sourcePilotReceivedSourceBackedHttpQuotes":True,"rootReceivedFindings":True,"activeFrozenContextMustRemainUnchanged":True},
      "nextBoundary":"basic06/detail05はこの監査の対象ではない。後続AI局所改訂または補足でsource-backed差分を反映し、各新SHAを改めて検査。helper gate通過とnative画像合格、source static factとアプリ実機合格を分ける。",
    }
    target.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf8",newline="\n")
    assert sha(cp.read_bytes())==CHECKLIST_SHA
    for path,pinned in DRAFTS.values():assert sha((ROOT/path).read_bytes())==pinned
    print(json.dumps({"path":str(target),"sha256":sha(target.read_bytes()),"counts":counts,"importantNewDefects":0,"existingMinorGaps":3,"rawCount":41,"lockedPairsVerified":25},ensure_ascii=False))


if __name__=="__main__":main()
