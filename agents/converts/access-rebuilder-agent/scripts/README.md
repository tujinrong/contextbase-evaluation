# 工程用スクリプト

リポジトリから実行する。今回のsample-project1は既に2回の訓練を完了する台帳を持つため、同じプロファイルでbegin-iterationを再実行して訓練を増やさない。

```powershell
node agents/converts/access-rebuilder-agent/scripts/rebuild.mjs status
node --test agents/converts/access-rebuilder-agent/tests/*.test.mjs
```

新しい許可済み実行では、requestへ入力・対象方式・範囲・反復上限を設定してprepare→begin-iterationを行う。tests/Test-AccessExtractor.ps1で指定方式内の使い捨てfixtureを検査し、Export-Access.ps1へSourceFile、TargetRoot、ExpectedSha256、SafetyFixtureVerifiedを渡して取得する。

emit-sql.mjsはrequestを検査して同方式の抽出manifestからSQLと型対応を生成する。C#業務コードはprompts/convert.mdに従ってCodexが作成し、prompts/review.mdに従って独立比較する。検証結果をbuild/test-results/のJSONへ保存し、rebuild.mjs complete-iteration --result <リポジトリ相対JSON>で入力hashと回番号を照合して終了する。

rebuild.mjs manifestで出力hash、Package-Source.ps1 -TargetRoot <方式ルート>で固定build/source.zipを作成する。旧build-agentの仕様入力preflightをAccess入力へ流用しない。DB実行はrequestに許可と専用接続先がある範囲だけで行う。
