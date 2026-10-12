# Webon汎用照会クラス 顧客結合照会汎用管理クラス 顧客結合照会(XML)の取得とデータ管理、アクセスメソッドの提供

## 表紙

| 項目 | 内容 |
| --- | --- |
| 文書名 | 基本設計書 |
| システム名 |  |
| 機能ID | COM-076 |
| 画面名 | Webon汎用照会クラス 顧客結合照会汎用管理クラス 顧客結合照会(XML)の取得とデータ管理、アクセスメソッドの提供 |
| 会社名 |  |
| 作成日 |  |


## 概要

### 概要説明

Webon汎用照会クラス 顧客結合照会汎用管理クラス 顧客結合照会(XML)の取得とデータ管理、アクセスメソッドの提供の入力・表示・要求処理を行う。

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

### getEtc

#### 処理概要

Webon汎用照会クラス 顧客結合照会汎用管理クラス 顧客結合照会(XML)の取得とデータ管理、アクセスメソッドの提供で「getEtc」の要求を受け付ける。入力・確認・データ操作・応答の順と、条件が成立しない場合の処理を以下に示す。

#### 処理手順

1. 処理結果を呼出元へ返す。この経路の後続手順は実行しない。

#### 結果・例外時の扱い

| 到達条件 | 結果 |
| --- | --- |
| この終了経路へ到達した場合 | 処理結果を呼出元へ返す |

### setEtc

#### 処理概要

Webon汎用照会クラス 顧客結合照会汎用管理クラス 顧客結合照会(XML)の取得とデータ管理、アクセスメソッドの提供で「setEtc」の要求を受け付ける。入力・確認・データ操作・応答の順と、条件が成立しない場合の処理を以下に示す。

#### 処理手順

1. 関連情報を取得・設定する（処理2：詳細仕様参照）。

### isErrFlg

#### 処理概要

Webon汎用照会クラス 顧客結合照会汎用管理クラス 顧客結合照会(XML)の取得とデータ管理、アクセスメソッドの提供で「isErrFlg」の要求を受け付ける。入力・確認・データ操作・応答の順と、条件が成立しない場合の処理を以下に示す。

#### 処理手順

1. 処理結果を呼出元へ返す。この経路の後続手順は実行しない。

#### 結果・例外時の扱い

| 到達条件 | 結果 |
| --- | --- |
| この終了経路へ到達した場合 | 処理結果を呼出元へ返す |

### setErrFlg

#### 処理概要

Webon汎用照会クラス 顧客結合照会汎用管理クラス 顧客結合照会(XML)の取得とデータ管理、アクセスメソッドの提供で「setErrFlg」の要求を受け付ける。入力・確認・データ操作・応答の順と、条件が成立しない場合の処理を以下に示す。

#### 処理手順

1. 関連情報を取得・設定する（処理2：詳細仕様参照）。

### getCustomerUnionList

#### 処理概要

Webon汎用照会クラス 顧客結合照会汎用管理クラス 顧客結合照会(XML)の取得とデータ管理、アクセスメソッドの提供で「getCustomerUnionList」の要求を受け付ける。入力・確認・データ操作・応答の順と、条件が成立しない場合の処理を以下に示す。

#### 処理手順

1. 処理結果を呼出元へ返す。この経路の後続手順は実行しない。

#### 結果・例外時の扱い

| 到達条件 | 結果 |
| --- | --- |
| この終了経路へ到達した場合 | 処理結果を呼出元へ返す |

### setCustomerUnionList

#### 処理概要

Webon汎用照会クラス 顧客結合照会汎用管理クラス 顧客結合照会(XML)の取得とデータ管理、アクセスメソッドの提供で「setCustomerUnionList」の要求を受け付ける。入力・確認・データ操作・応答の順と、条件が成立しない場合の処理を以下に示す。

#### 処理手順

1. 関連情報を取得・設定する（処理2：詳細仕様参照）。

### getWoCif

#### 処理概要

Webon汎用照会クラス 顧客結合照会汎用管理クラス 顧客結合照会(XML)の取得とデータ管理、アクセスメソッドの提供で「getWoCif」の要求を受け付ける。入力・確認・データ操作・応答の順と、条件が成立しない場合の処理を以下に示す。

#### 処理手順

1. 処理結果を呼出元へ返す。この経路の後続手順は実行しない。

#### 結果・例外時の扱い

| 到達条件 | 結果 |
| --- | --- |
| この終了経路へ到達した場合 | 処理結果を呼出元へ返す |

### setWoCif

#### 処理概要

Webon汎用照会クラス 顧客結合照会汎用管理クラス 顧客結合照会(XML)の取得とデータ管理、アクセスメソッドの提供で「setWoCif」の要求を受け付ける。入力・確認・データ操作・応答の順と、条件が成立しない場合の処理を以下に示す。

#### 処理手順

1. 関連情報を取得・設定する（処理2：詳細仕様参照）。

### getWoBrno

#### 処理概要

Webon汎用照会クラス 顧客結合照会汎用管理クラス 顧客結合照会(XML)の取得とデータ管理、アクセスメソッドの提供で「getWoBrno」の要求を受け付ける。入力・確認・データ操作・応答の順と、条件が成立しない場合の処理を以下に示す。

#### 処理手順

1. 処理結果を呼出元へ返す。この経路の後続手順は実行しない。

#### 結果・例外時の扱い

| 到達条件 | 結果 |
| --- | --- |
| この終了経路へ到達した場合 | 処理結果を呼出元へ返す |

### setWoBrno

#### 処理概要

Webon汎用照会クラス 顧客結合照会汎用管理クラス 顧客結合照会(XML)の取得とデータ管理、アクセスメソッドの提供で「setWoBrno」の要求を受け付ける。入力・確認・データ操作・応答の順と、条件が成立しない場合の処理を以下に示す。

#### 処理手順

1. 関連情報を取得・設定する（処理2：詳細仕様参照）。

### get店番

#### 処理概要

