# sample-project1 Access品質改善結果

更新日: 2026-10-25。今回の実行IDは`20261025-access-quality`、対象はAccessのみです。Accessの今回の生成・検査記録と、他6方式の前回実行を区別します。全7方式の今回合格を表す集約PASSは付けていません。正式評価値は`null`です。

Accessは本文11ptと標準Rectangleの見出し、新規学籍番号の直接入力、7桁郵便マスクと全量検査付き貼付、完全に架空の初期確認用データ、フォームの初期化と終了時の状態保護を更新しました。原仕様は変更せず、新指示との差分と次回修正案は[仕様問題・改善報告](../../test-project1-spec-bug-report.md)と[適用差分](../srcs/Access/build/generation/user-overrides.json)へ記録しています。共通の初期データ規則とAccessチェックは次回生成に適用します。他6方式へのデータ・ソース更新は今回実行していません。

| 方式 | 今回の状態 | 記録 |
| --- | --- | --- |
| Access | 今回生成・検査済み／入力60ファイル／対象環境内の結果 | [生成記録](../srcs/Access/build/generation/regeneration.json)／[今回の全体試験](../srcs/Access/build/test-results/summary.json)／[配布ACCDB・ソースZIP](../srcs/Access/build/) |
| CSharp_ASPNET | 前回実行 `20261025-regenerate`／今回再生成・再検証なし | [前回方式別記録](../srcs/CSharp_ASPNET/build/generation/regeneration.json) |
| CSharp_WPF | 前回実行 `20261025-regenerate`／今回再生成・再検証なし | [前回方式別記録](../srcs/CSharp_WPF/build/generation/regeneration.json) |
| Vue_CSharpAPI | 前回実行 `20261025-regenerate`／今回再生成・再検証なし | [前回方式別記録](../srcs/Vue_CSharpAPI/build/generation/regeneration.json) |
| VB.NET_WinForms | 前回実行 `20261025-regenerate`／今回再生成・再検証なし | [前回方式別記録](../srcs/VB.NET_WinForms/build/generation/regeneration.json) |
| AS400_RPG | 前回実行 `20261025-regenerate`／今回再生成・再検証なし | [前回方式別記録](../srcs/AS400_RPG/build/generation/regeneration.json) |
| COBOL | 前回実行 `20261025-regenerate`／今回再生成・再検証なし | [前回方式別記録](../srcs/COBOL/build/generation/regeneration.json) |

Accessの検査件数・対応した経路・終了状態・未実施は方式内記録を参照してください。Office 32bit、他DPI/IMEと利用者環境の手動受入、本番配備・通信障害・正式採点は別状態です。旧6方式の入力は規則更新後に凍結し直していないため、旧PASSを現規則の結果として使いません。

## 固定先の集約記録

- [方式別状態](generation/regeneration.json): Access今回1方式と、未再検証の前回6方式を分けています。
- [ソースZIP一覧](generation/source-packages.json): 各entryのrunIdとfreshnessを確認してください。集約runIdはnullで、全7方式の同一実行manifestではありません。
- [最終整合性](test-results/final-integrity.json): Accessの今回の凍結入力・出力・配布物ハッシュと方式内build全件包含を検査し、他6方式は前回証拠を明示します。
- [ソースZIP検査](test-results/source-package-validation.json): Accessの今回の展開・ハッシュ検査と独立ソース13検査を記録し、他6方式の展開証拠はpreviousPreparedへ分けています。
- [前回の規則更新](spec-generation/rule-update.json): 先に行った前提規則の更新記録です。今回Access以外の仕様書再生成を行った記録ではありません。

最終成果は各方式の固定`build/`、作業用・失敗試行・隔離DBは`.tmp/`へ置きます。過去実行別の成果フォルダは増やさず、履歴はGitで管理します。入力・QA・正式な試験コード・fixtureは保持します。

## 前回COBOL仕様変更の許可と根拠

以下は`20261025-regenerate`のCOBOL成果に対応する前回の利用者指定・個別改版証拠です。当該方式を今回更新した記録ではありません。20件のファイル・旧新版・変更前後SHA-256・理由は、方式内のspec-update.jsonと親整合性記録のpreviousRunAuthorizationに保持しています。

