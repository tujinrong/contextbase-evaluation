# 詳細仕様2冊の独立評価記録

評価者: /root/evaluation_inventory/grade_details。評価日: 2026-10-13。
training-assisted の凍結入力で、281行・316点を新規に意味照合した。
以下は手動で決定した判定・証拠範囲の監査用記録である。
保存処理は識別子、元配点、ハッシュ、行範囲、集計を機械的に展開するだけで、本文や判定を生成しない。
意味照合と実装試験、設計意図の再現と現行実装の達成は別である。

未実施: 業務アプリ起動、実SQL Server、同時保存、HTML/PNG視覚比較、Excel/PDF。
過去の合格は流用しない。原仕様・ソース・採点表・生成本文は変更しない。

~~~python
from pathlib import Path
import json, hashlib, re, html
from collections import Counter
from datetime import datetime
from zoneinfo import ZoneInfo
base=Path("agents/reverse-agent/test-report/20261013-session-pilot-01/evaluator-only/continuation-01")
frozen=base/"frozen"
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
manifest=json.loads((base/"frozen-manifest.json").read_text(encoding="utf-8-sig"))
bridge=json.loads((frozen/"evaluation/bridge-CSharp_ASPNET.json").read_text(encoding="utf-8-sig"))
S="DET-CSharp_ASPNET-SCR-STU-001"; E="DET-CSharp_ASPNET-SCR-STU-002"
G={S:"generated/20261013-pilot-v2-r2/spec/detail/student-search.md",E:"generated/20261013-pilot-v2-r2/spec/detail/student-editor.md"}
R={S:"current-reference/test-project1/srcs/CSharp_ASPNET/spec/詳細仕様書/CSharp_ASPNET/01_学生検索画面.md",E:"current-reference/test-project1/srcs/CSharp_ASPNET/spec/詳細仕様書/CSharp_ASPNET/02_学生登録画面.md"}
D={d["documentId"]:d for d in bridge["documents"] if d["documentId"] in G}
rows={(r["documentId"],r["index"]):r for r in bridge["items"] if r["documentId"] in G}
decisions={}
def add(doc,indices,j,gr,sr,reason,critical=False,divergence=False,rr=()):
    if isinstance(indices,int): indices=[indices]
    for i in indices:
        assert (doc,i) not in decisions,(doc,i)
        decisions[(doc,i)]=(j,gr,sr,reason,critical,divergence,rr)
# The following semantic decisions are hand-authored after reviewing the complete selected expectations.
# Search overview and fields.
add(S,0,"missing",[(18,47),(49,98),(849,849)],["Web/Controllers/StudentsController.cs:8-25","Core/SqlServerStudentService.cs:103-170","Views/Students/Search.cshtml:3-8"],"機能・I/O・責務は再現するが、概要のレンダリング画像併記と共通仕様・DB定義・開発規約の正本責務一式が揃わない。")
add(S,1,"match",[(49,98),(104,126),(800,814),(836,845)],["Views/Students/Search.cshtml:3-8","wwwroot/js/site.js:4-8","wwwroot/css/site.css:1-1"],"静的HTMLの条件・一覧・操作・メッセージ・Viewer制御・状態を対応付け、設計意図と現行差を明示する。実機撮影と称していない。")
for i,l,c,a in [(2,104,"student_no",9),(3,105,"name_key",12),(4,106,"kana_key",13),(5,107,"school_year",64),(6,108,"grade_code",66),(10,112,"prefecture_code",19),(11,113,"phone_number / emergency_phone_number",22),(12,114,"admission_date",24),(13,115,"admission_date",24)]:
    add(S,i,"missing",[(l,l),(639,732),(794,798)],["Core/SqlServerStudentService.cs:103-154",f"database/001_schema.sql:{a}-{a}"],f"入力・正規化・述語は説明するが、対応DB列 {c} の実DB型とNULL可否を全属性として再掲しない。SQLパラメーター型・DTO nullableを実表属性に代用しない。",True)
add(S,7,"match",[(109,109),(657,657),(781,786)],["Web/Inputs/StudentSaveInput.cs:57-60","Core/SqlServerStudentService.cs:131-145","database/001_schema.sql:28-28"],"任意・未設定・19コード単位・正Int64・存在と上位整合・完全一致・bigint NULLを対応付ける。",True)
add(S,8,"match",[(110,110),(781,786),(798,798),(835,838)],["Core/SqlServerStudentService.cs:110-110","Core/SqlServerStudentService.cs:146-146","database/001_schema.sql:28-28","wwwroot/js/site.js:7-7"],"false・チェック・class_id NULL・所属条件排他・解除・非活性の意図と実装タイミングを再現する。",True,True)
add(S,9,"hold",[(111,111),(135,135)],["Core/SqlServerStudentService.cs:111-112","Core/StudentNormalizer.cs:113-117","Views/Students/Search.cshtml:5-5"],"凍結基準は配列にN-07を対応付けるが、現行は01～04のOrdinal検査でCode/NFKCを呼ばない。生成のNFKCなしは正しい。配列への共通正規化の適用という基準解釈を裁定せず保留する。",False,True,[(91,91)])
add(S,14,"match",[(116,116),(232,295)],["Web/Controllers/StudentsController.cs:13-16","Infrastructure/WebStudentCoordinator.cs:7-9"],"今回入力を検査して最初のページを取得する検索操作で、業務DB保存はない。")
add(S,15,"match",[(118,118),(399,437)],["Web/Controllers/StudentsController.cs:21-21","Infrastructure/WebStudentCoordinator.cs:15-15"],"クリアは保持条件・結果を消し初期条件・未検索へ戻す。DB削除とは区別する。")
add(S,16,"match",[(119,119),(524,563)],["Views/Students/Search.cshtml:6-6","Web/Controllers/StudentsController.cs:23-25","Infrastructure/WebStudentCoordinator.cs:17-17"],"新規権限・遷移・検索条件を登録値へ流用しないことを再現する。")
add(S,17,"match",[(844,844),(18,18),(849,849)],["Views/Students/Search.cshtml:3-8","Web/Controllers/StudentsController.cs:8-25"],"メニューへ戻る設計意図と現行不存在、業務DB更新なしを明示する。実装達成ではない。",False,True)
add(S,18,"missing",[(178,178),(802,814),(844,844)],["Infrastructure/WebStudentCoordinator.cs:21-21","Views/Students/Search.cshtml:7-8"],"件数と状態はあるが、RangeFrom/RangeTo別の設定・値域・0件0～0を再掲しない。現行不存在の説明だけでは全属性一致にならない。")
add(S,19,"match",[(178,178),(804,810),(818,818)],["Core/SqlServerStudentService.cs:105-105","Core/SqlServerStudentService.cs:168-168","Infrastructure/WebPresentation.cs:7-7"],"今回検索入口の時点を日本時間19文字表示し、未検索・DB保存なしを区別する。")
add(S,20,"match",[(88,90),(120,120),(347,359)],["Views/Students/Search.cshtml:4-8","Core/SqlServerStudentService.cs:107-107","Infrastructure/WebStudentCoordinator.cs:12-12"],"20/50/100・既定20・表示指定・変更時1ページ・不正拒否を再現する。")
for i,l,c,a in [(21,164,"student_no",9),(22,165,"student_name",10),(23,166,"student_name_kana",11),(24,167,"birth_date",14),(25,168,"school_year / code_name",64),(26,170,"class_code / class_name",67),(27,172,"code_name",92),(28,173,"code_name / address_line1",20),(30,176,"updated_at",40)]:
    add(S,i,"missing",[(l,min(l+1,179)),(794,794),(814,814),(836,845)],["Core/SqlServerStudentService.cs:77-90","Infrastructure/WebPresentation.cs:20-20","Views/Students/Search.cshtml:8-8",f"database/001_schema.sql:{a}-{a}"],f"表示移送はあるが、{c} の業務長・実DB型・実表NULL可否一式を再掲しない。DTO nullableや物理容量から業務属性を推定しない。")
