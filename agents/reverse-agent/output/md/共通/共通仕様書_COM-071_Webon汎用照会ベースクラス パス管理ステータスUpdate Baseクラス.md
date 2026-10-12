# Webon汎用照会ベースクラス パス管理ステータスUpdate Baseクラス

## 表紙

| 項目 | 内容 |
| --- | --- |
| 文書名 | 基本設計書 |
| システム名 |  |
| 機能ID | COM-071 |
| 画面名 | Webon汎用照会ベースクラス パス管理ステータスUpdate Baseクラス |
| 会社名 |  |
| 作成日 |  |


## 概要

### 概要説明

Webon汎用照会ベースクラス パス管理ステータスUpdate Baseクラスの入力・表示・要求処理を行う。

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

### UpdatePathMngStatBase

#### 処理概要

Webon汎用照会ベースクラス パス管理ステータスUpdate Baseクラスで「UpdatePathMngStatBase」の要求を受け付ける。入力・確認・データ操作・応答の順と、条件が成立しない場合の処理を以下に示す。

#### 処理手順

1. 関連情報を取得・設定する（処理2：詳細仕様参照）。

### updatePathNo

#### 処理概要

Webon汎用照会ベースクラス パス管理ステータスUpdate Baseクラスで「updatePathNo」の要求を受け付ける。入力・確認・データ操作・応答の順と、条件が成立しない場合の処理を以下に示す。

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

#### DB操作の詳細

#### DB操作 SQL-F97C0AE27E69

| 情報 | 内容 |
| --- | --- |
| 操作ID | SQL-F97C0AE27E69 |
| 対象テーブル | NAVI.ＵＳパス管理ステータス |
| 操作 | 更新 |
| 処理説明 | 対象テーブルの条件に一致する行を更新する。設定項目・対象条件・確定取消は以下の定義に従う。 |
| 設定項目 | パス使用数 ← 〈pathNum〉／更新日 ← 〈ConvertUtil.dbGetDate()〉／更新時刻 ← 〈ConvertUtil.dbGetTime()〉 |
| 対象条件 | 抽出・更新対象条件：接続先='〈ip〉' |
| 確定・取消 | 呼出側または接続の設定に従う。当該メソッド単独でのコミット・ロールバック指定はない。 |
| 原本 | n2framework/WEB-INF/src/webon/base/UpdatePathMngStatBase.java:41 / updatePathNo@41 |

#### DB操作 SQL-8DA5C44CC841

| 情報 | 内容 |
| --- | --- |
| 操作ID | SQL-8DA5C44CC841 |
| 対象テーブル | NAVI.ＵＳパス管理ステータス |
| 操作 | 更新 |
| 処理説明 | 対象テーブルの条件に一致する行を更新する。設定項目・対象条件・確定取消は以下の定義に従う。 |
| 設定項目 | パス使用数 ← 〈pathNum〉／制限パス使用数 ← 〈pathNumLim〉／更新日 ← 〈ConvertUtil.dbGetDate()〉／更新時刻 ← 〈ConvertUtil.dbGetTime()〉 |
| 対象条件 | 抽出・更新対象条件：接続先='〈ip〉' |
| 確定・取消 | 呼出側または接続の設定に従う。当該メソッド単独でのコミット・ロールバック指定はない。 |
| 原本 | n2framework/WEB-INF/src/webon/base/UpdatePathMngStatBase.java:70 / updatePathNo@70 |

#### 結果・例外時の扱い

| 到達条件 | 結果 |
| --- | --- |
| 条件17を満たす（原本条件は補足説明を参照） | 処理の異常を通知し、この経路を終了する |

### updatePathNo

#### 処理概要

Webon汎用照会ベースクラス パス管理ステータスUpdate Baseクラスで「updatePathNo」の要求を受け付ける。入力・確認・データ操作・応答の順と、条件が成立しない場合の処理を以下に示す。

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

#### DB操作の詳細

#### DB操作 SQL-F97C0AE27E69

| 情報 | 内容 |
| --- | --- |
| 操作ID | SQL-F97C0AE27E69 |
| 対象テーブル | NAVI.ＵＳパス管理ステータス |
| 操作 | 更新 |
| 処理説明 | 対象テーブルの条件に一致する行を更新する。設定項目・対象条件・確定取消は以下の定義に従う。 |
| 設定項目 | パス使用数 ← 〈pathNum〉／更新日 ← 〈ConvertUtil.dbGetDate()〉／更新時刻 ← 〈ConvertUtil.dbGetTime()〉 |
| 対象条件 | 抽出・更新対象条件：接続先='〈ip〉' |
| 確定・取消 | 呼出側または接続の設定に従う。当該メソッド単独でのコミット・ロールバック指定はない。 |
| 原本 | n2framework/WEB-INF/src/webon/base/UpdatePathMngStatBase.java:41 / updatePathNo@41 |

#### DB操作 SQL-8DA5C44CC841

