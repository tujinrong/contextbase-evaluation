# Webon汎用照会ベースクラス パス管理ステータス Select Baseクラス

## 表紙

| 項目 | 内容 |
| --- | --- |
| 文書名 | 基本設計書 |
| システム名 |  |
| 機能ID | COM-070 |
| 画面名 | Webon汎用照会ベースクラス パス管理ステータス Select Baseクラス |
| 会社名 |  |
| 作成日 |  |


## 概要

### 概要説明

Webon汎用照会ベースクラス パス管理ステータス Select Baseクラスの入力・表示・要求処理を行う。

| 情報 | 内容 |
| --- | --- |
| 対象種別 | common |
| 開始契機 | 呼出元からの要求 |
| 処理対象 | NAVI.ＵＳパス管理ステータス |


## 項目一覧

| No | グループ | 項目名 | 種類 | 入出力 | DB連携項目 | 候補取得元 | 必須 | 形式・桁 | 説明 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |

項目定義数：0項目。表示順と反復行の定義数を区別する。


## イベント仕様

### SelectPathMngStatBase

#### 処理概要

Webon汎用照会ベースクラス パス管理ステータス Select Baseクラスで「SelectPathMngStatBase」の要求を受け付ける。入力・確認・データ操作・応答の順と、条件が成立しない場合の処理を以下に示す。

#### 処理手順

1. 関連情報を取得・設定する（処理2：詳細仕様参照）。

### selectPathNoForUp

#### 処理概要

Webon汎用照会ベースクラス パス管理ステータス Select Baseクラスで「selectPathNoForUp」の要求を受け付ける。入力・確認・データ操作・応答の順と、条件が成立しない場合の処理を以下に示す。

#### 処理手順

1. 関連情報を取得・設定する（処理9：詳細仕様参照）。

2. 関連情報を取得・設定する（処理10：詳細仕様参照）。

3. 関連情報を取得・設定する（処理11：詳細仕様参照）。

4. 関連情報を取得・設定する（処理12：詳細仕様参照）。

5. 関連情報を取得・設定する（処理13：詳細仕様参照）。

6. 関連情報を取得・設定する（処理14：詳細仕様参照）。

7. 関連情報を取得・設定する（処理15：詳細仕様参照）。

8. 通常処理と例外時の処理を区別して実行する。例外処理は対応する例外が発生した場合に限る。

8.1. 通常処理：関連情報を取得・設定する（処理16：詳細仕様参照）。

8-例外1. 例外条件「SQLException e」に該当した場合に次の手順を行う。型名は原本の表記。

8-例外1.1. 例外発生時：処理の異常を通知し、この経路を終了する。この経路の後続手順は実行しない。

9. 「getList()  が異なる  未設定」に該当するか確認する。成立時と不成立時の手順を分けて行う。

9.1. 条件成立時：成立の結果を返す。この経路の後続手順は実行しない。

9-別.1. 条件不成立時：不成立の結果を返す。この経路の後続手順は実行しない。

#### DB操作の詳細

#### DB操作 SQL-519634C3F762

| 情報 | 内容 |
| --- | --- |
| 操作ID | SQL-519634C3F762 |
| 対象テーブル | NAVI.ＵＳパス管理ステータス |
| 操作 | 参照 |
| 処理説明 | 対象テーブルの対象データを読み取る。設定項目・対象条件・確定取消は以下の定義に従う。 |
| 設定項目 | 当該SQL式の列指定・実行時引数を使用する。組立式と原本のパラメーター設定を参照。 |
| 対象条件 | 抽出・更新対象条件：接続先='〈ip〉' FOR UPDATE WAIT 10 |
| 確定・取消 | 呼出側または接続の設定に従う。当該メソッド単独でのコミット・ロールバック指定はない。 |
| 原本 | n2framework/WEB-INF/src/webon/base/SelectPathMngStatBase.java:39 / selectPathNoForUp@39 |

#### 結果・例外時の扱い

| 到達条件 | 結果 |
| --- | --- |
| 条件17を満たす（原本条件は補足説明を参照） | 処理の異常を通知し、この経路を終了する |
| getList()  が異なる  未設定 | 成立の結果を返す |
| NOT (getList()  が異なる  未設定) | 不成立の結果を返す |

### checkPathNo

#### 処理概要

Webon汎用照会ベースクラス パス管理ステータス Select Baseクラスで「checkPathNo」の要求を受け付ける。入力・確認・データ操作・応答の順と、条件が成立しない場合の処理を以下に示す。

#### 処理手順

1. 関連情報を取得・設定する（処理8：詳細仕様参照）。

2. 関連情報を取得・設定する（処理9：詳細仕様参照）。

3. 関連情報を取得・設定する（処理10：詳細仕様参照）。

4. 関連情報を取得・設定する（処理11：詳細仕様参照）。

5. 関連情報を取得・設定する（処理12：詳細仕様参照）。

6. 通常処理と例外時の処理を区別して実行する。例外処理は対応する例外が発生した場合に限る。

6.1. 通常処理：関連情報を取得・設定する（処理13：詳細仕様参照）。

6-例外1. 例外条件「SQLException e」に該当した場合に次の手順を行う。型名は原本の表記。

6-例外1.1. 例外発生時：処理の異常を通知し、この経路を終了する。この経路の後続手順は実行しない。

7. 「getList()  が異なる  未設定」に該当するか確認する。成立時と不成立時の手順を分けて行う。

7.1. 条件成立時：「条件14を満たす（原本条件は補足説明を参照）」に該当するか確認する。成立時と不成立時の手順を分けて行う。