add(S,29,"match",[(113,113),(174,174)],["Core/SqlServerStudentService.cs:80-80","Core/SqlServerStudentService.cs:148-148","database/001_schema.sql:22-22","Views/Students/Search.cshtml:8-8"],"本人電話varchar(16) NULL、NULLの－、緊急電話は検索だけで一覧へ代替表示しない対応を示す。")
add(S,31,"match",[(126,126),(163,163),(528,559)],["Views/Students/Search.cshtml:8-8","Web/Controllers/StudentsController.cs:24-25","Core/SqlServerStudentService.cs:172-194"],"学生IDで遷移し行番号を使わず、登録側で最新対象・存在・権限を確認する。",True)
add(S,32,"match",[(123,125),(343,397),(844,844)],["Views/Students/Search.cshtml:8-8","Infrastructure/WebStudentCoordinator.cs:12-12","Core/SqlServerStudentService.cs:160-168"],"ページ操作と有効範囲補正、先頭／最後の設計操作と現行前後・反映ボタンの差を示す。",False,True)
add(S,[33,34],"match",[(89,90),(121,122),(721,730)],["Core/SqlServerStudentService.cs:107-108","Core/SqlServerStudentService.cs:162-164","Views/Students/Search.cshtml:8-8"],"固定並び4値・方向2値・既定・変更時1ページ・同順位ID昇順・任意DB列拒否を示す。",True)
# Search zero-point diagnostics.
add(S,[35,36,37,38,39],"missing",[(132,136)],["Core/SqlServerStudentService.cs:196-216","Views/Students/Search.cshtml:5-5"],"検索候補は詳述するが、当該基準候補行の新規登録・既存保持・保護値等の共通用途属性を当該文書に全て再掲しない。0点診断を残す。")
add(S,[40,41,42],"match",[(88,90),(120,122),(721,730)],["Views/Students/Search.cshtml:8-8","Core/SqlServerStudentService.cs:107-108"],"固定候補の値・表示・順序・初期・変更条件を再現する。")
add(S,43,"match",[(153,154),(178,178),(802,812)],["Core/Contracts.cs:57-58","Infrastructure/WebStudentCoordinator.cs:21-21","Core/SqlServerStudentService.cs:156-168"],"件数は非負の実件数で、未検索・超過は未設定、表示件数と別である。")
add(S,[44,45],"missing",[(178,178),(844,844)],["Infrastructure/WebStudentCoordinator.cs:21-21","Views/Students/Search.cshtml:7-8"],"表示範囲の現行不存在は述べるが、各内部値の設定・0件0～0を設計意図として具体化しない。")
add(S,46,"match",[(168,169),(107,107),(844,844)],["Core/SqlServerStudentService.cs:79-79","database/001_schema.sql:64-64","Views/Students/Search.cshtml:8-8"],"一覧年度の取得・任意整数・西暦範囲と未所属表示の意図／現行差を示す。",False,True)
add(S,47,"missing",[(169,169),(814,814)],["Core/SqlServerStudentService.cs:79-79","database/001_schema.sql:92-92"],"学年名称の取得はあるが、業務上限12スカラー値を再掲しない。")
add(S,48,"match",[(170,171),(732,732),(844,844)],["Core/SqlServerStudentService.cs:79-88","database/001_schema.sql:67-67","Views/Students/Search.cshtml:8-8"],"クラスコードの領域・DTO移送・名称欠落で行を落とさないこと・未所属表示の意図と現行差を示す。",False,True)
add(S,49,"missing",[(171,171),(814,814)],["Core/SqlServerStudentService.cs:79-79","database/001_schema.sql:68-68"],"クラス名のnvarchar(36)はあるが18スカラー値の業務長を再掲しない。")
add(S,50,"match",[(167,167),(820,820)],["Core/Contracts.cs:51-55","Core/JapaneseDateService.cs:41-50","Core/SqlServerStudentService.cs:76-83"],"内部生年月日と和暦表示を分離し時差を適用しない。")
add(S,51,"match",[(126,126),(163,163),(532,559)],["Core/Contracts.cs:50-50","Web/Controllers/StudentsController.cs:24-25","Core/SqlServerStudentService.cs:174-181"],"対象はDB採番IDであり行番号ではない。対象存在・権限を再確認する。",True)
add(S,52,"match",[(142,147),(824,826)],["Infrastructure/SearchContextStore.cs:9-14","Web/Controllers/StudentsController.cs:8-22"],"不透明64桁キー・利用者セッション画面別・30分と照合経路を示し、タブ照合の現行適用範囲も明示する。",True,True)
add(S,53,"match",[(186,190)],["Infrastructure/WebHostSetup.cs:15-18","Views/Students/Search.cshtml:4-8"],"基盤CSRFを各POSTに使用し認可・二重送信と別の責務として説明する。",True)
add(S,54,"match",[(493,499),(522,522)],["wwwroot/js/site.js:4-4","Infrastructure/SearchContextStore.cs:14-14"],"aria-busyとボタン制御を再送全体の拒否やDB排他と同一視しない。")
add(S,55,"missing",[(522,522),(839,839)],["wwwroot/js/site.js:2-9"],"旧応答破棄の意図は示すが、連番初期値と桁あふれ時採番停止を再掲しない。")
# Search event facets have been individually reviewed; the following explicit indices serialize those decisions.
search_event_groups=[
([56],[(194,196)],["Web/Controllers/StudentsController.cs:8-11"],"認証済み初回は未検索で学生一覧を取得しない。",False,False),
([57,58],[(200,230),(26,28),(836,839)],["Web/Controllers/StudentsController.cs:8-11","Infrastructure/SearchContextStore.cs:9-14","Core/SqlServerStudentService.cs:197-216"],"初期01/02・20件・昇順・候補・状態作成／復帰・認証・障害を手順とフローで示し、必須候補不足の意図を明示する。",True,True),
([59,60],[(224,226),(744,786)],["Core/SqlServerStudentService.cs:197-216","database/001_schema.sql:189-197"],"コード分類と学年クラスの関連・抽出・順序・SNAPSHOT・確定を示し、JOINとFKを区別する。",False,False),
([61],[(228,230),(802,830),(836,841)],["Web/Controllers/StudentsController.cs:8-22","Infrastructure/WebHostSetup.cs:23-23"],"初期表示に適用する未検索・権限・候補障害を未実行結果から区別する。",False,True),
([62],[(234,236)],["Web/Controllers/StudentsController.cs:13-16","Core/SqlServerStudentService.cs:137-170"],"今回条件で非削除学生を検索する概要が一致する。",False,False),
([63,64],[(240,295),(639,732),(802,820)],["Web/Controllers/StudentsController.cs:13-16","Infrastructure/WebStudentCoordinator.cs:7-9","Core/SqlServerStudentService.cs:103-170"],"複製・正規化・検査・指定マスター・10001上限・0件・最初のページ・同一読取・成功条件保持・日付表示の手順と分岐が揃う。",True,False),
([65,66],[(285,287),(639,786)],["Core/SqlServerStudentService.cs:82-90","Core/SqlServerStudentService.cs:103-170","Core/SqlServerStudentService.cs:218-222"],"クラス・分類値付きコードLEFT JOIN、全述語・型付き引数・同条件件数／ページ・SNAPSHOTと行保持を説明する。",True,False),
([67],[(289,295),(802,830),(840,841)],["Web/Controllers/StudentsController.cs:13-16","Infrastructure/WebStudentCoordinator.cs:20-21","Core/SqlServerStudentService.cs:159-170"],"原入力・エラー・空一覧・0件／超過・所有旧版拒否・障害境界を区別し、失敗表示の意図／現行差を示す。",True,True),
([68,69,70],[(299,341),(485,522),(837,839)],["Web/Controllers/StudentsController.cs:22-22","wwwroot/js/site.js:7-8","Core/SqlServerStudentService.cs:197-216"],"未所属・上位整合解除・未反映通知・Applied維持と、先行クラス補完／旧応答破棄の設計意図・現行差を概要・手順・フローへ対応付ける。",False,True),
([72,73],[(333,341),(744,771),(802,830)],["Web/Controllers/StudentsController.cs:22-22","Core/SqlServerStudentService.cs:197-216","Infrastructure/SearchContextStore.cs:13-14"],"候補クラスとコードの取得・画面絞込み・順序・人数集計なし・学生検索なし・入力と前成功一覧・所有期限／障害を説明する。",False,False),
([74,75,76],[(345,397),(639,732),(841,841)],["Infrastructure/WebStudentCoordinator.cs:11-12","Infrastructure/SearchContextStore.cs:13-14","Core/SqlServerStudentService.cs:103-170"],"成功済み条件のみ、許可表示指定、変更時1ページ、件数再取得・最終ページ補正・未検索／失効／障害の手順と分岐を示す。",True,True),
([77,78,79],[(389,397),(639,830)],["Web/Controllers/StudentsController.cs:18-19","Infrastructure/WebStudentCoordinator.cs:12-12","Core/SqlServerStudentService.cs:82-90","Core/SqlServerStudentService.cs:103-170"],"同じ検索JOIN・同条件件数とページ、各呼出の読取境界、空一覧・0件・超過・拒否・SQL取消を説明する。",True,False),
([80,81,82],[(401,437),(526,563),(844,844)],["Web/Controllers/StudentsController.cs:21-25","Infrastructure/WebStudentCoordinator.cs:15-17","Views/Students/Search.cshtml:6-8"],"クリア・新規・ID編集参照を分岐し、権限・流用禁止・登録側読込・メニュー意図と現行不存在を対応付ける。",True,True),
([83,84,85],[(431,437),(557,563),(802,830)],["Infrastructure/WebStudentCoordinator.cs:15-17","Web/Controllers/StudentsController.cs:21-25","Infrastructure/SearchContextStore.cs:13-14"],"操作自体の業務DB更新なし、メモリER非適用、遷移先読込と再描画候補・状態拒否／障害を区別する。",True,False),
([86,87,88],[(441,483),(565,584),(841,843)],["Web/Controllers/StudentsController.cs:8-11","Web/Controllers/StudentsController.cs:38-38","Infrastructure/WebStudentCoordinator.cs:14-14","Infrastructure/SearchContextStore.cs:13-14"],"元状態へ復帰し、所有認証期限版・未検索／検索済み・元条件再検索・確定通知と期限初期化意図／現行409を手順・フローへ対応付ける。",True,True),
([89,90,91],[(475,483),(625,629),(639,830),(841,843)],["Core/SqlServerStudentService.cs:82-90","Core/SqlServerStudentService.cs:103-170","Infrastructure/WebStudentCoordinator.cs:14-14","Web/Controllers/StudentsController.cs:8-11"],"復帰に同じJOIN・元条件件数と一覧を適用し、条件外学生を押し込まず、拒否・補正・通知消費・確定と再検索成功を区別する。",True,True)]
for ix,gr,sr,reason,c,d in search_event_groups: add(S,ix,"match",gr,sr,reason,c,d)
add(S,71,"hold",[(333,335),(765,771)],["Web/Controllers/StudentsController.cs:39-39","Core/SqlServerStudentService.cs:197-208"],"現行原仕様EV-SRC-003の読取ERはm_student occupancyを含む一方、同じOP-CLASSは検索で人数集計なしと明示する。生成とsource includeOccupancy=falseは一致。原仕様内の図／操作矛盾を片側へ決めず保留する。",False,True,[(276,289),(448,455)])
for i,l in {92:104,93:105,94:106,95:107,96:108,97:109,98:110,100:112,101:113,102:114,103:115,106:120,117:121,118:122}.items():
    add(S,i,"match",[(l,l),(240,251),(639,763)],["Web/Inputs/StudentSearchInput.cs:7-29","Core/SqlServerStudentService.cs:103-170","Web/Controllers/StudentsController.cs:13-16"],"フォーム→処理値→DB条件・方向・正規化・未設定・不正時原入力と空一覧を対応付ける。内部名の綴りで減点しない。",True)