| 情報 | 内容 |
| --- | --- |
| 操作ID | SQL-8DA5C44CC841 |
| 対象テーブル | NAVI.ＵＳパス管理ステータス |
| 操作 | 更新 |
| 処理説明 | 対象テーブルの条件に一致する行を更新する。設定項目・対象条件・確定取消は以下の定義に従う。 |
| 設定項目 | パス使用数 ← 〈pathNum〉／制限パス使用数 ← 〈pathNumLim〉／更新日 ← 〈ConvertUtil.dbGetDate()〉／更新時刻 ← 〈ConvertUtil.dbGetTime()〉 |
| 対象条件 | 抽出・更新対象条件：接続先='〈ip〉' |
| 確定・取消 | 呼出側または接続の設定に従う。当該メソッド単独でのコミット・ロールバック指定はない。 |
| 原本 | n2framework/WEB-INF/src/webon/base/UpdatePathMngStatBase.java:70 / updatePathNo@70 |

#### 結果・例外時の扱い

| 到達条件 | 結果 |
| --- | --- |
| 条件19を満たす（原本条件は補足説明を参照） | 処理の異常を通知し、この経路を終了する |

### DB関連処理


## 補足説明

### 適用条件

各仮定のQA番号を確認する。静的に確認できた操作・条件を適用する。

### 処理・条件の原本対応

文書内の条件番号・処理番号は次の原本表記に対応する。完全な業務用語への置換を行っていない箇所はQA・reportで確認する。

| イベント | 参照番号 | 原本条件・処理 |
| --- | --- | --- |
| UpdatePathMngStatBase | 処理1 | super(connection) |
| UpdatePathMngStatBase | 処理2 | super(connection) |
| updatePathNo | 処理1 | execute(sb.toString()) |
| updatePathNo | 処理2 | sb.append(" WHERE ").append(DBKEY_ACCESSPOINT).append("='").append(ip).append("'") |
| updatePathNo | 処理3 | sb.append(",").append(DBKEY_UPTIME).append("=").append(ConvertUtil.dbGetTime()) |
| updatePathNo | 処理4 | sb.append(",").append(DBKEY_UPDATE).append("=").append(ConvertUtil.dbGetDate()) |
| updatePathNo | 処理5 | sb.append(" ").append(DBKEY_PATHNUM).append("=").append(pathNum) |
| updatePathNo | 処理6 | sb.append(" SET") |
| updatePathNo | 処理7 | sb.append("UPDATE ").append(DBNAME) |
| updatePathNo | 処理8 | StringBuffer sb = new StringBuffer() |
| updatePathNo | 処理9 | StringBuffer sb = new StringBuffer() |
| updatePathNo | 処理10 | sb.append("UPDATE ").append(DBNAME) |
| updatePathNo | 処理11 | sb.append(" SET") |
| updatePathNo | 処理12 | sb.append(" ").append(DBKEY_PATHNUM).append("=").append(pathNum) |
| updatePathNo | 処理13 | sb.append(",").append(DBKEY_UPDATE).append("=").append(ConvertUtil.dbGetDate()) |
| updatePathNo | 処理14 | sb.append(",").append(DBKEY_UPTIME).append("=").append(ConvertUtil.dbGetTime()) |
| updatePathNo | 処理15 | sb.append(" WHERE ").append(DBKEY_ACCESSPOINT).append("='").append(ip).append("'") |
| updatePathNo | 処理16 | execute(sb.toString()) |
| updatePathNo | 条件17 | SQLException e |
| updatePathNo | 処理1 | execute(sb.toString()) |
| updatePathNo | 処理2 | sb.append(" WHERE ").append(DBKEY_ACCESSPOINT).append("='").append(ip).append("'") |
| updatePathNo | 処理3 | sb.append(",").append(DBKEY_UPTIME).append("=").append(ConvertUtil.dbGetTime()) |
| updatePathNo | 処理4 | sb.append(",").append(DBKEY_UPDATE).append("=").append(ConvertUtil.dbGetDate()) |
| updatePathNo | 処理5 | sb.append(",").append(DBKEY_LIMPATHNUM).append("=").append(pathNumLim) |
| updatePathNo | 処理6 | sb.append(" ").append(DBKEY_PATHNUM).append("=").append(pathNum) |
| updatePathNo | 処理7 | sb.append(" SET") |
| updatePathNo | 処理8 | sb.append("UPDATE ").append(DBNAME) |
| updatePathNo | 処理9 | StringBuffer sb = new StringBuffer() |
| updatePathNo | 処理10 | StringBuffer sb = new StringBuffer() |
| updatePathNo | 処理11 | sb.append("UPDATE ").append(DBNAME) |
| updatePathNo | 処理12 | sb.append(" SET") |
| updatePathNo | 処理13 | sb.append(" ").append(DBKEY_PATHNUM).append("=").append(pathNum) |
| updatePathNo | 処理14 | sb.append(",").append(DBKEY_LIMPATHNUM).append("=").append(pathNumLim) |
| updatePathNo | 処理15 | sb.append(",").append(DBKEY_UPDATE).append("=").append(ConvertUtil.dbGetDate()) |
| updatePathNo | 処理16 | sb.append(",").append(DBKEY_UPTIME).append("=").append(ConvertUtil.dbGetTime()) |
| updatePathNo | 処理17 | sb.append(" WHERE ").append(DBKEY_ACCESSPOINT).append("='").append(ip).append("'") |
| updatePathNo | 処理18 | execute(sb.toString()) |
| updatePathNo | 条件19 | SQLException e |

