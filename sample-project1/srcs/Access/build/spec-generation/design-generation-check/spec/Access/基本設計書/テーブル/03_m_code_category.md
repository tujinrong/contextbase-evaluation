<!-- spec-meta: {"schema":"spec-md/1.1","documentId":"ACCESS-BAS-STU-03-M_CODE_CATEGORY","version":"0.1","path":"sample-project1/srcs/Access/build/spec-generation/design-generation-check/spec/Access/基本設計書/テーブル/03_m_code_category.md","layout":"TABLE","table":{"logicalName":"コード種別マスタ","physicalName":"m_code_category","profile":"論理","primaryKey":["category_id"],"fieldIds":{"category_id":"TBL-03-001","category_name":"TBL-03-002","code_length":"TBL-03-003","allow_add":"TBL-03-004","is_active":"TBL-03-005","remarks":"TBL-03-006","created_at":"TBL-03-007","created_by":"TBL-03-008","updated_at":"TBL-03-009","updated_by":"TBL-03-010","row_version":"TBL-03-011"}},"sheets":[{"sheet":"m_code_category","kind":"TABLE","sections":[{"heading":"テーブルヘッダー","kind":"HEADER"},{"heading":"項目詳細","kind":"LIST","key":["No"],"columns":["No","論理名","物理名","PK","NOT NULL","タイプ","長さ","初期値","説明"]}]}],"isolationProfile":"Access","generationStatus":"verification-draft","inputSpecRoot":"sample-project1/spec/Access/"} -->
# コード種別マスタ テーブル仕様書

## テーブルヘッダー

| 項目 | 内容 |
| --- | --- |
| 文書ID／版 | BAS-STU-03-M_CODE_CATEGORY／0.1／2026-10-28 |
| 生成状態 | verification-draft。基本設計Agentの試験生成・未採用 |
| 入力文書版 | ACCESS-BAS-STU-03-M_CODE_CATEGORY／8.1。11項目を継承 |
| 論理テーブル名 | コード種別マスタ |
| 物理テーブル名 | m_code_category |
| 対象／スキーマ | 論理／言語・DB製品非依存 |
| 用途／項目数 | コード分類1件の識別、固定桁、通常保守条件を管理。11項目 |
| 主キー（順序） | category_id |
| 共通規則・制約 | [総合仕様・制約](../03_テーブル仕様書.md)／[記述規約](../../規約/全体/テーブル仕様書記述規約.md) |
| 長さ／初期値の基準 | 長さは業務上限。数字は整数桁.小数桁。初期値は業務設定 |
| 項目IDの対応 | TBL-03-{Noを3桁}。既存fieldIdsと項目順を維持 |
| 物理名の位置付け | 対応確認用。実DB型・容量・制約は[Access分冊](../../DB定義/Access/テーブル/03_m_code_category.md)を保持 |
| 記号 | PK・NOT NULLは〇／空欄。初期値なし・長さ対象外は空欄。条件付き必須は説明参照 |

## 項目詳細

| No | 論理名 | 物理名 | PK | NOT NULL | タイプ | 長さ | 初期値 | 説明 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | コード分類 | category_id | 〇 | 〇 | 文字 | 24 |  | 分類の識別キーであり、登録後に変更しない。 |
| 2 | コード分類名 | category_name |  | 〇 | 文字 | 12 |  | 性別・在籍区分等、分類の表示名称を保持する。 |
| 3 | コード値の桁数 | code_length |  | 〇 | 数字 | 2.0 |  | 分類内のコード値に適用する固定桁数。 |
| 4 | 値の追加可否 | allow_add |  | 〇 | 真偽 |  |  | 通常保守で同じ分類へ値を追加できるかを示す。 |
| 5 | 分類の利用可否 | is_active |  | 〇 | 真偽 |  | 利用可 | 既存5分類では利用可を維持する。 |
| 6 | 備考 | remarks |  |  | 文字 | 120 |  | 分類の用途と保守上の注意を記録する。 |
| 7 | 作成日時 | created_at |  | 〇 | 日時 |  |  | 最初の保存時点を自動設定し、後から変更しない。 |
| 8 | 作成者 | created_by |  | 〇 | 文字 | 64 |  | 認証済み登録者を自動設定し、登録後は変更しない。 |
| 9 | 更新日時 | updated_at |  | 〇 | 日時 |  |  | 実変更を保存した時点を自動設定する。 |
| 10 | 更新者 | updated_by |  | 〇 | 文字 | 64 |  | 実変更を行った認証済み利用者を設定する。 |
| 11 | 更新管理番号 | row_version |  | 〇 | 数字 |  | 1 | 新規1、実変更ごとに1加算し、上限では停止する。桁上限は採用DB定義に従う。 |
