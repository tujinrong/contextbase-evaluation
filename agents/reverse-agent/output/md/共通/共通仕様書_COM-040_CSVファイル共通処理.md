# CSVファイル共通処理

## 表紙

| 項目 | 内容 |
| --- | --- |
| 文書名 | 基本設計書 |
| システム名 |  |
| 機能ID | COM-040 |
| 画面名 | CSVファイル共通処理 |
| 会社名 |  |
| 作成日 |  |


## 概要

### 概要説明

CSVファイル共通処理の入力・表示・要求処理を行う。

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

### writeCsv

#### 処理概要

CSVファイル共通処理で「writeCsv」の要求を受け付ける。入力・確認・データ操作・応答の順と、条件が成立しない場合の処理を以下に示す。

#### 処理手順

1. 関連情報を取得・設定する（処理14：詳細仕様参照）。

2. 「対象項目がない、または条件15を満たす（原本条件は補足説明を参照）」に該当するか確認する。成立時と不成立時の手順を分けて行う。

2-別.1. 条件不成立時：繰返し条件「条件16を満たす（原本条件は補足説明を参照）」に従い、次の手順を繰り返す。条件を満たさなくなった場合は繰返しの後へ進む。

2-別.1.1. 繰返しの各回：指定した条件でデータを照会する。

2-別.2. 条件不成立時：関連情報を取得・設定する（処理17：詳細仕様参照）。

3. 繰返し条件「条件18を満たす（原本条件は補足説明を参照）」に従い、次の手順を繰り返す。条件を満たさなくなった場合は繰返しの後へ進む。

3.1. 繰返しの各回：関連情報を取得・設定する（処理19：詳細仕様参照）。

3.2. 繰返しの各回：繰返し条件「条件20を満たす（原本条件は補足説明を参照）」に従い、次の手順を繰り返す。条件を満たさなくなった場合は繰返しの後へ進む。

3.2.1. 繰返しの各回：指定した条件でデータを照会する。

3.3. 繰返しの各回：関連情報を取得・設定する（処理21：詳細仕様参照）。

4. 関連情報を取得・設定する（処理22：詳細仕様参照）。

5. 「対象項目」を設定する。

6. 「対象項目」を設定する。

7. 通常処理と例外時の処理を区別して実行する。例外処理は対応する例外が発生した場合に限る。

7.1. 通常処理：関連情報を取得・設定する（処理23：詳細仕様参照）。

7.2. 通常処理：指定した条件でデータを照会する。

7.3. 通常処理：「対象項目がある」に該当するか確認する。該当する場合に限り、次の分岐内手順を行う。該当しない場合は分岐の後へ進む。

7.3.1. 条件成立時：関連情報を取得・設定する（処理24：詳細仕様参照）。

7.4. 通常処理：関連情報を取得・設定する（処理25：詳細仕様参照）。

7.5. 通常処理：関連情報を取得・設定する（処理26：詳細仕様参照）。

7.6. 通常処理：使用した接続・処理資源を解放する。

7.7. 通常処理：使用した接続・処理資源を解放する。

7-例外1. 例外条件「Exception e」に該当した場合に次の手順を行う。型名は原本の表記。

7-例外1.1. 例外発生時：処理の異常を通知し、この経路を終了する。この経路の後続手順は実行しない。

#### 結果・例外時の扱い

| 到達条件 | 結果 |
| --- | --- |
| 条件27を満たす（原本条件は補足説明を参照） | 処理の異常を通知し、この経路を終了する |


## 補足説明

### 適用条件

各仮定のQA番号を確認する。静的に確認できた操作・条件を適用する。

### 処理・条件の原本対応

文書内の条件番号・処理番号は次の原本表記に対応する。完全な業務用語への置換を行っていない箇所はQA・reportで確認する。

| イベント | 参照番号 | 原本条件・処理 |
| --- | --- | --- |
| writeCsv | 処理1 | baos.writeTo(bout) |
| writeCsv | 処理2 | BufferedOutputStream bout = new BufferedOutputStream(res.getOutputStream()) |
| writeCsv | 処理3 | baos.write(data) |
| writeCsv | 処理4 | ByteArrayOutputStream baos = new ByteArrayOutputStream() |
| writeCsv | 処理5 | String fileName= CommonUtil.getCurrentDate("HHmmss") + ".csv" |
| writeCsv | 条件6 | int i = 0 ; i &lt; variableData.size(); i++ |
| writeCsv | 処理7 | sb.replace(sb.length() - 1,sb.length(), "\r" ) |
| writeCsv | 条件8 | int ii = 0 ; ii &lt; vec.size(); ii++ |
| writeCsv | 処理9 | Vector vec= (Vector)variableData.get(i) |
| writeCsv | 処理10 | sb.replace(sb.length() - 1,sb.length(), "\r" ) |
| writeCsv | 条件11 | int i = 0; i &lt; fixedData.length; i++ |
| writeCsv | 条件12 | fixedData[0].equals("") |
| writeCsv | 処理13 | StringBuffer sb = new StringBuffer ( 1024 ) |
| writeCsv | 処理14 | StringBuffer sb = new StringBuffer ( 1024 ) |
| writeCsv | 条件15 | fixedData[0].equals("") |
| writeCsv | 条件16 | int i = 0; i &lt; fixedData.length; i++ |
| writeCsv | 処理17 | sb.replace(sb.length() - 1,sb.length(), "\r" ) |
| writeCsv | 条件18 | int i = 0 ; i &lt; variableData.size(); i++ |
| writeCsv | 処理19 | Vector vec= (Vector)variableData.get(i) |
| writeCsv | 条件20 | int ii = 0 ; ii &lt; vec.size(); ii++ |
| writeCsv | 処理21 | sb.replace(sb.length() - 1,sb.length(), "\r" ) |
| writeCsv | 処理22 | String fileName= CommonUtil.getCurrentDate("HHmmss") + ".csv" |
| writeCsv | 処理23 | ByteArrayOutputStream baos = new ByteArrayOutputStream() |
| writeCsv | 処理24 | baos.write(data) |
| writeCsv | 処理25 | BufferedOutputStream bout = new BufferedOutputStream(res.getOutputStream()) |
| writeCsv | 処理26 | baos.writeTo(bout) |
| writeCsv | 条件27 | Exception e |

