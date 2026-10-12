# Webon汎用照会ベースクラス 稼動店舗管理マスタSelect Baseクラス

## 表紙

| 項目 | 内容 |
| --- | --- |
| 文書名 | 基本設計書 |
| システム名 |  |
| 機能ID | COM-068 |
| 画面名 | Webon汎用照会ベースクラス 稼動店舗管理マスタSelect Baseクラス |
| 会社名 |  |
| 作成日 |  |


## 概要

### 概要説明

Webon汎用照会ベースクラス 稼動店舗管理マスタSelect Baseクラスの入力・表示・要求処理を行う。

| 情報 | 内容 |
| --- | --- |
| 対象種別 | common |
| 開始契機 | 呼出元からの要求 |
| 処理対象 | NAVI.ＵＪ稼動店舗管理マスタ |


## 項目一覧

| No | グループ | 項目名 | 種類 | 入出力 | DB連携項目 | 候補取得元 | 必須 | 形式・桁 | 説明 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |

項目定義数：0項目。表示順と反復行の定義数を区別する。


## イベント仕様

### SelectOperationBranchMstBase

#### 処理概要

Webon汎用照会ベースクラス 稼動店舗管理マスタSelect Baseクラスで「SelectOperationBranchMstBase」の要求を受け付ける。入力・確認・データ操作・応答の順と、条件が成立しない場合の処理を以下に示す。

#### 処理手順

1. 関連情報を取得・設定する（処理2：詳細仕様参照）。

### selectOperationBranchNo

#### 処理概要

Webon汎用照会ベースクラス 稼動店舗管理マスタSelect Baseクラスで「selectOperationBranchNo」の要求を受け付ける。入力・確認・データ操作・応答の順と、条件が成立しない場合の処理を以下に示す。

#### 処理手順

1. 関連情報を取得・設定する（処理6：詳細仕様参照）。

2. 関連情報を取得・設定する（処理7：詳細仕様参照）。

3. 関連情報を取得・設定する（処理8：詳細仕様参照）。

4. 関連情報を取得・設定する（処理9：詳細仕様参照）。

5. 通常処理と例外時の処理を区別して実行する。例外処理は対応する例外が発生した場合に限る。

5.1. 通常処理：関連情報を取得・設定する（処理10：詳細仕様参照）。

5-例外1. 例外条件「SQLException e」に該当した場合に次の手順を行う。型名は原本の表記。

5-例外1.1. 例外発生時：処理の異常を通知し、この経路を終了する。この経路の後続手順は実行しない。

6. 「getList()  が異なる  未設定」に該当するか確認する。成立時と不成立時の手順を分けて行う。

6.1. 条件成立時：成立の結果を返す。この経路の後続手順は実行しない。

6-別.1. 条件不成立時：不成立の結果を返す。この経路の後続手順は実行しない。

#### DB操作の詳細

#### DB操作 SQL-694864CAA608

| 情報 | 内容 |
| --- | --- |
| 操作ID | SQL-694864CAA608 |
| 対象テーブル | NAVI.ＵＪ稼動店舗管理マスタ |
| 操作 | 参照 |
| 処理説明 | 対象テーブルの対象データを読み取る。設定項目・対象条件・確定取消は以下の定義に従う。 |
| 設定項目 | 当該SQL式の列指定・実行時引数を使用する。組立式と原本のパラメーター設定を参照。 |
| 対象条件 | WHERE句による限定はこのSQL式にない。呼出条件・動的付加条件は原本を参照する。 |
| 確定・取消 | 呼出側または接続の設定に従う。当該メソッド単独でのコミット・ロールバック指定はない。 |
| 原本 | n2framework/WEB-INF/src/webon/base/SelectOperationBranchMstBase.java:41 / selectOperationBranchNo@41 |

#### 結果・例外時の扱い

