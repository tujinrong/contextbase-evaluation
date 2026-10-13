# Round 4 editor evaluator assembly

All judgements and targeted meanings below were manually authored from this new document, the 161 original selected rows and current frozen source. Code binds mechanical identities/evidence only.

~~~python
from pathlib import Path
import hashlib,json,collections,datetime
B=Path('agents/reverse-agent/test-report/20261013-session-pilot-01/evaluator-only/focus-round-04')
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
original=[r for r in json.loads((B/'selected-rows.json').read_text(encoding='utf-8')) if r['documentId']=='DET-CSharp_ASPNET-SCR-STU-002']
G='frozen/generated/spec/detail/student-editor.md'
R='frozen/current-reference/test-project1/srcs/CSharp_ASPNET/spec/詳細仕様書/CSharp_ASPNET/02_学生登録画面.md'
C='frozen/evaluation/test-project1/spec-eval/checklists/DET-CSharp_ASPNET-SCR-STU-002.md'
J={}
def src(f,a,z=None):return ('frozen/sources/'+f,a,z or a)
def add(i,st,g,s,r,reason,meaning):
 assert i not in J
 J[i]=(st,g,s,r,reason,meaning)
add(0,'missing',[(15,52),(1106,1148)],[src('Web/Controllers/StudentsController.cs',23,38),src('Core/SqlServerStudentService.cs',227,324)],[(16,81)],'学生1件の対象、モード、責務と入力/保存値の区別は具体的だが、外部ファイルなし・仕様MDを業務IOに含めない境界、正本と開発規約の責務、画像併記を含む概要意味一式は本書にない。未生成の分担表だけで補わない。','学生業務値、フォーム受信、ScopedサービスとSingleton状態、現行HTML投影と関連文書分担の概要を読んだ。')
add(1,'missing',[(48,131)],[src('Views/Students/Edit.cshtml',3,17),src('wwwroot/css/site.css',1)],[(29,45)],'原画面の左右業務グループと状態別独立ダイアログの配置を再現しない。現行ソースの一fieldset・順次2列・inline warning・別削除フォームの投影は正確であるが、原配置の意味一致にはしない。生成されたsource矛盾やcriticalではない。','新規投影、既存/参照差分、確認tableと専用削除formの置き場所・操作を確認した。')
# Field entries explicitly reviewed for each logical field. Shapes/IDs alone are not semantic proof.
F=[
(2,'match',137,203,'Core/SqlServerStudentService.cs',172,194,8,'学生管理番号は新規未採番/既存表示、ルートlongとモデルlong?、DB bigint IDENTITY NOT NULL・入力外/自動採番を再現。'),
(3,'match',138,176,'Core/StudentNormalizer.cs',59,64,9,'学籍番号は新規空必須/既存readonly不変、raw/保存15スカラー、識別子正規化、varchar15 NOT NULL、削除済み含む一意を再現。'),
(4,'match',139,177,'Core/StudentNormalizer.cs',47,57,10,'氏名は新規空必須、raw/保存8スカラー、単一行Trim/非NFKC、原表記nvarchar16 NOT NULLとtyped移送を再現。'),
(5,'match',140,178,'Core/StudentNormalizer.cs',72,85,11,'カナは新規空必須、raw36/正規化18、NFKC/カタカナ化/空白整理、nvarchar36 NOT NULLとtyped移送を再現。'),
(6,'missing',141,179,'Core/JapaneseDateService.cs',17,39,14,'生年月日の4原入力・新規空/全部必須・厳密変換・date NOT NULLは再現するが、元号raw入力上限を設計属性として定義しない。989のraw10検査なしは実装観測であり、入力上限の設計意図を補わない。'),
(7,'match',142,180,'Core/StudentNormalizer.cs',113,128,16,'性別は初期0/未回答許容・必須、数字1桁GENDER値/名称と可否、varchar1 NOT NULLを再現。'),
(8,'match',143,181,'Core/StudentNormalizer.cs',95,100,17,'郵便は必須raw10/保存7、Unicodeスカラー/正規化数字7桁・varchar7 NOT NULLを再現。1113で3桁-4桁の設計表示と現行保存7桁復元を区別。'),
(9,'match',144,182,'Core/StudentNormalizer.cs',113,117,19,'都道府県は新規未選択・必須2桁、PREFECTURE値/名称・既存同値保持、varchar2 NOT NULLを再現。'),
(10,'match',145,183,'Core/StudentNormalizer.cs',131,132,20,'住所1は必須raw/保存45スカラー、単一行Trim、nvarchar90 NOT NULL、取得表示と保存の物理対応を再現。'),
(11,'match',146,184,'Core/StudentNormalizer.cs',47,57,21,'住所2は任意raw/保存45、Trim空NULL・nvarchar90 NULL、通常更新のNULL上書きを再現。'),
(12,'match',147,185,'Core/StudentNormalizer.cs',87,93,22,'本人電話はraw20/正規化最大16、形式と任意NULL/最低1連絡手段、varchar16 NULLを再現。'),
(13,'match',148,186,'Core/StudentNormalizer.cs',102,111,23,'本人メールはraw/保存60、ASCII形式/ドメイン小文字化、任意NULL/最低1連絡手段、varchar60 NULLを再現。'),
(14,'match',149,187,'Core/JapaneseDateService.cs',52,59,24,'入学日は新規空必須、ISO10入力→DateOnly→date NOT NULL、生年月日以上/業務日以下を再現。1113の設計西暦表示形式と実装ブラウザーtype=dateを区別し、表示保証を創作しない。'),
(15,'match',150,188,'Core/StudentNormalizer.cs',136,154,26,'在籍区分は初期01、必須数字2桁・01在学/02休学/03卒業/04退学、分類値名称と区分別条件、varchar2 NOT NULLを再現。'),
(16,'match',151,189,'Core/StudentNormalizer.cs',137,154,27,'終了日は新規未設定、03/04必須・01/02NULL、ISO10→DateOnly?→date NULL、入学日以上と1113の設計西暦表示/実装差を再現。'),
(17,'match',152,195,'Core/SqlServerStudentService.cs',236,237,64,'年度は当学校年度初期、任意int?、1900～9998、class.school_year smallint NOT NULLとの整合だけに使い、学生保存しない。'),
(18,'match',153,196,'Core/SqlServerStudentService.cs',344,383,66,'学年は任意2桁/空すべて、class.grade_code varchar2 NOT NULLとの整合補助で学生保存しない。1115は有効新規選択と保存時コード存在を設計意図として明記し、現行の全値列挙/独立GRADE照会なしと分ける。'),
(19,'match',154,190,'Web/Inputs/StudentSaveInput.cs',40,60,28,'クラスは新規未所属NULL、01/02必須・03/04任意、19ASCII桁正Int64/long?→bigint NULL、IDだけ保存し名称/補助値と分離。'),
(20,'match',155,204,'Core/SqlServerStudentService.cs',201,214,71,'人数は非削除01/02参考集計/非負、未選択－、定員int NULL無制限/1～9999、予約でなく保存時再計算を再現。'),
(21,'match',156,191,'Core/StudentNormalizer.cs',139,157,29,'緊急氏名はraw/保存8・任意NULL、緊急3入力全未設定または全設定、nvarchar16 NULLを再現。'),
(22,'match',157,192,'Core/StudentNormalizer.cs',140,157,31,'緊急続柄は任意2桁分類値/名称・一式条件、NULL時分類NULL/非NULL時サーバー算定、varchar2 NULLを再現。'),
(23,'match',158,193,'Core/StudentNormalizer.cs',87,93,32,'緊急電話はraw20/正規化最大16・任意NULL/一式条件/最低1連絡先、varchar16 NULLを再現。'),
(24,'match',159,194,'Core/StudentNormalizer.cs',47,57,33,'備考は任意raw/保存120スカラー、プレーンテキストLF統一/Trim空NULL、nvarchar240 NULLを再現。'),
(25,'match',160,197,'Core/SqlServerStudentService.cs',234,257,148,'確認変更理由はraw/保存60、LF/Trim空NULL、確認続行と終了区分訂正で必須、監査nvarchar120 NULLへ移し学生備考と分離。'),
(26,'match',161,205,'Infrastructure/WebPresentation.cs',5,7,40,'更新情報は新規未設定、UTC時点から日本時間19文字/認証主体64スカラー、管理入力外、datetimeoffset7/nvarchar128 NOT NULLを再現。'),
(27,'match',162,198,'Core/SqlServerStudentService.cs',392,414,37,'削除理由は削除時専用必須raw/保存60、学生delete_reasonと監査operation_reasonのnvarchar120 NULLへ設定。通常保存理由/編集中業務値と分離。'),
(28,'match',163,None,'Web/Controllers/StudentsController.cs',26,33,None,'登録更新はViewer以外/新規登録と既存更新のモード、同じSaveへ接続し、操作自体にDB保存列を持たせない。'),
(29,'match',164,None,'Web/Controllers/StudentsController.cs',35,35,None,'入力クリア/編集取消は確認後Originalを複製し、新規初期値/既存読込時値へ戻す。DB最新再読込と区別。'),
(30,'match',165,None,'Web/Controllers/StudentsController.cs',24,25,None,'最新再読込は既存時リンク、dirty破棄確認後GETで最新業務値と版/新Snapshotを取得し、版だけ差替えない。'),
(31,'match',166,None,'Web/Controllers/StudentsController.cs',8,11,None,'検索へ戻るはdirty破棄確認後、復帰Contextと読込時検索版のGET/Resumeで復帰する。手動と成功Flash/303を分ける。'),
(32,'match',167,None,'Infrastructure/WebStudentCoordinator.cs',19,19,None,'論理削除は既存Administrator専用、対象/理由/期待版/明示確認だけを送り、編集業務値を保存しない。'),
(33,'match',168,None,'Core/SqlServerStudentService.cs',269,290,None,'候補は全件数と最大20行の番号/氏名/和暦生年月日/クラスのみ、照合全ID版と表示を分離。'),
(34,'match',169,None,'Core/SqlServerStudentService.cs',274,290,None,'別人続行は理由と確認キーで同じSaveを再実行し、主体/セッション/対象/版/期限/19値/全候補を再検査。'),
(35,'match',170,None,'wwwroot/js/site.js',6,6,None,'確認取消はautofocusの既定type=buttonでキー/sectionをブラウザー内で消し、入力を保持して要求/DB更新なし。')]
for i,st,gl,tr,sf,a,z,db,r in F:
 gs=[(gl,gl),(25,25)]+([(tr,tr)] if tr else [])
 if 3<=i<=25 or i==27:gs.append((1043,1049))
 if i in (8,14,16):gs.append((1113,1113))
 if i==6:gs.append((985,1008))
 if i==18:gs.append((1115,1115))
 extras={20:[(580,580),(1027,1027)],25:[(463,463),(623,623)],28:[(455,470)],29:[(770,828)],30:[(836,889)],31:[(897,968)],32:[(685,764)],33:[(619,679)],34:[(619,651)],35:[(619,651)]}
 gs+=extras.get(i,[])
 ss=[src(sf,a,z),src('Views/Students/Edit.cshtml',4,17),src('Web/Inputs/StudentSaveInput.cs',9,60)]
 if 3<=i<=27:ss.extend([src('Core/StudentNormalizer.cs',119,159),src('Core/SqlServerStudentService.cs',30,38),src('Core/SqlServerStudentService.cs',67,72)])
 if db:ss.append(src('database/001_schema.sql',db,db))
 if i==3:ss.append(src('Core/SqlServerStudentService.cs',246,267))
 if i==26:ss.extend([src('Core/SqlServerStudentService.cs',46,51),src('database/001_schema.sql',40,59)])
 add(i,st,gs,ss,[(85+i,85+i)],r,'今回読んだ項目の実文脈：'+r)
