# データウェアハウス コード検索Baseのスーパークラス 各コード検索Baseクラスは、必ずこのクラスを継承する

## 表紙

| 項目 | 内容 |
| --- | --- |
| 文書名 | 基本設計書 |
| システム名 |  |
| 機能ID | COM-023 |
| 画面名 | データウェアハウス コード検索Baseのスーパークラス 各コード検索Baseクラスは、必ずこのクラスを継承する |
| 会社名 |  |
| 作成日 |  |


## 概要

### 概要説明

データウェアハウス コード検索Baseのスーパークラス 各コード検索Baseクラスは、必ずこのクラスを継承するの入力・表示・要求処理を行う。

| 情報 | 内容 |
| --- | --- |
| 対象種別 | common |
| 開始契機 | 呼出元からの要求 |
| 処理対象 | 入力値・画面状態 |


## 項目一覧

| No | グループ | 項目名 | 種類 | 入出力 | DB連携項目 | 候補取得元 | 必須 | 形式・桁 | 説明 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |

項目定義数：0項目。表示順と反復行の定義数を区別する。


## イベント仕様

### CommonBaseSelectCode

#### 処理概要

データウェアハウス コード検索Baseのスーパークラス 各コード検索Baseクラスは、必ずこのクラスを継承するで「CommonBaseSelectCode」の要求を受け付ける。入力・確認・データ操作・応答の順と、条件が成立しない場合の処理を以下に示す。

#### 処理手順

1. 関連情報を取得・設定する（処理2：詳細仕様参照）。

### executeMap

#### 処理概要

データウェアハウス コード検索Baseのスーパークラス 各コード検索Baseクラスは、必ずこのクラスを継承するで「executeMap」の要求を受け付ける。入力・確認・データ操作・応答の順と、条件が成立しない場合の処理を以下に示す。

#### 処理手順

1. 関連情報を取得・設定する（処理13：詳細仕様参照）。

2. 関連情報を取得・設定する（処理14：詳細仕様参照）。

3. 通常処理と例外時の処理を区別して実行する。例外処理は対応する例外が発生した場合に限る。

3.1. 通常処理：関連情報を取得・設定する（処理15：詳細仕様参照）。

3.2. 通常処理：関連情報を取得・設定する（処理16：詳細仕様参照）。

3.3. 通常処理：「「対象項目」」に該当するか確認する。該当する場合に限り、次の分岐内手順を行う。該当しない場合は分岐の後へ進む。

3.3.1. 条件成立時：関連情報を取得・設定する（処理17：詳細仕様参照）。

3.4. 通常処理：「対象項目」を設定する。

3-例外1. 例外条件「SQLException e」に該当した場合に次の手順を行う。型名は原本の表記。

3-例外1.1. 例外発生時：関連情報を取得・設定する（処理18：詳細仕様参照）。

3-例外1.2. 例外発生時：終了時の共通後処理を行ってから、処理の異常を通知し、この経路を終了する。この経路の後続手順は実行しない。

3-後処理. 通常終了・例外・途中のreturnのいずれでも、この範囲を抜ける前に次の共通後処理を行う。

3-後処理.1. 終了時の共通後処理：「対象項目がある」に該当するか確認する。該当する場合に限り、次の分岐内手順を行う。該当しない場合は分岐の後へ進む。

3-後処理.1.1. 条件成立時：使用した接続・処理資源を解放する。

3-後処理.2. 終了時の共通後処理：「対象項目がある」に該当するか確認する。該当する場合に限り、次の分岐内手順を行う。該当しない場合は分岐の後へ進む。

3-後処理.2.1. 条件成立時：使用した接続・処理資源を解放する。

3-後処理.3. 終了時の共通後処理：関連情報を取得・設定する（処理19：詳細仕様参照）。

3-後処理.4. 終了時の共通後処理：関連情報を取得・設定する（処理20：詳細仕様参照）。

#### 結果・例外時の扱い

| 到達条件 | 結果 |
| --- | --- |
| 条件21を満たす（原本条件は補足説明を参照） | 処理の異常を通知し、この経路を終了する |

### convertResultSetToMap

#### 処理概要

データウェアハウス コード検索Baseのスーパークラス 各コード検索Baseクラスは、必ずこのクラスを継承するで「convertResultSetToMap」の要求を受け付ける。入力・確認・データ操作・応答の順と、条件が成立しない場合の処理を以下に示す。

#### 処理手順

1. 関連情報を取得・設定する（処理7：詳細仕様参照）。

