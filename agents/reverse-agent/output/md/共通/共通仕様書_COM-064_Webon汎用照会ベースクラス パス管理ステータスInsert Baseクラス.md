# Webon汎用照会ベースクラス パス管理ステータスInsert Baseクラス

## 表紙

| 項目 | 内容 |
| --- | --- |
| 文書名 | 基本設計書 |
| システム名 |  |
| 機能ID | COM-064 |
| 画面名 | Webon汎用照会ベースクラス パス管理ステータスInsert Baseクラス |
| 会社名 |  |
| 作成日 |  |


## 概要

### 概要説明

Webon汎用照会ベースクラス パス管理ステータスInsert Baseクラスの入力・表示・要求処理を行う。

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

### InsertPathMngStatBase

#### 処理概要

Webon汎用照会ベースクラス パス管理ステータスInsert Baseクラスで「InsertPathMngStatBase」の要求を受け付ける。入力・確認・データ操作・応答の順と、条件が成立しない場合の処理を以下に示す。

#### 処理手順

1. 関連情報を取得・設定する（処理2：詳細仕様参照）。

### insertPathNo

#### 処理概要

Webon汎用照会ベースクラス パス管理ステータスInsert Baseクラスで「insertPathNo」の要求を受け付ける。入力・確認・データ操作・応答の順と、条件が成立しない場合の処理を以下に示す。

#### 処理手順

1. 関連情報を取得・設定する（処理21：詳細仕様参照）。

2. 関連情報を取得・設定する（処理22：詳細仕様参照）。

3. 関連情報を取得・設定する（処理23：詳細仕様参照）。

4. 関連情報を取得・設定する（処理24：詳細仕様参照）。

5. 関連情報を取得・設定する（処理25：詳細仕様参照）。

6. 関連情報を取得・設定する（処理26：詳細仕様参照）。

7. 関連情報を取得・設定する（処理27：詳細仕様参照）。

8. 関連情報を取得・設定する（処理28：詳細仕様参照）。

9. 関連情報を取得・設定する（処理29：詳細仕様参照）。

10. 関連情報を取得・設定する（処理30：詳細仕様参照）。

11. 関連情報を取得・設定する（処理31：詳細仕様参照）。

12. 関連情報を取得・設定する（処理32：詳細仕様参照）。

13. 関連情報を取得・設定する（処理33：詳細仕様参照）。

14. 関連情報を取得・設定する（処理34：詳細仕様参照）。

15. 関連情報を取得・設定する（処理35：詳細仕様参照）。

16. 関連情報を取得・設定する（処理36：詳細仕様参照）。

17. 関連情報を取得・設定する（処理37：詳細仕様参照）。

18. 関連情報を取得・設定する（処理38：詳細仕様参照）。

19. 関連情報を取得・設定する（処理39：詳細仕様参照）。

20. 通常処理と例外時の処理を区別して実行する。例外処理は対応する例外が発生した場合に限る。

20.1. 通常処理：関連情報を取得・設定する（処理40：詳細仕様参照）。

20-例外1. 例外条件「SQLException e」に該当した場合に次の手順を行う。型名は原本の表記。

20-例外1.1. 例外発生時：処理の異常を通知し、この経路を終了する。この経路の後続手順は実行しない。

#### DB操作の詳細

#### DB操作 SQL-B07128F6323E

| 情報 | 内容 |
| --- | --- |
| 操作ID | SQL-B07128F6323E |
| 対象テーブル | NAVI.ＵＳパス管理ステータス |
| 操作 | 挿入 |
| 処理説明 | 対象テーブルの新しい行を登録する。設定項目・対象条件・確定取消は以下の定義に従う。 |
| 設定項目 | 接続先 ← 〈ConvertUtil.dbMoldStr(ip, 15)〉／パス使用数 ← 〈ConvertUtil.dbMoldInt(DBVAL_INITPATHNUM, 3)〉／制限パス使用数 ← 〈ConvertUtil.dbMoldInt(DBVAL_INITPATHNUMLIM, 3)〉／作成日 ← 〈ConvertUtil.dbGetDate()〉／作成時刻 ← 〈ConvertUtil.dbGetTime()〉／更新日 ← 〈ConvertUtil.dbGetDate()〉／更新時刻 ← 〈ConvertUtil.dbGetTime()〉 |
| 対象条件 | 新しい行を挿入する。重複や採番の扱いは呼出元および列制約に従う。 |
| 確定・取消 | 呼出側または接続の設定に従う。当該メソッド単独でのコミット・ロールバック指定はない。 |
| 原本 | n2framework/WEB-INF/src/webon/base/InsertPathMngStatBase.java:42 / insertPathNo@42 |

#### 結果・例外時の扱い