D=[
(36,'match',[(230,230),(195,195),(1114,1114)],'年度候補は全クラス/入力年度を重複除去、降順、当年度/既存所属年度/NULL、範囲とクラス0警告意図を組み合わせて再現。'),
(37,'match',[(231,231),(1025,1025),(1115,1115)],'学年の分類値名称/順序/初期空すべて/00と未所属区別に加え、1115に有効新規選択の意図を明記する。現行は停止含む全値保持/disabledなしと区別して意味再現を評価。'),
(38,'match',[(232,232),(567,580),(399,400)],'クラスID/年度学年コード名称、並び、停止過去既存保持、新席/最終所属の可否、上位同期/不一致解除を再現。'),
(39,'match',[(229,229),(1039,1039)],'在籍分類値名称/順序/初期01/既存保持、01～04の保護停止/期間短縮禁止とUI可否の別判定を再現。'),
(40,'match',[(228,228),(1025,1025)],'都道府県分類値名称/順序/未選択、新規有効期間/既存同値保持を再現。'),
(41,'match',[(227,227),(1039,1039)],'性別分類値名称/順序/初期0未回答、既存同値保持と0保護を再現。'),
(42,'match',[(233,233),(1049,1049)],'続柄分類値名称/順序/未選択NULL、既存保持、新規有効期間、緊急一式/派生分類を再現。'),
(43,'match',[(226,226),(985,1006),(1116,1116)],'元号5ID/名称/新しい順/未選択、許容日付範囲・業務日・境界、変更時範囲再検証の設計意図と即時検証なしの現行を区別。'),
(44,'missing',[(989,989),(1112,1112)],'元号は固定ID・空エラーを詳述するが、raw上限を設計属性として規定しない。実装のraw10検査なしの観測は正確で、設計上限を再現したことにはしない。'),
(45,'match',[(990,990),(1006,1008)],'元号年stringの4桁/元年元または1・全必須/新規空・境界厳密変換、不正補正なしとNULL例外を区別。'),
(46,'match',[(991,991),(996,1008)],'月string2桁正整数・必須/空、実在日/元号境界/未来日と非補正を再現。'),
(47,'match',[(992,992),(996,1008)],'日string2桁正整数・必須/空、実在日/元号境界/未来日と非補正を再現。'),
(48,'match',[(179,179),(985,1008)],'生年月日は4raw入力から成功後のみDateOnly/DB dateへ移し、解析前未確定/原入力と内部日付を分離。'),
(49,'match',[(205,205),(1006,1006)],'更新日時はUTC時点/管理DTOで、日本時間19文字、新規未設定、入力外を再現。'),
(50,'match',[(205,205),(1100,1100)],'更新者は認証主体string64スカラー、管理入力外/新規未設定、物理容量128と分離。'),
(51,'match',[(204,204),(580,580),(1027,1027)],'人数は非削除01/02の非負参考集計、未選択－、保存時本人除外再計算で席予約にしない。'),
(52,'match',[(204,204),(580,580)],'定員int?はNULL無制限、非NULL1～9999、0を代替にしない。'),
(53,'match',[(168,168),(671,671),(1006,1006)],'候補生年月日を内部日付から元号込みToWarekiへ、元年元/2桁月日を表示し比較内部日付と分離。'),
(54,'match',[(168,168),(619,624)],'重複全件数/0候補なしと最大20表示を区別し、全候補ID版をハッシュへ含める。'),
(55,'match',[(203,203),(239,239),(458,458)],'学生対象IDは新規NULL/既存ルート、正Int64最大19ASCII桁、行番号でなく権限存在Snapshot一致を確認。'),
(56,'match',[(199,199),(240,240),(458,463)],'期待版は更新削除の正Int64最大19桁、新規なし、最新DB/WHEREと照合し、Snapshot版や最新へ差替えない。'),
(57,'match',[(241,243)],'検索キーは独立32byte乱数64hex、利用者/session/tab・30分/初回未指定、別Snapshotキーと復帰検索版を分離。'),
(58,'match',[(244,245),(619,626),(673,679)],'確認は独立256bit64hex/10分、主体session対象版19値全候補ハッシュBusyと結び、消費/Unknown/Busy解除を区別。'),
(59,'match',[(242,242),(582,582),(774,828)],'既存DB DetailとOriginalを編集値から分離し、Original取消復元と最新DB NoChange比較の違いを明記。新規Detailなし/初期DTO Snapshotも区別する。'),
(60,'match',[(200,200),(460,460)],'NameKeyは保存氏名からNFKC大文字/全空白除去でサーバー生成160スカラー。入力を信用しない。'),
(61,'match',[(201,201),(460,460)],'KanaKeyは正規化カナから空白除去でサーバー生成18上限、入力から受けない。'),
(62,'match',[(38,38),(257,257),(1096,1102)],'CSRFは認証/MVC基盤opaque情報で長さ創作なし、状態変更POSTの先行拒否を認可/二重送信/排他と別に記述。'),
(63,'missing',[(250,250),(445,445),(1117,1117)],'Busy分離と実際のaria-busy/他button無効化は説明するが、設計のbool false初期/開始終了/再入拒否を規定しない。分離意図のみでは全属性一致としない。'),
(64,'missing',[(250,250),(445,445),(1117,1117)],'要求連番/旧応答破棄なしの現行と設計の分離意図は記述するが、非負連番0初期/旧応答無視/あふれ時停止の具体契約はない。')]
for i,st,g,r in D:
 if i<=43:s=[src('Views/Students/Edit.cshtml',7,13),src('Core/SqlServerStudentService.cs',196,216),src('Core/MasterMaintenanceService.cs',105,115),src('database/002_seed.sql',14,84)];rr=[(126+i-36,126+i-36)]
 elif i<=48:s=[src('Core/JapaneseDateService.cs',17,59),src('Core/StudentNormalizer.cs',123,143)];rr=[(139+i-44,139+i-44)]
 elif i<=54:s=[src('Infrastructure/WebPresentation.cs',5,7),src('Core/SqlServerStudentService.cs',46,51),src('Core/SqlServerStudentService.cs',201,214),src('Core/SqlServerStudentService.cs',269,290),src('Core/JapaneseDateService.cs',41,50),src('database/001_schema.sql',40,59),src('database/001_schema.sql',201)];rr=[(139+i-44,139+i-44)]
 elif i<=59:s=[src('Infrastructure/SearchContextStore.cs',9,15),src('Infrastructure/EditorSnapshotStore.cs',7,11),src('Web/Inputs/StudentSaveInput.cs',34,60),src('Core/SqlServerStudentService.cs',224,335)];rr=[(139+i-44,139+i-44)]
 elif i<=61:s=[src('Core/StudentNormalizer.cs',66,85),src('Core/StudentNormalizer.cs',144,147)];rr=[(139+i-44,139+i-44)]
 else:s=[src('wwwroot/js/site.js',2,9),src('Infrastructure/WebHostSetup.cs',14,18),src('Core/SqlServerStudentService.cs',278)];rr=[(139+i-44,139+i-44)]
 add(i,st,g,s,rr,r,'今回読んだ候補/内部の実文脈：'+r)