Webon汎用照会クラス 顧客結合照会汎用管理クラス 顧客結合照会(XML)の取得とデータ管理、アクセスメソッドの提供で「get店番」の要求を受け付ける。入力・確認・データ操作・応答の順と、条件が成立しない場合の処理を以下に示す。

#### 処理手順

1. 処理結果を呼出元へ返す。この経路の後続手順は実行しない。

#### 結果・例外時の扱い

| 到達条件 | 結果 |
| --- | --- |
| この終了経路へ到達した場合 | 処理結果を呼出元へ返す |

### set店番

#### 処理概要

Webon汎用照会クラス 顧客結合照会汎用管理クラス 顧客結合照会(XML)の取得とデータ管理、アクセスメソッドの提供で「set店番」の要求を受け付ける。入力・確認・データ操作・応答の順と、条件が成立しない場合の処理を以下に示す。

#### 処理手順

1. 関連情報を取得・設定する（処理2：詳細仕様参照）。

### get顧客番号

#### 処理概要

Webon汎用照会クラス 顧客結合照会汎用管理クラス 顧客結合照会(XML)の取得とデータ管理、アクセスメソッドの提供で「get顧客番号」の要求を受け付ける。入力・確認・データ操作・応答の順と、条件が成立しない場合の処理を以下に示す。

#### 処理手順

1. 処理結果を呼出元へ返す。この経路の後続手順は実行しない。

#### 結果・例外時の扱い

| 到達条件 | 結果 |
| --- | --- |
| この終了経路へ到達した場合 | 処理結果を呼出元へ返す |

### set顧客番号

#### 処理概要

Webon汎用照会クラス 顧客結合照会汎用管理クラス 顧客結合照会(XML)の取得とデータ管理、アクセスメソッドの提供で「set顧客番号」の要求を受け付ける。入力・確認・データ操作・応答の順と、条件が成立しない場合の処理を以下に示す。

#### 処理手順

1. 関連情報を取得・設定する（処理2：詳細仕様参照）。

### get科目

#### 処理概要

Webon汎用照会クラス 顧客結合照会汎用管理クラス 顧客結合照会(XML)の取得とデータ管理、アクセスメソッドの提供で「get科目」の要求を受け付ける。入力・確認・データ操作・応答の順と、条件が成立しない場合の処理を以下に示す。

#### 処理手順

1. 処理結果を呼出元へ返す。この経路の後続手順は実行しない。

#### 結果・例外時の扱い

| 到達条件 | 結果 |
| --- | --- |
| この終了経路へ到達した場合 | 処理結果を呼出元へ返す |

### set科目

#### 処理概要

Webon汎用照会クラス 顧客結合照会汎用管理クラス 顧客結合照会(XML)の取得とデータ管理、アクセスメソッドの提供で「set科目」の要求を受け付ける。入力・確認・データ操作・応答の順と、条件が成立しない場合の処理を以下に示す。

#### 処理手順

1. 関連情報を取得・設定する（処理2：詳細仕様参照）。

### get科目符号

#### 処理概要

Webon汎用照会クラス 顧客結合照会汎用管理クラス 顧客結合照会(XML)の取得とデータ管理、アクセスメソッドの提供で「get科目符号」の要求を受け付ける。入力・確認・データ操作・応答の順と、条件が成立しない場合の処理を以下に示す。

#### 処理手順

1. 処理結果を呼出元へ返す。この経路の後続手順は実行しない。

#### 結果・例外時の扱い

| 到達条件 | 結果 |
| --- | --- |
| この終了経路へ到達した場合 | 処理結果を呼出元へ返す |

### set科目符号

#### 処理概要

Webon汎用照会クラス 顧客結合照会汎用管理クラス 顧客結合照会(XML)の取得とデータ管理、アクセスメソッドの提供で「set科目符号」の要求を受け付ける。入力・確認・データ操作・応答の順と、条件が成立しない場合の処理を以下に示す。

#### 処理手順

1. 関連情報を取得・設定する（処理2：詳細仕様参照）。

### get口座番号預り番号

#### 処理概要

Webon汎用照会クラス 顧客結合照会汎用管理クラス 顧客結合照会(XML)の取得とデータ管理、アクセスメソッドの提供で「get口座番号預り番号」の要求を受け付ける。入力・確認・データ操作・応答の順と、条件が成立しない場合の処理を以下に示す。

#### 処理手順

1. 処理結果を呼出元へ返す。この経路の後続手順は実行しない。

#### 結果・例外時の扱い

| 到達条件 | 結果 |
| --- | --- |
| この終了経路へ到達した場合 | 処理結果を呼出元へ返す |

### set口座番号預り番号

#### 処理概要

Webon汎用照会クラス 顧客結合照会汎用管理クラス 顧客結合照会(XML)の取得とデータ管理、アクセスメソッドの提供で「set口座番号預り番号」の要求を受け付ける。入力・確認・データ操作・応答の順と、条件が成立しない場合の処理を以下に示す。

#### 処理手順

1. 関連情報を取得・設定する（処理2：詳細仕様参照）。

### getWebonByCif

#### 処理概要

Webon汎用照会クラス 顧客結合照会汎用管理クラス 顧客結合照会(XML)の取得とデータ管理、アクセスメソッドの提供で「getWebonByCif」の要求を受け付ける。入力・確認・データ操作・応答の順と、条件が成立しない場合の処理を以下に示す。

#### 処理手順

1. 通常処理と例外時の処理を区別して実行する。例外処理は対応する例外が発生した場合に限る。

1.1. 通常処理：「対象項目がない」に該当するか確認する。該当する場合に限り、次の分岐内手順を行う。該当しない場合は分岐の後へ進む。

1.1.1. 条件成立時：処理の異常を通知し、この経路を終了する。この経路の後続手順は実行しない。

1.2. 通常処理：「対象項目がない」に該当するか確認する。該当する場合に限り、次の分岐内手順を行う。該当しない場合は分岐の後へ進む。

1.2.1. 条件成立時：処理の異常を通知し、この経路を終了する。この経路の後続手順は実行しない。

1.3. 通常処理：「対象項目がない」に該当するか確認する。該当する場合に限り、次の分岐内手順を行う。該当しない場合は分岐の後へ進む。

