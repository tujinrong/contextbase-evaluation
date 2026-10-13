# Round4 SQL・DTO ソース対応メモ

2026-10-13。projectId `test-project1`／方式 `CSharp_ASPNET`。新しい Round4 本文と照合するために、この監査で原文を読み直した。過去のレビュー合格を再使用しない。全体規則 DOC-SPEC-RULES 7.2、DOC-MD-EXCEL 7.2、AG-REVERSE 7.1 とローカル AGENTS を使用する。

入力は `agents/reverse-agent/.tmp/20261013-tuning-01/capsules/CSharp_ASPNET-assisted/sources` 内の原文だけ。以下の根拠はそのディレクトリからの相対パス・1-based 行番号。参考設計本文・原仕様・spec-eval・採点期待値は読まず、原アプリ・SQL・DB を実行していない。18 ファイルの全文読取りと SHA は `source-pins-before.json`、FlashMessageStore全文とWebHostSetup 1-25行の補足読取りは `source-pins-supplement.json` に記録する。構造検査、画像確認、実行試験、正式採点の結果ではない。

## DB実体と保持状態

|対象|原文で確定した形・使用範囲|根拠|
|---|---|---|
|物理表|`m_student`, `m_class`, `m_code_category`, `m_code`, `t_operation_log`, `t_confirmation`, `t_runtime_state` の7表をDDLが定義する。DDLの存在とWeb経路での使用を区別する。|database/001_schema.sql:7-184|
|コード定義|`m_code` PKは `(category_id,code_value)`、categoryへのFKは `category_id`。classのgrade、studentのgender/prefecture/enrollment/relationshipは各category/codeの複合FK。|database/001_schema.sql:112-135,187-199|
|クラス所属|studentの`class_id`はNULL可でclassへのFK。年度・学年はstudentの独立列ではなく、classを通じた値。`m_class`は`school_year`と`grade_category/grade_code`を持つ。|database/001_schema.sql:28,62-88,190-191; Core/SqlServerStudentService.cs:82-91,187-194|
|FKのない表|operation_logのtarget_table/target_key、confirmationのtarget_id、runtime_stateの各識別値には、このDDLでFKを定義していない。検索JOINをFKに転記しない。|database/001_schema.sql:137-184,187-195|
|Web確認状態|`_webTokens`のWeb経路は静的`ConcurrentDictionary<string,Confirmation>`。所有者、学生ID/版、payload/candidate hash、期限、Busyを保持する。DB `t_confirmation`読取・発行・消費は`!_webTokens`側。|Core/SqlServerStudentService.cs:19-29,276-290,308-314,330-342|
|検索・編集状態|`SearchContextStore.Entry`はprocess memoryでApplied/LastResult/Gate/所有者・session・tab・期限・revisionを保持。EditorSnapshotStoreは別のprocess memoryでOriginalのJSON clone、Detail等を30分保持。これらを`dbo.t_runtime_state`への保存と説明しない。|Infrastructure/SearchContextStore.cs:7-15; Infrastructure/EditorSnapshotStore.cs:5-11|
|Web登録とFlash|DIは3状態storeをSingleton、IStudentServiceをScopedとして`webTokens:true`を指定する。Flashは別memory辞書、主体/session/contextキー、10分期限、Takeで削除する。|Infrastructure/WebHostSetup.cs:13,19; Infrastructure/FlashMessageStore.cs:4-9|

## UI → DTO → 正規化 → DBの対応

