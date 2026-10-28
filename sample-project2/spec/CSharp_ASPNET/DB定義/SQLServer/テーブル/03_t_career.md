<!-- spec-meta: {"schema":"spec-md/1.1","documentId":"SP2-CSharp_ASPNET-DB-T03","version":"1.0","path":"sample-project2/spec/CSharp_ASPNET/DB定義/SQLServer/テーブル/03_t_career.md","layout":"TABLE","table":{"logicalName":"社員経歴","physicalName":"t_career","profile":"SQLServer2022","primaryKey":["career_id"],"fieldIds":{"career_id":"T03-001","employee_id":"T03-002","start_month":"T03-003","end_month":"T03-004","company_name":"T03-005","project_name":"T03-006","description":"T03-007","duties":"T03-008","achievements":"T03-009","technologies":"T03-010","role_category":"T03-011","role_code":"T03-012","team_size":"T03-013","phases":"T03-014"},"schema":"dbo"},"sheets":[{"sheet":"t_career","kind":"TABLE","sections":[{"heading":"テーブルヘッダー","kind":"HEADER"},{"heading":"項目詳細","kind":"LIST","key":["No"],"columns":["No","論理名","物理名","PK","NOT NULL","タイプ","長さ","初期値","説明"]}]}]} -->
# 社員経歴 物理テーブル定義

## テーブルヘッダー

| 項目 | 内容 |
| --- | --- |
| 文書ID／版 | SP2-CSharp_ASPNET-DB-T03／1.0／2026-10-28 |
| 論理／物理名 | 社員経歴／dbo.t_career |
| 対象DB | SQL Server 2022 Express、SampleProject2_Career（専用新規DBの設計） |
| 主キー（構成順） | career_id |
| 項目数 | 14 |
| 対応論理定義 | [基本テーブル](../../../基本設計書/テーブル/03_t_career.md)。fieldIdsと項目順/業務長を保持 |
| 制約・索引・更新境界 | PK(career_id IDENTITY)、employee_id FK NO ACTION、役割複合FK、role_category固定、年月DAY=1/開始≦終了、人数1～999。IX(employee_id,start_month DESC,career_id DESC)。20件/11値完全重複/所有は親保存内で検査。 |
| 共通定義 | [DB定義](../01_DB定義書.md)。型容量/NULL/既定値、同時保存ゲート、接続・取消・初期設定の正本 |
| 型・長さ・NULL | タイプは実SQL型、長さは従前の業務上限。NOT NULLの〇以外はNULL可。空欄は初期値なし/非適用、明示値0/01/1は保持 |
| 実施状態 | 物理設計のみ。DDL/SQL実行・投入・製品検証未実施 |

## 項目詳細

| No | 論理名 | 物理名 | PK | NOT NULL | タイプ | 長さ | 初期値 | 説明 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | 経歴ID | career_id | 〇 | 〇 | bigint |  | 自動採番 | 不変。画面内の未保存行識別子と分ける。 IDENTITY(1,1)、OUTPUTで取得。MAX+1禁止。 |
| 2 | 社員管理ID | employee_id |  | 〇 | bigint |  |  | 社員の主キー参照。親のない明細は不可。 |
| 3 | 開始年月 | start_month |  | 〇 | date |  |  | 1900-01～業務年月、月初日で保存。 |
| 4 | 終了年月 | end_month |  |  | date |  |  | 開始年月以上、業務年月以下、月初日。NULLは継続中。 |
| 5 | 会社名 | company_name |  | 〇 | nvarchar(200) | 100 |  | その経歴の所属会社。前職を含む。 容量はUTF-16単位、長さ列の業務上限はRuneで別検査。 原値保持はLatin1_General_100_BIN2。 |
| 6 | 案件名 | project_name |  | 〇 | nvarchar(200) | 100 |  | 案件名または担当職務名。顧客等は匿名表記可。 容量はUTF-16単位、長さ列の業務上限はRuneで別検査。 原値保持はLatin1_General_100_BIN2。 |
| 7 | 業務概要 | description |  | 〇 | nvarchar(2000) | 1000 |  | 案件・職務の目的や概要。 容量はUTF-16単位、長さ列の業務上限はRuneで別検査。 |
| 8 | 担当業務 | duties |  | 〇 | nvarchar(2000) | 1000 |  | 本人の担当範囲。 容量はUTF-16単位、長さ列の業務上限はRuneで別検査。 |
| 9 | 実績・成果 | achievements |  |  | nvarchar(2000) | 1000 |  | 成果を自由記入。数値成果を必須にしない。 容量はUTF-16単位、長さ列の業務上限はRuneで別検査。 |
| 10 | 技術環境 | technologies |  |  | nvarchar(1000) | 500 |  | OS・言語/FW・DB等を1欄に自由記入。 容量はUTF-16単位、長さ列の業務上限はRuneで別検査。 |
| 11 | 役割分類 | role_category |  | 〇 | varchar(24) | 24 | PROJECT_ROLE | 自動固定。 |
| 12 | 役割 | role_code |  | 〇 | char(2) | 2 |  | 役割分類と複合で汎用コード参照。 |
| 13 | チーム人数 | team_size |  | 〇 | smallint | 3.0 |  | 1～999の整数。個人担当も1として登録。 |
| 14 | 担当工程 | phases |  |  | nvarchar(400) | 200 |  | 要件整理・設計・開発・運用等を自由記入。 容量はUTF-16単位、長さ列の業務上限はRuneで別検査。 |