| 到達条件 | 結果 |
| --- | --- |
| 条件11を満たす（原本条件は補足説明を参照） | 処理の異常を通知し、この経路を終了する |
| getList()  が異なる  未設定 | 成立の結果を返す |
| NOT (getList()  が異なる  未設定) | 不成立の結果を返す |

### selectByBrno

#### 処理概要

Webon汎用照会ベースクラス 稼動店舗管理マスタSelect Baseクラスで「selectByBrno」の要求を受け付ける。入力・確認・データ操作・応答の順と、条件が成立しない場合の処理を以下に示す。

#### 処理手順

1. 関連情報を取得・設定する（処理10：詳細仕様参照）。

2. 関連情報を取得・設定する（処理11：詳細仕様参照）。

3. 関連情報を取得・設定する（処理12：詳細仕様参照）。

4. 関連情報を取得・設定する（処理13：詳細仕様参照）。

5. 関連情報を取得・設定する（処理14：詳細仕様参照）。

6. 関連情報を取得・設定する（処理15：詳細仕様参照）。

7. 関連情報を取得・設定する（処理16：詳細仕様参照）。

8. 関連情報を取得・設定する（処理17：詳細仕様参照）。

9. 通常処理と例外時の処理を区別して実行する。例外処理は対応する例外が発生した場合に限る。

9.1. 通常処理：関連情報を取得・設定する（処理18：詳細仕様参照）。

9-例外1. 例外条件「SQLException e」に該当した場合に次の手順を行う。型名は原本の表記。

9-例外1.1. 例外発生時：処理の異常を通知し、この経路を終了する。この経路の後続手順は実行しない。

10. 「getList()  が異なる  未設定」に該当するか確認する。成立時と不成立時の手順を分けて行う。

10.1. 条件成立時：成立の結果を返す。この経路の後続手順は実行しない。

10-別.1. 条件不成立時：不成立の結果を返す。この経路の後続手順は実行しない。

#### DB操作の詳細

#### DB操作 SQL-9782CA7464D4

| 情報 | 内容 |
| --- | --- |
| 操作ID | SQL-9782CA7464D4 |
| 対象テーブル | NAVI.ＵＪ稼動店舗管理マスタ |
| 操作 | 参照 |
| 処理説明 | 対象テーブルの対象データを読み取る。設定項目・対象条件・確定取消は以下の定義に従う。 |
| 設定項目 | 当該SQL式の列指定・実行時引数を使用する。組立式と原本のパラメーター設定を参照。 |
| 対象条件 | 抽出・更新対象条件：店番=〈brno〉 |
| 確定・取消 | 呼出側または接続の設定に従う。当該メソッド単独でのコミット・ロールバック指定はない。 |
| 原本 | n2framework/WEB-INF/src/webon/base/SelectOperationBranchMstBase.java:69 / selectByBrno@69 |

#### 結果・例外時の扱い

| 到達条件 | 結果 |
| --- | --- |
| 条件19を満たす（原本条件は補足説明を参照） | 処理の異常を通知し、この経路を終了する |
| getList()  が異なる  未設定 | 成立の結果を返す |
| NOT (getList()  が異なる  未設定) | 不成立の結果を返す |

### selectNotActiveByBrno

#### 処理概要

Webon汎用照会ベースクラス 稼動店舗管理マスタSelect Baseクラスで「selectNotActiveByBrno」の要求を受け付ける。入力・確認・データ操作・応答の順と、条件が成立しない場合の処理を以下に示す。

#### 処理手順

1. 関連情報を取得・設定する（処理11：詳細仕様参照）。

2. 関連情報を取得・設定する（処理12：詳細仕様参照）。

3. 関連情報を取得・設定する（処理13：詳細仕様参照）。

4. 関連情報を取得・設定する（処理14：詳細仕様参照）。

5. 関連情報を取得・設定する（処理15：詳細仕様参照）。

6. 関連情報を取得・設定する（処理16：詳細仕様参照）。

