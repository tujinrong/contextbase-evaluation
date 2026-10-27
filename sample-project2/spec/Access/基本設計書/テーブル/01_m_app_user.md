<!-- spec-meta: {"schema":"spec-md/1.1","documentId":"SP2-Access-T01","version":"1.0","path":"sample-project2/spec/Access/基本設計書/テーブル/01_m_app_user.md","layout":"TABLE","table":{"logicalName":"利用者","physicalName":"m_app_user","profile":"論理","primaryKey":["user_id"],"fieldIds":{"user_id":"T01-001","login_id":"T01-002","display_name":"T01-003","password_verifier":"T01-004","role_id":"T01-005","is_enabled":"T01-006","failed_count":"T01-007","locked_until":"T01-008"}},"sheets":[{"sheet":"m_app_user","kind":"TABLE","sections":[{"heading":"テーブルヘッダー","kind":"HEADER"},{"heading":"項目詳細","kind":"LIST","key":["No"],"columns":["No","論理名","物理名","PK","NOT NULL","タイプ","長さ","初期値","説明"]}]}]} -->
# 利用者 テーブル仕様書

## テーブルヘッダー

| 項目 | 内容 |
| --- | --- |
| 文書ID／版 | SP2-Access-T01／1.0／2026-10-27 |
| 論理／物理名 | 利用者／m_app_user |
| 対象 | 論理／言語・DB製品非依存 |
| 用途／項目数 | ログインと役割・失敗制御／8項目 |
| 主キー（順序） | user_id |
| 共通規則 | [共通制約](../07_テーブル仕様書.md)、[認証条件](../../プロジェクト情報.md) |
| 長さ・空欄 | 業務上限。PK/NOT NULLの〇以外、初期値なし・長さ非該当は空欄 |
| 項目ID | T01-{No3桁}、fieldIdsと対応 |

## 項目詳細

| No | 論理名 | 物理名 | PK | NOT NULL | タイプ | 長さ | 初期値 | 説明 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | 利用者ID | user_id | 〇 | 〇 | 文字 | 20 |  | 初期設定時に固定する不変ID。監査の主体。 |
| 2 | ログインID | login_id |  | 〇 | 文字 | 20 |  | 半角英数字、英字大小を無視して一意。初期設定後はこのDEMOで変更しない。 |
| 3 | 表示名 | display_name |  | 〇 | 文字 | 40 |  | メニュー等に表示。本人氏名であることは要求しない。 |
| 4 | パスワード検証情報 | password_verifier |  | 〇 | 文字 | 1024 |  | ソルト・方式/パラメーターを含む一方向検証情報。平文/復号可能なパスワードを保存しない。形式と方式は詳細工程で固定する。 |
| 5 | 利用者役割 | role_id |  | 〇 | 文字 | 5 |  | ADMINまたはSTAFF。汎用コード参照ではない。 |
| 6 | 利用可能 | is_enabled |  | 〇 | 真偽 |  | 有効 | 停止時はログインと次の更新/出力を拒否する。 |
| 7 | 連続失敗回数 | failed_count |  | 〇 | 数字 | 1.0 | 0 | 0～5。成功/ロック期間終了後にリセットし、新たな失敗を数える。 |
| 8 | ロック解除日時 | locked_until |  |  | 日時 |  |  | 5回連続失敗した時点+15分。UTC。未ロックはNULL。 |