1.3.1. 条件成立時：処理の異常を通知し、この経路を終了する。この経路の後続手順は実行しない。

1.4. 通常処理：関連情報を取得・設定する（処理6：詳細仕様参照）。

1.5. 通常処理：関連情報を取得・設定する（処理7：詳細仕様参照）。

1.6. 通常処理：関連情報を取得・設定する（処理8：詳細仕様参照）。

1.7. 通常処理：関連情報を取得・設定する（処理9：詳細仕様参照）。

1.8. 通常処理：関連情報を取得・設定する（処理10：詳細仕様参照）。

1-例外1. 例外条件「WebonException e」に該当した場合に次の手順を行う。型名は原本の表記。

1-例外1.1. 例外発生時：処理の異常を通知し、この経路を終了する。この経路の後続手順は実行しない。

1-例外2. 例外条件「Exception e」に該当した場合に次の手順を行う。型名は原本の表記。

1-例外2.1. 例外発生時：処理の異常を通知し、この経路を終了する。この経路の後続手順は実行しない。

#### 結果・例外時の扱い

| 到達条件 | 結果 |
| --- | --- |
| 対象項目がない | 処理の異常を通知し、この経路を終了する |
| NOT (cif  が等しい  未設定)・対象項目がない | 処理の異常を通知し、この経路を終了する |
| NOT (cif  が等しい  未設定)・NOT (br  が等しい  未設定)・対象項目がない | 処理の異常を通知し、この経路を終了する |
| 条件11を満たす（原本条件は補足説明を参照） | 処理の異常を通知し、この経路を終了する |
| 条件12を満たす（原本条件は補足説明を参照） | 処理の異常を通知し、この経路を終了する |

### getWebon

#### 処理概要

Webon汎用照会クラス 顧客結合照会汎用管理クラス 顧客結合照会(XML)の取得とデータ管理、アクセスメソッドの提供で「getWebon」の要求を受け付ける。入力・確認・データ操作・応答の順と、条件が成立しない場合の処理を以下に示す。

#### 処理手順

1. 業務連携基盤を実行する。

2. 「顧客番号」を設定する。

3. 「原店番号」を設定する。

4. 関連情報を取得・設定する（処理2：詳細仕様参照）。

5. 「入力値の制約と変換結果が成立しない」に該当するか確認する。該当する場合に限り、次の分岐内手順を行う。該当しない場合は分岐の後へ進む。

5.1. 条件成立時：「Webon取得結果エラー」を設定する。

5.2. 条件成立時：処理の異常を通知し、この経路を終了する。この経路の後続手順は実行しない。

#### 結果・例外時の扱い

| 到達条件 | 結果 |
| --- | --- |
| 入力値の制約と変換結果が成立しない | 処理の異常を通知し、この経路を終了する |

### analyzeWeon

#### 処理概要

Webon汎用照会クラス 顧客結合照会汎用管理クラス 顧客結合照会(XML)の取得とデータ管理、アクセスメソッドの提供で「analyzeWeon」の要求を受け付ける。入力・確認・データ操作・応答の順と、条件が成立しない場合の処理を以下に示す。

#### 処理手順

1. 「通帳部宛」を設定する。

2. 「顧客結合照会」を設定する。

3. 「明細行」を設定する。

4. 「顧客番号」を設定する。

5. 「店番」を設定する。

6. 関連情報を取得・設定する（処理48：詳細仕様参照）。

7. 関連情報を取得・設定する（処理49：詳細仕様参照）。

8. 関連情報を取得・設定する（処理50：詳細仕様参照）。

9. 繰返し条件「条件51を満たす（原本条件は補足説明を参照）」に従い、次の手順を繰り返す。条件を満たさなくなった場合は繰返しの後へ進む。

9.1. 繰返しの各回：「対象項目がない」に該当するか確認する。該当する場合に限り、次の分岐内手順を行う。該当しない場合は分岐の後へ進む。

9.1.1. 条件成立時：関連情報を取得・設定する（処理52：詳細仕様参照）。

9.2. 繰返しの各回：「「対象項目」 が等しい Node.ELEMENT_NODE」に該当するか確認する。該当する場合に限り、次の分岐内手順を行う。該当しない場合は分岐の後へ進む。

9.2.1. 条件成立時：「「対象項目」.equals(WOKEY_TSUCYO)」に該当するか確認する。該当する場合に限り、次の分岐内手順を行う。該当しない場合は分岐の後へ進む。

9.2.1.1. 条件成立時：関連情報を取得・設定する（処理53：詳細仕様参照）。

9.2.1.2. 条件成立時：繰返し条件「条件54を満たす（原本条件は補足説明を参照）」に従い、次の手順を繰り返す。条件を満たさなくなった場合は繰返しの後へ進む。

9.2.1.2.1. 繰返しの各回：「対象項目がない」に該当するか確認する。該当する場合に限り、次の分岐内手順を行う。該当しない場合は分岐の後へ進む。

9.2.1.2.1.1. 条件成立時：関連情報を取得・設定する（処理55：詳細仕様参照）。

9.2.1.2.2. 繰返しの各回：「「対象項目」 が等しい Node.ELEMENT_NODE」に該当するか確認する。該当する場合に限り、次の分岐内手順を行う。該当しない場合は分岐の後へ進む。

9.2.1.2.2.1. 条件成立時：「「対象項目」.equals(WOKEY_KETSUGO)」に該当するか確認する。該当する場合に限り、次の分岐内手順を行う。該当しない場合は分岐の後へ進む。

9.2.1.2.2.1.1. 条件成立時：関連情報を取得・設定する（処理56：詳細仕様参照）。

9.2.1.2.3. 繰返しの各回：関連情報を取得・設定する（処理57：詳細仕様参照）。

9.2.1.3. 条件成立時：関連情報を取得・設定する（処理58：詳細仕様参照）。

9.3. 繰返しの各回：関連情報を取得・設定する（処理59：詳細仕様参照）。

10. 関連情報を取得・設定する（処理60：詳細仕様参照）。

