# test-project1 最新生成結果

更新日: 2026-10-24。入力識別子: `20261024-layout`。全7方式の出力配置を更新しました。仕様本文・評価基準・業務上の期待値は変更していません。

## 出力規則

- ソースは各方式の既存配置を更新し、完成したアプリ・配布物・現在の検査記録は `srcs/<方式>/build/` の固定パスへ更新します。
- 凍結入力、構造検査、出力ハッシュは `build/generation/`、検査結果は `build/test-results/`、解析用ソースZIPは `build/source.zip` に格納します。実行IDは記録の属性です。
- 中間物、依存キャッシュ、作業コピー、分離検証先は各方式の `.tmp/` に生成します。共通制御の作業物はプロジェクトまたはAgent自身の `.tmp/` に格納します。
- 最終結果をGitで管理し、すべての `.tmp/` を除外します。過去の実行ID・日付・試行ごとの生成結果を最終出力へ蓄積しません。再実行時には以前の検査合格を失効させ、今回の結果を記録します。

## 方式別の現在結果

| 方式 | 最終アプリ・配布物 | 検査記録 | 入出力記録 |
| --- | --- | --- | --- |
| VB.NET WinForms | [build](../srcs/VB.NET_WinForms/build/) | [test-results](../srcs/VB.NET_WinForms/build/test-results/) | [generation](../srcs/VB.NET_WinForms/build/generation/) |
| C# WPF | [build](../srcs/CSharp_WPF/build/) | [test-results](../srcs/CSharp_WPF/build/test-results/) | [generation](../srcs/CSharp_WPF/build/generation/) |
| C# ASP.NET | [build](../srcs/CSharp_ASPNET/build/) | [test-results](../srcs/CSharp_ASPNET/build/test-results/) | [generation](../srcs/CSharp_ASPNET/build/generation/) |
| Vue + C# API | [build](../srcs/Vue_CSharpAPI/build/) | [test-results](../srcs/Vue_CSharpAPI/build/test-results/) | [generation](../srcs/Vue_CSharpAPI/build/generation/) |
| COBOL | [build](../srcs/COBOL/build/) | [test-results](../srcs/COBOL/build/test-results/) | [generation](../srcs/COBOL/build/generation/) |
| AS400 RPG | [build](../srcs/AS400_RPG/build/) | [test-results](../srcs/AS400_RPG/build/test-results/) | [generation](../srcs/AS400_RPG/build/generation/) |
| Access | [StudentManagement.accdb](../srcs/Access/build/StudentManagement.accdb) | [test-results](../srcs/Access/build/test-results/) | [generation](../srcs/Access/build/generation/) |

.NET 4方式はビルドと既存契約検査、COBOLはWindowsホスト検査、RPGはCホストと静的検査、AccessはVBEコンパイル・業務検査・参照整合性・配置・競合検査を実行しました。各方式の記録に実行条件と未実施範囲を記載しています。

WPFとVueは既存のロック済みNuGet依存に対する監査エラーにより、通常の復元が失敗します。今回のビルド・契約検査は、その呼出しだけ `NuGetAudit=false` とした条件付き結果です。依存バージョンと恒久的な監査設定は変更していません。通常条件での復元成功を表しません。詳細は両方式の `build/test-results/audit-status.json` を参照してください。

## 共通検査

- [最終整合性検査](test-results/final-integrity.json): 凍結入力・ソース・最終成果・配布記録のハッシュ、固定配置、Gitへの包含と除外、保護入力の差分。
- [独立配置検査](test-results/isolation.json): 7方式のローカル参照、仕様書への参照、共有元・他方式への依存。
- [出力配置の回帰検査](test-results/output-layout-tests.json): 再実行での更新、旧合格の失効、除外、アーカイブ展開、リンクによる入力破壊の拒否。
- [ソースZIP検査](test-results/source-package-validation.json): 全7方式のメンバー照合と各方式 `.tmp/source-isolation/` への展開。今回は `--hashes-only` であり、ZIPからの再ビルドは実行していません。
- [ソースZIP一覧](generation/source-packages.json): 各方式 `build/source.zip` の現在ハッシュと収録ソース。

SQL Serverへの適用・接続統合試験、LinuxでのCOBOL本番構成、IBM iネイティブ実行、全画面の手動操作、正式採点は今回未実施です。正式評価値は `null` です。

## 旧出力の整理

旧 `report/`、世代別の検査記録、`agent-input/` の旧ZIP、旧方式別の作業物は、現在の最終出力から外して対応する `.tmp/legacy-work/` へ可逆移動しました。旧SQL Serverセットアップ資材はプロジェクトの `.tmp/sqlserver-setup/` に移動しました。新しい生成処理はこれらを参照・更新しません。

旧生成物の削除は自動承認レビューで `blocked by policy` と拒否されたため、削除を再試行せず、Git除外対象への移動で整理しています。