EV=[
(65,'match',[(263,274)],'新規は認証/作成権限を持つ利用者が初期Input・候補・Snapshotを作る概要を再現。'),
(66,'match',[(267,274),(319,319),(1114,1114),(1049,1049),(571,576)],'初期コード/候補取得、0/01/当年度/和暦入学日空を手順で再現。1114に必須初期不足の保存不可とクラス0警告の意図、区分別所属必須/過去未所属可を他章に具体化し、専用警告未接続との差を説明する。'),
(67,'match',[(278,319),(1114,1114),(1049,1049)],'作成認可、候補/初期Input、前後Context確認/元Status拒否、空日付表示の図に、1114の初期必須不足時拒否意図を組み合わせて必要意味を確認。図だけの分岐数で評価せず、現行Loadが意図の警告処理を実装したとは主張しない。'),
(68,'match',[(301,313),(1012,1023),(1079,1090)],'新規Lookupの分類INNER/学年LEFT/学生人数参照とDDLの分類値関連を示し、名称参照とメモリSnapshot、非書込を区別。'),
(69,'match',[(301,319),(1012,1014)],'コード→クラス2結果集合、全JOIN/順序/人数/CommitをOP-LKで具体化し、新規学生本体取得/DMLなし。'),
(70,'match',[(257,257),(315,319)],'新規の初回/読取後Context拒否、Snapshot未作成、WebFault元Status/その他503と保存結果非適用を再現。'),
(71,'match',[(325,336)],'IDによる非削除学生最新読込、別Lookup、復帰再確認、新Snapshot、同View編集参照の概要を再現。'),
(72,'match',[(329,336),(25,25),(387,389)],'非削除1件/不在404・新規へ切替えない、DB値/版復元Snapshot、和暦/番号readonly/Viewer制御/停止既存値保持を再現。'),
(73,'match',[(340,389)],'参照認可/非削除存在/和暦Input復元/新Snapshot/モードの分岐を図と手順で再現。二度目Context.Getの401/403/409も503と分けており、後段成功を初回確認で保証しない。'),
(74,'match',[(368,383),(1012,1039),(1079,1090)],'対象単表と候補別取得を正確に説明し、クラス/学年/必須3コード/任意続柄の分類値関連・NULL可否をSQL/DDL ERで再現。'),
(75,'match',[(329,336),(381,383),(1012,1014)],'対象ID非削除SELECT→候補コード/クラス別取得、typed ID/日付復元/最大1行/DB非書込を再現。'),
(76,'match',[(385,389),(257,257)],'不在/削除済/正でないID404、停止既存保持、初回と後段Contextの元Status、非WebFault503を再現。保存でしか発生しない結果を読取へ追加しない。'),
(77,'match',[(395,406),(1116,1116),(985,1008),(1049,1049),(567,580)],'所属上位同期/解除、在籍別日付所属条件、和暦厳密検査の機能内連動を再現。設計の候補再取得/元号変更検証と実際のDOM処理を別に明記。'),
(78,'match',[(399,445),(1116,1116),(985,1008),(1049,1049),(463,464),(567,580)],'元号変更の範囲再検証/年度学年区分変更の再取得意図を1116で示し、厳密非補正/原入力エラー・区分別必須・終了訂正権限理由・上位解除通知/人数参考の本文と組み合わせる。現行changeの未接続機能を実装済みとはしない。'),
(79,'match',[(410,445),(1116,1116),(1008,1008),(1049,1049),(619,624)],'入力変更図と設計意図から、元号変更検証/正常不正・原入力保持、在籍の日付所属条件、候補再取得/参考表示の全意味を複数章で確認する。現行DOM図は即時検証/取得を行わない差を明記し、差をsource矛盾としない。'),
(80,'match',[(433,441),(1012,1023),(1079,1090)],'現行DOM内処理はSQLなし、候補取得元は分類コード/クラス/非削除所属人数の関係であることをSQL/関連図と組み合わせて再現。'),
(81,'match',[(441,441),(1116,1116),(1012,1023)],'候補再取得の設計意図と、クラス候補SQL・分類学年JOIN・順序/人数取得をOP-LKで具体化。現行changeからDB呼出しがない境界を分ける。'),
(82,'match',[(443,445),(594,607),(1008,1008)],'入力補助の取消/保持と厳密日付の通常FieldError原入力再表示、NULL対象外例外を区別。未実行保存成功を補わない。'),
(83,'match',[(451,451),(609,609)],'学生1件/監査を同一保存単位で確定、正常CommitのみSaved・通知配信と別境界の概要を再現。'),
(84,'match',[(455,472),(563,586),(619,628)],'19入力複製/生成3値/緊急4保存値、信頼認可時点、Gate内最新存在版分類クラス新席定員・NoChange・全候補・DML選択・監査Commit/Unknownの順序を具体化。'),
(85,'match',[(476,537),(1057,1069)],'通常入力/存在版/権限/NoChange/確認待ち/学生監査/Commit/Unknownを全分岐と例外表で再現。catch内再表示/外拒否・元Status・非WebFault503を分ける。'),
(86,'match',[(541,559),(565,580),(1079,1090)],'保存の読み書きと実PK/FKを分け、学生クラス/必須3分類/任意続柄/クラス学年/コード分類の関連を再現。監査target_keyをFKとしない。'),
(87,'match',[(563,586),(211,220),(1053,1075)],'最新対象/コードクラス/新席定員/全行番号/全候補/モード別INSERTかUPDATE/監査を具体SQL・typed params・対象条件・確定取消で再現。'),
(88,'match',[(590,609),(1059,1069)],'通常入力保持/不在404/版409/確認409/NoChange200/正常Commit303/Unknown503検索確認を再現し、再表示Lookup失敗や通知失敗をCommitと混同しない。'),
(89,'match',[(615,628)],'別人理由とサーバー確認を同じ保存POSTの全検査へ渡す概要を再現。'),
(90,'match',[(619,628),(117,125),(673,679)],'全件数/先頭20最小4列・取消既定、主体session対象版期限19値全候補hashBusy、差で再確認/理由付き全検査・取消DBなしを再現。'),
(91,'match',[(632,651),(673,679)],'候補有無/非NULLキー/照合Busy/理由/取消要求なし/再POST/Commit消費/Unknown無効化を図と結果で再現。'),
(92,'match',[(655,671),(1079,1090)],'候補学生→任意クラスLEFT、分類値の学年在籍都道府県LEFTとメモリ確認の関連を再現。'),
(93,'match',[(667,679),(619,623)],'非削除本人除外/日付一致かつNameKeyまたはKanaKey、ID昇順全取得/TOPなし、typed params/全候補ID版hashを具体化。'),
(94,'match',[(675,679),(590,607),(1059,1069)],'再確認Rollback/発行409、理由不足422、先行版競合/NoChange、取消無DB、正常Commit/Unknownの確認結果を分ける。'),
(95,'match',[(685,685),(758,758)],'管理者が対象と理由を確認し、業務値を保存せず論理削除して通常検索と人数から除外する概要を再現。'),
(96,'match',[(689,698),(756,758)],'専用ID期待版理由明示確認、Gate内非削除存在版、削除管理7列+監査のみ一括確定、Saved検索復帰を再現。'),
(97,'match',[(702,764),(1059,1069)],'確認取消/入口権限理由版/存在競合/限定UPDATE/監査/Commit/失敗Unknown/後段Loadの全分岐とStatusを再現。'),
(98,'match',[(742,758),(1012,1039),(1079,1090)],'削除単表再読/限定更新/監査・非成功Loadと、候補/名称クラス分類値の関連を組み合わせる。FK/業務値変更を創作しない。'),
(99,'match',[(756,764),(216,218),(1057,1075)],'非削除現版SELECT→期待版WHEREの削除7列UPDATE件数1→DELETE監査→正常Commit/取消・結果分類をtyped paramsで具体化。'),
(100,'hold',[(696,696),(762,764)],'原仕様の削除入力不備原入力保持保証に対し、現行Deleteは非Saved後LoadでDB最新値/版/新Snapshotを作り、投稿業務値・削除理由を復元しない。新稿764と現在source37を再読し実装忠実性を確認したが、原保証適用/原品質は未裁定。0点誤記扱いや実装保証加点にせずnullを維持。'),
(101,'match',[(770,770),(836,836),(897,897)],'取消はOriginal、再読込はDB最新、戻るはApplied Resumeと別の目的/状態境界を再現。'),
(102,'match',[(774,828),(840,889),(901,968),(401,404),(1069,1069)],'新規初期/既存最後読込Original復元、明示確認後最新業務値/版一括置換、戻る/終了未保存確認とUnknown検索案内を操作別に再現。'),
(103,'match',[(785,828),(849,889),(913,943),(401,404)],'Reset/Reload/Backそれぞれ取消保持/続行の図と手順を確認。メモリ復元/DB最新/検索復帰を区別し、FormGuard400など入口も別段階に図示。隣接操作の図だけを証拠にしない。'),
(104,'match',[(810,822),(873,885),(947,962),(1079,1090)],'ResetメモリとLookup、Reload対象単表とLookup、復帰SNAPSHOT検索の学生クラスコードLEFT関係を操作別SQL/共通ERで再現。'),
(105,'match',[(822,828),(885,889),(960,968)],'Reset学生取得なし/Lookupのみ、Reload非削除1件+候補、戻るApplied再検索という各DB操作の条件/引数/非書込を再現。'),
(106,'match',[(824,828),(887,889),(964,968),(1069,1069)],'取消保持、再読込対象/Context拒否、復帰検索版競合、Unknown再送せず検索確認を操作ごとに区別し、版の無言更新なし。')]
ER=[(165,167),(169,177),(179,189),(191,199),(201,203),(205,207),(211,213),(215,223),(225,236),(238,250),(252,254),(256,258),(262,264),(266,274),(276,285),(287,296),(298,300),(302,304),(308,310),(312,322),(324,342),(344,356),(358,360),(362,364),(368,370),(372,380),(382,391),(393,400),(402,404),(406,408),(412,414),(416,424),(426,439),(441,453),(455,457),(459,461),(465,467),(469,477),(479,489),(491,503),(505,507),(509,511)]
for i,st,g,r in EV:
 if i<=70:s=[src('Infrastructure/WebStudentCoordinator.cs',17),src('Web/Controllers/StudentsController.cs',25),src('Web/Inputs/StudentSaveInput.cs',44,54),src('Core/SqlServerStudentService.cs',196,216),src('Infrastructure/SearchContextStore.cs',13,14)]
 elif i<=76:s=[src('Infrastructure/WebStudentCoordinator.cs',17),src('Core/SqlServerStudentService.cs',172,216),src('Web/Controllers/StudentsController.cs',25),src('Views/Students/Edit.cshtml',4,17),src('Infrastructure/SearchContextStore.cs',13,14)]
 elif i<=82:s=[src('wwwroot/js/site.js',2,9),src('Core/StudentNormalizer.cs',119,159),src('Core/JapaneseDateService.cs',17,59),src('Core/SqlServerStudentService.cs',196,216)]
 elif i<=88:s=[src('Core/SqlServerStudentService.cs',227,324),src('Core/SqlServerStudentService.cs',344,390),src('Web/Controllers/StudentsController.cs',28,38)]
 elif i<=94:s=[src('Core/SqlServerStudentService.cs',224,335),src('Views/Students/Edit.cshtml',14),src('wwwroot/js/site.js',3,6)]
 elif i<=100:s=[src('Core/SqlServerStudentService.cs',392,416),src('Web/Controllers/StudentsController.cs',25,38),src('Infrastructure/WebStudentCoordinator.cs',17,19)]
 else:s=[src('Web/Controllers/StudentsController.cs',8,11),src('Web/Controllers/StudentsController.cs',24,41),src('Infrastructure/WebStudentCoordinator.cs',14,21),src('wwwroot/js/site.js',2,8),src('Core/SqlServerStudentService.cs',172,216)]
 s.append(src('Infrastructure/WebHostSetup.cs',23))
 if i in (68,74,80,86,92,98,104):s.append(src('database/001_schema.sql',189,201))
 add(i,st,g,s,[ER[i-65]],r,'今回の'+original[i]['originalCells'][2]+' '+original[i]['originalCells'][3]+'実文脈：'+r)
