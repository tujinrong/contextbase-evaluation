# Access 年金データ Excel 出力の Open XML 置換

## 表紙

| 項目 | 内容 |
| --- | --- |
| 文書名 | 基本設計書 |
| システム名 |  |
| 機能ID | COM-144 |
| 画面名 | Access 年金データ Excel 出力の Open XML 置換 |
| 会社名 |  |
| 作成日 |  |


## 概要

### 概要説明

Access 年金データ Excel 出力の Open XML 置換の入力・表示・要求処理を行う。

| 情報 | 内容 |
| --- | --- |
| 対象種別 | common |
| 開始契機 | 呼出元からの要求 |
| 処理対象 | N2_SIGHT.Ｂ顧客基本表、受給有無テーブル、年金1_LK、年金種類テーブル、年金＿削除明細、店名テーブル、性別テーブル、裁定請求テーブル |


## 項目一覧

| No | グループ | 項目名 | 種類 | 入出力 | DB連携項目 | 候補取得元 | 必須 | 形式・桁 | 説明 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |

項目定義数：0項目。表示順と反復行の定義数を区別する。


## イベント仕様

### PensionExcelExportService

#### 処理概要

Access 年金データ Excel 出力の Open XML 置換で「PensionExcelExportService」の要求を受け付ける。入力・確認・データ操作・応答の順と、条件が成立しない場合の処理を以下に示す。

#### 処理手順

1. 関連する処理へ制御を渡す。詳細な実行経路は原本対応を参照する。

### PensionExcelExportService

#### 処理概要

Access 年金データ Excel 出力の Open XML 置換で「PensionExcelExportService」の要求を受け付ける。入力・確認・データ操作・応答の順と、条件が成立しない場合の処理を以下に示す。

#### 処理手順

1. 「対象項目がない」に該当するか確認する。該当する場合に限り、次の分岐内手順を行う。該当しない場合は分岐の後へ進む。

1.1. 条件成立時：処理の異常を通知し、この経路を終了する。この経路の後続手順は実行しない。

2. 関連情報を取得・設定する（処理2：詳細仕様参照）。

#### 結果・例外時の扱い

| 到達条件 | 結果 |
| --- | --- |
| 対象項目がない | 処理の異常を通知し、この経路を終了する |

### getInstance

#### 処理概要

Access 年金データ Excel 出力の Open XML 置換で「getInstance」の要求を受け付ける。入力・確認・データ操作・応答の順と、条件が成立しない場合の処理を以下に示す。

#### 処理手順

1. 処理結果を呼出元へ返す。この経路の後続手順は実行しない。

#### 結果・例外時の扱い

| 到達条件 | 結果 |
| --- | --- |
| この終了経路へ到達した場合 | 処理結果を呼出元へ返す |

### buildByBranch

#### 処理概要

Access 年金データ Excel 出力の Open XML 置換で「buildByBranch」の要求を受け付ける。入力・確認・データ操作・応答の順と、条件が成立しない場合の処理を以下に示す。

#### 処理手順

1. 関連情報を取得・設定する（処理6：詳細仕様参照）。

2. 「「対象項目」」に該当するか確認する。該当する場合に限り、次の分岐内手順を行う。該当しない場合は分岐の後へ進む。

2.1. 条件成立時：処理結果を呼出元へ返す。この経路の後続手順は実行しない。

3. 「６ヶ月先\n確認」を設定する。

4. 関連情報を取得・設定する（処理7：詳細仕様参照）。

5. 繰返し条件「条件8を満たす（原本条件は補足説明を参照）」に従い、次の手順を繰り返す。条件を満たさなくなった場合は繰返しの後へ進む。

5.1. 繰返しの各回：関連情報を取得・設定する（処理9：詳細仕様参照）。

5.2. 繰返しの各回：「確」を設定する。

6. 関連情報を取得・設定する（処理10：詳細仕様参照）。

7. 「年金データ_」を設定する。

8. 「年金ﾃﾞｰﾀ」を設定する。

9. 処理結果を呼出元へ返す。この経路の後続手順は実行しない。

#### DB操作の詳細

#### DB操作 SQL-1CC29D9EDFFF

| 情報 | 内容 |
| --- | --- |
| 操作ID | SQL-1CC29D9EDFFF |
| 対象テーブル | 年金1_LK |
| 操作 | 参照 |
| 処理説明 | 対象テーブルの対象データを読み取る。設定項目・対象条件・確定取消は以下の定義に従う。 |
| 設定項目 | 当該SQL式の列指定・実行時引数を使用する。組立式と原本のパラメーター設定を参照。 |
| 対象条件 | 抽出・更新対象条件：R.店番 = ? |
| 確定・取消 | 呼出側または接続の設定に従う。当該メソッド単独でのコミット・ロールバック指定はない。 同じ原本に明示トランザクションの呼出元があり、経路別の確定・取消範囲は関連処理で確認する。 |
| 原本 | nenkin/WEB-INF/src/nenkin/service/PensionRepository.java:224 / listByBranch@223 |

