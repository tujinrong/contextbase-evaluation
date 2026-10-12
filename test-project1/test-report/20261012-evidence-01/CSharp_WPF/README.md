# WPF 新規実行・画面撮影fixture

実行ID `20261012-evidence-01`、2026-10-12、project `test-project1`、AG-BUILD7.5。**今回の非SQL検査244件がPASS、実画面の撮影入口を準備済み。** 過去のPASSは転記していない。GUI操作・撮影はrootへ引継ぎ、この担当はまだ実行していない。

| 今回実行した検査 | PASS数 | 範囲 |
| --- | ---: | --- |
| Core | 96 | 純粋正規化/入力/境界。SQL非接続 |
| production XAML/VM Smoke | 7 | 未表示Window生成、検索条件状態。SQL非接続 |
| native境界 | 102 | raw XML・正規化・メッセージ・最小候補DTO。SQL非接続 |
| actual .NET Framework | 27 | 当方式のnet472 DLLをCLR4.0.30319.42000で実行。SQL Server hostingは未実施 |
| 新規画面fixture | 12 | 原本Window/VMをfixture gatewayで未表示試験 |

最終ビルドは各0警告0エラー。.NET SDK10.0.401。新harnessの最初のビルドはSystem.IO imports欠落の3エラーで失敗し、fixtureコードだけを補正して再ビルド成功した。初回 `fixture-build.log` は保持し、成功は `fixture-build-r2.log` に記録した。

## 入力と独立データ

`inputs.json` に方式内spec46ファイルの版/hashとproductionソース/hashを固定し、試験後すべて一致を確認した。文書版は8.0/8.1、検索・登録詳細/方式規約/方式別共通/SQLServer DB定義は8.0。原仕様、runtimeコード、業務DDLを変更していない。`results.json` に今回のtestソースと起動バイナリhashも収録する。

方式専用 `tests/GuiEvidence/fixture.json` と当報告の `fixture-data.json` は同じ架空3件。fixture SHA-256: `E01889280FE00AEC2A2984EFC1FEE8E4F3AEB027DBEA4EB7248E0DF3C26BAFD0`。学籍番号TEST-WPF-001..003、氏名は仮名太郎/花子/次郎、メールはexample.invalid。SQL配備初期データとは別で、DBへ保存していない。

## rootへ渡す実画面入口

起動exe:

`D:\開発\contextbase-evaluation\test-project1\srcs\CSharp_WPF\tests\GuiEvidence\bin\Debug\net10.0-windows\Wpf.GuiEvidence.exe`

| 引数 | 実画面 |
| --- | --- |
| `--screen search` | 原本StudentSearchView。Loaded後のfixture検索で在学/休学の2行 |
| `--screen new` | 原本StudentEditView。新規の初期値 |
| `--screen edit` | 原本StudentEditView。TEST-WPF-001、仮名太郎、所属クラス、更新情報 |

任意で `--role viewer` / `--role staff` / `--role admin`。検索から「新規登録」「開く」の通常イベントも利用できる。登録画面下部はスクロールして撮影する。入口は原本App.xaml resourcesと原本Window/VMを使用し、起動だけをテスト専用派生Appに置換してSQL起動を避ける。撮影はウィンドウを実際に表示して行い、仕様モックPNGや静的画像で代替しない。

## 証拠と未実施

今回コマンド/終了値は `existing-test-commands.json`、生ログは `core-*`, `smoke-*`, `boundary-*`, `framework-*`, `fixture-*`。新fixtureの機械結果は `fixture-test.log` のJSON。生成ソースの手順は方式内 `tests/GuiEvidence/README.md` にある。

fixtureの保存・削除は明示拒否し、Savedを返さない。fixture roleは表示制御だけで、Windows/DB認可ではない。共有DBの構造契約修正待ちは維持している。SQL接続/DDL/共有schema/API/SQLCLR hosting/永続CRUD/競合/非sysadmin主体、およびこの担当によるGUI起動・操作・撮影は **NOT_RUN**。実DB結合合格やスクリーンショット取得済みとの判定は出していない。