MP=[(107,203),(108,176),(109,177),(110,178),(111,179),(112,180),(113,181),(114,182),(115,183),(116,184),(117,185),(118,186),(119,187),(120,188),(121,189),(122,195),(123,196),(124,190),(125,204),(126,191),(127,192),(128,193),(129,194),(130,197),(131,205),(132,198),(133,168)]
MR=['学生IDは表示/ルートの内部識別でIDENTITY採番。取得不在を新規や行番号へ置換しない。','番号は入力string→Draft→Identifier→student_no、新規のみ/既存不変/全行一意、通常入力不正原値再表示。','氏名はstring→Text→student_name、原表記Trim/必須、通常不正でDMLなし原入力保持。','カナはstring→Kana→student_name_kana、rawと正規化別、通常不正原入力保持。','生年月日は4raw string→Parse→DateOnly→birth_date、元号列保存なし。通常FieldErrorとNULL対象外例外を分ける。','性別はGENDER値を検査しgender_codeへ、名称は表示専用。','郵便はPostal→保存7桁、1113の3-4表示意図と現行7桁復元を分離。','都道府県はPREFECTURE値→prefecture_code、分類名/名称と保存値分離。','住所1は必須Text→address_line1、通常不正原入力保持/DMLなし。','住所2は任意Text/空NULL→address_line2、通常更新NULL上書き。','本人電話はPhone→phone_number、任意NULL/最低1連絡先条件。','メールはASCII形式/ドメイン小文字→email_address、任意NULL。','入学日はISO string→ParseIso→DateOnly→admission_date、再表示/内部比較を分離。','在籍区分はENROLLMENT_STATUS検査値→enrollment_status_code、名称表示と分離。','終了日はISO厳密date/NULL→enrollment_end_date、03/04必須・01/02NULL。','年度int?は補助要求でclass実年度との整合のみ、学生保存しない。','学年string?は補助要求でclass実学年との整合のみ、名称表示/非保存、1115で設計コード存在と実装差を説明。','クラスstring?→IdParser→long?→class_id、補助年度学年名称を重複保存しない。','人数は算出集計/定員はclass.capacity、参考表示/未選択代替/新席再計算を区別。','緊急氏名は任意Text→emergency_contact_name、全未設定/全設定/NULL更新。','続柄は任意コード→relationship_code、分類は派生または同時NULL。','緊急電話はPhone→emergency_phone_number、緊急一式/最低1連絡先。','備考はLF/Trim任意Text→remarks、空NULLと原入力分離。','確認変更理由はReason→監査operation_reason、学生値/NoChange/hashの対象外。','更新管理DB値→Detail→日本時間/認証主体表示、入力DTO外。','削除理由は専用Reason→必須Text→学生delete_reason/監査reason。原不正保持保証と非SavedLoadが両立しないため適用裁定待ち。','候補は全件数+先頭20の最小4表示値であり、照合全ID版と分離。']
for (i,gl),r in zip(MP,MR):
 g=[(gl,gl),(590,607)]
 if i==107:g=[(137,137),(203,203),(330,334),(381,389)]
 if i==113:g.append((1113,1113))
 if i==123:g.append((1115,1115))
 if i==131:g.append((161,161))
 if i==132:g=[(198,198),(689,698),(764,764)]
 if i==133:g=[(168,168),(619,679)]
 s=[src('Web/Inputs/StudentSaveInput.cs',34,60),src('Core/StudentNormalizer.cs',119,159),src('Core/SqlServerStudentService.cs',30,38),src('Core/SqlServerStudentService.cs',183,194),src('Core/SqlServerStudentService.cs',269,324),src('Web/Controllers/StudentsController.cs',28,37),src('Views/Students/Edit.cshtml',14,17)]
 if i==132:s.extend([src('Core/SqlServerStudentService.cs',392,416),src('Web/Inputs/StudentDeleteInput.cs',4)])
 add(i,'hold' if i==132 else 'match',g,s,[(684+i-107,684+i-107)],r,'今回の移送元/変換/移送先/異常の実文脈：'+r)
