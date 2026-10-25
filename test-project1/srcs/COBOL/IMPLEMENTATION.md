# 仕様ID・生成物・境界

入力正本は方式内spec版8.0／8.1／8.2、49ファイルです。入力ハッシュは `build/input-manifest.json`、現行結果は `build/test-results/summary.json` に保存し、過去版はGit履歴で管理します。

| 仕様・操作 | 生成ファイル | 内容 |
| --- | --- | --- |
| SCR-STU-001、EV-SRC-001～006、SRC-001～033 | STMAIN, STSRCH, STSTATE, STCAND, STMLOOK, STRENDER | 検索、条件連動、4固定ソート・ページ、クリア、登録後再取得。入力中条件と実行済み条件を別保持 |
| SCR-STU-002、EV-REG-001～007、REG-001～034 | STEDIT, STSAVE, STDELT, STDUP, STRULES, STRENDER | 新規・編集・参照、19raw検査、確認、版、取消・再読込、論理削除 |
| 共通01～03 | STAUTH, STCLOCK | 信頼CGI主体、CSRF、DB業務日、SNAPSHOT設定 |
| 共通04～05・17 | STNORM, STVALID, STHINT; bridge/student_bridge.c | rawスカラー上限・正規化後上限、コード桁、電話・メール、必須・組合せ |
| 共通06～10 | STMLOOK, STMCHECK, STRULES, STDUP | コード・クラス・停止/期間/定員、全候補ID/版ハッシュ、先頭20件表示 |
| 共通11～12 | STSTATE, STFLASH; bridge/student_bridge.c | owner/session/kind/tabをAES-GCMに結合、revision条件付き更新・消費、検索30分・確認/Flash10分 |
| 共通13～14 | STSAVE, STDELT, STAUDIT, STMAINT | 同じDBゲート、Tx内再判定・保存・監査、NoChange、取消と結果不明の分岐 |
| 共通15～16 | STMSG, STRENDER, STDATE, STDATEOUT, STISODATE; assets | メッセージ、和暦4入力・境界、西暦、HTML escaping、UTF8ヘッダー |
| マスタ保守・コード70値 | STMAINT; sql/MC-*.sql, MK-*.sql, MAINT-LOG.sql; database/002_seed.sql | 保護コード、追加可否、年度・名称一意、参照時学年/期間、定員、状態遷移監査 |
| SQLServer定義 | database/001_schema.sql,002_seed.sql; tools/generate_database.mjs | 業務5表89列、技術2表、複合FK・nullable続柄分類/値、UTC・版・監査制約 |

表のPROGRAM-IDは `cobol/<名称>.cob` に対応します。19rawの正確な並びは `tools/emit_cobol.py` のrawmapです。生年月日は19論理項目のうち1項目、元号/年/月/日4入力で受けます。現行検索は番号、氏名、クラス、在籍集合の4条件です。一覧は番号、氏名／カナ、生年月日、年度・学年、クラス、在籍、編集／参照の7列。SQL一覧は非表示IDを含む10物理列だけを取得し、住所・電話・更新日時は取得しません。更新日時による並べ替えは継続します。

`STPROMPT` は編集取消・再読込・復帰・削除のpendingActionと編集中rawを暗号化Editor状態へ退避し、CONFIRM／CANCELを処理します。クライアントのconfirmed値はHTTP境界で拒否します。重複確認も独立HTMLへ表示し、全候補ID／版の再照合は既存STDUP/STSAVEが担います。HTML候補fixtureによるレンダー試験は、この状態I/Oや実DBの確認後保存を検証していません。

## ABIとトランザクション

`tools/abi-schema.json` からC/COPYを生成します。ST_PARAM=24、ST_DB_REQUEST=976、ST_DB_RESULT=40、ST_VALUE=1032byte。64bit pointer、little-endian、int32/int64/int16 NULL標識です。Cはsizeof/offsetofをstatic assert、実COPYのABI probeで値・pointer・NULLとAPP内の整列を確認します。BY VALUEはC整数/pointer、BY REFERENCEは固定記録、STCONNECT/STHASHSTARTはpointer戻り値、他はint32です。

最大バイト領域・実長・スカラー文字数を分け、末尾空白をSQL実長へ加えません。38固定command_idだけを実行し、ColumnSizeはカタログの宣言長です。LIKEは!/%/_/[をリテラル化、ソートは固定4×2分岐、生入力をSQLへ連結しません。SQLSTATE/native番号は別項目、01004/FETCH切捨てを成功扱いしません。

検索は同じSNAPSHOT Txで件数・一覧を読み10,001件で上限判定。検索用CLASS-LISTは人数を集計せず、登録用CLASS-EDITのみ参考人数を出します。保存・保守は排他applock後に再判定し、監査失敗では業務DMLも取消します。確認は全候補を読み、理由を入力ハッシュへ含めず、理由未入力の再送でトークンを失わせません。

接続・statement・cursor・hash・描画バッファは所有者で解放します。CGIヘッダーは候補取得を含む描画完了後に送ります。

## 検査範囲

生成・構文・ホストリンク・境界実行は実施済みです。Linux再ビルド/依存確定、SQLServer DDL/seed/CRUD/保守、CGI再起動状態復帰、2接続競合、監査失敗、COMMIT後応答喪失、実ブラウザー操作は未実施です。これらをmock成功や完成した配備として扱いません。

2026-10-23最終補正：外部POSTはCREATE／UPDATE／OPTIONS等の明示action、空・旧actionを拒否する。検索nameと反復statusCodeを内部RAWへ変換し、空の廃止キーも400/E-SRC-002。OPTIONSはeditorIdの有無で分岐する。検索からの遷移はPOST OPTIONSでdraftをCAS保存した後、個人情報を含まないmetadataだけの303 GETへ移す。STPENDはSearchとEditorへpendingを結合し、10分期限とSearchRevision更新で背景GET／POST・古い確認を拒否する。未変更のRESET／RELOAD／BACKは直接実行し、重複・削除の理由エラーはrawを保持して同じ確認へ戻す。重複／削除成功時は学生・監査と同じTx内でpendingを解除する。
