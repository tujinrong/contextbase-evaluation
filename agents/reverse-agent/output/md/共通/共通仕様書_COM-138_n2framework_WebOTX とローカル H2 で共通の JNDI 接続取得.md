# n2framework/WebOTX とローカル H2 で共通の JNDI 接続取得

## 表紙

| 項目 | 内容 |
| --- | --- |
| 文書名 | 基本設計書 |
| システム名 |  |
| 機能ID | COM-138 |
| 画面名 | n2framework/WebOTX とローカル H2 で共通の JNDI 接続取得 |
| 会社名 |  |
| 作成日 |  |


## 概要

### 概要説明

n2framework/WebOTX とローカル H2 で共通の JNDI 接続取得の入力・表示・要求処理を行う。

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

### NenkinDataSource

#### 処理概要

n2framework/WebOTX とローカル H2 で共通の JNDI 接続取得で「NenkinDataSource」の要求を受け付ける。入力・確認・データ操作・応答の順と、条件が成立しない場合の処理を以下に示す。

#### 処理手順

1. 関連する処理へ制御を渡す。詳細な実行経路は原本対応を参照する。

### openConnection

#### 処理概要

n2framework/WebOTX とローカル H2 で共通の JNDI 接続取得で「openConnection」の要求を受け付ける。入力・確認・データ操作・応答の順と、条件が成立しない場合の処理を以下に示す。

#### 処理手順

1. 関連情報を取得・設定する（処理4：詳細仕様参照）。

2. 「対象項目がない」に該当するか確認する。該当する場合に限り、次の分岐内手順を行う。該当しない場合は分岐の後へ進む。

2.1. 条件成立時：排他制御の範囲内で次の手順を実行する。

2.1.1. 排他制御の範囲内：関連情報を取得・設定する（処理5：詳細仕様参照）。

2.1.2. 排他制御の範囲内：「対象項目がない」に該当するか確認する。該当する場合に限り、次の分岐内手順を行う。該当しない場合は分岐の後へ進む。

2.1.2.1. 条件成立時：「年金業務用JNDI DataSourceを取得できません。」を設定する。

2.1.2.2. 条件成立時：関連情報を取得・設定する（処理6：詳細仕様参照）。

3. 処理結果を呼出元へ返す。この経路の後続手順は実行しない。

#### 結果・例外時の扱い

| 到達条件 | 結果 |
| --- | --- |
| この終了経路へ到達した場合 | 処理結果を呼出元へ返す |

### openStaffConnection

#### 処理概要

n2framework/WebOTX とローカル H2 で共通の JNDI 接続取得で「openStaffConnection」の要求を受け付ける。入力・確認・データ操作・応答の順と、条件が成立しない場合の処理を以下に示す。

#### 処理手順

1. 関連情報を取得・設定する（処理4：詳細仕様参照）。

2. 「対象項目がない」に該当するか確認する。該当する場合に限り、次の分岐内手順を行う。該当しない場合は分岐の後へ進む。

2.1. 条件成立時：排他制御の範囲内で次の手順を実行する。

2.1.1. 排他制御の範囲内：関連情報を取得・設定する（処理5：詳細仕様参照）。

2.1.2. 排他制御の範囲内：「対象項目がない」に該当するか確認する。該当する場合に限り、次の分岐内手順を行う。該当しない場合は分岐の後へ進む。

2.1.2.1. 条件成立時：「N2職員名簿用JNDI DataSourceを取得できません。」を設定する。

2.1.2.2. 条件成立時：関連情報を取得・設定する（処理6：詳細仕様参照）。

3. 処理結果を呼出元へ返す。この経路の後続手順は実行しない。

#### 結果・例外時の扱い

| 到達条件 | 結果 |
| --- | --- |
| この終了経路へ到達した場合 | 処理結果を呼出元へ返す |

### openCustomerConnection

#### 処理概要

n2framework/WebOTX とローカル H2 で共通の JNDI 接続取得で「openCustomerConnection」の要求を受け付ける。入力・確認・データ操作・応答の順と、条件が成立しない場合の処理を以下に示す。

#### 処理手順

1. 関連情報を取得・設定する（処理4：詳細仕様参照）。

2. 「対象項目がない」に該当するか確認する。該当する場合に限り、次の分岐内手順を行う。該当しない場合は分岐の後へ進む。

2.1. 条件成立時：排他制御の範囲内で次の手順を実行する。

2.1.1. 排他制御の範囲内：関連情報を取得・設定する（処理5：詳細仕様参照）。

2.1.2. 排他制御の範囲内：「対象項目がない」に該当するか確認する。該当する場合に限り、次の分岐内手順を行う。該当しない場合は分岐の後へ進む。

2.1.2.1. 条件成立時：「N2顧客基本表用JNDI DataSourceを取得できません。」を設定する。

2.1.2.2. 条件成立時：関連情報を取得・設定する（処理6：詳細仕様参照）。