add(S,99,"hold",[(111,111),(135,135)],["Core/SqlServerStudentService.cs:111-112","Core/StudentNormalizer.cs:113-117"],"親在籍配列と同じN-07適用解釈を保留し、0点診断も残す。",False,True,[(91,91)])
add(S,104,"missing",[(178,178),(844,844)],["Infrastructure/WebStudentCoordinator.cs:21-21","Views/Students/Search.cshtml:7-8"],"件数と状態はあるが開始／終了範囲の移送・0件値を再掲しない。")
add(S,105,"match",[(178,178),(818,818)],["Core/SqlServerStudentService.cs:105-105","Core/SqlServerStudentService.cs:168-168","Infrastructure/WebPresentation.cs:7-7"],"今回検索時点を日本時間へ移送し、DB保存と区別する。")
for i,l in {107:164,108:165,109:166,110:167,111:168,112:170,113:172,114:173,115:174,116:176}.items():
    add(S,i,"match",[(l,min(l+1,177)),(728,732),(814,820),(844,844)],["Core/SqlServerStudentService.cs:77-90","Infrastructure/WebPresentation.cs:20-20","Views/Students/Search.cshtml:8-8"],"当該DB→DTO→表示の方向・変換・未設定・保存値と照合値・日付・欠損と設計意図／現行差を対応付ける。",False,i in [111,112,113])
