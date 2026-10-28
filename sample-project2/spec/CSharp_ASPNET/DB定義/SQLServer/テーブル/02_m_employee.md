<!-- spec-meta: {"schema":"spec-md/1.1","documentId":"SP2-CSharp_ASPNET-DB-T02","version":"1.0","path":"sample-project2/spec/CSharp_ASPNET/DB定義/SQLServer/テーブル/02_m_employee.md","layout":"TABLE","table":{"logicalName":"社員","physicalName":"m_employee","profile":"SQLServer2022","primaryKey":["employee_id"],"fieldIds":{"employee_id":"T02-001","employee_no":"T02-002","employee_name":"T02-003","employee_kana":"T02-004","department_category":"T02-005","department_code":"T02-006","employment_category":"T02-007","employment_status":"T02-008","join_date":"T02-009","career_summary":"T02-010","skills":"T02-011","qualifications":"T02-012","self_pr":"T02-013","updated_at":"T02-014","updated_by":"T02-015","revision":"T02-016"},"schema":"dbo"},"sheets":[{"sheet":"m_employee","kind":"TABLE","sections":[{"heading":"テーブルヘッダー","kind":"HEADER"},{"heading":"項目詳細","kind":"LIST","key":["No"],"columns":["No","論理名","物理名","PK","NOT NULL","タイプ","長さ","初期値","説明"]}]}]} -->
# 社員 物理テーブル定義

## テーブルヘッダー

| 項目 | 内容 |
| --- | --- |
| 文書ID／版 | SP2-CSharp_ASPNET-DB-T02／1.0／2026-10-28 |
| 論理／物理名 | 社員／dbo.m_employee |
| 対象DB | SQL Server 2022 Express、SampleProject2_Career（専用新規DBの設計） |
| 主キー（構成順） | employee_id |
| 項目数 | 16 |
| 対応論理定義 | [基本テーブル](../../../基本設計書/テーブル/02_m_employee.md)。fieldIdsと項目順/業務長を保持 |
| 制約・索引・更新境界 | PK(employee_id IDENTITY)、UQ(employee_no)、番号6桁、固定分類CHECK、部署/在籍の複合FK、revision 1～2147483647、join_date>=1900-01-01。社員DELETEなし。社員数200は確定時検査。 |
| 共通定義 | [DB定義](../01_DB定義書.md)。型容量/NULL/既定値、同時保存ゲート、接続・取消・初期設定の正本 |
| 型・長さ・NULL | タイプは実SQL型、長さは従前の業務上限。NOT NULLの〇以外はNULL可。空欄は初期値なし/非適用、明示値0/01/1は保持 |
| 実施状態 | 物理設計のみ。DDL/SQL実行・投入・製品検証未実施 |

## 項目詳細

| No | 論理名 | 物理名 | PK | NOT NULL | タイプ | 長さ | 初期値 | 説明 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | 社員管理ID | employee_id | 〇 | 〇 | bigint |  | 自動採番 | 内部識別。不変、欠番可。 IDENTITY(1,1)、OUTPUTで取得。MAX+1禁止。 |
| 2 | 社員番号 | employee_no |  | 〇 | char(6) | 6 |  | 半角数字6桁、一意、不変、先頭ゼロ保持。 |
| 3 | 氏名 | employee_name |  | 〇 | nvarchar(80) | 40 |  | 表示表記を保存し、検索用の正規化は照合時だけ行う。 容量はUTF-16単位、長さ列の業務上限はRuneで別検査。 原値保持はLatin1_General_100_BIN2。 |
| 4 | 氏名カナ | employee_kana |  | 〇 | nvarchar(160) | 80 |  | 全角カナ・長音・中点・空白。半角カナは正規化する。 容量はUTF-16単位、長さ列の業務上限はRuneで別検査。 原値保持はLatin1_General_100_BIN2。 |
| 5 | 部署分類 | department_category |  | 〇 | varchar(24) | 24 | DEPARTMENT | 自動固定、利用者は変更不可。 |
| 6 | 部署 | department_code |  | 〇 | char(2) | 2 |  | 部署分類と複合で汎用コード参照。 |
| 7 | 在籍分類 | employment_category |  | 〇 | varchar(24) | 24 | EMPLOYMENT_STATUS | 自動固定、利用者は変更不可。 |
| 8 | 在籍区分 | employment_status |  | 〇 | char(2) | 2 | 01 | 在職01/休職02/退職03。社員を削除する属性ではない。 |
| 9 | 入社日 | join_date |  | 〇 | date |  |  | 1900-01-01以上、業務日以下。前職経歴の期間を制限しない。 |
| 10 | 職務要約 | career_summary |  |  | nvarchar(2000) | 1000 |  | 改行可。 容量はUTF-16単位、長さ列の業務上限はRuneで別検査。 |
| 11 | スキル・得意分野 | skills |  |  | nvarchar(2000) | 1000 |  | 自由記入。技術経験年数の自動集計はしない。 容量はUTF-16単位、長さ列の業務上限はRuneで別検査。 |
| 12 | 保有資格 | qualifications |  |  | nvarchar(2000) | 1000 |  | 1資格1行を目安に資格名・取得年月を自由記入。 容量はUTF-16単位、長さ列の業務上限はRuneで別検査。 |
| 13 | 自己PR | self_pr |  |  | nvarchar(2000) | 1000 |  | 改行可。 容量はUTF-16単位、長さ列の業務上限はRuneで別検査。 |
| 14 | 更新日時 | updated_at |  | 〇 | datetime2(7) |  |  | 保存確定時のUTC時点。新規時にも設定。 UTC、C# DateTimeOffsetからUtcDateTimeで授受。 |
| 15 | 更新者 | updated_by |  | 〇 | nvarchar(40) | 20 |  | 認証主体の利用者ID。利用者表の対応IDを記録。 容量はUTF-16単位、長さ列の業務上限はRuneで別検査。 原値保持はLatin1_General_100_BIN2。 当時の主体記録、FKなし。 |
| 16 | 更新版 | revision |  | 〇 | int | 10.0 | 1 | 1～2147483647。全経歴を含む集約の楽観版。 |