7. 関連情報を取得・設定する（処理17：詳細仕様参照）。

8. 関連情報を取得・設定する（処理18：詳細仕様参照）。

9. 関連情報を取得・設定する（処理19：詳細仕様参照）。

10. 通常処理と例外時の処理を区別して実行する。例外処理は対応する例外が発生した場合に限る。

10.1. 通常処理：関連情報を取得・設定する（処理20：詳細仕様参照）。

10-例外1. 例外条件「SQLException e」に該当した場合に次の手順を行う。型名は原本の表記。

10-例外1.1. 例外発生時：処理の異常を通知し、この経路を終了する。この経路の後続手順は実行しない。

11. 「getList()  が異なる  未設定」に該当するか確認する。成立時と不成立時の手順を分けて行う。

11.1. 条件成立時：成立の結果を返す。この経路の後続手順は実行しない。

11-別.1. 条件不成立時：不成立の結果を返す。この経路の後続手順は実行しない。

#### DB操作の詳細

#### DB操作 SQL-35487658430A

| 情報 | 内容 |
| --- | --- |
| 操作ID | SQL-35487658430A |
| 対象テーブル | NAVI.ＵＪ稼動店舗管理マスタ |
| 操作 | 参照 |
| 処理説明 | 対象テーブルの対象データを読み取る。設定項目・対象条件・確定取消は以下の定義に従う。 |
| 設定項目 | 当該SQL式の列指定・実行時引数を使用する。組立式と原本のパラメーター設定を参照。 |
| 対象条件 | 抽出・更新対象条件：店番=〈brno〉 AND 取引可能フラグ='1' |
| 確定・取消 | 呼出側または接続の設定に従う。当該メソッド単独でのコミット・ロールバック指定はない。 |
| 原本 | n2framework/WEB-INF/src/webon/base/SelectOperationBranchMstBase.java:100 / selectNotActiveByBrno@100 |

#### 結果・例外時の扱い

| 到達条件 | 結果 |
| --- | --- |
| 条件21を満たす（原本条件は補足説明を参照） | 処理の異常を通知し、この経路を終了する |
| getList()  が異なる  未設定 | 成立の結果を返す |
| NOT (getList()  が異なる  未設定) | 不成立の結果を返す |

### DB関連処理


## 補足説明

### 適用条件

各仮定のQA番号を確認する。静的に確認できた操作・条件を適用する。

### 処理・条件の原本対応

文書内の条件番号・処理番号は次の原本表記に対応する。完全な業務用語への置換を行っていない箇所はQA・reportで確認する。

