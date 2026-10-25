# test-project1 今回のソース再生成結果

更新日: 2026-10-25。実行ID: `20261025-regenerate`。AG-BUILD 7.7。6方式のソースを更新しました。COBOLは確定済み部分を更新し、新Text UIは端末契約待ちです。全7方式の完成や実機受入完了を示す記録ではありません。

## 入力と出力

入力正本は各方式の `test-project1/spec/<方式>/`、ソース正本は `test-project1/srcs/<方式>/` です。表の入力数は方式別仕様と全体規則の凍結ファイル数です。文書ID・版・SHA-256は各方式の `build/generation/inputs.json` に記録し、出力との照合は `outputs.json` に記録します。旧 `srcs/<方式>/spec`、他方式の仕様、`spec-eval` は実装入力にしていません。

| 方式 | 今回の状態 | 凍結入力数 | 今回実行した範囲 | 記録と成果 |
| --- | --- | ---: | --- | --- |
| CSharp_ASPNET | ソース更新済み | 58 | Release publish、Core・HTTPS契約・ログイン、実Razor/JSのブラウザー操作 | [生成記録](../srcs/CSharp_ASPNET/build/generation/generation.md) / [最終結果](../srcs/CSharp_ASPNET/build/) |
| CSharp_WPF | ソース更新済み | 59 | Release publish、Core・fixture・native境界・Framework、実Windowの4ケース | [生成記録](../srcs/CSharp_WPF/build/generation/generation.md) / [最終結果](../srcs/CSharp_WPF/build/) |
| Vue_CSharpAPI | ソース更新済み | 59 | Release publish、Core・HTTPS API、Vue操作と配布bundle＋実Controller | [生成記録](../srcs/Vue_CSharpAPI/build/generation/generation.md) / [最終結果](../srcs/Vue_CSharpAPI/build/) |
| VB.NET_WinForms | ソース更新済み | 59 | Release publish、Core・fixture・Framework、実フォーム245検査 | [生成記録](../srcs/VB.NET_WinForms/build/generation/generation.md) / [最終結果](../srcs/VB.NET_WinForms/build/) |
| AS400_RPG | ソース更新済み | 58 | DDS/RPG/Cソース更新、Windows C実行・静的検査・独立ソースレビュー | [生成記録](../srcs/AS400_RPG/build/generation/generation.md) / [最終結果](../srcs/AS400_RPG/build/) |
| Access | ソース更新済み | 58 | ACCDB生成・VBEコンパイル、実フォーム・全件検索・FK・2プロセス競合 | [生成記録](../srcs/Access/build/generation/generation.md) / [最終結果](../srcs/Access/build/) |
| COBOL | 一部更新・端末契約待ち | 59 | 確定済みSQLカタログ38コマンド・DDL/seed、旧CGI/CLIホストの再ビルド・検査のみ | [生成記録](../srcs/COBOL/build/generation/generation.md) / [最終結果](../srcs/COBOL/build/) |

ASP.NETとVueの既存業務・画面ソースは方式自身の最新仕様と照合し、一致する実装を維持したうえで、DDL/seedと現在入力の追跡情報・配布物を再生成しました。WPFはレイアウトと参照表示、WinFormsとAccessは全件検索・状態保持・実フォーム、RPGは27×132の単画面と補助画面を更新しています。検査件数・対象ファイル・入力/出力版は各生成記録を参照してください。

## COBOLの未完了部分

自身仕様の `QA-TEXT-COBOL` は端末製品・描画ライブラリー・信頼する入力/認証アダプターと検証環境の選定を要求しています。これらの契約が未確定のため、新Text UIの実装を保留しました。再開に必要なAPIと実行条件は [interruption.json](../srcs/COBOL/build/generation/interruption.json) に列挙しています。今回の旧CGI/CLIホスト検査合格を、新Text UIの仕様適合や受入結果にはしていません。

## 検査条件と未実施

WPFとVueは、ロック済みNuGet依存に対する今回の通常復元がNU1902/NU1903で失敗しました。ビルドと契約検査はその呼出しだけ `NuGetAudit=false` とした条件付き結果です。依存版と恒久的な監査設定は変更していません。ASP.NETとWinFormsのビルドは監査有効です。詳細は各方式の検査記録を参照してください。

RPGのIBM iコンパイル・Db2・5250実機、SQL Serverへの適用・接続統合、LinuxのCOBOL本番端末、全画面の手動受入・全DPI/IME検証、配備、正式採点は未実施です。AccessはローカルACE/Accessで検査しました。ブラウザーと.NETフォームのfixture試験は実SQL Server接続試験を表しません。正式評価値は `null` です。

## 仕様内の局所修正

AG-BUILDの局所修正规則に従い、方式内で一意に確定できる旧記載・誤参照を修正して版を上げ、該当方式だけpreflightを再実行しました。業務表・正式な試験期待値を変更する解決はしていません。

- `test-project1/spec/CSharp_WPF/共通/方式別/01_共通実装仕様.md`: 8.4 → 8.5。根拠と変更前後のSHA-256は同方式の `local-spec-fix.json` に記録。
- `test-project1/spec/AS400_RPG/詳細仕様書/02_学生登録画面.md`: 8.5 → 8.6。根拠と変更前後のSHA-256は同方式の `local-spec-fix.json` に記録。
- `test-project1/spec/Access/共通/09_項目制約定義.md`: 8.3 → 8.4。根拠と変更前後のSHA-256は同方式の `local-spec-fix.json` に記録。
- `test-project1/spec/Access/規約/開発規約.md`: 8.2 → 8.3。根拠と変更前後のSHA-256は同方式の `local-spec-fix.json` に記録。
- `test-project1/spec/Access/共通/方式別/01_共通実装仕様.md`: 8.5 → 8.6。根拠と変更前後のSHA-256は同方式の `local-spec-fix.json` に記録。

最終整合性検査は、この5ファイルだけを明示し、Git HEADの変更前・現在の変更後・凍結入力のハッシュが一致する修正記録を要求します。QA・fixture・評価基準に対する包括的な例外は設けていません。

## 共通の最終検査

- [最終整合性検査](test-results/final-integrity.json): 全方式の凍結入力・ソース・アプリ・検査記録・配布物のハッシュ、固定配置、Git包含/除外、保護入力差分と局所修正証跡。
- [独立配置検査](test-results/isolation.json): 自身仕様への参照の閉鎖、共有元・他方式への依存検査。
- [preflight回帰検査](test-results/preflight-tests.json): 52項目PASS。正本配置・入力範囲・読取り専用検査・旧合格の失効。
- [出力配置回帰検査](test-results/output-layout-tests.json): 8テストPASS。固定パス更新・ZIP除外・隔離展開・リンク拒否。
- [ソースZIP検査](test-results/source-package-validation.json): 全7方式のZIPメンバー・ハッシュを照合し、それぞれ `.tmp/source-isolation/` に展開。`--hashes-only` のためZIPからの再ビルドは未実施です。
- [ソースZIP一覧](generation/source-packages.json) / [方式別状態一覧](generation/regeneration.json)。COBOLのZIPにも `PARTIAL_BLOCKED` を明記しています。

最終ソースは正本を更新し、配布物・今回の検査記録・入出力manifestは各方式の `build/` の固定パスへ更新しました。中間生成・失敗試行・キャッシュ・隔離展開は各方式の `.tmp/`、共通制御はAgentまたはprojectの `.tmp/` を使用しています。`.tmp/` はGit管理対象外で、過去の日付・実行ID・attemptごとの成果を `build/` に累積しません。入力・QA・正式な試験コード・fixtureは保持しています。Gitのcommit/pushは実行していません。
