<!-- spec-meta: {"schema":"spec-md/1.1","documentId":"SP2-CSharp_ASPNET-DB-T05","version":"1.0","path":"sample-project2/spec/CSharp_ASPNET/DB定義/SQLServer/テーブル/05_m_code.md","layout":"TABLE","table":{"logicalName":"汎用コード","physicalName":"m_code","profile":"SQLServer2022","primaryKey":["category_id","code"],"fieldIds":{"category_id":"T05-001","code":"T05-002","code_name":"T05-003","sort_order":"T05-004","is_enabled":"T05-005","updated_at":"T05-006","updated_by":"T05-007","revision":"T05-008"},"schema":"dbo"},"sheets":[{"sheet":"m_code","kind":"TABLE","sections":[{"heading":"テーブルヘッダー","kind":"HEADER"},{"heading":"項目詳細","kind":"LIST","key":["No"],"columns":["No","論理名","物理名","PK","NOT NULL","タイプ","長さ","初期値","説明"]}]}]} -->
# 汎用コード 物理テーブル定義

## テーブルヘッダー

| 項目 | 内容 |
| --- | --- |
| 文書ID／版 | SP2-CSharp_ASPNET-DB-T05／1.0／2026-10-28 |
| 論理／物理名 | 汎用コード／dbo.m_code |
| 対象DB | SQL Server 2022 Express、SampleProject2_Career（専用新規DBの設計） |
| 主キー（構成順） | category_id、code |
| 項目数 | 8 |
| 対応論理定義 | [基本テーブル](../../../基本設計書/テーブル/05_m_code.md)。fieldIdsと項目順/業務長を保持 |
| 制約・索引・更新境界 | PK(category_id,code)、分類FK NO ACTION、codeは01～99、sort_order 1～999、revision 1～2147483647。初期9/分類99上限と在籍固定3値保護は確定時サービス検査。キー変更/DELETEなし。 |
| 共通定義 | [DB定義](../01_DB定義書.md)。型容量/NULL/既定値、同時保存ゲート、接続・取消・初期設定の正本 |
| 型・長さ・NULL | タイプは実SQL型、長さは従前の業務上限。NOT NULLの〇以外はNULL可。空欄は初期値なし/非適用、明示値0/01/1は保持 |
| 実施状態 | 物理設計のみ。DDL/SQL実行・投入・製品検証未実施 |

## 項目詳細

| No | 論理名 | 物理名 | PK | NOT NULL | タイプ | 長さ | 初期値 | 説明 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | 分類ID | category_id | 〇 | 〇 | varchar(24) | 24 |  | コード分類を参照。不変。 |
| 2 | コード | code | 〇 | 〇 | char(2) | 2 |  | 半角数字01～99。分類内一意、不変。 |
| 3 | 名称 | code_name |  | 〇 | nvarchar(80) | 40 |  | 現在名称を画面/帳票へ表示。 容量はUTF-16単位、長さ列の業務上限はRuneで別検査。 原値保持はLatin1_General_100_BIN2。 |
| 4 | 並び順 | sort_order |  | 〇 | smallint | 3.0 | 1 | 1～999。同順可、コード昇順で補完。 |
| 5 | 有効 | is_enabled |  | 〇 | bit |  | 1 | 停止しても既存参照は保持。在籍3値は停止不可。 |
| 6 | 更新日時 | updated_at |  | 〇 | datetime2(7) |  |  | 新規/実変更の確定時UTC。 UTC、C# DateTimeOffsetからUtcDateTimeで授受。 |
| 7 | 更新者 | updated_by |  | 〇 | nvarchar(40) | 20 |  | 認証済みADMINの利用者ID。初期投入時は投入主体。 容量はUTF-16単位、長さ列の業務上限はRuneで別検査。 原値保持はLatin1_General_100_BIN2。 当時の主体記録、FKなし。 |
| 8 | 更新版 | revision |  | 〇 | int | 10.0 | 1 | 1～2147483647。競合検出用。 |
