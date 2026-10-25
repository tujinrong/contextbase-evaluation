<!-- spec-meta: {"schema":"spec-md/1.1","documentId":"AS400_RPG-BAS-STU-03-T_OPERATION_LOG","version":"8.1","path":"test-project1/spec/AS400_RPG/基本設計書/テーブル/05_t_operation_log.md","layout":"TABLE","table":{"logicalName":"操作履歴","physicalName":"t_operation_log","profile":"論理","primaryKey":["log_id"],"fieldIds":{"log_id":"TBL-05-001","target_table":"TBL-05-002","target_key":"TBL-05-003","operation_type":"TBL-05-004","before_version":"TBL-05-005","after_version":"TBL-05-006","changed_columns":"TBL-05-007","executed_by":"TBL-05-008","executed_at":"TBL-05-009","correlation_id":"TBL-05-010","operation_reason":"TBL-05-011","duplicate_confirmed":"TBL-05-012"}},"sheets":[{"sheet":"t_operation_log","kind":"TABLE","sections":[{"heading":"テーブルヘッダー","kind":"HEADER"},{"heading":"項目詳細","kind":"LIST","key":["No"],"columns":["No","論理名","物理名","PK","NOT NULL","タイプ","長さ","初期値","説明"]}]}],"isolationProfile":"AS400_RPG"} -->
# 操作履歴 テーブル仕様書

## テーブルヘッダー

| 項目 | 内容 |
| --- | --- |
| 文書ID／版 | BAS-STU-03-T_OPERATION_LOG／8.1／2026-10-25 |
| 論理テーブル名 | 操作履歴 |
| 物理テーブル名 | t_operation_log |
| 対象／スキーマ | 論理／言語・DB製品非依存 |
| 用途／項目数 | 確定した変更１件を追記。個人情報の変更前後値は保持しない。 12項目。 |
| 主キー（順序） | log_id |
| 共通規則・制約 | [総合仕様・制約](../03_テーブル仕様書.md)／[記述・Excel配置規約](../../規約/全体/テーブル仕様書記述規約.md) |
| 長さ／初期値の基準 | 長さは業務上限。数字は整数桁.小数桁。初期値は業務設定。 |
| 項目IDの対応 | TBL-05-{Noを3桁}。メタ情報fieldIdsに対応を記録。 |
| 物理名の位置付け | 対応付けの参照名。実装言語・DB製品の指定ではない。 |
| 記号 | PK・NOT NULL：〇が該当、空欄は非該当。初期値なし・長さ対象外は空欄。条件付き必須は説明参照。 |

## 項目詳細

| No | 論理名 | 物理名 | PK | NOT NULL | タイプ | 長さ | 初期値 | 説明 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | 操作履歴番号 | log_id | 〇 | 〇 | 数字 |  | 自動採番 | 自動。追記記録の識別子。桁上限は採用DB定義を参照。 |
| 2 | 対象情報の種類 | target_table |  | 〇 | 文字 | 21 |  | 自動。学生、クラス、コード分類、コード値のいずれか。 |
| 3 | 対象の識別情報 | target_key |  | 〇 | 文字 | 35 |  | 自動。管理番号または分類と値。氏名等を含めない。 |
| 4 | 操作の種類 | operation_type |  | 〇 | 文字 | 11 |  | 自動。新規・変更・論理削除・停止・再開。 |
| 5 | 変更前の更新管理番号 | before_version |  |  | 数字 |  |  | 新規以外必須。新規は空。桁上限は採用DB定義を参照。 |
| 6 | 変更後の更新管理番号 | after_version |  | 〇 | 数字 |  | 1 | 自動。新規は1、変更は以前の番号＋1。桁上限は採用DB定義を参照。 |
| 7 | 変更項目一覧 | changed_columns |  | 〇 | 配列 |  |  | 自動。変更した項目を記録。入力値自体は複写しない。 |
| 8 | 実行者 | executed_by |  | 〇 | 文字 | 64 |  | 自動。認証された利用者番号。 |
| 9 | 実行日時 | executed_at |  | 〇 | 日時 |  |  | 自動。対応する保存操作の日時。 |
| 10 | 受付番号 | correlation_id |  | 〇 | 識別子 |  |  | 自動。障害調査用。同一要求で関連付ける。 |
| 11 | 操作・確認理由 | operation_reason |  |  | 文字 | 60 |  | 条件付き。削除・終了区分訂正・重複警告続行時は必須。 |
| 12 | 重複警告の確認有無 | duplicate_confirmed |  | 〇 | 真偽 |  |  | 自動。別人確認を経た保存で有。 |
