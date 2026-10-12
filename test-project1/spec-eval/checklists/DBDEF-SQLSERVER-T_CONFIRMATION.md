<!-- spec-meta: {"schema":"spec-md/1.0","documentId":"EVAL-DBDEF-SQLSERVER-T_CONFIRMATION","path":"test-project1/spec-eval/checklists/DBDEF-SQLSERVER-T_CONFIRMATION.md","version":"7.1","sheets":[{"heading":"概要","kind":"GRID","sheet":"01_概要"},{"heading":"採点一覧","kind":"LIST","sheet":"02_採点一覧","key":["評価ID"]},{"heading":"集計一覧","kind":"LIST","sheet":"03_集計一覧","key":["評価軸"]},{"heading":"補足説明","kind":"GRID","sheet":"04_補足説明"}]} -->
# DBDEF-SQLSERVER-T_CONFIRMATION 仕様書評価チェックリスト

版7.1／2026-10-12。基準改訂。原仕様品質・逆仕様再現の得点は未評価。

## 概要

対象は[06_t_confirmation](../../spec/DB定義/SQLServer/テーブル/06_t_confirmation.md)。基準7.1、原仕様SHA256=16f8e4e8fa950cee7b00024977a846055107160f2c5a8dc3c01aef7da9764a4e。満点12点。元の項目評価IDと１項目１点を引継ぎ、テーブルヘッダーは３点。実採点は未実施。

## 採点一覧

