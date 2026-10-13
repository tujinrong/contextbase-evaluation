# Focus round 04 学生検索 独立意味評価

EVALUATOR ONLY — generation入力不可。

生成4.0 SHA256 `35defbc0495678f32ec140535d46e96bbfda0e66259aac13982a6cf28b0e41c0`。原仕様8.0／採点表7.4。
source43・許可reference11・起動runtime13・新raw prompt/result/answer/schemaを固定。旧採点転用なし。
全120行（有配点71＋診断49）、観測一致133/147点、不足10点、矛盾0点、保留4点。
重大矛盾0件。完了得点・完了率・95%判定はnull。

全判定と現版根拠は下の行別表を参照。生成・ソース・設計意図を分け、旧判定の転用を行わない。
在籍配列正規化と候補ER/人数操作の矛盾は原基準の要裁定として全行を残す。

| index | 評価ID | 配点 | 判定 | 加点 | 所見 |
| --- | --- | ---: | --- | ---: | --- |
| 0 | DET-CSharp_ASPNET-SCR-STU-001-818202EDAA7C | 3 | missing | 0 | 検索の物理責務と参照経路は詳しいが、本画面を正本とする具体契約と共通実装・DB定義・命名配備規約への責務配置を一式には説明していない。計画IDと責務名の列挙だけで原概要全体の再現としない。 |
| 1 | DET-CSharp_ASPNET-SCR-STU-001-8EE9449F3E51 | 3 | missing | 0 | 現行ソース投影の入力・モード・候補・メッセージ・一覧は具体的である。一方、原設計画面にある表示範囲、メニュー、先頭最後操作を設計意図として比較するだけで、その画面構造をレイアウトには再現していない。出自の分離は正しく、意味不足を記録する。 |
| 2 | DET-CSharp_ASPNET-SCR-STU-001-85EB2FF4920B | 1 | match | 1 | 学籍番号の任意条件、空初期、rawと正規化の15スカラー上限、番号形式、前方一致、DB型と必須列、文字入力とサービス条件の移送を合わせて再現する。保存の完全番号と検索前方条件を混同しない。 |
| 3 | DET-CSharp_ASPNET-SCR-STU-001-641EC981BB78 | 1 | match | 1 | 氏名のraw8と照合キー160、NFKC大文字空白除去、部分一致、表示氏名との別領域、DB容量とNULL属性、空初期と任意条件を再現する。HTML16は業務8と別に扱う。 |
| 4 | DET-CSharp_ASPNET-SCR-STU-001-8487A9C21424 | 1 | match | 1 | カナの任意入力、raw36から変換後18、許可カナと照合用空白除去、部分一致、DB36容量とNOT NULL、入力と保存側必須の違いを再現する。 |
| 5 | DET-CSharp_ASPNET-SCR-STU-001-46AE28C86B75 | 1 | match | 1 | 年度のすべて初期と未指定、1900～9998、候補存在、nullable整数の移送、所属クラス年度への完全一致とSmallIntを再現する。年度0を未設定にしない。 |
| 6 | DET-CSharp_ASPNET-SCR-STU-001-7FF1B82EB5CC | 1 | match | 1 | 学年のすべて、任意空NULL、数字2桁への正規化、GRADE存在、停止候補と00実コード、クラスの学年列とVarChar2を再現し、未所属とは分ける。 |
| 7 | DET-CSharp_ASPNET-SCR-STU-001-2097E1CD5ADD | 1 | match | 1 | クラスの未指定と正Int64、19桁受信境界、実在と指定年度学年照合、nullable学生所属列、候補IDと完全一致BigIntを再現する。上位条件照合はクラス実値で行う。 |
| 8 | DET-CSharp_ASPNET-SCR-STU-001-0D82B3220DFF | 1 | match | 1 | 未所属false初期、真偽入力、class_id NULL検索と所属条件排他を再現する。ブラウザー解除と再描画disabledの違い、OFFで以前値を戻さない設計意図を明示する。 |
| 9 | DET-CSharp_ASPNET-SCR-STU-001-9C7EAABFFC27 | 1 | hold | null | 在籍の初期01・02、空配列全区分、最大4値と重複拒否は再読できる。原属性の正規化N-07と現行のOrdinal固定値検査には正解未裁定の差があるため、原1点を保留し新本文の事実誤りとはしない。 |
| 10 | DET-CSharp_ASPNET-SCR-STU-001-BEFC3E38BC46 | 1 | match | 1 | 都道府県のすべてと任意NULL、2桁正規化、分類付き存在、停止候補、学生prefecture_code完全一致、VarChar2とNOT NULLを再現する。 |
| 11 | DET-CSharp_ASPNET-SCR-STU-001-CE345AE8B601 | 1 | match | 1 | 電話raw20と変換後最大16、Unicode正規化と国内国際形式、空初期・任意NULL、本人または緊急電話の完全一致、双方のnullable列とVarChar16を再現する。 |
| 12 | DET-CSharp_ASPNET-SCR-STU-001-4ECDE6AD0828 | 1 | match | 1 | 入学日開始の任意片側条件、1900から業務日、日付型への厳密変換、開始を含むDate比較と必須保存列を再現する。参考設計の表示書式とISO入力を、現行native dateの表示未固定と分ける。 |
| 13 | DET-CSharp_ASPNET-SCR-STU-001-A3F0DF53EC17 | 1 | match | 1 | 入学日終了の任意片側条件、共通範囲、両端逆転拒否、終了を含むDate比較、保存列NOT NULLを再現する。表示とISO受信を設計意図と現行部品で区別する。 |
| 14 | DET-CSharp_ASPNET-SCR-STU-001-14CE9B3FB604 | 1 | match | 1 | 検索操作は今回条件を検査しPage1で取得する。条件フォームの入力と結果表示、学生参照と状態保持、非保存を手順まで具体化する。 |
| 15 | DET-CSharp_ASPNET-SCR-STU-001-3EBF0942E20F | 1 | match | 1 | 原行はクリアである。独立フォームとContextRequest、初期01・02と未検索への復元、Applied・LastResult消去、同じID維持とDB削除なしを再現する。Optionsや新規への説明を根拠にしない。 |
| 16 | DET-CSharp_ASPNET-SCR-STU-001-29BE85CA6FA3 | 1 | match | 1 | 原行は新規登録である。Viewer非表示と入口作成権限、GET新規入口、検索条件を登録値へ転記しない遷移、登録側責務を再現する。クリアの根拠とは区別する。 |
| 17 | DET-CSharp_ASPNET-SCR-STU-001-778AE19CABEA | 1 | match | 1 | メニューへの操作を参考設計の意図として示し、現行ビューに専用操作・遷移URLがないことを明示する。機能内で業務DBを書かない範囲を合わせて読め、架空の接続済みMenuを主張していない。 |
| 18 | DET-CSharp_ASPNET-SCR-STU-001-4C53DF730112 | 1 | missing | 0 | 件数と未検索・0件・超過は再現する。RangeFrom・RangeToは設計意図と現行不在を示すが、両範囲値の型・全許容範囲・成功時と欠損時の契約を属性一式として具体化していない。 |
| 19 | DET-CSharp_ASPNET-SCR-STU-001-F3F05B9FA665 | 1 | match | 1 | 検索入口の実行時刻から日本時間19文字の検索日時へ移し、保存しない表示値と未検索NULLを区別する。found以外の実表示の違いも明示する。 |
| 20 | DET-CSharp_ASPNET-SCR-STU-001-45CB937AB1D9 | 1 | match | 1 | 表示件数の固定20・50・100、初期20、許可外拒否、数値制御と非DB保存、Page変更時の1ページ化、取得Sizeと受信条件の分離を再現する。 |
| 21 | DET-CSharp_ASPNET-SCR-STU-001-4BE95BEB109D | 1 | match | 1 | 表示番号は保存済みstudent_no文字列、15とVarChar15の必須列で、キーやLIKE表現ではない。未検索一覧、表示専用DTO、欠損設計意図と現行の違いを合わせて再現する。 |
| 22 | DET-CSharp_ASPNET-SCR-STU-001-2580A923AAE8 | 1 | match | 1 | 表示氏名は登録表記とDTO文字列、業務8とDB16、NOT NULL、未検索一覧を再現する。name_keyの検索・並び替えとは分離する。 |
| 23 | DET-CSharp_ASPNET-SCR-STU-001-5992A6AEB5CC | 1 | match | 1 | 表示カナは保存表記とDTO、18とDB36、NOT NULL、未検索の空一覧を再現する。照合kana_keyは非表示である。 |
| 24 | DET-CSharp_ASPNET-SCR-STU-001-E2A700703DCF | 1 | match | 1 | 表示生年月日は必須内部dateから和暦へ移し、元年と2桁月日、非入力・時差なしを再現する。生年月日の内部値を一覧応答へそのまま出さない。 |
| 25 | DET-CSharp_ASPNET-SCR-STU-001-D97621F3E369 | 1 | match | 1 | 年度は所属クラスの整数、学年はGRADE名称で、年度範囲と名称12、基表smallintとnvarchar24、JOIN後NULLを再現する。未所属の－という設計意図と現行の補完なしを区別する。 |
| 26 | DET-CSharp_ASPNET-SCR-STU-001-809FC6941D89 | 1 | match | 1 | クラスコード9・名称18の保存側業務上限とDB容量、列とDTOの移送、NULL結合、学生行保持を再現する。停止期間外の設計注記と現行一覧に未取得の状態を比較する。 |
| 27 | DET-CSharp_ASPNET-SCR-STU-001-C241C2C610FB | 1 | match | 1 | 在籍は分類と値で名称へ結合し、名称12とDB24、基表NOT NULLとJOIN NULLを分ける。名称欠落だけで学生を除外しない表示責務を再現する。 |
| 28 | DET-CSharp_ASPNET-SCR-STU-001-201E2ADAAED5 | 1 | match | 1 | 住所は都道府県名称12と住所1の45、各DB容量と必須性から算出する表示値である。住所2を出さず、名称NULL時の不整合を明示する。 |
| 29 | DET-CSharp_ASPNET-SCR-STU-001-7B137736C1F9 | 1 | match | 1 | 本人電話の保存列とDTO、最大16とnullable VarChar16、未設定－を再現する。検索が緊急電話へ一致しても、一覧へ緊急電話は出さない。 |
| 30 | DET-CSharp_ASPNET-SCR-STU-001-09BFD0B375D6 | 1 | match | 1 | 更新日時はDB datetimeoffsetとUTC管理値から日本時間19文字へ変換する表示DTOで、日時文字列自体をDB保存しない。未検索時は一覧を出さない。 |
| 31 | DET-CSharp_ASPNET-SCR-STU-001-9F0DF8AE8584 | 1 | match | 1 | 行の編集参照は学生IDの文字列をリンクへ使い、Viewer参照と他権限編集を区別する。遷移先で最新対象を取得し、行番号・表示値を対象IDにしない。 |
| 32 | DET-CSharp_ASPNET-SCR-STU-001-BCAFF893A5B7 | 1 | match | 1 | ページは未検索非活性、要求PageとPageSizeによる範囲取得、変更時Page1、最終有効ページ補正を再現する。先頭最後の設計意図と現行前後ボタンとの差を明示する。 |
| 33 | DET-CSharp_ASPNET-SCR-STU-001-9930CD28DA63 | 1 | match | 1 | 並び順は固定4キーを選択し、初期studentNo、許可列switchと主ソート、常に学生ID昇順を添える。自由なDB列名や保存値として扱わない。 |
| 34 | DET-CSharp_ASPNET-SCR-STU-001-3577E1D08486 | 1 | match | 1 | 方向は初期asc、固定小文字asc・descだけを許し、検査済み方向で全集合をソートする非保存指定である。方向変更でPage1へ戻る。 |
| 35 | DET-CSharp_ASPNET-SCR-STU-001-3CA4298726C7 | 0 | missing | 0 | 検索年度の生成元・範囲・降順・すべてと候補0件は具体的である。原候補行に含まれる登録当年度の選択補助と新規初期を、本書の共有候補契約には具体化していない。0点診断を残す。 |
| 36 | DET-CSharp_ASPNET-SCR-STU-001-24E04907EBCB | 0 | missing | 0 | 検索GRADEの分類・順序・00・停止許容を再現する。登録新規有効値と既存値別枠保持の属性一式は、保存側再検査の一般説明に留まり共有候補契約として不足する。 |
| 37 | DET-CSharp_ASPNET-SCR-STU-001-911C12BA9C4F | 0 | missing | 0 | 検索クラスの順序・条件・停止・上位不適合解除と登録人数集計の区別は正しい。登録の新規所属・最終所属・既存保持の全条件と新規未選択を一式には説明していない。 |
| 38 | DET-CSharp_ASPNET-SCR-STU-001-2EFE8DD8D16C | 0 | missing | 0 | 検索在籍の分類、順序、初期01・02と全解除は再現する。原共有候補行の新規登録初期01・保護値・有効新規選択までを本書では具体化していない。 |
| 39 | DET-CSharp_ASPNET-SCR-STU-001-3CBFA4E19E92 | 0 | missing | 0 | 検索都道府県の分類・順序・すべて・停止許容は具体的である。登録新規未選択と有効新規・既存同値保持までの属性一式は不足する。 |
| 40 | DET-CSharp_ASPNET-SCR-STU-001-839BE5C68724 | 0 | match | 0 | 表示件数はビュー固定3候補と順序、初期20、業務コードでなくPageで反映し変更時Page1という候補診断を再現する。 |
| 41 | DET-CSharp_ASPNET-SCR-STU-001-6EB9CBF8698A | 0 | match | 0 | 並び順候補の4キー・4ラベル・順序・初期と許可列対応を示し、自由列名を受付けない候補契約を再現する。 |
| 42 | DET-CSharp_ASPNET-SCR-STU-001-AE6D87D5FD40 | 0 | match | 0 | 昇降順の固定2値、順序とラベル、初期asc、大文字拒否を再現する。DB業務コードではない。 |
| 43 | DET-CSharp_ASPNET-SCR-STU-001-B58C16E76F3C | 0 | match | 0 | 件数は非負整数のCountと件数SQLから最大10000の実数を移し、未検索・超過NULLと0件0を分ける。表示件数や範囲0～0とは別という設計意図も記録する。 |
| 44 | DET-CSharp_ASPNET-SCR-STU-001-184621105C7E | 0 | missing | 0 | 開始位置RangeFromと0件0～0の設計意図はあるが、型・最大範囲・成功時設定元・未検索超過未設定までの内部項目属性を具体化していない。現行の不在説明だけで一致としない。 |
| 45 | DET-CSharp_ASPNET-SCR-STU-001-57216B6625D4 | 0 | missing | 0 | 終了位置RangeToと0件0～0の設計意図はあるが、型・最大範囲・成功時設定元・未検索超過未設定までの内部項目属性を具体化していない。 |
| 46 | DET-CSharp_ASPNET-SCR-STU-001-BDFBC17D956D | 0 | match | 0 | 一覧年度のnullable整数、クラス年度列、1900～9998の西暦範囲と未所属の設計表示を再現する。現行の専用補完なしを区別する。 |
| 47 | DET-CSharp_ASPNET-SCR-STU-001-30F27E0FB66C | 0 | match | 0 | 学年名の文字列、GRADE名称、業務12と表示専用の移送、未所属設計表示と現行NULLを区別して内部項目を再現する。 |
| 48 | DET-CSharp_ASPNET-SCR-STU-001-8A501244EF50 | 0 | match | 0 | クラスコードの文字列、9文字、m_class設定元と一覧への移送、外部結合で学生行を残すこと、未所属表示意図を再現する。 |
| 49 | DET-CSharp_ASPNET-SCR-STU-001-F5E57DED2AF4 | 0 | match | 0 | クラス名称の文字列、18文字、m_class設定元と一覧への移送、名称欠落で学生行を消さないこと、停止期間外表示の責務差を再現する。 |
| 50 | DET-CSharp_ASPNET-SCR-STU-001-5B9587C349EA | 0 | match | 0 | 内部生年月日のDB date必須列、DateOnlyから和暦文字列への移送、非入力・時差なしを再現する。nullable設計名を保存時任意と読み替えない。 |
| 51 | DET-CSharp_ASPNET-SCR-STU-001-D8B62A990A55 | 0 | match | 0 | 学生IDはbigint採番からlongと十進文字列へ移し、既存ルートを最新取得する。新規対象なし、正対象の読込み、行番号非使用と権限存在再確認を再現する。 |
| 52 | DET-CSharp_ASPNET-SCR-STU-001-A9CE89C36F45 | 0 | match | 0 | ContextIdの64hex乱数と文字列、初回未発行、利用時の主体・セッション・指定画面・30分を再現する。Tab条件付き照合と復帰未指定を設計意図から区別する。 |
| 53 | DET-CSharp_ASPNET-SCR-STU-001-6AA636D6AE05 | 0 | missing | 0 | CSRF生成・MVC検査、状態版や認証の代替でないことは明確である。内部項目としてのopaque文字列と実値長の決定責務を一式には示していない。 |
| 54 | DET-CSharp_ASPNET-SCR-STU-001-DA1AFEB05304 | 0 | missing | 0 | submitとaria-busy、抑止範囲の実動作は詳しい。原内部項目の真偽IsBusy、false初期、開始終了による自動設定という型・初期・ライフサイクルは設計意図としても具体化していない。 |
| 55 | DET-CSharp_ASPNET-SCR-STU-001-D5F99F6B1962 | 0 | missing | 0 | RequestSequence初期0・旧応答破棄・桁あふれ停止の意図と現行未接続は示す。非負整数という型、非同期要求で画面内要求連番を設定する内部項目契約が一式では不足する。 |
| 56 | DET-CSharp_ASPNET-SCR-STU-001-2F4076F4B844 | 3 | match | 3 | 初回認証済みGETで未検索と候補を作り学生一覧検索はしない。状態付き起動はResumeへ分岐し、初回の目的と対象を再現する。 |
| 57 | DET-CSharp_ASPNET-SCR-STU-001-CEB54B9A108C | 3 | match | 3 | 初回認証・新Entry・候補と初期01・02・20件・番号昇順・未検索を順に具体化する。必須候補不足の設計禁止と現行ボタン未禁止、要求世代設計と現行を分ける。 |
| 58 | DET-CSharp_ASPNET-SCR-STU-001-8B5BD3A34BD3 | 3 | match | 3 | 初回／復帰分岐、認証、初期未検索、候補、描画と例外の図を示す。設計の必須候補判定が現行にないことも説明し、図存在だけで一致としない。 |
| 59 | DET-CSharp_ASPNET-SCR-STU-001-D7CFBCD19044 | 3 | match | 3 | 初回候補は分類とコード、クラスと学年コードの参照辺を使い、物理FKと用途JOIN、外部結合・名称欠落・非書込みを区別してER材料を再現する。 |
| 60 | DET-CSharp_ASPNET-SCR-STU-001-C629D630F584 | 3 | match | 3 | コード分類JOINとクラス候補の二結果セット、順序・型・学生人数未集計、同一SNAPSHOT参照とcommitを具体化し、初回OP-CODE/CLASS相当を再現する。 |
| 61 | DET-CSharp_ASPNET-SCR-STU-001-9C4A6F5838F0 | 3 | match | 3 | 初回に発生する認証・候補・描画拒否と未検索操作制御を示す。非実行の検索結果を初回へ適用せず、候補不足の設計結果と現行を区別する。 |
| 62 | DET-CSharp_ASPNET-SCR-STU-001-9637E6E4F65A | 3 | match | 3 | 指定された今回条件で非削除学生を検索する目的、Page1、成功条件保持と0件超過成功を具体化して処理概要を再現する。 |
| 63 | DET-CSharp_ASPNET-SCR-STU-001-8C6836155E22 | 3 | match | 3 | 入力の受信・移送・検査・存在整合、同条件の件数一覧、上限0件、成功条件保持と日付表示を具体化する。引数複製と設計上の旧応答破棄を現行状態版と別に照合する。 |
| 64 | DET-CSharp_ASPNET-SCR-STU-001-69FC36696F49 | 3 | match | 3 | 入力拒否から検索、10001超過・0件・found、状態確定と表示の条件フローを示す。422検証と403/409状態拒否、SQL取消、後段障害を合流点の固定状態にせず区別する。 |
| 65 | DET-CSharp_ASPNET-SCR-STU-001-1EA9445F88DE | 3 | match | 3 | 学生クラスとGRADE・在籍・都道府県の分類値JOINを示し、COUNTと一覧の辺、FKと読取り関係、外部結合による名称欠落保持を再現する。 |
| 66 | DET-CSharp_ASPNET-SCR-STU-001-C8A0C07C26B8 | 3 | match | 3 | 指定マスターの用途別確認、完全番号存在確認非適用、同一SNAPSHOTのCOUNT/PAGE、全述語・型付き値・上限・並び順・ページと取得列を再現する。 |
| 67 | DET-CSharp_ASPNET-SCR-STU-001-4031A7ED4200 | 3 | match | 3 | 検索入力エラー・0件・超過・所有者拒否・システム例外を具体化する。局所再表示の入力と空一覧、残るLastResult、後段失敗の状態非復元を設計意図と区別する。 |
| 68 | DET-CSharp_ASPNET-SCR-STU-001-25F8A2CE6127 | 3 | match | 3 | 年度学年クラス未所属の条件変更は検索実行と別で、候補と今回入力の再表示、未反映通知、成功済み一覧維持を再現する。 |
| 69 | DET-CSharp_ASPNET-SCR-STU-001-D5DBFDB9B880 | 3 | match | 3 | 未所属解除と非活性、OFF非復元、上位に不適合なクラス解除、クラス先行補完と旧応答破棄の設計意図を現行未接続から区別し、Options手順を具体化する。 |
| 70 | DET-CSharp_ASPNET-SCR-STU-001-ECF83B2057CD | 3 | match | 3 | 未所属の分岐、候補取得、クラス適合判定と解除通知、今回条件未反映と一覧維持のフローを再現する。ブラウザー補助・旧応答破棄設計・通常POSTを混同しない。 |
| 71 | DET-CSharp_ASPNET-SCR-STU-001-2E6EC8AADACD | 3 | hold | null | 新本文は検索候補で人数を集計しない読取関連を正しく示す。原の候補ERに人数の学生辺があり、同じ原OP-CLASS定義は検索人数集計なしとするため、原FLOWではなく本ER行3点を未裁定として保留する。 |
| 72 | DET-CSharp_ASPNET-SCR-STU-001-E9251F3FFD1F | 3 | match | 3 | 検索候補OP-CLASS相当の対象・完全順序・人数なしと参照確定、上位条件はSQLへ渡さず取得後に抽出する実装差を説明する。学生件数検索と書込みは実行しない。 |
| 73 | DET-CSharp_ASPNET-SCR-STU-001-8B3FD87731C8 | 3 | match | 3 | 候補変更だけで学生再検索しない、LastResult維持と未反映・不適合解除通知を再現する。OptionsのModelState非停止と局所catchなしを明示し、実行していない0件検索分岐を付加しない。 |
| 74 | DET-CSharp_ASPNET-SCR-STU-001-72E55C707425 | 3 | match | 3 | ページ・並び替えは最後のAppliedを深く複製し、未実行条件を混ぜず、表示指定変更ならPage1を使う。原の処理目的を具体化する。 |
| 75 | DET-CSharp_ASPNET-SCR-STU-001-981EDBD68D75 | 3 | match | 3 | 状態の所有期限版と未検索拒否、許可表示指定、保持条件COUNT/PAGE、件数減少補正と0件操作を手順として再現する。別SNAPSHOTの第2検索まで境界を説明する。 |
| 76 | DET-CSharp_ASPNET-SCR-STU-001-3D1170870753 | 3 | match | 3 | 第4稿のPage図は所有403・状態409と検証422のe.Statusを保持し、SQL障害・Gate待機取消を別にする。保持条件、補正、再検索、状態更新と再表示を全経路で具体化する。 |
| 77 | DET-CSharp_ASPNET-SCR-STU-001-F891789D8BAE | 3 | match | 3 | ページの件数学生クラス辺と一覧3用途コード辺を、同条件のQ-Sと別候補Q-Lに対応させる。物理FKと検索JOIN、非更新を再現する。 |
| 78 | DET-CSharp_ASPNET-SCR-STU-001-0DC7ABFB61F6 | 3 | match | 3 | 保持条件のCOUNTとPAGE、最大件数・許可順序・IDtie-break・ページ補正・取得項目を具体化する。一回の読取り整合性と補正の別検索を区別し、架空の全体同一Txを主張しない。 |
| 79 | DET-CSharp_ASPNET-SCR-STU-001-FD120ACB2559 | 3 | match | 3 | Page拒否の元状態、Applied由来入力と空一覧、ModelStateと後段再構築・描画の範囲、旧結果保持を説明する。今回未実行条件と保持条件の責務を分け、0件超過・期限拒否も対応する。 |
| 80 | DET-CSharp_ASPNET-SCR-STU-001-3E9561673E6C | 3 | match | 3 | 行操作、新規、クリアとメニュー設計意図の対象を具体化する。登録入口へ移す操作と検索状態を初期化する操作を別責務として読み取れる。 |
| 81 | DET-CSharp_ASPNET-SCR-STU-001-0F958E6A35C9 | 3 | match | 3 | 新規作成権限と登録条件非流用、既存学生IDによる登録側取得、クリアの初期未検索化を手順で再現する。メニュー移動の参考設計意図と現行専用入口不在を分けて示す。 |
| 82 | DET-CSharp_ASPNET-SCR-STU-001-04A9D80CB796 | 3 | match | 3 | クリア図と新規・既存図を合わせ、権限確認、学生IDで登録へ、初期条件未検索の各分岐を再現する。メニューについては設計上の操作と現行不在を本文で補い、接続済み図の枝を捏造しない。 |
| 83 | DET-CSharp_ASPNET-SCR-STU-001-BA5C23F04C4F | 0 | match | 0 | クリアと遷移制御自体に業務DBの書込みERを作らず、メモリ消去と登録側読込みを分離する。再描画候補と登録側集計の実ソース読取りは別に明示している。 |
| 84 | DET-CSharp_ASPNET-SCR-STU-001-F4832740C697 | 3 | match | 3 | 遷移の学生読込みは登録側責務、クリアの消去はメモリで業務表を読書きする消去ではない。後続候補SQLと登録読込みを当該制御のDB更新に読み替えない。 |
| 85 | DET-CSharp_ASPNET-SCR-STU-001-DE44988F8890 | 3 | match | 3 | 操作ごとの認証・作成権限・対象不在・状態拒否と初期化結果を明示する。新規やクリアへ未実行の検索結果状態を付加せず、登録の読込と入力取消を区別する。 |
| 86 | DET-CSharp_ASPNET-SCR-STU-001-E22DC1F3ED19 | 3 | match | 3 | 保存削除の確定復帰と保存しない戻り、未検索または元条件再検索の対象・目的を再現する。取消の現行Edit滞在と復帰リンクを区別する。 |
| 87 | DET-CSharp_ASPNET-SCR-STU-001-ED6049702EC4 | 3 | match | 3 | 所有認証期限版、未検索復元か元条件COUNT/PAGE、確定通知だけをTake、条件外学生を追加しない手順を再現する。期限初期化・Tab照合の設計と現行差も説明する。 |
| 88 | DET-CSharp_ASPNET-SCR-STU-001-4745B3118380 | 3 | match | 3 | 復帰の所有状態検査、検索済み分岐、元条件再検索と確定通知、未検索復元の図と例外を再現する。Take後表示障害と提示ページ差を成功保証へまとめない。 |
| 89 | DET-CSharp_ASPNET-SCR-STU-001-3A56EE94C8EF | 3 | match | 3 | 復帰検索の学生クラスと3用途コード、分類値外部結合と学生行保持をQ-S図へ対応し、別候補読取とメモリ状態通知を区別する。 |
| 90 | DET-CSharp_ASPNET-SCR-STU-001-3F24B3D24CD6 | 3 | match | 3 | 元AppliedによるCOUNT/PAGEの同条件検索、最新非削除集合と読取commit、未検索では検索なしを再現する。条件外保存学生追加なしと保持ページ非補正の実装差を説明する。 |
| 91 | DET-CSharp_ASPNET-SCR-STU-001-06F52338F30B | 3 | match | 3 | 他者旧版期限の拒否、局所catchなし、未検索／検索済みと通知消費、条件不変更を再現する。確定済DB書込みと303・復帰HTMLの到達を区別し、未知結果を成功通知にしない。 |
| 92 | DET-CSharp_ASPNET-SCR-STU-001-4CEB20699DCB | 0 | match | 0 | 番号の画面入力からサービス値とstudent_no前方条件への移送、任意NULL、番号正規化と型付き送信、入力エラーの原入力材料とDB検索前拒否を再現する。 |
| 93 | DET-CSharp_ASPNET-SCR-STU-001-304D86123D7F | 0 | match | 0 | 氏名raw入力からNameKey相当の照合値、name_key部分一致と任意NULL、正規化・非表示キー、入力失敗再表示とDB処理なしを再現する。 |
| 94 | DET-CSharp_ASPNET-SCR-STU-001-6DC80333D39F | 0 | match | 0 | カナ入力から正規化照合キー、kana_key部分一致、任意省略とraw変換値の区別、入力エラー材料と検索前拒否を再現する。 |
| 95 | DET-CSharp_ASPNET-SCR-STU-001-FA1B1DEC5FC4 | 0 | match | 0 | 年度をint?へ移し、1900～9998・候補存在後にm_class.school_year完全一致SmallIntで使う。未指定NULLと変換・検査失敗を区別する。 |
| 96 | DET-CSharp_ASPNET-SCR-STU-001-EEA4FE49B2DD | 0 | match | 0 | 学年の任意空と2桁正規化をクラス学年の完全一致へ移し、学年なし00と未所属を分離する。失敗の原入力材料とDB検索前拒否を再現する。 |
| 97 | DET-CSharp_ASPNET-SCR-STU-001-E47A8676FF5E | 0 | match | 0 | クラスrawから正long?、所属列完全一致、指定年度学年の実値照合、未指定NULLを再現する。ID変換エラーを0やNULL条件として検索しない。 |
| 98 | DET-CSharp_ASPNET-SCR-STU-001-B44E2FCE1CFA | 0 | match | 0 | 未所属trueのclass_id IS NULL、所属3条件との排他、チェック配列と画面状態、Options解除とSearch拒否の違いを再現する。 |
| 99 | DET-CSharp_ASPNET-SCR-STU-001-91FBF38A968F | 0 | hold | null | 在籍配列の空全区分とIN移送、最大4件と重複拒否は具体的である。原移送N-07と現行の未正規化Ordinal検査の裁定がないため、この0点診断行もhold/nullで残す。 |
| 100 | DET-CSharp_ASPNET-SCR-STU-001-8A43F42C52E8 | 0 | match | 0 | 都道府県を任意NULLと2桁正規化後の分類付き値からprefecture_code完全一致へ移し、表示住所検索と混同しない。入力失敗でDB検索をしない。 |
| 101 | DET-CSharp_ASPNET-SCR-STU-001-6DEBDB212746 | 0 | match | 0 | 電話raw・正規化後値から本人または緊急列の完全一致へ移し、任意NULLと入力失敗再表示、検索前拒否を再現する。表示本人電話とは分ける。 |
| 102 | DET-CSharp_ASPNET-SCR-STU-001-66EBD557D2C4 | 0 | match | 0 | 開始日の任意stringから厳密DateOnly?とSQL Date、開始包含、片側指定、未指定NULLを再現する。入力不正をNULL条件へ黙って変換しない。 |
| 103 | DET-CSharp_ASPNET-SCR-STU-001-FA5975CE821D | 0 | match | 0 | 終了日の任意stringからDateOnly?とSQL Date、終了包含、両端逆転拒否と未指定NULL、検索前拒否を再現する。 |
| 104 | DET-CSharp_ASPNET-SCR-STU-001-8BDCB190100E | 0 | missing | 0 | 件数SQLとtotalCount出力、未検索0件超過の違いは追える。設計RangeFrom/Toの成功時出力元と欠損時移送契約は具体化されず、現行不在という説明だけで全移送属性は満たさない。 |
| 105 | DET-CSharp_ASPNET-SCR-STU-001-F54A1A8CAD59 | 0 | match | 0 | 検索入口実行時刻から日本時間表示文字列への出力、DB保存なしと未検索NULL、foundだけ本文表示する現行差を再現する。 |
| 106 | DET-CSharp_ASPNET-SCR-STU-001-E8CB75BB9186 | 0 | match | 0 | 表示件数の受信・型・許可20/50/100・既定20・非保存と取得範囲指定、変換検査失敗と再表示の責務差を再現する。 |
| 107 | DET-CSharp_ASPNET-SCR-STU-001-B30B1EA938EF | 0 | match | 0 | 学籍番号は保存文字列から一覧DTOへ移し、検索パターンを表示せず、保存文字順でソートする。表示入力対象外と学生行保持を再現する。 |
| 108 | DET-CSharp_ASPNET-SCR-STU-001-6B8E0F8CE3F6 | 0 | match | 0 | 氏名は保存表記からStudentRowとstudentNameへ移し、照合name_keyを一覧へ出さない。表示欠損設計と現行必須列を区別する。 |
| 109 | DET-CSharp_ASPNET-SCR-STU-001-B42712AE75D9 | 0 | match | 0 | 保存カナ表記を一覧へ移す出力で、検索kana_keyは非表示である。入力項目と表示DTOの役割を分離する。 |
| 110 | DET-CSharp_ASPNET-SCR-STU-001-FE626D2530FC | 0 | match | 0 | 内部birth_dateから和暦表示DTOへ移し、年月日書式と時差なし、一覧での非入力を再現する。生dateを公開一覧へ出すものではない。 |
| 111 | DET-CSharp_ASPNET-SCR-STU-001-36DED7C9B233 | 0 | match | 0 | クラス年度とGRADE名称を一覧複合項目へ移し、学年コードの保存値と名称を分ける。未所属の設計－と現行JOIN NULLを区別し、学生行を無言で落とさない。 |
| 112 | DET-CSharp_ASPNET-SCR-STU-001-B03C4F9CFB91 | 0 | match | 0 | 学生class_idからクラスコード名称へ外部結合して移し、未所属・停止・期間外注記の意図と一覧状態未取得を区別する。名称欠落で学生行を消さない。 |
| 113 | DET-CSharp_ASPNET-SCR-STU-001-7AFB3215861F | 0 | match | 0 | 在籍の分類と値でCodeNameを取得し、EnrollmentStatusNameからenrollmentNameへ移す。名称NULLでも学生行を除外せず、一律補完を捏造しない。 |
| 114 | DET-CSharp_ASPNET-SCR-STU-001-2287F8F28EDE | 0 | match | 0 | 都道府県名と住所1をaddressDisplayへ連結し、住所2非表示、都道府県名称NULLだけの不整合補完と学生行保持を再現する。 |
| 115 | DET-CSharp_ASPNET-SCR-STU-001-8458E300284A | 0 | match | 0 | 本人電話を表示DTOへ移し、NULLだけ－とする。緊急電話は検索条件のOR対象でも一覧出力へ移さない。 |
| 116 | DET-CSharp_ASPNET-SCR-STU-001-F7227FD532A4 | 0 | match | 0 | DB更新datetimeoffsetを日本時間yyyy/MM/dd HH:mm:ssの一覧文字列へ移す。表示文字列とDB管理日時、未検索一覧を分けて再現する。 |
| 117 | DET-CSharp_ASPNET-SCR-STU-001-A5D22CFF7C14 | 0 | match | 0 | SortKeyは固定4値から許可SQL列へ移し、最後に学生ID昇順を付ける。任意DB列名・保存値にはせず、拒否時は保持条件由来の再表示であることを明示する。 |
| 118 | DET-CSharp_ASPNET-SCR-STU-001-0F98A4A4A753 | 0 | match | 0 | SortDirectionはasc/desc固定値と初期ascから検査後ORDER BYへ移す非保存指定である。変更時Page1、拒否時の再表示責務も具体化する。 |
| 119 | DET-CSharp_ASPNET-SCR-STU-001-297A9AA423DF | 3 | missing | 0 | raw・型・長さ・DB・表示・状態版の補足は具体的で、設計とソースを区別する。一方、実装工程における直接入力の正本・開発規約責務、停止候補・最終席競合・履歴失敗を含む試験観点一式までは自己完結しておらず、未生成計画への一般対応だけで全補足の再現とはしない。 |

各行の現版生成/ソース/許可参考設計/原本/採点行のSHAと行範囲はJSONに保存。
このbuilderは新規手判定の保存と検証のみで、期待セルをgenerationへ渡さず原稿を組み立てない。
