# HTML表示共通処理

## 表紙

| 項目 | 内容 |
| --- | --- |
| 文書名 | 基本設計書 |
| システム名 |  |
| 機能ID | COM-149 |
| 画面名 | HTML表示共通処理 |
| 会社名 |  |
| 作成日 |  |


## 概要

### 概要説明

HTML表示共通処理の入力・表示・要求処理を行う。

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

### HtmlUtil

#### 処理概要

HTML表示共通処理で「HtmlUtil」の要求を受け付ける。入力・確認・データ操作・応答の順と、条件が成立しない場合の処理を以下に示す。

#### 処理手順

1. 関連する処理へ制御を渡す。詳細な実行経路は原本対応を参照する。

### escape

#### 処理概要

HTML表示共通処理で「escape」の要求を受け付ける。入力・確認・データ操作・応答の順と、条件が成立しない場合の処理を以下に示す。

#### 処理手順

1. 関連情報を取得・設定する（処理2：詳細仕様参照）。

2. 処理結果を呼出元へ返す。この経路の後続手順は実行しない。

#### 結果・例外時の扱い

| 到達条件 | 結果 |
| --- | --- |
| この終了経路へ到達した場合 | 処理結果を呼出元へ返す |

### value

#### 処理概要

HTML表示共通処理で「value」の要求を受け付ける。入力・確認・データ操作・応答の順と、条件が成立しない場合の処理を以下に示す。

#### 処理手順

1. 処理結果を呼出元へ返す。この経路の後続手順は実行しない。

#### 結果・例外時の扱い

| 到達条件 | 結果 |
| --- | --- |
| この終了経路へ到達した場合 | 処理結果を呼出元へ返す |

### checked

#### 処理概要

HTML表示共通処理で「checked」の要求を受け付ける。入力・確認・データ操作・応答の順と、条件が成立しない場合の処理を以下に示す。

#### 処理手順

1. 処理結果を呼出元へ返す。この経路の後続手順は実行しない。

#### 結果・例外時の扱い

| 到達条件 | 結果 |
| --- | --- |
| この終了経路へ到達した場合 | 処理結果を呼出元へ返す |

### selected

#### 処理概要

HTML表示共通処理で「selected」の要求を受け付ける。入力・確認・データ操作・応答の順と、条件が成立しない場合の処理を以下に示す。

#### 処理手順

1. 処理結果を呼出元へ返す。この経路の後続手順は実行しない。

#### 結果・例外時の扱い

| 到達条件 | 結果 |
| --- | --- |
| この終了経路へ到達した場合 | 処理結果を呼出元へ返す |

### selected

#### 処理概要

HTML表示共通処理で「selected」の要求を受け付ける。入力・確認・データ操作・応答の順と、条件が成立しない場合の処理を以下に示す。

#### 処理手順

1. 処理結果を呼出元へ返す。この経路の後続手順は実行しない。

#### 結果・例外時の扱い

| 到達条件 | 結果 |
| --- | --- |
| この終了経路へ到達した場合 | 処理結果を呼出元へ返す |

### formatWesternDate

#### 処理概要

HTML表示共通処理で「formatWesternDate」の要求を受け付ける。入力・確認・データ操作・応答の順と、条件が成立しない場合の処理を以下に示す。

#### 処理手順

1. 関連情報を取得・設定する（処理2：詳細仕様参照）。

2. 処理結果を呼出元へ返す。この経路の後続手順は実行しない。

#### 結果・例外時の扱い

| 到達条件 | 結果 |
| --- | --- |
| この終了経路へ到達した場合 | 処理結果を呼出元へ返す |

### formatJapaneseDate

#### 処理概要

HTML表示共通処理で「formatJapaneseDate」の要求を受け付ける。入力・確認・データ操作・応答の順と、条件が成立しない場合の処理を以下に示す。

#### 処理手順

1. 関連情報を取得・設定する（処理22：詳細仕様参照）。

2. 「対象項目がない」に該当するか確認する。該当する場合に限り、次の分岐内手順を行う。該当しない場合は分岐の後へ進む。

