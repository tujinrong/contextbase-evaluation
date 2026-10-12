<!-- spec-meta: {"schema":"spec-md/1.0","documentId":"EVAL-DBDEF-SQLSERVER-T_OPERATION_LOG","path":"test-project1/spec-eval/checklists/DBDEF-SQLSERVER-T_OPERATION_LOG.md","version":"7.1","sheets":[{"heading":"概要","kind":"GRID","sheet":"01_概要"},{"heading":"採点一覧","kind":"LIST","sheet":"02_採点一覧","key":["評価ID"]},{"heading":"集計一覧","kind":"LIST","sheet":"03_集計一覧","key":["評価軸"]},{"heading":"補足説明","kind":"GRID","sheet":"04_補足説明"}]} -->
# DBDEF-SQLSERVER-T_OPERATION_LOG 仕様書評価チェックリスト

版7.1／2026-10-12。基準改訂。原仕様品質・逆仕様再現の得点は未評価。

## 概要

対象は[05_t_operation_log](../../spec/DB定義/SQLServer/テーブル/05_t_operation_log.md)。基準7.1、原仕様SHA256=564c8e41e48234d80ae95e8e26e83a0d39e39b58a07815663f87622c53137bbd。満点15点。元の項目評価IDと１項目１点を引継ぎ、テーブルヘッダーは３点。実採点は未実施。

## 採点一覧

