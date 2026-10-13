# 新規 focus round 01 学生検索 意味評価

EVALUATOR ONLY — generation 入力不可。

新本文SHA256 `98477f6d144d445253704c2720c59d065e7614de186e425bfa8840373f0b822b`。原仕様8.0／採点表7.4／生成1.0。
source 43件・利用者承認reference 11件・候補本文・原仕様・配点行・生成prompt/resultを同じ95-pin凍結で照合した。
旧match/合格の転用なし。全120行（71有配点＋49診断）を新本文で再読した。

観測一致 117 / 147点、欠落 26点、要裁定 4点。重要な生成矛盾0件。
完了得点・完了率・95%判定はnull。これは検索1文書の部分実測である。

判定は意味単位。図の分岐は参照先と明示した設計意図も併せ、字面/番号/図存在だけでは採点していない。
画面構成は本文の設計差分表だけでは未描画の操作配置を補完しない。未実装設計意図を現行動作と偽装していない。

主な不足は画面の設計対応、名称の業務長、表示範囲、検索応答の最新要求確認、共用文書と実装試験の責務。
在籍配列の正規化と候補ERのoccupancy関係は原基準/実装または原基準内の要裁定。全原行を残す。

## 行別判定

| index | 評価ID | 配点 | 判定 | 加点 | 所見 |
| --- | --- | ---: | --- | ---: | --- |
| 0 | DET-CSharp_ASPNET-SCR-STU-001-818202EDAA7C | 3 | missing | 0 | 機能責務・読取IO・メモリを説明しているが、共用契約/DB定義/開発規約との正本責務と画像併記の契約を満たさない。draft自身も関連計画ID未供給を記録。 |
| 1 | DET-CSharp_ASPNET-SCR-STU-001-8EE9449F3E51 | 3 | missing | 0 | 描画可能な現行ソースの静的HTMLは存在する。ただし参考設計画面のメニュー・表示範囲・先頭/最後操作の配置を再現せず、差分表の語句のみで画面対応一式を代替できない。 |
| 2 | DET-CSharp_ASPNET-SCR-STU-001-85EB2FF4920B | 1 | match | 1 | 番号raw/正規化15、任意、番号形式、前方一致、保存なし、varchar15非NULLとSize31を区別して再現。 |
| 3 | DET-CSharp_ASPNET-SCR-STU-001-641EC981BB78 | 1 | match | 1 | 氏名raw8と照合キー160、保存表記との区別、部分一致、nvarchar320非NULLとSize642を再現。 |
| 4 | DET-CSharp_ASPNET-SCR-STU-001-8487A9C21424 | 1 | match | 1 | カナraw36/表記18/空白除去キー、任意、部分一致、nvarchar36非NULLとSize74を再現。 |
| 5 | DET-CSharp_ASPNET-SCR-STU-001-46AE28C86B75 | 1 | match | 1 | 年度任意・1900から9998・実在年度候補・一致条件・smallint非NULL・入力との型境界を再現。 |
| 6 | DET-CSharp_ASPNET-SCR-STU-001-7FF1B82EB5CC | 1 | match | 1 | 2桁学年・GRADE分類・停止検索可・未所属と00の区別・varchar2非NULLを再現。 |
| 7 | DET-CSharp_ASPNET-SCR-STU-001-2097E1CD5ADD | 1 | match | 1 | 19桁正Int64・任意・実在/上位一致・学生class_id bigint NULL・IDと表示名の区別を再現。 |
| 8 | DET-CSharp_ASPNET-SCR-STU-001-0D82B3220DFF | 1 | match | 1 | 未所属真偽・false初期・所属3条件排他・NULL判定・専用保存列なしを再現。 |
| 9 | DET-CSharp_ASPNET-SCR-STU-001-9C7EAABFFC27 | 1 | hold | null | 原仕様は配列にN-07を指定するが実装はOrdinalで01から04を厳密照合しNFKCしない。新版は実装を正確に記すがこの設計変換の適用を裁定しない。重複/上限/空配列の意味は確認済み。 |
| 10 | DET-CSharp_ASPNET-SCR-STU-001-BEFC3E38BC46 | 1 | match | 1 | 都道府県raw2・NFKC/ASCII2桁・PREFECTURE存在・停止許容・任意・varchar2非NULLを再現。 |
| 11 | DET-CSharp_ASPNET-SCR-STU-001-CE345AE8B601 | 1 | match | 1 | 電話raw20/保存16・空条件なし・NFKC等・本人OR緊急完全一致・二列varchar16 NULLを再現。 |
| 12 | DET-CSharp_ASPNET-SCR-STU-001-4ECDE6AD0828 | 1 | missing | 0 | 開始任意・ISO10入力・1900から業務日・片側/両端順序・date非NULL・Dateバインド・開始を含むは再現するが、入力ISOと区別した西暦表示形式の設計意図がない。ネイティブdate inputの説明を誤りとせず属性一式不足とする。 |
| 13 | DET-CSharp_ASPNET-SCR-STU-001-A3F0DF53EC17 | 1 | missing | 0 | 終了任意・開始と同じ形式/範囲・開始以下拒否・date非NULL・Dateバインド・終了を含むは再現するが、入力ISOと区別した西暦表示形式の設計意図がない。 |
| 14 | DET-CSharp_ASPNET-SCR-STU-001-14CE9B3FB604 | 1 | match | 1 | 検索受付・現在入力検査・1ページ目・成功時のみ保持・業務DB書込みなしを再現。 |
| 15 | DET-CSharp_ASPNET-SCR-STU-001-3EBF0942E20F | 1 | match | 1 | クリアはメモリ条件/結果を消去し初期値/未検索へ戻る。DB DELETEとは区別して再現。 |
| 16 | DET-CSharp_ASPNET-SCR-STU-001-29BE85CA6FA3 | 1 | match | 1 | 新規リンクはViewer非表示・入口権限確認・検索値を登録へ流用しない・遷移先責務を再現。 |
| 17 | DET-CSharp_ASPNET-SCR-STU-001-778AE19CABEA | 1 | missing | 0 | メニューという差分名だけで、共通メニューへの戻り操作/イベント/責務を定義していない。現行ソースにないことは正しく説明。 |
| 18 | DET-CSharp_ASPNET-SCR-STU-001-4C53DF730112 | 1 | missing | 0 | 件数0から10000・未検索/超過/0件を区別するが、開始/終了位置の意味と範囲0から10000の表示定義がない。 |
| 19 | DET-CSharp_ASPNET-SCR-STU-001-F3F05B9FA665 | 1 | match | 1 | サービス実行時刻・日本時間yyyy/MM/dd HH:mm:ss・未検索・保存値と表示の区別を再現。 |
| 20 | DET-CSharp_ASPNET-SCR-STU-001-45CB937AB1D9 | 1 | match | 1 | 20/50/100・既定20・入力制御/SQL取得指定・変更時1ページ・非DB保存を再現。固定候補により最大3桁が確定。 |
| 21 | DET-CSharp_ASPNET-SCR-STU-001-4BE95BEB109D | 1 | match | 1 | 保存番号varchar15非NULL・15以内・文字順・検索パターンとの区別を再現。 |
| 22 | DET-CSharp_ASPNET-SCR-STU-001-2580A923AAE8 | 1 | match | 1 | 表示氏名nvarchar16非NULLと業務8スカラー、登録表記と照合キーの区別を再現。 |
| 23 | DET-CSharp_ASPNET-SCR-STU-001-5992A6AEB5CC | 1 | match | 1 | 表示カナnvarchar36非NULLと業務18スカラー、キーと表記の区別を再現。 |
| 24 | DET-CSharp_ASPNET-SCR-STU-001-E2A700703DCF | 1 | match | 1 | 内部date非NULLから和暦表示、元年/2桁月日、時差を加えない・入力なしを再現。 |
| 25 | DET-CSharp_ASPNET-SCR-STU-001-D97621F3E369 | 1 | missing | 0 | 年度範囲/結合NULL/学年名称取得を説明するが名称の業務12スカラー上限がない。nvarchar24容量で代替しない。 |
| 26 | DET-CSharp_ASPNET-SCR-STU-001-809FC6941D89 | 1 | missing | 0 | クラスコード9・nvarchar36非NULL・結合欠損/状態差を説明するが名称18スカラー業務上限がない。 |
| 27 | DET-CSharp_ASPNET-SCR-STU-001-C241C2C610FB | 1 | missing | 0 | 分類と値のLEFT JOIN・nvarchar24非NULL・名称欠損でも行保持を説明するが名称12スカラー業務上限がない。 |
| 28 | DET-CSharp_ASPNET-SCR-STU-001-201E2ADAAED5 | 1 | missing | 0 | 住所1業務45/容量90・都道府県名連結・住所2非表示を説明するが都道府県名称12スカラー業務上限がない。 |
| 29 | DET-CSharp_ASPNET-SCR-STU-001-7B137736C1F9 | 1 | match | 1 | 本人電話のみ・varchar16 NULL・nullは－・緊急電話は検索対象だけを再現。 |
| 30 | DET-CSharp_ASPNET-SCR-STU-001-09BFD0B375D6 | 1 | match | 1 | 更新日時datetimeoffset7非NULL・日本時間19文字表示を再現。 |
| 31 | DET-CSharp_ASPNET-SCR-STU-001-9F0DF8AE8584 | 1 | match | 1 | 行番号ではなく管理ID・long/bigint・入口最新再取得/存在/権限・参照と編集の切替を再現。 |
| 32 | DET-CSharp_ASPNET-SCR-STU-001-BCAFF893A5B7 | 1 | match | 1 | 現行前後/反映と有効ページ補正を詳述し、先頭/最後は参考設計意図として区別。非DBの表示指定を再現。 |
| 33 | DET-CSharp_ASPNET-SCR-STU-001-9930CD28DA63 | 1 | match | 1 | 固定4ソート・既定番号・入力とORDER BY許可列の分離・末尾ID昇順・保存なしを再現。列挙値から上限13が確定。 |
| 34 | DET-CSharp_ASPNET-SCR-STU-001-3577E1D08486 | 1 | match | 1 | 小文字asc/desc・既定asc・非DB指定・サービス検査を再現。列挙値から最大4が確定。 |
| 35 | DET-CSharp_ASPNET-SCR-STU-001-3CA4298726C7 | 0 | missing | 0 | 検索年度の順序/停止過去/空値は記すが候補診断一式に含む登録当年度選択補助の説明がない。 |
| 36 | DET-CSharp_ASPNET-SCR-STU-001-24E04907EBCB | 0 | missing | 0 | 検索学年・停止/期間無制限・順序/00は記すが登録の新規有効値と既存値別枠保持の候補契約を記さない。 |
| 37 | DET-CSharp_ASPNET-SCR-STU-001-911C12BA9C4F | 0 | missing | 0 | 検索クラスの現在表示/抽出/順序/解除を記すが参考候補の学年名称・登録所属の3区分の定義が不足。 |
| 38 | DET-CSharp_ASPNET-SCR-STU-001-2EFE8DD8D16C | 0 | missing | 0 | 検索の01/02初期・全解除・許可4値は記すが保護コードの意味と登録新規有効値/既定01が不足。 |
| 39 | DET-CSharp_ASPNET-SCR-STU-001-3CBFA4E19E92 | 0 | missing | 0 | 検索の都道府県候補は詳しいが登録新規有効値/既存同値保持の契約が不足。 |
| 40 | DET-CSharp_ASPNET-SCR-STU-001-839BE5C68724 | 0 | match | 0 | 固定20/50/100順・20初期・変更時1ページ・コードマスタではないを再現。 |
| 41 | DET-CSharp_ASPNET-SCR-STU-001-6EB9CBF8698A | 0 | match | 0 | 固定4キーの表示と順序・番号初期・自由DB列不可を再現。 |
| 42 | DET-CSharp_ASPNET-SCR-STU-001-AE6D87D5FD40 | 0 | match | 0 | 固定asc/desc順・表示・asc初期を再現。 |
| 43 | DET-CSharp_ASPNET-SCR-STU-001-B58C16E76F3C | 0 | missing | 0 | 件数の非負/成功/未検索/超過/上限を再現するが診断束にある0件範囲0から0がない。 |
| 44 | DET-CSharp_ASPNET-SCR-STU-001-184621105C7E | 0 | missing | 0 | 開始位置の非負型/5桁/0件0/成功設定を定義していない。単に表示範囲という設計意図だけ。 |
| 45 | DET-CSharp_ASPNET-SCR-STU-001-57216B6625D4 | 0 | missing | 0 | 終了位置の非負型/5桁/0件0/成功設定を定義していない。 |
| 46 | DET-CSharp_ASPNET-SCR-STU-001-BDFBC17D956D | 0 | match | 0 | 年度int?・4桁範囲・クラス取得元・未所属－の設計意図と現行差を再現。 |
| 47 | DET-CSharp_ASPNET-SCR-STU-001-30F27E0FB66C | 0 | missing | 0 | 学年名称string?/コード名称取得元と未所属差は説明するが12スカラー上限がない。 |
| 48 | DET-CSharp_ASPNET-SCR-STU-001-8A501244EF50 | 0 | match | 0 | クラスコードstring?・9桁取得元・結合欠損でも行を落とさない・未所属の意図を再現。 |
| 49 | DET-CSharp_ASPNET-SCR-STU-001-F5E57DED2AF4 | 0 | missing | 0 | クラス名称の型/取得元/結合欠損は説明するが18スカラー上限がない。 |
| 50 | DET-CSharp_ASPNET-SCR-STU-001-5B9587C349EA | 0 | match | 0 | 必須DateOnlyの内部birth_date・ISO日付境界・和暦移送・無時差を再現。 |
| 51 | DET-CSharp_ASPNET-SCR-STU-001-D8B62A990A55 | 0 | match | 0 | 正Int64/19桁・新規対象なし・既存DB採番/行/route・権限と存在再確認を再現。 |
| 52 | DET-CSharp_ASPNET-SCR-STU-001-A9CE89C36F45 | 0 | match | 0 | 状態IDは32バイト乱数64hex、主体/セッション/タブ/期限30分と非空Tabのみという実装差を再現。 |
| 53 | DET-CSharp_ASPNET-SCR-STU-001-6AA636D6AE05 | 0 | missing | 0 | POST偽造防止の基盤検査は記すがopaque値/実値長は基盤決定事項/認可や再送制御の代替でないという診断束が不足。 |
| 54 | DET-CSharp_ASPNET-SCR-STU-001-DA1AFEB05304 | 0 | match | 0 | 初期非処理中・submit時の別ボタン非活性/aria-busy・DB排他とは別でソースの抑止限界を正しく再現。 |
| 55 | DET-CSharp_ASPNET-SCR-STU-001-D5F99F6B1962 | 0 | missing | 0 | 旧候補応答破棄の意図と要求連番未実装は記すが非負整数/初期0/桁あふれ採番停止の内部契約を定義しない。 |
| 56 | DET-CSharp_ASPNET-SCR-STU-001-2F4076F4B844 | 3 | match | 3 | 認証済み起動・学生一覧取得なし・候補取得・メニューの設計/現行差を再現。 |
| 57 | DET-CSharp_ASPNET-SCR-STU-001-CEB54B9A108C | 3 | match | 3 | 初期値・候補・状態発行/復帰・業務日時を説明。必須マスタ不足停止と応答照合を設計意図として実装と区別。 |
| 58 | DET-CSharp_ASPNET-SCR-STU-001-8B5BD3A34BD3 | 3 | match | 3 | 認証拒否/候補/未検索の図と必須マスタ不足停止の意図を組み合わせ、ソースに該当停止分岐がないことも明記する。図の存在だけではなく分岐意味を照合。 |
| 59 | DET-CSharp_ASPNET-SCR-STU-001-D7CFBCD19044 | 3 | match | 3 | 候補分類コード/学年クラスの関連・複合分類値・FKと読取JOIN/非削除連動を区別して再現。 |
| 60 | DET-CSharp_ASPNET-SCR-STU-001-C629D630F584 | 3 | match | 3 | 候補コードとクラスをSNAPSHOT二結果セットで取得し操作順と抽出/移送を詳述。表番号綴りは評価しない。 |
| 61 | DET-CSharp_ASPNET-SCR-STU-001-9C4A6F5838F0 | 3 | match | 3 | 初回は未検索/候補障害拒否、検索局所失敗と0/超過、所有権拒否、候補だけの非再検索を適用イベントごとに再現。 |
| 62 | DET-CSharp_ASPNET-SCR-STU-001-9637E6E4F65A | 3 | match | 3 | 入力条件による非削除学生検索・業務DB読取りのみを再現。 |
| 63 | DET-CSharp_ASPNET-SCR-STU-001-8C6836155E22 | 3 | missing | 0 | 複製・検証・同一検索SNAPSHOT・上限/0/初頁・保持・日付表示は説明するが、検索結果応答そのものが最新要求である確認の設計契約が候補応答だけに限定され不足。 |
| 64 | DET-CSharp_ASPNET-SCR-STU-001-69FC36696F49 | 3 | match | 3 | 入力/存在失敗・件数超過・同一読取り単位のページ経路の図を、0件emptyと日付表示の明示仕様と併せて意味照合。 |
| 65 | DET-CSharp_ASPNET-SCR-STU-001-1EA9445F88DE | 3 | match | 3 | 学生/クラス/学年/在籍/都道府県の用途alias・複合キーLEFT JOIN・NULL多重度・書込非対象を再現。 |
| 66 | DET-CSharp_ASPNET-SCR-STU-001-C8A0C07C26B8 | 3 | match | 3 | 指定マスター確認→TOP10001件数→同条件ページ取得・typed bind・commitを再現。 |
| 67 | DET-CSharp_ASPNET-SCR-STU-001-4031A7ED4200 | 3 | match | 3 | 入力保持/一覧消去の設計意図と局所適用限界、0件/超過区別、所有/版拒否、候補非再検索を再現。 |
| 68 | DET-CSharp_ASPNET-SCR-STU-001-25F8A2CE6127 | 3 | match | 3 | 所属条件連動と候補更新、まだ学生を検索しないを再現。 |
| 69 | DET-CSharp_ASPNET-SCR-STU-001-D5DBFDB9B880 | 3 | match | 3 | 未所属解除/非活性/OFF非復元、不適合解除/通知、上位補完/古い応答破棄の設計意図、未反映とApplied保持を現行差付きで再現。 |
| 70 | DET-CSharp_ASPNET-SCR-STU-001-ECF83B2057CD | 3 | match | 3 | 未所属分岐・候補取得・不適合解除/未反映の図と旧応答破棄の意図を組み合わせて意味照合。 |
| 71 | DET-CSharp_ASPNET-SCR-STU-001-2E6EC8AADACD | 3 | hold | null | 原ERはoccupancy付き学生関連だが原DB操作は検索で学生人数集計しない。実装Lookup(false)もOccupied=0。新版は未集計値と正確に記し、原仕様内のER/操作矛盾の正解を決めない。 |
| 72 | DET-CSharp_ASPNET-SCR-STU-001-E9251F3FFD1F | 3 | match | 3 | クラス候補参照・上位条件による画面絞込み・業務書込/学生検索/人数集計なしを再現。 |
| 73 | DET-CSharp_ASPNET-SCR-STU-001-8B3FD87731C8 | 3 | match | 3 | 条件原入力と既存一覧・非再検索、所有/期限拒否、検証/検索の対象外結果、実装未検査の差を明示。 |
| 74 | DET-CSharp_ASPNET-SCR-STU-001-72E55C707425 | 3 | match | 3 | Applied由来の結果を別順序/ページで再取得、未実行値を混ぜないを再現。 |
| 75 | DET-CSharp_ASPNET-SCR-STU-001-981EDBD68D75 | 3 | match | 3 | 状態/期限/版、許可表示指定、変更時1頁、同条件再検索/最終補正、0件非活性、設計期限初期化との差を再現。 |
| 76 | DET-CSharp_ASPNET-SCR-STU-001-3D1170870753 | 3 | match | 3 | 保持条件有無/拒否・許可検索条件・件数/ページ補正・全体順序取得の図と明示した共通検査を意味照合。 |
| 77 | DET-CSharp_ASPNET-SCR-STU-001-F891789D8BAE | 3 | match | 3 | ページも同じ学生/クラス/用途別コードLEFT JOINとFK/読取関係を参照し再現。 |
| 78 | DET-CSharp_ASPNET-SCR-STU-001-0DC7ABFB61F6 | 3 | match | 3 | 件数→ページ同条件の実行、補正再検索、typed offset/sizeと順序を再現。 |
| 79 | DET-CSharp_ASPNET-SCR-STU-001-FD120ACB2559 | 3 | match | 3 | ページはAppliedを保持し、局所拒否/共通障害/0/超過/候補のみ非再検索という該当結果を再現。 |
| 80 | DET-CSharp_ASPNET-SCR-STU-001-3E9561673E6C | 3 | match | 3 | 新規/行/クリア等の画面操作受付を独立イベントで再現。 |
| 81 | DET-CSharp_ASPNET-SCR-STU-001-0F958E6A35C9 | 3 | missing | 0 | 新規権限/値非流用、ID読込は遷移先、クリア状態初期化は再現するが、メニューへの戻り手順は差分名だけで操作契約を定義していない。 |
| 82 | DET-CSharp_ASPNET-SCR-STU-001-04A9D80CB796 | 3 | missing | 0 | 新規/既存/クリアのフローはあるがメニューへの遷移経路は図にも手順にもなく、差分表の話題名だけでは操作分岐意味が不足。 |
| 83 | DET-CSharp_ASPNET-SCR-STU-001-BA5C23F04C4F | 0 | match | 0 | 検索画面の遷移/状態操作に業務DB ERを作らず、遷移先LoadのDB読取と候補再描画を別責務に分類。原非適用0点を保持。 |
| 84 | DET-CSharp_ASPNET-SCR-STU-001-F4832740C697 | 3 | match | 3 | 遷移とメモリClearに業務DB更新なし・遷移先Loadと再描画候補読取を区別して再現。 |
| 85 | DET-CSharp_ASPNET-SCR-STU-001-DE44988F8890 | 3 | match | 3 | 操作対象の権限/未存在/版/候補障害と入力/0件/超過の発生対象を混同せず再現。 |
| 86 | DET-CSharp_ASPNET-SCR-STU-001-E22DC1F3ED19 | 3 | match | 3 | 登録保存/削除Savedまたは取消/戻るから元検索状態復元、成功以外の非自動帰還を再現。 |
| 87 | DET-CSharp_ASPNET-SCR-STU-001-ED6049702EC4 | 3 | match | 3 | 所有/期限/版・未検索復元・元条件の最新DB再検索・条件非変更・確定成功通知・期限初期化意図と実装拒否の差を再現。 |
| 88 | DET-CSharp_ASPNET-SCR-STU-001-4745B3118380 | 3 | match | 3 | 所有/期限拒否、検索済み分岐、元条件再検索、通知移送のフローを再現。初期化は設計意図として別記。 |
| 89 | DET-CSharp_ASPNET-SCR-STU-001-3A56EE94C8EF | 3 | match | 3 | 復帰時も一覧読取関連を共通参照し用途alias/複合分類値/NULLを再現。 |
| 90 | DET-CSharp_ASPNET-SCR-STU-001-3F24B3D24CD6 | 3 | match | 3 | 元Appliedの件数とページ再取得、同じ検索SQL・条件非変更、SQL用ページ補正を再現。 |
| 91 | DET-CSharp_ASPNET-SCR-STU-001-06F52338F30B | 3 | match | 3 | 復帰拒否/失敗・成功通知の確定と消費・0/超過/未検索・元条件維持を区別して再現。 |
| 92 | DET-CSharp_ASPNET-SCR-STU-001-4CEB20699DCB | 0 | match | 0 | 番号raw→正規化→student_no前方一致・NULL条件なし・保存なし・拒否原入力を再現。 |
| 93 | DET-CSharp_ASPNET-SCR-STU-001-304D86123D7F | 0 | match | 0 | 氏名raw8→NameKey160→name_key部分一致・表記別・NULL条件なし・拒否原入力を再現。 |
| 94 | DET-CSharp_ASPNET-SCR-STU-001-6DC80333D39F | 0 | match | 0 | カナ正規化/空白除去照合キー→kana_key部分一致・NULL条件なし・拒否原入力を再現。 |
| 95 | DET-CSharp_ASPNET-SCR-STU-001-FA1B1DEC5FC4 | 0 | match | 0 | 年度任意/int?/smallint・実在範囲/完全一致・不正拒否を再現。 |
| 96 | DET-CSharp_ASPNET-SCR-STU-001-EEA4FE49B2DD | 0 | match | 0 | NFKC2桁GRADE→grade_code完全一致・00と未所属別・空なし/拒否を再現。 |
| 97 | DET-CSharp_ASPNET-SCR-STU-001-E47A8676FF5E | 0 | match | 0 | Optional正Int64→学生class_id完全一致・NULL任意・年度学年実値一致・不正拒否を再現。 |
| 98 | DET-CSharp_ASPNET-SCR-STU-001-B44E2FCE1CFA | 0 | match | 0 | 未所属true→class_id IS NULL・false初期・所属条件排他/不正拒否を再現。 |
| 99 | DET-CSharp_ASPNET-SCR-STU-001-91FBF38A968F | 0 | hold | null | 在籍配列N-07の適用は原設計とOrdinal厳密実装の要裁定。空配列/複数IN/重複拒否は再現済み。0点診断も保留を隠さない。 |
| 100 | DET-CSharp_ASPNET-SCR-STU-001-8A43F42C52E8 | 0 | match | 0 | PREFECTURE正規化2桁→prefecture_code完全一致・任意NULL・存在/拒否を再現。 |
| 101 | DET-CSharp_ASPNET-SCR-STU-001-6DEBDB212746 | 0 | match | 0 | 正規化電話→本人または緊急二列完全一致・NULL条件なし/拒否を再現。 |
| 102 | DET-CSharp_ASPNET-SCR-STU-001-66EBD557D2C4 | 0 | match | 0 | ISO10→DateOnly?→admission_date下端を含む・任意片側・範囲/拒否を再現。 |
| 103 | DET-CSharp_ASPNET-SCR-STU-001-FA5975CE821D | 0 | match | 0 | ISO10→DateOnly?→admission_date上端を含む・任意片側・開始以下拒否を再現。 |
| 104 | DET-CSharp_ASPNET-SCR-STU-001-8BDCB190100E | 0 | missing | 0 | 件数と各結果状態は定義済みだが開始/終了位置の計算と表示移送はない。 |
| 105 | DET-CSharp_ASPNET-SCR-STU-001-F54A1A8CAD59 | 0 | match | 0 | SearchedAtの今回サービス時刻→日本時間表示・非DB保存・未検索区別を再現。 |
| 106 | DET-CSharp_ASPNET-SCR-STU-001-E8CB75BB9186 | 0 | match | 0 | 固定表示件数の入力/既定/検査/SQL範囲・非DB保存を再現。 |
| 107 | DET-CSharp_ASPNET-SCR-STU-001-B30B1EA938EF | 0 | match | 0 | 保存番号を文字列表示/文字順・照合パターンを転用しない・行を黙って落とさないを再現。 |
| 108 | DET-CSharp_ASPNET-SCR-STU-001-6B8E0F8CE3F6 | 0 | match | 0 | 登録表記のStudentName→表示・NameKeyと区別・非NULLDDL/行保持を再現。 |
| 109 | DET-CSharp_ASPNET-SCR-STU-001-B42712AE75D9 | 0 | match | 0 | 保存表記カナ→表示・KanaKeyと区別・行保持を再現。 |
| 110 | DET-CSharp_ASPNET-SCR-STU-001-FE626D2530FC | 0 | match | 0 | birth_date内部日付→無時差和暦表示・表示項目/原値分離を再現。 |
| 111 | DET-CSharp_ASPNET-SCR-STU-001-36DED7C9B233 | 0 | match | 0 | 年度/学年名称のLEFT JOIN移送と未所属－の意図、現行欠損表示差/行保持を再現。 |
| 112 | DET-CSharp_ASPNET-SCR-STU-001-B03C4F9CFB91 | 0 | match | 0 | class_id→コード/名称のLEFT JOIN移送、未所属/停止/期間外表示の意図と現行注記欠落を再現。 |
| 113 | DET-CSharp_ASPNET-SCR-STU-001-7AFB3215861F | 0 | match | 0 | 分類と値→在籍名、名称欠落でも学生行を除外しないを再現。 |
| 114 | DET-CSharp_ASPNET-SCR-STU-001-2287F8F28EDE | 0 | match | 0 | 都道府県名+住所1のみ連結・住所2なし・欠損[不整合]・行保持を再現。 |
| 115 | DET-CSharp_ASPNET-SCR-STU-001-8458E300284A | 0 | match | 0 | 本人電話のみ移送・null－・緊急電話非表示を再現。 |
| 116 | DET-CSharp_ASPNET-SCR-STU-001-F7227FD532A4 | 0 | match | 0 | DB更新日時→日本時間西暦表示・保存元と表示値を分離して再現。 |
| 117 | DET-CSharp_ASPNET-SCR-STU-001-A5D22CFF7C14 | 0 | match | 0 | 固定4ソート→許可列・最後のID昇順・不正拒否を再現。 |
| 118 | DET-CSharp_ASPNET-SCR-STU-001-0F98A4A4A753 | 0 | match | 0 | asc/desc・asc既定→主列方向・不正拒否を再現。 |
| 119 | DET-CSharp_ASPNET-SCR-STU-001-297A9AA423DF | 3 | missing | 0 | 移送/型/長さ/接続/状態版の説明は詳しいが開発入力の正本責務・共用仕様/DB/開発規約との参照契約と実装工程の試験観点を定義していない。 |

各行の生成/原本/採点表/ソースのSHA256付き行範囲は search-evaluation.json に記録。
build_search_evaluation.py はこの手判定の保存・証拠参照・算術だけを行い、AI原稿の組立てやキーワード採点を行わない。