2.1. 条件成立時：処理結果を呼出元へ返す。この経路の後続手順は実行しない。

3. 「対象項目」を設定する。

4. 関連情報を取得・設定する（処理23：詳細仕様参照）。

5. 関連情報を取得・設定する（処理24：詳細仕様参照）。

6. 関連情報を取得・設定する（処理25：詳細仕様参照）。

7. 関連情報を取得・設定する（処理26：詳細仕様参照）。

8. 関連情報を取得・設定する（処理27：詳細仕様参照）。

9. 「条件28を満たす（原本条件は補足説明を参照）」に該当するか確認する。成立時と不成立時の手順を分けて行う。

9.1. 条件成立時：関連情報を取得・設定する（処理29：詳細仕様参照）。

9.2. 条件成立時：関連情報を取得・設定する（処理30：詳細仕様参照）。

9-別.1. 条件不成立時：「条件31を満たす（原本条件は補足説明を参照）」に該当するか確認する。成立時と不成立時の手順を分けて行う。

9-別.1.1. 条件成立時：関連情報を取得・設定する（処理32：詳細仕様参照）。

9-別.1.2. 条件成立時：関連情報を取得・設定する（処理33：詳細仕様参照）。

9-別.1-別.1. 条件不成立時：「条件34を満たす（原本条件は補足説明を参照）」に該当するか確認する。成立時と不成立時の手順を分けて行う。

9-別.1-別.1.1. 条件成立時：関連情報を取得・設定する（処理35：詳細仕様参照）。

9-別.1-別.1.2. 条件成立時：関連情報を取得・設定する（処理36：詳細仕様参照）。

9-別.1-別.1-別.1. 条件不成立時：「条件37を満たす（原本条件は補足説明を参照）」に該当するか確認する。成立時と不成立時の手順を分けて行う。

9-別.1-別.1-別.1.1. 条件成立時：関連情報を取得・設定する（処理38：詳細仕様参照）。

9-別.1-別.1-別.1.2. 条件成立時：関連情報を取得・設定する（処理39：詳細仕様参照）。

9-別.1-別.1-別.1-別.1. 条件不成立時：「条件40を満たす（原本条件は補足説明を参照）」に該当するか確認する。成立時と不成立時の手順を分けて行う。

9-別.1-別.1-別.1-別.1.1. 条件成立時：関連情報を取得・設定する（処理41：詳細仕様参照）。

9-別.1-別.1-別.1-別.1.2. 条件成立時：関連情報を取得・設定する（処理42：詳細仕様参照）。

9-別.1-別.1-別.1-別.1-別.1. 条件不成立時：処理結果を呼出元へ返す。この経路の後続手順は実行しない。

10. 処理結果を呼出元へ返す。この経路の後続手順は実行しない。

#### 結果・例外時の扱い

| 到達条件 | 結果 |
| --- | --- |
| 対象項目がない | 処理結果を呼出元へ返す |
| NOT (date  が等しい  未設定)・条件43を満たす（原本条件は補足説明を参照）・条件44を満たす（原本条件は補足説明を参照）・条件45を満たす（原本条件は補足説明を参照）・条件46を満たす（原本条件は補足説明を参照）・条件47を満たす（原本条件は補足説明を参照） | 処理結果を呼出元へ返す |
| NOT (date  が等しい  未設定) | 処理結果を呼出元へ返す |

### formatReportDate

#### 処理概要

HTML表示共通処理で「formatReportDate」の要求を受け付ける。入力・確認・データ操作・応答の順と、条件が成立しない場合の処理を以下に示す。

#### 処理手順

1. 処理結果を呼出元へ返す。この経路の後続手順は実行しない。

#### 結果・例外時の扱い

| 到達条件 | 結果 |
| --- | --- |
| この終了経路へ到達した場合 | 処理結果を呼出元へ返す |

### json

#### 処理概要

HTML表示共通処理で「json」の要求を受け付ける。入力・確認・データ操作・応答の順と、条件が成立しない場合の処理を以下に示す。

#### 処理手順

1. 「対象項目がない」に該当するか確認する。該当する場合に限り、次の分岐内手順を行う。該当しない場合は分岐の後へ進む。