|項目|要求・型と保存/参照経路|根拠|
|---|---|---|
|学籍番号|Search `StudentNo`、editor `StudentNo` → `student_no`。raw/saved15 scalar、Trim→NFKC→大文字、英数字/ハイフン。検索はprefix LIKE、保存新規時書込み、既存値変更は拒否してUPDATE列から除外。論理削除済みも番号重複検査対象。|Web/Inputs/StudentSearchInput.cs:7,19-22; Web/Inputs/StudentSaveInput.cs:9,34-42; Core/StudentNormalizer.cs:59-64,124; Core/SqlServerStudentService.cs:113,140,254,264-266,294-297|
|氏名|Search Name→StudentName、editor StudentName→student_name。raw/saved8 scalar、Trim、元氏名にNFKC/大文字化なし。derived name_keyだけNFKC/大文字化/全空白除去、最大160 scalar。検索はkeyのcontains LIKE。|Core/StudentNormalizer.cs:47-70,125,144; Core/SqlServerStudentService.cs:114-115,141; Web/Inputs/StudentSearchInput.cs:19|
|氏名カナ|Search Kana→StudentNameKana、editor同名→student_name_kana。raw36、NFKC・ひらがなからカタカナ・連続空白整理、saved18 scalar。kana_keyは半角空白除去。検索はkeyのcontains LIKE。|Core/StudentNormalizer.cs:72-85,126,145; Core/SqlServerStudentService.cs:116,142|
|和暦生年月日|4成分BirthDateInputから`DateOnly`→birth_date。DBからdetailはToInput、一覧はToWareki。成分を物理列やDB和暦文字列と説明しない。|Web/Inputs/StudentSaveInput.cs:12,36,48; Core/Contracts.cs:8,50-60; Core/JapaneseDateService.cs:17-50; Core/StudentNormalizer.cs:127; Core/SqlServerStudentService.cs:188,194|
|性別・都道府県・在籍・続柄|string code→gender_code/prefecture_code/enrollment_status_code/relationship_code、width1/2/2/2。固定category3列はINSERT literal、relationship_categoryはcodeがNULLならNULL、他はRELATIONSHIP。code/categoryの存在、有効状態・期間をCheckRulesで検査し、既存と同値のcodeは停止/期間外を保持できる。|Core/StudentNormalizer.cs:113-117,128-130,136,140,146-147; Core/SqlServerStudentService.cs:296,344-356|
|郵便・電話|postal raw10→NFKC・空白/hyphen除去→ASCII7桁。phone raw20→NFKC・空白/hyphen/括弧除去→国内10/11桁又は+国際。本人/緊急電話をvarchar16で保存。Search phoneは両列の完全一致ORで、メールは電話検索対象でない。|Core/StudentNormalizer.cs:87-101,129,133,141; Core/SqlServerStudentService.cs:33-37,117,148|
|住所・メール|address_line1/2 raw/saved45 scalar、Trim、1必須2任意。email raw/saved60、ASCII形式検査、domainのみ小文字。NULL/empty textは任意ならNULL。|Core/StudentNormalizer.cs:47-58,102-111,131-134; Core/SqlServerStudentService.cs:34-35|
|入学日・終了日|`string`/`string?`からParseIsoでDateOnly→Date parameter→date。終了日NULL/emptyはNULL、入力空白はParseIsoに渡す。西暦復元はyyyy-MM-dd。学籍区分01/02はendNULL+class必須、03/04はend必須かつadmission以上。NULL例外詳細は別監査対象。|Core/StudentNormalizer.cs:135-138,148-154; Core/SqlServerStudentService.cs:69-72,190-191; database/001_schema.sql:198|
|年度・学年・クラス|SchoolYear `int?`、GradeCode `string?`は照合/候補用でstudentの追加列として保存しない。ClassIdはWeb decimal string→正のInt64?→class_id。class候補一致、期間・有効性・新規占席時capacityをCheckRulesで検査する。|Web/Inputs/StudentSaveInput.cs:23,28-29,40-42,53,57-60; Core/SqlServerStudentService.cs:357-380|
|緊急連絡先・備考|emergency name8、optional relationship2、phone20→16、remarks120 scalar・multiline正規化。緊急3値は全NULL又は全設定、本人電話/email/緊急電話のいずれか1値が必要。|Core/StudentNormalizer.cs:139-142,155-158|
|変更・削除理由|OperationReasonはStudentDraftの列ではなくSaveRequest.Reason→Text60 multiline→operation_log.operation_reason。DeleteReasonは別要求Reason→必須Text60 multiline→student.delete_reasonとaudit reason。|Web/Inputs/StudentSaveInput.cs:32,42; Web/Inputs/StudentDeleteInput.cs:4; Core/SqlServerStudentService.cs:234,385-389,395-413|
|表示項目|検索住所はprefecture code_name（欠落なら[不整合]）+address_line1だけ。address_line2は表示に加算しない。出生はToWareki、更新日時はUTC+9書式、class/grade/statusはRowSelect LEFT JOINの別名からDTO、JSON、Viewへ移す。|Core/SqlServerStudentService.cs:77-91; Infrastructure/WebPresentation.cs:7,20; Views/Students/Search.cshtml:8|
|技術状態|ID/rowVersionのWeb境界はdecimal string、内部/SQLはInt64/bigint。ExpectedVersion、Snapshot/ReturnContext/DuplicateToken/CSRFは業務列とは別。StudentDetail/StudentRow/LookupSet/NormalizedStudentを物理表としない。|Core/Contracts.cs:3,50-70; Web/Inputs/StudentSaveInput.cs:30-42,54,57-60; Views/Students/Edit.cshtml:5; Core/StudentNormalizer.cs:11-15|

HTML maxlengthはUTF-16 control上限でサービスraw scalar上限と異なる（Search:30/16/72/40、editor:30/16/72/20/90/40/120/240等）。保存容量と混同しない。View根拠は `Views/Students/Search.cshtml:5` と `Views/Students/Edit.cshtml:6-13`。

