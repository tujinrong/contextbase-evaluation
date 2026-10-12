<!-- spec-meta: {"schema":"spec-md/1.1","documentId":"DBDEF-SQLSERVER-M_CODE","version":"7.2","path":"test-project1/spec/DB定義/SQLServer/テーブル/04_m_code.md","layout":"TABLE","table":{"logicalName":"コード管理マスタ","physicalName":"m_code","profile":"SQLServer","primaryKey":["category_id","code_value"],"fieldIds":{"category_id":"DB-M_CODE-CATEGORY_ID","code_value":"DB-M_CODE-CODE_VALUE","code_name":"DB-M_CODE-CODE_NAME","display_order":"DB-M_CODE-DISPLAY_ORDER","is_active":"DB-M_CODE-IS_ACTIVE","valid_from":"DB-M_CODE-VALID_FROM","valid_to":"DB-M_CODE-VALID_TO","is_protected":"DB-M_CODE-IS_PROTECTED","remarks":"DB-M_CODE-REMARKS","created_at":"DB-M_CODE-CREATED_AT","created_by":"DB-M_CODE-CREATED_BY","updated_at":"DB-M_CODE-UPDATED_AT","updated_by":"DB-M_CODE-UPDATED_BY","row_version":"DB-M_CODE-ROW_VERSION"}},"sheets":[{"sheet":"m_code","kind":"TABLE","sections":[{"heading":"テーブルヘッダー","kind":"HEADER"},{"heading":"項目詳細","kind":"LIST","key":["No"],"columns":["No","論理名","物理名","PK","NOT NULL","タイプ","長さ","初期値","説明"]}]}]} -->
# コード管理マスタ DB定義書

## テーブルヘッダー

| 項目 | 内容 |
| --- | --- |
| 文書ID／版 | DBDEF-SQLSERVER-M_CODE／7.2／2026-10-12 |
| 論理テーブル名 | コード管理マスタ |
| 物理テーブル名 | m_code |
| 対象／スキーマ | SQLServer／dbo |
| 用途／項目数 | 分類内のコード値１件を管理。 14項目。 |
| 主キー（順序） | category_id → code_value |
| 共通規則・制約 | [総合仕様・制約](../01_DB定義書.md)／[記述・Excel配置規約](../../../../../docs/テーブル仕様書記述規約.md) |
| 長さ／初期値の基準 | 長さは業務上限、タイプはDB型・容量。初期値はDB既定値。 |
| 項目IDの対応 | 物理列に対応する既存DB項目IDを維持。メタ情報fieldIdsに対応を記録。 |
| 基礎仕様 | [論理テーブル仕様](../../../基本設計書/03_テーブル仕様書.md)／[項目制約](../../../共通/09_項目制約定義.md) |
| 記号 | PK・NOT NULL：〇が該当、空欄は非該当。初期値なし・長さ対象外は空欄。条件付き必須は説明参照。 |

## 項目詳細

| No | 論理名 | 物理名 | PK | NOT NULL | タイプ | 長さ | 初期値 | 説明 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | コード分類 | category_id | 〇 | 〇 | varchar(24) | 24 |  | コード種別マスタに存在する分類。FK:m_code_category.category_id。 |
| 2 | コード値 | code_value | 〇 | 〇 | varchar(10) | 10 |  | 分類で決めた固定桁。先頭ゼロを保持。 |
| 3 | コード名称 | code_name |  | 〇 | nvarchar(24) | 12 |  | 画面に表示する名称。 |
| 4 | 表示順 | display_order |  | 〇 | int | 10.0 | 0 | 必須・0。同順位はコード値順。 |
| 5 | 利用可否 | is_active |  | 〇 | bit |  | 1 | 必須・利用可。利用不可は新規選択不可。 |
| 6 | 有効開始日 | valid_from |  | 〇 | date |  |  | 必須・1900年1月1日。両端を含む。 |
| 7 | 有効終了日 | valid_to |  |  | date |  |  | 空は期限なし。開始日以上。 |
| 8 | 保護対象 | is_protected |  | 〇 | bit |  |  | 保護値の停止・期間短縮等を禁止。 |
| 9 | 備考 | remarks |  |  | nvarchar(240) | 120 |  | 意味や使用上の注意。 |
| 10 | 作成日時 | created_at |  | 〇 | datetimeoffset(7) |  |  | 自動。最初の保存日時。変更不可。 |
| 11 | 作成者 | created_by |  | 〇 | nvarchar(128) | 64 |  | 自動。認証された登録者。変更不可。 |
| 12 | 更新日時 | updated_at |  | 〇 | datetimeoffset(7) |  |  | 自動。実変更の保存時点。 |
| 13 | 更新者 | updated_by |  | 〇 | nvarchar(128) | 64 |  | 自動。認証された変更者。 |
| 14 | 更新管理番号 | row_version |  | 〇 | bigint | 19.0 | 1 | 自動。新規1、実変更ごとに1加算、上限で停止。9223372036854775807到達後の加算を拒否。手動加算bigint。SQL Serverのrowversion型ではない。 |