#### DB操作 SQL-28470D010AFF

| 情報 | 内容 |
| --- | --- |
| 操作ID | SQL-28470D010AFF |
| 対象テーブル | 店名テーブル |
| 操作 | 参照 |
| 処理説明 | 対象テーブルの対象データを読み取る。設定項目・対象条件・確定取消は以下の定義に従う。 |
| 設定項目 | 当該SQL式の列指定・実行時引数を使用する。組立式と原本のパラメーター設定を参照。 |
| 対象条件 | 抽出・更新対象条件：R.店番 = ? |
| 確定・取消 | 呼出側または接続の設定に従う。当該メソッド単独でのコミット・ロールバック指定はない。 同じ原本に明示トランザクションの呼出元があり、経路別の確定・取消範囲は関連処理で確認する。 |
| 原本 | nenkin/WEB-INF/src/nenkin/service/PensionRepository.java:224 / listByBranch@223 |

#### DB操作 SQL-0F5F7D3D4469

| 情報 | 内容 |
| --- | --- |
| 操作ID | SQL-0F5F7D3D4469 |
| 対象テーブル | 性別テーブル |
| 操作 | 参照 |
| 処理説明 | 対象テーブルの対象データを読み取る。設定項目・対象条件・確定取消は以下の定義に従う。 |
| 設定項目 | 当該SQL式の列指定・実行時引数を使用する。組立式と原本のパラメーター設定を参照。 |
| 対象条件 | 抽出・更新対象条件：R.店番 = ? |
| 確定・取消 | 呼出側または接続の設定に従う。当該メソッド単独でのコミット・ロールバック指定はない。 同じ原本に明示トランザクションの呼出元があり、経路別の確定・取消範囲は関連処理で確認する。 |
| 原本 | nenkin/WEB-INF/src/nenkin/service/PensionRepository.java:224 / listByBranch@223 |

#### DB操作 SQL-0E90141F3DE0

| 情報 | 内容 |
| --- | --- |
| 操作ID | SQL-0E90141F3DE0 |
| 対象テーブル | 裁定請求テーブル |
| 操作 | 参照 |
| 処理説明 | 対象テーブルの対象データを読み取る。設定項目・対象条件・確定取消は以下の定義に従う。 |
| 設定項目 | 当該SQL式の列指定・実行時引数を使用する。組立式と原本のパラメーター設定を参照。 |
| 対象条件 | 抽出・更新対象条件：R.店番 = ? |
| 確定・取消 | 呼出側または接続の設定に従う。当該メソッド単独でのコミット・ロールバック指定はない。 同じ原本に明示トランザクションの呼出元があり、経路別の確定・取消範囲は関連処理で確認する。 |
| 原本 | nenkin/WEB-INF/src/nenkin/service/PensionRepository.java:224 / listByBranch@223 |

#### DB操作 SQL-6597FFB0C483

| 情報 | 内容 |
| --- | --- |
| 操作ID | SQL-6597FFB0C483 |
| 対象テーブル | 受給有無テーブル |
| 操作 | 参照 |
| 処理説明 | 対象テーブルの対象データを読み取る。設定項目・対象条件・確定取消は以下の定義に従う。 |
| 設定項目 | 当該SQL式の列指定・実行時引数を使用する。組立式と原本のパラメーター設定を参照。 |
| 対象条件 | 抽出・更新対象条件：R.店番 = ? |
| 確定・取消 | 呼出側または接続の設定に従う。当該メソッド単独でのコミット・ロールバック指定はない。 同じ原本に明示トランザクションの呼出元があり、経路別の確定・取消範囲は関連処理で確認する。 |
| 原本 | nenkin/WEB-INF/src/nenkin/service/PensionRepository.java:224 / listByBranch@223 |

#### DB操作 SQL-87035C2BB1E0

| 情報 | 内容 |
| --- | --- |
| 操作ID | SQL-87035C2BB1E0 |
| 対象テーブル | 年金種類テーブル |
| 操作 | 参照 |
| 処理説明 | 対象テーブルの対象データを読み取る。設定項目・対象条件・確定取消は以下の定義に従う。 |
| 設定項目 | 当該SQL式の列指定・実行時引数を使用する。組立式と原本のパラメーター設定を参照。 |
| 対象条件 | 抽出・更新対象条件：R.店番 = ? |
| 確定・取消 | 呼出側または接続の設定に従う。当該メソッド単独でのコミット・ロールバック指定はない。 同じ原本に明示トランザクションの呼出元があり、経路別の確定・取消範囲は関連処理で確認する。 |
| 原本 | nenkin/WEB-INF/src/nenkin/service/PensionRepository.java:224 / listByBranch@223 |

