<!-- spec-meta: {"schema":"spec-md/1.1","documentId":"VB.NET_WINFORMS-BAS-STU-03-M_CODE","version":"8.1","path":"sample-project1/spec/VB.NET_WinForms/基本設計書/テーブル/04_m_code.md","layout":"TABLE","table":{"logicalName":"コード管理マスタ","physicalName":"m_code","profile":"論理","primaryKey":["category_id","code_value"],"fieldIds":{"category_id":"TBL-04-001","code_value":"TBL-04-002","code_name":"TBL-04-003","display_order":"TBL-04-004","is_active":"TBL-04-005","valid_from":"TBL-04-006","valid_to":"TBL-04-007","is_protected":"TBL-04-008","remarks":"TBL-04-009","created_at":"TBL-04-010","created_by":"TBL-04-011","updated_at":"TBL-04-012","updated_by":"TBL-04-013","row_version":"TBL-04-014"}},"sheets":[{"sheet":"m_code","kind":"TABLE","sections":[{"heading":"テーブルヘッダー","kind":"HEADER"},{"heading":"項目詳細","kind":"LIST","key":["No"],"columns":["No","論理名","物理名","PK","NOT NULL","タイプ","長さ","初期値","説明"]}]}],"isolationProfile":"VB.NET_WinForms"} -->
# コード管理マスタ テーブル仕様書

## テーブルヘッダー

| 項目 | 内容 |
| --- | --- |
| 文書ID／版 | BAS-STU-03-M_CODE／8.1／2026-10-25 |
| 論理テーブル名 | コード管理マスタ |
| 物理テーブル名 | m_code |
| 対象／スキーマ | 論理／言語・DB製品非依存 |
| 用途／項目数 | 分類内のコード値１件を管理。 14項目。 |
| 主キー（順序） | category_id → code_value |
| 共通規則・制約 | [総合仕様・制約](../03_テーブル仕様書.md)／[記述・Excel配置規約](../../規約/全体/テーブル仕様書記述規約.md) |
| 長さ／初期値の基準 | 長さは業務上限。数字は整数桁.小数桁。初期値は業務設定。 |
| 項目IDの対応 | TBL-04-{Noを3桁}。メタ情報fieldIdsに対応を記録。 |
| 物理名の位置付け | 対応付けの参照名。実装言語・DB製品の指定ではない。 |
| 記号 | PK・NOT NULL：〇が該当、空欄は非該当。初期値なし・長さ対象外は空欄。条件付き必須は説明参照。 |

## 項目詳細

| No | 論理名 | 物理名 | PK | NOT NULL | タイプ | 長さ | 初期値 | 説明 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | コード分類 | category_id | 〇 | 〇 | 文字 | 24 |  | コード種別マスタに存在する分類。 |
| 2 | コード値 | code_value | 〇 | 〇 | 文字 | 10 |  | 分類で決めた固定桁。先頭ゼロを保持。 |
| 3 | コード名称 | code_name |  | 〇 | 文字 | 12 |  | 画面に表示する名称。 |
| 4 | 表示順 | display_order |  | 〇 | 数字 |  | 0 | 同順位はコード値順。桁上限は採用DB定義を参照。 |
| 5 | 利用可否 | is_active |  | 〇 | 真偽 |  | 利用可 | 利用不可は新規選択不可。 |
| 6 | 有効開始日 | valid_from |  | 〇 | 日付 |  | 1900-01-01 | 両端を含む。 |
| 7 | 有効終了日 | valid_to |  |  | 日付 |  |  | 空は期限なし。開始日以上。 |
| 8 | 保護対象 | is_protected |  | 〇 | 真偽 |  |  | 保護値の停止・期間短縮等を禁止。 |
| 9 | 備考 | remarks |  |  | 文字 | 120 |  | 意味や使用上の注意。 |
| 10 | 作成日時 | created_at |  | 〇 | 日時 |  |  | 自動。最初の保存日時。変更不可。 |
| 11 | 作成者 | created_by |  | 〇 | 文字 | 64 |  | 自動。認証された登録者。変更不可。 |
| 12 | 更新日時 | updated_at |  | 〇 | 日時 |  |  | 自動。実変更の保存時点。 |
| 13 | 更新者 | updated_by |  | 〇 | 文字 | 64 |  | 自動。認証された変更者。 |
| 14 | 更新管理番号 | row_version |  | 〇 | 数字 |  | 1 | 自動。新規1、実変更ごとに1加算、上限で停止。桁上限は採用DB定義を参照。 |