7.1.1. 条件成立時：成立の結果を返す。この経路の後続手順は実行しない。

7.1-別.1. 条件不成立時：不成立の結果を返す。この経路の後続手順は実行しない。

7-別.1. 条件不成立時：不成立の結果を返す。この経路の後続手順は実行しない。

#### DB操作の詳細

#### DB操作 SQL-D94B94F30EBB

| 情報 | 内容 |
| --- | --- |
| 操作ID | SQL-D94B94F30EBB |
| 対象テーブル | NAVI.ＵＳパス管理ステータス |
| 操作 | 参照 |
| 処理説明 | 対象テーブルの対象データを読み取る。設定項目・対象条件・確定取消は以下の定義に従う。 |
| 設定項目 | 当該SQL式の列指定・実行時引数を使用する。組立式と原本のパラメーター設定を参照。 |
| 対象条件 | 抽出・更新対象条件：接続先='〈ip〉' |
| 確定・取消 | 呼出側または接続の設定に従う。当該メソッド単独でのコミット・ロールバック指定はない。 |
| 原本 | n2framework/WEB-INF/src/webon/base/SelectPathMngStatBase.java:69 / checkPathNo@69 |

#### 結果・例外時の扱い

| 到達条件 | 結果 |
| --- | --- |
| 条件15を満たす（原本条件は補足説明を参照） | 処理の異常を通知し、この経路を終了する |
| getList()  が異なる  未設定・条件16を満たす（原本条件は補足説明を参照） | 成立の結果を返す |
| getList()  が異なる  未設定・条件17を満たす（原本条件は補足説明を参照） | 不成立の結果を返す |
| NOT (getList()  が異なる  未設定) | 不成立の結果を返す |

### DB関連処理


## 補足説明

### 適用条件

各仮定のQA番号を確認する。静的に確認できた操作・条件を適用する。

### 処理・条件の原本対応

文書内の条件番号・処理番号は次の原本表記に対応する。完全な業務用語への置換を行っていない箇所はQA・reportで確認する。

| イベント | 参照番号 | 原本条件・処理 |
| --- | --- | --- |
| SelectPathMngStatBase | 処理1 | super(connection) |
| SelectPathMngStatBase | 処理2 | super(connection) |
| selectPathNoForUp | 処理1 | execute(sb.toString()) |
| selectPathNoForUp | 処理2 | sb.append(" WAIT ").append("10") |
| selectPathNoForUp | 処理3 | sb.append(" FOR UPDATE" ) |
| selectPathNoForUp | 処理4 | sb.append(" WHERE ").append(DBKEY_ACCESSPOINT).append("='").append(ip).append("'") |
| selectPathNoForUp | 処理5 | sb.append(" FROM ").append(DBNAME) |
| selectPathNoForUp | 処理6 | sb.append(",").append(DBKEY_LIMPATHNUM) |
| selectPathNoForUp | 処理7 | sb.append("SELECT ").append(DBKEY_PATHNUM) |
| selectPathNoForUp | 処理8 | StringBuilder sb = new StringBuilder() |
| selectPathNoForUp | 処理9 | StringBuilder sb = new StringBuilder() |
| selectPathNoForUp | 処理10 | sb.append("SELECT ").append(DBKEY_PATHNUM) |
| selectPathNoForUp | 処理11 | sb.append(",").append(DBKEY_LIMPATHNUM) |
| selectPathNoForUp | 処理12 | sb.append(" FROM ").append(DBNAME) |
| selectPathNoForUp | 処理13 | sb.append(" WHERE ").append(DBKEY_ACCESSPOINT).append("='").append(ip).append("'") |
| selectPathNoForUp | 処理14 | sb.append(" FOR UPDATE" ) |
| selectPathNoForUp | 処理15 | sb.append(" WAIT ").append("10") |
| selectPathNoForUp | 処理16 | execute(sb.toString()) |
| selectPathNoForUp | 条件17 | SQLException e |
| checkPathNo | 条件1 | getList().size()&gt;0 |
| checkPathNo | 処理2 | execute(sb.toString()) |
| checkPathNo | 処理3 | sb.append(" WHERE ").append(DBKEY_ACCESSPOINT).append("='").append(ip).append("'") |
| checkPathNo | 処理4 | sb.append(" FROM ").append(DBNAME) |
| checkPathNo | 処理5 | sb.append(",").append(DBKEY_LIMPATHNUM) |
| checkPathNo | 処理6 | sb.append("SELECT ").append(DBKEY_PATHNUM) |
| checkPathNo | 処理7 | StringBuilder sb = new StringBuilder() |
| checkPathNo | 処理8 | StringBuilder sb = new StringBuilder() |
| checkPathNo | 処理9 | sb.append("SELECT ").append(DBKEY_PATHNUM) |
| checkPathNo | 処理10 | sb.append(",").append(DBKEY_LIMPATHNUM) |
| checkPathNo | 処理11 | sb.append(" FROM ").append(DBNAME) |
| checkPathNo | 処理12 | sb.append(" WHERE ").append(DBKEY_ACCESSPOINT).append("='").append(ip).append("'") |
| checkPathNo | 処理13 | execute(sb.toString()) |
| checkPathNo | 条件14 | getList().size()&gt;0 |
| checkPathNo | 条件15 | SQLException e |
| checkPathNo | 条件16 | getList().size()&gt;0 |
| checkPathNo | 条件17 | NOT (getList().size()&gt;0) |