3. 処理結果を呼出元へ返す。この経路の後続手順は実行しない。

#### 結果・例外時の扱い

| 到達条件 | 結果 |
| --- | --- |
| この終了経路へ到達した場合 | 処理結果を呼出元へ返す |

### lookup

#### 処理概要

n2framework/WebOTX とローカル H2 で共通の JNDI 接続取得で「lookup」の要求を受け付ける。入力・確認・データ操作・応答の順と、条件が成立しない場合の処理を以下に示す。

#### 処理手順

1. 関連情報を取得・設定する（処理8：詳細仕様参照）。

2. 繰返し条件「条件9を満たす（原本条件は補足説明を参照）」に従い、次の手順を繰り返す。条件を満たさなくなった場合は繰返しの後へ進む。

2.1. 繰返しの各回：通常処理と例外時の処理を区別して実行する。例外処理は対応する例外が発生した場合に限る。

2.1.1. 通常処理：関連情報を取得・設定する（処理10：詳細仕様参照）。

2.1.2. 通常処理：「条件11を満たす（原本条件は補足説明を参照）」に該当するか確認する。該当する場合に限り、次の分岐内手順を行う。該当しない場合は分岐の後へ進む。

2.1.2.1. 条件成立時：処理結果を呼出元へ返す。この経路の後続手順は実行しない。

2.1-例外1. 例外条件「NamingException e」に該当した場合に次の手順を行う。型名は原本の表記。

2.1-例外1.1. 例外発生時：関連情報を取得・設定する（処理12：詳細仕様参照）。

3. 関連情報を取得・設定する（処理13：詳細仕様参照）。

4. 「対象項目がある」に該当するか確認する。該当する場合に限り、次の分岐内手順を行う。該当しない場合は分岐の後へ進む。

4.1. 条件成立時：関連情報を取得・設定する（処理14：詳細仕様参照）。

5. 処理の異常を通知し、この経路を終了する。この経路の後続手順は実行しない。

#### 結果・例外時の扱い

| 到達条件 | 結果 |
| --- | --- |
| 条件15を満たす（原本条件は補足説明を参照）・条件16を満たす（原本条件は補足説明を参照） | 処理結果を呼出元へ返す |
| この終了経路へ到達した場合 | 処理の異常を通知し、この経路を終了する |


## 補足説明

### 適用条件

各仮定のQA番号を確認する。静的に確認できた操作・条件を適用する。

### 処理・条件の原本対応

文書内の条件番号・処理番号は次の原本表記に対応する。完全な業務用語への置換を行っていない箇所はQA・reportで確認する。

| イベント | 参照番号 | 原本条件・処理 |
| --- | --- | --- |
| openConnection | 処理1 | businessCached = dataSource |
| openConnection | 処理2 | dataSource = businessCached |
| openConnection | 処理3 | DataSource dataSource = businessCached |
| openConnection | 処理4 | DataSource dataSource = businessCached |
| openConnection | 処理5 | dataSource = businessCached |
| openConnection | 処理6 | businessCached = dataSource |
| openStaffConnection | 処理1 | staffCached = dataSource |
| openStaffConnection | 処理2 | dataSource = staffCached |
| openStaffConnection | 処理3 | DataSource dataSource = staffCached |
| openStaffConnection | 処理4 | DataSource dataSource = staffCached |
| openStaffConnection | 処理5 | dataSource = staffCached |
| openStaffConnection | 処理6 | staffCached = dataSource |
| openCustomerConnection | 処理1 | customerCached = dataSource |
| openCustomerConnection | 処理2 | dataSource = customerCached |
| openCustomerConnection | 処理3 | DataSource dataSource = customerCached |
| openCustomerConnection | 処理4 | DataSource dataSource = customerCached |
| openCustomerConnection | 処理5 | dataSource = customerCached |
| openCustomerConnection | 処理6 | customerCached = dataSource |
| lookup | 処理1 | failure.initCause(last) |
| lookup | 処理2 | SQLException failure = new SQLException(message) |
| lookup | 条件3 | int i = 0; i &lt; jndiNames.length; i++ |
| lookup | 処理4 | last = e |
| lookup | 条件5 | value instanceof DataSource |
| lookup | 処理6 | Object value = new InitialContext().lookup(jndiNames[i]) |
| lookup | 処理7 | NamingException last = null |
| lookup | 処理8 | NamingException last = null |
| lookup | 条件9 | int i = 0; i &lt; jndiNames.length; i++ |
| lookup | 処理10 | Object value = new InitialContext().lookup(jndiNames[i]) |
| lookup | 条件11 | value instanceof DataSource |
| lookup | 処理12 | last = e |
| lookup | 処理13 | SQLException failure = new SQLException(message) |
| lookup | 処理14 | failure.initCause(last) |
| lookup | 条件15 | int i = 0; i &lt; jndiNames.length; i++ |
| lookup | 条件16 | value instanceof DataSource |