11. 関連情報を取得・設定する（処理61：詳細仕様参照）。

12. 関連情報を取得・設定する（処理62：詳細仕様参照）。

13. 関連情報を取得・設定する（処理63：詳細仕様参照）。

14. 繰返し条件「条件64を満たす（原本条件は補足説明を参照）」に従い、次の手順を繰り返す。条件を満たさなくなった場合は繰返しの後へ進む。

14.1. 繰返しの各回：「対象項目がない」に該当するか確認する。該当する場合に限り、次の分岐内手順を行う。該当しない場合は分岐の後へ進む。

14.1.1. 条件成立時：関連情報を取得・設定する（処理65：詳細仕様参照）。

14.2. 繰返しの各回：「「対象項目」 が等しい Node.ELEMENT_NODE」に該当するか確認する。該当する場合に限り、次の分岐内手順を行う。該当しない場合は分岐の後へ進む。

14.2.1. 条件成立時：「「対象項目」.equals(WOKEY_ROOP)」に該当するか確認する。成立時と不成立時の手順を分けて行う。

14.2.1.1. 条件成立時：関連情報を取得・設定する（処理66：詳細仕様参照）。

14.2.1-別.1. 条件不成立時：「「対象項目」.equals(DBKEY_BRANCHNO)」に該当するか確認する。成立時と不成立時の手順を分けて行う。

14.2.1-別.1.1. 条件成立時：「条件67を満たす（原本条件は補足説明を参照）」に該当するか確認する。成立時と不成立時の手順を分けて行う。

14.2.1-別.1.1.1. 条件成立時：関連情報を取得・設定する（処理68：詳細仕様参照）。

14.2.1-別.1.1-別.1. 条件不成立時：「Webon取得結果解析エラー」を設定する。

14.2.1-別.1.1-別.2. 条件不成立時：関連情報を取得・設定する（処理69：詳細仕様参照）。

14.2.1-別.1.1-別.3. 条件不成立時：「店番」を設定する。

14.2.1-別.1.1-別.4. 条件不成立時：関連情報を取得・設定する（処理70：詳細仕様参照）。

14.2.1-別.1.1-別.5. 条件不成立時：「対象項目」を設定する。

14.2.1-別.1.1-別.6. 条件不成立時：処理の異常を通知し、この経路を終了する。この経路の後続手順は実行しない。

14.2.1-別.1-別.1. 条件不成立時：「「対象項目」.equals(DBKEY_CUSTNO)」に該当するか確認する。該当する場合に限り、次の分岐内手順を行う。該当しない場合は分岐の後へ進む。

14.2.1-別.1-別.1.1. 条件成立時：「条件71を満たす（原本条件は補足説明を参照）」に該当するか確認する。成立時と不成立時の手順を分けて行う。

14.2.1-別.1-別.1.1.1. 条件成立時：関連情報を取得・設定する（処理72：詳細仕様参照）。

14.2.1-別.1-別.1.1-別.1. 条件不成立時：「Webon取得結果解析エラー」を設定する。

14.2.1-別.1-別.1.1-別.2. 条件不成立時：関連情報を取得・設定する（処理73：詳細仕様参照）。

14.2.1-別.1-別.1.1-別.3. 条件不成立時：「顧客番号」を設定する。

14.2.1-別.1-別.1.1-別.4. 条件不成立時：関連情報を取得・設定する（処理74：詳細仕様参照）。

14.2.1-別.1-別.1.1-別.5. 条件不成立時：「対象項目」を設定する。

14.2.1-別.1-別.1.1-別.6. 条件不成立時：処理の異常を通知し、この経路を終了する。この経路の後続手順は実行しない。

14.3. 繰返しの各回：関連情報を取得・設定する（処理75：詳細仕様参照）。

15. 繰返し条件「条件76を満たす（原本条件は補足説明を参照）」に従い、次の手順を繰り返す。条件を満たさなくなった場合は繰返しの後へ進む。

15.1. 繰返しの各回：関連情報を取得・設定する（処理77：詳細仕様参照）。

15.2. 繰返しの各回：繰返し条件「条件78を満たす（原本条件は補足説明を参照）」に従い、次の手順を繰り返す。条件を満たさなくなった場合は繰返しの後へ進む。

15.2.1. 繰返しの各回：関連情報を取得・設定する（処理79：詳細仕様参照）。

15.2.2. 繰返しの各回：「店番」を設定する。

15.2.3. 繰返しの各回：「顧客番号」を設定する。

15.2.4. 繰返しの各回：関連情報を取得・設定する（処理80：詳細仕様参照）。

15.2.5. 繰返しの各回：「対象項目がない」に該当するか確認する。該当する場合に限り、次の分岐内手順を行う。該当しない場合は分岐の後へ進む。

15.2.5.1. 条件成立時：関連情報を取得・設定する（処理81：詳細仕様参照）。

15.2.6. 繰返しの各回：「「対象項目」 が等しい Node.ELEMENT_NODE、かつ「対象項目」.equals("科目")」に該当するか確認する。該当する場合に限り、次の分岐内手順を行う。該当しない場合は分岐の後へ進む。

15.2.6.1. 条件成立時：「条件82を満たす（原本条件は補足説明を参照）」に該当するか確認する。成立時と不成立時の手順を分けて行う。

15.2.6.1.1. 条件成立時：「科目」を設定する。

15.2.6.1-別.1. 条件不成立時：「Webon取得結果解析エラー」を設定する。

15.2.6.1-別.2. 条件不成立時：関連情報を取得・設定する（処理83：詳細仕様参照）。

15.2.6.1-別.3. 条件不成立時：「科目」を設定する。

15.2.6.1-別.4. 条件不成立時：関連情報を取得・設定する（処理84：詳細仕様参照）。

15.2.6.1-別.5. 条件不成立時：「対象項目」を設定する。

15.2.6.1-別.6. 条件不成立時：処理の異常を通知し、この経路を終了する。この経路の後続手順は実行しない。

15.2.7. 繰返しの各回：関連情報を取得・設定する（処理85：詳細仕様参照）。

