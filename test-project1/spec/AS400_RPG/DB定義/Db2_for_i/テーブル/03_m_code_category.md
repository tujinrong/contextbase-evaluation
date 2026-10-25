<!-- spec-meta: {"schema":"spec-md/1.1","documentId":"AS400_RPG-DBDEF-DB2_FOR_I-M_CODE_CATEGORY","version":"8.1","path":"test-project1/spec/AS400_RPG/DB定義/Db2_for_i/テーブル/03_m_code_category.md","layout":"TABLE","table":{"logicalName":"コード種別マスタ","physicalName":"m_code_category","profile":"Db2_for_i","primaryKey":["category_id"],"fieldIds":{"category_id":"DB-M_CODE_CATEGORY-CATEGORY_ID","category_name":"DB-M_CODE_CATEGORY-CATEGORY_NAME","code_length":"DB-M_CODE_CATEGORY-CODE_LENGTH","allow_add":"DB-M_CODE_CATEGORY-ALLOW_ADD","is_active":"DB-M_CODE_CATEGORY-IS_ACTIVE","remarks":"DB-M_CODE_CATEGORY-REMARKS","created_at":"DB-M_CODE_CATEGORY-CREATED_AT","created_by":"DB-M_CODE_CATEGORY-CREATED_BY","updated_at":"DB-M_CODE_CATEGORY-UPDATED_AT","updated_by":"DB-M_CODE_CATEGORY-UPDATED_BY","row_version":"DB-M_CODE_CATEGORY-ROW_VERSION"}},"sheets":[{"sheet":"m_code_category","kind":"TABLE","sections":[{"heading":"テーブルヘッダー","kind":"HEADER"},{"heading":"項目詳細","kind":"LIST","key":["No"],"columns":["No","論理名","物理名","PK","NOT NULL","タイプ","長さ","初期値","説明"]}]}],"isolationProfile":"AS400_RPG"} -->
# コード種別マスタ DB定義書

## テーブルヘッダー

| 項目 | 内容 |
| --- | --- |
| 文書ID／版 | DBDEF-DB2_FOR_I-M_CODE_CATEGORY／8.1／2026-10-25 |
| 論理テーブル名 | コード種別マスタ |
| 物理テーブル名 | m_code_category |
| 対象／スキーマ | Db2_for_i／STUDAPP |
| 用途／項目数 | コード分類１件の桁数・保守条件を管理。 11項目。 |
| 主キー（順序） | category_id |
| 共通規則・制約 | [総合仕様・制約](../01_DB定義書.md)／[記述・Excel配置規約](../../../規約/全体/テーブル仕様書記述規約.md) |
| 長さ／初期値の基準 | 長さは業務上限、タイプはDB型・容量。初期値はDB既定値。 |
| 項目IDの対応 | 物理列に対応する既存DB項目IDを維持。メタ情報fieldIdsに対応を記録。 |
| 基礎仕様 | [論理テーブル仕様](../../../基本設計書/03_テーブル仕様書.md)／[項目制約](../../../共通/09_項目制約定義.md) |
| 記号 | PK・NOT NULL：〇が該当、空欄は非該当。初期値なし・長さ対象外は空欄。条件付き必須は説明参照。 |

## 項目詳細

| No | 論理名 | 物理名 | PK | NOT NULL | タイプ | 長さ | 初期値 | 説明 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | コード分類 | category_id | 〇 | 〇 | VARCHAR(24) CCSID 1208 | 24 |  | 分類の識別情報。登録後変更不可。 |
| 2 | コード分類名 | category_name |  | 〇 | VARGRAPHIC(24) CCSID 1200 | 12 |  | 性別・在籍区分等。 |
| 3 | コード値の桁数 | code_length |  | 〇 | SMALLINT | 2.0 |  | 分類内の値を固定桁で管理。 |
| 4 | 値の追加可否 | allow_add |  | 〇 | SMALLINT |  |  | 通常保守で新しい値を増やせるか。 |
| 5 | 分類の利用可否 | is_active |  | 〇 | SMALLINT |  | 1 | 必須・利用可。本版の5分類は利用可を維持。 |
| 6 | 備考 | remarks |  |  | VARGRAPHIC(240) CCSID 1200 | 120 |  | 分類の用途・保守上の注意。 |
| 7 | 作成日時 | created_at |  | 〇 | TIMESTAMP(6) |  |  | 自動。最初の保存日時。変更不可。 |
| 8 | 作成者 | created_by |  | 〇 | VARGRAPHIC(128) CCSID 1200 | 64 |  | 自動。認証された登録者。変更不可。 |
| 9 | 更新日時 | updated_at |  | 〇 | TIMESTAMP(6) |  |  | 自動。実変更の保存時点。 |
| 10 | 更新者 | updated_by |  | 〇 | VARGRAPHIC(128) CCSID 1200 | 64 |  | 自動。認証された変更者。 |
| 11 | 更新管理番号 | row_version |  | 〇 | BIGINT | 19.0 | 1 | 自動。新規1、実変更ごとに1加算、上限で停止。9223372036854775807到達後の加算を拒否。 |
