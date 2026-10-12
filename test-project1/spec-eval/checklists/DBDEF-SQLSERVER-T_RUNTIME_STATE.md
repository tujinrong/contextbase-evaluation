<!-- spec-meta: {"schema":"spec-md/1.0","documentId":"EVAL-DBDEF-SQLSERVER-T_RUNTIME_STATE","path":"test-project1/spec-eval/checklists/DBDEF-SQLSERVER-T_RUNTIME_STATE.md","version":"7.1","sheets":[{"heading":"概要","kind":"GRID","sheet":"01_概要"},{"heading":"採点一覧","kind":"LIST","sheet":"02_採点一覧","key":["評価ID"]},{"heading":"集計一覧","kind":"LIST","sheet":"03_集計一覧","key":["評価軸"]},{"heading":"補足説明","kind":"GRID","sheet":"04_補足説明"}]} -->
# DBDEF-SQLSERVER-T_RUNTIME_STATE 仕様書評価チェックリスト

版7.1／2026-10-12。基準改訂。原仕様品質・逆仕様再現の得点は未評価。

## 概要

対象は[07_t_runtime_state](../../spec/DB定義/SQLServer/テーブル/07_t_runtime_state.md)。基準7.1、原仕様SHA256=13e0671d71b8f9ba4da15b7aa6918e7242ec0378cbdf77d90e88d7b5c10583ed。満点11点。元の項目評価IDと１項目１点を引継ぎ、テーブルヘッダーは３点。実採点は未実施。

## 採点一覧