1.1. 条件成立時：処理結果を呼出元へ返す。この経路の後続手順は実行しない。

2. 関連情報を取得・設定する（処理5：詳細仕様参照）。

3. 繰返し条件「条件6を満たす（原本条件は補足説明を参照）」に従い、次の手順を繰り返す。条件を満たさなくなった場合は繰返しの後へ進む。

3.1. 繰返しの各回：関連情報を取得・設定する（処理7：詳細仕様参照）。

3.2. 繰返しの各回：値に応じた分岐の詳細は原本対応を参照する。

4. 処理結果を呼出元へ返す。この経路の後続手順は実行しない。

#### 結果・例外時の扱い

| 到達条件 | 結果 |
| --- | --- |
| 対象項目がない | 処理結果を呼出元へ返す |
| NOT (value  が等しい  未設定) | 処理結果を呼出元へ返す |

### parseIso

#### 処理概要

HTML表示共通処理で「parseIso」の要求を受け付ける。入力・確認・データ操作・応答の順と、条件が成立しない場合の処理を以下に示す。

#### 処理手順

1. 「対象項目がない、またはvalue.trim().length()  が等しい  0」に該当するか確認する。該当する場合に限り、次の分岐内手順を行う。該当しない場合は分岐の後へ進む。

1.1. 条件成立時：戻り先画面を指定せず処理を終了する。この経路の後続手順は実行しない。

2. 関連情報を取得・設定する（処理2：詳細仕様参照）。

3. 「対象項目」を設定する。

4. 通常処理と例外時の処理を区別して実行する。例外処理は対応する例外が発生した場合に限る。

4.1. 通常処理：処理結果を呼出元へ返す。この経路の後続手順は実行しない。

4-例外1. 例外条件「ParseException e」に該当した場合に次の手順を行う。型名は原本の表記。

4-例外1.1. 例外発生時：戻り先画面を指定せず処理を終了する。この経路の後続手順は実行しない。

#### 結果・例外時の扱い