U=[(134,176,'student_noは新規だけINSERT、更新/削除不変、全行一意。'),(135,177,'student_nameは検証済TextをINSERT/UPDATE、削除不変。'),(136,178,'student_name_kanaは正規化カナをINSERT/UPDATE、削除不変。'),(137,179,'birth_dateは厳密内部日付をINSERT/UPDATE、和暦raw別列なし、削除不変。'),(138,180,'gender_codeは検証値をINSERT/UPDATE、固定分類を維持、削除不変。'),(139,181,'postal_codeは正規化7桁をINSERT/UPDATE、表示意図と別、削除不変。'),(140,182,'prefecture_codeは検証値をINSERT/UPDATE、固定分類を維持、削除不変。'),(141,183,'address_line1は必須TextをINSERT/UPDATE、削除不変。'),(142,184,'address_line2は任意値/NULLでINSERT/UPDATE上書き、削除不変。'),(143,185,'phone_numberは正規化値/NULLでINSERT/UPDATE上書き、削除不変。'),(144,186,'email_addressは正規化値/NULLでINSERT/UPDATE上書き、削除不変。'),(145,187,'admission_dateは厳密内部dateをINSERT/UPDATE、削除不変。'),(146,188,'enrollment_status_codeは検証値をINSERT/UPDATE、終了訂正権限理由を適用、削除不変。'),(147,189,'enrollment_end_dateは区分検査後date/NULLでINSERT/UPDATE、削除不変。'),(148,190,'class_idは正long/NULLでINSERT/UPDATE、年度学年は非保存、削除不変。'),(149,191,'emergency_contact_nameは検証値/NULLで一式INSERT/UPDATE、削除不変。'),(150,192,'relationship_codeは検証値/NULLで分類と同時INSERT/UPDATE/全消去、削除不変。'),(151,193,'emergency_phone_numberは正規化値/NULLで一式INSERT/UPDATE、削除不変。'),(152,194,'remarksは複数行Text/NULLでINSERT/UPDATE上書き、削除不変。')]
for i,gl,r in U:
 g=[(gl,gl),(211,218)]
 if i==139:g.append((1113,1113))
 add(i,'match',g,[src('Core/StudentNormalizer.cs',119,159),src('Core/SqlServerStudentService.cs',292,307),src('Core/SqlServerStudentService.cs',409,414)],[(716+i-134,716+i-134)],r,'今回の物理SET/INSERTの対象：'+r)
