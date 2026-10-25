# build-agent

定義版7.6／2026-10-24。[契約](AGENT.md)・[起動指示](PROMPT.md)に従い、選択projectの各方式specから独立したシステムを更新する。業務コード・DB・試験の横断共用はしない。

最終ソースはsrcs/方式ID/の正本を更新する。最終配布物は方式内build/app・build/publish等、Accessはbuild/StudentManagement.accdb1個。最終検査記録はbuild/test-results/、入力・出力manifestはbuild/generation/、解析用ZIPはbuild/source.zipへ固定名で更新し、Gitで履歴を管理する。中間生成・失敗試行・処理系・cache・隔離展開は各方式.tmp/へ置く。過去成果をrun-id別・backup別に累積しない。共通集約だけproject/build/、共通作業だけproject/.tmp/を使用する。

```powershell
node agents/build-agent/scripts/preflight.mjs --project test-project1 --profile CSharp_ASPNET --run-id current
python -X utf8 test-project1/srcs/CSharp_ASPNET/tools/build.py
python -X utf8 agents/build-agent/scripts/package-source.py current --profile CSharp_ASPNET
python -X utf8 agents/build-agent/scripts/verify-packages.py current --profile CSharp_ASPNET --hashes-only
node agents/build-agent/scripts/manifest.mjs --project test-project1 --profile CSharp_ASPNET --run-id current
```

run-idは記録の属性であり、同名再実行も固定出力先を更新する。preflightは旧outputs.jsonと旧ZIPを失効させる。manifestは今回のproject/profile/run-idと凍結入力hashを照合し、古いpackageを現在の成果として収録しない。入力が変更されたらpreflightからやり直す。構造PASS・hash一致は実装合格や正式受入ではない。

--hashes-onlyはZIPの全メンバーhash・除外境界・方式内の別展開だけを検証する。省略時は利用可能な独立.NET/native/Vueビルドも実行するが、SQLやIBM i等の受入とは別に記録する。ZIPには原仕様・spec-eval・試験期待値・中間物を含めず、production buildに必須の配置helperだけを許可する。

工程制御の回帰検査はnode agents/build-agent/scripts/preflight-tests.mjsとpython -X utf8 agents/build-agent/scripts/output-layout-tests.py。isolate-*、split-dotnet-tests、materialize-*、旧文書生成補助は一度限りの移送資源であり、現行アプリへ再実行しない。

共有SQL Server DB移行は認証・権限・排他・正規化等の共有契約を確認してから扱う。インストール・DB作成・配備は本配置修正の実行範囲に含めない。SQL補助の中間物はproject/.tmp/sqlserver-setup、最終記録はproject/buildの固定先へ出力する。既存DBを上書きしない安全条件は継続する。環境不足・未実施・失敗を最終記録へ明記し、以前のPASSを流用しない。