add(S,119,"missing",[(788,849)],["Core/StudentNormalizer.cs:37-117","Core/JapaneseDateService.cs:9-61","Infrastructure/SearchContextStore.cs:9-15","Core/SqlServerStudentService.cs:103-170"],"型・長さ・SQL・状態は詳述するが、共通T／DATE-Tの試験観点と直接開発入力・正本責務一式を再掲しない。")
# Editor overview and all-attribute fields.
add(E,0,"missing",[(15,45),(440,484),(923,939)],["Web/Controllers/StudentsController.cs:23-38","Views/Students/Edit.cshtml:3-17","Core/SqlServerStudentService.cs:227-416"],"学生一件と監査I/O・責務はあるが、画像併記、外部ファイル対象外と正本責務一式を再掲しない。")
add(E,1,"match",[(23,84),(90,123),(925,931)],["Views/Students/Edit.cshtml:3-17","wwwroot/css/site.css:1-1","wwwroot/js/site.js:2-8"],"業務入力・和暦4部品・モード・readonly/disabled・候補確認・取消・理由・メッセージ・削除の静的配置と制約を対応付ける。")
add(E,2,"missing",[(90,90),(180,180),(192,192),(476,476)],["database/001_schema.sql:8-8","database/001_schema.sql:43-43","Core/Contracts.cs:59-60"],"ID採番はあるが実表student_idのbigint IDENTITY(1,1) NOT NULL一式を再掲しない。ルートlongでDB属性を代用しない。",True)
for i,l,t in [(3,91,142),(4,92,143),(5,93,144),(7,95,146),(9,97,148),(10,98,149),(11,99,150),(12,100,151),(13,101,152),(15,103,154),(19,107,156),(21,109,157),(22,110,158),(23,111,159),(24,112,160),(25,113,163),(27,115,168)]:
    add(E,i,"match",[(l,l),(t,t),(856,902),(175,184),(468,484)],["Views/Students/Edit.cshtml:6-17","Web/Inputs/StudentSaveInput.cs:9-43","Core/StudentNormalizer.cs:119-159","Core/SqlServerStudentService.cs:227-416","database/001_schema.sql:9-37"],"当該項目の入力／表示／保存・必須未設定・初期・業務長と正規化・フォーム要求・実DB型NULL・関連検査保存を文書内で対応付ける。",i not in [11,24])
add(E,6,"missing",[(94,94),(129,129),(145,145),(870,880)],["Core/JapaneseDateService.cs:9-39","Web/Inputs/StudentSaveInput.cs:12-12","Views/Students/Edit.cshtml:7-7"],"和暦4値と厳密変換はあるが元号原入力最大長10を再掲しない。年・月・日の上限と別である。",True)
add(E,8,"hold",[(96,96),(147,147)],["Core/SqlServerStudentService.cs:189-189","Web/Inputs/StudentSaveInput.cs:49-49","Views/Students/Edit.cshtml:9-9","Core/StudentNormalizer.cs:95-100"],"基準の郵便番号3桁－4桁表示に対し、現行は保存済7桁をそのまま復元し表示整形を持たない。生成はソースに忠実。表示契約と実装差を裁定せず保留する。",False,True,[(93,93)])
for i,l,t in [(14,102,153),(16,104,155)]:
    add(E,i,"missing",[(l,l),(t,t),(880,882)],["Core/JapaneseDateService.cs:52-59","Core/SqlServerStudentService.cs:190-191","Views/Students/Edit.cshtml:11-11"],"ISO入力・範囲・条件付き必須NULL・dateはあるが、西暦yyyy/MM/dd表示契約を設計意図として再掲しない。ネイティブdate部品の実表示は未試験。",True)
for i,l,t,c in [(17,105,161,"school_year"),(18,106,162,"grade_code")]:
    add(E,i,"missing",[(l,l),(t,t),(945,945)],["Core/SqlServerStudentService.cs:236-237","Core/SqlServerStudentService.cs:371-371","database/001_schema.sql:64-66"],f"選択補助・保存なし・整合はあるが、m_class.{c}の実DB型とNOT NULLを再掲しない。")
add(E,20,"missing",[(108,108),(257,257),(900,902)],["Core/Contracts.cs:63-64","Core/SqlServerStudentService.cs:201-201","Core/SqlServerStudentService.cs:377-380","database/001_schema.sql:71-71"],"参考人数・NULL無制限・定員範囲・予約でないことはあるが、m_class.capacity:int NULLを明示しない。C# int?でDB型を代用しない。",True)
add(E,26,"missing",[(114,114),(180,181),(480,480)],["database/001_schema.sql:40-41","Core/Contracts.cs:59-60","Infrastructure/WebPresentation.cs:7-7"],"日本時間と主体はあるが、更新者64スカラー値・updated_at/byの実型NOT NULL一式を再掲しない。書込パラメーター型でDB属性を代用しない。")
for i,l,gr,sr in [(28,116,[(379,506)],["Web/Controllers/StudentsController.cs:26-33"]),(29,117,[(658,708)],["Web/Controllers/StudentsController.cs:35-35"]),(30,118,[(710,759)],["Web/Controllers/StudentsController.cs:24-25","wwwroot/js/site.js:5-5"]),(31,119,[(761,850)],["Web/Controllers/StudentsController.cs:8-11","wwwroot/js/site.js:5-5"]),(32,120,[(583,656)],["Web/Controllers/StudentsController.cs:37-37","Infrastructure/WebStudentCoordinator.cs:19-19"]),(33,121,[(508,581)],["Views/Students/Edit.cshtml:14-14","Core/SqlServerStudentService.cs:269-290"]),(34,122,[(508,581)],["Views/Students/Edit.cshtml:14-14","Core/SqlServerStudentService.cs:274-315"]),(35,123,[(508,581)],["Views/Students/Edit.cshtml:14-14","wwwroot/js/site.js:6-6"])]:
    add(E,i,"match",[(l,l)]+gr,sr,"当該操作のモード・権限・入力引数・DB保存との分離・明示確認・結果遷移を対応付ける。候補全件と20件表示、保存と取消を分離する。",i in [28,31,32,33,34])
