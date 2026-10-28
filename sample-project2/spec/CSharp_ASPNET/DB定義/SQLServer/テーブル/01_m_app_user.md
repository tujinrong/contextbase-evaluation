<!-- spec-meta: {"schema":"spec-md/1.1","documentId":"SP2-CSharp_ASPNET-DB-T01","version":"1.0","path":"sample-project2/spec/CSharp_ASPNET/DB定義/SQLServer/テーブル/01_m_app_user.md","layout":"TABLE","table":{"logicalName":"利用者","physicalName":"m_app_user","profile":"SQLServer2022","primaryKey":["user_id"],"fieldIds":{"user_id":"T01-001","login_id":"T01-002","display_name":"T01-003","password_verifier":"T01-004","role_id":"T01-005","is_enabled":"T01-006","failed_count":"T01-007","locked_until":"T01-008"},"schema":"dbo"},"sheets":[{"sheet":"m_app_user","kind":"TABLE","sections":[{"heading":"テーブルヘッダー","kind":"HEADER"},{"heading":"項目詳細","kind":"LIST","key":["No"],"columns":["No","論理名","物理名","PK","NOT NULL","タイプ","長さ","初期値","説明"]}]}]} -->
# 利用者 物理テーブル定義

## テーブルヘッダー

| 項目 | 内容 |
| --- | --- |
| 文書ID／版 | SP2-CSharp_ASPNET-DB-T01／1.0／2026-10-28 |
| 論理／物理名 | 利用者／dbo.m_app_user |
| 対象DB | SQL Server 2022 Express、SampleProject2_Career（専用新規DBの設計） |
| 主キー（構成順） | user_id |
| 項目数 | 8 |
| 対応論理定義 | [基本テーブル](../../../基本設計書/テーブル/01_m_app_user.md)。fieldIdsと項目順/業務長を保持 |
| 制約・索引・更新境界 | PK(user_id)、UQ(login_id CI)、role_id IN (ADMIN,STAFF)、failed_count 0～5。user_idは不変、利用者DELETEなし。認証更新は全更新ゲートで直列化。 |
| 共通定義 | [DB定義](../01_DB定義書.md)。型容量/NULL/既定値、同時保存ゲート、接続・取消・初期設定の正本 |
| 型・長さ・NULL | タイプは実SQL型、長さは従前の業務上限。NOT NULLの〇以外はNULL可。空欄は初期値なし/非適用、明示値0/01/1は保持 |
| 実施状態 | 物理設計のみ。DDL/SQL実行・投入・製品検証未実施 |

## 項目詳細

| No | 論理名 | 物理名 | PK | NOT NULL | タイプ | 長さ | 初期値 | 説明 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | 利用者ID | user_id | 〇 | 〇 | nvarchar(40) | 20 |  | 初期設定時に固定する不変ID。監査の主体。 容量はUTF-16単位、長さ列の業務上限はRuneで別検査。 原値保持はLatin1_General_100_BIN2。 |
| 2 | ログインID | login_id |  | 〇 | varchar(20) | 20 |  | 半角英数字、英字大小を無視して一意。初期設定後はこのDEMOで変更しない。 Latin1_General_100_CI_AS、一意。 |
| 3 | 表示名 | display_name |  | 〇 | nvarchar(80) | 40 |  | メニュー等に表示。本人氏名であることは要求しない。 容量はUTF-16単位、長さ列の業務上限はRuneで別検査。 原値保持はLatin1_General_100_BIN2。 |
| 4 | パスワード検証情報 | password_verifier |  | 〇 | nvarchar(2048) | 1024 |  | ソルト・方式/パラメーターを含む一方向検証情報。平文/復号可能なパスワードを保存しない。形式と方式は詳細工程で固定する。 容量はUTF-16単位、長さ列の業務上限はRuneで別検査。 |
| 5 | 利用者役割 | role_id |  | 〇 | varchar(5) | 5 |  | ADMINまたはSTAFF。汎用コード参照ではない。 |
| 6 | 利用可能 | is_enabled |  | 〇 | bit |  | 1 | 停止時はログインと次の更新/出力を拒否する。 |
| 7 | 連続失敗回数 | failed_count |  | 〇 | tinyint | 1.0 | 0 | 0～5。成功/ロック期間終了後にリセットし、新たな失敗を数える。 |
| 8 | ロック解除日時 | locked_until |  |  | datetime2(7) |  |  | 5回連続失敗した時点+15分。UTC。未ロックはNULL。 UTC、C# DateTimeOffsetからUtcDateTimeで授受。 |
