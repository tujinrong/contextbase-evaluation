# Access→ASP.NET Core 訓練結果

2026-10-27。実施反復は2回、利用者指定の上限に到達。追加の変換反復は開始しない。

第1回は本体取得と初期生成を実施し、ビルド・Core36件・メモリ環境ブラウザー8件が通過した。SQL式のCStr内算術、推移依存の警告、監査差分・guard・版、和暦と編集状態を指摘として第2回へ引き継いだ。第1回の結果を完成判定には使用していない。

第2回の最終結果：

| 検査 | 結果 | 固定記録 |
| --- | --- | --- |
| 原本・本体抽出 | hash一致、7表93列7関係2クエリ5フォーム27モジュール/クラス、抽出失敗0件 | ../generation/access-extraction.json |
| 抽出器fixture | 8項目PASS。起動フォーム/AutoExec非実行、Unicode、古い出力除去 | extractor-safety.json |
| Agent機構 | 10件PASS。パス/許可/hash/最大2回、SQL型/式/FK容量、非実行定数抽出 | agent.json |
| Releaseビルド・publish | 0警告・0エラー、配布物生成 | build.json |
| Core | 45件PASS | core.json |
| 専用SQL Server | 11件PASS。保存・監査・重複・権限・競合・guard境界等 | sql.json |
| Webアダプター | 20件PASS。和暦、snapshot、リセット/再読込、旧確認の失効等 | web-adapter.json |
| 実SQL使用ブラウザー | 8件PASS。実フォーム入力、検索/保存/再検索/編集/取消/論理削除、重複確認、CSRF | browser.json |
| 専用DB構造とseed | 7表93列7関係、初期マスタ5分類70コード、冪等再投入、先頭ゼロ | sql-schema.json |
| 起動プロファイル | TrainingSqlで起動し、HTTP200とTRN001/2のSQL検索を確認 | launch.json |
| 逆解析用ソースZIP | 48ファイル、原仕様/期待値/中間物なし、独立展開のReleaseビルド0警告・0エラー | package-isolation.json |
| 独立比較 | IR001～IR004修正を静的確認、未解消指摘0件 | independent-review.json |

SQL Serverの実検証先はローカルSQLEXPRESS／AccessRebuilderTraining_01a17be7（Express17.0.5005.3）。テストは新規の架空キーを使い、作った学生を通常の論理削除経路で後処理した。削除機能がないクラスのQA行は訓練専用DBに残す。原ACCDBの学生行は移行せず、元のTRN初期行は保持している。

この回の内部で、FKの物理容量差、Reloadからのビュー選択、Reset/Reload後の古い確認の失効を修正し再確認した。失敗ログや試行は.tmp/、各回の要約は../generation/training.jsonの固定台帳にある。ブラウザー試験の再実行は同一候補の不具合・試験前提の確認であり、第3回の生成反復を行っていない。

検査条件：.NET SDK10.0.401、net10.0、SqlClient7.1.1、Pkcs9.0.21、依存監査有効、Chromiumの1280×900。検索/編集を目視し、重なりや横方向の切れがないことを確認した。

未確認：原Access実画面での動的差分比較、手動受入、本番Windows認証ホストの配備、参照ライブラリー完全目録、任意ActiveX、他Accessでの一般化、大量件数の性能。formalScore=null。原本・ソースの静的比較と上記の限定した動作検査を、完全互換・本番受入として扱わない。
