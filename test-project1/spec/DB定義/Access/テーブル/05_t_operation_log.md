<!-- spec-meta: {"schema":"spec-md/1.1","documentId":"DBDEF-ACCESS-T_OPERATION_LOG","version":"7.1","path":"test-project1/spec/DB定義/Access/テーブル/05_t_operation_log.md","layout":"TABLE","table":{"logicalName":"操作履歴","physicalName":"t_operation_log","profile":"Access","primaryKey":["log_id"],"fieldIds":{"log_id":"DB-T_OPERATION_LOG-LOG_ID","target_table":"DB-T_OPERATION_LOG-TARGET_TABLE","target_key":"DB-T_OPERATION_LOG-TARGET_KEY","operation_type":"DB-T_OPERATION_LOG-OPERATION_TYPE","before_version":"DB-T_OPERATION_LOG-BEFORE_VERSION","after_version":"DB-T_OPERATION_LOG-AFTER_VERSION","changed_columns":"DB-T_OPERATION_LOG-CHANGED_COLUMNS","executed_by":"DB-T_OPERATION_LOG-EXECUTED_BY","executed_at":"DB-T_OPERATION_LOG-EXECUTED_AT","correlation_id":"DB-T_OPERATION_LOG-CORRELATION_ID","operation_reason":"DB-T_OPERATION_LOG-OPERATION_REASON","duplicate_confirmed":"DB-T_OPERATION_LOG-DUPLICATE_CONFIRMED"}},"sheets":[{"sheet":"t_operation_log","kind":"TABLE","sections":[{"heading":"テーブルヘッダー","kind":"HEADER"},{"heading":"項目詳細","kind":"LIST","key":["No"],"columns":["No","論理名","物理名","PK","タイプ","長さ","初期値","説明"]}]}]} -->
# 操作履歴 DB定義書

## テーブルヘッダー

| 項目 | 内容 |
| --- | --- |
| 文書ID／版 | DBDEF-ACCESS-T_OPERATION_LOG／7.1／2026-10-12 |
| 論理テーブル名 | 操作履歴 |
| 物理テーブル名 | t_operation_log |
| 対象／スキーマ | Access／非適用（ACE） |
| 用途／項目数 | 確定した変更１件を追記。個人情報の変更前後値は保持しない。 12項目。 |
| 主キー（順序） | log_id |
| 共通規則・制約 | [総合仕様・制約](../01_DB定義書.md)／[記述・Excel配置規約](../../../../../docs/テーブル仕様書記述規約.md) |
| 長さ／初期値の基準 | 長さは業務上限。数字は整数桁.小数桁。初期値はDB既定値。画面の初期値とは別。 |
| 項目IDの対応 | 物理列に対応する既存DB項目IDを維持。メタ情報fieldIdsに対応を記録。 |
| 基礎仕様 | [論理テーブル仕様](../../../基本設計書/03_テーブル仕様書.md)／[項目制約](../../../共通/09_項目制約定義.md) |

## 項目詳細

| No | 論理名 | 物理名 | PK | タイプ | 長さ | 初期値 | 説明 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | 操作履歴番号 | log_id | 〇 | 数字 | 10.0 | 自動採番 | 自動。DB:COUNTER／NULL不可。追記記録の識別子。 |
| 2 | 対象情報の種類 | target_table | － | 文字 | 21 | 指定なし | 自動。DB:TEXT(42)／NULL不可。学生、クラス、コード分類、コード値のいずれか。 |
| 3 | 対象の識別情報 | target_key | － | 文字 | 35 | 指定なし | 自動。DB:TEXT(70)／NULL不可。管理番号または分類と値。氏名等を含めない。 |
| 4 | 操作の種類 | operation_type | － | 文字 | 11 | 指定なし | 自動。DB:TEXT(22)／NULL不可。新規・変更・論理削除・停止・再開。 |
| 5 | 変更前の更新管理番号 | before_version | － | 数字 | 10.0 | 指定なし | 新規以外必須。DB:LONG／NULL可。新規は空。 |
| 6 | 変更後の更新管理番号 | after_version | － | 数字 | 10.0 | 指定なし | 自動。DB:LONG／NULL不可。新規は1、変更は以前の番号＋1。 |
| 7 | 変更項目一覧 | changed_columns | － | 配列 | － | 指定なし | 自動。DB:LONGTEXT／NULL不可。変更した項目を記録。入力値自体は複写しない。許可列名のJSON配列、実値は保持しない。 |
| 8 | 実行者 | executed_by | － | 文字 | 64 | 指定なし | 自動。DB:TEXT(128)／NULL不可。認証された利用者番号。 |
| 9 | 実行日時 | executed_at | － | 日時 | － | 指定なし | 自動。DB:DATETIME／NULL不可。対応する保存操作の日時。 |
| 10 | 受付番号 | correlation_id | － | 識別子 | － | 指定なし | 自動。DB:TEXT(36)／NULL不可。障害調査用。同一要求で関連付ける。 |
| 11 | 操作・確認理由 | operation_reason | － | 文字 | 60 | 指定なし | 条件付き。DB:TEXT(120)／NULL可。削除・終了区分訂正・重複警告続行時は必須。 |
| 12 | 重複警告の確認有無 | duplicate_confirmed | － | 真偽 | － | False | 自動。DB:YESNO／NULL不可。別人確認を経た保存で有。 |