for i,l,gr in [(36,133,[(945,945)]),(37,134,[(945,945)]),(38,135,[(890,902)]),(40,131,[]),(42,136,[(882,882)]),(43,129,[(870,880),(947,947)])]:
    add(E,i,"match",[(l,l)]+gr,["Views/Students/Edit.cshtml:7-13","Core/SqlServerStudentService.cs:196-216","Web/Inputs/StudentSaveInput.cs:44-54","wwwroot/js/site.js:8-8"],"候補元・キー名称・抽出既存保持・順序初期連動・用途と未実装の意図を再現する。",False,i in [37,43])
add(E,[39,41],"missing",[(130,132),(884,884)],["Views/Students/Edit.cshtml:8-11","database/002_seed.sql:19-22"],"分類・表示・初期・保持はあるが、候補の保護値契約を再掲しない。")
add(E,44,"missing",[(94,94),(145,145),(870,878)],["Core/JapaneseDateService.cs:9-39","Views/Students/Edit.cshtml:7-7"],"元号キー・型・空・境界はあるが原入力最大長10を再掲しない。")
add(E,[45,46,47,48],"match",[(94,94),(145,145),(870,880)],["Core/JapaneseDateService.cs:17-50","Web/Inputs/StudentSaveInput.cs:12-12","Core/StudentNormalizer.cs:127-127","Views/Students/Edit.cshtml:7-7"],"和暦各raw文字列の型上限・全値必須・初期空・元年・厳密変換とdate保存を分ける。",True)
add(E,[49,50],"match",[(114,114),(180,181),(925,927)],["Core/Contracts.cs:59-60","Core/SqlServerStudentService.cs:181-181","Core/SqlServerStudentService.cs:229-229","Infrastructure/WebPresentation.cs:7-7"],"更新時点と主体をシステム生成・UTC／日本時間・未設定・DTO外・上限と対応付ける。")
add(E,[51,52],"match",[(108,108),(257,257),(470,470),(900,902)],["Core/SqlServerStudentService.cs:201-201","Core/SqlServerStudentService.cs:377-380","database/001_schema.sql:201-201"],"人数参考と再計算・NULL無制限・1～9999・0を代用しないことを示す。",True)
add(E,[53,54],"match",[(121,121),(516,526),(571,581)],["Views/Students/Edit.cshtml:14-14","Core/SqlServerStudentService.cs:269-290","Core/JapaneseDateService.cs:47-50"],"候補和暦・全件数を20件表示と全候補比較から分離する。",True)
for i,l,sr in [(55,192,["Web/Controllers/StudentsController.cs:23-29","Core/SqlServerStudentService.cs:174-181"]),(56,193,["Web/Inputs/StudentSaveInput.cs:42-60","Core/SqlServerStudentService.cs:252-252","Core/SqlServerStudentService.cs:407-407"]),(57,195,["Infrastructure/SearchContextStore.cs:9-15","Infrastructure/WebStudentCoordinator.cs:6-14"]),(58,197,["Core/SqlServerStudentService.cs:224-225","Core/SqlServerStudentService.cs:274-335"]),(59,194,["Infrastructure/EditorSnapshotStore.cs:7-11","Core/SqlServerStudentService.cs:260-262"])]:
    add(E,i,"match",[(l,l),(866,866),(943,951)],sr,"対象・版・状態キー・確認・Snapshotの型・初期未設定・所有期限・生成用途を再現し、比較先等の意図／実装差を明示する。",True,i in [57,59])
