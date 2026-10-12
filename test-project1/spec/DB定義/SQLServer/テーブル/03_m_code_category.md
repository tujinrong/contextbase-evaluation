<!-- spec-meta: {"schema":"spec-md/1.1","documentId":"DBDEF-SQLSERVER-M_CODE_CATEGORY","version":"7.1","path":"test-project1/spec/DB定義/SQLServer/テーブル/03_m_code_category.md","layout":"TABLE","table":{"logicalName":"コード種別マスタ","physicalName":"m_code_category","profile":"SQLServer","primaryKey":["category_id"],"fieldIds":{"category_id":"DB-M_CODE_CATEGORY-CATEGORY_ID","category_name":"DB-M_CODE_CATEGORY-CATEGORY_NAME","code_length":"DB-M_CODE_CATEGORY-CODE_LENGTH","allow_add":"DB-M_CODE_CATEGORY-ALLOW_ADD","is_active":"DB-M_CODE_CATEGORY-IS_ACTIVE","remarks":"DB-M_CODE_CATEGORY-REMARKS","created_at":"DB-M_CODE_CATEGORY-CREATED_AT","created_by":"DB-M_CODE_CATEGORY-CREATED_BY","updated_at":"DB-M_CODE_CATEGORY-UPDATED_AT","updated_by":"DB-M_CODE_CATEGORY-UPDATED_BY","row_version":"DB-M_CODE_CATEGORY-ROW_VERSION"}},"sheets":[{"sheet":"m_code_category","kind":"TABLE","sections":[{"heading":"テーブルヘッダー","kind":"HEADER"},{"heading":"項目詳細","kind":"LIST","key":["No"],"columns":["No","論理名","物理名","PK","タイプ","長さ","初期値","説明"]}]}]} -->
# コード種別マスタ DB定義書

## テーブルヘッダー

| 項目 | 内容 |
| --- | --- |
| 文書ID／版 | DBDEF-SQLSERVER-M_CODE_CATEGORY／7.1／2026-10-12 |
| 論理テーブル名 | コード種別マスタ |
| 物理テーブル名 | m_code_category |
| 対象／スキーマ | SQLServer／dbo |
| 用途／項目数 | コード分類１件の桁数・保守条件を管理。 11項目。 |
| 主キー（順序） | category_id |
| 共通規則・制約 | [総合仕様・制約](../01_DB定義書.md)／[記述・Excel配置規約](../../../../../docs/テーブル仕様書記述規約.md) |
| 長さ／初期値の基準 | 長さは業務上限。数字は整数桁.小数桁。初期値はDB既定値。画面の初期値とは別。 |
| 項目IDの対応 | 物理列に対応する既存DB項目IDを維持。メタ情報fieldIdsに対応を記録。 |
| 基礎仕様 | [論理テーブル仕様](../../../基本設計書/03_テーブル仕様書.md)／[項目制約](../../../共通/09_項目制約定義.md) |

## 項目詳細

| No | 論理名 | 物理名 | PK | タイプ | 長さ | 初期値 | 説明 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | コード分類 | category_id | 〇 | 文字 | 24 | 指定なし | 必須。DB:varchar(24)／NULL不可。分類の識別情報。登録後変更不可。 |
| 2 | コード分類名 | category_name | － | 文字 | 12 | 指定なし | 必須。DB:nvarchar(24)／NULL不可。性別・在籍区分等。 |
| 3 | コード値の桁数 | code_length | － | 数字 | 2.0 | 指定なし | 必須。DB:smallint／NULL不可。分類内の値を固定桁で管理。 |
| 4 | 値の追加可否 | allow_add | － | 真偽 | － | 指定なし | 必須。DB:bit／NULL不可。通常保守で新しい値を増やせるか。 |
| 5 | 分類の利用可否 | is_active | － | 真偽 | － | 1 | 必須・利用可。DB:bit／NULL不可。本版の5分類は利用可を維持。 |
| 6 | 備考 | remarks | － | 文字 | 120 | 指定なし | 任意。DB:nvarchar(240)／NULL可。分類の用途・保守上の注意。 |
| 7 | 作成日時 | created_at | － | 日時 | － | 指定なし | 自動。DB:datetimeoffset(7)／NULL不可。最初の保存日時。変更不可。 |
| 8 | 作成者 | created_by | － | 文字 | 64 | 指定なし | 自動。DB:nvarchar(128)／NULL不可。認証された登録者。変更不可。 |
| 9 | 更新日時 | updated_at | － | 日時 | － | 指定なし | 自動。DB:datetimeoffset(7)／NULL不可。実変更の保存時点。 |
| 10 | 更新者 | updated_by | － | 文字 | 64 | 指定なし | 自動。DB:nvarchar(128)／NULL不可。認証された変更者。 |
| 11 | 更新管理番号 | row_version | － | 数字 | 19.0 | 1 | 自動。DB:bigint／NULL不可。新規1、実変更ごとに1加算、上限で停止。9223372036854775807到達後の加算を拒否。手動加算bigint。SQL Serverのrowversion型ではない。 |