UT=[(153,[(200,202),(211,218)],'name_key/kana_keyは保存氏名カナからサーバー再生成、入力受理なし、INSERT/UPDATEで設定・削除不変。'),(154,[(203,203),(211,213)],'student_idはIDENTITY自動採番/INSERT入力列なし/OUTPUT取得、アプリ最大値+1採番なし、更新削除不変。'),(155,[(202,202),(211,218),(1049,1049)],'必須3分類は新規固定・更新維持、続柄分類は値から派生またはNULL化、フォーム受理なし、一式4列/監査差分へ移送。'),(156,[(212,216)],'created_at/byは開始UTC/認証主体を新規設定、通常更新/削除保持。'),(157,[(212,218),(465,469),(756,758)],'updated_at/byと版は新規1、期待版一致の実変更/削除で時点主体+1、NoChangeは更新管理/監査なし。'),(158,[(212,218),(756,758)],'新規未削除/削除属性NULL、通常更新保持、削除時限定属性を設定し編集中一般業務値を保存しない。'),(159,[(217,218),(1073,1075)],'監査は新規前版NULL後版1/更新削除前後版/対象/変更列名/主体時点/理由/受付GUID/確認有無、同TXで追加し個人情報値を複写しない。')]
for i,g,r in UT:add(i,'match',g,[src('Core/StudentNormalizer.cs',144,147),src('Core/SqlServerStudentService.cs',292,315),src('Core/SqlServerStudentService.cs',385,414),src('database/001_schema.sql',8,43),src('database/001_schema.sql',137,153)],[(735+i-153,735+i-153)],r,'今回の派生/管理更新の対象：'+r)
add(160,'missing',[(970,1008),(1041,1119),(1121,1148)],[src('Program.cs',2,8),src('Infrastructure/WebHostSetup.cs',28),src('Core/JapaneseDateService.cs',17,59),src('Core/SqlServerStudentService.cs',227,324)],[(743,815)],'移送19値/生成値/型/NULL/日付/Unicode/排他/確定/監査は詳述するが、直接開発入力・正本の責務と実装工程の共通/date試験/往復/境界/停止候補/最終席/旧版/履歴失敗/Unknown検証の実施責任が具体化されない。実行証跡を未生成報告へ分担する文書名だけで補足全体を充足しない。','今回の補足はソース日付・normalizer・SQL・HTTP・差分と未生成分担表であり、開発と検証の直接責務は具体化していない。')
assert set(J)==set(range(161))
def evidence(p,a,z):
 f=B/p;n=len(f.read_text(encoding='utf-8-sig').splitlines());assert 1<=a<=z<=n,(p,a,z,n)
 return {'path':p,'startLine':a,'endLine':z,'sha256':sha(f)}