add(E,60,"missing",[(177,177),(860,860),(571,571)],["Core/StudentNormalizer.cs:66-70","Core/StudentNormalizer.cs:144-144"],"氏名キー生成と用途はあるが160スカラー値上限を再掲しない。NVarChar(320)から業務長を推定しない。",True)
add(E,61,"match",[(93,93),(144,144),(177,177),(860,860)],["Core/StudentNormalizer.cs:72-85","Core/StudentNormalizer.cs:145-145"],"保存カナから生成する照合値・18スカラー値上限・入力を信用しない対応を示す。",True)
add(E,62,"match",[(925,925),(387,388)],["Infrastructure/WebHostSetup.cs:15-18","Views/Students/Edit.cshtml:5-5","Web/Controllers/StudentsController.cs:41-41"],"状態変更POSTのCSRF・許可項目・認証認可との分離を再現する。",True)
add(E,63,"match",[(337,377),(200,200)],["wwwroot/js/site.js:2-5","Core/SqlServerStudentService.cs:244-244","Core/SqlServerStudentService.cs:278-278"],"送信表示とボタン制御をDB排他・確認Busyと別にし現行再送抑止の限界を示す。")
add(E,64,"missing",[(328,377),(935,935)],["wwwroot/js/site.js:2-9","Web/Controllers/StudentsController.cs:23-38"],"DOM/HTML送信は説明するが、応答世代初期0・旧応答破棄・桁あふれ停止を設計意図として再掲しない。")
# Editor event facets: each explicit index was independently reviewed.
editor_events=[
([65],[(207,209)],["Web/Controllers/StudentsController.cs:23-25","Infrastructure/WebStudentCoordinator.cs:17-17"],"作成権限のある新規モード起動を再現する。",False,False),
([66,67],[(213,263),(882,884),(945,945)],["Infrastructure/WebStudentCoordinator.cs:17-17","Web/Inputs/StudentSaveInput.cs:44-54","Core/SqlServerStudentService.cs:196-216"],"認証・業務日・候補・初期値・未入力未採番と、必須コード不足／クラス0件の意図・現行差を手順と条件フローで示す。",True,True),
([68,69,70],[(237,263),(908,919),(945,945)],["Core/SqlServerStudentService.cs:196-216","database/001_schema.sql:189-199","Infrastructure/SearchContextStore.cs:13-13"],"分類・学年クラスの図、候補項目・条件・順序・SNAPSHOT・確定、初期表示の権限／候補障害と未実行保存を区別する。",False,True),
([71],[(267,269)],["Web/Controllers/StudentsController.cs:24-25","Infrastructure/WebStudentCoordinator.cs:17-17","Core/SqlServerStudentService.cs:172-194"],"対象IDで非削除学生の最新表示を行う概要を再現する。",False,False),
([72,73],[(273,322),(951,951)],["Core/SqlServerStudentService.cs:172-216","Web/Inputs/StudentSaveInput.cs:44-54","Views/Students/Edit.cshtml:3-13"],"対象不在拒否・最新値と期待版・Snapshot分離・和暦復元・Viewer参照／編集・停止同値保持を手順とフローで示す。",True,True),
([74,75,76],[(299,322),(253,259),(908,919)],["Core/SqlServerStudentService.cs:172-216","database/001_schema.sql:189-199","Infrastructure/WebStudentCoordinator.cs:17-17"],"学生とクラス／分類コード関連、実単表読取と別Lookup、ID非削除・BigInt・最大1行、対象なしと一般失敗・既存値保持を区別する。",True,False),
([77,78,79],[(326,377),(870,902),(945,949)],["wwwroot/js/site.js:2-9","Core/JapaneseDateService.cs:17-39","Core/StudentNormalizer.cs:119-159","Core/SqlServerStudentService.cs:344-383"],"所属・在籍・生年月日の意図を現行DOM補助と保存最終検査から区別し、和暦原入力・終了訂正・候補／人数連動を手順と条件フローへ対応付ける。",True,True),
([80,81,82],[(357,377),(241,259),(908,919),(947,947)],["wwwroot/js/site.js:2-9","Core/SqlServerStudentService.cs:196-216","Web/Controllers/StudentsController.cs:22-25"],"描画済候補・人数・コード分類の図と処理を示し、変更時DB通信なしの現行と再取得意図を区別する。取消要求なし・原入力・最終検査の責務を説明する。",True,True),
([83],[(381,383)],["Core/SqlServerStudentService.cs:227-323","Web/Controllers/StudentsController.cs:26-33"],"学生1件と監査1件の一括確定を再現する。",True,False),
([84,85],[(387,438),(175,186),(488,506),(886,902)],["Core/SqlServerStudentService.cs:227-323","Core/SqlServerStudentService.cs:344-390","Core/StudentNormalizer.cs:119-159","Web/Controllers/StudentsController.cs:28-33"],"19入力・派生緊急一式・保存制御・最新版・マスター・席増加だけの定員・NoChange・全候補確認解放・学生監査Commit・既知失敗／不明を手順と分岐で再現する。",True,False),
([86,87,88],[(442,506),(569,575),(908,931)],["Core/SqlServerStudentService.cs:244-323","Core/SqlServerStudentService.cs:344-390","Web/Controllers/StudentsController.cs:29-33","database/001_schema.sql:189-199"],"全用途分類付き関連図、読取書込監査メモリFKの別、対象・定員・候補・INSERT/UPDATE択一・1件OUTPUT・監査一括確定、原入力と結果を区別する。",True,False),
([89,90,91],[(510,550),(579,581),(949,949)],["Core/SqlServerStudentService.cs:224-225","Core/SqlServerStudentService.cs:274-335","Views/Students/Edit.cshtml:14-14","wwwroot/js/site.js:3-6"],"理由付き同じ保存の全検査再実行、全件／20件・取消初期操作・主体対象版・19値と全候補ハッシュ・期限・再確認・消費／Unknownを説明する。専用通知は意図と現行差を分ける。",True,True),
([92,93,94],[(554,581),(488,506),(908,919),(949,949)],["Core/SqlServerStudentService.cs:82-90","Core/SqlServerStudentService.cs:269-335","Web/Controllers/StudentsController.cs:29-33"],"候補学生所属外部結合、全述語・型・全件ID順・確認メモリ、確認相違と保存結果を対応付ける。",True,True),
([95,96,97],[(585,625),(648,656)],["Views/Students/Edit.cshtml:17-17","Web/Controllers/StudentsController.cs:37-37","Infrastructure/WebStudentCoordinator.cs:19-19","Core/SqlServerStudentService.cs:392-416"],"管理者・対象理由明示確認・ID版だけ・編集業務値なし・ゲート・非削除版・削除属性と監査・Commit・既知失敗／Unknown・復帰を手順と分岐で示す。",True,False),
([98,99],[(629,650),(908,919)],["Core/SqlServerStudentService.cs:404-414","database/001_schema.sql:189-199"],"学生所属コード関連と学生／監査操作図、ID版非削除条件・7更新列・更新1件・監査同一Commit・FKとの別を具体化する。",True,False),
([101,102,103],[(660,708),(712,799),(488,506)],["Web/Controllers/StudentsController.cs:35-35","Web/Controllers/StudentsController.cs:24-25","Web/Controllers/StudentsController.cs:8-11","wwwroot/js/site.js:2-5","Infrastructure/EditorSnapshotStore.cs:7-11"],"新規初期／既存Snapshot取消・最新値と版一式・破棄取消／続行・戻り／終了・Unknown検索案内を別操作の手順と条件フローで再現する。",True,False),
([104,105,106],[(690,708),(742,759),(803,850),(908,919),(488,506)],["Core/SqlServerStudentService.cs:172-216","Core/SqlServerStudentService.cs:82-90","Web/Controllers/StudentsController.cs:35-35","Web/Controllers/StudentsController.cs:8-11"],"Snapshot復元と別Lookup・ID最新再読込・検索再取得の図／DB操作を分け、失効・不在・版・原入力／最新値と未実行保存結果を区別する。",True,False)]
for ix,gr,sr,reason,c,d in editor_events: add(E,ix,"match",gr,sr,reason,c,d)
add(E,100,"hold",[(652,656),(488,506)],["Web/Controllers/StudentsController.cs:37-37","Views/Students/Edit.cshtml:17-17","Core/SqlServerStudentService.cs:396-416"],"原イベント結果は入力不備の原入力保持を要求するが、現行削除結果型の失敗は通常Loadへ戻し投稿削除理由・編集中Inputを復元しない。生成656行は現行に忠実。保存失敗の保持と別の契約であり原期待値の採否を裁定せず保留する。",True,True,[(459,461)])
# Editor transfer diagnostics.
add(E,107,"match",[(90,90),(180,180),(192,192),(476,476)],["database/001_schema.sql:8-8","Core/SqlServerStudentService.cs:292-304","Views/Students/Edit.cshtml:4-4"],"IDは自動採番・表示だけで、ルートとモデルへ移送する。DB型不足は親1点行に別記する。")
for i,l in {108:142,109:143,110:144,111:145,112:146,114:148,115:149,116:150,117:151,118:152,119:153,120:154,121:155,122:161,123:162,124:156,126:157,127:158,128:159,129:160,130:163}.items():
    add(E,i,"match",[(l,l),(90,123),(175,186),(387,402),(856,902)],["Web/Inputs/StudentSaveInput.cs:9-54","Core/StudentNormalizer.cs:119-159","Core/SqlServerStudentService.cs:227-323","Core/SqlServerStudentService.cs:344-390"],"当該フォーム→DTO要求→保存値DBまたは制御の方向・未設定・変換・保存失敗原入力を対応付け、理由・選択補助・管理値と業務値を分ける。",True,i==123)