#### DB操作 SQL-1A463E2BC06C

| 情報 | 内容 |
| --- | --- |
| 操作ID | SQL-1A463E2BC06C |
| 対象テーブル | 年金1_LK |
| 操作 | 挿入 |
| 処理説明 | 対象テーブルの新しい行を登録する。設定項目・対象条件・確定取消は以下の定義に従う。 |
| 設定項目 | 店番 ← バインド引数1（PreparedStatementまたは呼出側の設定順序）／顧客番号 ← バインド引数2（PreparedStatementまたは呼出側の設定順序）／担当者コード ← バインド引数3（PreparedStatementまたは呼出側の設定順序）／顧客氏名 ← バインド引数4（PreparedStatementまたは呼出側の設定順序）／ふりがな ← バインド引数5（PreparedStatementまたは呼出側の設定順序）／性別 ← バインド引数6（PreparedStatementまたは呼出側の設定順序）／住所 ← バインド引数7（PreparedStatementまたは呼出側の設定順序）／電話番号 ← バインド引数8（PreparedStatementまたは呼出側の設定順序）／生年月日 ← バインド引数9（PreparedStatementまたは呼出側の設定順序）／種類：国民年金 ← バインド引数10（PreparedStatementまたは呼出側の設定順序）／種類：厚生年金 ← バインド引数11（PreparedStatementまたは呼出側の設定順序）／種類：共済年金 ← バインド引数12（PreparedStatementまたは呼出側の設定順序）／種類：厚生年金基金 ← バインド引数13（PreparedStatementまたは呼出側の設定順序）／種類：国民年金基金 ← バインド引数14（PreparedStatementまたは呼出側の設定順序）／年金種類 ← バインド引数15（PreparedStatementまたは呼出側の設定順序）／裁定請求 ← バインド引数16（PreparedStatementまたは呼出側の設定順序）／請求予定日 ← バインド引数17（PreparedStatementまたは呼出側の設定順序）／予定年齢 ← バインド引数18（PreparedStatementまたは呼出側の設定順序）／配偶者名 ← バインド引数19（PreparedStatementまたは呼出側の設定順序）／配偶者生年月日 ← バインド引数20（PreparedStatementまたは呼出側の設定順序）／受給有無 ← バインド引数21（PreparedStatementまたは呼出側の設定順序）／予約徴求日 ← バインド引数22（PreparedStatementまたは呼出側の設定順序）／備考 ← バインド引数23（PreparedStatementまたは呼出側の設定順序）／データ更新日 ← バインド引数24（PreparedStatementまたは呼出側の設定順序）／更新時間 ← バインド引数25（PreparedStatementまたは呼出側の設定順序）／更新者 ← バインド引数26（PreparedStatementまたは呼出側の設定順序）／６ヶ月先確認 ← バインド引数27（PreparedStatementまたは呼出側の設定順序）／変更FLG ← バインド引数28（PreparedStatementまたは呼出側の設定順序） |
| 対象条件 | 新しい行を挿入する。重複や採番の扱いは呼出元および列制約に従う。 |
| 確定・取消 | 呼出側または接続の設定に従う。当該メソッド単独でのコミット・ロールバック指定はない。 同じ原本に明示トランザクションの呼出元があり、経路別の確定・取消範囲は関連処理で確認する。 |
| 原本 | nenkin/WEB-INF/src/nenkin/service/PensionRepository.java:661 / insert@657 |