| 到達条件 | 結果 |
| --- | --- |
| 条件41を満たす（原本条件は補足説明を参照） | 処理の異常を通知し、この経路を終了する |

### DB関連処理


## 補足説明

### 適用条件

各仮定のQA番号を確認する。静的に確認できた操作・条件を適用する。

### 処理・条件の原本対応

文書内の条件番号・処理番号は次の原本表記に対応する。完全な業務用語への置換を行っていない箇所はQA・reportで確認する。

| イベント | 参照番号 | 原本条件・処理 |
| --- | --- | --- |
| InsertPathMngStatBase | 処理1 | super(connection) |
| InsertPathMngStatBase | 処理2 | super(connection) |
| insertPathNo | 処理1 | execute(sb.toString()) |
| insertPathNo | 処理2 | sb.append(")") |
| insertPathNo | 処理3 | sb.append(",").append(ConvertUtil.dbGetTime()) |
| insertPathNo | 処理4 | sb.append(",").append(ConvertUtil.dbGetDate()) |
| insertPathNo | 処理5 | sb.append(",").append(ConvertUtil.dbGetTime()) |
| insertPathNo | 処理6 | sb.append(",").append(ConvertUtil.dbGetDate()) |
| insertPathNo | 処理7 | sb.append(",").append(ConvertUtil.dbMoldInt(DBVAL_INITPATHNUMLIM, 3)) |
| insertPathNo | 処理8 | sb.append(",").append(ConvertUtil.dbMoldInt(DBVAL_INITPATHNUM, 3)) |
| insertPathNo | 処理9 | sb.append("(").append(ConvertUtil.dbMoldStr(ip, 15)) |
| insertPathNo | 処理10 | sb.append(" VALUES") |
| insertPathNo | 処理11 | sb.append(" )") |
| insertPathNo | 処理12 | sb.append(" ,").append(DBKEY_UPTIME) |
| insertPathNo | 処理13 | sb.append(" ,").append(DBKEY_UPDATE) |
| insertPathNo | 処理14 | sb.append(" ,").append(DBKEY_MKTIME) |
| insertPathNo | 処理15 | sb.append(" ,").append(DBKEY_MKDATE) |
| insertPathNo | 処理16 | sb.append(" ,").append(DBKEY_LIMPATHNUM) |
| insertPathNo | 処理17 | sb.append(" ,").append(DBKEY_PATHNUM) |
| insertPathNo | 処理18 | sb.append(" (").append(DBKEY_ACCESSPOINT) |
| insertPathNo | 処理19 | sb.append("INSERT INTO ").append(DBNAME) |
| insertPathNo | 処理20 | StringBuffer sb = new StringBuffer() |
| insertPathNo | 処理21 | StringBuffer sb = new StringBuffer() |
| insertPathNo | 処理22 | sb.append("INSERT INTO ").append(DBNAME) |
| insertPathNo | 処理23 | sb.append(" (").append(DBKEY_ACCESSPOINT) |
| insertPathNo | 処理24 | sb.append(" ,").append(DBKEY_PATHNUM) |
| insertPathNo | 処理25 | sb.append(" ,").append(DBKEY_LIMPATHNUM) |
| insertPathNo | 処理26 | sb.append(" ,").append(DBKEY_MKDATE) |
| insertPathNo | 処理27 | sb.append(" ,").append(DBKEY_MKTIME) |
| insertPathNo | 処理28 | sb.append(" ,").append(DBKEY_UPDATE) |
| insertPathNo | 処理29 | sb.append(" ,").append(DBKEY_UPTIME) |
| insertPathNo | 処理30 | sb.append(" )") |
| insertPathNo | 処理31 | sb.append(" VALUES") |
| insertPathNo | 処理32 | sb.append("(").append(ConvertUtil.dbMoldStr(ip, 15)) |
| insertPathNo | 処理33 | sb.append(",").append(ConvertUtil.dbMoldInt(DBVAL_INITPATHNUM, 3)) |
| insertPathNo | 処理34 | sb.append(",").append(ConvertUtil.dbMoldInt(DBVAL_INITPATHNUMLIM, 3)) |
| insertPathNo | 処理35 | sb.append(",").append(ConvertUtil.dbGetDate()) |
| insertPathNo | 処理36 | sb.append(",").append(ConvertUtil.dbGetTime()) |
| insertPathNo | 処理37 | sb.append(",").append(ConvertUtil.dbGetDate()) |
| insertPathNo | 処理38 | sb.append(",").append(ConvertUtil.dbGetTime()) |
| insertPathNo | 処理39 | sb.append(")") |
| insertPathNo | 処理40 | execute(sb.toString()) |
| insertPathNo | 条件41 | SQLException e |

