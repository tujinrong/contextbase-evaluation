# データウェアハウス カウンターシフト登録Baseクラス

## 表紙

| 項目 | 内容 |
| --- | --- |
| 文書名 | 基本設計書 |
| システム名 |  |
| 機能ID | COM-025 |
| 画面名 | データウェアハウス カウンターシフト登録Baseクラス |
| 会社名 |  |
| 作成日 |  |


## 概要

### 概要説明

データウェアハウス カウンターシフト登録Baseクラスの入力・表示・要求処理を行う。

| 情報 | 内容 |
| --- | --- |
| 対象種別 | common |
| 開始契機 | 呼出元からの要求 |
| 処理対象 | DB2.Ｕカウンターシフト |


## 項目一覧

| No | グループ | 項目名 | 種類 | 入出力 | DB連携項目 | 候補取得元 | 必須 | 形式・桁 | 説明 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |

項目定義数：0項目。表示順と反復行の定義数を区別する。


## イベント仕様

### InsertCounterShiftBase

#### 処理概要

データウェアハウス カウンターシフト登録Baseクラスで「InsertCounterShiftBase」の要求を受け付ける。入力・確認・データ操作・応答の順と、条件が成立しない場合の処理を以下に示す。

#### 処理手順

1. 関連情報を取得・設定する（処理2：詳細仕様参照）。

### insert

#### 処理概要

データウェアハウス カウンターシフト登録Baseクラスで「insert」の要求を受け付ける。入力・確認・データ操作・応答の順と、条件が成立しない場合の処理を以下に示す。

#### 処理手順

1. 通常処理と例外時の処理を区別して実行する。例外処理は対応する例外が発生した場合に限る。

1.1. 通常処理：「insert into DB2.Ｕカウンターシフト 」を設定する。

1.2. 通常処理：「(アクセス日付,アクセス時刻,機能ＩＤ,画面ＩＤ,コマンドＩＤ,アクションＩＤ,」を設定する。

1.3. 通常処理：「ＪＳＰ名,ユーザーＩＤ) 」を設定する。

1.4. 通常処理：関連情報を取得・設定する（処理10：詳細仕様参照）。

1.5. 通常処理：関連情報を取得・設定する（処理11：詳細仕様参照）。

1.6. 通常処理：関連情報を取得・設定する（処理12：詳細仕様参照）。

1.7. 通常処理：関連情報を取得・設定する（処理13：詳細仕様参照）。

1.8. 通常処理：関連情報を取得・設定する（処理14：詳細仕様参照）。

1.9. 通常処理：関連情報を取得・設定する（処理15：詳細仕様参照）。

1.10. 通常処理：関連情報を取得・設定する（処理16：詳細仕様参照）。

1.11. 通常処理：「対象項目」を設定する。

1.12. 通常処理：「対象項目」を設定する。

1.13. 通常処理：「対象項目」を設定する。

1.14. 通常処理：「対象項目」を設定する。

1.15. 通常処理：「対象項目」を設定する。

1.16. 通常処理：「ユーザーＩＤ」を設定する。

1.17. 通常処理：関連情報を取得・設定する（処理17：詳細仕様参照）。

1.18. 通常処理：関連情報を取得・設定する（処理18：詳細仕様参照）。

1-例外1. 例外条件「SQLException e」に該当した場合に次の手順を行う。型名は原本の表記。

1-例外1.1. 例外発生時：処理の異常を通知し、この経路を終了する。この経路の後続手順は実行しない。

#### DB操作の詳細

#### DB操作 SQL-55B58633E466

| 情報 | 内容 |
| --- | --- |
| 操作ID | SQL-55B58633E466 |
| 対象テーブル | DB2.Ｕカウンターシフト |
| 操作 | 挿入 |
| 処理説明 | 対象テーブルの新しい行を登録する。設定項目・対象条件・確定取消は以下の定義に従う。 |
| 設定項目 | アクセス日付 ← 〈gSDFDate.format(date)〉／アクセス時刻 ← 〈gSDFTime.format(date)〉／機能ＩＤ ← 〈map.get(機能ＩＤ)：空値・NULLの条件付き設定〉／画面ＩＤ ← 〈map.get(画面ＩＤ)：空値・NULLの条件付き設定〉／コマンドＩＤ ← 〈map.get(コマンドＩＤ)：空値・NULLの条件付き設定〉／アクションＩＤ ← 〈map.get(アクションＩＤ)：空値・NULLの条件付き設定〉／ＪＳＰ名 ← 〈map.get(ＪＳＰ名)：空値・NULLの条件付き設定〉／ユーザーＩＤ ← '〈map.get("ユーザーＩＤ")〉' |
| 対象条件 | 新しい行を挿入する。重複や採番の扱いは呼出元および列制約に従う。 |
| 確定・取消 | 呼出側または接続の設定に従う。当該メソッド単独でのコミット・ロールバック指定はない。 |
| 原本 | n2framework/WEB-INF/src/common/base/InsertCounterShiftBase.java:34 / insert@34 |

