# Access 撮影fixture R6

生成ID `20261012-evidence-01-ui-r6`。最終方式内VBAからSingleFile／IncludeTests／NoStartupの新規ACCDBを作り、productionのMaintainClass／clsStudentService.SaveStudentで架空クラス1件・学生3件・CREATE監査4件を登録した。実DAO読返しは [synthetic-data.json](synthetic-data.json)、入力版・SHA・閉鎖時の原本保護は [results.json](results.json)、登録ログは [seed.raw.log](seed.raw.log)。

実Access FileFormat12、SELF、外部リンク0。Visible=false COMでClose/Quit済み。閉鎖時fixture SHA-256は `C69ADE20DB77996D2C17A8B15646CEBE78DC882CF19B46DFFEC275194D5CF150`。配布原本は開かず、SHA-256 `D1777167FD7423BF4399F05D006519FD5A8E005A6FEF2E56B1A8F11AAD73EC87` はseed前後で一致した。撮影後のfixture内部メタデータ変更はrootの閉鎖記録で区別する。

入口は `srcs/Access/build/20261012-evidence-01-ui-r6/20261012-build-04-access-single-evidence-01-ui-r6.accdb`。build-04は既存の使い捨てファイルガード識別用で、今回の入力／実行はR6である。既存Show-UiFixture.ps1へこのFixtureと新規ReportDirectoryを指定できる。

実UIの確認手順:

1. frmStudentSearchを表示し、4条件「すべて」、卒業・退学・未所属Falseを確認する。
2. 既定検索でTEST-ACE-001／002の2件、卒業を追加して003を含む3件を確認する。
3. クラス「2026 1年 TEST-UI 架空撮影A組」を選び、年度／学年同期を確認する。学年「学年なし」に変更してクラス「すべて」とW-STU-107解除通知を確認する。
4. クリアで「すべて」と在学／休学へ戻ること、未所属選択で年度／学年／クラスが「すべて」のまま非活性になることを確認する。
5. 新規登録を空のまま保存し、`E-DATE-001: 生年月日の元号・年・月・日を確認してください。` の中点3文字と入力保持を確認する。
6. 一覧のTEST-ACE-001を開き、仮名・和暦日付・クラスと学籍番号編集不可を確認する。直接OpenArgsは既存 `1|evidence`、新規 `|evidence`。

架空住所・電話・example.invalidメールだけを用い、配布原本にfixtureを混入させていない。共有SQL配備・接続・移行・認可結合は実行していない。画像撮影はrootの実productionフォーム操作で行う。