| 評価ID | 対象章 | 仕様ID | 観点 | 期待仕様 | 配点 | 適用 | 原仕様 | 原仕様品質判定 | 原仕様品質得点 | 逆仕様再現判定 | 逆仕様再現得点 | 観測値・証拠 | 指摘 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| DBDEF-SQLSERVER-T_RUNTIME_STATE-5EF3ECE695BB | テーブルヘッダー | TABLE-HEADER | 表の定義・主キー順序 | 文書ID／版=DBDEF-SQLSERVER-T_RUNTIME_STATE／7.1／2026-10-12；論理テーブル名=実行時状態情報；物理テーブル名=t_runtime_state；対象／スキーマ=SQLServer／dbo；用途／項目数=利用者別の検索・確認・成功通知の技術情報。 8項目。補助表の論理名は既存物理名・説明に基づく表記補足。；主キー（順序）=state_id；共通規則・制約=[総合仕様・制約](../../spec/DB定義/SQLServer/01_DB定義書.md)／[記述・Excel配置規約](../../../docs/テーブル仕様書記述規約.md)；長さ／初期値の基準=長さは業務上限。数字は整数桁.小数桁。初期値は処理設定、DB DEFAULT未定義。；項目IDの対応=物理列に対応する既存DB項目IDを維持。メタ情報fieldIdsに対応を記録。；基礎仕様=[論理テーブル仕様](../../spec/基本設計書/03_テーブル仕様書.md)／[項目制約](../../spec/共通/09_項目制約定義.md) | 3 | 適用 | [07_t_runtime_state](../../spec/DB定義/SQLServer/テーブル/07_t_runtime_state.md) | 未評価 | 未採点 | 未評価 | 未採点 | 未記入 | 未記入 |
| DBDEF-SQLSERVER-08C52E3D71A9 | 項目詳細 | AUX-STATE-1 | 項目属性一式 | No=1；論理名=状態識別子；物理名=state_id；PK=〇；タイプ=文字；長さ=64；初期値=－；説明=DB:varchar(64)／NULL不可。PK、256bit乱数の64桁hex。Base64Urlと混在させない。DB DEFAULTは元資料で未定義。。全属性と参照先の条件が一致して１点。 | 1 | 適用 | [07_t_runtime_state](../../spec/DB定義/SQLServer/テーブル/07_t_runtime_state.md) | 未評価 | 未採点 | 未評価 | 未採点 | 未記入 | 未記入 |
| DBDEF-SQLSERVER-7C0BFE1E8E34 | 項目詳細 | AUX-STATE-2 | 項目属性一式 | No=2；論理名=所有者；物理名=owner_id；PK=－；タイプ=文字；長さ=64；初期値=－；説明=DB:nvarchar(128)／NULL不可。認証主体64スカラー値。DB DEFAULTは元資料で未定義。。全属性と参照先の条件が一致して１点。 | 1 | 適用 | [07_t_runtime_state](../../spec/DB定義/SQLServer/テーブル/07_t_runtime_state.md) | 未評価 | 未採点 | 未評価 | 未採点 | 未記入 | 未記入 |
| DBDEF-SQLSERVER-467947DA365D | 項目詳細 | AUX-STATE-3 | 項目属性一式 | No=3；論理名=ログインセッション識別子；物理名=login_session_id；PK=－；タイプ=文字；長さ=64；初期値=－；説明=DB:varchar(64)／NULL不可。認証セッションキー、外部契約。DB DEFAULTは元資料で未定義。。全属性と参照先の条件が一致して１点。 | 1 | 適用 | [07_t_runtime_state](../../spec/DB定義/SQLServer/テーブル/07_t_runtime_state.md) | 未評価 | 未採点 | 未評価 | 未採点 | 未記入 | 未記入 |
| DBDEF-SQLSERVER-9CC82AB05AA2 | 項目詳細 | AUX-STATE-4 | 項目属性一式 | No=4；論理名=状態種別；物理名=state_kind；PK=－；タイプ=文字；長さ=16；初期値=－；説明=DB:varchar(16)／NULL不可。検索・確認・一回の成功通知。DB DEFAULTは元資料で未定義。。全属性と参照先の条件が一致して１点。 | 1 | 適用 | [07_t_runtime_state](../../spec/DB定義/SQLServer/テーブル/07_t_runtime_state.md) | 未評価 | 未採点 | 未評価 | 未採点 | 未記入 | 未記入 |
| DBDEF-SQLSERVER-4B0D661F9639 | 項目詳細 | AUX-STATE-5 | 項目属性一式 | No=5；論理名=暗号化状態情報；物理名=encrypted_payload；PK=－；タイプ=バイナリ；長さ=－；初期値=－；説明=DB:varbinary(max)／NULL不可。認証付き暗号。個人情報の平文永続保存禁止。DB DEFAULTは元資料で未定義。。全属性と参照先の条件が一致して１点。 | 1 | 適用 | [07_t_runtime_state](../../spec/DB定義/SQLServer/テーブル/07_t_runtime_state.md) | 未評価 | 未採点 | 未評価 | 未採点 | 未記入 | 未記入 |
| DBDEF-SQLSERVER-2C38C1F07F5C | 項目詳細 | AUX-STATE-6 | 項目属性一式 | No=6；論理名=有効期限；物理名=expires_at；PK=－；タイプ=日時；長さ=－；初期値=－；説明=DB:datetimeoffset(7)／NULL不可。UTC、検索30分・確認10分。DB DEFAULTは元資料で未定義。。全属性と参照先の条件が一致して１点。 | 1 | 適用 | [07_t_runtime_state](../../spec/DB定義/SQLServer/テーブル/07_t_runtime_state.md) | 未評価 | 未採点 | 未評価 | 未採点 | 未記入 | 未記入 |
| DBDEF-SQLSERVER-E28BCA9686EF | 項目詳細 | AUX-STATE-7 | 項目属性一式 | No=7；論理名=更新管理番号；物理名=revision；PK=－；タイプ=数字；長さ=19.0；初期値=処理:1；説明=DB:bigint／NULL不可。正の更新番号、初期1。DB DEFAULTは元資料で未定義。。全属性と参照先の条件が一致して１点。 | 1 | 適用 | [07_t_runtime_state](../../spec/DB定義/SQLServer/テーブル/07_t_runtime_state.md) | 未評価 | 未採点 | 未評価 | 未採点 | 未記入 | 未記入 |
| DBDEF-SQLSERVER-8FE25D3F533C | 項目詳細 | AUX-STATE-8 | 項目属性一式 | No=8；論理名=消費済み状態；物理名=consumed；PK=－；タイプ=真偽；長さ=－；初期値=処理:0；説明=DB:bit／NULL不可。初期0、一回消費。DB DEFAULTは元資料で未定義。。全属性と参照先の条件が一致して１点。 | 1 | 適用 | [07_t_runtime_state](../../spec/DB定義/SQLServer/テーブル/07_t_runtime_state.md) | 未評価 | 未採点 | 未評価 | 未採点 | 未記入 | 未記入 |

## 集計一覧

| 評価軸 | 確認行数 | 適用満点 | 獲得点 | 状態 |
| --- | --- | --- | --- | --- |
| 原仕様品質 | 9 | 11 | 未採点 | 未評価 |
| 逆仕様再現 | 9 | 11 | 未採点 | 未評価 |

## 補足説明

テーブル別仕様。表現上のタイプ・長さと、説明欄の実DB型・容量・NULL・条件付き必須を両方確認する。
[採点規則](../00_採点規則.md)。分冊前後の二重加点を禁止する。
