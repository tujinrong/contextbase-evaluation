<!-- spec-meta: {"schema":"spec-md/1.1","documentId":"VUE_CSHARPAPI-DBDEF-SQLSERVER-T_CONFIRMATION","version":"8.1","path":"test-project1/spec/Vue_CSharpAPI/DB定義/SQLServer/テーブル/06_t_confirmation.md","layout":"TABLE","table":{"logicalName":"重複確認情報","physicalName":"t_confirmation","profile":"SQLServer","primaryKey":["token"],"fieldIds":{"token":"AUX-CONF-1","principal":"AUX-CONF-2","session_id":"AUX-CONF-3","target_id":"AUX-CONF-4","expected_version":"AUX-CONF-5","payload_hash":"AUX-CONF-6","candidate_hash":"AUX-CONF-7","expires_at":"AUX-CONF-8","consumed":"AUX-CONF-9"}},"sheets":[{"sheet":"t_confirmation","kind":"TABLE","sections":[{"heading":"テーブルヘッダー","kind":"HEADER"},{"heading":"項目詳細","kind":"LIST","key":["No"],"columns":["No","論理名","物理名","PK","NOT NULL","タイプ","長さ","初期値","説明"]}]}],"isolationProfile":"Vue_CSharpAPI"} -->
# 重複確認情報 DB定義書

## テーブルヘッダー

| 項目 | 内容 |
| --- | --- |
| 文書ID／版 | DBDEF-SQLSERVER-T_CONFIRMATION／8.1／2026-10-25 |
| 論理テーブル名 | 重複確認情報 |
| 物理テーブル名 | t_confirmation |
| 対象／スキーマ | SQLServer／dbo |
| 用途／項目数 | 重複候補の確認と保存要求を関連付ける技術情報。 9項目。補助表の論理名は既存物理名・説明に基づく表記補足。 |
| 主キー（順序） | token |
| 共通規則・制約 | [総合仕様・制約](../01_DB定義書.md)／[記述・Excel配置規約](../../../規約/全体/テーブル仕様書記述規約.md) |
| 長さ／初期値の基準 | 長さは業務上限、タイプはDB型・容量。初期値は処理設定。DB DEFAULTは未定義。 |
| 項目IDの対応 | 物理列に対応する既存DB項目IDを維持。メタ情報fieldIdsに対応を記録。 |
| 基礎仕様 | [論理テーブル仕様](../../../基本設計書/03_テーブル仕様書.md)／[項目制約](../../../共通/09_項目制約定義.md) |
| 記号 | PK・NOT NULL：〇が該当、空欄は非該当。初期値なし・長さ対象外は空欄。条件付き必須は説明参照。 |

## 項目詳細

| No | 論理名 | 物理名 | PK | NOT NULL | タイプ | 長さ | 初期値 | 説明 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | 確認トークン | token | 〇 | 〇 | uniqueidentifier |  |  | 予測困難な発行値。 |
| 2 | 認証主体 | principal |  | 〇 | nvarchar(128) | 64 |  | 発行時の認証主体。 |
| 3 | 認証セッション | session_id |  | 〇 | uniqueidentifier |  |  | 認証セッション。 |
| 4 | 対象学生管理番号 | target_id |  |  | bigint | 19.0 |  | 新規NULL、更新は学生ID。 |
| 5 | 読込時更新管理番号 | expected_version |  |  | bigint | 19.0 |  | 新規NULL、更新は正の版。 |
| 6 | 入力内容ハッシュ | payload_hash |  | 〇 | binary(32) | 32 |  | 正規化した19業務入力のハッシュ。 |
| 7 | 重複候補ハッシュ | candidate_hash |  | 〇 | binary(32) | 32 |  | 全候補ID/版の正規化集合ハッシュ。 |
| 8 | 有効期限 | expires_at |  | 〇 | datetimeoffset(7) |  |  | 発行時点＋10分。 |
| 9 | 消費済み状態 | consumed |  | 〇 | bit |  | 処理:0 | 初期0、確定保存と同時消費。 |
