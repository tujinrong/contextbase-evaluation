<!-- spec-meta: {"schema":"spec-md/1.1","documentId":"VUE_CSHARPAPI-BAS-STU-03-M_CODE_CATEGORY","version":"8.1","path":"sample-project1/spec/Vue_CSharpAPI/基本設計書/テーブル/03_m_code_category.md","layout":"TABLE","table":{"logicalName":"コード種別マスタ","physicalName":"m_code_category","profile":"論理","primaryKey":["category_id"],"fieldIds":{"category_id":"TBL-03-001","category_name":"TBL-03-002","code_length":"TBL-03-003","allow_add":"TBL-03-004","is_active":"TBL-03-005","remarks":"TBL-03-006","created_at":"TBL-03-007","created_by":"TBL-03-008","updated_at":"TBL-03-009","updated_by":"TBL-03-010","row_version":"TBL-03-011"}},"sheets":[{"sheet":"m_code_category","kind":"TABLE","sections":[{"heading":"テーブルヘッダー","kind":"HEADER"},{"heading":"項目詳細","kind":"LIST","key":["No"],"columns":["No","論理名","物理名","PK","NOT NULL","タイプ","長さ","初期値","説明"]}]}],"isolationProfile":"Vue_CSharpAPI"} -->
# コード種別マスタ テーブル仕様書

## テーブルヘッダー

| 項目 | 内容 |
| --- | --- |
| 文書ID／版 | BAS-STU-03-M_CODE_CATEGORY／8.1／2026-10-25 |
| 論理テーブル名 | コード種別マスタ |
| 物理テーブル名 | m_code_category |
| 対象／スキーマ | 論理／言語・DB製品非依存 |
| 用途／項目数 | コード分類１件の桁数・保守条件を管理。 11項目。 |
| 主キー（順序） | category_id |
| 共通規則・制約 | [総合仕様・制約](../03_テーブル仕様書.md)／[記述・Excel配置規約](../../規約/全体/テーブル仕様書記述規約.md) |
| 長さ／初期値の基準 | 長さは業務上限。数字は整数桁.小数桁。初期値は業務設定。 |
| 項目IDの対応 | TBL-03-{Noを3桁}。メタ情報fieldIdsに対応を記録。 |
| 物理名の位置付け | 対応付けの参照名。実装言語・DB製品の指定ではない。 |
| 記号 | PK・NOT NULL：〇が該当、空欄は非該当。初期値なし・長さ対象外は空欄。条件付き必須は説明参照。 |

## 項目詳細

| No | 論理名 | 物理名 | PK | NOT NULL | タイプ | 長さ | 初期値 | 説明 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | コード分類 | category_id | 〇 | 〇 | 文字 | 24 |  | 分類の識別情報。登録後変更不可。 |
| 2 | コード分類名 | category_name |  | 〇 | 文字 | 12 |  | 性別・在籍区分等。 |
| 3 | コード値の桁数 | code_length |  | 〇 | 数字 | 2.0 |  | 分類内の値を固定桁で管理。 |
| 4 | 値の追加可否 | allow_add |  | 〇 | 真偽 |  |  | 通常保守で新しい値を増やせるか。 |
| 5 | 分類の利用可否 | is_active |  | 〇 | 真偽 |  | 利用可 | 本版の5分類は利用可を維持。 |
| 6 | 備考 | remarks |  |  | 文字 | 120 |  | 分類の用途・保守上の注意。 |
| 7 | 作成日時 | created_at |  | 〇 | 日時 |  |  | 自動。最初の保存日時。変更不可。 |
| 8 | 作成者 | created_by |  | 〇 | 文字 | 64 |  | 自動。認証された登録者。変更不可。 |
| 9 | 更新日時 | updated_at |  | 〇 | 日時 |  |  | 自動。実変更の保存時点。 |
| 10 | 更新者 | updated_by |  | 〇 | 文字 | 64 |  | 自動。認証された変更者。 |
| 11 | 更新管理番号 | row_version |  | 〇 | 数字 |  | 1 | 自動。新規1、実変更ごとに1加算、上限で停止。桁上限は採用DB定義を参照。 |
