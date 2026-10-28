<!-- spec-meta: {"schema":"spec-md/1.1","documentId":"ACCESS-DBDEF-ACCESS-T_WRITE_GUARD","version":"8.1","path":"sample-project1/srcs/Access/build/spec-generation/design-generation-check/spec/Access/DB定義/Access/テーブル/06_t_write_guard.md","layout":"TABLE","table":{"logicalName":"書込み制御情報","physicalName":"t_write_guard","profile":"Access","primaryKey":["guard_id"],"fieldIds":{"guard_id":"AUX-GUARD-01","lock_bit":"AUX-GUARD-02"}},"sheets":[{"sheet":"t_write_guard","kind":"TABLE","sections":[{"heading":"テーブルヘッダー","kind":"HEADER"},{"heading":"項目詳細","kind":"LIST","key":["No"],"columns":["No","論理名","物理名","PK","NOT NULL","タイプ","長さ","初期値","説明"]}]}],"isolationProfile":"Access","generationStatus":"verification-draft","inputSpecRoot":"sample-project1/spec/Access/"} -->
# 書込み制御情報 DB定義書

## テーブルヘッダー

| 項目 | 内容 |
| --- | --- |
| 文書ID／版 | DBDEF-ACCESS-T_WRITE_GUARD／8.1／2026-10-25 |
| 論理テーブル名 | 書込み制御情報 |
| 物理テーブル名 | t_write_guard |
| 対象／スキーマ | Access／非適用（ACE） |
| 用途／項目数 | 協調処理の同時実行を制御する固定行。 2項目。補助表の論理名は既存物理名・説明に基づく表記補足。 |
| 主キー（順序） | guard_id |
| 共通規則・制約 | [総合仕様・制約](../01_DB定義書.md)／[記述・Excel配置規約](../../../規約/全体/テーブル仕様書記述規約.md) |
| 長さ／初期値の基準 | 長さは業務上限、タイプはDB型・容量。初期値は処理設定。DB DEFAULTは未定義。 |
| 項目IDの対応 | 物理列に対応する既存DB項目IDを維持。メタ情報fieldIdsに対応を記録。 |
| 基礎仕様 | [論理テーブル仕様](../../../基本設計書/03_テーブル仕様書.md)／[項目制約](../../../共通/09_項目制約定義.md) |
| 記号 | PK・NOT NULL：〇が該当、空欄は非該当。初期値なし・長さ対象外は空欄。条件付き必須は説明参照。 |

## 項目詳細

| No | 論理名 | 物理名 | PK | NOT NULL | タイプ | 長さ | 初期値 | 説明 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | 制御行番号 | guard_id | 〇 | 〇 | LONG | 1.0 | 処理:1 | 固定値1。 |
| 2 | ロック状態 | lock_bit |  | 〇 | YESNO |  | 処理:False | 初期Falseまたは0、全協調更新・必要な検索で制御行を取得。 |