2. 繰返し条件「条件8を満たす（原本条件は補足説明を参照）」に従い、次の手順を繰り返す。条件を満たさなくなった場合は繰返しの後へ進む。

2.1. 繰返しの各回：関連情報を取得・設定する（処理9：詳細仕様参照）。

2.2. 繰返しの各回：関連情報を取得・設定する（処理10：詳細仕様参照）。

2.3. 繰返しの各回：「対象項目がない」に該当するか確認する。成立時と不成立時の手順を分けて行う。

2.3.1. 条件成立時：関連情報を取得・設定する（処理11：詳細仕様参照）。

2.3-別.1. 条件不成立時：関連情報を取得・設定する（処理12：詳細仕様参照）。

3. 処理結果を呼出元へ返す。この経路の後続手順は実行しない。

#### 結果・例外時の扱い

| 到達条件 | 結果 |
| --- | --- |
| この終了経路へ到達した場合 | 処理結果を呼出元へ返す |

### getMap

#### 処理概要

データウェアハウス コード検索Baseのスーパークラス 各コード検索Baseクラスは、必ずこのクラスを継承するで「getMap」の要求を受け付ける。入力・確認・データ操作・応答の順と、条件が成立しない場合の処理を以下に示す。

#### 処理手順

1. 処理結果を呼出元へ返す。この経路の後続手順は実行しない。

#### 結果・例外時の扱い

| 到達条件 | 結果 |
| --- | --- |
| この終了経路へ到達した場合 | 処理結果を呼出元へ返す |

### setMap

#### 処理概要

データウェアハウス コード検索Baseのスーパークラス 各コード検索Baseクラスは、必ずこのクラスを継承するで「setMap」の要求を受け付ける。入力・確認・データ操作・応答の順と、条件が成立しない場合の処理を以下に示す。

#### 処理手順

1. 関連情報を取得・設定する（処理2：詳細仕様参照）。


## 補足説明

### 適用条件

各仮定のQA番号を確認する。静的に確認できた操作・条件を適用する。

### 処理・条件の原本対応

文書内の条件番号・処理番号は次の原本表記に対応する。完全な業務用語への置換を行っていない箇所はQA・reportで確認する。

| イベント | 参照番号 | 原本条件・処理 |
| --- | --- | --- |
| CommonBaseSelectCode | 処理1 | super(connection) |
| CommonBaseSelectCode | 処理2 | super(connection) |
| executeMap | 処理1 | stmt = null |
| executeMap | 処理2 | rs = null |
| executeMap | 処理3 | stmt = null |
| executeMap | 処理4 | rs = null |
| executeMap | 処理5 | stmt = null |
| executeMap | 処理6 | rs = null |
| executeMap | 処理7 | FWLog.error(sql) |
| executeMap | 処理8 | FWLog.debug(this.getClass(), sql) |
| executeMap | 処理9 | rs = stmt.executeQuery(sql) |
| executeMap | 処理10 | stmt = getConnection().createStatement() |
| executeMap | 処理11 | ResultSet rs = null |
| executeMap | 処理12 | Statement stmt = null |
| executeMap | 処理13 | Statement stmt = null |
| executeMap | 処理14 | ResultSet rs = null |
| executeMap | 処理15 | stmt = getConnection().createStatement() |
| executeMap | 処理16 | rs = stmt.executeQuery(sql) |
| executeMap | 処理17 | FWLog.debug(this.getClass(), sql) |
| executeMap | 処理18 | FWLog.error(sql) |
| executeMap | 処理19 | rs = null |
| executeMap | 処理20 | stmt = null |
| executeMap | 条件21 | SQLException e |
| convertResultSetToMap | 条件1 | rs.next() |
| convertResultSetToMap | 処理2 | mapRS.put(code,"") |
| convertResultSetToMap | 処理3 | mapRS.put(code,value.trim()) |
| convertResultSetToMap | 処理4 | String value = rs.getString(2) |
| convertResultSetToMap | 処理5 | String code = rs.getString(1) |
| convertResultSetToMap | 処理6 | Map mapRS = new HashMap() |
| convertResultSetToMap | 処理7 | Map mapRS = new HashMap() |
| convertResultSetToMap | 条件8 | rs.next() |
| convertResultSetToMap | 処理9 | String code = rs.getString(1) |
| convertResultSetToMap | 処理10 | String value = rs.getString(2) |
| convertResultSetToMap | 処理11 | mapRS.put(code,"") |
| convertResultSetToMap | 処理12 | mapRS.put(code,value.trim()) |
| setMap | 処理1 | this.map = map |
| setMap | 処理2 | this.map = map |

