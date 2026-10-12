<!-- spec-meta: {"schema":"spec-md/1.0","documentId":"EVAL-DBDEF-DB2_FOR_I-M_CLASS","path":"test-project1/spec-eval/checklists/DBDEF-DB2_FOR_I-M_CLASS.md","version":"7.2","sheets":[{"heading":"概要","kind":"GRID","sheet":"01_概要"},{"heading":"採点一覧","kind":"LIST","sheet":"02_採点一覧","key":["評価ID"]},{"heading":"集計一覧","kind":"LIST","sheet":"03_集計一覧","key":["評価軸"]},{"heading":"補足説明","kind":"GRID","sheet":"04_補足説明"}]} -->
# DBDEF-DB2_FOR_I-M_CLASS 仕様書評価チェックリスト

版7.2／2026-10-12。基準改訂。原仕様品質・逆仕様再現の得点は未評価。

## 概要

対象は[02_m_class](../../spec/DB定義/Db2_for_i/テーブル/02_m_class.md)。基準7.2、原仕様SHA256=28a4f10b4b3d133bfffd1685384eccc852b50a61c9b50e4718984ed7f77a7c23。満点20点。元の項目評価IDと１項目１点を引継ぎ、テーブルヘッダーは３点。実採点は未実施。

## 採点一覧

