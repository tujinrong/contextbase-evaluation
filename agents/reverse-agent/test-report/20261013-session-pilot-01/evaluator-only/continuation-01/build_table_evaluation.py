"""Assemble manually reviewed table decisions; no automatic semantic matcher."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib, json, re
from collections import Counter

OUT = Path(__file__).resolve().parent
FROZEN = OUT / 'frozen'
MANIFEST = json.loads((OUT / 'frozen-manifest.json').read_text(encoding='utf-8'))
ITEMS = json.loads((OUT / 'selected-rows.json').read_text(encoding='utf-8'))
PINS = {x['snapshotPath']: x for x in MANIFEST['pins']}

# Every field and interpretation below was independently read by the evaluator.
# Each tuple: physical field, judgment, semantic rationale, supplementary MD lines.
REVIEWS = {
    'm_student': [
        ('student_id','match','内部識別子・採番・不変を項目表と保存設定表で確認。bigintの整数域は19桁小数0の表記と意味対応。欠番を連番保証へ置換していない。',[(8,10),(213,214)]),
        ('student_no','missing','一意・削除後の再利用禁止・変更不可は記載。学校の付番責務は本文に記載がなく全属性一式は未一致。',[(10,10),(63,63),(214,214)]),
        ('student_name','match','8スカラーと16 UTF-16単位を区別し、原表記保持とTrimを補足で記載。',[(466,470)]),
        ('student_name_kana','match','業務18スカラーと物理36単位を分け、FormKC・カタカナ化を具体的に記載。',[(472,472)]),
        ('name_key','match','氏名派生キー、160スカラー、検索・候補比較・通常保存時の再作成を本文と設定処理で確認。',[(209,209),(226,226),(470,470)]),
        ('kana_key','match','正規化カナの空白除去、18スカラー、検索/候補比較用を記載。',[(472,472)]),
        ('birth_date','match','内部日付・元号入力/復元、1900下限・入学日との前後・業務日以前の条件を補足で確認。',[(324,324),(480,480)]),
        ('gender_category','match','型/必須/分類固定/処理設定を記載。',[]),
        ('gender_code','match','1桁・必須・未回答0の初期値・分類と値の複合参照を表、制約、補足で確認。',[(65,65),(488,488)]),
        ('postal_code','match','7文字ASCII・区切り除去・先頭ゼロ保持を記載。',[]),
        ('prefecture_category','match','型/必須/分類固定/処理設定を記載。',[]),
        ('prefecture_code','match','国内都道府県の論理名、2桁コード、複合FKの対象列を制約表で確認。',[(66,66)]),
        ('address_line1','missing','必須・型・45スカラーは記載されるが、住所1に入れる住所成分の業務説明がない。',[]),
        ('address_line2','missing','任意・型・45スカラー・空入力NULLは記載されるが、住所2に入れる住所成分の業務説明がない。',[]),
        ('phone_number','match','任意/連絡先の条件付き必須、国内/国際形式、区切り除去を記載。',[(71,71),(474,474)]),
        ('email_address','match','60 ASCII文字、形式と条件付き必須、一意制約なしによる共有を補足で記載。',[(71,71),(476,476)]),
        ('admission_date','match','1900下限・生年月日以上・業務日以前をDB/サービス境界として記載。',[(70,70),(480,480)]),
        ('enrollment_category','match','型/必須/分類固定/処理設定を記載。',[]),
        ('enrollment_status_code','match','4状態と01初期値、分類と値の複合参照を記載。',[(67,67),(488,488)]),
        ('enrollment_end_date','match','終了状態だけ必須、在学/休学NULL、1900下限・入学日以上・業務日以前を記載。',[(70,70),(480,480)]),
        ('class_id','match','在学/休学必須、他状態NULL可、単一列で最大1所属、FKの参照先を記載。bigint整数域は19桁小数0と意味対応。',[(10,10),(64,64)]),
        ('emergency_contact_name','match','8スカラー、NULL可、一式入力時の必須性を記載。',[(71,71)]),
        ('relationship_category','match','未選択NULL、有値時の固定分類、22列の通常保存値への同時設定を記載。',[(71,71),(209,209),(226,226)]),
        ('relationship_code','missing','2桁・複合FK・一式NULL整合は記載されるが、続柄の業務値の意味を項目定義で説明していない。',[(68,68),(71,71)]),
        ('emergency_phone_number','match','本人電話と同じ16文字保存形式、一式入力時の必須を記載。',[(71,71),(474,474)]),
        ('remarks','missing','120スカラーと改行可は記載されるが、業務上の対象外情報の境界が記載されない。',[]),
        ('is_deleted','match','bit・既定0・論理削除1・在籍状態との独立性を記載。',[(10,10),(72,72)]),
        ('deleted_at','match','日時型・NULL可・削除時設定・未削除NULLを記載。',[(72,72)]),
        ('deleted_by','match','64スカラー・NULL可・認証主体から削除時設定・未削除NULLを記載。',[(72,72)]),
        ('delete_reason','match','60スカラー・削除時必須・空白拒否・未削除NULLを記載。',[(72,72),(482,482)]),
        ('created_at','match','最初のINSERT時点で設定し通常更新/論理削除で変更しないことを記載。',[]),
        ('created_by','match','認証主体64スカラー、初回設定、通常更新/論理削除で変更しないことを記載。',[]),
        ('updated_at','match','新規/実変更/論理削除の日時設定と変更なし時の不変を記載。',[(500,500)]),
        ('updated_by','match','認証主体64スカラー、新規/実変更/論理削除の設定と変更なし時の不変を記載。',[(500,500)]),
        ('row_version','match','bigint整数域、正数、初期1、実変更/削除時の手動加算、無変更不変、上限拒否を補足で記載。',[(500,500)]),
    ],
    'm_class': [
        ('class_id','match','内部識別子・IDENTITY採番・更新設定列に含めないことを記載。64bit整数域は19桁小数0と意味対応。',[(202,202),(218,239)]),
        ('school_year','match','1900～9998の整数域と年度期間、登録後不変を本文で記載。',[(52,56)]),
        ('grade_category','match','24文字ASCII・固定GRADE・INSERT設定・更新不変を記載。',[]),
        ('grade_code','match','2桁・複合FK・参照学生がある場合の学年変更拒否・設計初期値と実装の区別を記載。',[(56,58),(423,427)]),
        ('class_code','match','9文字・形式・年度内一意・登録後不変を記載。',[(56,56)]),
        ('class_name','match','業務18スカラーと物理36 UTF-16単位、顧客表示名称を記載。',[(9,9)]),
        ('valid_from','match','年度内の開始日/終了日以下、設計の年度開始初期値と実装入力の区別を記載。',[(423,425)]),
        ('valid_to','match','年度内の終了日/開始日以上/両端含む、設計の年度終了初期値と実装入力の区別を記載。',[(52,52),(423,425)]),
        ('capacity','match','整数1～9999・任意NULL・NULLで制限なし・0拒否を記載。4桁小数0の業務域と意味対応。',[(57,57)]),
        ('display_order','match','32bit整数域・非負・既定0と候補順序を記載。10桁小数0の型域と意味対応。',[(277,277)]),
        ('is_active','match','bit・既定1、停止後も行と学生参照を残すことを記載。',[(373,373),(423,429)]),
        ('remarks','match','任意NULL・120スカラー、クラス説明用途と担任人事管理対象外を記載。',[(429,429)]),
        ('created_at','match','初回保存のUTC日時、更新対象外を記載。',[]),
        ('created_by','match','認証DBログイン名64スカラー、初回保存、更新対象外を記載。',[]),
        ('updated_at','match','実変更時の日時設定、無変更不変を記載。',[]),
        ('updated_by','match','認証DBログイン名64スカラー、実変更時設定、無変更不変を記載。',[]),
        ('row_version','match','手動bigint・初期1・実変更+1・無変更不変・最大整数で停止を記載。',[(60,60),(391,391)]),
    ],
    'm_code_category': [
        ('category_id','match','分類識別子24バイト・単一PKと設計上登録後不変を、実装境界と区別して記載。',[(328,330)]),
        ('category_name','match','分類名称12スカラー・物理24 UTF-16単位・具体的分類名を記載。',[(53,57)]),
        ('code_length','match','smallint・分類別固定幅・業務2.0の整数桁/小数桁表記を明示。',[(308,308),(332,332)]),
        ('allow_add','match','bit・通常保守におけるコード追加可否を記載。',[]),
        ('is_active','match','bit・既定1・5分類の有効状態維持を設計意図として記載し実DDL制約と区別。',[(53,57),(328,330)]),
        ('remarks','missing','型/120スカラー/NULLとseed設定は記載するが、備考を記載する業務用途の説明がない。',[]),
        ('created_at','match','初回UTC投入、設計上の作成情報不変を実装の権限/入口範囲と区別して記載。',[(328,330)]),
        ('created_by','match','DB認証者64スカラー・初回設定・設計上不変を明示。',[(328,330)]),
        ('updated_at','match','設計上の実変更時設定をseed実装/未実装通常保守と区別して記載。',[(328,330)]),
        ('updated_by','match','DB認証者64スカラーと設計上の実変更時設定を区別して記載。',[(328,330)]),
        ('row_version','match','初期1・bigint正数/上限と、設計上実変更+1・上限停止を記載し、未実装通常保守を偽装しない。',[(328,330)]),
    ],
    'm_code': [
        ('category_id','match','24文字ASCII・複合PK第1列・分類マスター参照を記載。',[]),
        ('code_value','match','10文字ASCII・複合PK第2列・分類別固定桁・先頭ゼロ保持を記載。',[]),
        ('code_name','match','12スカラー/24 UTF-16単位、option表示名としての利用を記載。',[(432,432)]),
        ('display_order','match','int・非負・既定0・同順位コード順の候補順序を記載。int整数域と10桁小数0の表記は意味対応。',[]),
        ('is_active','match','bit・既定1・分類状態との合成と新規停止値の選択不可を記載。',[(432,432),(447,447)]),
        ('valid_from','match','date・1900-01-01の初期投入・両端を含む期間を記載。',[(426,426)]),
        ('valid_to','match','NULL期限なし・開始日以上・非設定時NULLを記載。',[(426,426)]),
        ('is_protected','match','bit・停止/期間短縮禁止・通常保守新規0/既存保持を記載。',[(416,416),(428,428)]),
        ('remarks','missing','型/120スカラー/空入力NULLは記載するが、備考の業務用途を説明していない。',[]),
        ('created_at','match','初回UTC保存・更新対象外を設計意図と実装対応で記載。',[(490,490)]),
        ('created_by','match','DB認証者64スカラー・初回設定・更新対象外を記載。',[(490,490)]),
        ('updated_at','match','実変更時UTC設定、無変更不変を記載。',[(412,412)]),
        ('updated_by','match','DB認証者64スカラー・実変更時設定・無変更不変を記載。',[(412,412)]),
        ('row_version','match','bigint正整数・初期1・手動+1・無変更不変・long.MaxValue拒否を記載。',[]),
    ],
    't_operation_log': [
        ('log_id','match','単独PK・bigint整数域・IDENTITY採番・追記識別子を記載。',[]),
        ('target_table','match','21バイトと4対象の設計意図を再現し、現実装3対象と分類保守未実装を明示している。',[(410,410)]),
        ('target_key','match','35文字・内部ID/分類と値・氏名等の実値を保存しない識別構成を記載。',[(11,13)]),
        ('operation_type','match','11文字・5操作種別・学生DELETEが論理削除であることを記載。',[]),
        ('before_version','match','bigint整数域・新規NULL/それ以外は確認済み前版を、アプリとDDL境界を区別して記載。',[(412,412)]),
        ('after_version','match','bigint整数域・新規1/実変更は前版+1・DB DEFAULTなしを記載。',[(13,13),(412,412)]),
        ('changed_columns','hold','原基準の保存入口における許可列名/重複検査の要求に対し、ソースAudit/Logは受取配列のJSON化のみ。生成文書は固定構築とDDL検査範囲を正確に区別する。設計要求と構築による保証を同等と扱う裁定は未実施。',[(97,97),(163,163),(232,232),(285,285),(365,372)]),
        ('executed_by','match','認証主体・64スカラー・学生とマスターの設定元を記載。',[(394,394)]),
        ('executed_at','match','UTC時点型・業務保存と同じnowを設定することを記載。',[]),
        ('correlation_id','match','GUID・同一サービス要求との関連・要求調査用途とマスター内生成を記載。',[(404,404),(412,412)]),
        ('operation_reason','match','60スカラー/NULL可・削除/終了区分訂正/重複続行の条件付き必須を記載。',[(392,392)]),
        ('duplicate_confirmed','match','bit・既定0・重複確認を経た保存の設定と削除フォーム確認との区別を記載。',[(398,398)]),
    ],
    't_confirmation': [
        ('token','match','単一PK・GUID型・アプリ発行値を記載。文字列型へ置換せずDB分岐/メモリ分岐を区別。',[(129,139)]),
        ('principal','match','64スカラーの認証主体を発行時に設定し照合することを記載。',[]),
        ('session_id','match','GUIDの認証セッションを検証/変換して設定することを記載。',[]),
        ('target_id','match','bigint整数域・新規NULL/更新対象IDを記載。',[(56,56)]),
        ('expected_version','match','bigint整数域・新規NULL/更新正数の要求組合せを表/保存前検査で記載。',[(56,56)]),
        ('payload_hash','match','固定32バイト・正規化19業務項目のSHA-256を列挙して記載。',[(121,121)]),
        ('candidate_hash','match','固定32バイト・全候補ID/版を学生ID順に正規化してハッシュ化。先頭20件との区別を記載。',[(102,102),(123,123)]),
        ('expires_at','match','日時型・UTC・発行基準now+10分・時点を取り直さない条件を記載。',[(68,68)]),
        ('consumed','match','bit・発行時0・有効確認後の学生保存と同一トランザクションで1へ更新することを記載。',[(274,277)]),
    ],
    't_runtime_state': [
        ('state_id','unobservable','型/PKは再現されるが、DB状態IDの発行・メモリIDとの列対応は未実装で観測不能。メモリの256bit hexを物理列の保証に転記しない。',[(301,301),(309,319)]),
        ('owner_id','unobservable','型/64スカラーは再現されるが、物理行の認証主体設定経路がなくメモリ所有者との対応は観測不能。',[(309,319)]),
        ('login_session_id','unobservable','型/64バイトは再現されるが、認証セッションとの物理行設定契約は未接続。',[(301,301),(309,319)]),
        ('state_kind','unobservable','型/16バイトは再現されるが、DB上の状態種別値と検索/確認/通知の対応は未定義。',[(301,301),(325,325)]),
        ('encrypted_payload','unobservable','varbinary(max)は再現されるが認証付き暗号・平文禁止の物理保存経路がない。列名だけで暗号化済みと加点しない。',[(303,303),(325,325)]),
        ('expires_at','unobservable','UTC型は再現されるが、物理行の検索/確認期限設定経路は未実装。メモリ期限をDB契約へ置換しない。',[(295,295),(309,319)]),
        ('revision','unobservable','bigint正数は再現されるが、物理行の初期1設定・加算/比較契約は未実装。',[(297,297),(309,313)]),
        ('consumed','unobservable','bitは再現されるが、物理行の初期0設定・一回消費経路は未実装。',[(305,305),(317,319)]),
    ],
}

def evidence(path,start,end):
    assert path in PINS, path
    content=(FROZEN/path).read_text(encoding='utf-8-sig').splitlines()
    assert 1 <= start <= end <= len(content), (path,start,end,len(content))
    return dict(path=path,startLine=start,endLine=end,sha256=PINS[path]['sha256'])

rows=[]
reference_versions={x['documentId']:x['currentVersion'] for x in json.loads((FROZEN/'evaluation/bridge-CSharp_ASPNET.json').read_text(encoding='utf-8-sig'))['documents']}
for table,decisions in REVIEWS.items():
    document_id='DBDEF-SQLSERVER-'+table.upper()
    items=[x for x in ITEMS if x['documentId']==document_id]
    assert len(items)==len(decisions)+1
    path='generated/20261013-pilot-v3-tables/spec/database/tables/'+table+'.md'
    lines=(FROZEN/path).read_text(encoding='utf-8').splitlines()
    header=items[0]
    rows.append(dict(evaluationId=header['evaluationId'],documentId=document_id,judgement='missing',originalPoints=3,awardedPoints=0,critical=False,criticalReason='文書内共通参照/書式契約の欠落。保存・認証動作の矛盾は確定していない。',explanation='名称・用途・スキーマ・列数・PKは表本文から確認できるが、テーブルヘッダーとしての共通制約/基礎仕様の参照対応一式を提示していない。文字列のID/版差だけを減点理由にしていない。',generatedEvidence=[evidence(path,1,min(16,len(lines)))],sourceEvidence=[],sourceFidelity='NO_GENERATED_FALSE_GUARANTEE_ESTABLISHED',reference=dict(path='current-reference/'+header['currentSpecPath'],sha256=header['currentSpecSha256']),semanticReviewMethod='MANUAL_ITEM_LEVEL'))
    for item,(field,judgement,reason,extra) in zip(items[1:],decisions):
        assert f'物理名={field}；' in item['originalCells'][4], (document_id,field)
        primary=next(n for n,s in enumerate(lines,1) if s.startswith('|') and f'| {field} |' in s)
        generated=[evidence(path,primary,primary)]+[evidence(path,a,b) for a,b in extra]
        source=[]
        for match in re.finditer(r'sources/([^`|;、／\s:]+\.(?:cs|sql|cshtml|js|ps1)):(\d+)[–-](\d+)',lines[primary-1]):
            sp='sources/'+match.group(1);a=int(match.group(2));b=int(match.group(3)); ref=evidence(sp,a,b)
            if ref not in source: source.append(ref)
        if field=='changed_columns':
            source.extend([evidence('sources/Core/SqlServerStudentService.cs',385,390),evidence('sources/Core/MasterMaintenanceService.cs',132,135)])
        if table=='t_runtime_state':
            source.extend([evidence('sources/Infrastructure/SearchContextStore.cs',9,14),evidence('sources/Infrastructure/FlashMessageStore.cs',6,9)])
        rows.append(dict(evaluationId=item['evaluationId'],documentId=document_id,physicalField=field,judgement=judgement,originalPoints=item['originalPoints'],awardedPoints=item['originalPoints'] if judgement=='match' else 0 if judgement in ['missing','conflict'] else None,critical=False,criticalReason='ソースで確定した値/NULL/型/認証/確定に対する生成本文の矛盾は確定していない。未実装保証は保留し成功へ替えていない。',explanation=reason,generatedEvidence=generated,sourceEvidence=source,sourceFidelity='SOURCE_REFERENCE_ADJUDICATION_REQUIRED' if judgement=='hold' else 'SOURCE_FAITHFUL_UNOBSERVABLE_COMPONENT' if judgement=='unobservable' else 'NO_SOURCE_CONTRADICTION_ESTABLISHED',reference=dict(path='current-reference/'+item['currentSpecPath'],sha256=item['currentSpecSha256']),semanticReviewMethod='MANUAL_ITEM_LEVEL'))

assert len(rows)==113 and len({x['evaluationId'] for x in rows})==113
assert sum(x['originalPoints'] for x in rows)==127
for row in rows:
    row['reference']['version']=reference_versions[row['documentId']]
    row['generatedVersion']='1.0'
    row['criticalConstraint']=row['originalPoints']==1
    row['criticalFinding']=row['critical'] and row['judgement']=='conflict'
    row['criticalClassificationReason']='型/長さ/NULL/保存設定を含む属性一式は、値の損失・誤主体・競合等に直結し得る重要制約として検査。説明のみの欠落をcritical矛盾には置換しない。' if row['criticalConstraint'] else 'ヘッダーの文書内参照/表示書式は通常の文書品質条件。'
changed=[x['snapshotPath'] for x in MANIFEST['pins'] if hashlib.sha256((FROZEN/x['snapshotPath']).read_bytes()).hexdigest()!=x['sha256']]
assert not changed
counts=Counter(x['judgement'] for x in rows)
earned=sum(x['awardedPoints'] or 0 for x in rows)
pending=[x for x in rows if x['awardedPoints'] is None]
result=dict(schema='mvc-table-semantic-partial-evaluation/1',classification='EVALUATOR_ONLY',generatorMayRead=False,mode='training-assisted',evaluator='/root/evaluation_inventory',evaluatedAt=datetime.now(timezone.utc).isoformat(),generatedComponent='20261013-pilot-v3-tables',scope='seven physical table documents only',fullFormalMaximum=1408,selectedMaximum=127,selectedRows=113,confirmedAwardedPoints=earned,selectedConfirmedPointsRate=round(100*earned/127,4),completedSelectedScore=None if pending else earned,formalPercentage=None,status='PARTIAL_SEMANTIC_REVIEW_WITH_HOLDS' if pending else 'PARTIAL_SEMANTIC_REVIEW_COMPLETE',judgementCounts=dict(counts),unscoredRows=len(pending),unscoredPoints=sum(x['originalPoints'] for x in pending),criticalGeneratedConflicts=0,denominatorReduced=False,oldReportsReusedAsPasses=False,snapshotManifest='frozen-manifest.json',snapshotManifestSha256=hashlib.sha256((OUT/'frozen-manifest.json').read_bytes()).hexdigest(),numericInterpretation='Decimal integer length x.0 is interpreted semantically with explicitly stated signed integer type/range; Unicode business scalar limits remain separately required. This is not a byte/character substitution.',structuralFindings=[dict(document=table,issue='TABLE_HEADER_AND_NINE_COLUMN_TABLE_PROFILE_NOT_REPRODUCED',scoredSeparately=False) for table in REVIEWS],rows=rows,notPerformed=['Runtime SQL/HTTP/UI execution','HTML/PDF/Excel visual checks','Other 22 original evaluation documents','Formal 1408-point completion or 95 percent qualification','Source/reference hold adjudication'])
(OUT/'table-evaluation.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({k:v for k,v in result.items() if k not in ['rows','structuralFindings']},ensure_ascii=False))