#### 結果・例外時の扱い

| 到達条件 | 結果 |
| --- | --- |
| 条件19を満たす（原本条件は補足説明を参照） | 処理の異常を通知し、この経路を終了する |

### setColumun

#### 処理概要

データウェアハウス カウンターシフト登録Baseクラスで「setColumun」の要求を受け付ける。入力・確認・データ操作・応答の順と、条件が成立しない場合の処理を以下に示す。

#### 処理手順

1. 関連情報を取得・設定する（処理9：詳細仕様参照）。

2. 「map.get(columun)  が異なる  未設定、かつ条件10を満たす（原本条件は補足説明を参照）」に該当するか確認する。成立時と不成立時の手順を分けて行う。

2.1. 条件成立時：「条件11を満たす（原本条件は補足説明を参照）」に該当するか確認する。該当する場合に限り、次の分岐内手順を行う。該当しない場合は分岐の後へ進む。

2.1.1. 条件成立時：関連情報を取得・設定する（処理12：詳細仕様参照）。

2.2. 条件成立時：関連情報を取得・設定する（処理13：詳細仕様参照）。

2.3. 条件成立時：「条件14を満たす（原本条件は補足説明を参照）」に該当するか確認する。該当する場合に限り、次の分岐内手順を行う。該当しない場合は分岐の後へ進む。

2.3.1. 条件成立時：関連情報を取得・設定する（処理15：詳細仕様参照）。

2-別.1. 条件不成立時：関連情報を取得・設定する（処理16：詳細仕様参照）。

### DB関連処理


## 補足説明

### 適用条件

各仮定のQA番号を確認する。静的に確認できた操作・条件を適用する。

### 処理・条件の原本対応

文書内の条件番号・処理番号は次の原本表記に対応する。完全な業務用語への置換を行っていない箇所はQA・reportで確認する。

| イベント | 参照番号 | 原本条件・処理 |
| --- | --- | --- |
| InsertCounterShiftBase | 処理1 | super(connection) |
| InsertCounterShiftBase | 処理2 | super(connection) |
| insert | 処理1 | execute(sb.toString()) |
| insert | 処理2 | sb.append(")") |
| insert | 処理3 | sb.append(gSDFTime.format(date)) |
| insert | 処理4 | SimpleDateFormat gSDFTime = new SimpleDateFormat("HHmmssSSS") |
| insert | 処理5 | sb.append(gSDFDate.format(date) + ",") |
| insert | 処理6 | SimpleDateFormat gSDFDate = new SimpleDateFormat("yyyyMMdd") |
| insert | 処理7 | Date date = new Date() |
| insert | 処理8 | sb.append("(") |
| insert | 処理9 | sb.append(" values ") |
| insert | 処理10 | sb.append(" values ") |
| insert | 処理11 | sb.append("(") |
| insert | 処理12 | Date date = new Date() |
| insert | 処理13 | SimpleDateFormat gSDFDate = new SimpleDateFormat("yyyyMMdd") |
| insert | 処理14 | sb.append(gSDFDate.format(date) + ",") |
| insert | 処理15 | SimpleDateFormat gSDFTime = new SimpleDateFormat("HHmmssSSS") |
| insert | 処理16 | sb.append(gSDFTime.format(date)) |
| insert | 処理17 | sb.append(")") |
| insert | 処理18 | execute(sb.toString()) |
| insert | 条件19 | SQLException e |
| setColumun | 処理1 | sb.append("'") |
| setColumun | 条件2 | isChar |
| setColumun | 処理3 | sb.append(map.get(columun)) |
| setColumun | 処理4 | sb.append("'") |
| setColumun | 条件5 | isChar |
| setColumun | 処理6 | sb.append("null") |
| setColumun | 条件7 | !"".equals(map.get(columun)) |
| setColumun | 処理8 | sb.append(comma) |
| setColumun | 処理9 | sb.append(comma) |
| setColumun | 条件10 | !"".equals(map.get(columun)) |
| setColumun | 条件11 | isChar |
| setColumun | 処理12 | sb.append("'") |
| setColumun | 処理13 | sb.append(map.get(columun)) |
| setColumun | 条件14 | isChar |
| setColumun | 処理15 | sb.append("'") |
| setColumun | 処理16 | sb.append("null") |

