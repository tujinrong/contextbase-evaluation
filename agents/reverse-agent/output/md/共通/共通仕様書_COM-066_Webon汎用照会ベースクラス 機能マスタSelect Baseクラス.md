# Webon汎用照会ベースクラス 機能マスタSelect Baseクラス

## 表紙

| 項目 | 内容 |
| --- | --- |
| 文書名 | 基本設計書 |
| システム名 |  |
| 機能ID | COM-066 |
| 画面名 | Webon汎用照会ベースクラス 機能マスタSelect Baseクラス |
| 会社名 |  |
| 作成日 |  |


## 概要

### 概要説明

Webon汎用照会ベースクラス 機能マスタSelect Baseクラスの入力・表示・要求処理を行う。

| 情報 | 内容 |
| --- | --- |
| 対象種別 | common |
| 開始契機 | 呼出元からの要求 |
| 処理対象 | NAVI.ＵＪ機能マスタ、NAVI.ＵＭ機能マスタ |


## 項目一覧

| No | グループ | 項目名 | 種類 | 入出力 | DB連携項目 | 候補取得元 | 必須 | 形式・桁 | 説明 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |

項目定義数：0項目。表示順と反復行の定義数を区別する。


## イベント仕様

### SelectFunctionMasterBase

#### 処理概要

Webon汎用照会ベースクラス 機能マスタSelect Baseクラスで「SelectFunctionMasterBase」の要求を受け付ける。入力・確認・データ操作・応答の順と、条件が成立しない場合の処理を以下に示す。

#### 処理手順

1. 関連情報を取得・設定する（処理2：詳細仕様参照）。

### selectValueByFunctionIdAndKey

#### 処理概要

Webon汎用照会ベースクラス 機能マスタSelect Baseクラスで「selectValueByFunctionIdAndKey」の要求を受け付ける。入力・確認・データ操作・応答の順と、条件が成立しない場合の処理を以下に示す。

#### 処理手順

1. 通常処理と例外時の処理を区別して実行する。例外処理は対応する例外が発生した場合に限る。

1.1. 通常処理：関連情報を取得・設定する（処理3：詳細仕様参照）。

1.2. 通常処理：「select 値 from NAVI.ＵＭ機能マスタ 」を設定する。

1.3. 通常処理：「where 機能名='」を設定する。

1.4. 通常処理：「and キー名='」を設定する。

1.5. 通常処理：関連情報を取得・設定する（処理4：詳細仕様参照）。

1-例外1. 例外条件「SQLException e」に該当した場合に次の手順を行う。型名は原本の表記。

1-例外1.1. 例外発生時：処理の異常を通知し、この経路を終了する。この経路の後続手順は実行しない。

2. 「getList()  が異なる  未設定」に該当するか確認する。成立時と不成立時の手順を分けて行う。

2.1. 条件成立時：成立の結果を返す。この経路の後続手順は実行しない。

2-別.1. 条件不成立時：不成立の結果を返す。この経路の後続手順は実行しない。

#### DB操作の詳細

#### DB操作 SQL-D1BA242EB73F

| 情報 | 内容 |
| --- | --- |
| 操作ID | SQL-D1BA242EB73F |
| 対象テーブル | NAVI.ＵＭ機能マスタ |
| 操作 | 参照 |
| 処理説明 | 対象テーブルの対象データを読み取る。設定項目・対象条件・確定取消は以下の定義に従う。 |
| 設定項目 | 当該SQL式の列指定・実行時引数を使用する。組立式と原本のパラメーター設定を参照。 |
| 対象条件 | 抽出・更新対象条件：機能名='〈functionId〉'and キー名='〈key〉' |
| 確定・取消 | 呼出側または接続の設定に従う。当該メソッド単独でのコミット・ロールバック指定はない。 |
| 原本 | n2framework/WEB-INF/src/webon/base/SelectFunctionMasterBase.java:39 / selectValueByFunctionIdAndKey@39 |

#### 結果・例外時の扱い

| 到達条件 | 結果 |
| --- | --- |
| 条件5を満たす（原本条件は補足説明を参照） | 処理の異常を通知し、この経路を終了する |
| getList()  が異なる  未設定 | 成立の結果を返す |
| NOT (getList()  が異なる  未設定) | 不成立の結果を返す |

### selectByFunctionId

#### 処理概要

Webon汎用照会ベースクラス 機能マスタSelect Baseクラスで「selectByFunctionId」の要求を受け付ける。入力・確認・データ操作・応答の順と、条件が成立しない場合の処理を以下に示す。

#### 処理手順

1. 通常処理と例外時の処理を区別して実行する。例外処理は対応する例外が発生した場合に限る。

1.1. 通常処理：関連情報を取得・設定する（処理3：詳細仕様参照）。

1.2. 通常処理：「select * from NAVI.ＵＪ機能マスタ 」を設定する。

1.3. 通常処理：「where 機能名='」を設定する。

1.4. 通常処理：関連情報を取得・設定する（処理4：詳細仕様参照）。

1-例外1. 例外条件「SQLException e」に該当した場合に次の手順を行う。型名は原本の表記。

1-例外1.1. 例外発生時：処理の異常を通知し、この経路を終了する。この経路の後続手順は実行しない。

2. 「getList()  が異なる  未設定」に該当するか確認する。成立時と不成立時の手順を分けて行う。

2.1. 条件成立時：成立の結果を返す。この経路の後続手順は実行しない。

2-別.1. 条件不成立時：不成立の結果を返す。この経路の後続手順は実行しない。

#### DB操作の詳細

#### DB操作 SQL-BF61EBA506D0

| 情報 | 内容 |
| --- | --- |
| 操作ID | SQL-BF61EBA506D0 |
| 対象テーブル | NAVI.ＵＪ機能マスタ |
| 操作 | 参照 |
| 処理説明 | 対象テーブルの対象データを読み取る。設定項目・対象条件・確定取消は以下の定義に従う。 |
| 設定項目 | 当該SQL式の列指定・実行時引数を使用する。組立式と原本のパラメーター設定を参照。 |
| 対象条件 | 抽出・更新対象条件：機能名='〈functionId〉' |
| 確定・取消 | 呼出側または接続の設定に従う。当該メソッド単独でのコミット・ロールバック指定はない。 |
| 原本 | n2framework/WEB-INF/src/webon/base/SelectFunctionMasterBase.java:60 / selectByFunctionId@60 |

#### 結果・例外時の扱い

| 到達条件 | 結果 |
| --- | --- |
| 条件5を満たす（原本条件は補足説明を参照） | 処理の異常を通知し、この経路を終了する |
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
| SelectFunctionMasterBase | 処理1 | super(connection) |
| SelectFunctionMasterBase | 処理2 | super(connection) |
| selectValueByFunctionIdAndKey | 処理1 | execute(sb.toString()) |
| selectValueByFunctionIdAndKey | 処理2 | StringBuffer sb = new StringBuffer() |
| selectValueByFunctionIdAndKey | 処理3 | StringBuffer sb = new StringBuffer() |
| selectValueByFunctionIdAndKey | 処理4 | execute(sb.toString()) |
| selectValueByFunctionIdAndKey | 条件5 | SQLException e |
| selectByFunctionId | 処理1 | execute(sb.toString()) |
| selectByFunctionId | 処理2 | StringBuffer sb = new StringBuffer() |
| selectByFunctionId | 処理3 | StringBuffer sb = new StringBuffer() |
| selectByFunctionId | 処理4 | execute(sb.toString()) |
| selectByFunctionId | 条件5 | SQLException e |

