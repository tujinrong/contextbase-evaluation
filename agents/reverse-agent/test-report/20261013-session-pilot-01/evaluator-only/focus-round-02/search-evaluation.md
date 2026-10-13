# Focus round 02 学生検索 独立意味評価

EVALUATOR ONLY — generation入力不可。

生成2.0 SHA256 `7750a80014ed98cd2408807798c30cead8f395e6e139a8b1cb4a610768f5634a`。原仕様8.0／採点表7.4。
source43・許可reference11・起動runtime13・新raw prompt/result/answer/schemaを固定。旧採点転用なし。
全120行（有配点71＋診断49）、観測一致129/147点、不足11点、矛盾3点、保留4点。
重大矛盾0件、非重大の図/ソース/本文矛盾1件。完了得点・完了率・95%判定はnull。

図009は状態拒否とサービスValidationFailedを409固定へ併合し、実際の422と本文579に矛盾する。
FLOW原3点をconflictとし、結果説明固有の正しい対応状態を同じ誤りで二重減点しない。
残る有配点不足は概要の描画画像/正本責務、全画面配置、日付表示層、実装工程の試験/開発入力責務。
在籍配列正規化と候補ER/人数操作の矛盾は原基準の要裁定として全行を残す。

| index | 評価ID | 配点 | 判定 | 加点 | 所見 |
| --- | --- | ---: | --- | ---: | --- |
| 0 | DET-CSharp_ASPNET-SCR-STU-001-818202EDAA7C | 3 | missing | 0 | 機能・参照IO・メモリ/役割は詳述するが、原概要の描画画像併記と直接正本/開発規約の責務一式は再現されず、計画パスだけでは補完しない。 |
| 1 | DET-CSharp_ASPNET-SCR-STU-001-8EE9449F3E51 | 3 | missing | 0 | ソース投影は条件・一覧・権限・メッセージを描くが、設計にあるメニュー・表示範囲・先頭/最後の配置を差分表だけで補完せず画面全体対応は不足。 |
| 2 | DET-CSharp_ASPNET-SCR-STU-001-85EB2FF4920B | 1 | match | 1 | 任意番号raw15/正規化15、空NULL、形式だけ検査、前方一致、varchar15非NULLと型付き検索bind、保存なしを別層で再現。 |
| 3 | DET-CSharp_ASPNET-SCR-STU-001-641EC981BB78 | 1 | match | 1 | 氏名raw8と表記8、NameKey160/別DB容量、任意NULL、部分一致、表記/照合値を別に再現。 |
| 4 | DET-CSharp_ASPNET-SCR-STU-001-8487A9C21424 | 1 | match | 1 | カナraw36→表記18/照合キー、カナ検査/空白処理、任意NULL、部分一致とnvarchar36非NULLの対応を再現。 |
| 5 | DET-CSharp_ASPNET-SCR-STU-001-46AE28C86B75 | 1 | match | 1 | 任意年度int?、実在1900～9998、西暦、クラスsmallint非NULL属性、未所属との排他/完全一致を再現。 |
| 6 | DET-CSharp_ASPNET-SCR-STU-001-7FF1B82EB5CC | 1 | match | 1 | GRADE分類/値、raw2とNFKC数字2桁、任意NULL、実在、00と未所属の区別、クラスvarchar2非NULL条件を再現。 |
| 7 | DET-CSharp_ASPNET-SCR-STU-001-2097E1CD5ADD | 1 | match | 1 | 画面文字列→正Int64?、19桁/0拒否、存在/上位整合、任意NULL、学生class_id bigint NULLへ完全一致を再現。 |
| 8 | DET-CSharp_ASPNET-SCR-STU-001-0D82B3220DFF | 1 | match | 1 | false初期、trueはclass_id IS NULL、所属条件との排他、未所属解除/非活性とOFF非復元の意図/現行差を再現。 |
| 9 | DET-CSharp_ASPNET-SCR-STU-001-9C7EAABFFC27 | 1 | hold | null | 配列既定01/02、最大4/Ordinal重複拒否/空配列全区分/IN/DB型は明確だが、原N-07正規化と厳密Ordinal実装の扱いが未裁定。正解を捏造しない。 |
| 10 | DET-CSharp_ASPNET-SCR-STU-001-BEFC3E38BC46 | 1 | match | 1 | 都道府県任意、raw2/NFKC数字2桁、PREFECTURE存在、NULL条件省略、varchar2非NULL基表と検索bindを再現。 |
| 11 | DET-CSharp_ASPNET-SCR-STU-001-CE345AE8B601 | 1 | match | 1 | 電話raw20→正規化最大16、形式/任意空NULL、本人または緊急の二列OR完全一致、両列varchar16 NULLを再現。 |
| 12 | DET-CSharp_ASPNET-SCR-STU-001-4ECDE6AD0828 | 1 | missing | 0 | 開始日の任意ISO10/NFKC厳密変換/範囲/内部DateOnly/両端含むSQLは正確だが、独立した原表示形式の契約を入力値形式で代替している。 |
| 13 | DET-CSharp_ASPNET-SCR-STU-001-A3F0DF53EC17 | 1 | missing | 0 | 終了日の任意ISO10/片側/開始以下/内部dateと包含比較は説明するが、原表示形式の独立契約が入力部品/解析形式の説明だけで不足。 |
| 14 | DET-CSharp_ASPNET-SCR-STU-001-14CE9B3FB604 | 1 | match | 1 | 検索操作・Page1・条件確定・DB参照のみ・UI再入抑止と応答順意図の現行差を再現。 |
| 15 | DET-CSharp_ASPNET-SCR-STU-001-3EBF0942E20F | 1 | match | 1 | 条件変更/候補更新は学生検索せず、再取得/解除/通知/Applied維持と自動連動の設計意図を区別して再現。 |
| 16 | DET-CSharp_ASPNET-SCR-STU-001-29BE85CA6FA3 | 1 | match | 1 | クリアで同IDのApplied/結果とModelStateを初期化し未検索/初期条件へ戻る、学生DELETEなしを再現。 |
| 17 | DET-CSharp_ASPNET-SCR-STU-001-778AE19CABEA | 1 | match | 1 | 新規の権限確認/条件非転記、メニューへDB更新なく戻る意図と実装専用経路欠落を意味として明示。 |
| 18 | DET-CSharp_ASPNET-SCR-STU-001-4C53DF730112 | 1 | match | 1 | TotalCountと範囲を別表示値、0～10000/0件0～0/未検索・超過未設定として意図を定義し、Presentの未実装範囲算出と区別。 |
| 19 | DET-CSharp_ASPNET-SCR-STU-001-F3F05B9FA665 | 1 | match | 1 | 検索日時は今回サービスSearchedAtから日本時間の西暦日時へ移送し、未検索非表示/非DB保存/更新日時との区別を再現。 |
| 20 | DET-CSharp_ASPNET-SCR-STU-001-45CB937AB1D9 | 1 | match | 1 | 表示件数は必須20/50/100、既定20、変更時Page1、SQL Int size/保存なしの制御を再現。 |
| 21 | DET-CSharp_ASPNET-SCR-STU-001-4BE95BEB109D | 1 | match | 1 | 保存番号15/varchar15非NULLを表示、照合用パターンではなく文字順、初回未検索と行保持を再現。 |
| 22 | DET-CSharp_ASPNET-SCR-STU-001-2580A923AAE8 | 1 | match | 1 | 氏名保存表記8/nvarchar16非NULLのまま出力、NameKeyから再構成せず行保持を再現。 |
| 23 | DET-CSharp_ASPNET-SCR-STU-001-5992A6AEB5CC | 1 | match | 1 | 保存カナ18/nvarchar36非NULLを表示、照合キーと区別、初回未検索/入力対象外を再現。 |
| 24 | DET-CSharp_ASPNET-SCR-STU-001-E2A700703DCF | 1 | match | 1 | 生年月日date非NULL→DateOnly→和暦の元年/mmdd表示、入力なし/時差なし/必須値欠損の不整合を再現。 |
| 25 | DET-CSharp_ASPNET-SCR-STU-001-D97621F3E369 | 1 | match | 1 | 年度smallint1900～9998とGRADE名称業務12/容量24/非NULL基表、JOIN任意出力、未所属－/欠損不整合の意図を再現。 |
| 26 | DET-CSharp_ASPNET-SCR-STU-001-809FC6941D89 | 1 | match | 1 | クラスコード9/名称18と容量/非NULL基表、class_id経由LEFT JOIN、未所属/停止/期間外の区別意図と現行注記欠落を再現。 |
| 27 | DET-CSharp_ASPNET-SCR-STU-001-C241C2C610FB | 1 | match | 1 | 在籍名称12/容量24/基表非NULL、用途分類＋値LEFT JOIN、名称欠落で行を消さない/不整合表示の意図を再現。 |
| 28 | DET-CSharp_ASPNET-SCR-STU-001-201E2ADAAED5 | 1 | match | 1 | 都道府県名称12＋住所1の45/各容量と基表非NULL、住所2非表示、連結/欠損不整合/行保持を再現。 |
| 29 | DET-CSharp_ASPNET-SCR-STU-001-7B137736C1F9 | 1 | match | 1 | 本人電話16/varchar16 NULL、null－、緊急電話を一覧へ出さず保存値を表示する対応を再現。 |
| 30 | DET-CSharp_ASPNET-SCR-STU-001-09BFD0B375D6 | 1 | match | 1 | updated_at datetimeoffset7非NULLのUTC保存と+09西暦19桁表示を分け、未検索/非編集出力を再現。 |
| 31 | DET-CSharp_ASPNET-SCR-STU-001-9F0DF8AE8584 | 1 | match | 1 | 行番号/表示名ではなく正64bit学生IDで参照編集へ遷移し対象最新取得/権限/未存在を登録側で再確認する。 |
| 32 | DET-CSharp_ASPNET-SCR-STU-001-BCAFF893A5B7 | 1 | match | 1 | 先頭/前/次/最後と有効範囲補正の意図を、現行前後/変更反映とPage補正/Resume差から分離して再現。 |
| 33 | DET-CSharp_ASPNET-SCR-STU-001-9930CD28DA63 | 1 | match | 1 | 13以内の固定4ソート/既定studentNo、許可列switch、末尾ID昇順、任意DB列を受けない/保存なしを再現。 |
| 34 | DET-CSharp_ASPNET-SCR-STU-001-3577E1D08486 | 1 | match | 1 | 小文字asc/desc固定2種/既定asc、主列方向/ID昇順、必須/非DB制御を再現。 |
| 35 | DET-CSharp_ASPNET-SCR-STU-001-3CA4298726C7 | 0 | missing | 0 | 検索年度降順/停止過去/範囲/空候補は定義するが、診断候補の新規登録当年度補助を本書で一式定義しない。関連計画だけでは属性補完しない。 |
| 36 | DET-CSharp_ASPNET-SCR-STU-001-24E04907EBCB | 0 | missing | 0 | 検索GRADE名称/停止含む/順序/00区別は明確だが、登録新規有効と既存別枠保持の候補属性一式は本書では不足。 |
| 37 | DET-CSharp_ASPNET-SCR-STU-001-911C12BA9C4F | 0 | missing | 0 | 検索クラス上位絞込/順序/空/解除と登録側責務は説明するが、年度・学年・コード・名の表示と登録新規/最終/既存保持の診断属性一式は不足。 |
| 38 | DET-CSharp_ASPNET-SCR-STU-001-2EFE8DD8D16C | 0 | missing | 0 | 検索区分候補/01・02/全解除は明確だが、登録新規01、有効選択と保護01～04の役割をこの候補行で一式定義しない。 |
| 39 | DET-CSharp_ASPNET-SCR-STU-001-3CBFA4E19E92 | 0 | missing | 0 | 検索PREFECTURE停止含む/名称/順序/任意空は定義するが、登録新規有効/既存同値保持/登録未選択の全診断属性は不足。 |
| 40 | DET-CSharp_ASPNET-SCR-STU-001-839BE5C68724 | 0 | match | 0 | 非業務コードの固定20→50→100、20既定、変更Page1、表示件数の意味を再現。 |
| 41 | DET-CSharp_ASPNET-SCR-STU-001-6EB9CBF8698A | 0 | match | 0 | 固定4候補の値/論理表示/順序/番号既定と自由DB列不可を再現。 |
| 42 | DET-CSharp_ASPNET-SCR-STU-001-AE6D87D5FD40 | 0 | match | 0 | 固定asc→desc、昇順/降順ラベル、asc既定を再現。 |
| 43 | DET-CSharp_ASPNET-SCR-STU-001-B58C16E76F3C | 0 | match | 0 | 件数は非負0～10000の別整数値、検索成功時/未検索・超過未設定/0件範囲0～0を意図と実装差付きで再現。 |
| 44 | DET-CSharp_ASPNET-SCR-STU-001-184621105C7E | 0 | match | 0 | RangeFromを件数と別の非負位置値、同値域/成功時/未検索・超過未設定/0件0として明示。現行算式の不存在を捏造で埋めない。 |
| 45 | DET-CSharp_ASPNET-SCR-STU-001-57216B6625D4 | 0 | match | 0 | RangeToを件数と別の非負位置値、同値域/成功時/未検索・超過未設定/0件0として明示。現行算式の不存在を分離。 |
| 46 | DET-CSharp_ASPNET-SCR-STU-001-BDFBC17D956D | 0 | match | 0 | 任意年度出力の取得元/四桁1900～9998/西暦/未所属－の意図と現行差を再現。 |
| 47 | DET-CSharp_ASPNET-SCR-STU-001-30F27E0FB66C | 0 | match | 0 | GRADE名称string?の業務12、保存コードではなく名称、未所属－/名称欠損不整合を再現。 |
| 48 | DET-CSharp_ASPNET-SCR-STU-001-8A501244EF50 | 0 | match | 0 | クラスコードstring?9、class_id経由、未所属の表示意図/名称欠落でも行保持を再現。 |
| 49 | DET-CSharp_ASPNET-SCR-STU-001-F5E57DED2AF4 | 0 | match | 0 | クラス名称string?18、容量36とは別、未所属の表示意図/名称欠落でも行保持を再現。 |
| 50 | DET-CSharp_ASPNET-SCR-STU-001-5B9587C349EA | 0 | match | 0 | 内部birth_dateはdate必須/DateOnly取得、欠損不整合、無時差で和暦変換し表示値と分離する。 |
| 51 | DET-CSharp_ASPNET-SCR-STU-001-D8B62A990A55 | 0 | match | 0 | 対象ID正Int64/19桁/新規null/DB採番/ルート移送、行番号でなく権限/存在再確認を再現。 |
| 52 | DET-CSharp_ASPNET-SCR-STU-001-A9CE89C36F45 | 0 | match | 0 | 共通乱数32byte→64hex不透明Context、所有者/セッション/タブ/30分、初回発行と復帰/一覧要求を再現。 |
| 53 | DET-CSharp_ASPNET-SCR-STU-001-6AA636D6AE05 | 0 | missing | 0 | Antiforgeryのフォーム生成とPOST検査/ID・版・排他非代替は正確だが、基盤opaque型と長さの基盤定義責務が内部項目として不足。 |
| 54 | DET-CSharp_ASPNET-SCR-STU-001-DA1AFEB05304 | 0 | missing | 0 | ブラウザーform submit時のボタン非活性/ariaBusyとDB排他別は記載するが、IsBusy真偽の初期false/開始終了による内部制御一式は不足。 |
| 55 | DET-CSharp_ASPNET-SCR-STU-001-D5F99F6B1962 | 0 | match | 0 | 画面RequestSequenceは非負/初期0/非同期要求時/旧応答無視/桁あふれ採番停止の意図を再現し、サーバーRevisionと区別。 |
| 56 | DET-CSharp_ASPNET-SCR-STU-001-2F4076F4B844 | 3 | match | 3 | 認証利用者起動と状態新規発行/候補取得だけ、学生一覧は初回取得しないを再現。 |
| 57 | DET-CSharp_ASPNET-SCR-STU-001-CEB54B9A108C | 3 | match | 3 | 参照権限/業務時刻、候補/初期01・02/20/studentNo asc/未検索、状態発行と復帰経路、必須マスター不足停止の意図を再現。 |
| 58 | DET-CSharp_ASPNET-SCR-STU-001-8B5BD3A34BD3 | 3 | match | 3 | 認証/候補/初期未検索の実装図と必須候補不足時不可の設計意図を組み合わせ、未実装保証へ置き換えない。 |
| 59 | DET-CSharp_ASPNET-SCR-STU-001-D7CFBCD19044 | 3 | match | 3 | 分類→値→GRADE複合参照の読取関係、検索用途LEFT相当/停止保持/監査書込みなしを再現。 |
| 60 | DET-CSharp_ASPNET-SCR-STU-001-C629D630F584 | 3 | match | 3 | コード候補→クラス候補の順序/型/実行単位/学生未読取/業務書込みなしを再現。 |
| 61 | DET-CSharp_ASPNET-SCR-STU-001-9C4A6F5838F0 | 3 | match | 3 | 初回の候補取得/状態拒否と検索結果対象外、失敗原入力/結果意図と実装差、他者/期限拒否/候補非再検索を再現。 |
| 62 | DET-CSharp_ASPNET-SCR-STU-001-9637E6E4F65A | 3 | match | 3 | 入力条件による非削除学生検索、参照のみ/サービス結果意味を再現。 |
| 63 | DET-CSharp_ASPNET-SCR-STU-001-8C6836155E22 | 3 | match | 3 | 入力複製/正規化/存在整合、同条件SNAPSHOT件数ページ、上限/0/1頁、Applied保持/日付表示と最新検索応答意図を現行差付きで再現。 |
| 64 | DET-CSharp_ASPNET-SCR-STU-001-69FC36696F49 | 3 | match | 3 | 入力/存在失敗、上限/empty分岐、同じ読取単位の一覧、和暦/他日時変換を図と明示仕様で意味照合。 |
| 65 | DET-CSharp_ASPNET-SCR-STU-001-1EA9445F88DE | 3 | match | 3 | 学生/任意クラス/GRADE/在籍/都道府県の複合用途alias LEFT JOIN、NULL多重度/読み関係とFK/監査非連動を再現。 |
| 66 | DET-CSharp_ASPNET-SCR-STU-001-C8A0C07C26B8 | 3 | match | 3 | マスター存在整合→TOP10001件数→同条件ページ、型付きbind/順序/commitを再現。 |
| 67 | DET-CSharp_ASPNET-SCR-STU-001-4031A7ED4200 | 3 | match | 3 | 入力保持/空一覧の局所範囲、LastResult残存、0件/超過区別、所有/版拒否と候補非再検索を意図/現行差付きで再現。 |
| 68 | DET-CSharp_ASPNET-SCR-STU-001-25F8A2CE6127 | 3 | match | 3 | 所属条件変更と候補連動を、学生検索未実行/Applied維持のイベントとして再現。 |
| 69 | DET-CSharp_ASPNET-SCR-STU-001-D5DBFDB9B880 | 3 | match | 3 | 未所属解除/非活性/OFF非復元、不適合解除/警告、クラス先行補完/古い候補破棄/未反映の意図と実装差を再現。 |
| 70 | DET-CSharp_ASPNET-SCR-STU-001-ECF83B2057CD | 3 | match | 3 | 未所属分岐/候補取得/不適合解除/未反映の実装図を上位補完/旧応答破棄の意図と意味照合。 |
| 71 | DET-CSharp_ASPNET-SCR-STU-001-2E6EC8AADACD | 3 | hold | null | 原候補ERは学生occupancy関連、原OP-CLASSは検索人数集計なしで内部矛盾。新版Lookup(false)のゼロは未集計値と正確に説明。未裁定を新たな正解で埋めない。 |
| 72 | DET-CSharp_ASPNET-SCR-STU-001-E9251F3FFD1F | 3 | match | 3 | クラス候補/上位条件絞込、学生検索/人数集計/業務書込みなしと操作型/順序を再現。 |
| 73 | DET-CSharp_ASPNET-SCR-STU-001-8B3FD87731C8 | 3 | match | 3 | 今回原入力/旧一覧、未反映/非再検索、不整合クラス解除/所有期限拒否、検証未実施の境界と対象外結果を再現。 |
| 74 | DET-CSharp_ASPNET-SCR-STU-001-72E55C707425 | 3 | match | 3 | 元Appliedから順序/表示指定/頁だけを変更し、入力途中値を混ぜず再取得する目的を再現。 |
| 75 | DET-CSharp_ASPNET-SCR-STU-001-981EDBD68D75 | 3 | match | 3 | 所有期限/厳密版と適用済条件、許可表示指定/変更1頁、同条件再検索/一度最終補正、0件不可、期限初期化意図と現行拒否を再現。 |
| 76 | DET-CSharp_ASPNET-SCR-STU-001-3D1170870753 | 3 | conflict | 0 | 図はAppliedなし/状態WebFaultに加えQ/Nの検証WebFaultを409固定ノードへ併合。実際のValidationFailedは422でControllerが維持し、正しい579行本文では図の事実誤認を打ち消せない。元3点を保持。 |
| 77 | DET-CSharp_ASPNET-SCR-STU-001-F891789D8BAE | 3 | match | 3 | ページでも同じ学生/任意クラス/用途別複合コードLEFT JOINと読み関係/FKの区別を再現。 |
| 78 | DET-CSharp_ASPNET-SCR-STU-001-0DC7ABFB61F6 | 3 | match | 3 | 件数→ページの同条件検索、許可全体順序/型付きoffset,size、一度補正は別検索SNAPSHOTとして再現。 |
| 79 | DET-CSharp_ASPNET-SCR-STU-001-FD120ACB2559 | 3 | match | 3 | 結果説明固有の局所WebFault対応状態/Applied保持/空一覧/共通SQL取消/0件超過/候補非再検索は正確。別の図誤りをこの説明へ重複減点しない。 |
| 80 | DET-CSharp_ASPNET-SCR-STU-001-3E9561673E6C | 3 | match | 3 | 新規/学生行/クリア/メニューの操作受付を実装経路と設計意図に分けて再現。 |
| 81 | DET-CSharp_ASPNET-SCR-STU-001-0F958E6A35C9 | 3 | match | 3 | 新規権限/条件非流用、対象IDで遷移し読込は登録側、クリア初期状態/DB更新なく共通メニューへ戻る意図を再現。 |
| 82 | DET-CSharp_ASPNET-SCR-STU-001-04A9D80CB796 | 3 | match | 3 | クリア/新規/既存ID分岐の図とDB更新なくメニュー復帰の意図を組み合わせ操作分岐の意味を再現。 |
| 83 | DET-CSharp_ASPNET-SCR-STU-001-BA5C23F04C4F | 0 | match | 0 | 遷移/メモリClearに業務ERを作らず、遷移先学生読込と候補再描画の読取を別責務に分類。原非適用0点を維持。 |
| 84 | DET-CSharp_ASPNET-SCR-STU-001-F4832740C697 | 3 | match | 3 | 操作自体の業務DB更新なし/遷移先読取を区別し、候補Lookupは再描画責務として示す。 |
| 85 | DET-CSharp_ASPNET-SCR-STU-001-DE44988F8890 | 3 | match | 3 | 操作固有の権限/未存在/版/候補障害と検索未実行時の0件/上限等対象外を混同しない。 |
| 86 | DET-CSharp_ASPNET-SCR-STU-001-E22DC1F3ED19 | 3 | match | 3 | 保存/削除Savedと取消/戻るから元Context復帰、非Savedの非自動帰還/結果不明を区別して再現。 |
| 87 | DET-CSharp_ASPNET-SCR-STU-001-ED6049702EC4 | 3 | match | 3 | 所有/期限/版、未検索復元/元条件最新DB再検索、条件非変更と確定成功通知/消費、期限初期化意図と実装拒否差を再現。 |
| 88 | DET-CSharp_ASPNET-SCR-STU-001-4745B3118380 | 3 | match | 3 | 所有期限拒否/検索済有無/元条件検索/確定Flashの復帰図と設計初期化意図を意味照合。 |
| 89 | DET-CSharp_ASPNET-SCR-STU-001-3A56EE94C8EF | 3 | match | 3 | 復帰も同じ学生/任意クラス/用途別複合コード読取関係・FK/監査区別を参照し再現。 |
| 90 | DET-CSharp_ASPNET-SCR-STU-001-3F24B3D24CD6 | 3 | match | 3 | 元Appliedの件数/ページを同条件検索、最新DB/条件非変更、SQL用頁補正と保持pageの違いを再現。 |
| 91 | DET-CSharp_ASPNET-SCR-STU-001-06F52338F30B | 3 | match | 3 | 復帰拒否/失敗段階、確定通知と消費、0件/超過/未検索、元条件維持を区別して再現。 |
| 92 | DET-CSharp_ASPNET-SCR-STU-001-4CEB20699DCB | 0 | match | 0 | 番号原入力→NFKC/大文字化→student_no前方一致、NULL条件省略/保存なし/不正原入力の対応を再現。 |
| 93 | DET-CSharp_ASPNET-SCR-STU-001-304D86123D7F | 0 | match | 0 | 氏名原表記とNameKeyを分離し空NULL/部分一致/不正原入力、name_key型付きbindを再現。 |
| 94 | DET-CSharp_ASPNET-SCR-STU-001-6DC80333D39F | 0 | match | 0 | カナ表記正規化と空白除去キーを分離、空NULL/kana_key部分一致/不正原入力を再現。 |
| 95 | DET-CSharp_ASPNET-SCR-STU-001-FA1B1DEC5FC4 | 0 | match | 0 | 任意年度int?1900～9998、クラスsmallintへ完全一致/実在検査/拒否原入力を再現。 |
| 96 | DET-CSharp_ASPNET-SCR-STU-001-EEA4FE49B2DD | 0 | match | 0 | NFKC2桁GRADE→grade_code完全一致、00と未所属別、空NULL/実在/不正拒否を再現。 |
| 97 | DET-CSharp_ASPNET-SCR-STU-001-E47A8676FF5E | 0 | match | 0 | 任意クラス正64bit→学生class_id完全一致、NULLなし/0不可、年度と正規化学年との実値整合を再現。 |
| 98 | DET-CSharp_ASPNET-SCR-STU-001-B44E2FCE1CFA | 0 | match | 0 | 未所属bool false→true時class_id IS NULL、所属排他/拒否、Options解除をSearch自動解除としない。 |
| 99 | DET-CSharp_ASPNET-SCR-STU-001-91FBF38A968F | 0 | hold | null | 空配列全区分/IN/重複拒否は正確だがN-07適用とOrdinal厳密値の原設計対実装は未裁定。0点診断の保留も残す。 |
| 100 | DET-CSharp_ASPNET-SCR-STU-001-8A43F42C52E8 | 0 | match | 0 | PREFECTURE2桁正規化→prefecture_code完全一致、任意空NULL/実在/不正拒否を再現。 |
| 101 | DET-CSharp_ASPNET-SCR-STU-001-6DEBDB212746 | 0 | match | 0 | 電話正規化→本人または緊急の二列完全一致、空NULL/不正原入力/保存なしを再現。 |
| 102 | DET-CSharp_ASPNET-SCR-STU-001-66EBD557D2C4 | 0 | match | 0 | 開始ISO10→DateOnly?→admission_date包含下端、任意片側/範囲/不正原入力を再現。表示形式不足は親項目で別判定。 |
| 103 | DET-CSharp_ASPNET-SCR-STU-001-FA5975CE821D | 0 | match | 0 | 終了ISO10→DateOnly?→admission_date包含上端、任意片側/開始≦終了/拒否を再現。 |
| 104 | DET-CSharp_ASPNET-SCR-STU-001-8BDCB190100E | 0 | match | 0 | 件数/開始/終了を別表示値として未検索/0件/超過を区別する意図、現行範囲移送なしを明示し算式を実装保証にしない。 |
| 105 | DET-CSharp_ASPNET-SCR-STU-001-F54A1A8CAD59 | 0 | match | 0 | 今回SearchedAt→日本時間日時、未検索区別/DB保存なし/行を黙って落とさない表示対応を再現。 |
| 106 | DET-CSharp_ASPNET-SCR-STU-001-E8CB75BB9186 | 0 | match | 0 | 表示件数20/50/100/既定20/必須検査/SQL取得範囲、非DB保存を再現。 |
| 107 | DET-CSharp_ASPNET-SCR-STU-001-B30B1EA938EF | 0 | match | 0 | 保存番号文字列を表示/文字順、照合パターンとは別、取得型/必須/行保持を再現。 |
| 108 | DET-CSharp_ASPNET-SCR-STU-001-6B8E0F8CE3F6 | 0 | match | 0 | 登録氏名表記のまま移送、NameKeyとの区別/基表非NULL/行保持を再現。 |
| 109 | DET-CSharp_ASPNET-SCR-STU-001-B42712AE75D9 | 0 | match | 0 | 保存カナ表記を表示、照合キーと区別/基表非NULL/行保持を再現。 |
| 110 | DET-CSharp_ASPNET-SCR-STU-001-FE626D2530FC | 0 | match | 0 | dateから無時差和暦へ変換し、内部日付/表示文字列/欠損不整合を分ける。 |
| 111 | DET-CSharp_ASPNET-SCR-STU-001-36DED7C9B233 | 0 | match | 0 | 年度/学年名称LEFT JOINの移送、未所属－/欠損不整合の意図と現行表示差、行保持を再現。 |
| 112 | DET-CSharp_ASPNET-SCR-STU-001-B03C4F9CFB91 | 0 | match | 0 | class_id経由コード/名称、未所属/停止/期間外表示の意図と現行欠落、行保持を再現。 |
| 113 | DET-CSharp_ASPNET-SCR-STU-001-7AFB3215861F | 0 | match | 0 | 在籍分類と値→名称、欠落でも行保持/不整合意図と実装差を再現。 |
| 114 | DET-CSharp_ASPNET-SCR-STU-001-2287F8F28EDE | 0 | match | 0 | 都道府県名＋住所1のみ連結、住所2非表示/欠損不整合/行保持を再現。 |
| 115 | DET-CSharp_ASPNET-SCR-STU-001-8458E300284A | 0 | match | 0 | 本人電話だけ移送、null－、緊急電話を一覧へ出さず行保持を再現。 |
| 116 | DET-CSharp_ASPNET-SCR-STU-001-F7227FD532A4 | 0 | match | 0 | DB更新日時→日本時間西暦、保存時刻と表示値/行保持を区別して再現。 |
| 117 | DET-CSharp_ASPNET-SCR-STU-001-A5D22CFF7C14 | 0 | match | 0 | 固定4ソート→許可列、末尾学生ID昇順、自由列/不正指定の拒否を再現。 |
| 118 | DET-CSharp_ASPNET-SCR-STU-001-0F98A4A4A753 | 0 | match | 0 | asc/desc、asc既定、主列方向/ID昇順/不正拒否を再現。 |
| 119 | DET-CSharp_ASPNET-SCR-STU-001-297A9AA423DF | 3 | missing | 0 | typed移送/業務長/日付/接続/状態版と関連計画は詳しいが、直接正本/開発規約の入力責務と実装工程の往復/境界試験観点の契約を一式定義しない。 |

各行の現版生成/ソース/許可参考設計/原本/採点行のSHAと行範囲はJSONに保存。
このbuilderは新規手判定の保存と検証のみで、期待セルをgenerationへ渡さず原稿を組み立てない。
