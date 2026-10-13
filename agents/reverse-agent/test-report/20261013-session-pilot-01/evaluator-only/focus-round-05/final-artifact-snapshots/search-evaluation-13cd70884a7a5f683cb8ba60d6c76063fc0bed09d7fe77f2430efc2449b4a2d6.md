# Focus round 05 学生検索 独立意味評価

EVALUATOR ONLY — generation入力不可。

生成5.0 SHA256 `8aedbb2b4316bfb72a0987cce5ddbe7a123dcb8d755a3b59845054e194160d64`。原仕様8.0／採点表7.4。
source43・許可reference11・起動runtime13・新raw prompt/result/answer/schemaを固定。旧採点転用なし。
全120行（有配点71＋診断49）、観測一致140/147点、不足3点、矛盾0点、保留4点。
重大矛盾0件。完了得点・完了率・95%判定はnull。

全判定と現版根拠は下の行別表を参照。生成・ソース・設計意図を分け、旧判定の転用を行わない。
在籍配列正規化と候補ER/人数操作の矛盾は原基準の要裁定として全行を残す。

| index | 評価ID | 配点 | 判定 | 加点 | 所見 |
| --- | --- | ---: | --- | ---: | --- |
| 0 | DET-CSharp_ASPNET-SCR-STU-001-818202EDAA7C | 3 | match | 3 | 検索と候補・ページ・遷移の参照責務、Controller/Coordinator/Serviceと状態保持、共通呼出引数結果、機能詳細・共通実装・DB定義・命名配備規約の正本配置を具体化する。設計名と実在クラスを区別し、業務表非更新と外部IO範囲を再現する。 |
| 1 | DET-CSharp_ASPNET-SCR-STU-001-8EE9449F3E51 | 3 | missing | 0 | 現行Viewer投影と権限差分、条件・一覧・メッセージ・ページは具体的である。原設計HTMLの表示範囲・専用メニュー・先頭最後を配置として再現せず、参考意図と現行不在の比較に留まる。出自は正しく区別されるが原レイアウト一式は不足する。 |
| 2 | DET-CSharp_ASPNET-SCR-STU-001-85EB2FF4920B | 1 | match | 1 | 番号の空初期・任意省略、rawと正規化15スカラー、形式・前方一致、DTO移送、VarChar15必須列とパターン31を分けて再現する。保存の完全番号と検索条件を混同しない。 |
| 3 | DET-CSharp_ASPNET-SCR-STU-001-641EC981BB78 | 1 | match | 1 | 氏名のraw8、正規化照合キー160、NFKC大文字空白除去、部分一致、表示表記との別領域、DB16/320容量とNULL属性、任意空を再現する。 |
| 4 | DET-CSharp_ASPNET-SCR-STU-001-8487A9C21424 | 1 | match | 1 | カナraw36から結果18、許可カナと照合用空白除去、任意条件の部分一致、保存側必須とnvarchar36、空初期・NULL省略を再現する。 |
| 5 | DET-CSharp_ASPNET-SCR-STU-001-46AE28C86B75 | 1 | match | 1 | 年度のすべて初期、nullable整数、1900～9998と候補存在、所属クラス年度への完全一致SmallIntを再現する。0を未指定扱いしない。 |
| 6 | DET-CSharp_ASPNET-SCR-STU-001-7FF1B82EB5CC | 1 | match | 1 | 学年の任意空NULL、2桁正規化、GRADE分類付き存在、停止候補と00実コード、クラス学年列への完全一致とVarChar2を再現する。 |
| 7 | DET-CSharp_ASPNET-SCR-STU-001-2097E1CD5ADD | 1 | match | 1 | クラスのすべて初期、rawから正Int64/19桁、未指定NULL、実在と上位実値整合、nullable所属列とBigInt完全一致を再現する。 |
| 8 | DET-CSharp_ASPNET-SCR-STU-001-0D82B3220DFF | 1 | match | 1 | 未所属false初期の真偽入力、class_id NULL条件と所属排他、ON解除・OFF非復元を再現する。ブラウザー解除と再描画disabledを区別する。 |
| 9 | DET-CSharp_ASPNET-SCR-STU-001-9C7EAABFFC27 | 1 | hold | null | 初期01/02、空全区分、最大4・重複拒否とINは具体的である。原属性のN-07と現行Ordinal固定値検査の未裁定差は原1点の保留とし、新本文の事実矛盾にしない。 |
| 10 | DET-CSharp_ASPNET-SCR-STU-001-BEFC3E38BC46 | 1 | match | 1 | 都道府県のすべて初期、任意NULL、2桁正規化とPREFECTURE存在、停止許容、学生列完全一致VarChar2・NOT NULLを再現する。 |
| 11 | DET-CSharp_ASPNET-SCR-STU-001-CE345AE8B601 | 1 | match | 1 | 電話raw20と形式最大16、任意空、NFKCと区切り除去、本人/緊急の完全一致OR、nullable保存列とVarChar16を再現する。 |
| 12 | DET-CSharp_ASPNET-SCR-STU-001-4ECDE6AD0828 | 1 | match | 1 | 開始日任意片側、1900から業務日、ISO受信からDateOnly?とDate包含比較、保存列必須を再現する。native date表示未固定と参考設計の表示・入力契約を分ける。 |
| 13 | DET-CSharp_ASPNET-SCR-STU-001-A3F0DF53EC17 | 1 | match | 1 | 終了日の共通範囲、任意片側、両端逆転拒否、Date包含比較と保存列NOT NULL、rawと型付き値を再現する。 |
| 14 | DET-CSharp_ASPNET-SCR-STU-001-14CE9B3FB604 | 1 | match | 1 | 検索操作のフォームと引数、今回条件検査・Page1・成功条件保持、学生参照と状態更新を具体化する。業務保存を行う操作とはしない。 |
| 15 | DET-CSharp_ASPNET-SCR-STU-001-3EBF0942E20F | 1 | match | 1 | 原行クリアに対応し、独立Contextフォーム、初期01/02と未検索、Applied/LastResult消去、状態ID維持、DB DELETEなしを再現する。 |
| 16 | DET-CSharp_ASPNET-SCR-STU-001-29BE85CA6FA3 | 1 | match | 1 | 原行新規登録に対応し、Viewer非表示と入口作成権限、復帰ID付き登録GET、検索条件非転記、登録側責務を再現する。クリアの根拠を流用しない。 |
| 17 | DET-CSharp_ASPNET-SCR-STU-001-778AE19CABEA | 1 | match | 1 | ナビゲーションの設計意図としてメニューを示し、現行に専用入口がないことを比較する。検索の非更新範囲と併読し、未接続Menuを実装済みとせず操作意味を再現する。 |
| 18 | DET-CSharp_ASPNET-SCR-STU-001-4C53DF730112 | 1 | match | 1 | 件数と表示範囲を分け、非負整数、5桁欄と0～10000、設定元、未検索/超過未設定、0件範囲0を設計契約として具体化する。現行Countと範囲未実装を明示し、未定義算式を補作しない。 |
| 19 | DET-CSharp_ASPNET-SCR-STU-001-F3F05B9FA665 | 1 | match | 1 | 検索入口実行日時から日本時間19文字へ移し、未検索未設定と非DB保存を再現する。設計RequestContext名と実在SearchResult、foundだけ本文表示する現行差を区別する。 |
| 20 | DET-CSharp_ASPNET-SCR-STU-001-45CB937AB1D9 | 1 | match | 1 | 表示件数の20/50/100固定値、初期20、非保存制御、許可外拒否と型付きSize、変更時Page1を再現する。 |
| 21 | DET-CSharp_ASPNET-SCR-STU-001-4BE95BEB109D | 1 | match | 1 | 保存番号15とVarChar15必須列から一覧文字列へ移し、検索パターンを表示せず保存文字順とする。未検索空一覧と表示専用の意味を再現する。 |
| 22 | DET-CSharp_ASPNET-SCR-STU-001-2580A923AAE8 | 1 | match | 1 | 表示氏名の保存表記、業務8・DB16・NOT NULL、DTO移送と非表示name_key、未検索空一覧を再現する。 |
| 23 | DET-CSharp_ASPNET-SCR-STU-001-5992A6AEB5CC | 1 | match | 1 | 表示カナの保存表記、業務18・DB36・NOT NULL、DTO移送と非表示kana_key、未検索空一覧を再現する。 |
| 24 | DET-CSharp_ASPNET-SCR-STU-001-E2A700703DCF | 1 | match | 1 | 必須内部dateを元年・2桁月日の和暦へ移す表示を再現する。非入力、時差なし、設計nullableと保存列必須を区別する。 |
| 25 | DET-CSharp_ASPNET-SCR-STU-001-D97621F3E369 | 1 | match | 1 | 年度4桁と学年名称12、所属列/分類名称への対応、smallint/nvarchar24基表NOT NULLとJOIN NULLを再現する。未所属－の設計と現行補完なしを区別する。 |
| 26 | DET-CSharp_ASPNET-SCR-STU-001-809FC6941D89 | 1 | match | 1 | クラスコード9と名18、DB9/36と保存制約、nullable結合とDTO、未所属/停止/期間外・名称欠落の設計と現行状態未取得の差を再現する。 |
| 27 | DET-CSharp_ASPNET-SCR-STU-001-C241C2C610FB | 1 | match | 1 | 在籍の分類値JOINから名称12とDB24をDTOへ移し、基表NOT NULLとJOIN NULLを分け、名称欠落で学生行を落とさない。 |
| 28 | DET-CSharp_ASPNET-SCR-STU-001-201E2ADAAED5 | 1 | match | 1 | 都道府県名12と住所1の45を算出住所へ移し、DB容量と必須性、住所2非表示、名称NULLだけ不整合を再現する。 |
| 29 | DET-CSharp_ASPNET-SCR-STU-001-7B137736C1F9 | 1 | match | 1 | 本人電話16とnullable VarChar16、NULL時－、DTO移送と非入力を再現する。緊急電話検索一致でも一覧に緊急電話を出さない。 |
| 30 | DET-CSharp_ASPNET-SCR-STU-001-09BFD0B375D6 | 1 | match | 1 | DB更新datetimeoffsetのUTC管理値を日本時間19文字へ移す表示を再現する。DB値と表示文字列、未検索一覧を区別する。 |
| 31 | DET-CSharp_ASPNET-SCR-STU-001-9F0DF8AE8584 | 1 | match | 1 | 編集参照は行番号でなく学生IDを使い、Viewer参照・他Role編集と最新対象再取得、登録側の読込みを再現する。 |
| 32 | DET-CSharp_ASPNET-SCR-STU-001-BCAFF893A5B7 | 1 | match | 1 | 未検索非活性とPage/Size取得、表示指定変更Page1、最終有効ページ補正を再現する。先頭最後の設計意図と現行前後操作を区別する。 |
| 33 | DET-CSharp_ASPNET-SCR-STU-001-9930CD28DA63 | 1 | match | 1 | 固定4キーと初期studentNo、許可主ソート列switch、最後の学生ID昇順、非保存指定と変更時Page1を再現する。 |
| 34 | DET-CSharp_ASPNET-SCR-STU-001-3577E1D08486 | 1 | match | 1 | 固定小文字asc/desc、初期ascと許可外拒否、全集合ORDER BYと方向変更時Page1、非DB制御を再現する。 |
| 35 | DET-CSharp_ASPNET-SCR-STU-001-3CA4298726C7 | 0 | missing | 0 | 検索年度の生成・範囲・降順・すべては具体的である。共有候補の登録当年度選択補助と新規初期までは説明されず、0点診断として不足を残す。 |
| 36 | DET-CSharp_ASPNET-SCR-STU-001-24E04907EBCB | 0 | missing | 0 | 検索GRADEの値・名称・順序・00・停止許容は具体的である。登録新規有効値と既存値の別枠保持の属性一式は再掲されていない。 |
| 37 | DET-CSharp_ASPNET-SCR-STU-001-911C12BA9C4F | 0 | missing | 0 | 検索クラスの完全順序・上位抽出・解除と登録人数集計を区別するが、登録新規所属・最終所属・既存保持と新規未選択の共有候補一式は不足する。 |
| 38 | DET-CSharp_ASPNET-SCR-STU-001-2EFE8DD8D16C | 0 | missing | 0 | 検索在籍の分類・順序・01/02と全解除は再現する。共有候補の新規登録初期01、保護値と有効新規選択の一式は不足する。 |
| 39 | DET-CSharp_ASPNET-SCR-STU-001-3CBFA4E19E92 | 0 | missing | 0 | 検索都道府県の分類・名称・順序・すべて・停止許容は再現する。登録の未選択初期、有効新規と既存同値保持までの共有契約は不足する。 |
| 40 | DET-CSharp_ASPNET-SCR-STU-001-839BE5C68724 | 0 | match | 0 | 表示件数の固定3値と順序、初期20、業務コードではないこと、Pageで反映して変更時Page1を再現する。 |
| 41 | DET-CSharp_ASPNET-SCR-STU-001-6EB9CBF8698A | 0 | match | 0 | 並び順4キー・4ラベル・順序・初期、自由DB列名を拒否して許可列へ対応する候補契約を再現する。 |
| 42 | DET-CSharp_ASPNET-SCR-STU-001-AE6D87D5FD40 | 0 | match | 0 | 方向の固定2値とラベル順、初期asc、大文字など許可外拒否を再現する。 |
| 43 | DET-CSharp_ASPNET-SCR-STU-001-B58C16E76F3C | 0 | match | 0 | 件数の非負整数、最大長5、0～10000とOP-COUNT/page、成功設定・未検索超過未設定を設計と現行で具体化する。表示件数と範囲は別の値である。 |
| 44 | DET-CSharp_ASPNET-SCR-STU-001-184621105C7E | 0 | match | 0 | 原内部項目の開始位置に対し、RangeFromの非負整数、5桁、0～10000、OP-COUNT/page、未検索超過未設定・0件0を明記する。現行未宣言・未計算を区別し未定義算式は追加しない。 |
| 45 | DET-CSharp_ASPNET-SCR-STU-001-57216B6625D4 | 0 | match | 0 | 原内部項目の終了位置に対し、RangeToの非負整数、5桁、0～10000、OP-COUNT/page、未検索超過未設定・0件0を具体化する。現行不在を実装済みにはしない。 |
| 46 | DET-CSharp_ASPNET-SCR-STU-001-BDFBC17D956D | 0 | match | 0 | 年度の任意整数、4桁1900～9998、クラス列設定元と表示用途、未所属－の設計と現行nullable移送を再現する。 |
| 47 | DET-CSharp_ASPNET-SCR-STU-001-30F27E0FB66C | 0 | match | 0 | 学年名称のstring、12、GRADE名称設定元と表示用途、未所属－の設計と現行NULLを再現する。 |
| 48 | DET-CSharp_ASPNET-SCR-STU-001-8A501244EF50 | 0 | match | 0 | クラスコードのstringと9、m_class設定元、未所属表示と名称欠落による学生行保持を再現する。 |
| 49 | DET-CSharp_ASPNET-SCR-STU-001-F5E57DED2AF4 | 0 | match | 0 | クラス名称のstringと18、m_class設定元、未所属/状態差と名称欠落による学生行保持を再現する。 |
| 50 | DET-CSharp_ASPNET-SCR-STU-001-5B9587C349EA | 0 | match | 0 | 内部生年月日のDateOnly?設計、取得必須・欠損不整合、設定元dateと和暦変換、時差なしを再現する。現行DateOnlyとDB NOT NULLを区別する。 |
| 51 | DET-CSharp_ASPNET-SCR-STU-001-D8B62A990A55 | 0 | match | 0 | 学生IDをbigint採番からlongと十進文字列へ移し、新規は対象なし、既存は正対象で再取得・権限存在確認する。行番号を使わない。 |
| 52 | DET-CSharp_ASPNET-SCR-STU-001-A9CE89C36F45 | 0 | match | 0 | 状態キーの64hex乱数、stringと初回未発行、所有主体・認証セッション・指定Tab・30分を再現する。Tab省略時とResume未指定の実装差を区別する。 |
| 53 | DET-CSharp_ASPNET-SCR-STU-001-6AA636D6AE05 | 0 | missing | 0 | CSRF生成・MVC検査と認証・版・排他との別責務は具体的である。opaque文字列の型と基盤が実値長を定める内部項目の全属性までは示されない。 |
| 54 | DET-CSharp_ASPNET-SCR-STU-001-DA1AFEB05304 | 0 | match | 0 | IsBusyの真偽・最大長1・false初期・開始終了設定・UI再入防止とDB排他別を設計契約に明記する。現行プロパティ不在とsubmit補助の限定範囲を区別する。 |
| 55 | DET-CSharp_ASPNET-SCR-STU-001-D5F99F6B1962 | 0 | match | 0 | RequestSequenceの非負整数、画面内要求連番、初期0と非同期採番、旧応答破棄・桁あふれ停止を設計契約として再現し、現行Revisionと同一視しない。 |
| 56 | DET-CSharp_ASPNET-SCR-STU-001-2F4076F4B844 | 3 | match | 3 | 認証済み初回GETで未検索と候補を作り学生一覧は検索しない目的、状態付き起動の復帰分岐を再現する。 |
| 57 | DET-CSharp_ASPNET-SCR-STU-001-CEB54B9A108C | 3 | match | 3 | 認証・新Entry・初期01/02と20件番号昇順・候補・未検索を具体的順序で示す。必須候補不足禁止と引数複製/応答世代の設計と現行差を区別する。 |
| 58 | DET-CSharp_ASPNET-SCR-STU-001-8B5BD3A34BD3 | 3 | match | 3 | 初回/復帰分岐、認証、初期条件、候補と描画、拒否・後段障害の図を具体化する。設計の必須マスター判定不在を明示し、図存在だけで一致としない。 |
| 59 | DET-CSharp_ASPNET-SCR-STU-001-D7CFBCD19044 | 3 | match | 3 | 分類コードのJOIN、クラスと学年の関連、物理FKと読取JOIN、人数非集計、名称欠落保持と非書込みを初回に対応させる。 |
| 60 | DET-CSharp_ASPNET-SCR-STU-001-C629D630F584 | 3 | match | 3 | 候補の二結果セット、対象列と完全順序、同一SNAPSHOT、人数省略・参照commitをOP-CODE/CLASS相当として具体化する。 |
| 61 | DET-CSharp_ASPNET-SCR-STU-001-9C4A6F5838F0 | 3 | match | 3 | 初回の認証・候補・変換描画拒否と未検索操作を示す。検索未実行時の0件超過結果を付加せず、候補不足の設計と実装差を明示する。 |
| 62 | DET-CSharp_ASPNET-SCR-STU-001-9637E6E4F65A | 3 | match | 3 | 今回条件による非削除学生のPage1検索、成功確認と条件結果保持、0件と超過の成功分岐を処理目的として再現する。 |
| 63 | DET-CSharp_ASPNET-SCR-STU-001-8C6836155E22 | 3 | match | 3 | 入力移送・検査・存在整合、同条件COUNT/PAGEと上限0件、成功条件保持、日付表示を手順化する。配列引継ぎと成功後深い複製、応答世代設計を現行と分ける。 |
| 64 | DET-CSharp_ASPNET-SCR-STU-001-69FC36696F49 | 3 | match | 3 | 入力拒否、同条件件数と上限0件一覧、状態更新、表示へのフローを具体化する。検証422・所有403・状態409・取消と後段障害を固定状態にまとめない。 |
| 65 | DET-CSharp_ASPNET-SCR-STU-001-1EA9445F88DE | 3 | match | 3 | 学生クラスとGRADE/在籍/都道府県の分類値JOIN、COUNTと一覧の辺、基表FKと用途参照、外部結合で学生行保持を再現する。 |
| 66 | DET-CSharp_ASPNET-SCR-STU-001-C8A0C07C26B8 | 3 | match | 3 | 指定マスター確認と上位整合、番号完全一致存在検査非適用、COUNT/PAGEの同条件SNAPSHOT、全述語と型、上限・ソート・取得列を具体化する。 |
| 67 | DET-CSharp_ASPNET-SCR-STU-001-4031A7ED4200 | 3 | match | 3 | 入力検証・0件・超過・所有等拒否、局所入力と空一覧再表示、LastResult維持、catch外障害と後段状態非復元を再現する。設計の結果扱いと現行を区別する。 |
| 68 | DET-CSharp_ASPNET-SCR-STU-001-25F8A2CE6127 | 3 | match | 3 | 年度学年クラス未所属の条件変更は学生検索と別で、今回入力・候補・成功済み一覧と未反映通知を再表示する目的を再現する。 |
| 69 | DET-CSharp_ASPNET-SCR-STU-001-D5DBFDB9B880 | 3 | match | 3 | 未所属解除非活性とOFF非復元、上位不適合解除、クラス先行補完・応答世代の設計意図と実装差を明示し、Optionsの具体手順を再現する。 |
| 70 | DET-CSharp_ASPNET-SCR-STU-001-ECF83B2057CD | 3 | match | 3 | 未所属と候補取得、クラス適合判定と解除、未反映通知・LastResult維持の図と本文を対応させる。現行全体POSTと設計上の補完・旧応答破棄を分離する。 |
| 71 | DET-CSharp_ASPNET-SCR-STU-001-2E6EC8AADACD | 3 | hold | null | 現行候補の人数なし読取図は具体的である。原候補ERの学生人数辺と原OP-CLASSの検索人数集計なしが併存するため、原3点は未裁定を保持する。 |
| 72 | DET-CSharp_ASPNET-SCR-STU-001-E9251F3FFD1F | 3 | match | 3 | OP-CLASS相当の対象・完全順序・参照確定と人数省略を示す。上位条件はSQL受信値ではなく取得後抽出という実装差を説明し、学生検索や書込みを行わない。 |
| 73 | DET-CSharp_ASPNET-SCR-STU-001-8B3FD87731C8 | 3 | match | 3 | 候補だけでは学生再検索せず、LastResultと今回条件未反映・不適合解除通知を再現する。ModelState非停止と局所catchなしを明示し、未実行の検索結果を付加しない。 |
| 74 | DET-CSharp_ASPNET-SCR-STU-001-72E55C707425 | 3 | match | 3 | Appliedを複製し表示指定だけ変更する再検索目的、未実行条件非混入と変更時Page1を具体化する。 |
| 75 | DET-CSharp_ASPNET-SCR-STU-001-981EDBD68D75 | 3 | match | 3 | 状態所有期限版・未検索拒否、許可表示指定、COUNT/PAGEと件数減少補正、0件操作を手順化する。一度だけの第2検索と別SNAPSHOTを区別する。 |
| 76 | DET-CSharp_ASPNET-SCR-STU-001-3D1170870753 | 3 | match | 3 | Pageフローは403/409/422の元状態、Gate取得前取消、保持条件・補正・再検索・確定・後段再表示を分岐として再現する。再構築へ固定状態を付加しない。 |
| 77 | DET-CSharp_ASPNET-SCR-STU-001-F891789D8BAE | 3 | match | 3 | Pageの件数学生クラス辺と一覧3用途コード、Q-S検索JOINと別Q-L、物理FKと読取関連を対応させ、非更新を再現する。 |
| 78 | DET-CSharp_ASPNET-SCR-STU-001-0DC7ABFB61F6 | 3 | match | 3 | 保持条件のCOUNT/PAGE、最大件数と許可順序、学生IDtie-break、ページと型付き値・取得列を具体化する。一回と補正別検索の読取境界を区別する。 |
| 79 | DET-CSharp_ASPNET-SCR-STU-001-FD120ACB2559 | 3 | match | 3 | Pageの元WebFault状態、Applied由来inputと空一覧、ModelState非停止、catch内外再構築・描画・取消と旧結果の扱いを具体化し設計との差を明示する。 |
| 80 | DET-CSharp_ASPNET-SCR-STU-001-3E9561673E6C | 3 | match | 3 | 新規・行操作とクリア、メニュー意図の対象を示し、登録入口移送と検索状態初期化を別の責務として再現する。 |
| 81 | DET-CSharp_ASPNET-SCR-STU-001-0F958E6A35C9 | 3 | match | 3 | 作成権限と検索条件非流用、既存学生IDで登録側取得、クリアの初期未検索を手順化する。メニュー移動は設計意図と現行入口不在として区別する。 |
| 82 | DET-CSharp_ASPNET-SCR-STU-001-04A9D80CB796 | 3 | match | 3 | クリアと新規/既存図を合わせ、権限確認、対象IDによる登録、初期未検索の分岐を再現する。メニュー設計意図を本文で補い未接続の実装枝を捏造しない。 |
| 83 | DET-CSharp_ASPNET-SCR-STU-001-BA5C23F04C4F | 0 | match | 0 | クリアと遷移制御自体をメモリ/画面制御として、業務DB書込みERを付加しない。再描画候補と登録側最新読込の実際の読取りは別に示す。 |
| 84 | DET-CSharp_ASPNET-SCR-STU-001-F4832740C697 | 3 | match | 3 | 業務表更新なし、クリアはメモリ消去、対象読込みは登録側責務を再現する。後続の候補SQLを学生DELETEや状態永続DELETEと混同しない。 |
| 85 | DET-CSharp_ASPNET-SCR-STU-001-DE44988F8890 | 3 | match | 3 | 作成権限・対象不在・復帰状態再確認拒否とクリア結果を示す。登録読込・取消と復帰を区別し、未実行検索の0件超過を操作へ適用しない。 |
| 86 | DET-CSharp_ASPNET-SCR-STU-001-E22DC1F3ED19 | 3 | match | 3 | 保存削除の確定復帰と非保存戻り、未検索復元か元条件再検索の目的を再現する。入力取消の現行Edit滞在を区別する。 |
| 87 | DET-CSharp_ASPNET-SCR-STU-001-ED6049702EC4 | 3 | match | 3 | 所有認証期限版、未検索または元条件検索、条件不変更と確定通知だけのTakeを手順化する。期限初期化・Tab照合の意図と現行差を明示する。 |
| 88 | DET-CSharp_ASPNET-SCR-STU-001-4745B3118380 | 3 | match | 3 | 状態確認・検索済み分岐・元条件再検索・未検索復元と確定通知の図を再現する。通知消費と後段描画、SQL取得ページと提示ページを区別する。 |
| 89 | DET-CSharp_ASPNET-SCR-STU-001-3A56EE94C8EF | 3 | match | 3 | 復帰の学生クラスと3用途コードの分類値外部結合、学生行保持をQ-Sへ対応し、別候補読取とメモリ状態通知を区別する。 |
| 90 | DET-CSharp_ASPNET-SCR-STU-001-3F24B3D24CD6 | 3 | match | 3 | 元Appliedの同条件COUNT/PAGEと参照確定、未検索では検索なし、条件外保存学生追加なしを再現する。保持条件とSQLローカルページを区別する。 |
| 91 | DET-CSharp_ASPNET-SCR-STU-001-06F52338F30B | 3 | match | 3 | 他者・期限・旧版拒否、局所catchなし、未検索/再検索、Take前後失敗と条件不変更を再現する。UnknownをSavedにせず303と配信確定を区別する。 |
| 92 | DET-CSharp_ASPNET-SCR-STU-001-4CEB20699DCB | 0 | match | 0 | 番号inputからサービス値・student_no前方条件へ移し、任意NULLと正規化、型付きパターン、入力検証時の再表示材料とDB検索なしを再現する。 |
| 93 | DET-CSharp_ASPNET-SCR-STU-001-304D86123D7F | 0 | match | 0 | 氏名inputからNameKey相当とname_key部分一致へ移し、空省略・表示表記との差、入力失敗の材料とDB検索前拒否を再現する。 |
| 94 | DET-CSharp_ASPNET-SCR-STU-001-6DC80333D39F | 0 | match | 0 | カナinputから正規化照合キーとkana_key部分一致へ移し、空省略とraw変換値、入力エラー再表示と検索前拒否を再現する。 |
| 95 | DET-CSharp_ASPNET-SCR-STU-001-FA1B1DEC5FC4 | 0 | match | 0 | 年度をint?へ移し範囲と候補確認後に所属年度SmallIntで完全一致する。未指定NULLと型/検査不正を区別し、検索前拒否を再現する。 |
| 96 | DET-CSharp_ASPNET-SCR-STU-001-EEA4FE49B2DD | 0 | match | 0 | 学年を任意NULL・2桁正規化からクラス学年完全一致へ移す。00実コードと未所属の差、失敗再表示とDB検索なしを再現する。 |
| 97 | DET-CSharp_ASPNET-SCR-STU-001-E47A8676FF5E | 0 | match | 0 | クラスrawからlong?、所属列完全一致と指定年度学年整合へ移す。未指定NULLと不正IDを分け、変換失敗を0/NULL条件にしない。 |
| 98 | DET-CSharp_ASPNET-SCR-STU-001-B44E2FCE1CFA | 0 | match | 0 | 未所属trueからclass_id IS NULL、所属排他とチェック状態、Options解除とSearch拒否の違いを再現する。 |
| 99 | DET-CSharp_ASPNET-SCR-STU-001-91FBF38A968F | 0 | hold | null | 在籍空配列とIN、最大4と重複拒否は具体的である。原移送N-07と現行未正規化Ordinal検査の裁定がなく、原0点診断もhold/nullで保持する。 |
| 100 | DET-CSharp_ASPNET-SCR-STU-001-8A43F42C52E8 | 0 | match | 0 | 都道府県inputを分類付き正規化値から学生コード完全一致へ移す。任意NULL、入力失敗の原入力材料と検索前拒否、表示住所との別責務を再現する。 |
| 101 | DET-CSharp_ASPNET-SCR-STU-001-6DEBDB212746 | 0 | match | 0 | 電話rawから正規化値、本人/緊急の完全一致ORへ移し、空省略と入力失敗再表示・DB検索前拒否を再現する。一覧電話とは別の用途である。 |
| 102 | DET-CSharp_ASPNET-SCR-STU-001-66EBD557D2C4 | 0 | match | 0 | 開始文字列から厳密DateOnly?とSQL Date、開始包含と片側指定、未指定NULL・入力不正拒否を再現する。 |
| 103 | DET-CSharp_ASPNET-SCR-STU-001-FA5975CE821D | 0 | match | 0 | 終了文字列からDateOnly?とSQL Date、終了包含と両端逆転検査、未指定NULLと検索前拒否を再現する。 |
| 104 | DET-CSharp_ASPNET-SCR-STU-001-8BDCB190100E | 0 | match | 0 | COUNT由来TotalCountと設計RangeFrom/ToのOP-COUNT/page設定・表示方向、未検索/0件/超過の違いを具体化する。現行範囲移送なしと未定義算式を区別し、一般式を補わない。 |
| 105 | DET-CSharp_ASPNET-SCR-STU-001-F54A1A8CAD59 | 0 | match | 0 | 入口実行時刻を日本時間文字列へ移す非DB出力、未検索未設定とfoundだけ本文表示する現行、設計名との差を再現する。 |
| 106 | DET-CSharp_ASPNET-SCR-STU-001-E8CB75BB9186 | 0 | match | 0 | PageSizeの受信型、20/50/100・初期20、非保存と取得Size、表示指定変更、拒否後保持条件由来の再表示を再現する。 |
| 107 | DET-CSharp_ASPNET-SCR-STU-001-B30B1EA938EF | 0 | match | 0 | 保存番号を一覧DTO文字列へ移し、検索LIKE表現を表示せず、保存文字順でソートする非入力出力を再現する。 |
| 108 | DET-CSharp_ASPNET-SCR-STU-001-6B8E0F8CE3F6 | 0 | match | 0 | 保存氏名表記をStudentRowとstudentNameへ移し、照合キーを非表示にする。必須基表と未検索空一覧、名称欠落で学生行を落とさない契約を再現する。 |
| 109 | DET-CSharp_ASPNET-SCR-STU-001-B42712AE75D9 | 0 | match | 0 | 保存カナ表記を一覧DTOへ移し、検索kana_keyは非表示とする。表示入力対象外と未検索空一覧を再現する。 |
| 110 | DET-CSharp_ASPNET-SCR-STU-001-FE626D2530FC | 0 | match | 0 | 内部birth_dateを和暦表示へ移し、元年/月日書式と時差なし、非入力を再現する。内部dateを一覧objectへ直接出さない。 |
| 111 | DET-CSharp_ASPNET-SCR-STU-001-36DED7C9B233 | 0 | match | 0 | クラス年度とGRADE名称を複合一覧へ移し、年度西暦・学年名称・未所属設計－と現行JOIN NULLを区別する。名称欠落で学生行を落とさない。 |
| 112 | DET-CSharp_ASPNET-SCR-STU-001-B03C4F9CFB91 | 0 | match | 0 | class_idからクラスコード名称を外部結合で移し、未所属/停止/期間外意図と現行状態未取得を分ける。学生行保持を再現する。 |
| 113 | DET-CSharp_ASPNET-SCR-STU-001-7AFB3215861F | 0 | match | 0 | 在籍分類と値で名称取得しEnrollmentStatusNameからenrollmentNameへ移す。名称欠落だけで学生を除外せず、架空の一律補完を付加しない。 |
| 114 | DET-CSharp_ASPNET-SCR-STU-001-2287F8F28EDE | 0 | match | 0 | 都道府県名と住所1を算出addressDisplayへ移し、住所2非表示、都道府県名称NULLだけの不整合補完を再現する。 |
| 115 | DET-CSharp_ASPNET-SCR-STU-001-8458E300284A | 0 | match | 0 | 本人電話を一覧へ移しNULLだけ－とする。緊急電話は検索OR対象でも一覧出力へ移送しない。 |
| 116 | DET-CSharp_ASPNET-SCR-STU-001-F7227FD532A4 | 0 | match | 0 | DB更新datetimeoffsetを日本時間19文字の一覧文字列へ移し、保存管理日時と表示値、未検索空一覧を分ける。 |
| 117 | DET-CSharp_ASPNET-SCR-STU-001-A5D22CFF7C14 | 0 | match | 0 | SortKey固定4値を許可主列へ移し学生ID昇順を添える非保存指定を再現する。任意DB列を受けず、拒否後の保持条件再表示を区別する。 |
| 118 | DET-CSharp_ASPNET-SCR-STU-001-0F98A4A4A753 | 0 | match | 0 | asc/descと初期ascから検査後ORDER BYへ移し、方向変更Page1と非保存制御、拒否時の再表示責務を再現する。 |
| 119 | DET-CSharp_ASPNET-SCR-STU-001-297A9AA423DF | 3 | match | 3 | raw/正規化/型/DB/再表示、設計内部名と現行、Unicode長と容量、状態版、直接開発入力・正本責務と実装試験の具体的確認を自己完結して再現する。停止候補・最終席・履歴失敗・Unknown等の担当境界を含め、文書/投影/実機試験を代用しない。 |

各行の現版生成/ソース/許可参考設計/原本/採点行のSHAと行範囲はJSONに保存。
このbuilderは新規手判定の保存と検証のみで、期待セルをgenerationへ渡さず原稿を組み立てない。