add(E,113,"hold",[(96,96),(147,147)],["Core/SqlServerStudentService.cs:189-189","Views/Students/Edit.cshtml:9-9","Core/StudentNormalizer.cs:95-100"],"親郵便番号と同じ表示契約の裁定を保留し移送診断を残す。",False,True,[(93,93)])
add(E,125,"match",[(108,108),(257,257),(470,470),(900,902)],["Core/SqlServerStudentService.cs:201-201","Core/SqlServerStudentService.cs:377-380","Views/Students/Edit.cshtml:12-12"],"参考人数と定員を分け、未設定・無制限・保存再計算・予約なしを説明する。",True)
add(E,131,"match",[(114,114),(180,181),(275,281)],["Core/SqlServerStudentService.cs:181-181","Views/Students/Edit.cshtml:4-4","Infrastructure/WebPresentation.cs:7-7"],"更新時点と更新者はDTOに受けず、システム値を日本時間・主体として表示する。")
add(E,132,"hold",[(115,115),(168,169),(654,656)],["Web/Controllers/StudentsController.cs:37-37","Views/Students/Edit.cshtml:17-17","Core/SqlServerStudentService.cs:396-416"],"削除理由のDB移送は一致するが、入力不正時の原入力保持は現行Loadで満たされない。親イベント結果と同じ契約裁定を保留する。",True,True,[(459,461)])
add(E,133,"match",[(121,121),(516,526),(571,581)],["Core/SqlServerStudentService.cs:269-290","Views/Students/Edit.cshtml:14-14"],"全件数と最大20件表示を内部全候補比較から分離する。",True)
# Editor update diagnostics.
add(E,134,"match",[(176,176),(472,478),(183,183)],["Core/SqlServerStudentService.cs:254-254","Core/SqlServerStudentService.cs:264-266","Core/SqlServerStudentService.cs:294-301","Core/SqlServerStudentService.cs:409-413"],"番号は新規のみ設定・更新不変・削除保持・全行一意を再現する。",True)
for i,l in {135:143,136:144,137:145,138:146,140:148,141:149,142:150,143:151,144:152,145:153,146:154,147:155,148:156,149:157,150:158,151:159,152:160}.items():
    add(E,i,"match",[(l,l),(175,183),(476,480),(648,650)],["Core/StudentNormalizer.cs:119-159","Core/SqlServerStudentService.cs:294-307","Core/SqlServerStudentService.cs:409-413"],"当該列の検査済新規値・通常全更新・任意空NULL上書き・削除保持と監査差分の別を再現する。",True)
add(E,139,"hold",[(96,96),(147,147),(175,175)],["Core/SqlServerStudentService.cs:189-189","Core/SqlServerStudentService.cs:294-301","Views/Students/Edit.cshtml:9-9"],"登録更新値は一致するが凍結更新行に郵便表示契約も含むため、親と同じ裁定を保留する。",False,True,[(93,93)])
updates=[
(153,[(177,177),(860,860)],["Core/StudentNormalizer.cs:144-145","Core/SqlServerStudentService.cs:294-307"],"照合値は保存側生成・元氏名カナから再生成・削除保持で入力を信用しない。"),
(154,[(180,181),(476,478)],["database/001_schema.sql:8-8","Core/SqlServerStudentService.cs:292-304"],"IDENTITY採番・更新削除保持で最大値＋1を使わない。"),
(155,[(178,179),(175,184),(919,919)],["Core/StudentNormalizer.cs:139-147","Core/SqlServerStudentService.cs:294-307","database/001_schema.sql:196-199"],"必須3分類の固定／保持、続柄連動算定／NULL化、緊急一式消去と監査を再現する。"),
(156,[(180,183),(476,480)],["Core/SqlServerStudentService.cs:296-301","Core/SqlServerStudentService.cs:409-413"],"作成時点主体は新規設定・更新削除保持を再現する。"),
(157,[(180,183),(395,399),(648,650)],["Core/SqlServerStudentService.cs:261-263","Core/SqlServerStudentService.cs:296-315","Core/SqlServerStudentService.cs:409-414"],"初版1・実変更のみ時点主体版+1・期待版条件・NoChange管理値増加なしを再現する。"),
(158,[(180,183),(648,650)],["Core/SqlServerStudentService.cs:296-301","Core/SqlServerStudentService.cs:409-413"],"新規非削除と削除未設定・通常保持・削除時属性のみと一般入力なしを示す。"),
(159,[(184,184),(482,484),(650,650)],["Core/SqlServerStudentService.cs:306-307","Core/SqlServerStudentService.cs:385-390","Core/SqlServerStudentService.cs:413-413"],"監査1件の対象前後版・列JSON・操作・主体時点・理由受付確認を一括確定し個人情報値を複写しない。")]
for i,gr,sr,reason in updates: add(E,i,"match",gr,sr,reason,True)
add(E,160,"missing",[(852,951)],["Core/StudentNormalizer.cs:37-159","Core/JapaneseDateService.cs:9-61","Core/SqlServerStudentService.cs:227-416"],"移送型・正規化日付所属SQL派生は詳述するが、共通T／DATE-T試験観点と直接開発入力・正本責務一式を再掲しない。")
assert set(decisions)==set(rows),(sorted(set(rows)-set(decisions)),sorted(set(decisions)-set(rows)))
cache={}
def evidence(p,a,b):
    if p not in cache: cache[p]=(frozen/p).read_text(encoding="utf-8-sig").splitlines()
    assert 1<=a<=b<=len(cache[p]),(p,a,b,len(cache[p]))
    return {"path":"frozen/"+p,"startLine":a,"endLine":b,"sha256":sha(frozen/p)}
