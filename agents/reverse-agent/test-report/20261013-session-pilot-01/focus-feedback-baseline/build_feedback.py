"""Build generator-safe source observations; no reference/checklist input."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib, json

R=Path(__file__).resolve()
while not (R/'test-project1/srcs/CSharp_ASPNET').is_dir(): R=R.parent
O=Path(__file__).resolve().parent
C=R/'agents/reverse-agent/.tmp/20261013-tuning-01/capsules/CSharp_ASPNET-assisted'
M=json.loads((C/'manifest.json').read_text(encoding='utf-8'))
G=R/'test-project1/spec-analysis/CSharp_ASPNET/20261013-pilot-v2-r2/spec/detail'
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
source_pins={x['path']:x for x in M['files']}
for p,entry in source_pins.items(): assert sha(C/'sources'/p)==entry['sha256']
def refs(*entries):
    result=[]
    for path,a,b in entries:
        assert path in source_pins
        lines=(C/'sources'/path).read_text(encoding='utf-8-sig').splitlines()
        assert 1<=a<=b<=len(lines)
        result.append(dict(path='sources/'+path,startLine=a,endLine=b,sha256=source_pins[path]['sha256']))
    return result
def generated(name,*ranges):
    p=G/name; lines=p.read_text(encoding='utf-8-sig').splitlines()
    result=[]
    for a,b in ranges:
        assert 1<=a<=b<=len(lines)
        result.append(dict(path='spec/detail/'+name,startLine=a,endLine=b,sha256=sha(p)))
    return result
def finding(i,title,issue,direction,sources,locations,severity='major'):
    return dict(id=i,severity=severity,title=title,sourceBackedIssue=issue,revisionDirection=direction,sourceReferences=sources,generatedLocations=locations)
def preserve(i,title,behavior,sources,locations):
    return dict(id=i,title=title,observedBehavior=behavior,revisionInstruction='この分岐・範囲・条件を新稿にも保持する。現行実装と異なる意図を扱う場合は、現行動作と明確に分ける。',sourceReferences=sources,generatedLocations=locations)

search_findings=[
finding('SEARCH-FIELD-TRACE','UI入力から実列とSQLバインドまでの直接対応',
 '入力表・移送表・WHERE表の正しい情報が分散し、項目を起点に受信型/正規化/実DB型/DB NULL/述語/バインドを一巡して確認しにくい。DTO nullable、LEFT JOINによるNULL、入力未指定、元列のNULL許可を別々に扱う必要がある。',
 '各検索フォーム項目をキーとして、フォーム名→StudentSearchInput→SearchCriteria→正規化値→実列のDDL型/容量/NULL→述語/パラメーター名/SqlDbType/Size→未指定時の動作をfactと本文に対応付ける。氏名はname_key nvarchar(320) NOT NULLと@name NVarChar(642)、電話は2つのvarchar(16) NULL列と同じ@phone、年度はm_class.school_year smallint NOT NULLと任意条件int?を区別する。未所属はclass_id IS NULLで専用パラメーターなし。',
 refs(('Web/Inputs/StudentSearchInput.cs',7,22),('Core/SqlServerStudentService.cs',113,154),('database/001_schema.sql',9,32),('database/001_schema.sql',64,71)),
 generated('student-search.md',(104,115),(164,179),(665,679))),
finding('SEARCH-DISPLAY-TRACE','一覧表示の取得元・長さ・NULL・整形を結ぶ',
 '一覧の取得元とDTOは詳述されるが、表示項目ごとの業務スカラー上限、実DB型、元列のNULL、結合欠落のNULLとRazor表示の対応が一箇所で完結しない。',
 'RowSelect→Row→StudentRow→Razorの実使用経路を表示項目別に示す。クラス名はnvarchar(36)とCHECK18スカラー、コード名称はnvarchar(24)とCHECK12スカラーを分ける。LEFT JOINでNULLになる所属/名称を元列のNOT NULLと混同しない。住所は都道府県名称と住所1であり、住所2・緊急電話等を勝手に追加しない。使われない表示helperを公開JSON応答と扱わない。',
 refs(('Core/SqlServerStudentService.cs',74,91),('Core/Contracts.cs',50,58),('Views/Students/Search.cshtml',7,8),('database/001_schema.sql',64,81),('database/001_schema.sql',115,128)),
 generated('student-search.md',(161,179))),
finding('SEARCH-STATE-COMPARISON','操作ごとの保持・版・失敗応答を比較する',
 '共通保持契約をイベント各章で反復しているため、Search/Page/Options/Resume/Clearの固有差を横断しにくい。',
 '共通のEntry/所有者/セッション/期限/Gateを一箇所へ整理し、各イベントは「今回入力の取得元・結果の取得元・版照合・版更新・期限延長・失敗時画面」を比較できる表と固有手順にする。OptionsのGate不使用、ResumeのApplied.Page未補正、状態確定後の候補取得失敗を省略しない。',
 refs(('Web/Controllers/StudentsController.cs',8,22),('Infrastructure/WebStudentCoordinator.cs',7,15),('Infrastructure/SearchContextStore.cs',9,15)),
 generated('student-search.md',(24,47),(232,397),(439,483)),severity='minor'),
finding('SEARCH-LAYOUT-STATES','状態・権限の成立する静的画面例',
 '静的図は主に未検索Viewerの例であり、主要結果状態と非Viewer操作の位置/活性は文章から追う必要がある。',
 '原ソースの条件で成立する未検索/0件/上限超過/取得あり、およびViewer/非Viewerの差を、独立した静的状態例か状態枠として示す。_Layoutとsite.cssを含め、架空の学生値や実行成功を追加しない。静的再構成と実機撮影を区別する。',
 refs(('Views/Shared/_Layout.cshtml',1,1),('Views/Students/Search.cshtml',3,8),('wwwroot/css/site.css',1,1)),
 generated('student-search.md',(49,98),(800,814)),severity='minor'),
finding('SEARCH-OBSERVED-BOUNDARIES','設計意図・未接続helper・現行動作の境界',
 '内部PresentオブジェクトとRazorの画面契約、宣言だけのhelperと実際の公開入口は区別済みである。この区別を章の責務説明でも維持し、未実装の表示値や操作を現行応答へ混ぜない。',
 '実装のPresentにはoutcome/totalCount/items/page等があるがRangeFrom/RangeToはない。実際のOptionsはController内の再描画でありCoordinator.Options/Lookupsの公開APIではない。引用する設計意図は出所と未実装/差分を明示し、ソース説明の章で実装保証へ置換しない。試験項目を書く場合も予定/観点と実行結果を区別する。',
 refs(('Infrastructure/WebStudentCoordinator.cs',16,21),('Web/Controllers/StudentsController.cs',22,22),('Views/Students/Search.cshtml',7,8)),
 generated('student-search.md',(22,26),(178,179)),severity='minor'),
]
search_preserve=[
preserve('SEARCH-CURRENT-APPLIED','入力中条件と最後の成功条件を分ける',
 '今回入力はフォーム/要求/Criteriaにあり、EntryにDraft領域はない。SearchはEnsureSearch後にAppliedを複製しLastResultとRevisionを更新する。PageはAppliedの複製を使うため未検索のブラウザー変更を採用しない。',
 refs(('Web/Controllers/StudentsController.cs',13,22),('Infrastructure/WebStudentCoordinator.cs',7,12),('Infrastructure/SearchContextStore.cs',9,15)),
 generated('student-search.md',(24,47),(232,295),(343,397))),
preserve('SEARCH-OPTIONS-NO-GATE','Optionsは一覧の再検索・確定をしない',
 '公開POST optionsは今回条件を再表示し、LastResultを材料にする。ContextRevisionを受信してもUse/Gateによる照合・版更新・期限延長を行わない。未所属で3所属条件を解除し、不適合クラスを解除する。',
 refs(('Web/Controllers/StudentsController.cs',22,22),('Infrastructure/SearchContextStore.cs',13,14)),
 generated('student-search.md',(297,341))),
preserve('SEARCH-PAGE-RESUME','Page補正とResumeの差を保持する',
 'Pageは件数/並び指定が変わればPage=1、成功後にAppliedを更新し、必要なら最終ページ補正後に再検索する。ResumeはAppliedで再検索しLastResult/Revisionを更新するがApplied.Pageを補正しない。AppliedなしのResumeは未検索表示で版を増やさない。',
 refs(('Infrastructure/WebStudentCoordinator.cs',11,14)),
 generated('student-search.md',(343,397),(439,483))),
preserve('SEARCH-SNAPSHOT-LIMIT','検索件数と一覧のDB範囲',
 'SearchAsyncの件数と一覧は同じSNAPSHOT内で、TOP10001により上限超過を検出し、超過時は一覧を取得しない。件数10001は全件数確定値ではない。並びは固定4キー/2方向とstudent_id ASCで、20/50/100件を取得する。画面候補のLookupは別接続/別トランザクションである。',
 refs(('Core/SqlServerStudentService.cs',107,108),('Core/SqlServerStudentService.cs',123,168),('Core/SqlServerStudentService.cs',197,216),('Web/Controllers/StudentsController.cs',39,39)),
 generated('student-search.md',(287,295),(639,732))),
preserve('SEARCH-LOCAL-FAILURES','失敗応答と保持済結果は同じ状態ではない',
 '局所WebFault時のSearch/Page応答はPresent(entry,null)で空の結果材料になるがLastResultを削除しない。後のOptionsが最後の成功一覧を表示し得る。Search成功後のLookup/画面変換失敗に合わせてメモリ確定を戻す補償はない。',
 refs(('Web/Controllers/StudentsController.cs',14,22),('Infrastructure/WebStudentCoordinator.cs',9,12)),
 generated('student-search.md',(295,295),(341,341))),
preserve('SEARCH-OWNER-TAB','所有・セッション・Tab照合の実適用範囲',
 'Getは所有者/セッション/期限を確認し、Tab引数が非空の場合だけTabを比較する。IndexのResumeとCheckReturn/Loadの復帰版取得はTabを指定しない。全入口でTabまで常時照合すると記載しない。',
 refs(('Infrastructure/SearchContextStore.cs',13,14),('Web/Controllers/StudentsController.cs',8,11),('Web/Controllers/StudentsController.cs',25,25),('Infrastructure/WebStudentCoordinator.cs',6,6)),
 generated('student-search.md',(138,157))),
preserve('SEARCH-MEMORY-LOOKUP','検索状態と参考人数の保存先',
 'Entryはプロセス内辞書でありDB状態表へのCRUDではない。SearchModelはLookupAsync(false)を呼び、Occupiedに定数0を返す。検索候補0が実占有人数0を意味しない。',
 refs(('Infrastructure/SearchContextStore.cs',9,12),('Web/Controllers/StudentsController.cs',39,39),('Core/SqlServerStudentService.cs',196,214)),
 generated('student-search.md',(26,47),(132,136))),
preserve('SEARCH-EXACT-STATUS-VALUES','在籍配列は一般Code正規化と異なる',
 'SearchAsyncは在籍配列の長さ・Ordinal重複・01～04の値をそのまま検査する。Grade/PrefectureのCode呼出しとは別で、配列にNFKC/Trimを自動適用しない。',
 refs(('Core/SqlServerStudentService.cs',111,119)),
 generated('student-search.md',(111,111),(135,135))),
]

editor_findings=[
finding('EDITOR-FIELD-BIND','各業務入力・派生値・制御値の保存経路',
 '主要19入力の移送/物理型は既に詳述されるが、Columnsに従う総括と別表を往復し、UIから実パラメーター名/SqlDbType/Size/NULLへの直接対応を追いにくい。',
 '19入力と派生name_key/kana_key/relationship_categoryを項目キーでColumns/Paramへつなぐ。@列名、実SqlDbType/Size、DateOnly→午前0時DateTime→Date、null→DBNullを示す。年度/学年は学生保存列を作らずクラス整合照合に使う。OperationReasonは監査@reason、削除Reasonはdelete_reasonと監査理由であり、同じ保存項目と扱わない。',
 refs(('Web/Inputs/StudentSaveInput.cs',9,42),('Core/StudentNormalizer.cs',124,147),('Core/SqlServerStudentService.cs',30,37),('Core/SqlServerStudentService.cs',67,72),('Core/SqlServerStudentService.cs',294,307),('Core/SqlServerStudentService.cs',385,410)),
 generated('student-editor.md',(90,123),(138,186),(476,484))),
finding('EDITOR-DATE-UNITS','元号入力と正規化後の桁数・日付バインド',
 '元号原入力、HTML maxlength、FormKC後のNumber検査、内部DateOnlyと物理dateの各層を分けて一巡できる説明が不足する。氏名の原表記と照合キー生成の上限も別層である。',
 '生年月日のEraはID完全一致、Year/Month/DayはFormKC後にNumberが4/2/2コード単位以内のASCII正数を検査し、Yearの元を1として扱う。HTMLのmaxlength4/2/2と同じ検査時点だと決め付けない。元号境界・業務日・逆変換一致、dateの非時点性とDateバインドをつなぐ。氏名の8スカラー原表記とNameKey160スカラー/nvarchar320を区別する。',
 refs(('Views/Students/Edit.cshtml',6,7),('Core/JapaneseDateService.cs',17,39),('Core/StudentNormalizer.cs',37,70),('Core/SqlServerStudentService.cs',67,76),('database/001_schema.sql',10,14)),
 generated('student-editor.md',(92,94),(142,145),(856,860))),
finding('EDITOR-MANAGEMENT-FIELDS','候補・管理表示を実列と算出値へ対応付ける',
 '学生ID/更新表示、年度/学年/定員/参考人数の元列属性と、DTO nullable/表示未設定/算出値を同じ表で区別しにくい。',
 '学生ID bigint IDENTITY、更新日時datetimeoffset(7)、更新者nvarchar128/CHECK64、クラス年度smallint NOT NULL、学年varchar2 NOT NULL、定員int NULLと実値取得を明示する。Occupiedは非削除かつ01/02学生数の副問合せでm_classの保存列ではない。NULL定員の上限比較省略と表示文字列、LEFT JOIN由来NULLを分ける。',
 refs(('database/001_schema.sql',8,8),('database/001_schema.sql',40,41),('database/001_schema.sql',64,84),('Core/SqlServerStudentService.cs',196,214),('Core/SqlServerStudentService.cs',357,383),('Views/Students/Edit.cshtml',4,12)),
 generated('student-editor.md',(90,115),(257,257),(470,484))),
finding('EDITOR-STATIC-LAYOUT','共通ヘッダー・適用CSS・単一成立モード',
 '静的再構成は_Layoutのヘッダーを落とし、新規基準図に既存再読込/管理者削除/確認を合成する。候補表の実CSSによる最小幅が再現されず、狭幅で収まるように見える。',
 '共通_Layoutを含め、標準図を成立する1モードに限定し他モードを独立例にする。候補sectionはrole=dialogかつclass=warningであり、CSSの.dialog classとは別なので.dialog tableの規則を勝手に適用しない。実tableのmin-width1050px・padding・font-size・背景を保持し、ソースにないモーダル/スクロール枠で補修しない。静的素材と実画面撮影を区別する。',
 refs(('Views/Shared/_Layout.cshtml',1,1),('Views/Students/Edit.cshtml',3,17),('Web/Models/StudentEditPageModel.cs',5,14),('wwwroot/css/site.css',1,1)),
 generated('student-editor.md',(41,84))),
finding('EDITOR-OPERATION-COMPARISON','共通Lookupとイベント固有の確定/保持',
 '読込/取消/再読込/検索復帰ごとの共通Lookup図が反復され、保存/削除/確認の固有分岐を追いにくい。',
 '共通Lookup・保持領域・受付/エラーを一箇所へ整理し、各イベントに対象/入力取得元/版/SQL全述語/確定取消/失敗時保持の固有差を残す。NoChange、確認待ち、Saved、Unknownを同じ成功としてまとめない。試験観点はソース分岐から提示し、実行結果や未接続意図の実装達成を創作しない。',
 refs(('Web/Controllers/StudentsController.cs',23,38),('Infrastructure/WebStudentCoordinator.cs',17,19),('Core/SqlServerStudentService.cs',196,216),('Core/SqlServerStudentService.cs',227,323),('Core/SqlServerStudentService.cs',392,416)),
 generated('student-editor.md',(205,322),(658,849)),severity='minor'),
]
editor_preserve=[
preserve('EDITOR-SAVE-DELETE-FAILURE','保存失敗のInput保持と削除失敗のLoadを分ける',
 '保存結果がSaved以外なら投稿Inputを再表示し、Snapshot.Detail/元Snapshot/復帰版を使ってLookupを再取得する。削除結果がSaved以外なら通常Loadへ戻り、最新Detail/新Snapshotを作る。削除Reasonは空textareaで、投稿理由や編集中Inputを復元しない。Loadが対象なしになれば共通404へ変わり得る。',
 refs(('Web/Controllers/StudentsController.cs',25,37),('Infrastructure/WebStudentCoordinator.cs',17,19),('Views/Students/Edit.cshtml',17,17)),
 generated('student-editor.md',(488,508),(652,656))),
preserve('EDITOR-TOKEN-RECONFIRM','確認照合・再発行・候補全体',
 '稼働Web登録はwebTokens:true。確認は主体/セッション/対象ID/期待版/期限/19業務入力ハッシュ/全候補ID版ハッシュ/Busyの獲得で照合する。現在対象の版競合とNoChangeは確認照合より前に返り得る。無効確認で候補あり又は非NULLキーなら学生Txをrollbackして再発行し、候補全件数と最大20件表示を分ける。',
 refs(('Infrastructure/WebHostSetup.cs',19,19),('Core/SqlServerStudentService.cs',19,29),('Core/SqlServerStudentService.cs',224,225),('Core/SqlServerStudentService.cs',252,290)),
 generated('student-editor.md',(516,581))),
preserve('EDITOR-TOKEN-LIFECYCLE','ブラウザー取消・サーバーキー・確定後処理',
 '編集inputと確認取消はブラウザーのDuplicateTokenを消すが、サーバー辞書の古いキーをその場で削除しない。Webキーは32バイト乱数hex・入口時点+10分、Saved/Unknownで除去し、確定/結果不明以外の失敗でclaimed Busyを解放する。DB確認表分岐は別で、消費UPDATEは学生保存と同一Txで行う。万能な再送冪等性を保証しない。',
 refs(('wwwroot/js/site.js',3,6),('Core/SqlServerStudentService.cs',308,342)),
 generated('student-editor.md',(516,581),(937,937))),
preserve('EDITOR-CONFIRM-SCOPE','確認とSnapshot/検索復帰の識別を分ける',
 'Confirmation自体の保持要素にSnapshotId/検索Context/Tabはない。編集Snapshotと送信復帰先はControllerで別途照合する。周辺照合を確認キー自体の全識別結合と同じ保証にしない。',
 refs(('Core/SqlServerStudentService.cs',19,29),('Core/SqlServerStudentService.cs',278,283),('Web/Controllers/StudentsController.cs',29,29),('Infrastructure/EditorSnapshotStore.cs',7,10)),
 generated('student-editor.md',(516,581),(937,937))),
preserve('EDITOR-COMMIT-UNKNOWN','確定単位と結果不明を保持する',
 '保存/論理削除は比較版付き学生更新と監査を同じTxで確定し、正常Commit後だけSavedとなる。NoChangeはrollbackしてDML/監査/管理値増加を行わない。捕捉対象例外ではwriteStarted&&(commitAttempted||!rolledBack)がUnknownで、Commit試行後の例外を後続rollback成功で取消確定にしない。Open/Beginは分類tryの外にある。',
 refs(('Core/SqlServerStudentService.cs',240,263),('Core/SqlServerStudentService.cs',294,323),('Core/SqlServerStudentService.cs',392,416)),
 generated('student-editor.md',(488,508),(646,656))),
preserve('EDITOR-SNAPSHOT-RELOAD','取消と最新再読込の取得元',
 'ResetはSnapshot.OriginalのJSON複製へ戻す。全項目空でもDB最新でもなく、読込時の期待版を保持する。最新再読込はLoad/GetAsyncで新しいDetail/期待版/Snapshotを取得する。Snapshotはプロセス内辞書、所有者/セッション/対象/30分期限を確認する。',
 refs(('Web/Controllers/StudentsController.cs',25,35),('Infrastructure/EditorSnapshotStore.cs',7,11),('Core/SqlServerStudentService.cs',172,194),('Web/Inputs/StudentSaveInput.cs',44,54)),
 generated('student-editor.md',(658,768))),
preserve('EDITOR-POSTAL-RAW','郵便保存と読込表示の実動作',
 'Postalは原入力10スカラー、FormKC/指定空白ハイフン除去後ASCII7桁で保存する。DetailとStudentSaveInput.Fromは保存済み文字列をそのまま復元し、現在のinputに3桁-4桁表示整形はない。表示整形を新しい実装動作として創作しない。',
 refs(('Core/StudentNormalizer.cs',95,100),('Core/SqlServerStudentService.cs',185,190),('Web/Inputs/StudentSaveInput.cs',49,49),('Views/Students/Edit.cshtml',9,9)),
 generated('student-editor.md',(96,96),(147,147))),
preserve('EDITOR-OUTPUT-AND-INPUT','学生19業務値と管理/理由/候補を分ける',
 '管理ID/版/認証者/時点は任意の通常入力ではなく、版は正ASCII Int64として検査する。年度/学年は保存列を増やさずクラス整合に使用する。OperationReasonと削除Reasonは別フォーム/要求で、論理削除は編集中の19業務値を保存しない。',
 refs(('Web/Inputs/StudentSaveInput.cs',28,60),('Infrastructure/WebStudentCoordinator.cs',18,19),('Core/SqlServerStudentService.cs',234,237),('Core/SqlServerStudentService.cs',409,413),('Views/Students/Edit.cshtml',17,17)),
 generated('student-editor.md',(175,186),(387,402),(648,656))),
preserve('EDITOR-REAL-ENTRYPOINT','MVC入口と表示helperを混同しない',
 '保存/削除はMVCフォーム経路で、Savedは303 Locationへ進む。WebPresentation.Saveの宣言を実際の公開JSON保存応答としない。ブラウザーsubmitの他ボタン無効化やDirty警告をサーバー冪等処理と扱わない。',
 refs(('Web/Controllers/StudentsController.cs',26,38),('Infrastructure/WebPresentation.cs',30,30),('wwwroot/js/site.js',2,6)),
 generated('student-editor.md',(387,508),(935,937))),
]

documents=[]
for doc_id,name,findings,correct in [('SM-DET-STUDENT-SEARCH','student-search.md',search_findings,search_preserve),('SM-DET-STUDENT-EDITOR','student-editor.md',editor_findings,editor_preserve)]:
    expected_hash={'student-search.md':'22493127df161fb44c518bf03e52eae6fd9887168b2ab4be2eaeabfdcf5de4bc','student-editor.md':'1a6bacdaaccced64295e119c43c3a1b1c603beb5e775c34c692ff5de2b48e22d'}[name]
    assert sha(G/name)==expected_hash
    src_paths=sorted({x['path'][len('sources/'):] for block in findings+correct for x in block['sourceReferences']})
    payload=dict(schema='source-backed-writer-feedback/1',classification='GENERATOR_SAFE_SOURCE_FEEDBACK',reviewDocumentId=doc_id,createdAt=datetime.now(timezone.utc).isoformat(),reviewer='/root/evaluation_inventory',projectId='test-project1',profile='CSharp_ASPNET',mode='training-assisted',scope='student-search-and-student-editor-only',sourceBackedOnly=True,provenance=dict(sourceCapsuleManifestPath=(C/'manifest.json').relative_to(R).as_posix(),sourceCapsuleManifestSha256=sha(C/'manifest.json'),generatedDocumentPath=(G/name).relative_to(R).as_posix(),generatedDocumentSha256=sha(G/name),generatedDocumentVersion='1.0',generatedComponent='20261013-pilot-v2-r2',sourceFiles=[dict(path='sources/'+p,sha256=source_pins[p]['sha256'],bytes=source_pins[p]['bytes']) for p in src_paths]),sourceBackedFindings=findings,existingCorrectBehaviors=correct,revisionBoundary=['新稿は新しいAI解析・執筆・独立レビューで作る。既存本文の機械置換を新しいAI執筆と扱わない。','現行ソースで確認した事実と利用者が許可した設計意図を区別する。未実装方針・実行成功・追加機能を創作しない。','実使用経路を閉包で追い、宣言だけのhelperを稼働入口と扱わない。','ここにない欠落を全て補完済と解釈しない。今回の指摘はソースに根拠を持つ書き直し材料。'],notPerformed=['Application startup','SQL Server execution','Concurrency execution tests'])
    text=json.dumps(payload,ensure_ascii=False,indent=2)+'\n'
    for forbidden in ['spec-eval','evaluator-only','originalCells','evaluationId','confirmedAwardedPoints','formalMaximum','minimumFor95']:
        assert forbidden not in text, forbidden
    out=O/(name.replace('.md','-feedback.json'));out.write_text(text,encoding='utf-8')
    documents.append(dict(reviewDocumentId=doc_id,path=out.name,sha256=sha(out),findings=len(findings),preservedBehaviors=len(correct),sourceFiles=len(src_paths)))
manifest=dict(schema='generator-safe-feedback-manifest/1',classification='GENERATOR_SAFE_SOURCE_FEEDBACK',createdAt=datetime.now(timezone.utc).isoformat(),reviewer='/root/evaluation_inventory',sourceCapsuleManifestSha256=sha(C/'manifest.json'),sourceBytesModified=False,generatedBytesModified=False,documents=documents,sourceReferenceRangesValidated=True,generatedReferenceRangesValidated=True)
(O/'feedback-manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps(manifest,ensure_ascii=False))