15.2.8. 繰返しの各回：「対象項目がない」に該当するか確認する。該当する場合に限り、次の分岐内手順を行う。該当しない場合は分岐の後へ進む。

15.2.8.1. 条件成立時：関連情報を取得・設定する（処理86：詳細仕様参照）。

15.2.9. 繰返しの各回：「「対象項目」 が等しい Node.ELEMENT_NODE、かつ「対象項目」.equals("科目符号")」に該当するか確認する。該当する場合に限り、次の分岐内手順を行う。該当しない場合は分岐の後へ進む。

15.2.9.1. 条件成立時：「科目符号」を設定する。

15.2.10. 繰返しの各回：関連情報を取得・設定する（処理87：詳細仕様参照）。

15.2.11. 繰返しの各回：「対象項目がない」に該当するか確認する。該当する場合に限り、次の分岐内手順を行う。該当しない場合は分岐の後へ進む。

15.2.11.1. 条件成立時：関連情報を取得・設定する（処理88：詳細仕様参照）。

15.2.12. 繰返しの各回：「「対象項目」 が等しい Node.ELEMENT_NODE、かつ「対象項目」.equals("口座番号預り番号")」に該当するか確認する。該当する場合に限り、次の分岐内手順を行う。該当しない場合は分岐の後へ進む。

15.2.12.1. 条件成立時：「条件89を満たす（原本条件は補足説明を参照）」に該当するか確認する。成立時と不成立時の手順を分けて行う。

15.2.12.1.1. 条件成立時：「口座番号預り番号」を設定する。

15.2.12.1-別.1. 条件不成立時：「Webon取得結果解析エラー」を設定する。

15.2.12.1-別.2. 条件不成立時：関連情報を取得・設定する（処理90：詳細仕様参照）。

15.2.12.1-別.3. 条件不成立時：「口座番号預り番号」を設定する。

15.2.12.1-別.4. 条件不成立時：関連情報を取得・設定する（処理91：詳細仕様参照）。

15.2.12.1-別.5. 条件不成立時：「対象項目」を設定する。

15.2.12.1-別.6. 条件不成立時：処理の異常を通知し、この経路を終了する。この経路の後続手順は実行しない。

15.2.13. 繰返しの各回：関連情報を取得・設定する（処理92：詳細仕様参照）。

15.2.14. 繰返しの各回：関連情報を取得・設定する（処理93：詳細仕様参照）。

16. 入力値の制約と変換結果を確認する。

17. 「条件94を満たす（原本条件は補足説明を参照）」に該当するか確認する。該当する場合に限り、次の分岐内手順を行う。該当しない場合は分岐の後へ進む。

17.1. 条件成立時：「Webon取得結果解析エラー」を設定する。

17.2. 条件成立時：「対象項目」を設定する。

17.3. 条件成立時：処理の異常を通知し、この経路を終了する。この経路の後続手順は実行しない。

#### 結果・例外時の扱い

| 到達条件 | 結果 |
| --- | --- |
| 条件95を満たす（原本条件は補足説明を参照）・「対象項目」 が等しい Node.ELEMENT_NODE・NOT (「対象項目」.equals(WOKEY_ROOP))・「対象項目」.equals(DBKEY_BRANCHNO)・条件96を満たす（原本条件は補足説明を参照） | 処理の異常を通知し、この経路を終了する |
| 条件97を満たす（原本条件は補足説明を参照）・「対象項目」 が等しい Node.ELEMENT_NODE・NOT (「対象項目」.equals(WOKEY_ROOP))・NOT (「対象項目」.equals(DBKEY_BRANCHNO))・「対象項目」.equals(DBKEY_CUSTNO)・条件98を満たす（原本条件は補足説明を参照） | 処理の異常を通知し、この経路を終了する |
| 条件99を満たす（原本条件は補足説明を参照）・条件100を満たす（原本条件は補足説明を参照）・「対象項目」 が等しい Node.ELEMENT_NODE、かつ「対象項目」.equals("科目")・条件101を満たす（原本条件は補足説明を参照） | 処理の異常を通知し、この経路を終了する |
| 条件102を満たす（原本条件は補足説明を参照）・条件103を満たす（原本条件は補足説明を参照）・「対象項目」 が等しい Node.ELEMENT_NODE、かつ「対象項目」.equals("口座番号預り番号")・条件104を満たす（原本条件は補足説明を参照） | 処理の異常を通知し、この経路を終了する |
| 条件105を満たす（原本条件は補足説明を参照） | 処理の異常を通知し、この経路を終了する |

### checkWebon

#### 処理概要

Webon汎用照会クラス 顧客結合照会汎用管理クラス 顧客結合照会(XML)の取得とデータ管理、アクセスメソッドの提供で「checkWebon」の要求を受け付ける。入力・確認・データ操作・応答の順と、条件が成立しない場合の処理を以下に示す。

#### 処理手順

1. 関連情報を取得・設定する（処理8：詳細仕様参照）。

2. 繰返し条件「条件9を満たす（原本条件は補足説明を参照）」に従い、次の手順を繰り返す。条件を満たさなくなった場合は繰返しの後へ進む。

2.1. 繰返しの各回：関連情報を取得・設定する（処理10：詳細仕様参照）。

2.2. 繰返しの各回：「条件11を満たす（原本条件は補足説明を参照）」に該当するか確認する。該当する場合に限り、次の分岐内手順を行う。該当しない場合は分岐の後へ進む。

2.2.1. 条件成立時：対象データを削除する。

3. 関連情報を取得・設定する（処理12：詳細仕様参照）。

4. 繰返し条件「条件13を満たす（原本条件は補足説明を参照）」に従い、次の手順を繰り返す。条件を満たさなくなった場合は繰返しの後へ進む。

4.1. 繰返しの各回：関連情報を取得・設定する（処理14：詳細仕様参照）。

4.2. 繰返しの各回：「店番」を設定する。

4.3. 繰返しの各回：「顧客番号」を設定する。

4.4. 繰返しの各回：「科目」を設定する。

4.5. 繰返しの各回：「科目符号」を設定する。