out=[]
for o in original:
 i=o['index'];st,gs,ss,rs,r,meaning=J[i];check=evidence(C,14+i,14+i);assert o['evaluationId'] in (B/C).read_text(encoding='utf-8-sig').splitlines()[13+i]
 row={'evaluationId':o['evaluationId'],'documentId':o['documentId'],'index':i,'originalPoints':o['originalPoints'],'judgement':st,'awardedPoints':o['originalPoints'] if st=='match' else None if st in ('hold','unobservable') else 0,'reason':r,'generatedEvidence':[evidence(G,a,z) for a,z in gs],'sourceEvidence':[evidence(p,a,z) for p,a,z in ss],'referenceEvidence':[evidence(R,a,z) for a,z in rs],'checklistEvidence':[check],'originalCriticalClassification':o['criticalClassification'],'criticalConstraint':False,'criticalFinding':False,'criticalClassificationReason':'元行はNOT_CLASSIFIED。認可/版/限定列/Commit/Unknownを現行ソースに即して区別する。不足と原品質裁定待ちは生成された重要矛盾ではない。','observability':'source-and-authorized-reference-reviewed','reviewedGeneratedMeaning':meaning,'originalSpecQualityJudgement':'hold' if st=='hold' else 'not_scored_in_reproduction_axis','originalSpecQualityPoints':None}
 if st=='hold':row.update({'adjudicationRequired':True,'referenceReproductionJudgement':'source_faithful_difference_original_guarantee_applicability_pending','adjudicationReason':'削除入力不備の原入力保持保証と現行非Saved後Loadは適用/原品質裁定待ち。新稿を再読した実装忠実性を実装保証へ加点しない。'})
 out.append(row)
