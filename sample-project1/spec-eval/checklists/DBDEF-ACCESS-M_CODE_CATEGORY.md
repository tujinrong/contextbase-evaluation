<!-- spec-meta: {"schema":"spec-md/1.0","documentId":"EVAL-DBDEF-ACCESS-M_CODE_CATEGORY","path":"test-project1/spec-eval/checklists/DBDEF-ACCESS-M_CODE_CATEGORY.md","version":"7.2","sheets":[{"heading":"概要","kind":"GRID","sheet":"01_概要"},{"heading":"採点一覧","kind":"LIST","sheet":"02_採点一覧","key":["評価ID"]},{"heading":"集計一覧","kind":"LIST","sheet":"03_集計一覧","key":["評価軸"]},{"heading":"補足説明","kind":"GRID","sheet":"04_補足説明"}]} -->
# DBDEF-ACCESS-M_CODE_CATEGORY 仕様書評価チェックリスト

版7.2／2026-10-12。基準改訂。原仕様品質・逆仕様再現の得点は未評価。

## 概要

対象は[03_m_code_category](../../spec/DB定義/Access/テーブル/03_m_code_category.md)。基準7.2、原仕様SHA256=28883a6609c1dc0f5079d8e20761eb70e1ac21da7028886642ff17f0c9579efc。満点14点。元の項目評価IDと１項目１点を引継ぎ、テーブルヘッダーは３点。実採点は未実施。

## 採点一覧