4.6. 繰返しの各回：「口座番号預り番号」を設定する。

### unionAccCheck

#### 処理概要

Webon汎用照会クラス 顧客結合照会汎用管理クラス 顧客結合照会(XML)の取得とデータ管理、アクセスメソッドの提供で「unionAccCheck」の要求を受け付ける。入力・確認・データ操作・応答の順と、条件が成立しない場合の処理を以下に示す。

#### 処理手順

1. 「kb.get科目() が等しい 未設定」に該当するか確認する。該当する場合に限り、次の分岐内手順を行う。該当しない場合は分岐の後へ進む。

1.1. 条件成立時：不成立の結果を返す。この経路の後続手順は実行しない。

2. 「kb.get口座番号預り番号() が等しい 未設定」に該当するか確認する。該当する場合に限り、次の分岐内手順を行う。該当しない場合は分岐の後へ進む。

2.1. 条件成立時：不成立の結果を返す。この経路の後続手順は実行しない。

3. 「get科目を実行するが成立する」に該当するか確認する。該当する場合に限り、次の分岐内手順を行う。該当しない場合は分岐の後へ進む。

3.1. 条件成立時：不成立の結果を返す。この経路の後続手順は実行しない。

4. 「get口座番号預り番号を実行するが成立する」に該当するか確認する。該当する場合に限り、次の分岐内手順を行う。該当しない場合は分岐の後へ進む。

4.1. 条件成立時：不成立の結果を返す。この経路の後続手順は実行しない。

5. 「!ValidateUtil.numCheck(kb.get科目())」に該当するか確認する。該当する場合に限り、次の分岐内手順を行う。該当しない場合は分岐の後へ進む。

5.1. 条件成立時：不成立の結果を返す。この経路の後続手順は実行しない。

6. 「!ValidateUtil.numCheck(kb.get口座番号預り番号())」に該当するか確認する。該当する場合に限り、次の分岐内手順を行う。該当しない場合は分岐の後へ進む。

6.1. 条件成立時：不成立の結果を返す。この経路の後続手順は実行しない。

7. 「kb.get科目().length() が異なる 2」に該当するか確認する。該当する場合に限り、次の分岐内手順を行う。該当しない場合は分岐の後へ進む。

7.1. 条件成立時：不成立の結果を返す。この経路の後続手順は実行しない。

8. 成立の結果を返す。この経路の後続手順は実行しない。

#### 結果・例外時の扱い

| 到達条件 | 結果 |
| --- | --- |
| kb.get科目() が等しい 未設定 | 不成立の結果を返す |
| NOT (kb.get科目() が等しい 未設定)・kb.get口座番号預り番号() が等しい 未設定 | 不成立の結果を返す |
| NOT (kb.get科目() が等しい 未設定)・NOT (kb.get口座番号預り番号() が等しい 未設定)・get科目を実行するが成立する | 不成立の結果を返す |
| NOT (kb.get科目() が等しい 未設定)・NOT (kb.get口座番号預り番号() が等しい 未設定)・NOT (kb.get科目().isEmpty())・get口座番号預り番号を実行するが成立する | 不成立の結果を返す |
| NOT (kb.get科目() が等しい 未設定)・NOT (kb.get口座番号預り番号() が等しい 未設定)・NOT (kb.get科目().isEmpty())・NOT (kb.get口座番号預り番号().isEmpty())・!ValidateUtil.numCheck(kb.get科目()) | 不成立の結果を返す |
| NOT (kb.get科目() が等しい 未設定)・NOT (kb.get口座番号預り番号() が等しい 未設定)・NOT (kb.get科目().isEmpty())・NOT (kb.get口座番号預り番号().isEmpty())・NOT (!ValidateUtil.numCheck(kb.get科目()))・!ValidateUtil.numCheck(kb.get口座番号預り番号()) | 不成立の結果を返す |
| NOT (kb.get科目() が等しい 未設定)・NOT (kb.get口座番号預り番号() が等しい 未設定)・NOT (kb.get科目().isEmpty())・NOT (kb.get口座番号預り番号().isEmpty())・NOT (!ValidateUtil.numCheck(kb.get科目()))・NOT (!ValidateUtil.numCheck(kb.get口座番号預り番号()))・kb.get科目().length() が異なる 2 | 不成立の結果を返す |
| NOT (kb.get科目() が等しい 未設定)・NOT (kb.get口座番号預り番号() が等しい 未設定)・NOT (kb.get科目().isEmpty())・NOT (kb.get口座番号預り番号().isEmpty())・NOT (!ValidateUtil.numCheck(kb.get科目()))・NOT (!ValidateUtil.numCheck(kb.get口座番号預り番号()))・NOT (kb.get科目().length() が異なる 2) | 成立の結果を返す |

### createWoException

#### 処理概要

Webon汎用照会クラス 顧客結合照会汎用管理クラス 顧客結合照会(XML)の取得とデータ管理、アクセスメソッドの提供で「createWoException」の要求を受け付ける。入力・確認・データ操作・応答の順と、条件が成立しない場合の処理を以下に示す。

#### 処理手順

1. 関連情報を取得・設定する（処理2：詳細仕様参照）。

2. 「対象項目」を設定する。

3. 「対象項目」を設定する。

4. 「対象項目」を設定する。

5. 「対象項目」を設定する。

6. 「対象項目」を設定する。

7. 処理結果を呼出元へ返す。この経路の後続手順は実行しない。

#### 結果・例外時の扱い

| 到達条件 | 結果 |
| --- | --- |
| この終了経路へ到達した場合 | 処理結果を呼出元へ返す |

### getSyokaiName

#### 処理概要

