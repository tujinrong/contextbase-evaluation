# VB 新規実行・画面撮影fixture

実行ID `20261012-evidence-01`、2026-10-12、project `test-project1`、AG-BUILD7.5。**今回の非SQL検査149件がPASS、実画面ソースの撮影入口を準備済み。** 過去のPASSは転記していない。GUI操作・撮影はrootへ引継ぎ、この担当はまだ実行していない。

| 今回実行した検査 | PASS数 | 範囲 |
| --- | ---: | --- |
| Core/Controls/raw wire | 111 | 正規化/入力/未表示Form生成/XML。SQL非接続 |
| actual .NET Framework | 23 | 当方式のnet472 DLLをCLR4.0.30319.42000で実行。SQL Server hostingは未実施 |
| 新規画面fixture | 15 | 原本Form/Presenterによる未表示検索・読込・新規・入力保持 |

ビルドは各0警告0エラー。.NET SDK10.0.401。Option Strict/Explicit/InferはOn。新harnessソースのうち、業務アプリ側はVB.NET、既存の独立SQLCLR試験資源は方式内C#のまま実行した。

## 入力と独立データ

`inputs.json` に方式内spec46ファイルの版/hashとproductionソース/hashを固定し、試験後すべて一致を確認した。文書版は8.0/8.1、検索・登録詳細/方式規約/方式別共通/SQLServer DB定義は8.0。原仕様、runtimeコード、業務DDLを変更していない。既存Tests.vbprojだけにGuiEvidence/**/*.vbのCompile除外を追加し、テスト用アダプターが既存テストへ混入することを防いだ。

方式専用 `Tests/GuiEvidence/fixture.json` と当報告の `fixture-data.json` は同じ架空3件。fixture SHA-256: `C7DF1D4F80618D9AC123D72D317F36749378BC9174A046CB013C080678B6029A`。学籍番号TEST-VB-001..003、氏名は仮名太郎/花子/次郎、メールはexample.invalid。SQL配備初期データとは別で、DBへ保存していない。

## rootへ渡す実画面入口

起動exe:

`D:\開発\contextbase-evaluation\test-project1\srcs\VB.NET_WinForms\Tests\GuiEvidence\bin\Debug\net10.0-windows\Vb.GuiEvidence.exe`

| 引数 | 実画面ソース |
| --- | --- |
| `--screen search` | 原本FrmStudentSearch。Shown後のfixture検索で在学/休学の2行 |
| `--screen new` | 原本FrmStudentEdit。新規の初期値 |
| `--screen edit` | 原本FrmStudentEdit。TEST-VB-001、仮名太郎、所属クラス、更新情報 |

任意で `--role viewer` / `--role staff` / `--role admin`。検索から「新規登録」/行の編集という通常イベントも利用できる。登録画面下部はスクロールして撮影する。

production Form/Presenterは具象StudentApplicationServiceを要求し、認証メソッドはvirtualではない。そのためこのハーネスは原本Forms/Presenters/Controls/Domain/Infrastructureを当方式内Linkで無変更コンパイルし、ApplicationServiceだけをテスト専用同型クラスで置換する。test-onlyクラスはIStudentService fixtureへ委譲する。production実行ファイルのSQL認証アダプターの試験にはならない。別画面や静的画像は生成していない。原本UIソース/hashは `inputs.json`、新ソース/バイナリhashは `results.json` に記録する。

## 証拠と未実施

今回コマンド/終了値は `existing-test-commands.json`、生ログは `core-controls-*`, `framework-*`, `fixture-*`。新fixture機械結果は `fixture-test.log` のJSON。生成ソースの手順は方式内 `Tests/GuiEvidence/README.md` にある。

fixtureの保存・削除は明示拒否し、Savedを返さない。fixture roleは表示制御だけで、Windows/DB認可ではない。共有DBの構造契約修正待ちは維持している。SQL接続/DDL/共有schema/API/SQLCLR hosting/永続CRUD/競合/非sysadmin主体、およびこの担当によるGUI起動・操作・撮影は **NOT_RUN**。実DB結合合格やスクリーンショット取得済みとの判定は出していない。