summary={'rows':161,'maximumPoints':169,'confirmedPoints':sum(x['awardedPoints'] or 0 for x in out),'missingPoints':sum(x['originalPoints'] for x in out if x['judgement']=='missing'),'conflictPoints':0,'heldPoints':sum(x['originalPoints'] for x in out if x['judgement']=='hold'),'unobservablePoints':0,'judgementCounts':dict(collections.Counter(x['judgement'] for x in out)),'criticalFindings':0,'diagnosticRows':sum(x['originalPoints']==0 for x in out),'completeScore':None,'completionPercentage':None}
assert sum(x['originalPoints'] for x in out)==169 and summary['diagnosticRows']==82
im=json.loads((B/'frozen-input-manifest.json').read_text(encoding='utf-8'));cm=json.loads((B/'student-editor-snapshot.json').read_text(encoding='utf-8'));um=json.loads((B/'frozen-manifest.json').read_text(encoding='utf-8'))
for p in um['pins']:assert sha(B/'frozen'/p['snapshotPath'])==p['sha256']
draft=json.loads((B/'frozen/provenance/jobs/eebb51fa1eb2da8f/draft-result.json').read_text(encoding='utf-8'));pub=Path('test-project1/spec-analysis/CSharp_ASPNET/20261013-focus-round-04/spec/detail/student-editor.md');assert sha(pub)==sha(B/G)==draft['contentSha256']
report={'schema':'independent-detail-evaluation/3','classification':'EVALUATOR_ONLY','generatorMayRead':False,'evaluator':'/root/evaluation_inventory/grade_details','evaluatedAt':datetime.datetime.now(datetime.timezone.utc).isoformat(),'projectId':'test-project1','profile':'CSharp_ASPNET','mode':'training-assisted','iteration':'20261013-focus-round-04','documentId':'DET-CSharp_ASPNET-SCR-STU-002','generatedDocumentId':'SM-DET-STUDENT-EDITOR','generatedVersion':'4.0','currentReferenceVersion':'8.0','checklistVersion':'7.4','singleIterationScore':True,'unionComponent':False,'oldMatchScoresReused':False,'wholeNewGeneratedDocumentRead':True,'allOriginalSelectedRowsRead':True,'sourceReviewedFresh':True,'inputManifestSha256':sha(B/'frozen-input-manifest.json'),'candidateSnapshotSha256':sha(B/'student-editor-snapshot.json'),'unionManifestSha256':sha(B/'frozen-manifest.json'),'selectedRowsSha256':sha(B/'selected-rows.json'),'generatedSha256':sha(B/G),'sourceCapsuleManifestSha256':im['sourceCapsuleManifestSha256'],'generationBindingScope':cm['generationBindingScope'],'sealedV2Provenance':False,'verifiedInputPins':90,'verifiedCandidatePins':20,'verifiedUnionPins':130,'sourceCount':43,'authorizedReferenceCount':11,'runtimeAtLaunchFiles':13,'publishedEqualsCompletedDraftAndFrozen':True,'method':'全新本文と全原行を人手再読し、意味単位を当該文書内の図/本文/明記された設計意図で照合。機械処理はID/配点/ハッシュ/行/集計のみ。未裁定はnull、source-faithful差をgenerated conflictにしない。','notPerformed':['application_execution','database_execution','native_visual_acceptance','image_render_acceptance','Excel_PDF_roundtrip','full_1408_score'],'summary':summary,'rows':out}
runner=[p for p in im['pins'] if p['snapshotPath'].endswith('runner-source.py')];report['preservedRunnerPins']=runner
(B/'editor-evaluation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');print(json.dumps(summary,ensure_ascii=False));print('sha',sha(B/'editor-evaluation.json'))
~~~
