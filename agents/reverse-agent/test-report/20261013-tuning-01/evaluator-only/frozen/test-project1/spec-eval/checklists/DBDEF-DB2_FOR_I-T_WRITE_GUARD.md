<!-- spec-meta: {"schema":"spec-md/1.0","documentId":"EVAL-DBDEF-DB2_FOR_I-T_WRITE_GUARD","path":"test-project1/spec-eval/checklists/DBDEF-DB2_FOR_I-T_WRITE_GUARD.md","version":"7.2","sheets":[{"heading":"概要","kind":"GRID","sheet":"01_概要"},{"heading":"採点一覧","kind":"LIST","sheet":"02_採点一覧","key":["評価ID"]},{"heading":"集計一覧","kind":"LIST","sheet":"03_集計一覧","key":["評価軸"]},{"heading":"補足説明","kind":"GRID","sheet":"04_補足説明"}]} -->
# DBDEF-DB2_FOR_I-T_WRITE_GUARD 仕様書評価チェックリスト

版7.2／2026-10-12。基準改訂。原仕様品質・逆仕様再現の得点は未評価。

## 概要

対象は[06_t_write_guard](../../spec/DB定義/Db2_for_i/テーブル/06_t_write_guard.md)。基準7.2、原仕様SHA256=2d841f796745ee14b2e53f488b84dab115c9b71f2c2191d216637ae322ad0cfe。満点5点。元の項目評価IDと１項目１点を引継ぎ、テーブルヘッダーは３点。実採点は未実施。

## 採点一覧

| 評価ID | 対象章 | 仕様ID | 観点 | 期待仕様 | 配点 | 適用 | 原仕様 | 原仕様品質判定 | 原仕様品質得点 | 逆仕様再現判定 | 逆仕様再現得点 | 観測値・証拠 | 指摘 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| DBDEF-DB2_FOR_I-T_WRITE_GUARD-5EF3ECE695BB | テーブルヘッダー | TABLE-HEADER | 表の定義・主キー順序 | 文書ID／版=DBDEF-DB2_FOR_I-T_WRITE_GUARD／7.2／2026-10-12；論理テーブル名=書込み制御情報；物理テーブル名=t_write_guard；対象／スキーマ=Db2_for_i／STUDAPP；用途／項目数=協調処理の同時実行を制御する固定行。 2項目。補助表の論理名は既存物理名・説明に基づく表記補足。；主キー（順序）=guard_id；共通規則・制約=[総合仕様・制約](../../spec/DB定義/Db2_for_i/01_DB定義書.md)／[記述・Excel配置規約](../../../docs/テーブル仕様書記述規約.md)；長さ／初期値の基準=長さは業務上限、タイプはDB型・容量。初期値は処理設定。DB DEFAULTは未定義。；項目IDの対応=物理列に対応する既存DB項目IDを維持。メタ情報fieldIdsに対応を記録。；基礎仕様=[論理テーブル仕様](../../spec/基本設計書/03_テーブル仕様書.md)／[項目制約](../../spec/共通/09_項目制約定義.md)；記号=PK・NOT NULL：〇が該当、空欄は非該当。初期値なし・長さ対象外は空欄。条件付き必須は説明参照。 | 3 | 適用 | [06_t_write_guard](../../spec/DB定義/Db2_for_i/テーブル/06_t_write_guard.md) | 未評価 | 未採点 | 未評価 | 未採点 | 未記入 | 未記入 |
| DBDEF-DB2_FOR_I-6E93B26851A5 | 項目詳細 | AUX-GUARD-01 | 項目属性一式 | No=1；論理名=制御行番号；物理名=guard_id；PK=〇；NOT NULL=〇；タイプ=SMALLINT；長さ=1.0；初期値=処理:1；説明=固定値1。 全属性と参照先の条件が一致して１点。 | 1 | 適用 | [06_t_write_guard](../../spec/DB定義/Db2_for_i/テーブル/06_t_write_guard.md) | 未評価 | 未採点 | 未評価 | 未採点 | 未記入 | 未記入 |
| DBDEF-DB2_FOR_I-CB06D2861CD2 | 項目詳細 | AUX-GUARD-02 | 項目属性一式 | No=2；論理名=ロック状態；物理名=lock_bit；PK=；NOT NULL=〇；タイプ=SMALLINT；長さ=；初期値=処理:0；説明=初期0、全協調更新・必要な検索で制御行を取得。 全属性と参照先の条件が一致して１点。 | 1 | 適用 | [06_t_write_guard](../../spec/DB定義/Db2_for_i/テーブル/06_t_write_guard.md) | 未評価 | 未採点 | 未評価 | 未採点 | 未記入 | 未記入 |

## 集計一覧

| 評価軸 | 確認行数 | 適用満点 | 獲得点 | 状態 |
| --- | --- | --- | --- | --- |
| 原仕様品質 | 3 | 5 | 未採点 | 未評価 |
| 逆仕様再現 | 3 | 5 | 未採点 | 未評価 |

## 補足説明

テーブル別仕様。表現上のタイプ・長さと、説明欄の実DB型・容量・NULL・条件付き必須を両方確認する。
[採点規則](../00_採点規則.md)。分冊前後の二重加点を禁止する。
