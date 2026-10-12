<!-- spec-meta: {"schema":"spec-md/1.1","documentId":"DBDEF-DB2_FOR_I-T_WRITE_GUARD","version":"7.1","path":"test-project1/spec/DB定義/Db2_for_i/テーブル/06_t_write_guard.md","layout":"TABLE","table":{"logicalName":"書込み制御情報","physicalName":"t_write_guard","profile":"Db2_for_i","primaryKey":["guard_id"],"fieldIds":{"guard_id":"AUX-GUARD-01","lock_bit":"AUX-GUARD-02"}},"sheets":[{"sheet":"t_write_guard","kind":"TABLE","sections":[{"heading":"テーブルヘッダー","kind":"HEADER"},{"heading":"項目詳細","kind":"LIST","key":["No"],"columns":["No","論理名","物理名","PK","タイプ","長さ","初期値","説明"]}]}]} -->
# 書込み制御情報 DB定義書

## テーブルヘッダー

| 項目 | 内容 |
| --- | --- |
| 文書ID／版 | DBDEF-DB2_FOR_I-T_WRITE_GUARD／7.1／2026-10-12 |
| 論理テーブル名 | 書込み制御情報 |
| 物理テーブル名 | t_write_guard |
| 対象／スキーマ | Db2_for_i／STUDAPP |
| 用途／項目数 | 協調処理の同時実行を制御する固定行。 2項目。補助表の論理名は既存物理名・説明に基づく表記補足。 |
| 主キー（順序） | guard_id |
| 共通規則・制約 | [総合仕様・制約](../01_DB定義書.md)／[記述・Excel配置規約](../../../../../docs/テーブル仕様書記述規約.md) |
| 長さ／初期値の基準 | 長さは業務上限。数字は整数桁.小数桁。初期値は処理設定、DB DEFAULT未定義。 |
| 項目IDの対応 | 物理列に対応する既存DB項目IDを維持。メタ情報fieldIdsに対応を記録。 |
| 基礎仕様 | [論理テーブル仕様](../../../基本設計書/03_テーブル仕様書.md)／[項目制約](../../../共通/09_項目制約定義.md) |

## 項目詳細

| No | 論理名 | 物理名 | PK | タイプ | 長さ | 初期値 | 説明 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | 制御行番号 | guard_id | 〇 | 数字 | 1.0 | 処理:1 | DB:SMALLINT／NULL不可。PK、固定値1。DB DEFAULTは元資料で未定義。 |
| 2 | ロック状態 | lock_bit | － | 真偽 | － | 処理:0 | DB:SMALLINT／NULL不可。初期0、全協調更新・必要な検索で制御行を取得。DB DEFAULTは元資料で未定義。 |