| 到達条件 | 結果 |
| --- | --- |
| 対象項目がない、またはvalue.trim().length()  が等しい  0 | 戻り先画面を指定せず処理を終了する |
| NOT (value  が等しい  未設定 &#124;&#124; value.trim().length()  が等しい  0) | 処理結果を呼出元へ返す |
| NOT (value  が等しい  未設定 &#124;&#124; value.trim().length()  が等しい  0)・条件3を満たす（原本条件は補足説明を参照） | 戻り先画面を指定せず処理を終了する |

### two

#### 処理概要

HTML表示共通処理で「two」の要求を受け付ける。入力・確認・データ操作・応答の順と、条件が成立しない場合の処理を以下に示す。

#### 処理手順

1. 処理結果を呼出元へ返す。この経路の後続手順は実行しない。

#### 結果・例外時の扱い

| 到達条件 | 結果 |
| --- | --- |
| この終了経路へ到達した場合 | 処理結果を呼出元へ返す |


## 補足説明

### 適用条件

各仮定のQA番号を確認する。静的に確認できた操作・条件を適用する。

### 処理・条件の原本対応

文書内の条件番号・処理番号は次の原本表記に対応する。完全な業務用語への置換を行っていない箇所はQA・reportで確認する。

| イベント | 参照番号 | 原本条件・処理 |
| --- | --- | --- |
| escape | 処理1 | String text = value == null ? "" : String.valueOf(value) |
| escape | 処理2 | String text = value == null ? "" : String.valueOf(value) |
| formatWesternDate | 処理1 | Date date = parseIso(value) |
| formatWesternDate | 処理2 | Date date = parseIso(value) |
| formatJapaneseDate | 処理1 | eraYear = year - 2018 |
| formatJapaneseDate | 処理2 | symbol = "R" |
| formatJapaneseDate | 処理3 | eraYear = year - 1988 |
| formatJapaneseDate | 処理4 | symbol = "H" |
| formatJapaneseDate | 処理5 | eraYear = year - 1925 |
| formatJapaneseDate | 処理6 | symbol = "S" |
| formatJapaneseDate | 処理7 | eraYear = year - 1911 |
| formatJapaneseDate | 処理8 | symbol = "T" |
| formatJapaneseDate | 処理9 | eraYear = year - 1867 |
| formatJapaneseDate | 処理10 | symbol = "M" |
| formatJapaneseDate | 条件11 | !date.before(parseIso("1868-09-08")) |
| formatJapaneseDate | 条件12 | !date.before(parseIso("1912-07-30")) |
| formatJapaneseDate | 条件13 | !date.before(parseIso("1926-12-25")) |
| formatJapaneseDate | 条件14 | !date.before(parseIso("1989-01-08")) |
| formatJapaneseDate | 条件15 | !date.before(parseIso("2019-05-01")) |
| formatJapaneseDate | 処理16 | int eraYear |
| formatJapaneseDate | 処理17 | String symbol |
| formatJapaneseDate | 処理18 | int day = target.get(Calendar.DAY_OF_MONTH) |
| formatJapaneseDate | 処理19 | int month = target.get(Calendar.MONTH) + 1 |
| formatJapaneseDate | 処理20 | int year = target.get(Calendar.YEAR) |
| formatJapaneseDate | 処理21 | Date date = parseIso(value) |
| formatJapaneseDate | 処理22 | Date date = parseIso(value) |
| formatJapaneseDate | 処理23 | int year = target.get(Calendar.YEAR) |
| formatJapaneseDate | 処理24 | int month = target.get(Calendar.MONTH) + 1 |
| formatJapaneseDate | 処理25 | int day = target.get(Calendar.DAY_OF_MONTH) |
| formatJapaneseDate | 処理26 | String symbol |
| formatJapaneseDate | 処理27 | int eraYear |
| formatJapaneseDate | 条件28 | !date.before(parseIso("2019-05-01")) |
| formatJapaneseDate | 処理29 | symbol = "R" |
| formatJapaneseDate | 処理30 | eraYear = year - 2018 |
| formatJapaneseDate | 条件31 | !date.before(parseIso("1989-01-08")) |
| formatJapaneseDate | 処理32 | symbol = "H" |
| formatJapaneseDate | 処理33 | eraYear = year - 1988 |
| formatJapaneseDate | 条件34 | !date.before(parseIso("1926-12-25")) |
| formatJapaneseDate | 処理35 | symbol = "S" |
| formatJapaneseDate | 処理36 | eraYear = year - 1925 |
| formatJapaneseDate | 条件37 | !date.before(parseIso("1912-07-30")) |
| formatJapaneseDate | 処理38 | symbol = "T" |
| formatJapaneseDate | 処理39 | eraYear = year - 1911 |
| formatJapaneseDate | 条件40 | !date.before(parseIso("1868-09-08")) |
| formatJapaneseDate | 処理41 | symbol = "M" |
| formatJapaneseDate | 処理42 | eraYear = year - 1867 |
| formatJapaneseDate | 条件43 | NOT (!date.before(parseIso("2019-05-01"))) |
| formatJapaneseDate | 条件44 | NOT (!date.before(parseIso("1989-01-08"))) |
| formatJapaneseDate | 条件45 | NOT (!date.before(parseIso("1926-12-25"))) |
| formatJapaneseDate | 条件46 | NOT (!date.before(parseIso("1912-07-30"))) |
| formatJapaneseDate | 条件47 | NOT (!date.before(parseIso("1868-09-08"))) |
| json | 条件1 | int i = 0; i &lt; value.length(); i++ |
| json | 例外 | c |
| json | 処理3 | char c = value.charAt(i) |
| json | 処理4 | StringBuilder result = new StringBuilder() |
| json | 処理5 | StringBuilder result = new StringBuilder() |
| json | 条件6 | int i = 0; i &lt; value.length(); i++ |
| json | 処理7 | char c = value.charAt(i) |
| parseIso | 処理1 | SimpleDateFormat format = new SimpleDateFormat("yyyy-MM-dd") |
| parseIso | 処理2 | SimpleDateFormat format = new SimpleDateFormat("yyyy-MM-dd") |
| parseIso | 条件3 | ParseException e |

