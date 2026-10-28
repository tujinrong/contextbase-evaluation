<!-- spec-meta: {"schema":"spec-md/1.1","documentId":"ACCESS-BAS-STU-03-M_CLASS","version":"0.1","path":"sample-project1/srcs/Access/build/spec-generation/design-generation-check/spec/Access/基本設計書/テーブル/02_m_class.md","layout":"TABLE","table":{"logicalName":"クラスマスタ","physicalName":"m_class","profile":"論理","primaryKey":["class_id"],"fieldIds":{"class_id":"TBL-02-001","school_year":"TBL-02-002","grade_category":"TBL-02-003","grade_code":"TBL-02-004","class_code":"TBL-02-005","class_name":"TBL-02-006","valid_from":"TBL-02-007","valid_to":"TBL-02-008","capacity":"TBL-02-009","display_order":"TBL-02-010","is_active":"TBL-02-011","remarks":"TBL-02-012","created_at":"TBL-02-013","created_by":"TBL-02-014","updated_at":"TBL-02-015","updated_by":"TBL-02-016","row_version":"TBL-02-017"}},"sheets":[{"sheet":"m_class","kind":"TABLE","sections":[{"heading":"テーブルヘッダー","kind":"HEADER"},{"heading":"項目詳細","kind":"LIST","key":["No"],"columns":["No","論理名","物理名","PK","NOT NULL","タイプ","長さ","初期値","説明"]}]}],"isolationProfile":"Access","generationStatus":"verification-draft","inputSpecRoot":"sample-project1/spec/Access/"} -->
# クラスマスタ テーブル仕様書

## テーブルヘッダー

| 項目 | 内容 |
| --- | --- |
| 文書ID／版 | BAS-STU-03-M_CLASS／0.1／2026-10-28 |
| 生成状態 | verification-draft。基本設計Agentの試験生成・未採用 |
| 入力文書版 | ACCESS-BAS-STU-03-M_CLASS／8.1。17項目を継承 |
| 論理テーブル名 | クラスマスタ |
| 物理テーブル名 | m_class |
| 対象／スキーマ | 論理／言語・DB製品非依存 |
| 用途／項目数 | 学校年度内のクラス1件と利用条件を管理。17項目 |
| 主キー（順序） | class_id |
| 共通規則・制約 | [総合仕様・制約](../03_テーブル仕様書.md)／[記述規約](../../規約/全体/テーブル仕様書記述規約.md) |
| 長さ／初期値の基準 | 長さは業務上限。数字は整数桁.小数桁。初期値は業務設定 |
| 項目IDの対応 | TBL-02-{Noを3桁}。既存fieldIdsと項目順を維持 |
| 物理名の位置付け | 対応確認用。実DB型・容量・制約は[Access分冊](../../DB定義/Access/テーブル/02_m_class.md)を保持 |
| 記号 | PK・NOT NULLは〇／空欄。初期値なし・長さ対象外は空欄。条件付き必須は説明参照 |

## 項目詳細

| No | 論理名 | 物理名 | PK | NOT NULL | タイプ | 長さ | 初期値 | 説明 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | クラス管理番号 | class_id | 〇 | 〇 | 数字 |  | 自動採番 | 内部識別子を自動付番し、変更しない。桁上限は採用DB定義に従う。 |
| 2 | 学校年度 | school_year |  | 〇 | 数字 | 4.0 |  | 4月1日から翌年3月31日まで。登録後の年度変更は行わない。 |
| 3 | 学年のコード分類 | grade_category |  | 〇 | 文字 | 24 | GRADE | 学年の分類を自動で固定設定する。 |
| 4 | 学年 | grade_code |  | 〇 | 文字 | 2 | 00 | 参照する学生がいる場合、学年の意味を変更しない。 |
| 5 | クラスコード | class_code |  | 〇 | 文字 | 9 |  | 英数字・ハイフン、先頭英数字。年度内で一意、登録後は変更しない。 |
| 6 | クラス名 | class_name |  | 〇 | 文字 | 18 |  | 顧客向けに提示するクラス名称を保持する。 |
| 7 | 利用開始日 | valid_from |  | 〇 | 日付 |  | 年度開始日 | 学校年度内かつ利用終了日以下とする。 |
| 8 | 利用終了日 | valid_to |  | 〇 | 日付 |  | 年度終了日 | 学校年度内とし、期間には開始日・終了日を含める。 |
| 9 | 定員 | capacity |  |  | 数字 | 4.0 |  | 未設定は制限なし。0人定員は指定しない。 |
| 10 | 表示順 | display_order |  | 〇 | 数字 |  | 0 | クラス候補の表示順。桁上限は採用DB定義に従う。 |
| 11 | 利用可否 | is_active |  | 〇 | 真偽 |  | 利用可 | 停止後も保存済みの参照先として実体を残す。 |
| 12 | 備考 | remarks |  |  | 文字 | 120 |  | クラスの補足。担任の人事情報は管理しない。 |
| 13 | 作成日時 | created_at |  | 〇 | 日時 |  |  | 最初の保存時点を自動設定し、後から変更しない。 |
| 14 | 作成者 | created_by |  | 〇 | 文字 | 64 |  | 認証済み登録者を自動設定し、登録後は変更しない。 |
| 15 | 更新日時 | updated_at |  | 〇 | 日時 |  |  | 実変更を保存した時点を自動設定する。 |
| 16 | 更新者 | updated_by |  | 〇 | 文字 | 64 |  | 実変更を行った認証済み利用者を設定する。 |
| 17 | 更新管理番号 | row_version |  | 〇 | 数字 |  | 1 | 新規1、実変更ごとに1加算し、上限では停止する。桁上限は採用DB定義に従う。 |