| 設定先のDB項目 | バインド順 | 値の設定・変換（原本） |
| --- | --- | --- |
| 店番 | 1 | setInteger(statement, 1, value.getBranchNo()) |
| 顧客番号 | 2 | setInteger(statement, 2, value.getCustomerNo()) |
| 担当者コード | 3 | setInteger(statement, 3, value.getStaffCode()) |
| 顧客氏名 | 4 | value.getCustomerName() |
| ふりがな | 5 | value.getKanaName() |
| 性別 | 6 | setInteger(statement, 6, resolveCode(connection, GENDER_TABLE,<br>                "性別ｺｰﾄﾞ", "性別", value.getGender())) |
| 住所 | 7 | value.getAddress() |
| 電話番号 | 8 | setPhone(statement, 8, value.getPhoneNumber()) |
| 生年月日 | 9 | setDate(statement, 9, value.getBirthDate()) |
| 種類：国民年金 | 10 | value.isNationalPension() ? 1 : 0 |
| 種類：厚生年金 | 11 | value.isEmployeePension() ? 1 : 0 |
| 種類：共済年金 | 12 | value.isMutualAidPension() ? 1 : 0 |
| 種類：厚生年金基金 | 13 | value.isEmployeePensionFund() ? 1 : 0 |
| 種類：国民年金基金 | 14 | value.isNationalPensionFund() ? 1 : 0 |
| 年金種類 | 15 | setInteger(statement, 15, resolvePensionTypeCode(connection, value)) |
| 裁定請求 | 16 | setInteger(statement, 16, resolveCode(connection, CLAIM_TABLE,<br>                "裁請ｺｰﾄﾞ", "裁定請求", value.getClaimStatus())) |
| 請求予定日 | 17 | setDate(statement, 17, value.getClaimScheduledDate()) |
| 予定年齢 | 18 | setInteger(statement, 18, value.getPlannedAge()) |
| 配偶者名 | 19 | value.getSpouseName() |
| 配偶者生年月日 | 20 | setDate(statement, 20, value.getSpouseBirthDate()) |
| 受給有無 | 21 | setInteger(statement, 21, resolveCode(connection, BENEFIT_TABLE,<br>                "受給ｺｰﾄﾞ", "受給有無", value.getHasBenefit())) |
| 予約徴求日 | 22 | setDate(statement, 22, value.getReservationRequestDate()) |
| 備考 | 23 | value.getNotes() |
| データ更新日 | 24 | setDate(statement, 24, value.getDataUpdateDate()) |
| 更新時間 | 25 | setTime(statement, 25, updateTime) |
| 更新者 | 26 | setInteger(statement, 26, updatedBy) |
| ６ヶ月先確認 | 27 | value.isSixMonthCheck() ? 1 : 0 |
| 変更FLG | 28 | setInteger(statement, 28, Integer.valueOf(0)) |

#### 結果・例外時の扱い

| 到達条件 | 結果 |
| --- | --- |
| 「対象項目」 | 処理結果を呼出元へ返す |
| NOT (「対象項目」) | 処理結果を呼出元へ返す |

### threeDigits

#### 処理概要

Access 年金データ Excel 出力の Open XML 置換で「threeDigits」の要求を受け付ける。入力・確認・データ操作・応答の順と、条件が成立しない場合の処理を以下に示す。

#### 処理手順

1. 関連情報を取得・設定する（処理4：詳細仕様参照）。

2. 繰返し条件「条件5を満たす（原本条件は補足説明を参照）」に従い、次の手順を繰り返す。条件を満たさなくなった場合は繰返しの後へ進む。

2.1. 繰返しの各回：関連情報を取得・設定する（処理6：詳細仕様参照）。

3. 処理結果を呼出元へ返す。この経路の後続手順は実行しない。

#### 結果・例外時の扱い

| 到達条件 | 結果 |
| --- | --- |
| この終了経路へ到達した場合 | 処理結果を呼出元へ返す |

### DB関連処理


## 補足説明

### 適用条件

各仮定のQA番号を確認する。静的に確認できた操作・条件を適用する。

### 処理・条件の原本対応

文書内の条件番号・処理番号は次の原本表記に対応する。完全な業務用語への置換を行っていない箇所はQA・reportで確認する。

| イベント | 参照番号 | 原本条件・処理 |
| --- | --- | --- |
| PensionExcelExportService | 処理1 | this.repository = repository |
| PensionExcelExportService | 処理2 | this.repository = repository |
| buildByBranch | 処理1 | String compactDate = DateUtil.todayIso().replace("-", "") |
| buildByBranch | 条件2 | int i = 0; i &lt; reservations.size(); i++ |
| buildByBranch | 処理3 | PensionReservation row = reservations.get(i) |
| buildByBranch | 処理4 | List&lt;Object[]&gt; rows = new ArrayList&lt;Object[]&gt;() |
| buildByBranch | 処理5 | List&lt;PensionReservation&gt; reservations = repository.listByBranch(branchNo) |
| buildByBranch | 処理6 | List&lt;PensionReservation&gt; reservations = repository.listByBranch(branchNo) |
| buildByBranch | 処理7 | List&lt;Object[]&gt; rows = new ArrayList&lt;Object[]&gt;() |
| buildByBranch | 条件8 | int i = 0; i &lt; reservations.size(); i++ |
| buildByBranch | 処理9 | PensionReservation row = reservations.get(i) |
| buildByBranch | 処理10 | String compactDate = DateUtil.todayIso().replace("-", "") |
| threeDigits | 条件1 | text.length() &lt; 3 |
| threeDigits | 処理2 | text = "0" + text |
| threeDigits | 処理3 | String text = Integer.toString(value) |
| threeDigits | 処理4 | String text = Integer.toString(value) |
| threeDigits | 条件5 | text.length() &lt; 3 |
| threeDigits | 処理6 | text = "0" + text |