Windows実行と認証なしサンプルへの変更は、局所誤記とは別の `user-requested-platform-change` です。19文書の改版とWindows実行環境1文書の新設、計20件を [spec-update.json](../srcs/COBOL/build/generation/spec-update.json) に記録し、追加指定2件・変更前後の版とSHA-256・理由を保持しています。一般の本番認証規則は消去せず、当該前回実行のサンプルprofile例外を明示しました。

- `sample-project1/spec/COBOL/README.md`: 8.5 → 8.6。変更前後のSHA-256・理由はCOBOLの `spec-update.json` に記録。
- `sample-project1/spec/COBOL/プロジェクト情報.md`: 8.4 → 8.5。変更前後のSHA-256・理由はCOBOLの `spec-update.json` に記録。
- `sample-project1/spec/COBOL/共通/00_設計書一覧.md`: 8.5 → 8.6。変更前後のSHA-256・理由はCOBOLの `spec-update.json` に記録。
- `sample-project1/spec/COBOL/共通/01_システム概要.md`: 8.1 → 8.2。変更前後のSHA-256・理由はCOBOLの `spec-update.json` に記録。
- `sample-project1/spec/COBOL/共通/03_共通モジュール設計.md`: 8.3 → 8.4。変更前後のSHA-256・理由はCOBOLの `spec-update.json` に記録。
- `sample-project1/spec/COBOL/共通/04_共通UI部品設計.md`: 8.3 → 8.4。変更前後のSHA-256・理由はCOBOLの `spec-update.json` に記録。
- `sample-project1/spec/COBOL/共通/05_チェック・メッセージ設計.md`: 8.3 → 8.4。変更前後のSHA-256・理由はCOBOLの `spec-update.json` に記録。
- `sample-project1/spec/COBOL/共通/06_要件対応・設計判断.md`: 8.3 → 8.4。変更前後のSHA-256・理由はCOBOLの `spec-update.json` に記録。
- `sample-project1/spec/COBOL/共通/08_データアクセス仕様.md`: 8.4 → 8.5。変更前後のSHA-256・理由はCOBOLの `spec-update.json` に記録。
- `sample-project1/spec/COBOL/共通/方式別/01_共通実装仕様.md`: 8.4 → 8.5。変更前後のSHA-256・理由はCOBOLの `spec-update.json` に記録。
- `sample-project1/spec/COBOL/規約/COBOL.md`: 8.3 → 8.4。変更前後のSHA-256・理由はCOBOLの `spec-update.json` に記録。
- `sample-project1/spec/COBOL/規約/開発規約.md`: 8.2 → 8.3。変更前後のSHA-256・理由はCOBOLの `spec-update.json` に記録。
- `sample-project1/spec/COBOL/規約/全体/開発規約.md`: 8.1 → 8.2。変更前後のSHA-256・理由はCOBOLの `spec-update.json` に記録。
- `sample-project1/spec/COBOL/画面最適化記録.md`: 8.4 → 8.5。変更前後のSHA-256・理由はCOBOLの `spec-update.json` に記録。
- `sample-project1/spec/COBOL/基本設計書/01_学生検索画面.md`: 8.4 → 8.5。変更前後のSHA-256・理由はCOBOLの `spec-update.json` に記録。
- `sample-project1/spec/COBOL/基本設計書/02_学生登録画面.md`: 8.4 → 8.5。変更前後のSHA-256・理由はCOBOLの `spec-update.json` に記録。
- `sample-project1/spec/COBOL/詳細仕様書/01_学生検索画面.md`: 8.5 → 8.6。変更前後のSHA-256・理由はCOBOLの `spec-update.json` に記録。
- `sample-project1/spec/COBOL/詳細仕様書/02_学生登録画面.md`: 8.5 → 8.6。変更前後のSHA-256・理由はCOBOLの `spec-update.json` に記録。
- `sample-project1/spec/COBOL/DB定義/SQLServer/01_DB定義書.md`: 8.3 → 8.4。変更前後のSHA-256・理由はCOBOLの `spec-update.json` に記録。
- `sample-project1/spec/COBOL/共通/方式別/02_Windows実行環境.md`: 新規 → 1.0。変更前後のSHA-256・理由はCOBOLの `spec-update.json` に記録。

最終整合性検査では、当該前回実行の保護入力差分であるこの20ファイルだけを利用者指定の変更として個別に明示し、Git HEADの変更前（新規文書はnull）・現在・凍結入力と証跡を照合します。前段の局所修正5件と混ぜず、QA・fixture・評価基準に対する包括的な例外は設けていません。
