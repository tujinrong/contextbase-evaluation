<!-- spec-meta: {"schema":"spec-md/1.1","documentId":"ACCESS-BAS-STU-03-M_CODE","version":"0.1","path":"sample-project1/srcs/Access/build/spec-generation/design-generation-check/spec/Access/基本設計書/テーブル/04_m_code.md","layout":"TABLE","table":{"logicalName":"コード管理マスタ","physicalName":"m_code","profile":"論理","primaryKey":["category_id","code_value"],"fieldIds":{"category_id":"TBL-04-001","code_value":"TBL-04-002","code_name":"TBL-04-003","display_order":"TBL-04-004","is_active":"TBL-04-005","valid_from":"TBL-04-006","valid_to":"TBL-04-007","is_protected":"TBL-04-008","remarks":"TBL-04-009","created_at":"TBL-04-010","created_by":"TBL-04-011","updated_at":"TBL-04-012","updated_by":"TBL-04-013","row_version":"TBL-04-014"}},"sheets":[{"sheet":"m_code","kind":"TABLE","sections":[{"heading":"テーブルヘッダー","kind":"HEADER"},{"heading":"項目詳細","kind":"LIST","key":["No"],"columns":["No","論理名","物理名","PK","NOT NULL","タイプ","長さ","初期値","説明"]}]}],"isolationProfile":"Access","generationStatus":"verification-draft","inputSpecRoot":"sample-project1/spec/Access/"} -->
# コード管理マスタ テーブル仕様書

## テーブルヘッダー

| 項目 | 内容 |
| --- | --- |
| 文書ID／版 | BAS-STU-03-M_CODE／0.1／2026-10-28 |
| 生成状態 | verification-draft。基本設計Agentの試験生成・未採用 |
| 入力文書版 | ACCESS-BAS-STU-03-M_CODE／8.1。14項目を継承 |
| 論理テーブル名 | コード管理マスタ |
| 物理テーブル名 | m_code |
| 対象／スキーマ | 論理／言語・DB製品非依存 |
| 用途／項目数 | 分類内のコード値1件と名称・利用条件を管理。14項目 |
| 主キー（順序） | category_id → code_value |
| 共通規則・制約 | [総合仕様・制約](../03_テーブル仕様書.md)／[記述規約](../../規約/全体/テーブル仕様書記述規約.md) |
| 長さ／初期値の基準 | 長さは業務上限。数字は整数桁.小数桁。初期値は業務設定 |
| 項目IDの対応 | TBL-04-{Noを3桁}。既存fieldIdsと項目順を維持 |
| 物理名の位置付け | 対応確認用。実DB型・容量・制約は[Access分冊](../../DB定義/Access/テーブル/04_m_code.md)を保持 |
| 記号 | PK・NOT NULLは〇／空欄。初期値なし・長さ対象外は空欄。条件付き必須は説明参照 |

## 項目詳細

| No | 論理名 | 物理名 | PK | NOT NULL | タイプ | 長さ | 初期値 | 説明 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | コード分類 | category_id | 〇 | 〇 | 文字 | 24 |  | コード種別マスタに登録されている分類を参照する。 |
| 2 | コード値 | code_value | 〇 | 〇 | 文字 | 10 |  | 分類が定めた固定桁で保持し、先頭ゼロを失わない。 |
| 3 | コード名称 | code_name |  | 〇 | 文字 | 12 |  | 画面で提示する名称を保持する。 |
| 4 | 表示順 | display_order |  | 〇 | 数字 |  | 0 | 同じ表示順ならコード値順に並べる。桁上限は採用DB定義に従う。 |
| 5 | 利用可否 | is_active |  | 〇 | 真偽 |  | 利用可 | 利用不可のコードを新規選択させない。 |
| 6 | 有効開始日 | valid_from |  | 〇 | 日付 |  | 1900-01-01 | 有効期間に開始日を含める。 |
| 7 | 有効終了日 | valid_to |  |  | 日付 |  |  | 空は期限なし。指定時は開始日以上とし、終了日を期間に含める。 |
| 8 | 保護対象 | is_protected |  | 〇 | 真偽 |  |  | 保護値の停止や有効期間短縮等を拒否する。 |
| 9 | 備考 | remarks |  |  | 文字 | 120 |  | コードの意味と利用上の注意を保持する。 |
| 10 | 作成日時 | created_at |  | 〇 | 日時 |  |  | 最初の保存時点を自動設定し、後から変更しない。 |
| 11 | 作成者 | created_by |  | 〇 | 文字 | 64 |  | 認証済み登録者を自動設定し、登録後は変更しない。 |
| 12 | 更新日時 | updated_at |  | 〇 | 日時 |  |  | 実変更を保存した時点を自動設定する。 |
| 13 | 更新者 | updated_by |  | 〇 | 文字 | 64 |  | 実変更を行った認証済み利用者を設定する。 |
| 14 | 更新管理番号 | row_version |  | 〇 | 数字 |  | 1 | 新規1、実変更ごとに1加算し、上限では停止する。桁上限は採用DB定義に従う。 |
