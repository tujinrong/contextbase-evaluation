<!-- spec-meta: {"schema":"spec-md/1.0","documentId":"EVAL-DBDEF-SQLSERVER-M_CODE","path":"test-project1/spec-eval/checklists/DBDEF-SQLSERVER-M_CODE.md","version":"7.2","sheets":[{"heading":"概要","kind":"GRID","sheet":"01_概要"},{"heading":"採点一覧","kind":"LIST","sheet":"02_採点一覧","key":["評価ID"]},{"heading":"集計一覧","kind":"LIST","sheet":"03_集計一覧","key":["評価軸"]},{"heading":"補足説明","kind":"GRID","sheet":"04_補足説明"}]} -->
# DBDEF-SQLSERVER-M_CODE 仕様書評価チェックリスト

版7.2／2026-10-12。基準改訂。原仕様品質・逆仕様再現の得点は未評価。

## 概要

対象は[04_m_code](../../spec/DB定義/SQLServer/テーブル/04_m_code.md)。基準7.2、原仕様SHA256=365afcf8a0aca6062b6dccf0134403fcf8b7754f285c8878066baeffb2e5f5d9。満点17点。元の項目評価IDと１項目１点を引継ぎ、テーブルヘッダーは３点。実採点は未実施。

## 採点一覧