items=[]
for key in sorted(rows):
    r=rows[key]; doc,i=key; j,gr,sr,reason,c,div,rr=decisions[key]
    checklist="evaluation/"+D[doc]["evaluationChecklist"]
    cl=(frozen/checklist).read_text(encoding="utf-8-sig").splitlines()
    found=[n for n,line in enumerate(cl,1) if line.startswith("| "+r["evaluationId"]+" |")]
    assert len(found)==1,(key,found)
    ref=[evidence(checklist,found[0],found[0])]
    ref_lines=(frozen/R[doc]).read_text(encoding="utf-8-sig").splitlines()
    sid=r["originalCells"][2]
    rl=[n for n,line in enumerate(ref_lines,1) if line.startswith("| "+sid+" |") or line.startswith("### "+sid+" ")]
    if rl: ref.append(evidence(R[doc],rl[0],rl[0]))
    for a,b in rr: ref.append(evidence(R[doc],a,b))
    se=[]
    for x in sr:
        m=re.fullmatch(r"(.+):(\d+)-(\d+)",x); assert m,x
        se.append(evidence("sources/"+m[1],int(m[2]),int(m[3])))
    items.append({"documentId":doc,"evaluationId":r["evaluationId"],"index":i,"section":r["originalCells"][1],"specificationId":sid,"aspect":r["originalCells"][3],"originalPoints":r["originalPoints"],"diagnosticOnly":r["originalPoints"]==0,"judgement":j,"awardedPoints":None if j in ("hold","unobservable") else r["originalPoints"] if j=="match" else 0,"reason":reason,"generatedEvidence":[evidence(G[doc],a,b) for a,b in gr],"sourceEvidence":se,"referenceEvidence":ref,"originalExpectationSha256":hashlib.sha256(r["originalCells"][4].encode("utf-8")).hexdigest(),"expectationApplicability":"PENDING_ADJUDICATION" if j=="hold" else "REVIEWED_CURRENT_REFERENCE","observability":"SOURCE_REFERENCE_DISAGREEMENT" if j=="hold" else "SOURCE_OBSERVED_AND_TRAINING_REFERENCE_AVAILABLE","sourceFidelity":"consistent_on_observed_claims","sourceReferenceDivergence":div,"criticalConstraint":c,"criticalClassificationReason":"業務の入力意味・必須不変・権限・版・保存確定等を拘束する重要制約。" if c else "表示・文書・診断の対応で、単独の保存許可／確定保証ではない。","criticalFinding":False,"criticalFindingReason":"当該行でソースに反する重要制約の生成主張は認めない。設計意図の併記を実装成功と解釈しない。","originalSpecificationQuality":"hold" if doc==S and i==71 else "not_scored_in_this_artifact"})
assert len(items)==281 and sum(x["originalPoints"] for x in items)==316
pins=[]
for p in manifest["pins"]:
    path=p["snapshotPath"]; kind=p["kind"]
    relevant=kind in ("source","training-reference","full-bridge","provenance") or path in G.values() or path in R.values() or (kind=="evaluation-checklist" and any(D[d]["evaluationChecklist"] in path for d in G))
    if relevant:
        h=sha(frozen/path); assert h==p["sha256"],(path,h,p["sha256"])
        pins.append({**p,"verifiedSha256":h,"matchesFrozenManifest":True})
def summary(ii):
    return {"judgementCounts":dict(Counter(x["judgement"] for x in ii)),"positiveRows":sum(x["originalPoints"]>0 for x in ii),"zeroDiagnosticRows":sum(x["originalPoints"]==0 for x in ii),"confirmedAwardedPoints":sum(x["awardedPoints"] or 0 for x in ii),"missingPoints":sum(x["originalPoints"] for x in ii if x["judgement"]=="missing"),"pendingPoints":sum(x["originalPoints"] for x in ii if x["awardedPoints"] is None),"completeScore":None,"completePercent":None,"criticalGeneratedContradictions":0,"status":"WITHHELD_PENDING_REFERENCE_SOURCE_ADJUDICATION"}
docs=[]
for doc in G:
    ii=[x for x in items if x["documentId"]==doc]
    docs.append({"documentId":doc,"originalSpecificationVersion":D[doc]["currentVersion"],"originalSpecificationSha256":D[doc]["currentSha256"],"evaluationVersion":D[doc]["evaluationVersion"],"evaluationChecklistSha256":D[doc]["evaluationSha256"],"generatedVersion":"1.0","generatedComponent":"20261013-pilot-v2-r2","generatedPath":"frozen/"+G[doc],"generatedSha256":sha(frozen/G[doc]),"originalRows":len(ii),"originalMaximum":sum(x["originalPoints"] for x in ii),**summary(ii)})
report={"schema":"semantic-detail-evaluation/1.0","classification":"EVALUATOR_ONLY","generatorMayRead":False,"evaluator":"/root/evaluation_inventory/grade_details","evaluationDate":"2026-10-13","evaluatedAt":datetime.now(ZoneInfo("Asia/Tokyo")).isoformat(),"projectId":"test-project1","profile":"CSharp_ASPNET","mode":"training-assisted","runId":"20261013-session-pilot-01","continuationId":"continuation-01","component":"20261013-pilot-v2-r2","unionComponent":True,"singleIterationScore":False,"primaryTarget":"student-search-and-student-editor","historicalFullProfileOriginalMaximum":1408,"formal95MinimumForSelectedTarget":301,"frozenManifestSha256":sha(base/"frozen-manifest.json"),"selectedRowsFileSha256":sha(base/"selected-rows.json"),"bridgeSha256":sha(frozen/"evaluation/bridge-CSharp_ASPNET.json"),"selectedDocumentIds":list(G),"originalRows":281,"originalMaximum":316,"originalPointsChanged":False,"denominatorReduced":False,"diagnosticRowsRetained":True,"scoringPolicy":["意味単位。内部名・番号綴り・パスだけで減点しない。","当該文書内の複数章を組み合わせて意味を照合する。別生成文書で不足属性を補充しない。","明示された設計意図と正しい現行差の併記は再現match。実装達成ではない。","1点項目の全属性一致条件は維持。パラメーター型、DTO nullable、物理容量を実DB属性／業務長に代用しない。","原仕様内の矛盾や原基準／実装契約の未裁定はhold/null。元分母と0点診断を維持。","matchだけ加点。保留が残るため完了得点・割合・95%を出さない。"],"summary":summary(items),"documents":docs,"pins":pins,"items":items,"additionalDiagnostics":[{"id":"D-DETAIL-RENDER","points":0,"status":"NOT_PERFORMED","reason":"静的HTMLとソース構造を照合した。実ブラウザー描画、原仕様PNGと生成PNGの視覚比較、Excel/PDF品質は未検査。"},{"id":"D-DETAIL-TEST","points":0,"status":"NOT_PERFORMED","reason":"アプリ起動・実DB・同時保存・実装往復試験は未実施。意味照合と機械的ハッシュ／ID／配点／行範囲検査。"},{"id":"D-DETAIL-INDEPENDENCE","points":0,"status":"PRESERVED","reason":"過去採点を流用しない新規評価。読む生成本文は指定2冊のみ。原仕様・source・採点表・生成本文を変更しない。"}],"notPerformed":["Application execution","Real SQL Server execution","Concurrency tests","HTML/PNG rendering comparison","Excel/PDF validation","Expected-answer corrections","Model-weight training"],"mechanicalValidation":{"allEvaluationIdsUnique":len({x["evaluationId"] for x in items})==281,"allOriginalIdsRetained":True,"allOriginalPointsRetained":True,"allMatchEvidenceNumberedAndPinned":all(x["generatedEvidence"] for x in items if x["judgement"]=="match"),"allEvidenceRangesValidated":True,"pinsVerified":len(pins),"mechanicalChecksAreNotSemanticPass":True}}
(base/"detail-evaluation.json").write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
print(json.dumps(report["summary"],ensure_ascii=False))
print(json.dumps(docs,ensure_ascii=False))
print("artifact="+str(base/"detail-evaluation.json")+" sha256="+sha(base/"detail-evaluation.json"))
~~~