Webon汎用照会クラス 顧客結合照会汎用管理クラス 顧客結合照会(XML)の取得とデータ管理、アクセスメソッドの提供で「getSyokaiName」の要求を受け付ける。入力・確認・データ操作・応答の順と、条件が成立しない場合の処理を以下に示す。

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
| setEtc | 処理1 | this.etc = etc |
| setEtc | 処理2 | this.etc = etc |
| setErrFlg | 処理1 | this.errFlg = errFlg |
| setErrFlg | 処理2 | this.errFlg = errFlg |
| setCustomerUnionList | 処理1 | this.customerUnionList = customerUnionList |
| setCustomerUnionList | 処理2 | this.customerUnionList = customerUnionList |
| setWoCif | 処理1 | this.woCif = woCif |
| setWoCif | 処理2 | this.woCif = woCif |
| setWoBrno | 処理1 | this.woBrno = woBrno |
| setWoBrno | 処理2 | this.woBrno = woBrno |
| set店番 | 処理1 | this.店番 = 店番 |
| set店番 | 処理2 | this.店番 = 店番 |
| set顧客番号 | 処理1 | this.顧客番号 = 顧客番号 |
| set顧客番号 | 処理2 | this.顧客番号 = 顧客番号 |
| set科目 | 処理1 | this.科目 = 科目 |
| set科目 | 処理2 | this.科目 = 科目 |
| set科目符号 | 処理1 | this.科目符号 = 科目符号 |
| set科目符号 | 処理2 | this.科目符号 = 科目符号 |
| set口座番号預り番号 | 処理1 | this.口座番号預り番号 = 口座番号預り番号 |
| set口座番号預り番号 | 処理2 | this.口座番号預り番号 = 口座番号預り番号 |
| getWebonByCif | 処理1 | analyzeWeon() |
| getWebonByCif | 処理2 | getWebon(con) |
| getWebonByCif | 処理3 | this.loginInfo = loginInfo |
| getWebonByCif | 処理4 | this.woCif=cif |
| getWebonByCif | 処理5 | this.woBrno=br |
| getWebonByCif | 処理6 | this.woBrno=br |
| getWebonByCif | 処理7 | this.woCif=cif |
| getWebonByCif | 処理8 | this.loginInfo = loginInfo |
| getWebonByCif | 処理9 | getWebon(con) |
| getWebonByCif | 処理10 | analyzeWeon() |
| getWebonByCif | 条件11 | WebonException e |
| getWebonByCif | 条件12 | Exception e |
| getWebon | 処理1 | webonBase.doQuery() |
| getWebon | 処理2 | webonBase.doQuery() |
| analyzeWeon | 条件1 | errFlg |
| analyzeWeon | 条件2 | int i=0; i&lt;loopNodes.size(); i++ |
| analyzeWeon | 条件3 | int roopCount=0;roopCount&lt;FixedValue.SYS_WBNUMLIMIT;roopCount++ |
| analyzeWeon | 処理4 | customerUnionList.add(bean) |
| analyzeWeon | 処理5 | elem = getNextElement(elem) |
| analyzeWeon | 処理6 | etc.add(map) |
| analyzeWeon | 処理7 | Map&lt;String, String&gt;map = new HashMap&lt;String, String&gt;() |
| analyzeWeon | 条件8 | !getChildText(elem).equals("") |
| analyzeWeon | 処理9 | break |
| analyzeWeon | 処理10 | elem = getNextElement(elem) |
| analyzeWeon | 処理11 | break |
| analyzeWeon | 処理12 | elem = getNextElement(elem) |
| analyzeWeon | 処理13 | etc.add(map) |
| analyzeWeon | 処理14 | Map&lt;String, String&gt;map = new HashMap&lt;String, String&gt;() |
| analyzeWeon | 条件15 | !getChildText(elem).equals("") |
| analyzeWeon | 処理16 | break |
| analyzeWeon | 処理17 | elem=getNextElement2(elem) |
| analyzeWeon | 処理18 | KokyakuKetsugoBean bean = new KokyakuKetsugoBean() |
| analyzeWeon | 処理19 | Node elem=loopNodes.get(i).getFirstChild() |
| analyzeWeon | 条件20 | int roopCount=0;roopCount&lt;FixedValue.SYS_WBNUMLIMIT;roopCount++ |
| analyzeWeon | 処理21 | child = getNextElement(child) |
| analyzeWeon | 処理22 | loopNodes.add(child) |
| analyzeWeon | 処理23 | wobrno=getChildText(child) |
| analyzeWeon | 処理24 | etc.add(map) |
| analyzeWeon | 処理25 | Map&lt;String, String&gt;map = new HashMap&lt;String, String&gt;() |
| analyzeWeon | 条件26 | !getChildText(child).equals("") |
| analyzeWeon | 処理27 | wocustno=getChildText(child) |
| analyzeWeon | 処理28 | etc.add(map) |
| analyzeWeon | 処理29 | Map&lt;String, String&gt;map = new HashMap&lt;String, String&gt;() |
| analyzeWeon | 条件30 | !getChildText(child).equals("") |
| analyzeWeon | 処理31 | break |
| analyzeWeon | 処理32 | String wocustno=null |
| analyzeWeon | 処理33 | String wobrno=null |
| analyzeWeon | 処理34 | List&lt;Node&gt; loopNodes = new ArrayList&lt;Node&gt;() |
| analyzeWeon | 処理35 | Node child = root2.getFirstChild() |
| analyzeWeon | 条件36 | int roopCount=0;roopCount&lt;FixedValue.SYS_WBNUMLIMIT;roopCount++ |
| analyzeWeon | 処理37 | root = root.getNextSibling() |
| analyzeWeon | 処理38 | break |
| analyzeWeon | 条件39 | int roopCount2=0;roopCount2&lt;FixedValue.SYS_WBNUMLIMIT;roopCount2++ |
| analyzeWeon | 処理40 | root2 = root.getNextSibling() |
| analyzeWeon | 処理41 | break |
| analyzeWeon | 処理42 | break |
| analyzeWeon | 処理43 | root2 = root.getFirstChild() |
| analyzeWeon | 処理44 | break |
| analyzeWeon | 処理45 | Node root2=null |
| analyzeWeon | 処理46 | Node root=editData.getFirstChild() |
| analyzeWeon | 処理47 | Node editData = webonBase.getEditData() |
| analyzeWeon | 処理48 | Node editData = webonBase.getEditData() |
| analyzeWeon | 処理49 | Node root=editData.getFirstChild() |
| analyzeWeon | 処理50 | Node root2=null |
| analyzeWeon | 条件51 | int roopCount=0;roopCount&lt;FixedValue.SYS_WBNUMLIMIT;roopCount++ |
| analyzeWeon | 処理52 | break |
| analyzeWeon | 処理53 | root2 = root.getFirstChild() |
| analyzeWeon | 条件54 | int roopCount2=0;roopCount2&lt;FixedValue.SYS_WBNUMLIMIT;roopCount2++ |
| analyzeWeon | 処理55 | break |
| analyzeWeon | 処理56 | break |
| analyzeWeon | 処理57 | root2 = root.getNextSibling() |
| analyzeWeon | 処理58 | break |
| analyzeWeon | 処理59 | root = root.getNextSibling() |
| analyzeWeon | 処理60 | Node child = root2.getFirstChild() |
| analyzeWeon | 処理61 | List&lt;Node&gt; loopNodes = new ArrayList&lt;Node&gt;() |
| analyzeWeon | 処理62 | String wobrno=null |
| analyzeWeon | 処理63 | String wocustno=null |
| analyzeWeon | 条件64 | int roopCount=0;roopCount&lt;FixedValue.SYS_WBNUMLIMIT;roopCount++ |
| analyzeWeon | 処理65 | break |
| analyzeWeon | 処理66 | loopNodes.add(child) |
| analyzeWeon | 条件67 | !getChildText(child).equals("") |
| analyzeWeon | 処理68 | wobrno=getChildText(child) |
| analyzeWeon | 処理69 | Map&lt;String, String&gt;map = new HashMap&lt;String, String&gt;() |
| analyzeWeon | 処理70 | etc.add(map) |
| analyzeWeon | 条件71 | !getChildText(child).equals("") |
| analyzeWeon | 処理72 | wocustno=getChildText(child) |
| analyzeWeon | 処理73 | Map&lt;String, String&gt;map = new HashMap&lt;String, String&gt;() |
| analyzeWeon | 処理74 | etc.add(map) |
| analyzeWeon | 処理75 | child = getNextElement(child) |
| analyzeWeon | 条件76 | int i=0; i&lt;loopNodes.size(); i++ |
| analyzeWeon | 処理77 | Node elem=loopNodes.get(i).getFirstChild() |
| analyzeWeon | 条件78 | int roopCount=0;roopCount&lt;FixedValue.SYS_WBNUMLIMIT;roopCount++ |
| analyzeWeon | 処理79 | KokyakuKetsugoBean bean = new KokyakuKetsugoBean() |
| analyzeWeon | 処理80 | elem=getNextElement2(elem) |
| analyzeWeon | 処理81 | break |
| analyzeWeon | 条件82 | !getChildText(elem).equals("") |
| analyzeWeon | 処理83 | Map&lt;String, String&gt;map = new HashMap&lt;String, String&gt;() |
| analyzeWeon | 処理84 | etc.add(map) |
| analyzeWeon | 処理85 | elem = getNextElement(elem) |
| analyzeWeon | 処理86 | break |
| analyzeWeon | 処理87 | elem = getNextElement(elem) |
| analyzeWeon | 処理88 | break |
| analyzeWeon | 条件89 | !getChildText(elem).equals("") |
| analyzeWeon | 処理90 | Map&lt;String, String&gt;map = new HashMap&lt;String, String&gt;() |
| analyzeWeon | 処理91 | etc.add(map) |
| analyzeWeon | 処理92 | elem = getNextElement(elem) |
| analyzeWeon | 処理93 | customerUnionList.add(bean) |
| analyzeWeon | 条件94 | errFlg |
| analyzeWeon | 条件95 | int roopCount=0;roopCount&lt;FixedValue.SYS_WBNUMLIMIT;roopCount++ |
| analyzeWeon | 条件96 | NOT (!getChildText(child).equals("")) |
| analyzeWeon | 条件97 | int roopCount=0;roopCount&lt;FixedValue.SYS_WBNUMLIMIT;roopCount++ |
| analyzeWeon | 条件98 | NOT (!getChildText(child).equals("")) |
| analyzeWeon | 条件99 | int i=0; i&lt;loopNodes.size(); i++ |
| analyzeWeon | 条件100 | int roopCount=0;roopCount&lt;FixedValue.SYS_WBNUMLIMIT;roopCount++ |
| analyzeWeon | 条件101 | NOT (!getChildText(elem).equals("")) |
| analyzeWeon | 条件102 | int i=0; i&lt;loopNodes.size(); i++ |
| analyzeWeon | 条件103 | int roopCount=0;roopCount&lt;FixedValue.SYS_WBNUMLIMIT;roopCount++ |
| analyzeWeon | 条件104 | NOT (!getChildText(elem).equals("")) |
| analyzeWeon | 条件105 | errFlg |
| checkWebon | 条件1 | it.hasNext() |
| checkWebon | 処理2 | KokyakuKetsugoBean kb = it.next() |
| checkWebon | 処理3 | it = customerUnionList.iterator() |
| checkWebon | 条件4 | it.hasNext() |
| checkWebon | 条件5 | !unionAccCheck(kb) |
| checkWebon | 処理6 | KokyakuKetsugoBean kb=it.next() |
| checkWebon | 処理7 | Iterator&lt;KokyakuKetsugoBean&gt; it = customerUnionList.iterator() |
| checkWebon | 処理8 | Iterator&lt;KokyakuKetsugoBean&gt; it = customerUnionList.iterator() |
| checkWebon | 条件9 | it.hasNext() |
| checkWebon | 処理10 | KokyakuKetsugoBean kb=it.next() |
| checkWebon | 条件11 | !unionAccCheck(kb) |
| checkWebon | 処理12 | it = customerUnionList.iterator() |
| checkWebon | 条件13 | it.hasNext() |
| checkWebon | 処理14 | KokyakuKetsugoBean kb = it.next() |
| createWoException | 処理1 | WebonException e = new WebonException(msg,webonBase) |
| createWoException | 処理2 | WebonException e = new WebonException(msg,webonBase) |

