<!-- spec-meta: {"schema":"spec-md/1.1","documentId":"ACCESS-BAS-STU-03-T_OPERATION_LOG","version":"0.1","path":"sample-project1/srcs/Access/build/spec-generation/design-generation-check/spec/Access/基本設計書/テーブル/05_t_operation_log.md","layout":"TABLE","table":{"logicalName":"操作履歴","physicalName":"t_operation_log","profile":"論理","primaryKey":["log_id"],"fieldIds":{"log_id":"TBL-05-001","target_table":"TBL-05-002","target_key":"TBL-05-003","operation_type":"TBL-05-004","before_version":"TBL-05-005","after_version":"TBL-05-006","changed_columns":"TBL-05-007","executed_by":"TBL-05-008","executed_at":"TBL-05-009","correlation_id":"TBL-05-010","operation_reason":"TBL-05-011","duplicate_confirmed":"TBL-05-012"}},"sheets":[{"sheet":"t_operation_log","kind":"TABLE","sections":[{"heading":"テーブルヘッダー","kind":"HEADER"},{"heading":"項目詳細","kind":"LIST","key":["No"],"columns":["No","論理名","物理名","PK","NOT NULL","タイプ","長さ","初期値","説明"]}]}],"isolationProfile":"Access","generationStatus":"verification-draft","inputSpecRoot":"sample-project1/spec/Access/"} -->
# 操作履歴 テーブル仕様書

## テーブルヘッダー

| 項目 | 内容 |
| --- | --- |
| 文書ID／版 | BAS-STU-03-T_OPERATION_LOG／0.1／2026-10-28 |
| 生成状態 | verification-draft。基本設計Agentの試験生成・未採用 |
| 入力文書版 | ACCESS-BAS-STU-03-T_OPERATION_LOG／8.1。12項目を継承 |
| 論理テーブル名 | 操作履歴 |
| 物理テーブル名 | t_operation_log |
| 対象／スキーマ | 論理／言語・DB製品非依存 |
| 用途／項目数 | 確定変更1件を追記する。個人情報の変更前後値は保存しない。12項目 |
| 主キー（順序） | log_id |
| 共通規則・制約 | [総合仕様・制約](../03_テーブル仕様書.md)／[記述規約](../../規約/全体/テーブル仕様書記述規約.md) |
| 長さ／初期値の基準 | 長さは業務上限。数字は整数桁.小数桁。初期値は業務設定 |
| 項目IDの対応 | TBL-05-{Noを3桁}。既存fieldIdsと項目順を維持 |
| 物理名の位置付け | 対応確認用。実DB型・容量・制約は[Access分冊](../../DB定義/Access/テーブル/05_t_operation_log.md)を保持 |
| 記号 | PK・NOT NULLは〇／空欄。初期値なし・長さ対象外は空欄。条件付き必須は説明参照 |

## 項目詳細

| No | 論理名 | 物理名 | PK | NOT NULL | タイプ | 長さ | 初期値 | 説明 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | 操作履歴番号 | log_id | 〇 | 〇 | 数字 |  | 自動採番 | 追記した履歴を識別する自動付番値。桁上限は採用DB定義に従う。 |
| 2 | 対象情報の種類 | target_table |  | 〇 | 文字 | 21 |  | 学生、クラス、コード分類、コード値のどの変更かを自動設定する。 |
| 3 | 対象の識別情報 | target_key |  | 〇 | 文字 | 35 |  | 管理番号または分類と値を自動設定し、氏名等を含めない。 |
| 4 | 操作の種類 | operation_type |  | 〇 | 文字 | 11 |  | 新規・変更・論理削除・停止・再開の種別を自動設定する。 |
| 5 | 変更前の更新管理番号 | before_version |  |  | 数字 |  |  | 新規は空、それ以外は変更前の版を必須とする。桁上限は採用DB定義に従う。 |
| 6 | 変更後の更新管理番号 | after_version |  | 〇 | 数字 |  | 1 | 新規1、変更は以前の番号＋1を自動設定する。桁上限は採用DB定義に従う。 |
| 7 | 変更項目一覧 | changed_columns |  | 〇 | 配列 |  |  | 変更した項目を列挙する。入力値そのものを複写しない。 |
| 8 | 実行者 | executed_by |  | 〇 | 文字 | 64 |  | 認証された利用者番号を自動設定する。 |
| 9 | 実行日時 | executed_at |  | 〇 | 日時 |  |  | 対応する保存操作と同じ時点を自動設定する。 |
| 10 | 受付番号 | correlation_id |  | 〇 | 識別子 |  |  | 障害調査用の識別子。同一要求を関連付ける。 |
| 11 | 操作・確認理由 | operation_reason |  |  | 文字 | 60 |  | 削除、終了区分訂正、重複警告後の続行では必須とする。 |
| 12 | 重複警告の確認有無 | duplicate_confirmed |  | 〇 | 真偽 |  |  | 別人確認を経て保存した場合に有を自動設定する。 |
