<!-- spec-meta: {"schema":"spec-md/1.1","documentId":"CSHARP_WPF-DBDEF-SQLSERVER-T_RUNTIME_STATE","version":"8.1","path":"test-project1/spec/CSharp_WPF/DB定義/SQLServer/テーブル/07_t_runtime_state.md","layout":"TABLE","table":{"logicalName":"実行時状態情報","physicalName":"t_runtime_state","profile":"SQLServer","primaryKey":["state_id"],"fieldIds":{"state_id":"AUX-STATE-1","owner_id":"AUX-STATE-2","login_session_id":"AUX-STATE-3","state_kind":"AUX-STATE-4","encrypted_payload":"AUX-STATE-5","expires_at":"AUX-STATE-6","revision":"AUX-STATE-7","consumed":"AUX-STATE-8"}},"sheets":[{"sheet":"t_runtime_state","kind":"TABLE","sections":[{"heading":"テーブルヘッダー","kind":"HEADER"},{"heading":"項目詳細","kind":"LIST","key":["No"],"columns":["No","論理名","物理名","PK","NOT NULL","タイプ","長さ","初期値","説明"]}]}],"isolationProfile":"CSharp_WPF"} -->
# 実行時状態情報 DB定義書

## テーブルヘッダー

| 項目 | 内容 |
| --- | --- |
| 文書ID／版 | DBDEF-SQLSERVER-T_RUNTIME_STATE／8.1／2026-10-25 |
| 論理テーブル名 | 実行時状態情報 |
| 物理テーブル名 | t_runtime_state |
| 対象／スキーマ | SQLServer／dbo |
| 用途／項目数 | 利用者別の検索・確認・成功通知の技術情報。 8項目。補助表の論理名は既存物理名・説明に基づく表記補足。 |
| 主キー（順序） | state_id |
| 共通規則・制約 | [総合仕様・制約](../01_DB定義書.md)／[記述・Excel配置規約](../../../規約/全体/テーブル仕様書記述規約.md) |
| 長さ／初期値の基準 | 長さは業務上限、タイプはDB型・容量。初期値は処理設定。DB DEFAULTは未定義。 |
| 項目IDの対応 | 物理列に対応する既存DB項目IDを維持。メタ情報fieldIdsに対応を記録。 |
| 基礎仕様 | [論理テーブル仕様](../../../基本設計書/03_テーブル仕様書.md)／[項目制約](../../../共通/09_項目制約定義.md) |
| 記号 | PK・NOT NULL：〇が該当、空欄は非該当。初期値なし・長さ対象外は空欄。条件付き必須は説明参照。 |

## 項目詳細

| No | 論理名 | 物理名 | PK | NOT NULL | タイプ | 長さ | 初期値 | 説明 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | 状態識別子 | state_id | 〇 | 〇 | varchar(64) | 64 |  | 256bit乱数の64桁hex。Base64Urlと混在させない。 |
| 2 | 所有者 | owner_id |  | 〇 | nvarchar(128) | 64 |  | 認証主体64スカラー値。 |
| 3 | ログインセッション識別子 | login_session_id |  | 〇 | varchar(64) | 64 |  | 認証セッションキー、外部契約。 |
| 4 | 状態種別 | state_kind |  | 〇 | varchar(16) | 16 |  | 検索・確認・一回の成功通知。 |
| 5 | 暗号化状態情報 | encrypted_payload |  | 〇 | varbinary(max) |  |  | 認証付き暗号。個人情報の平文永続保存禁止。 |
| 6 | 有効期限 | expires_at |  | 〇 | datetimeoffset(7) |  |  | UTC、検索30分・確認10分。 |
| 7 | 更新管理番号 | revision |  | 〇 | bigint | 19.0 | 処理:1 | 正の更新番号、初期1。 |
| 8 | 消費済み状態 | consumed |  | 〇 | bit |  | 処理:0 | 初期0、一回消費。 |
