<!-- spec-meta: {"schema":"spec-md/1.1","documentId":"VUE_CSHARPAPI-BAS-STU-03-M_CLASS","version":"8.1","path":"test-project1/spec/Vue_CSharpAPI/基本設計書/テーブル/02_m_class.md","layout":"TABLE","table":{"logicalName":"クラスマスタ","physicalName":"m_class","profile":"論理","primaryKey":["class_id"],"fieldIds":{"class_id":"TBL-02-001","school_year":"TBL-02-002","grade_category":"TBL-02-003","grade_code":"TBL-02-004","class_code":"TBL-02-005","class_name":"TBL-02-006","valid_from":"TBL-02-007","valid_to":"TBL-02-008","capacity":"TBL-02-009","display_order":"TBL-02-010","is_active":"TBL-02-011","remarks":"TBL-02-012","created_at":"TBL-02-013","created_by":"TBL-02-014","updated_at":"TBL-02-015","updated_by":"TBL-02-016","row_version":"TBL-02-017"}},"sheets":[{"sheet":"m_class","kind":"TABLE","sections":[{"heading":"テーブルヘッダー","kind":"HEADER"},{"heading":"項目詳細","kind":"LIST","key":["No"],"columns":["No","論理名","物理名","PK","NOT NULL","タイプ","長さ","初期値","説明"]}]}],"isolationProfile":"Vue_CSharpAPI"} -->
# クラスマスタ テーブル仕様書

## テーブルヘッダー

| 項目 | 内容 |
| --- | --- |
| 文書ID／版 | BAS-STU-03-M_CLASS／8.1／2026-10-25 |
| 論理テーブル名 | クラスマスタ |
| 物理テーブル名 | m_class |
| 対象／スキーマ | 論理／言語・DB製品非依存 |
| 用途／項目数 | 学校年度内のクラス１件を管理。 17項目。 |
| 主キー（順序） | class_id |
| 共通規則・制約 | [総合仕様・制約](../03_テーブル仕様書.md)／[記述・Excel配置規約](../../規約/全体/テーブル仕様書記述規約.md) |
| 長さ／初期値の基準 | 長さは業務上限。数字は整数桁.小数桁。初期値は業務設定。 |
| 項目IDの対応 | TBL-02-{Noを3桁}。メタ情報fieldIdsに対応を記録。 |
| 物理名の位置付け | 対応付けの参照名。実装言語・DB製品の指定ではない。 |
| 記号 | PK・NOT NULL：〇が該当、空欄は非該当。初期値なし・長さ対象外は空欄。条件付き必須は説明参照。 |

## 項目詳細

| No | 論理名 | 物理名 | PK | NOT NULL | タイプ | 長さ | 初期値 | 説明 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | クラス管理番号 | class_id | 〇 | 〇 | 数字 |  | 自動採番 | 自動。内部識別子、変更不可。桁上限は採用DB定義を参照。 |
| 2 | 学校年度 | school_year |  | 〇 | 数字 | 4.0 |  | 4月1日～翌年3月31日、登録後変更不可。 |
| 3 | 学年のコード分類 | grade_category |  | 〇 | 文字 | 24 | GRADE | 自動固定。学年の分類。 |
| 4 | 学年 | grade_code |  | 〇 | 文字 | 2 | 00 | 参照学生がいる場合の意味変更を禁止。 |
| 5 | クラスコード | class_code |  | 〇 | 文字 | 9 |  | 英数字・ハイフン、先頭英数字。年度内で一意、変更不可。 |
| 6 | クラス名 | class_name |  | 〇 | 文字 | 18 |  | 顧客向けの名称。 |
| 7 | 利用開始日 | valid_from |  | 〇 | 日付 |  | 年度開始日 | 学校年度内、終了日以下。 |
| 8 | 利用終了日 | valid_to |  | 〇 | 日付 |  | 年度終了日 | 学校年度内。両端を含む。 |
| 9 | 定員 | capacity |  |  | 数字 | 4.0 |  | 未設定は制限なし。0人定員は指定しない。 |
| 10 | 表示順 | display_order |  | 〇 | 数字 |  | 0 | 候補表示の順番。桁上限は採用DB定義を参照。 |
| 11 | 利用可否 | is_active |  | 〇 | 真偽 |  | 利用可 | 停止しても既存参照は残す。 |
| 12 | 備考 | remarks |  |  | 文字 | 120 |  | クラス説明。担任の人事管理は対象外。 |
| 13 | 作成日時 | created_at |  | 〇 | 日時 |  |  | 自動。最初の保存日時。変更不可。 |
| 14 | 作成者 | created_by |  | 〇 | 文字 | 64 |  | 自動。認証された登録者。変更不可。 |
| 15 | 更新日時 | updated_at |  | 〇 | 日時 |  |  | 自動。実変更の保存時点。 |
| 16 | 更新者 | updated_by |  | 〇 | 文字 | 64 |  | 自動。認証された変更者。 |
| 17 | 更新管理番号 | row_version |  | 〇 | 数字 |  | 1 | 自動。新規1、実変更ごとに1加算、上限で停止。桁上限は採用DB定義を参照。 |
