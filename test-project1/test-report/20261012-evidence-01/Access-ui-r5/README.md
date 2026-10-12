# Access 最終撮影fixture R5

生成ID `20261012-evidence-01-ui-r5`。独立した最新VBA・生成器から、SingleFile/IncludeTests/NoStartup ACCDBを新規作成した。Visible=falseのAccess COMでコンパイルし、production MaintainClass / clsStudentService.SaveStudentを通して架空クラス1件・学生3件・CREATE監査4件を登録した。全件の実DAO読返しは [synthetic-data.json](synthetic-data.json)、登録ログは [seed.raw.log](seed.raw.log)、入力版・ハッシュ・原本保護は [results.json](results.json)、読返しの追加確認は [dao-json-postcheck.json](dao-json-postcheck.json)。同じ読返しは方式内 `tests/Evidence/ui-data-r5.json` にも保存した。

実Access FileFormat=12、SELF、外部リンク0。COM Close/Quit時のfixture SHA-256は `4212D3AAA24D84EE09FD1D6CB7A60D81AA669A8DC3046AF65DFBF62F3083420A`。原本は開かず、最終配布SHA-256 `0547CB5FF9D70C5F17F97D42E8D14E5EAEAB6D3CDEDD2B3F0DA9744960B22E2A` は前後一致した。手動撮影後の内部メタデータによるfixtureハッシュ変化は、rootのUI閉鎖記録で区別する。

撮影入口は `Access/build/20261012-evidence-01-ui-r5/20261012-build-04-access-single-evidence-01-ui-r5.accdb`。名前にbuild-04が残るのは既存の使い捨てDBガードの識別文字列を満たすためで、今回の入力・実行IDは上記R5である。自動起動フォームは設定していないので、`frmStudentSearch`を明示表示する。既存の方式内 `tests/Evidence/Show-UiFixture.ps1` はこの新規fixtureを指定して起動できる。

実UIの確認手順:

1. 初期画面で年度・学年・クラス・都道府県の4条件が「すべて」、卒業・退学・未所属がFalse、未検索・20件表示であることを確認する。
2. 検索を押す。既定の在学・休学でTEST-ACE-001／002の2件、卒業を追加すると003を含む3件になる。
3. クラスに「2026・1年・TEST-UI・架空撮影A組」を選ぶ。年度2026と学年1年が同期する。
4. 学年を「学年なし」に変更する。クラスは「すべて」になり、W-STU-107の選択解除通知を保持する。
5. クリアで全4条件が「すべて」、在学・休学だけ対象、未検索へ戻る。未所属を選ぶと年度・学年・クラスは「すべて」のまま非活性になり、このfixtureは全学生が所属済みなので検索は0件となる。
6. 新規登録で実production編集フォームを開く。新規の学籍番号は空、性別0・在学01。空のまま保存した場合の検証メッセージ・入力保持を確認できる。保存はこの使い捨てACE DBだけに作用する。
7. 一覧の学生を開き、TEST-ACE-001の仮名・和暦生年月日・クラスと、登録済み学籍番号が編集不可であることを確認する。直接開く場合のOpenArgsは既存 `1|evidence`、新規 `|evidence`。

配布原本・旧R4 fixtureを開いて撮影しない。共有SQL接続・配備・移行・認可結合は実行していない。撮影画像はrootの実画面記録であり、このseed実行は静止画像や別画面を生成していない。
