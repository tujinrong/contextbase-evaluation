<!-- spec-meta: {"schema":"spec-md/1.1","documentId":"DBDEF-ACCESS-M_CLASS","version":"7.1","path":"test-project1/spec/DB定義/Access/テーブル/02_m_class.md","layout":"TABLE","table":{"logicalName":"クラスマスタ","physicalName":"m_class","profile":"Access","primaryKey":["class_id"],"fieldIds":{"class_id":"DB-M_CLASS-CLASS_ID","school_year":"DB-M_CLASS-SCHOOL_YEAR","grade_category":"DB-M_CLASS-GRADE_CATEGORY","grade_code":"DB-M_CLASS-GRADE_CODE","class_code":"DB-M_CLASS-CLASS_CODE","class_name":"DB-M_CLASS-CLASS_NAME","valid_from":"DB-M_CLASS-VALID_FROM","valid_to":"DB-M_CLASS-VALID_TO","capacity":"DB-M_CLASS-CAPACITY","display_order":"DB-M_CLASS-DISPLAY_ORDER","is_active":"DB-M_CLASS-IS_ACTIVE","remarks":"DB-M_CLASS-REMARKS","created_at":"DB-M_CLASS-CREATED_AT","created_by":"DB-M_CLASS-CREATED_BY","updated_at":"DB-M_CLASS-UPDATED_AT","updated_by":"DB-M_CLASS-UPDATED_BY","row_version":"DB-M_CLASS-ROW_VERSION"}},"sheets":[{"sheet":"m_class","kind":"TABLE","sections":[{"heading":"テーブルヘッダー","kind":"HEADER"},{"heading":"項目詳細","kind":"LIST","key":["No"],"columns":["No","論理名","物理名","PK","タイプ","長さ","初期値","説明"]}]}]} -->
# クラスマスタ DB定義書

## テーブルヘッダー

| 項目 | 内容 |
| --- | --- |
| 文書ID／版 | DBDEF-ACCESS-M_CLASS／7.1／2026-10-12 |
| 論理テーブル名 | クラスマスタ |
| 物理テーブル名 | m_class |
| 対象／スキーマ | Access／非適用（ACE） |
| 用途／項目数 | 学校年度内のクラス１件を管理。 17項目。 |
| 主キー（順序） | class_id |
| 共通規則・制約 | [総合仕様・制約](../01_DB定義書.md)／[記述・Excel配置規約](../../../../../docs/テーブル仕様書記述規約.md) |
| 長さ／初期値の基準 | 長さは業務上限。数字は整数桁.小数桁。初期値はDB既定値。画面の初期値とは別。 |
| 項目IDの対応 | 物理列に対応する既存DB項目IDを維持。メタ情報fieldIdsに対応を記録。 |
| 基礎仕様 | [論理テーブル仕様](../../../基本設計書/03_テーブル仕様書.md)／[項目制約](../../../共通/09_項目制約定義.md) |

## 項目詳細

| No | 論理名 | 物理名 | PK | タイプ | 長さ | 初期値 | 説明 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | クラス管理番号 | class_id | 〇 | 数字 | 10.0 | 自動採番 | 自動。DB:COUNTER／NULL不可。内部識別子、変更不可。 |
| 2 | 学校年度 | school_year | － | 数字 | 4.0 | 指定なし | 必須。DB:LONG／NULL不可。4月1日～翌年3月31日、登録後変更不可。 |
| 3 | 学年のコード分類 | grade_category | － | 文字 | 24 | 指定なし | 自動固定。DB:TEXT(48)／NULL不可。学年の分類。固定値GRADE。 |
| 4 | 学年 | grade_code | － | 文字 | 2 | 指定なし | 必須・学年なし。DB:TEXT(4)／NULL不可。参照学生がいる場合の意味変更を禁止。FK:(grade_category,grade_code)→m_code(category_id,code_value)。 |
| 5 | クラスコード | class_code | － | 文字 | 9 | 指定なし | 必須。DB:TEXT(18)／NULL不可。英数字・ハイフン、先頭英数字。年度内で一意、変更不可。 |
| 6 | クラス名 | class_name | － | 文字 | 18 | 指定なし | 必須。DB:TEXT(36)／NULL不可。顧客向けの名称。 |
| 7 | 利用開始日 | valid_from | － | 日付 | － | 指定なし | 必須・年度開始日。DB:TEXT(10)／NULL不可。学校年度内、終了日以下。 |
| 8 | 利用終了日 | valid_to | － | 日付 | － | 指定なし | 必須・年度終了日。DB:TEXT(10)／NULL不可。学校年度内。両端を含む。 |
| 9 | 定員 | capacity | － | 数字 | 4.0 | 指定なし | 任意・未設定。DB:LONG／NULL可。未設定は制限なし。0人定員は指定しない。 |
| 10 | 表示順 | display_order | － | 数字 | 10.0 | 0 | 必須・0。DB:LONG／NULL不可。候補表示の順番。 |
| 11 | 利用可否 | is_active | － | 真偽 | － | True | 必須・利用可。DB:YESNO／NULL不可。停止しても既存参照は残す。 |
| 12 | 備考 | remarks | － | 文字 | 120 | 指定なし | 任意・空。DB:TEXT(240)／NULL可。クラス説明。担任の人事管理は対象外。 |
| 13 | 作成日時 | created_at | － | 日時 | － | 指定なし | 自動。DB:DATETIME／NULL不可。最初の保存日時。変更不可。 |
| 14 | 作成者 | created_by | － | 文字 | 64 | 指定なし | 自動。DB:TEXT(128)／NULL不可。認証された登録者。変更不可。 |
| 15 | 更新日時 | updated_at | － | 日時 | － | 指定なし | 自動。DB:DATETIME／NULL不可。実変更の保存時点。 |
| 16 | 更新者 | updated_by | － | 文字 | 64 | 指定なし | 自動。DB:TEXT(128)／NULL不可。認証された変更者。 |
| 17 | 更新管理番号 | row_version | － | 数字 | 10.0 | 1 | 自動。DB:LONG／NULL不可。新規1、実変更ごとに1加算、上限で停止。2147483647到達後の加算を拒否。 |
