<!-- spec-meta: {"schema":"spec-md/1.1","documentId":"CSHARP_ASPNET-DBDEF-SQLSERVER-T_OPERATION_LOG","version":"8.0","path":"test-project1/srcs/CSharp_ASPNET/spec/DB定義/SQLServer/テーブル/05_t_operation_log.md","layout":"TABLE","table":{"logicalName":"操作履歴","physicalName":"t_operation_log","profile":"SQLServer","primaryKey":["log_id"],"fieldIds":{"log_id":"DB-T_OPERATION_LOG-LOG_ID","target_table":"DB-T_OPERATION_LOG-TARGET_TABLE","target_key":"DB-T_OPERATION_LOG-TARGET_KEY","operation_type":"DB-T_OPERATION_LOG-OPERATION_TYPE","before_version":"DB-T_OPERATION_LOG-BEFORE_VERSION","after_version":"DB-T_OPERATION_LOG-AFTER_VERSION","changed_columns":"DB-T_OPERATION_LOG-CHANGED_COLUMNS","executed_by":"DB-T_OPERATION_LOG-EXECUTED_BY","executed_at":"DB-T_OPERATION_LOG-EXECUTED_AT","correlation_id":"DB-T_OPERATION_LOG-CORRELATION_ID","operation_reason":"DB-T_OPERATION_LOG-OPERATION_REASON","duplicate_confirmed":"DB-T_OPERATION_LOG-DUPLICATE_CONFIRMED"}},"sheets":[{"sheet":"t_operation_log","kind":"TABLE","sections":[{"heading":"テーブルヘッダー","kind":"HEADER"},{"heading":"項目詳細","kind":"LIST","key":["No"],"columns":["No","論理名","物理名","PK","NOT NULL","タイプ","長さ","初期値","説明"]}]}],"isolationProfile":"CSharp_ASPNET"} -->
# 操作履歴 DB定義書

## テーブルヘッダー

| 項目 | 内容 |
| --- | --- |
| 文書ID／版 | DBDEF-SQLSERVER-T_OPERATION_LOG／8.0／2026-10-12 |
| 論理テーブル名 | 操作履歴 |
| 物理テーブル名 | t_operation_log |
| 対象／スキーマ | SQLServer／dbo |
| 用途／項目数 | 確定した変更１件を追記。個人情報の変更前後値は保持しない。 12項目。 |
| 主キー（順序） | log_id |
| 共通規則・制約 | [総合仕様・制約](../01_DB定義書.md)／[記述・Excel配置規約](../../../規約/全体/テーブル仕様書記述規約.md) |
| 長さ／初期値の基準 | 長さは業務上限、タイプはDB型・容量。初期値はDB既定値。 |
| 項目IDの対応 | 物理列に対応する既存DB項目IDを維持。メタ情報fieldIdsに対応を記録。 |
| 基礎仕様 | [論理テーブル仕様](../../../基本設計書/03_テーブル仕様書.md)／[項目制約](../../../共通/09_項目制約定義.md) |
| 記号 | PK・NOT NULL：〇が該当、空欄は非該当。初期値なし・長さ対象外は空欄。条件付き必須は説明参照。 |

## 項目詳細

| No | 論理名 | 物理名 | PK | NOT NULL | タイプ | 長さ | 初期値 | 説明 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | 操作履歴番号 | log_id | 〇 | 〇 | bigint | 19.0 | 自動採番 | IDENTITY(1,1)。追記記録の識別子。 |
| 2 | 対象情報の種類 | target_table |  | 〇 | varchar(21) | 21 |  | 自動。学生、クラス、コード分類、コード値のいずれか。 |
| 3 | 対象の識別情報 | target_key |  | 〇 | varchar(35) | 35 |  | 自動。管理番号または分類と値。氏名等を含めない。 |
| 4 | 操作の種類 | operation_type |  | 〇 | varchar(11) | 11 |  | 自動。新規・変更・論理削除・停止・再開。 |
| 5 | 変更前の更新管理番号 | before_version |  |  | bigint | 19.0 |  | 新規以外必須。新規は空。 |
| 6 | 変更後の更新管理番号 | after_version |  | 〇 | bigint | 19.0 |  | 自動。新規は1、変更は以前の番号＋1。 |
| 7 | 変更項目一覧 | changed_columns |  | 〇 | nvarchar(max) |  |  | 自動。変更した項目を記録。入力値自体は複写しない。許可列名のJSON配列、実値は保持しない。ISJSON=1に加え配列型・許可列名・重複なしを保存入口で検査。 |
| 8 | 実行者 | executed_by |  | 〇 | nvarchar(128) | 64 |  | 自動。認証された利用者番号。 |
| 9 | 実行日時 | executed_at |  | 〇 | datetimeoffset(7) |  |  | 自動。対応する保存操作の日時。 |
| 10 | 受付番号 | correlation_id |  | 〇 | uniqueidentifier |  |  | 自動。障害調査用。同一要求で関連付ける。 |
| 11 | 操作・確認理由 | operation_reason |  |  | nvarchar(120) | 60 |  | 条件付き。削除・終了区分訂正・重複警告続行時は必須。 |
| 12 | 重複警告の確認有無 | duplicate_confirmed |  | 〇 | bit |  | 0 | 自動。別人確認を経た保存で有。 |
