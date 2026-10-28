# build-agent

定義版7.8／2026-10-25。[契約](AGENT.md)・[起動指示](PROMPT.md)に従い、選択方式のspecRoot=project/spec/方式ID/からsourceRoot=project/srcs/方式ID/へ独立したシステムを生成する。旧sourceRoot/specへの自動復帰や他方式仕様の共用は行わない。業務コード・DB・試験の横断共用はしない。

最終ソースはsrcs/方式ID/の正本を更新する。最終配布物は方式内build/app・build/publish等、Accessはbuild/StudentManagement.accdb1個。最終検査記録はbuild/test-results/、入力・出力manifestはbuild/generation/、解析用ZIPはbuild/source.zipへ固定名で更新し、Gitで履歴を管理する。中間生成・失敗試行・処理系・cache・隔離展開は各方式.tmp/へ置く。過去成果をrun-id別・backup別に累積しない。共通集約だけproject/build/、共通作業だけproject/.tmp/を使用する。

全方式の次回生成は[テストデータ整備規約](../../../docs/テストデータ整備規約.md)に従い、起動後に検索・新規登録・編集を試せる架空の初期確認用データと確認手順を備える。必要マスタ、確認用の業務行、異常系fixture、利用者の既存データを分け、初回投入と冪等な再投入・既存値保護を検査し、件数と基準日を固定manifestへ残す。共通規則の追加だけで指定外方式の投入済みとは扱わない。

Accessの生成・更新では[Access生成チェック](docs/Access生成チェック.md)を併用する。標準フォーム/部品、フォントとグループ見出し、モード別の入力属性、マスク/表示/保存の契約を確認し、実ACCDBのキーボード/貼付操作と画面表示を検査する。VBAコンパイルやプロパティ検査のみで入力と可読性を保証しない。

```powershell
node agents/builds/build-agent/scripts/preflight.mjs --project sample-project1 --profile CSharp_ASPNET --run-id current
python -X utf8 sample-project1/srcs/CSharp_ASPNET/tools/build.py
python -X utf8 agents/builds/build-agent/scripts/package-source.py current --profile CSharp_ASPNET
python -X utf8 agents/builds/build-agent/scripts/verify-packages.py current --profile CSharp_ASPNET --hashes-only
node agents/builds/build-agent/scripts/manifest.mjs --project sample-project1 --profile CSharp_ASPNET --run-id current
```

配置検査だけを行う場合は上記preflightへ`--inspect-only true`を付ける。inputs/structureは標準出力JSONへ返し、build/と.tmp/への書込み、旧outputs.jsonの失効、source.zipの移動は行わない。検査専用結果からmanifestを確定せず、実装生成時は通常preflightを実行する。

run-idは記録の属性であり、同名再実行も固定出力先を更新する。preflightは旧outputs.jsonと旧ZIPを失効させる。manifestは今回のproject/profile/run-idと凍結入力hashを照合し、古いpackageを現在の成果として収録しない。入力が変更されたらpreflightからやり直す。構造PASS・hash一致は実装合格や正式受入ではない。

--hashes-onlyはZIPの全メンバーhash・除外境界・方式内の別展開だけを検証する。省略時は利用可能な独立.NET/native/Vueビルドも実行するが、SQLやIBM i等の受入とは別に記録する。ZIPには原仕様・project/spec/全体・spec-eval・試験期待値・中間物を含めず、production buildに必須の配置helperだけを許可する。

工程制御の回帰検査はnode agents/builds/build-agent/scripts/preflight-tests.mjsとpython -X utf8 agents/builds/build-agent/scripts/output-layout-tests.py。isolate-*、split-dotnet-tests、materialize-*、旧文書生成補助は一度限りの移送資源であり、現行アプリへ再実行しない。旧仕様配置を生成するisolate-specs・finalize-isolation-docs・document-dotnet-projectsは現配置の正本作成に使用しない。

共有SQL Server DB移行は認証・権限・排他・正規化等の共有契約を確認してから扱う。インストール・DB作成・配備は本配置修正の実行範囲に含めない。SQL補助の中間物はproject/.tmp/sqlserver-setup、最終記録はproject/buildの固定先へ出力する。既存DBを上書きしない安全条件は継続する。環境不足・未実施・失敗を最終記録へ明記し、以前のPASSを流用しない。