| 評価ID | 対象章 | 仕様ID | 観点 | 期待仕様 | 配点 | 適用 | 原仕様 | 原仕様品質判定 | 原仕様品質得点 | 逆仕様再現判定 | 逆仕様再現得点 | 観測値・証拠 | 指摘 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| DBDEF-ACCESS-M_CODE_CATEGORY-5EF3ECE695BB | テーブルヘッダー | TABLE-HEADER | 表の定義・主キー順序 | 文書ID／版=DBDEF-ACCESS-M_CODE_CATEGORY／7.2／2026-10-12；論理テーブル名=コード種別マスタ；物理テーブル名=m_code_category；対象／スキーマ=Access／非適用（ACE）；用途／項目数=コード分類１件の桁数・保守条件を管理。 11項目。；主キー（順序）=category_id；共通規則・制約=[総合仕様・制約](../../spec/DB定義/Access/01_DB定義書.md)／[記述・Excel配置規約](../../../docs/テーブル仕様書記述規約.md)；長さ／初期値の基準=長さは業務上限、タイプはDB型・容量。初期値はDB既定値。；項目IDの対応=物理列に対応する既存DB項目IDを維持。メタ情報fieldIdsに対応を記録。；基礎仕様=[論理テーブル仕様](../../spec/基本設計書/03_テーブル仕様書.md)／[項目制約](../../spec/共通/09_項目制約定義.md)；記号=PK・NOT NULL：〇が該当、空欄は非該当。初期値なし・長さ対象外は空欄。条件付き必須は説明参照。 | 3 | 適用 | [03_m_code_category](../../spec/DB定義/Access/テーブル/03_m_code_category.md) | 未評価 | 未採点 | 未評価 | 未採点 | 未記入 | 未記入 |
| DBDEF-ACCESS-69D052666497 | 項目詳細 | DB-M_CODE_CATEGORY-CATEGORY_ID | 項目属性一式 | No=1；論理名=コード分類；物理名=category_id；PK=〇；NOT NULL=〇；タイプ=TEXT(48)；長さ=24；初期値=；説明=分類の識別情報。登録後変更不可。 全属性と参照先の条件が一致して１点。 | 1 | 適用 | [03_m_code_category](../../spec/DB定義/Access/テーブル/03_m_code_category.md) | 未評価 | 未採点 | 未評価 | 未採点 | 未記入 | 未記入 |
| DBDEF-ACCESS-05D6D60D037C | 項目詳細 | DB-M_CODE_CATEGORY-CATEGORY_NAME | 項目属性一式 | No=2；論理名=コード分類名；物理名=category_name；PK=；NOT NULL=〇；タイプ=TEXT(24)；長さ=12；初期値=；説明=性別・在籍区分等。 全属性と参照先の条件が一致して１点。 | 1 | 適用 | [03_m_code_category](../../spec/DB定義/Access/テーブル/03_m_code_category.md) | 未評価 | 未採点 | 未評価 | 未採点 | 未記入 | 未記入 |
| DBDEF-ACCESS-008ED279432C | 項目詳細 | DB-M_CODE_CATEGORY-CODE_LENGTH | 項目属性一式 | No=3；論理名=コード値の桁数；物理名=code_length；PK=；NOT NULL=〇；タイプ=LONG；長さ=2.0；初期値=；説明=分類内の値を固定桁で管理。 全属性と参照先の条件が一致して１点。 | 1 | 適用 | [03_m_code_category](../../spec/DB定義/Access/テーブル/03_m_code_category.md) | 未評価 | 未採点 | 未評価 | 未採点 | 未記入 | 未記入 |
| DBDEF-ACCESS-F81354CCCE46 | 項目詳細 | DB-M_CODE_CATEGORY-ALLOW_ADD | 項目属性一式 | No=4；論理名=値の追加可否；物理名=allow_add；PK=；NOT NULL=〇；タイプ=YESNO；長さ=；初期値=；説明=通常保守で新しい値を増やせるか。 全属性と参照先の条件が一致して１点。 | 1 | 適用 | [03_m_code_category](../../spec/DB定義/Access/テーブル/03_m_code_category.md) | 未評価 | 未採点 | 未評価 | 未採点 | 未記入 | 未記入 |
| DBDEF-ACCESS-1DE542C3FA24 | 項目詳細 | DB-M_CODE_CATEGORY-IS_ACTIVE | 項目属性一式 | No=5；論理名=分類の利用可否；物理名=is_active；PK=；NOT NULL=〇；タイプ=YESNO；長さ=；初期値=True；説明=必須・利用可。本版の5分類は利用可を維持。 全属性と参照先の条件が一致して１点。 | 1 | 適用 | [03_m_code_category](../../spec/DB定義/Access/テーブル/03_m_code_category.md) | 未評価 | 未採点 | 未評価 | 未採点 | 未記入 | 未記入 |
| DBDEF-ACCESS-2D61D98E9BAF | 項目詳細 | DB-M_CODE_CATEGORY-REMARKS | 項目属性一式 | No=6；論理名=備考；物理名=remarks；PK=；NOT NULL=；タイプ=TEXT(240)；長さ=120；初期値=；説明=分類の用途・保守上の注意。 全属性と参照先の条件が一致して１点。 | 1 | 適用 | [03_m_code_category](../../spec/DB定義/Access/テーブル/03_m_code_category.md) | 未評価 | 未採点 | 未評価 | 未採点 | 未記入 | 未記入 |
| DBDEF-ACCESS-44620E393D4F | 項目詳細 | DB-M_CODE_CATEGORY-CREATED_AT | 項目属性一式 | No=7；論理名=作成日時；物理名=created_at；PK=；NOT NULL=〇；タイプ=DATETIME；長さ=；初期値=；説明=自動。最初の保存日時。変更不可。 全属性と参照先の条件が一致して１点。 | 1 | 適用 | [03_m_code_category](../../spec/DB定義/Access/テーブル/03_m_code_category.md) | 未評価 | 未採点 | 未評価 | 未採点 | 未記入 | 未記入 |
| DBDEF-ACCESS-D70C32540A46 | 項目詳細 | DB-M_CODE_CATEGORY-CREATED_BY | 項目属性一式 | No=8；論理名=作成者；物理名=created_by；PK=；NOT NULL=〇；タイプ=TEXT(128)；長さ=64；初期値=；説明=自動。認証された登録者。変更不可。 全属性と参照先の条件が一致して１点。 | 1 | 適用 | [03_m_code_category](../../spec/DB定義/Access/テーブル/03_m_code_category.md) | 未評価 | 未採点 | 未評価 | 未採点 | 未記入 | 未記入 |
| DBDEF-ACCESS-EC7A2D51DD78 | 項目詳細 | DB-M_CODE_CATEGORY-UPDATED_AT | 項目属性一式 | No=9；論理名=更新日時；物理名=updated_at；PK=；NOT NULL=〇；タイプ=DATETIME；長さ=；初期値=；説明=自動。実変更の保存時点。 全属性と参照先の条件が一致して１点。 | 1 | 適用 | [03_m_code_category](../../spec/DB定義/Access/テーブル/03_m_code_category.md) | 未評価 | 未採点 | 未評価 | 未採点 | 未記入 | 未記入 |
| DBDEF-ACCESS-E4F91E1F5736 | 項目詳細 | DB-M_CODE_CATEGORY-UPDATED_BY | 項目属性一式 | No=10；論理名=更新者；物理名=updated_by；PK=；NOT NULL=〇；タイプ=TEXT(128)；長さ=64；初期値=；説明=自動。認証された変更者。 全属性と参照先の条件が一致して１点。 | 1 | 適用 | [03_m_code_category](../../spec/DB定義/Access/テーブル/03_m_code_category.md) | 未評価 | 未採点 | 未評価 | 未採点 | 未記入 | 未記入 |
| DBDEF-ACCESS-5A3FE4BBFDC8 | 項目詳細 | DB-M_CODE_CATEGORY-ROW_VERSION | 項目属性一式 | No=11；論理名=更新管理番号；物理名=row_version；PK=；NOT NULL=〇；タイプ=LONG；長さ=10.0；初期値=1；説明=自動。新規1、実変更ごとに1加算、上限で停止。2147483647到達後の加算を拒否。 全属性と参照先の条件が一致して１点。 | 1 | 適用 | [03_m_code_category](../../spec/DB定義/Access/テーブル/03_m_code_category.md) | 未評価 | 未採点 | 未評価 | 未採点 | 未記入 | 未記入 |

## 集計一覧

| 評価軸 | 確認行数 | 適用満点 | 獲得点 | 状態 |
| --- | --- | --- | --- | --- |
| 原仕様品質 | 12 | 14 | 未採点 | 未評価 |
| 逆仕様再現 | 12 | 14 | 未採点 | 未評価 |

## 補足説明

テーブル別仕様。表現上のタイプ・長さと、説明欄の実DB型・容量・NULL・条件付き必須を両方確認する。
[採点規則](../00_採点規則.md)。分冊前後の二重加点を禁止する。
