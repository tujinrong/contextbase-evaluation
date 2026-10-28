# Access 補助fixtureと検査正本

このフォルダーの `.bas`、PowerShell、架空値JSONは正式な試験資源として保持します。R4/R5/R6の名前は対象fixture契約を識別するもので、生成履歴の保存先ではありません。旧検索項目を前提にするR5等の検査を現在版の合格として扱いません。現在版の入口は `../Invoke-Verification.ps1` です。

補助試験の生成ACCDB・VBE出力・画面準備用JSON・ログは方式内 `.tmp/evidence/` の固定名へ出力し、再実行時に更新します。製品ACCDBは `build/StudentManagement.accdb` です。補助スクリプトは製品を開かず、SHA-256の前後照合で無変更を確認します。UI表示用の `Show-UiFixture.ps1` は明示実行時にだけ表示し、今回の自動検証では起動しません。

`Seed-UiFixture*.ps1` は各 `.tmp/evidence/ui*` に独立した架空データDBを作ります。原仕様・fixture正本・QAは削除しません。既存成果に依存する引数は現在の配布ハッシュを渡し、過去の固定ハッシュや過去検査のPASSを流用しません。
