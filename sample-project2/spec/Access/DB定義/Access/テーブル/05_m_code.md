<!-- spec-meta: {"schema":"spec-md/1.1","documentId":"SP2-Access-DB-T05","version":"1.0","path":"sample-project2/spec/Access/DB定義/Access/テーブル/05_m_code.md","layout":"TABLE","table":{"logicalName":"汎用コード","physicalName":"m_code","profile":"ACE","primaryKey":["category_id","code"],"fieldIds":{"category_id":"T05-001","code":"T05-002","code_name":"T05-003","sort_order":"T05-004","is_enabled":"T05-005","updated_at":"T05-006","updated_by":"T05-007","revision":"T05-008"}},"sheets":[{"sheet":"m_code","kind":"TABLE","sections":[{"heading":"テーブルヘッダー","kind":"HEADER"},{"heading":"項目詳細","kind":"LIST","key":["No"],"columns":["No","論理名","物理名","PK","NOT NULL","タイプ","長さ","初期値","説明"]}]}]} -->
# 汎用コード テーブル仕様書

## テーブルヘッダー

| 項目 | 内容 |
| --- | --- |
| 文書ID／版 | SP2-Access-DB-T05／1.0／2026-10-28 |
| 論理／物理名 | 汎用コード／m_code |
| 対象 | ACE／単一ACCDB内包。物理設計・実DB適用未実施 |
| 用途／項目数 | 選択候補と表示名称／8項目 |
| 主キー（順序） | category_id、code |
| 共通規則 | [ACE物理共通制約](../01_DB定義書.md)、[基本定義](../../../基本設計書/テーブル/05_m_code.md) |
| 件数・変更 | 初期9行。在籍3値は固定、他分類は01～99の範囲で追加可 |
| 長さ・空欄 | 業務上限。PK/NOT NULLの〇以外、初期値なし・長さ非該当は空欄 |
| 項目ID | T05-{No3桁}、fieldIdsと対応 |

## 項目詳細

| No | 論理名 | 物理名 | PK | NOT NULL | タイプ | 長さ | 初期値 | 説明 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | 分類ID | category_id | 〇 | 〇 | TEXT(24) | 24 |  | コード分類を参照。不変。 |
| 2 | コード | code | 〇 | 〇 | TEXT(2) | 2 |  | 半角数字01～99。分類内一意、不変。 |
| 3 | 名称 | code_name |  | 〇 | TEXT(80) | 40 |  | 現在名称を画面/帳票へ表示。 |
| 4 | 並び順 | sort_order |  | 〇 | SHORT | 3.0 | 1 | 1～999。同順可、コード昇順で補完。 |
| 5 | 有効 | is_enabled |  | 〇 | YESNO |  | 有効 | 停止しても既存参照は保持。在籍3値は停止不可。 |
| 6 | 更新日時 | updated_at |  | 〇 | DATETIME |  |  | 新規/実変更の確定時UTC。 |
| 7 | 更新者 | updated_by |  | 〇 | TEXT(40) | 20 |  | 認証済みADMINの利用者ID。初期投入時は投入主体。 |
| 8 | 更新版 | revision |  | 〇 | LONG | 10.0 | 1 | 1～2147483647。競合検出用。 |