| 評価ID | 対象章 | 仕様ID | 観点 | 期待仕様 | 配点 | 適用 | 原仕様 | 原仕様品質判定 | 原仕様品質得点 | 逆仕様再現判定 | 逆仕様再現得点 | 観測値・証拠 | 指摘 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| DBDEF-SQLSERVER-T_OPERATION_LOG-5EF3ECE695BB | テーブルヘッダー | TABLE-HEADER | 表の定義・主キー順序 | 文書ID／版=DBDEF-SQLSERVER-T_OPERATION_LOG／7.1／2026-10-12；論理テーブル名=操作履歴；物理テーブル名=t_operation_log；対象／スキーマ=SQLServer／dbo；用途／項目数=確定した変更１件を追記。個人情報の変更前後値は保持しない。 12項目。；主キー（順序）=log_id；共通規則・制約=[総合仕様・制約](../../spec/DB定義/SQLServer/01_DB定義書.md)／[記述・Excel配置規約](../../../docs/テーブル仕様書記述規約.md)；長さ／初期値の基準=長さは業務上限。数字は整数桁.小数桁。初期値はDB既定値。画面の初期値とは別。；項目IDの対応=物理列に対応する既存DB項目IDを維持。メタ情報fieldIdsに対応を記録。；基礎仕様=[論理テーブル仕様](../../spec/基本設計書/03_テーブル仕様書.md)／[項目制約](../../spec/共通/09_項目制約定義.md) | 3 | 適用 | [05_t_operation_log](../../spec/DB定義/SQLServer/テーブル/05_t_operation_log.md) | 未評価 | 未採点 | 未評価 | 未採点 | 未記入 | 未記入 |
| DBDEF-SQLSERVER-22DE7BFF89E6 | 項目詳細 | DB-T_OPERATION_LOG-LOG_ID | 項目属性一式 | No=1；論理名=操作履歴番号；物理名=log_id；PK=〇；タイプ=数字；長さ=19.0；初期値=自動採番；説明=自動。DB:bigint IDENTITY(1,1)／NULL不可。追記記録の識別子。。全属性と参照先の条件が一致して１点。 | 1 | 適用 | [05_t_operation_log](../../spec/DB定義/SQLServer/テーブル/05_t_operation_log.md) | 未評価 | 未採点 | 未評価 | 未採点 | 未記入 | 未記入 |
| DBDEF-SQLSERVER-92AB8B4EF168 | 項目詳細 | DB-T_OPERATION_LOG-TARGET_TABLE | 項目属性一式 | No=2；論理名=対象情報の種類；物理名=target_table；PK=－；タイプ=文字；長さ=21；初期値=指定なし；説明=自動。DB:varchar(21)／NULL不可。学生、クラス、コード分類、コード値のいずれか。。全属性と参照先の条件が一致して１点。 | 1 | 適用 | [05_t_operation_log](../../spec/DB定義/SQLServer/テーブル/05_t_operation_log.md) | 未評価 | 未採点 | 未評価 | 未採点 | 未記入 | 未記入 |
| DBDEF-SQLSERVER-DF1793D26622 | 項目詳細 | DB-T_OPERATION_LOG-TARGET_KEY | 項目属性一式 | No=3；論理名=対象の識別情報；物理名=target_key；PK=－；タイプ=文字；長さ=35；初期値=指定なし；説明=自動。DB:varchar(35)／NULL不可。管理番号または分類と値。氏名等を含めない。。全属性と参照先の条件が一致して１点。 | 1 | 適用 | [05_t_operation_log](../../spec/DB定義/SQLServer/テーブル/05_t_operation_log.md) | 未評価 | 未採点 | 未評価 | 未採点 | 未記入 | 未記入 |
| DBDEF-SQLSERVER-353864807D90 | 項目詳細 | DB-T_OPERATION_LOG-OPERATION_TYPE | 項目属性一式 | No=4；論理名=操作の種類；物理名=operation_type；PK=－；タイプ=文字；長さ=11；初期値=指定なし；説明=自動。DB:varchar(11)／NULL不可。新規・変更・論理削除・停止・再開。。全属性と参照先の条件が一致して１点。 | 1 | 適用 | [05_t_operation_log](../../spec/DB定義/SQLServer/テーブル/05_t_operation_log.md) | 未評価 | 未採点 | 未評価 | 未採点 | 未記入 | 未記入 |
| DBDEF-SQLSERVER-54C9DFFEEFF7 | 項目詳細 | DB-T_OPERATION_LOG-BEFORE_VERSION | 項目属性一式 | No=5；論理名=変更前の更新管理番号；物理名=before_version；PK=－；タイプ=数字；長さ=19.0；初期値=指定なし；説明=新規以外必須。DB:bigint／NULL可。新規は空。。全属性と参照先の条件が一致して１点。 | 1 | 適用 | [05_t_operation_log](../../spec/DB定義/SQLServer/テーブル/05_t_operation_log.md) | 未評価 | 未採点 | 未評価 | 未採点 | 未記入 | 未記入 |
| DBDEF-SQLSERVER-26203075A0F6 | 項目詳細 | DB-T_OPERATION_LOG-AFTER_VERSION | 項目属性一式 | No=6；論理名=変更後の更新管理番号；物理名=after_version；PK=－；タイプ=数字；長さ=19.0；初期値=指定なし；説明=自動。DB:bigint／NULL不可。新規は1、変更は以前の番号＋1。。全属性と参照先の条件が一致して１点。 | 1 | 適用 | [05_t_operation_log](../../spec/DB定義/SQLServer/テーブル/05_t_operation_log.md) | 未評価 | 未採点 | 未評価 | 未採点 | 未記入 | 未記入 |
| DBDEF-SQLSERVER-DC803EE48B43 | 項目詳細 | DB-T_OPERATION_LOG-CHANGED_COLUMNS | 項目属性一式 | No=7；論理名=変更項目一覧；物理名=changed_columns；PK=－；タイプ=配列；長さ=－；初期値=指定なし；説明=自動。DB:nvarchar(max)／NULL不可。変更した項目を記録。入力値自体は複写しない。許可列名のJSON配列、実値は保持しない。ISJSON=1に加え配列型・許可列名・重複なしを保存入口で検査。。全属性と参照先の条件が一致して１点。 | 1 | 適用 | [05_t_operation_log](../../spec/DB定義/SQLServer/テーブル/05_t_operation_log.md) | 未評価 | 未採点 | 未評価 | 未採点 | 未記入 | 未記入 |
| DBDEF-SQLSERVER-1D292C7BE2E9 | 項目詳細 | DB-T_OPERATION_LOG-EXECUTED_BY | 項目属性一式 | No=8；論理名=実行者；物理名=executed_by；PK=－；タイプ=文字；長さ=64；初期値=指定なし；説明=自動。DB:nvarchar(128)／NULL不可。認証された利用者番号。。全属性と参照先の条件が一致して１点。 | 1 | 適用 | [05_t_operation_log](../../spec/DB定義/SQLServer/テーブル/05_t_operation_log.md) | 未評価 | 未採点 | 未評価 | 未採点 | 未記入 | 未記入 |
| DBDEF-SQLSERVER-45F1EF868179 | 項目詳細 | DB-T_OPERATION_LOG-EXECUTED_AT | 項目属性一式 | No=9；論理名=実行日時；物理名=executed_at；PK=－；タイプ=日時；長さ=－；初期値=指定なし；説明=自動。DB:datetimeoffset(7)／NULL不可。対応する保存操作の日時。。全属性と参照先の条件が一致して１点。 | 1 | 適用 | [05_t_operation_log](../../spec/DB定義/SQLServer/テーブル/05_t_operation_log.md) | 未評価 | 未採点 | 未評価 | 未採点 | 未記入 | 未記入 |
| DBDEF-SQLSERVER-6E3285679060 | 項目詳細 | DB-T_OPERATION_LOG-CORRELATION_ID | 項目属性一式 | No=10；論理名=受付番号；物理名=correlation_id；PK=－；タイプ=識別子；長さ=－；初期値=指定なし；説明=自動。DB:uniqueidentifier／NULL不可。障害調査用。同一要求で関連付ける。。全属性と参照先の条件が一致して１点。 | 1 | 適用 | [05_t_operation_log](../../spec/DB定義/SQLServer/テーブル/05_t_operation_log.md) | 未評価 | 未採点 | 未評価 | 未採点 | 未記入 | 未記入 |
| DBDEF-SQLSERVER-988A08300C8C | 項目詳細 | DB-T_OPERATION_LOG-OPERATION_REASON | 項目属性一式 | No=11；論理名=操作・確認理由；物理名=operation_reason；PK=－；タイプ=文字；長さ=60；初期値=指定なし；説明=条件付き。DB:nvarchar(120)／NULL可。削除・終了区分訂正・重複警告続行時は必須。。全属性と参照先の条件が一致して１点。 | 1 | 適用 | [05_t_operation_log](../../spec/DB定義/SQLServer/テーブル/05_t_operation_log.md) | 未評価 | 未採点 | 未評価 | 未採点 | 未記入 | 未記入 |
| DBDEF-SQLSERVER-1062AD119CB2 | 項目詳細 | DB-T_OPERATION_LOG-DUPLICATE_CONFIRMED | 項目属性一式 | No=12；論理名=重複警告の確認有無；物理名=duplicate_confirmed；PK=－；タイプ=真偽；長さ=－；初期値=0；説明=自動。DB:bit／NULL不可。別人確認を経た保存で有。。全属性と参照先の条件が一致して１点。 | 1 | 適用 | [05_t_operation_log](../../spec/DB定義/SQLServer/テーブル/05_t_operation_log.md) | 未評価 | 未採点 | 未評価 | 未採点 | 未記入 | 未記入 |

## 集計一覧

| 評価軸 | 確認行数 | 適用満点 | 獲得点 | 状態 |
| --- | --- | --- | --- | --- |
| 原仕様品質 | 13 | 15 | 未採点 | 未評価 |
| 逆仕様再現 | 13 | 15 | 未採点 | 未評価 |

## 補足説明

テーブル別仕様。表現上のタイプ・長さと、説明欄の実DB型・容量・NULL・条件付き必須を両方確認する。
[採点規則](../00_採点規則.md)。分冊前後の二重加点を禁止する。