| 評価ID | 対象章 | 仕様ID | 観点 | 期待仕様 | 配点 | 適用 | 原仕様 | 原仕様品質判定 | 原仕様品質得点 | 逆仕様再現判定 | 逆仕様再現得点 | 観測値・証拠 | 指摘 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| DBDEF-SQLSERVER-T_CONFIRMATION-5EF3ECE695BB | テーブルヘッダー | TABLE-HEADER | 表の定義・主キー順序 | 文書ID／版=DBDEF-SQLSERVER-T_CONFIRMATION／7.1／2026-10-12；論理テーブル名=重複確認情報；物理テーブル名=t_confirmation；対象／スキーマ=SQLServer／dbo；用途／項目数=重複候補の確認と保存要求を関連付ける技術情報。 9項目。補助表の論理名は既存物理名・説明に基づく表記補足。；主キー（順序）=token；共通規則・制約=[総合仕様・制約](../../spec/DB定義/SQLServer/01_DB定義書.md)／[記述・Excel配置規約](../../../docs/テーブル仕様書記述規約.md)；長さ／初期値の基準=長さは業務上限。数字は整数桁.小数桁。初期値は処理設定、DB DEFAULT未定義。；項目IDの対応=物理列に対応する既存DB項目IDを維持。メタ情報fieldIdsに対応を記録。；基礎仕様=[論理テーブル仕様](../../spec/基本設計書/03_テーブル仕様書.md)／[項目制約](../../spec/共通/09_項目制約定義.md) | 3 | 適用 | [06_t_confirmation](../../spec/DB定義/SQLServer/テーブル/06_t_confirmation.md) | 未評価 | 未採点 | 未評価 | 未採点 | 未記入 | 未記入 |
| DBDEF-SQLSERVER-150705F3B7E6 | 項目詳細 | AUX-CONF-1 | 項目属性一式 | No=1；論理名=確認トークン；物理名=token；PK=〇；タイプ=識別子；長さ=－；初期値=－；説明=DB:uniqueidentifier／NULL不可。PK、予測困難な発行値。DB DEFAULTは元資料で未定義。。全属性と参照先の条件が一致して１点。 | 1 | 適用 | [06_t_confirmation](../../spec/DB定義/SQLServer/テーブル/06_t_confirmation.md) | 未評価 | 未採点 | 未評価 | 未採点 | 未記入 | 未記入 |
| DBDEF-SQLSERVER-117821D57334 | 項目詳細 | AUX-CONF-2 | 項目属性一式 | No=2；論理名=認証主体；物理名=principal；PK=－；タイプ=文字；長さ=64；初期値=－；説明=DB:nvarchar(128)／NULL不可。発行時の認証主体。DB DEFAULTは元資料で未定義。。全属性と参照先の条件が一致して１点。 | 1 | 適用 | [06_t_confirmation](../../spec/DB定義/SQLServer/テーブル/06_t_confirmation.md) | 未評価 | 未採点 | 未評価 | 未採点 | 未記入 | 未記入 |
| DBDEF-SQLSERVER-FB9A067DBEB3 | 項目詳細 | AUX-CONF-3 | 項目属性一式 | No=3；論理名=認証セッション；物理名=session_id；PK=－；タイプ=識別子；長さ=－；初期値=－；説明=DB:uniqueidentifier／NULL不可。認証セッション。DB DEFAULTは元資料で未定義。。全属性と参照先の条件が一致して１点。 | 1 | 適用 | [06_t_confirmation](../../spec/DB定義/SQLServer/テーブル/06_t_confirmation.md) | 未評価 | 未採点 | 未評価 | 未採点 | 未記入 | 未記入 |
| DBDEF-SQLSERVER-0B15A1560172 | 項目詳細 | AUX-CONF-4 | 項目属性一式 | No=4；論理名=対象学生管理番号；物理名=target_id；PK=－；タイプ=数字；長さ=19.0；初期値=－；説明=DB:bigint／NULL可。新規NULL、更新は学生ID。DB DEFAULTは元資料で未定義。。全属性と参照先の条件が一致して１点。 | 1 | 適用 | [06_t_confirmation](../../spec/DB定義/SQLServer/テーブル/06_t_confirmation.md) | 未評価 | 未採点 | 未評価 | 未採点 | 未記入 | 未記入 |
| DBDEF-SQLSERVER-776F2B152C2F | 項目詳細 | AUX-CONF-5 | 項目属性一式 | No=5；論理名=読込時更新管理番号；物理名=expected_version；PK=－；タイプ=数字；長さ=19.0；初期値=－；説明=DB:bigint／NULL可。新規NULL、更新は正の版。DB DEFAULTは元資料で未定義。。全属性と参照先の条件が一致して１点。 | 1 | 適用 | [06_t_confirmation](../../spec/DB定義/SQLServer/テーブル/06_t_confirmation.md) | 未評価 | 未採点 | 未評価 | 未採点 | 未記入 | 未記入 |
| DBDEF-SQLSERVER-50AAA747C754 | 項目詳細 | AUX-CONF-6 | 項目属性一式 | No=6；論理名=入力内容ハッシュ；物理名=payload_hash；PK=－；タイプ=バイナリ；長さ=32；初期値=－；説明=DB:binary(32)／NULL不可。正規化した19業務入力のハッシュ。DB DEFAULTは元資料で未定義。。全属性と参照先の条件が一致して１点。 | 1 | 適用 | [06_t_confirmation](../../spec/DB定義/SQLServer/テーブル/06_t_confirmation.md) | 未評価 | 未採点 | 未評価 | 未採点 | 未記入 | 未記入 |
| DBDEF-SQLSERVER-BE5AA671FC24 | 項目詳細 | AUX-CONF-7 | 項目属性一式 | No=7；論理名=重複候補ハッシュ；物理名=candidate_hash；PK=－；タイプ=バイナリ；長さ=32；初期値=－；説明=DB:binary(32)／NULL不可。全候補ID/版の正規化集合ハッシュ。DB DEFAULTは元資料で未定義。。全属性と参照先の条件が一致して１点。 | 1 | 適用 | [06_t_confirmation](../../spec/DB定義/SQLServer/テーブル/06_t_confirmation.md) | 未評価 | 未採点 | 未評価 | 未採点 | 未記入 | 未記入 |
| DBDEF-SQLSERVER-1C626EEB41CA | 項目詳細 | AUX-CONF-8 | 項目属性一式 | No=8；論理名=有効期限；物理名=expires_at；PK=－；タイプ=日時；長さ=－；初期値=－；説明=DB:datetimeoffset(7)／NULL不可。発行時点＋10分。DB DEFAULTは元資料で未定義。。全属性と参照先の条件が一致して１点。 | 1 | 適用 | [06_t_confirmation](../../spec/DB定義/SQLServer/テーブル/06_t_confirmation.md) | 未評価 | 未採点 | 未評価 | 未採点 | 未記入 | 未記入 |
| DBDEF-SQLSERVER-A73F73FC76C6 | 項目詳細 | AUX-CONF-9 | 項目属性一式 | No=9；論理名=消費済み状態；物理名=consumed；PK=－；タイプ=真偽；長さ=－；初期値=処理:0；説明=DB:bit／NULL不可。初期0、確定保存と同時消費。DB DEFAULTは元資料で未定義。。全属性と参照先の条件が一致して１点。 | 1 | 適用 | [06_t_confirmation](../../spec/DB定義/SQLServer/テーブル/06_t_confirmation.md) | 未評価 | 未採点 | 未評価 | 未採点 | 未記入 | 未記入 |

## 集計一覧

| 評価軸 | 確認行数 | 適用満点 | 獲得点 | 状態 |
| --- | --- | --- | --- | --- |
| 原仕様品質 | 10 | 12 | 未採点 | 未評価 |
| 逆仕様再現 | 10 | 12 | 未採点 | 未評価 |

## 補足説明

テーブル別仕様。表現上のタイプ・長さと、説明欄の実DB型・容量・NULL・条件付き必須を両方確認する。
[採点規則](../00_採点規則.md)。分冊前後の二重加点を禁止する。