## SQLバインド・検索境界

`Core/SqlServerStudentService.cs:30-38`の固定Columnsはvarchar15/1/7/2/16/60/24等、nvarchar16/36/320/90/240を指定する。nvarchar容量はUTF-16格納幅で、サービスとDDL scalar CHECKの8/18/160/45/120を倍量へ書き換えない。`database/001_schema.sql:9-59`。ParamはSqlDbTypeを明示し、DateOnlyだけDateTime midnightへ変換、NULLはDBNull.Value、size非0だけSizeを設定する（service:65-73）。

SearchはSnapshot transactionで件数とページを読み、COUNT TOP10001で10000超ならrowsなし・LimitExceeded true、通常は末尾ページへclipして固定tie-breaker student_id ASCを加え、ReadOnly結果でもCommitする。サービス戻り値はNoChange。JOINのactive/periodは検索抽出条件ではない。`service:103-171`。

LIKE値はEscapeLike(!,% ,_,[)を適用し、no prefix varchar31、name contains nvarchar642、kana contains nvarchar74。yearSmallInt、grade/prefecture/statusVarChar2、classBigInt、phoneVarChar16、from/toDate、offset/sizeInt。入力をSQL識別子へ挿入せずsortキー4種と方向2種を検査する。`service:107-108,137-164; normalizer:161`。

Lookupは別Snapshot transaction、codeとcategory INNER JOINでis_activeをAND合成、classはgradeLEFT JOINにより順序だけに使用、server editor/includeOccupancy=trueのみstudentの占席数をCOUNT。searchはfalseでoccupied=0。全候補取得後のView条件とWebPresentation.Lookups helperを区別する。`service:196-216; controller:39; coordinator:16-17; presentation:8-18; Views/Students/Edit.cshtml:8-13`。

## 保存・確定・取消・結果不明

1. SaveはViewer拒否、Normalize/理由/要求ID版/年度/学年検査が先。OpenとBegin ReadCommittedは後段tryの外。Gateはtransaction所有Exclusive sp_getapplock、LockTimeout5000、command timeout30。`service:65-66,92-101,227-244`。
2. 既存load/版一致/学籍番号不可変/終了区分訂正権限・理由→CheckRules→差分なしなら明示Rollback→版上限→全行番号重複→active学生のbirth+name_key OR kana_key候補照合→token照合。`service:245-286`。
3. 重複/不正token時はstudent transactionをRollbackしてから確認状態発行。Webはmemorytoken、非Webは別transactionにt_confirmation INSERT/Commit。表示は最大20、候補hashは全候補のID/版。候補0でもsuppliedtoken不正ならConfirmationRequiredになり得る。`service:224-225,287-290,330-342`。
4. INSERTは全normalized writeColumnsに固定category・is_deleted0・created/updatedUTC主体・row_version1、UPDATEはstudent_no除外の全normalized列をSETしてupdatedと版+1。UPDATE件数/取得idなしはDBConcurrencyException。changed-onlyの列SETとは説明しない。`service:292-306`。
5. auditは同一transactionで必須。INSERT changed_columnsは全insert+metadata、UPDATEは実差分+updated/版。非Web確認consumeも同一transactionで1件必須。commitAttempted=true→Commit完了→completed=true→memorytoken削除→Saved。`service:306-315,385-390`。
6. InputValidation、unique2601/2627、DBConcurrencyは各専用catch→Rollback helper→各ValidationFailed/Conflict。一般SqlException/InvalidOperationException/OperationCanceledExceptionでは`unknown = writeStarted && (commitAttempted || !rolledBack)`、UnknownならWebtoken除去、SystemErrorなら再使用可能なclaimed Busyをfinally解除。Rollback helperはCancellationToken.None、SqlException/InvalidOperationExceptionだけfalse。`service:316-329`。
7. DeleteはAdministrator/必須理由/正ID版（long.Max拒否）→Open/Begin try外→Gate→active行版照合→論理削除7列更新→audit DELETE→Commit。NoChange系の保存ではない。一般例外のUnknown式は同じ。`service:392-416`。

SystemErrorとUnknownはどちらもHTTP503だが確定状態を区別し、Unknownに「確実にロールバック済み」「再送してよい」と書かない。HTTPのSaved枝はservice200を直接返すのでなくControllerからFlash+303 Search return、NoChangeはEdit200。`Infrastructure/WebPresentation.cs:23-30; Web/Controllers/StudentsController.cs:31-38`。

## 未確認

現在はRound4本文が未出力。上記は原文対応表であり新稿合否ではない。原本実行、DB接続、HTTP/model binder、トランザクションの実動作、視覚確認、正式採点、参考設計意図との比較は未実施。画像は親監査が別記録する。
