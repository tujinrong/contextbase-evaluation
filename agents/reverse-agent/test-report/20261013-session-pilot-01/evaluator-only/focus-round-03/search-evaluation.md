# Focus round 02 学生検索 独立意味評価

EVALUATOR ONLY — generation入力不可。

生成3.0 SHA256 `370fcc8b85803fe167d0b7148e5e612e657ee6a8c9fcefca77d63a89af6c6777`。原仕様8.0／採点表7.4。
source43・許可reference11・起動runtime13・新raw prompt/result/answer/schemaを固定。旧採点転用なし。
全120行（有配点71＋診断49）、観測一致126/147点、不足17点、矛盾0点、保留4点。
重大矛盾0件。完了得点・完了率・95%判定はnull。

全判定と現版根拠は下の行別表を参照。生成・ソース・設計意図を分け、旧判定の転用を行わない。
在籍配列正規化と候補ER/人数操作の矛盾は原基準の要裁定として全行を残す。

| index | 評価ID | 配点 | 判定 | 加点 | 所見 |
| --- | --- | ---: | --- | ---: | --- |
| 0 | DET-CSharp_ASPNET-SCR-STU-001-818202EDAA7C | 3 | missing | 0 | 機能・読取IO・呼出し責務は正確だが、概要の描画画像併記と直接正本/開発入力責務の一式がなく、未生成計画パスをその証明にしない。 |
| 1 | DET-CSharp_ASPNET-SCR-STU-001-8EE9449F3E51 | 3 | missing | 0 | 現行ソースの静的投影として条件・一覧・モードは成立するが、設計の追加操作/表示範囲の配置全体は投影せず、話題表だけでは原画面対応を補完しない。 |
| 2 | DET-CSharp_ASPNET-SCR-STU-001-85EB2FF4920B | 1 | match | 1 | 任意の学籍番号raw15/正規化15、形式、空NULL、前方一致とvarchar15非NULL/VarChar31を区別し、検索では重複・変更検査や保存を行わない。 |
| 3 | DET-CSharp_ASPNET-SCR-STU-001-641EC981BB78 | 1 | match | 1 | 氏名raw8/表記8とNameKey160を分け、任意NULL、部分一致、実DB容量/非NULLと型付き検索bindを再現。 |
| 4 | DET-CSharp_ASPNET-SCR-STU-001-8487A9C21424 | 1 | match | 1 | カナraw36から正規化表記18/照合キー、許可カナ/空白処理、任意NULL、部分一致とnvarchar36非NULLを再現。 |
| 5 | DET-CSharp_ASPNET-SCR-STU-001-46AE28C86B75 | 1 | match | 1 | 任意年度int?、1900～9998/候補実在/すべて、クラスsmallint非NULL属性、西暦と上位完全一致を再現。 |
| 6 | DET-CSharp_ASPNET-SCR-STU-001-7FF1B82EB5CC | 1 | match | 1 | GRADE分類のraw2/NFKC数字2桁、任意空NULL/存在、停止検索可、00と未所属別、クラスvarchar2非NULLを再現。 |
| 7 | DET-CSharp_ASPNET-SCR-STU-001-2097E1CD5ADD | 1 | match | 1 | クラス文字列から任意正Int64、19桁/0不可/NULL、存在と年度学年整合、学生class_id bigint NULLの条件を再現。 |
| 8 | DET-CSharp_ASPNET-SCR-STU-001-0D82B3220DFF | 1 | match | 1 | 未所属false/trueのclass_id IS NULL、所属排他と拒否、ON解除/非活性/OFF非復元の意図と現行差を再現。 |
| 9 | DET-CSharp_ASPNET-SCR-STU-001-9C7EAABFFC27 | 1 | hold | null | 在籍01/02初期、最大4/Ordinal重複拒否/空配列全区分/IN/DB型は正確だが、原N-07正規化の配列適用と厳密実装の扱いは未裁定。新NULL経路も独立に確認。 |
| 10 | DET-CSharp_ASPNET-SCR-STU-001-BEFC3E38BC46 | 1 | match | 1 | PREFECTUREの任意値、raw2/NFKC数字2桁/存在、すべて、varchar2非NULLと完全一致型付きbindを再現。 |
| 11 | DET-CSharp_ASPNET-SCR-STU-001-CE345AE8B601 | 1 | match | 1 | 電話raw20/正規化最大16、許可形式、任意空NULL、本人または緊急のOR完全一致、両列varchar16 NULLを再現。 |
| 12 | DET-CSharp_ASPNET-SCR-STU-001-4ECDE6AD0828 | 1 | match | 1 | 開始ISO10から任意DateOnly、1900～業務日/片側/下端包含/DBdate必須を再現し、設計yyyy/MM/dd表示と入力形式を明示してネイティブ部品実装と分離。 |
| 13 | DET-CSharp_ASPNET-SCR-STU-001-A3F0DF53EC17 | 1 | match | 1 | 終了ISO10から任意DateOnly、片側/開始以下拒否/上端包含/DBdate必須を再現し、設計表示形式と受信・内部形式を分離。 |
| 14 | DET-CSharp_ASPNET-SCR-STU-001-14CE9B3FB604 | 1 | match | 1 | 検索操作は今回条件を検査しPage1で取得、成功条件保持/DB参照のみ、UI抑止と応答世代意図を現行処理から区別。 |
| 15 | DET-CSharp_ASPNET-SCR-STU-001-3EBF0942E20F | 1 | match | 1 | 原行の対象はクリア。同じContextのApplied/LastResult消去、版更新、ModelState消去、初期01/02・20・studentNo ascへ戻して未検索にする。学生DELETEなし。 |
| 16 | DET-CSharp_ASPNET-SCR-STU-001-29BE85CA6FA3 | 1 | match | 1 | 原行の対象は新規登録。Viewer非表示/作成権限確認、検索条件を新規学生へ転記せずreturnContextIdを渡して登録画面へ遷移する。 |
| 17 | DET-CSharp_ASPNET-SCR-STU-001-778AE19CABEA | 1 | missing | 0 | メニューという追加操作名と現行専用操作の不存在は説明するが、共通メニューへの戻り先とDB更新なしの操作契約を本書内で具体化しない。 |
| 18 | DET-CSharp_ASPNET-SCR-STU-001-4C53DF730112 | 1 | missing | 0 | 件数/結果状態は明確だが、表示範囲は追加表示の名と未実装差だけで、開始/終了の値域と0件の範囲属性一式が不足。 |
| 19 | DET-CSharp_ASPNET-SCR-STU-001-F3F05B9FA665 | 1 | match | 1 | 今回サービス入口SearchedAtを日本時間西暦日時へ移し、未検索非表示/非DB保存/更新日時と区別する。 |
| 20 | DET-CSharp_ASPNET-SCR-STU-001-45CB937AB1D9 | 1 | match | 1 | 表示件数の20/50/100、既定20、変更Page1、必須検査/SQL Int size/非DB保存を再現。 |
| 21 | DET-CSharp_ASPNET-SCR-STU-001-4BE95BEB109D | 1 | match | 1 | 保存番号15/varchar15非NULLを文字列表示し、照合パターンではなく文字順。未検索/欠損意図/行保持を再現。 |
| 22 | DET-CSharp_ASPNET-SCR-STU-001-2580A923AAE8 | 1 | match | 1 | 氏名保存表記8/容量16非NULLをそのまま表示、NameKeyと別、未検索/欠損意図/行保持を再現。 |
| 23 | DET-CSharp_ASPNET-SCR-STU-001-5992A6AEB5CC | 1 | match | 1 | 保存カナ表記18/容量36非NULLを表示、照合キーと別、未検索/欠損意図/行保持を再現。 |
| 24 | DET-CSharp_ASPNET-SCR-STU-001-E2A700703DCF | 1 | match | 1 | birth_date必須dateから無時差DateOnly/和暦表示、元年・月日2桁、入力なし/必須値欠損不整合を再現。 |
| 25 | DET-CSharp_ASPNET-SCR-STU-001-D97621F3E369 | 1 | match | 1 | 年度四桁1900～9998/学年名称業務12、基表smallint/容量24非NULLとJOIN任意出力、未所属－/名称不整合の意図を再現。 |
| 26 | DET-CSharp_ASPNET-SCR-STU-001-809FC6941D89 | 1 | match | 1 | クラスコード9/名称18/基表容量と非NULL、class_id経由、未所属/停止/期間外の区別意図と現行注記欠落を再現。 |
| 27 | DET-CSharp_ASPNET-SCR-STU-001-C241C2C610FB | 1 | match | 1 | 在籍名称業務12/容量24/基表非NULL、分類＋値LEFT JOIN、名称不整合の意図と行保持を再現。 |
| 28 | DET-CSharp_ASPNET-SCR-STU-001-201E2ADAAED5 | 1 | match | 1 | 都道府県名12＋住所145と各容量/基表非NULL、連結/住所2非表示/欠損不整合/行保持を再現。 |
| 29 | DET-CSharp_ASPNET-SCR-STU-001-7B137736C1F9 | 1 | match | 1 | 本人電話16/varchar16 NULL、NULLだけ－、緊急電話を表示せず保存値を出力する。 |
| 30 | DET-CSharp_ASPNET-SCR-STU-001-09BFD0B375D6 | 1 | match | 1 | UTC updated_at datetimeoffset7非NULLから日本時間yyyy/MM/dd HH:mm:ssの19文字表示、非編集出力を再現。 |
| 31 | DET-CSharp_ASPNET-SCR-STU-001-9F0DF8AE8584 | 1 | match | 1 | 編集／参照は行番号でなく正64bit学生IDで遷移し、登録入口で最新対象/権限/存在を再確認する。 |
| 32 | DET-CSharp_ASPNET-SCR-STU-001-BCAFF893A5B7 | 1 | match | 1 | 先頭・前・次・最後の意図と実装前後操作を区別し、Pageの保持頁補正/Resume差と有効範囲への再補正を説明。 |
| 33 | DET-CSharp_ASPNET-SCR-STU-001-9930CD28DA63 | 1 | match | 1 | studentNo既定の固定4ソート、最長13の許可値/任意DB列不可/末尾ID昇順、保存なしを再現。 |
| 34 | DET-CSharp_ASPNET-SCR-STU-001-3577E1D08486 | 1 | match | 1 | asc既定の固定2方向、小文字asc/descの最大4、主列方向/ID昇順、保存なし/不正拒否を再現。 |
| 35 | DET-CSharp_ASPNET-SCR-STU-001-3CA4298726C7 | 0 | missing | 0 | 検索年度の停止過去/範囲/降順/空候補は正確だが、新規登録当年度補助を候補契約として本書に再現しない。 |
| 36 | DET-CSharp_ASPNET-SCR-STU-001-24E04907EBCB | 0 | missing | 0 | 検索GRADE候補/名称/停止/順序/00は正確だが、新規有効選択と既存別枠保持の候補属性一式は計画責務へ分担しただけ。 |
| 37 | DET-CSharp_ASPNET-SCR-STU-001-911C12BA9C4F | 0 | missing | 0 | 検索クラス上位絞込/完全順序/空/解除は正確だが、学年名を含む表示と登録新規/最終/既存保持の診断属性一式が不足。 |
| 38 | DET-CSharp_ASPNET-SCR-STU-001-2EFE8DD8D16C | 0 | missing | 0 | 検索在籍候補/01・02/空全区分は正確だが、新規登録01/有効選択と保護01～04の役割をこの候補契約に再掲しない。 |
| 39 | DET-CSharp_ASPNET-SCR-STU-001-3CBFA4E19E92 | 0 | missing | 0 | 検索都道府県の名称/停止/順序/任意空は正確だが、登録新規有効・既存同値保持・登録未選択の一式は不足。 |
| 40 | DET-CSharp_ASPNET-SCR-STU-001-839BE5C68724 | 0 | match | 0 | 表示件数は業務コードではない固定20→50→100、20初期、変更1頁を再現。 |
| 41 | DET-CSharp_ASPNET-SCR-STU-001-6EB9CBF8698A | 0 | match | 0 | 並び順は固定4キーの論理表示/順序/studentNo初期、自由DB列指定なしを再現。 |
| 42 | DET-CSharp_ASPNET-SCR-STU-001-AE6D87D5FD40 | 0 | match | 0 | asc→desc固定順、昇順/降順ラベル、asc初期を再現。 |
| 43 | DET-CSharp_ASPNET-SCR-STU-001-B58C16E76F3C | 0 | missing | 0 | 件数のint/上限/NULL・0状態は明確だが、原内部項目一式に含む0件表示範囲0～0を本書で具体化しない。 |
| 44 | DET-CSharp_ASPNET-SCR-STU-001-184621105C7E | 0 | missing | 0 | RangeFromは未実装差の名前のみで、非負位置値/成功時/未検索・超過未設定/0件0の属性一式が不足。 |
| 45 | DET-CSharp_ASPNET-SCR-STU-001-57216B6625D4 | 0 | missing | 0 | RangeToは未実装差の名前のみで、非負位置値/成功時/未検索・超過未設定/0件0の属性一式が不足。 |
| 46 | DET-CSharp_ASPNET-SCR-STU-001-BDFBC17D956D | 0 | match | 0 | 任意年度出力の取得元、四桁1900～9998/西暦、未所属－の意図と現行差を再現。 |
| 47 | DET-CSharp_ASPNET-SCR-STU-001-30F27E0FB66C | 0 | match | 0 | GRADE名称string?の業務12、保存コードではなく名称、未所属－/欠損不整合の意図を再現。 |
| 48 | DET-CSharp_ASPNET-SCR-STU-001-8A501244EF50 | 0 | match | 0 | クラスコードstring?9/取得元、未所属の表示意図/名称欠落でも行を消さないを再現。 |
| 49 | DET-CSharp_ASPNET-SCR-STU-001-F5E57DED2AF4 | 0 | match | 0 | クラス名称string?18/容量36との区別/取得元、未所属の表示意図/行保持を再現。 |
| 50 | DET-CSharp_ASPNET-SCR-STU-001-5B9587C349EA | 0 | match | 0 | 内部DateOnlyのdate必須取得、欠損不整合、無時差で和暦へ変換し内部値と表示値を分ける。 |
| 51 | DET-CSharp_ASPNET-SCR-STU-001-D8B62A990A55 | 0 | match | 0 | 正64bit/19桁の対象ID、DB採番/新規NULL、ルート/行移送、行番号非代用、権限/存在再確認を再現。 |
| 52 | DET-CSharp_ASPNET-SCR-STU-001-A9CE89C36F45 | 0 | match | 0 | 32byte乱数→64hexの不透明Context、所有/セッション/タブ/30分、初回発行/復帰一覧要求を再現。 |
| 53 | DET-CSharp_ASPNET-SCR-STU-001-6AA636D6AE05 | 0 | missing | 0 | CSRFフォーム生成/POST検査とID・版・排他非代替は正確だが、基盤opaque型と実値長の基盤定義責務が内部項目として不足。 |
| 54 | DET-CSharp_ASPNET-SCR-STU-001-DA1AFEB05304 | 0 | missing | 0 | 同フォーム他ボタン/ariaBusyとEntry排他別は明確だが、IsBusy真偽の初期false/開始終了の内部属性一式は不足。 |
| 55 | DET-CSharp_ASPNET-SCR-STU-001-D5F99F6B1962 | 0 | missing | 0 | 応答世代の初期0/旧応答無視/overflow停止とRevision別は記載するが、画面内非負整数の型・設定元を内部項目一式として定義していない。 |
| 56 | DET-CSharp_ASPNET-SCR-STU-001-2F4076F4B844 | 3 | match | 3 | 認証利用者の起動、初回の候補/新状態だけで学生一覧は取得しないを再現。 |
| 57 | DET-CSharp_ASPNET-SCR-STU-001-CEB54B9A108C | 3 | match | 3 | 参照権限/時刻、初期01・02/20/番号昇順/未検索、状態発行/復帰、必須マスター不足なら検索不可の設計意図を再現。 |
| 58 | DET-CSharp_ASPNET-SCR-STU-001-8B5BD3A34BD3 | 3 | match | 3 | 認証/候補/未検索の実装図を、必須候補不足停止の明示意図と組み合わせ意味照合。実装済保証へ変えない。 |
| 59 | DET-CSharp_ASPNET-SCR-STU-001-D7CFBCD19044 | 3 | match | 3 | 分類→値→GRADE複合参照の読取関連、停止保持/用途別/監査書込非対象を再現。 |
| 60 | DET-CSharp_ASPNET-SCR-STU-001-C629D630F584 | 3 | match | 3 | コード→クラス候補二結果セット、型/順序/読取単位、学生未取得/業務書込みなしを再現。 |
| 61 | DET-CSharp_ASPNET-SCR-STU-001-9C4A6F5838F0 | 3 | match | 3 | 初回候補障害/状態拒否と対象外検索結果、失敗保持意図と現行差、他者拒否/候補非再検索を区別。 |
| 62 | DET-CSharp_ASPNET-SCR-STU-001-9637E6E4F65A | 3 | match | 3 | 今回条件で非削除学生を検索し参照のみ、正常/0件/超過の結果分類を再現。 |
| 63 | DET-CSharp_ASPNET-SCR-STU-001-8C6836155E22 | 3 | match | 3 | DTO移送/条件複製、正規化/存在整合、同条件SNAPSHOT件数ページ、保持/初頁/日付表示と旧応答無視の設計意図を現行HTML/版制御から分けて再現。 |
| 64 | DET-CSharp_ASPNET-SCR-STU-001-69FC36696F49 | 3 | match | 3 | 入力/存在拒否、上限/empty、同一読取一覧、和暦/西暦整形を図と明示仕様で意味照合。 |
| 65 | DET-CSharp_ASPNET-SCR-STU-001-1EA9445F88DE | 3 | match | 3 | 学生/任意クラス/GRADE/在籍/都道府県の分類値LEFT JOIN、NULL多重度、読取関係/FK/監査非連動を再現。 |
| 66 | DET-CSharp_ASPNET-SCR-STU-001-C8A0C07C26B8 | 3 | match | 3 | マスター存在整合→TOP10001件数→同条件ページ、型付きbind/順序/commitを再現。 |
| 67 | DET-CSharp_ASPNET-SCR-STU-001-4031A7ED4200 | 3 | match | 3 | 原入力/空一覧の局所範囲、LastResult残存、0件/超過/所有版拒否と候補非再検索を意図/実装差付きで再現。 |
| 68 | DET-CSharp_ASPNET-SCR-STU-001-25F8A2CE6127 | 3 | match | 3 | 所属変更と候補更新、まだ学生検索せずAppliedを維持するイベントを再現。 |
| 69 | DET-CSharp_ASPNET-SCR-STU-001-D5DBFDB9B880 | 3 | match | 3 | 未所属解除/非活性/OFF非復元、不適合解除通知、上位補完/旧応答破棄の意図と未反映/Applied保持を実装差付きで再現。 |
| 70 | DET-CSharp_ASPNET-SCR-STU-001-ECF83B2057CD | 3 | match | 3 | 未所属分岐/候補取得/解除/通知の図を、上位補完と旧応答無視の意図と組み合わせ意味照合。 |
| 71 | DET-CSharp_ASPNET-SCR-STU-001-2E6EC8AADACD | 3 | hold | null | 原候補ERのoccupancy付き学生関連と原検索候補操作の人数未集計が内部矛盾。新版はLookup(false)のゼロを未集計値と正確に記す。未裁定を保持。 |
| 72 | DET-CSharp_ASPNET-SCR-STU-001-E9251F3FFD1F | 3 | match | 3 | クラス候補参照/上位絞込、学生検索/人数集計/業務書込みなし、型/順序を再現。 |
| 73 | DET-CSharp_ASPNET-SCR-STU-001-8B3FD87731C8 | 3 | match | 3 | 今回原入力/旧一覧/未反映、クラス解除通知/非再検索、所有期限拒否と検証対象外結果の境界を再現。 |
| 74 | DET-CSharp_ASPNET-SCR-STU-001-72E55C707425 | 3 | match | 3 | 元Appliedから表示指定と頁を変更して再検索し、入力途中条件を混ぜないを再現。 |
| 75 | DET-CSharp_ASPNET-SCR-STU-001-981EDBD68D75 | 3 | match | 3 | 保持条件/所有期限/期待版、許可表示指定/変更1頁、同条件再検索/一度最終補正、0件不可と期限初期化意図/現行拒否差を再現。 |
| 76 | DET-CSharp_ASPNET-SCR-STU-001-3D1170870753 | 3 | match | 3 | 保持条件有無/版拒否、検査、件数と頁補正、全体順序取得の図を再現。今回は403/409/422をe.Statusで区別し図と本文とソースが整合。 |
| 77 | DET-CSharp_ASPNET-SCR-STU-001-F891789D8BAE | 3 | match | 3 | ページも同じ用途別分類値LEFT JOIN、学生任意クラスと物理FK/読取関連の区別を参照して再現。 |
| 78 | DET-CSharp_ASPNET-SCR-STU-001-0DC7ABFB61F6 | 3 | match | 3 | 同条件件数→ページと許可全順序、型付きoffset/size、補正の再検索は別SNAPSHOTと再現。 |
| 79 | DET-CSharp_ASPNET-SCR-STU-001-FD120ACB2559 | 3 | match | 3 | 局所WebFaultの対応HTTP状態/Applied保持/空一覧、共通SQL取消/0件超過/候補非再検索を正確に区別。 |
| 80 | DET-CSharp_ASPNET-SCR-STU-001-3E9561673E6C | 3 | match | 3 | 行・新規・クリアの操作受付と専用メニューの設計話題/現行欠落を区別して説明。 |
| 81 | DET-CSharp_ASPNET-SCR-STU-001-0F958E6A35C9 | 3 | missing | 0 | 新規権限/条件非流用、対象ID読込は登録側、クリア初期化は再現するが、メニューの戻り先とDB更新なしの手順は名だけで不足。 |
| 82 | DET-CSharp_ASPNET-SCR-STU-001-04A9D80CB796 | 3 | missing | 0 | クリア/新規/既存ID分岐の図はあるが、メニューの戻り先へ進む分岐は図/手順とも定義されず話題名だけでは不足。 |
| 83 | DET-CSharp_ASPNET-SCR-STU-001-BA5C23F04C4F | 0 | match | 0 | 遷移とメモリClearに業務ERを作らず、遷移先の学生取得/再描画候補読取を別責務へ区別。原非適用0点を保持。 |
| 84 | DET-CSharp_ASPNET-SCR-STU-001-F4832740C697 | 3 | match | 3 | 遷移/初期化自体の業務DB更新なし、遷移先詳細読取と再描画Lookupを分離して説明。 |
| 85 | DET-CSharp_ASPNET-SCR-STU-001-DE44988F8890 | 3 | match | 3 | 操作固有の権限/未存在/版/候補障害と、検索未実行時の0件/上限等の対象外を混同しない。 |
| 86 | DET-CSharp_ASPNET-SCR-STU-001-E22DC1F3ED19 | 3 | match | 3 | 保存削除Savedまたは取消戻るから元Contextへ復帰、非Savedの非自動帰還/結果不明を区別。 |
| 87 | DET-CSharp_ASPNET-SCR-STU-001-ED6049702EC4 | 3 | match | 3 | 所有/期限/版、未検索復元/元条件最新DB再検索、条件非変更、確定通知/消費、期限初期化意図と現行拒否差を再現。 |
| 88 | DET-CSharp_ASPNET-SCR-STU-001-4745B3118380 | 3 | match | 3 | 所有期限拒否、Applied有無、元条件再検索、確定通知の図と期限初期化意図を意味照合。 |
| 89 | DET-CSharp_ASPNET-SCR-STU-001-3A56EE94C8EF | 3 | match | 3 | 復帰も学生/任意クラス/分類値用途別コードの読取関連、FK/監査区別を参照して再現。 |
| 90 | DET-CSharp_ASPNET-SCR-STU-001-3F24B3D24CD6 | 3 | match | 3 | 元Appliedの件数とページ再取得、最新DB/条件非変更、SQL取得頁と表示page/保持補正の違いを再現。 |
| 91 | DET-CSharp_ASPNET-SCR-STU-001-06F52338F30B | 3 | match | 3 | 復帰拒否/後段失敗、確定通知/Take消費、未検索/0件/超過、元条件維持を区別。 |
| 92 | DET-CSharp_ASPNET-SCR-STU-001-4CEB20699DCB | 0 | match | 0 | 番号raw→正規化→student_no前方一致、NULL条件省略/保存なし/原入力拒否を再現。 |
| 93 | DET-CSharp_ASPNET-SCR-STU-001-304D86123D7F | 0 | match | 0 | 氏名表記とNameKey分離、任意NULL/name_key部分一致/型付きbind/原入力拒否を再現。 |
| 94 | DET-CSharp_ASPNET-SCR-STU-001-6DC80333D39F | 0 | match | 0 | カナ表記と空白除去キー分離、任意NULL/kana_key部分一致/原入力拒否を再現。 |
| 95 | DET-CSharp_ASPNET-SCR-STU-001-FA1B1DEC5FC4 | 0 | match | 0 | 任意年度1900～9998/int?/smallint、完全一致/存在検査/拒否を再現。 |
| 96 | DET-CSharp_ASPNET-SCR-STU-001-EEA4FE49B2DD | 0 | match | 0 | NFKC2桁GRADE→grade_code完全一致、00と未所属別、任意NULL/存在拒否を再現。 |
| 97 | DET-CSharp_ASPNET-SCR-STU-001-E47A8676FF5E | 0 | match | 0 | 任意正64bitクラス→学生class_id完全一致、NULLなし/0不可、実年度/正規化学年整合を再現。 |
| 98 | DET-CSharp_ASPNET-SCR-STU-001-B44E2FCE1CFA | 0 | match | 0 | 未所属bool false→true時class_id IS NULL、所属排他/拒否、Options解除をSearch自動解除にしない。 |
| 99 | DET-CSharp_ASPNET-SCR-STU-001-91FBF38A968F | 0 | hold | null | 空配列全区分/IN/重複拒否とNULL単体経路は正確だが、N-07配列正規化とOrdinal実装の原基準裁定は未完。0点診断も保留。 |
| 100 | DET-CSharp_ASPNET-SCR-STU-001-8A43F42C52E8 | 0 | match | 0 | PREFECTURE2桁正規化→prefecture_code完全一致、任意空NULL/存在/不正拒否を再現。 |
| 101 | DET-CSharp_ASPNET-SCR-STU-001-6DEBDB212746 | 0 | match | 0 | 電話正規化→本人または緊急の二列完全一致、空NULL/不正原入力/保存なしを再現。 |
| 102 | DET-CSharp_ASPNET-SCR-STU-001-66EBD557D2C4 | 0 | match | 0 | 開始ISO10→任意DateOnly→admission_date下端包含、片側/範囲/不正原入力を再現。 |
| 103 | DET-CSharp_ASPNET-SCR-STU-001-FA5975CE821D | 0 | match | 0 | 終了ISO10→任意DateOnly→admission_date上端包含、片側/開始≦終了/拒否を再現。 |
| 104 | DET-CSharp_ASPNET-SCR-STU-001-8BDCB190100E | 0 | missing | 0 | 件数と検索状態は明確だが、RangeFrom/RangeToの出力属性と未検索/0件/超過での値を移送契約として具体化していない。 |
| 105 | DET-CSharp_ASPNET-SCR-STU-001-F54A1A8CAD59 | 0 | match | 0 | 今回サービス時刻→日本時間日時、未検索区別/非DB保存/表示行保持の移送を再現。 |
| 106 | DET-CSharp_ASPNET-SCR-STU-001-E8CB75BB9186 | 0 | match | 0 | 表示件数20/50/100、20初期、必須検査/SQL取得範囲/非DB保存を再現。 |
| 107 | DET-CSharp_ASPNET-SCR-STU-001-B30B1EA938EF | 0 | match | 0 | 保存番号文字列の表示と文字順、検索パターン別/基表必須/行保持を再現。 |
| 108 | DET-CSharp_ASPNET-SCR-STU-001-6B8E0F8CE3F6 | 0 | match | 0 | 登録氏名表記のまま出力、NameKey別/基表必須/行保持を再現。 |
| 109 | DET-CSharp_ASPNET-SCR-STU-001-B42712AE75D9 | 0 | match | 0 | 保存カナ表記のまま出力、照合キー別/基表必須/行保持を再現。 |
| 110 | DET-CSharp_ASPNET-SCR-STU-001-FE626D2530FC | 0 | match | 0 | 内部date→無時差和暦表示、内部日付/文字列/欠損不整合の区別を再現。 |
| 111 | DET-CSharp_ASPNET-SCR-STU-001-36DED7C9B233 | 0 | match | 0 | 年度/学年名LEFT JOIN、未所属－/名称不整合の意図と実装補完欠落、行保持を再現。 |
| 112 | DET-CSharp_ASPNET-SCR-STU-001-B03C4F9CFB91 | 0 | match | 0 | class_id経由コード/名称、未所属/停止/期間外の意図と現行注記欠落、行保持を再現。 |
| 113 | DET-CSharp_ASPNET-SCR-STU-001-7AFB3215861F | 0 | match | 0 | 在籍分類と値→名称、欠落でも行保持/不整合意図と実装差を再現。 |
| 114 | DET-CSharp_ASPNET-SCR-STU-001-2287F8F28EDE | 0 | match | 0 | 都道府県名＋住所1連結、住所2非表示、欠損不整合/行保持を再現。 |
| 115 | DET-CSharp_ASPNET-SCR-STU-001-8458E300284A | 0 | match | 0 | 本人電話だけ表示、NULL－、緊急電話非表示/行保持を再現。 |
| 116 | DET-CSharp_ASPNET-SCR-STU-001-F7227FD532A4 | 0 | match | 0 | DB更新日時→日本時間西暦、保存と表示の責務/行保持を再現。 |
| 117 | DET-CSharp_ASPNET-SCR-STU-001-A5D22CFF7C14 | 0 | match | 0 | 固定4ソート→許可列/末尾学生ID昇順、不正自由列拒否を再現。 |
| 118 | DET-CSharp_ASPNET-SCR-STU-001-0F98A4A4A753 | 0 | match | 0 | asc/desc、asc初期、主列方向/ID昇順/不正拒否を再現。 |
| 119 | DET-CSharp_ASPNET-SCR-STU-001-297A9AA423DF | 3 | missing | 0 | 層別移送/長さ/日付/接続/版と関連計画は詳しいが、直接正本/開発規約の入力責務と実装工程の往復・境界試験契約の一式が不足。 |

各行の現版生成/ソース/許可参考設計/原本/採点行のSHAと行範囲はJSONに保存。
このbuilderは新規手判定の保存と検証のみで、期待セルをgenerationへ渡さず原稿を組み立てない。