| イベント | 参照番号 | 原本条件・処理 |
| --- | --- | --- |
| SelectOperationBranchMstBase | 処理1 | super(con) |
| SelectOperationBranchMstBase | 処理2 | super(con) |
| selectOperationBranchNo | 処理1 | execute(sb.toString()) |
| selectOperationBranchNo | 処理2 | sb.append(" ORDER BY " + DBKEY_BRANGHNO) |
| selectOperationBranchNo | 処理3 | sb.append(" FROM " + dbname) |
| selectOperationBranchNo | 処理4 | sb.append("SELECT *") |
| selectOperationBranchNo | 処理5 | StringBuffer sb = new StringBuffer() |
| selectOperationBranchNo | 処理6 | StringBuffer sb = new StringBuffer() |
| selectOperationBranchNo | 処理7 | sb.append("SELECT *") |
| selectOperationBranchNo | 処理8 | sb.append(" FROM " + dbname) |
| selectOperationBranchNo | 処理9 | sb.append(" ORDER BY " + DBKEY_BRANGHNO) |
| selectOperationBranchNo | 処理10 | execute(sb.toString()) |
| selectOperationBranchNo | 条件11 | SQLException e |
| selectByBrno | 処理1 | execute(sb.toString()) |
| selectByBrno | 処理2 | sb.append(" WHERE ").append(DBKEY_BRANGHNO).append("=").append(brno) |
| selectByBrno | 処理3 | sb.append(" FROM ").append(dbname) |
| selectByBrno | 処理4 | sb.append(",").append(DBKEY_ACTIVEFLAG) |
| selectByBrno | 処理5 | sb.append(",").append(DBKEY_ACCESSPOINT) |
| selectByBrno | 処理6 | sb.append(",").append(DBKEY_TRADEBRCODE) |
| selectByBrno | 処理7 | sb.append(" ").append(DBKEY_BRANGHNO) |
| selectByBrno | 処理8 | sb.append("SELECT ") |
| selectByBrno | 処理9 | StringBuffer sb = new StringBuffer() |
| selectByBrno | 処理10 | StringBuffer sb = new StringBuffer() |
| selectByBrno | 処理11 | sb.append("SELECT ") |
| selectByBrno | 処理12 | sb.append(" ").append(DBKEY_BRANGHNO) |
| selectByBrno | 処理13 | sb.append(",").append(DBKEY_TRADEBRCODE) |
| selectByBrno | 処理14 | sb.append(",").append(DBKEY_ACCESSPOINT) |
| selectByBrno | 処理15 | sb.append(",").append(DBKEY_ACTIVEFLAG) |
| selectByBrno | 処理16 | sb.append(" FROM ").append(dbname) |
| selectByBrno | 処理17 | sb.append(" WHERE ").append(DBKEY_BRANGHNO).append("=").append(brno) |
| selectByBrno | 処理18 | execute(sb.toString()) |
| selectByBrno | 条件19 | SQLException e |
| selectNotActiveByBrno | 処理1 | execute(sb.toString()) |
| selectNotActiveByBrno | 処理2 | sb.append(" AND ").append(DBKEY_ACTIVEFLAG).append("=").append("'1'") |
| selectNotActiveByBrno | 処理3 | sb.append(" WHERE ").append(DBKEY_BRANGHNO).append("=").append(brno) |
| selectNotActiveByBrno | 処理4 | sb.append(" FROM ").append(dbname) |
| selectNotActiveByBrno | 処理5 | sb.append(",").append(DBKEY_ACTIVEFLAG) |
| selectNotActiveByBrno | 処理6 | sb.append(",").append(DBKEY_ACCESSPOINT) |
| selectNotActiveByBrno | 処理7 | sb.append(",").append(DBKEY_TRADEBRCODE) |
| selectNotActiveByBrno | 処理8 | sb.append(" ").append(DBKEY_BRANGHNO) |
| selectNotActiveByBrno | 処理9 | sb.append("SELECT ") |
| selectNotActiveByBrno | 処理10 | StringBuffer sb = new StringBuffer() |
| selectNotActiveByBrno | 処理11 | StringBuffer sb = new StringBuffer() |
| selectNotActiveByBrno | 処理12 | sb.append("SELECT ") |
| selectNotActiveByBrno | 処理13 | sb.append(" ").append(DBKEY_BRANGHNO) |
| selectNotActiveByBrno | 処理14 | sb.append(",").append(DBKEY_TRADEBRCODE) |
| selectNotActiveByBrno | 処理15 | sb.append(",").append(DBKEY_ACCESSPOINT) |
| selectNotActiveByBrno | 処理16 | sb.append(",").append(DBKEY_ACTIVEFLAG) |
| selectNotActiveByBrno | 処理17 | sb.append(" FROM ").append(dbname) |
| selectNotActiveByBrno | 処理18 | sb.append(" WHERE ").append(DBKEY_BRANGHNO).append("=").append(brno) |
| selectNotActiveByBrno | 処理19 | sb.append(" AND ").append(DBKEY_ACTIVEFLAG).append("=").append("'1'") |
| selectNotActiveByBrno | 処理20 | execute(sb.toString()) |
| selectNotActiveByBrno | 条件21 | SQLException e |