| 評価ID | 対象章 | 仕様ID | 観点 | 期待仕様 | 配点 | 適用 | 原仕様 | 原仕様品質判定 | 原仕様品質得点 | 逆仕様再現判定 | 逆仕様再現得点 | 観測値・証拠 | 指摘 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| DBDEF-DB2_FOR_I-M_CLASS-5EF3ECE695BB | テーブルヘッダー | TABLE-HEADER | 表の定義・主キー順序 | 文書ID／版=DBDEF-DB2_FOR_I-M_CLASS／7.2／2026-10-12；論理テーブル名=クラスマスタ；物理テーブル名=m_class；対象／スキーマ=Db2_for_i／STUDAPP；用途／項目数=学校年度内のクラス１件を管理。 17項目。；主キー（順序）=class_id；共通規則・制約=[総合仕様・制約](../../spec/DB定義/Db2_for_i/01_DB定義書.md)／[記述・Excel配置規約](../../../docs/テーブル仕様書記述規約.md)；長さ／初期値の基準=長さは業務上限、タイプはDB型・容量。初期値はDB既定値。；項目IDの対応=物理列に対応する既存DB項目IDを維持。メタ情報fieldIdsに対応を記録。；基礎仕様=[論理テーブル仕様](../../spec/基本設計書/03_テーブル仕様書.md)／[項目制約](../../spec/共通/09_項目制約定義.md)；記号=PK・NOT NULL：〇が該当、空欄は非該当。初期値なし・長さ対象外は空欄。条件付き必須は説明参照。 | 3 | 適用 | [02_m_class](../../spec/DB定義/Db2_for_i/テーブル/02_m_class.md) | 未評価 | 未採点 | 未評価 | 未採点 | 未記入 | 未記入 |
| DBDEF-DB2_FOR_I-10CA1C540C75 | 項目詳細 | DB-M_CLASS-CLASS_ID | 項目属性一式 | No=1；論理名=クラス管理番号；物理名=class_id；PK=〇；NOT NULL=〇；タイプ=BIGINT；長さ=19.0；初期値=自動採番；説明=GENERATED ALWAYS AS IDENTITY。内部識別子、変更不可。 全属性と参照先の条件が一致して１点。 | 1 | 適用 | [02_m_class](../../spec/DB定義/Db2_for_i/テーブル/02_m_class.md) | 未評価 | 未採点 | 未評価 | 未採点 | 未記入 | 未記入 |
| DBDEF-DB2_FOR_I-0A96C8452548 | 項目詳細 | DB-M_CLASS-SCHOOL_YEAR | 項目属性一式 | No=2；論理名=学校年度；物理名=school_year；PK=；NOT NULL=〇；タイプ=SMALLINT；長さ=4.0；初期値=；説明=4月1日～翌年3月31日、登録後変更不可。 全属性と参照先の条件が一致して１点。 | 1 | 適用 | [02_m_class](../../spec/DB定義/Db2_for_i/テーブル/02_m_class.md) | 未評価 | 未採点 | 未評価 | 未採点 | 未記入 | 未記入 |
| DBDEF-DB2_FOR_I-F33B237D1B35 | 項目詳細 | DB-M_CLASS-GRADE_CATEGORY | 項目属性一式 | No=3；論理名=学年のコード分類；物理名=grade_category；PK=；NOT NULL=〇；タイプ=VARCHAR(24) CCSID1208；長さ=24；初期値=；説明=自動固定。学年の分類。固定値GRADE。 全属性と参照先の条件が一致して１点。 | 1 | 適用 | [02_m_class](../../spec/DB定義/Db2_for_i/テーブル/02_m_class.md) | 未評価 | 未採点 | 未評価 | 未採点 | 未記入 | 未記入 |
| DBDEF-DB2_FOR_I-64BED61D5794 | 項目詳細 | DB-M_CLASS-GRADE_CODE | 項目属性一式 | No=4；論理名=学年；物理名=grade_code；PK=；NOT NULL=〇；タイプ=VARCHAR(2) CCSID1208；長さ=2；初期値=；説明=必須・学年なし。参照学生がいる場合の意味変更を禁止。FK:(grade_category,grade_code)→m_code(category_id,code_value)。 全属性と参照先の条件が一致して１点。 | 1 | 適用 | [02_m_class](../../spec/DB定義/Db2_for_i/テーブル/02_m_class.md) | 未評価 | 未採点 | 未評価 | 未採点 | 未記入 | 未記入 |
| DBDEF-DB2_FOR_I-2925EE0FE407 | 項目詳細 | DB-M_CLASS-CLASS_CODE | 項目属性一式 | No=5；論理名=クラスコード；物理名=class_code；PK=；NOT NULL=〇；タイプ=VARCHAR(9) CCSID1208；長さ=9；初期値=；説明=英数字・ハイフン、先頭英数字。年度内で一意、変更不可。 全属性と参照先の条件が一致して１点。 | 1 | 適用 | [02_m_class](../../spec/DB定義/Db2_for_i/テーブル/02_m_class.md) | 未評価 | 未採点 | 未評価 | 未採点 | 未記入 | 未記入 |
| DBDEF-DB2_FOR_I-903B88E5632D | 項目詳細 | DB-M_CLASS-CLASS_NAME | 項目属性一式 | No=6；論理名=クラス名；物理名=class_name；PK=；NOT NULL=〇；タイプ=VARGRAPHIC(36) CCSID1200；長さ=18；初期値=；説明=顧客向けの名称。 全属性と参照先の条件が一致して１点。 | 1 | 適用 | [02_m_class](../../spec/DB定義/Db2_for_i/テーブル/02_m_class.md) | 未評価 | 未採点 | 未評価 | 未採点 | 未記入 | 未記入 |
| DBDEF-DB2_FOR_I-AB4CBECD9A62 | 項目詳細 | DB-M_CLASS-VALID_FROM | 項目属性一式 | No=7；論理名=利用開始日；物理名=valid_from；PK=；NOT NULL=〇；タイプ=DATE；長さ=；初期値=；説明=必須・年度開始日。学校年度内、終了日以下。 全属性と参照先の条件が一致して１点。 | 1 | 適用 | [02_m_class](../../spec/DB定義/Db2_for_i/テーブル/02_m_class.md) | 未評価 | 未採点 | 未評価 | 未採点 | 未記入 | 未記入 |
| DBDEF-DB2_FOR_I-D20E81ABB5BB | 項目詳細 | DB-M_CLASS-VALID_TO | 項目属性一式 | No=8；論理名=利用終了日；物理名=valid_to；PK=；NOT NULL=〇；タイプ=DATE；長さ=；初期値=；説明=必須・年度終了日。学校年度内。両端を含む。 全属性と参照先の条件が一致して１点。 | 1 | 適用 | [02_m_class](../../spec/DB定義/Db2_for_i/テーブル/02_m_class.md) | 未評価 | 未採点 | 未評価 | 未採点 | 未記入 | 未記入 |
| DBDEF-DB2_FOR_I-002C8FD7E5FE | 項目詳細 | DB-M_CLASS-CAPACITY | 項目属性一式 | No=9；論理名=定員；物理名=capacity；PK=；NOT NULL=；タイプ=INTEGER；長さ=4.0；初期値=；説明=任意・未設定。未設定は制限なし。0人定員は指定しない。 全属性と参照先の条件が一致して１点。 | 1 | 適用 | [02_m_class](../../spec/DB定義/Db2_for_i/テーブル/02_m_class.md) | 未評価 | 未採点 | 未評価 | 未採点 | 未記入 | 未記入 |
| DBDEF-DB2_FOR_I-C894C541F3B8 | 項目詳細 | DB-M_CLASS-DISPLAY_ORDER | 項目属性一式 | No=10；論理名=表示順；物理名=display_order；PK=；NOT NULL=〇；タイプ=INTEGER；長さ=10.0；初期値=0；説明=必須・0。候補表示の順番。 全属性と参照先の条件が一致して１点。 | 1 | 適用 | [02_m_class](../../spec/DB定義/Db2_for_i/テーブル/02_m_class.md) | 未評価 | 未採点 | 未評価 | 未採点 | 未記入 | 未記入 |
| DBDEF-DB2_FOR_I-30B9D6E3653F | 項目詳細 | DB-M_CLASS-IS_ACTIVE | 項目属性一式 | No=11；論理名=利用可否；物理名=is_active；PK=；NOT NULL=〇；タイプ=SMALLINT；長さ=；初期値=1；説明=必須・利用可。停止しても既存参照は残す。 全属性と参照先の条件が一致して１点。 | 1 | 適用 | [02_m_class](../../spec/DB定義/Db2_for_i/テーブル/02_m_class.md) | 未評価 | 未採点 | 未評価 | 未採点 | 未記入 | 未記入 |
| DBDEF-DB2_FOR_I-823FF026A517 | 項目詳細 | DB-M_CLASS-REMARKS | 項目属性一式 | No=12；論理名=備考；物理名=remarks；PK=；NOT NULL=；タイプ=VARGRAPHIC(240) CCSID1200；長さ=120；初期値=；説明=クラス説明。担任の人事管理は対象外。 全属性と参照先の条件が一致して１点。 | 1 | 適用 | [02_m_class](../../spec/DB定義/Db2_for_i/テーブル/02_m_class.md) | 未評価 | 未採点 | 未評価 | 未採点 | 未記入 | 未記入 |
| DBDEF-DB2_FOR_I-2F284D96F733 | 項目詳細 | DB-M_CLASS-CREATED_AT | 項目属性一式 | No=13；論理名=作成日時；物理名=created_at；PK=；NOT NULL=〇；タイプ=TIMESTAMP(6)；長さ=；初期値=；説明=自動。最初の保存日時。変更不可。 全属性と参照先の条件が一致して１点。 | 1 | 適用 | [02_m_class](../../spec/DB定義/Db2_for_i/テーブル/02_m_class.md) | 未評価 | 未採点 | 未評価 | 未採点 | 未記入 | 未記入 |
| DBDEF-DB2_FOR_I-B565DFCC8DE7 | 項目詳細 | DB-M_CLASS-CREATED_BY | 項目属性一式 | No=14；論理名=作成者；物理名=created_by；PK=；NOT NULL=〇；タイプ=VARGRAPHIC(128) CCSID1200；長さ=64；初期値=；説明=自動。認証された登録者。変更不可。 全属性と参照先の条件が一致して１点。 | 1 | 適用 | [02_m_class](../../spec/DB定義/Db2_for_i/テーブル/02_m_class.md) | 未評価 | 未採点 | 未評価 | 未採点 | 未記入 | 未記入 |
| DBDEF-DB2_FOR_I-E5B56430EB9C | 項目詳細 | DB-M_CLASS-UPDATED_AT | 項目属性一式 | No=15；論理名=更新日時；物理名=updated_at；PK=；NOT NULL=〇；タイプ=TIMESTAMP(6)；長さ=；初期値=；説明=自動。実変更の保存時点。 全属性と参照先の条件が一致して１点。 | 1 | 適用 | [02_m_class](../../spec/DB定義/Db2_for_i/テーブル/02_m_class.md) | 未評価 | 未採点 | 未評価 | 未採点 | 未記入 | 未記入 |
| DBDEF-DB2_FOR_I-3206E7D116C3 | 項目詳細 | DB-M_CLASS-UPDATED_BY | 項目属性一式 | No=16；論理名=更新者；物理名=updated_by；PK=；NOT NULL=〇；タイプ=VARGRAPHIC(128) CCSID1200；長さ=64；初期値=；説明=自動。認証された変更者。 全属性と参照先の条件が一致して１点。 | 1 | 適用 | [02_m_class](../../spec/DB定義/Db2_for_i/テーブル/02_m_class.md) | 未評価 | 未採点 | 未評価 | 未採点 | 未記入 | 未記入 |
| DBDEF-DB2_FOR_I-6A10086F0216 | 項目詳細 | DB-M_CLASS-ROW_VERSION | 項目属性一式 | No=17；論理名=更新管理番号；物理名=row_version；PK=；NOT NULL=〇；タイプ=BIGINT；長さ=19.0；初期値=1；説明=自動。新規1、実変更ごとに1加算、上限で停止。9223372036854775807到達後の加算を拒否。 全属性と参照先の条件が一致して１点。 | 1 | 適用 | [02_m_class](../../spec/DB定義/Db2_for_i/テーブル/02_m_class.md) | 未評価 | 未採点 | 未評価 | 未採点 | 未記入 | 未記入 |

## 集計一覧

| 評価軸 | 確認行数 | 適用満点 | 獲得点 | 状態 |
| --- | --- | --- | --- | --- |
| 原仕様品質 | 18 | 20 | 未採点 | 未評価 |
| 逆仕様再現 | 18 | 20 | 未採点 | 未評価 |

## 補足説明

テーブル別仕様。表現上のタイプ・長さと、説明欄の実DB型・容量・NULL・条件付き必須を両方確認する。
[採点規則](../00_採点規則.md)。分冊前後の二重加点を禁止する。