| 評価ID | 対象章 | 仕様ID | 観点 | 期待仕様 | 配点 | 適用 | 原仕様 | 原仕様品質判定 | 原仕様品質得点 | 逆仕様再現判定 | 逆仕様再現得点 | 観測値・証拠 | 指摘 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| DBDEF-SQLSERVER-M_CODE-5EF3ECE695BB | テーブルヘッダー | TABLE-HEADER | 表の定義・主キー順序 | 文書ID／版=DBDEF-SQLSERVER-M_CODE／7.2／2026-10-12；論理テーブル名=コード管理マスタ；物理テーブル名=m_code；対象／スキーマ=SQLServer／dbo；用途／項目数=分類内のコード値１件を管理。 14項目。；主キー（順序）=category_id → code_value；共通規則・制約=[総合仕様・制約](../../spec/DB定義/SQLServer/01_DB定義書.md)／[記述・Excel配置規約](../../../docs/テーブル仕様書記述規約.md)；長さ／初期値の基準=長さは業務上限、タイプはDB型・容量。初期値はDB既定値。；項目IDの対応=物理列に対応する既存DB項目IDを維持。メタ情報fieldIdsに対応を記録。；基礎仕様=[論理テーブル仕様](../../spec/基本設計書/03_テーブル仕様書.md)／[項目制約](../../spec/共通/09_項目制約定義.md)；記号=PK・NOT NULL：〇が該当、空欄は非該当。初期値なし・長さ対象外は空欄。条件付き必須は説明参照。 | 3 | 適用 | [04_m_code](../../spec/DB定義/SQLServer/テーブル/04_m_code.md) | 未評価 | 未採点 | 未評価 | 未採点 | 未記入 | 未記入 |
| DBDEF-SQLSERVER-E74762ED156F | 項目詳細 | DB-M_CODE-CATEGORY_ID | 項目属性一式 | No=1；論理名=コード分類；物理名=category_id；PK=〇；NOT NULL=〇；タイプ=varchar(24)；長さ=24；初期値=；説明=コード種別マスタに存在する分類。FK:m_code_category.category_id。 全属性と参照先の条件が一致して１点。 | 1 | 適用 | [04_m_code](../../spec/DB定義/SQLServer/テーブル/04_m_code.md) | 未評価 | 未採点 | 未評価 | 未採点 | 未記入 | 未記入 |
| DBDEF-SQLSERVER-5DC66F8F98AC | 項目詳細 | DB-M_CODE-CODE_VALUE | 項目属性一式 | No=2；論理名=コード値；物理名=code_value；PK=〇；NOT NULL=〇；タイプ=varchar(10)；長さ=10；初期値=；説明=分類で決めた固定桁。先頭ゼロを保持。 全属性と参照先の条件が一致して１点。 | 1 | 適用 | [04_m_code](../../spec/DB定義/SQLServer/テーブル/04_m_code.md) | 未評価 | 未採点 | 未評価 | 未採点 | 未記入 | 未記入 |
| DBDEF-SQLSERVER-89349759F4F9 | 項目詳細 | DB-M_CODE-CODE_NAME | 項目属性一式 | No=3；論理名=コード名称；物理名=code_name；PK=；NOT NULL=〇；タイプ=nvarchar(24)；長さ=12；初期値=；説明=画面に表示する名称。 全属性と参照先の条件が一致して１点。 | 1 | 適用 | [04_m_code](../../spec/DB定義/SQLServer/テーブル/04_m_code.md) | 未評価 | 未採点 | 未評価 | 未採点 | 未記入 | 未記入 |
| DBDEF-SQLSERVER-AD964DE8BF9D | 項目詳細 | DB-M_CODE-DISPLAY_ORDER | 項目属性一式 | No=4；論理名=表示順；物理名=display_order；PK=；NOT NULL=〇；タイプ=int；長さ=10.0；初期値=0；説明=必須・0。同順位はコード値順。 全属性と参照先の条件が一致して１点。 | 1 | 適用 | [04_m_code](../../spec/DB定義/SQLServer/テーブル/04_m_code.md) | 未評価 | 未採点 | 未評価 | 未採点 | 未記入 | 未記入 |
| DBDEF-SQLSERVER-DA834D6D6A2B | 項目詳細 | DB-M_CODE-IS_ACTIVE | 項目属性一式 | No=5；論理名=利用可否；物理名=is_active；PK=；NOT NULL=〇；タイプ=bit；長さ=；初期値=1；説明=必須・利用可。利用不可は新規選択不可。 全属性と参照先の条件が一致して１点。 | 1 | 適用 | [04_m_code](../../spec/DB定義/SQLServer/テーブル/04_m_code.md) | 未評価 | 未採点 | 未評価 | 未採点 | 未記入 | 未記入 |
| DBDEF-SQLSERVER-A2481C763112 | 項目詳細 | DB-M_CODE-VALID_FROM | 項目属性一式 | No=6；論理名=有効開始日；物理名=valid_from；PK=；NOT NULL=〇；タイプ=date；長さ=；初期値=；説明=必須・1900年1月1日。両端を含む。 全属性と参照先の条件が一致して１点。 | 1 | 適用 | [04_m_code](../../spec/DB定義/SQLServer/テーブル/04_m_code.md) | 未評価 | 未採点 | 未評価 | 未採点 | 未記入 | 未記入 |
| DBDEF-SQLSERVER-639A4734CA14 | 項目詳細 | DB-M_CODE-VALID_TO | 項目属性一式 | No=7；論理名=有効終了日；物理名=valid_to；PK=；NOT NULL=；タイプ=date；長さ=；初期値=；説明=空は期限なし。開始日以上。 全属性と参照先の条件が一致して１点。 | 1 | 適用 | [04_m_code](../../spec/DB定義/SQLServer/テーブル/04_m_code.md) | 未評価 | 未採点 | 未評価 | 未採点 | 未記入 | 未記入 |
| DBDEF-SQLSERVER-C5F4FB7F078E | 項目詳細 | DB-M_CODE-IS_PROTECTED | 項目属性一式 | No=8；論理名=保護対象；物理名=is_protected；PK=；NOT NULL=〇；タイプ=bit；長さ=；初期値=；説明=保護値の停止・期間短縮等を禁止。 全属性と参照先の条件が一致して１点。 | 1 | 適用 | [04_m_code](../../spec/DB定義/SQLServer/テーブル/04_m_code.md) | 未評価 | 未採点 | 未評価 | 未採点 | 未記入 | 未記入 |
| DBDEF-SQLSERVER-1F5D38780543 | 項目詳細 | DB-M_CODE-REMARKS | 項目属性一式 | No=9；論理名=備考；物理名=remarks；PK=；NOT NULL=；タイプ=nvarchar(240)；長さ=120；初期値=；説明=意味や使用上の注意。 全属性と参照先の条件が一致して１点。 | 1 | 適用 | [04_m_code](../../spec/DB定義/SQLServer/テーブル/04_m_code.md) | 未評価 | 未採点 | 未評価 | 未採点 | 未記入 | 未記入 |
| DBDEF-SQLSERVER-7803BFACE083 | 項目詳細 | DB-M_CODE-CREATED_AT | 項目属性一式 | No=10；論理名=作成日時；物理名=created_at；PK=；NOT NULL=〇；タイプ=datetimeoffset(7)；長さ=；初期値=；説明=自動。最初の保存日時。変更不可。 全属性と参照先の条件が一致して１点。 | 1 | 適用 | [04_m_code](../../spec/DB定義/SQLServer/テーブル/04_m_code.md) | 未評価 | 未採点 | 未評価 | 未採点 | 未記入 | 未記入 |
| DBDEF-SQLSERVER-E5EF2117B15E | 項目詳細 | DB-M_CODE-CREATED_BY | 項目属性一式 | No=11；論理名=作成者；物理名=created_by；PK=；NOT NULL=〇；タイプ=nvarchar(128)；長さ=64；初期値=；説明=自動。認証された登録者。変更不可。 全属性と参照先の条件が一致して１点。 | 1 | 適用 | [04_m_code](../../spec/DB定義/SQLServer/テーブル/04_m_code.md) | 未評価 | 未採点 | 未評価 | 未採点 | 未記入 | 未記入 |
| DBDEF-SQLSERVER-46A21A86AFB6 | 項目詳細 | DB-M_CODE-UPDATED_AT | 項目属性一式 | No=12；論理名=更新日時；物理名=updated_at；PK=；NOT NULL=〇；タイプ=datetimeoffset(7)；長さ=；初期値=；説明=自動。実変更の保存時点。 全属性と参照先の条件が一致して１点。 | 1 | 適用 | [04_m_code](../../spec/DB定義/SQLServer/テーブル/04_m_code.md) | 未評価 | 未採点 | 未評価 | 未採点 | 未記入 | 未記入 |
| DBDEF-SQLSERVER-71F4D506A8BC | 項目詳細 | DB-M_CODE-UPDATED_BY | 項目属性一式 | No=13；論理名=更新者；物理名=updated_by；PK=；NOT NULL=〇；タイプ=nvarchar(128)；長さ=64；初期値=；説明=自動。認証された変更者。 全属性と参照先の条件が一致して１点。 | 1 | 適用 | [04_m_code](../../spec/DB定義/SQLServer/テーブル/04_m_code.md) | 未評価 | 未採点 | 未評価 | 未採点 | 未記入 | 未記入 |
| DBDEF-SQLSERVER-47F004BA1C1F | 項目詳細 | DB-M_CODE-ROW_VERSION | 項目属性一式 | No=14；論理名=更新管理番号；物理名=row_version；PK=；NOT NULL=〇；タイプ=bigint；長さ=19.0；初期値=1；説明=自動。新規1、実変更ごとに1加算、上限で停止。9223372036854775807到達後の加算を拒否。手動加算bigint。SQL Serverのrowversion型ではない。 全属性と参照先の条件が一致して１点。 | 1 | 適用 | [04_m_code](../../spec/DB定義/SQLServer/テーブル/04_m_code.md) | 未評価 | 未採点 | 未評価 | 未採点 | 未記入 | 未記入 |

## 集計一覧

| 評価軸 | 確認行数 | 適用満点 | 獲得点 | 状態 |
| --- | --- | --- | --- | --- |
| 原仕様品質 | 15 | 17 | 未採点 | 未評価 |
| 逆仕様再現 | 15 | 17 | 未採点 | 未評価 |

## 補足説明

テーブル別仕様。表現上のタイプ・長さと、説明欄の実DB型・容量・NULL・条件付き必須を両方確認する。
[採点規則](../00_採点規則.md)。分冊前後の二重加点を禁止する。
