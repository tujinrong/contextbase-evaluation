# Webon汎用照会クラス 名寄せ情報照会（統一カナ氏名・生年月日による照会）クラス

## 表紙

| 項目 | 内容 |
| --- | --- |
| 文書名 | 基本設計書 |
| システム名 |  |
| 機能ID | COM-078 |
| 画面名 | Webon汎用照会クラス 名寄せ情報照会（統一カナ氏名・生年月日による照会）クラス |
| 会社名 |  |
| 作成日 |  |


## 概要

### 概要説明

Webon汎用照会クラス 名寄せ情報照会（統一カナ氏名・生年月日による照会）クラスの入力・表示・要求処理を行う。

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

### get統一顧客番号

#### 処理概要

Webon汎用照会クラス 名寄せ情報照会（統一カナ氏名・生年月日による照会）クラスで「get統一顧客番号」の要求を受け付ける。入力・確認・データ操作・応答の順と、条件が成立しない場合の処理を以下に示す。

#### 処理手順

1. 処理結果を呼出元へ返す。この経路の後続手順は実行しない。

#### 結果・例外時の扱い

| 到達条件 | 結果 |
| --- | --- |
| この終了経路へ到達した場合 | 処理結果を呼出元へ返す |

### set統一顧客番号

#### 処理概要

Webon汎用照会クラス 名寄せ情報照会（統一カナ氏名・生年月日による照会）クラスで「set統一顧客番号」の要求を受け付ける。入力・確認・データ操作・応答の順と、条件が成立しない場合の処理を以下に示す。

#### 処理手順

1. 関連情報を取得・設定する（処理2：詳細仕様参照）。

### get統一カナ氏名

#### 処理概要

Webon汎用照会クラス 名寄せ情報照会（統一カナ氏名・生年月日による照会）クラスで「get統一カナ氏名」の要求を受け付ける。入力・確認・データ操作・応答の順と、条件が成立しない場合の処理を以下に示す。

#### 処理手順

1. 処理結果を呼出元へ返す。この経路の後続手順は実行しない。

#### 結果・例外時の扱い

| 到達条件 | 結果 |
| --- | --- |
| この終了経路へ到達した場合 | 処理結果を呼出元へ返す |

### set統一カナ氏名

#### 処理概要

Webon汎用照会クラス 名寄せ情報照会（統一カナ氏名・生年月日による照会）クラスで「set統一カナ氏名」の要求を受け付ける。入力・確認・データ操作・応答の順と、条件が成立しない場合の処理を以下に示す。

#### 処理手順

1. 関連情報を取得・設定する（処理2：詳細仕様参照）。

### get統一生年月日

#### 処理概要

Webon汎用照会クラス 名寄せ情報照会（統一カナ氏名・生年月日による照会）クラスで「get統一生年月日」の要求を受け付ける。入力・確認・データ操作・応答の順と、条件が成立しない場合の処理を以下に示す。

#### 処理手順

1. 処理結果を呼出元へ返す。この経路の後続手順は実行しない。

#### 結果・例外時の扱い

| 到達条件 | 結果 |
| --- | --- |
| この終了経路へ到達した場合 | 処理結果を呼出元へ返す |

### set統一生年月日

#### 処理概要

Webon汎用照会クラス 名寄せ情報照会（統一カナ氏名・生年月日による照会）クラスで「set統一生年月日」の要求を受け付ける。入力・確認・データ操作・応答の順と、条件が成立しない場合の処理を以下に示す。

#### 処理手順

1. 関連情報を取得・設定する（処理2：詳細仕様参照）。

### get統一電話番号

#### 処理概要

Webon汎用照会クラス 名寄せ情報照会（統一カナ氏名・生年月日による照会）クラスで「get統一電話番号」の要求を受け付ける。入力・確認・データ操作・応答の順と、条件が成立しない場合の処理を以下に示す。

#### 処理手順

1. 処理結果を呼出元へ返す。この経路の後続手順は実行しない。

#### 結果・例外時の扱い

| 到達条件 | 結果 |
| --- | --- |
| この終了経路へ到達した場合 | 処理結果を呼出元へ返す |

### set統一電話番号

#### 処理概要

Webon汎用照会クラス 名寄せ情報照会（統一カナ氏名・生年月日による照会）クラスで「set統一電話番号」の要求を受け付ける。入力・確認・データ操作・応答の順と、条件が成立しない場合の処理を以下に示す。

#### 処理手順

1. 関連情報を取得・設定する（処理2：詳細仕様参照）。

### get統一人格Ｃ

#### 処理概要

Webon汎用照会クラス 名寄せ情報照会（統一カナ氏名・生年月日による照会）クラスで「get統一人格Ｃ」の要求を受け付ける。入力・確認・データ操作・応答の順と、条件が成立しない場合の処理を以下に示す。

#### 処理手順

1. 処理結果を呼出元へ返す。この経路の後続手順は実行しない。

#### 結果・例外時の扱い

| 到達条件 | 結果 |
| --- | --- |
| この終了経路へ到達した場合 | 処理結果を呼出元へ返す |

### set統一人格Ｃ

#### 処理概要

Webon汎用照会クラス 名寄せ情報照会（統一カナ氏名・生年月日による照会）クラスで「set統一人格Ｃ」の要求を受け付ける。入力・確認・データ操作・応答の順と、条件が成立しない場合の処理を以下に示す。

#### 処理手順

1. 関連情報を取得・設定する（処理2：詳細仕様参照）。

### get店番

#### 処理概要

Webon汎用照会クラス 名寄せ情報照会（統一カナ氏名・生年月日による照会）クラスで「get店番」の要求を受け付ける。入力・確認・データ操作・応答の順と、条件が成立しない場合の処理を以下に示す。

#### 処理手順

1. 処理結果を呼出元へ返す。この経路の後続手順は実行しない。

#### 結果・例外時の扱い

| 到達条件 | 結果 |
| --- | --- |
| この終了経路へ到達した場合 | 処理結果を呼出元へ返す |

### set店番

#### 処理概要

Webon汎用照会クラス 名寄せ情報照会（統一カナ氏名・生年月日による照会）クラスで「set店番」の要求を受け付ける。入力・確認・データ操作・応答の順と、条件が成立しない場合の処理を以下に示す。

#### 処理手順

1. 関連情報を取得・設定する（処理2：詳細仕様参照）。

### get顧客番号

#### 処理概要

Webon汎用照会クラス 名寄せ情報照会（統一カナ氏名・生年月日による照会）クラスで「get顧客番号」の要求を受け付ける。入力・確認・データ操作・応答の順と、条件が成立しない場合の処理を以下に示す。

#### 処理手順

1. 処理結果を呼出元へ返す。この経路の後続手順は実行しない。

#### 結果・例外時の扱い

| 到達条件 | 結果 |
| --- | --- |
| この終了経路へ到達した場合 | 処理結果を呼出元へ返す |

### set顧客番号

#### 処理概要

Webon汎用照会クラス 名寄せ情報照会（統一カナ氏名・生年月日による照会）クラスで「set顧客番号」の要求を受け付ける。入力・確認・データ操作・応答の順と、条件が成立しない場合の処理を以下に示す。

#### 処理手順

1. 関連情報を取得・設定する（処理2：詳細仕様参照）。

### getEtc

#### 処理概要

Webon汎用照会クラス 名寄せ情報照会（統一カナ氏名・生年月日による照会）クラスで「getEtc」の要求を受け付ける。入力・確認・データ操作・応答の順と、条件が成立しない場合の処理を以下に示す。

#### 処理手順

1. 処理結果を呼出元へ返す。この経路の後続手順は実行しない。

#### 結果・例外時の扱い

| 到達条件 | 結果 |
| --- | --- |
| この終了経路へ到達した場合 | 処理結果を呼出元へ返す |

### setEtc

#### 処理概要

Webon汎用照会クラス 名寄せ情報照会（統一カナ氏名・生年月日による照会）クラスで「setEtc」の要求を受け付ける。入力・確認・データ操作・応答の順と、条件が成立しない場合の処理を以下に示す。

#### 処理手順

1. 関連情報を取得・設定する（処理2：詳細仕様参照）。

### isErrFlg

#### 処理概要

Webon汎用照会クラス 名寄せ情報照会（統一カナ氏名・生年月日による照会）クラスで「isErrFlg」の要求を受け付ける。入力・確認・データ操作・応答の順と、条件が成立しない場合の処理を以下に示す。

#### 処理手順

1. 処理結果を呼出元へ返す。この経路の後続手順は実行しない。

#### 結果・例外時の扱い

| 到達条件 | 結果 |
| --- | --- |
| この終了経路へ到達した場合 | 処理結果を呼出元へ返す |

### setErrFlg

#### 処理概要

Webon汎用照会クラス 名寄せ情報照会（統一カナ氏名・生年月日による照会）クラスで「setErrFlg」の要求を受け付ける。入力・確認・データ操作・応答の順と、条件が成立しない場合の処理を以下に示す。

#### 処理手順

1. 関連情報を取得・設定する（処理2：詳細仕様参照）。

### getCustNayoseInfoList

#### 処理概要

Webon汎用照会クラス 名寄せ情報照会（統一カナ氏名・生年月日による照会）クラスで「getCustNayoseInfoList」の要求を受け付ける。入力・確認・データ操作・応答の順と、条件が成立しない場合の処理を以下に示す。

#### 処理手順

1. 処理結果を呼出元へ返す。この経路の後続手順は実行しない。

#### 結果・例外時の扱い

| 到達条件 | 結果 |
| --- | --- |
| この終了経路へ到達した場合 | 処理結果を呼出元へ返す |

### setCustNayoseInfoList

#### 処理概要

Webon汎用照会クラス 名寄せ情報照会（統一カナ氏名・生年月日による照会）クラスで「setCustNayoseInfoList」の要求を受け付ける。入力・確認・データ操作・応答の順と、条件が成立しない場合の処理を以下に示す。

#### 処理手順

1. 関連情報を取得・設定する（処理2：詳細仕様参照）。

### analyzeWeon

#### 処理概要

Webon汎用照会クラス 名寄せ情報照会（統一カナ氏名・生年月日による照会）クラスで「analyzeWeon」の要求を受け付ける。入力・確認・データ操作・応答の順と、条件が成立しない場合の処理を以下に示す。

#### 処理手順

1. 「通帳部宛」を設定する。

2. 「統一顧客名寄せ情報照会」を設定する。

3. 「対象項目がない」に該当するか確認する。該当する場合に限り、次の分岐内手順を行う。該当しない場合は分岐の後へ進む。

3.1. 条件成立時：関連情報を取得・設定する（処理52：詳細仕様参照）。

3.2. 条件成立時：「Webonの結果が未取得です」を設定する。

3.3. 条件成立時：処理の異常を通知し、この経路を終了する。この経路の後続手順は実行しない。

4. 関連情報を取得・設定する（処理53：詳細仕様参照）。

5. 関連情報を取得・設定する（処理54：詳細仕様参照）。

6. 関連情報を取得・設定する（処理55：詳細仕様参照）。

7. 関連情報を取得・設定する（処理56：詳細仕様参照）。

8. 繰返し条件「条件57を満たす（原本条件は補足説明を参照）」に従い、次の手順を繰り返す。条件を満たさなくなった場合は繰返しの後へ進む。

8.1. 繰返しの各回：「対象項目がない」に該当するか確認する。該当する場合に限り、次の分岐内手順を行う。該当しない場合は分岐の後へ進む。

8.1.1. 条件成立時：関連情報を取得・設定する（処理58：詳細仕様参照）。

8.2. 繰返しの各回：「「対象項目」 が等しい Node.ELEMENT_NODE」に該当するか確認する。該当する場合に限り、次の分岐内手順を行う。該当しない場合は分岐の後へ進む。

8.2.1. 条件成立時：「「対象項目」.equals(WOKEY_TSUCYO)」に該当するか確認する。該当する場合に限り、次の分岐内手順を行う。該当しない場合は分岐の後へ進む。

8.2.1.1. 条件成立時：関連情報を取得・設定する（処理59：詳細仕様参照）。

8.2.1.2. 条件成立時：繰返し条件「条件60を満たす（原本条件は補足説明を参照）」に従い、次の手順を繰り返す。条件を満たさなくなった場合は繰返しの後へ進む。

8.2.1.2.1. 繰返しの各回：「対象項目がない」に該当するか確認する。該当する場合に限り、次の分岐内手順を行う。該当しない場合は分岐の後へ進む。

8.2.1.2.1.1. 条件成立時：関連情報を取得・設定する（処理61：詳細仕様参照）。

8.2.1.2.2. 繰返しの各回：「「対象項目」 が等しい Node.ELEMENT_NODE」に該当するか確認する。該当する場合に限り、次の分岐内手順を行う。該当しない場合は分岐の後へ進む。

8.2.1.2.2.1. 条件成立時：「「対象項目」.equals(WOKEY_NAYOSE)」に該当するか確認する。該当する場合に限り、次の分岐内手順を行う。該当しない場合は分岐の後へ進む。

8.2.1.2.2.1.1. 条件成立時：関連情報を取得・設定する（処理62：詳細仕様参照）。

8.2.1.2.3. 繰返しの各回：関連情報を取得・設定する（処理63：詳細仕様参照）。

8.2.1.3. 条件成立時：関連情報を取得・設定する（処理64：詳細仕様参照）。

8.3. 繰返しの各回：関連情報を取得・設定する（処理65：詳細仕様参照）。

9. 繰返し条件「条件66を満たす（原本条件は補足説明を参照）」に従い、次の手順を繰り返す。条件を満たさなくなった場合は繰返しの後へ進む。

9.1. 繰返しの各回：関連情報を取得・設定する（処理67：詳細仕様参照）。

9.2. 繰返しの各回：関連情報を取得・設定する（処理68：詳細仕様参照）。

9.3. 繰返しの各回：関連情報を取得・設定する（処理69：詳細仕様参照）。

9.4. 繰返しの各回：関連情報を取得・設定する（処理70：詳細仕様参照）。

9.5. 繰返しの各回：関連情報を取得・設定する（処理71：詳細仕様参照）。

9.6. 繰返しの各回：関連情報を取得・設定する（処理72：詳細仕様参照）。

9.7. 繰返しの各回：繰返し条件「条件73を満たす（原本条件は補足説明を参照）」に従い、次の手順を繰り返す。条件を満たさなくなった場合は繰返しの後へ進む。

9.7.1. 繰返しの各回：「対象項目がない」に該当するか確認する。該当する場合に限り、次の分岐内手順を行う。該当しない場合は分岐の後へ進む。

9.7.1.1. 条件成立時：関連情報を取得・設定する（処理74：詳細仕様参照）。

9.7.2. 繰返しの各回：「「対象項目」 が等しい Node.ELEMENT_NODE、かつ「対象項目」.equals("統一顧客番号")」に該当するか確認する。成立時と不成立時の手順を分けて行う。

9.7.2.1. 条件成立時：「条件75を満たす（原本条件は補足説明を参照）」に該当するか確認する。成立時と不成立時の手順を分けて行う。

9.7.2.1.1. 条件成立時：関連情報を取得・設定する（処理76：詳細仕様参照）。

9.7.2.1-別.1. 条件不成立時：「Webon取得結果解析エラー」を設定する。

9.7.2.1-別.2. 条件不成立時：関連情報を取得・設定する（処理77：詳細仕様参照）。

9.7.2.1-別.3. 条件不成立時：「統一顧客番号」を設定する。

9.7.2.1-別.4. 条件不成立時：関連情報を取得・設定する（処理78：詳細仕様参照）。

9.7.2.1-別.5. 条件不成立時：「対象項目」を設定する。

9.7.2.1-別.6. 条件不成立時：処理の異常を通知し、この経路を終了する。この経路の後続手順は実行しない。

9.7.2-別.1. 条件不成立時：「「対象項目」 が等しい Node.ELEMENT_NODE、かつ「対象項目」.equals("統一カナ氏名")」に該当するか確認する。成立時と不成立時の手順を分けて行う。

9.7.2-別.1.1. 条件成立時：「条件79を満たす（原本条件は補足説明を参照）」に該当するか確認する。成立時と不成立時の手順を分けて行う。

9.7.2-別.1.1.1. 条件成立時：関連情報を取得・設定する（処理80：詳細仕様参照）。

9.7.2-別.1.1-別.1. 条件不成立時：「Webon取得結果解析エラー」を設定する。

9.7.2-別.1.1-別.2. 条件不成立時：関連情報を取得・設定する（処理81：詳細仕様参照）。

9.7.2-別.1.1-別.3. 条件不成立時：「統一カナ氏名」を設定する。

9.7.2-別.1.1-別.4. 条件不成立時：関連情報を取得・設定する（処理82：詳細仕様参照）。

9.7.2-別.1.1-別.5. 条件不成立時：「対象項目」を設定する。

9.7.2-別.1.1-別.6. 条件不成立時：処理の異常を通知し、この経路を終了する。この経路の後続手順は実行しない。

9.7.2-別.1-別.1. 条件不成立時：「「対象項目」 が等しい Node.ELEMENT_NODE、かつ「対象項目」.equals("統一生年月日")」に該当するか確認する。成立時と不成立時の手順を分けて行う。

9.7.2-別.1-別.1.1. 条件成立時：関連情報を取得・設定する（処理83：詳細仕様参照）。

9.7.2-別.1-別.1-別.1. 条件不成立時：「「対象項目」 が等しい Node.ELEMENT_NODE、かつ「対象項目」.equals("統一電話番号")」に該当するか確認する。成立時と不成立時の手順を分けて行う。

9.7.2-別.1-別.1-別.1.1. 条件成立時：関連情報を取得・設定する（処理84：詳細仕様参照）。

9.7.2-別.1-別.1-別.1-別.1. 条件不成立時：「「対象項目」 が等しい Node.ELEMENT_NODE、かつ「対象項目」.equals("統一人格C")」に該当するか確認する。成立時と不成立時の手順を分けて行う。

9.7.2-別.1-別.1-別.1-別.1.1. 条件成立時：関連情報を取得・設定する（処理85：詳細仕様参照）。

9.7.2-別.1-別.1-別.1-別.1-別.1. 条件不成立時：「「対象項目」 が等しい Node.ELEMENT_NODE、かつ「対象項目」.equals("名寄せ店番")」に該当するか確認する。該当する場合に限り、次の分岐内手順を行う。該当しない場合は分岐の後へ進む。

9.7.2-別.1-別.1-別.1-別.1-別.1.1. 条件成立時：関連情報を取得・設定する（処理86：詳細仕様参照）。

9.7.2-別.1-別.1-別.1-別.1-別.1.2. 条件成立時：関連情報を取得・設定する（処理87：詳細仕様参照）。

9.7.2-別.1-別.1-別.1-別.1-別.1.3. 条件成立時：「条件88を満たす（原本条件は補足説明を参照）、かつ条件89を満たす（原本条件は補足説明を参照）」に該当するか確認する。該当する場合に限り、次の分岐内手順を行う。該当しない場合は分岐の後へ進む。

9.7.2-別.1-別.1-別.1-別.1-別.1.3.1. 条件成立時：関連情報を取得・設定する（処理90：詳細仕様参照）。

9.7.2-別.1-別.1-別.1-別.1-別.1.3.2. 条件成立時：関連情報を取得・設定する（処理91：詳細仕様参照）。

9.7.2-別.1-別.1-別.1-別.1-別.1.3.3. 条件成立時：繰返し条件「条件92を満たす（原本条件は補足説明を参照）」に従い、次の手順を繰り返す。条件を満たさなくなった場合は繰返しの後へ進む。

9.7.2-別.1-別.1-別.1-別.1-別.1.3.3.1. 繰返しの各回：「条件93を満たす（原本条件は補足説明を参照）、かつ条件94を満たす（原本条件は補足説明を参照）」に該当するか確認する。該当する場合に限り、次の分岐内手順を行う。該当しない場合は分岐の後へ進む。

9.7.2-別.1-別.1-別.1-別.1-別.1.3.3.1.1. 条件成立時：関連情報を取得・設定する（処理95：詳細仕様参照）。

9.7.2-別.1-別.1-別.1-別.1-別.1.3.3.1.2. 条件成立時：「統一顧客番号」を設定する。

9.7.2-別.1-別.1-別.1-別.1-別.1.3.3.1.3. 条件成立時：「統一カナ氏名」を設定する。

9.7.2-別.1-別.1-別.1-別.1-別.1.3.3.1.4. 条件成立時：「統一生年月日」を設定する。

9.7.2-別.1-別.1-別.1-別.1-別.1.3.3.1.5. 条件成立時：「統一電話番号」を設定する。

9.7.2-別.1-別.1-別.1-別.1-別.1.3.3.1.6. 条件成立時：「統一人格Ｃ」を設定する。

9.7.2-別.1-別.1-別.1-別.1-別.1.3.3.1.7. 条件成立時：「「対象項目」 が等しい Node.ELEMENT_NODE、かつ「対象項目」.equals("店番")」に該当するか確認する。該当する場合に限り、次の分岐内手順を行う。該当しない場合は分岐の後へ進む。

9.7.2-別.1-別.1-別.1-別.1-別.1.3.3.1.7.1. 条件成立時：「店番」を設定する。

9.7.2-別.1-別.1-別.1-別.1-別.1.3.3.1.8. 条件成立時：「「対象項目」 が等しい Node.ELEMENT_NODE、かつ「対象項目」.equals("顧客番号")」に該当するか確認する。該当する場合に限り、次の分岐内手順を行う。該当しない場合は分岐の後へ進む。

9.7.2-別.1-別.1-別.1-別.1-別.1.3.3.1.8.1. 条件成立時：「顧客番号」を設定する。

9.7.2-別.1-別.1-別.1-別.1-別.1.3.3.1.9. 条件成立時：関連情報を取得・設定する（処理96：詳細仕様参照）。

9.7.2-別.1-別.1-別.1-別.1-別.1.3.3.2. 繰返しの各回：関連情報を取得・設定する（処理97：詳細仕様参照）。

9.7.2-別.1-別.1-別.1-別.1-別.1.3.3.3. 繰返しの各回：関連情報を取得・設定する（処理98：詳細仕様参照）。

9.7.2-別.1-別.1-別.1-別.1-別.1.3.3.4. 繰返しの各回：「対象項目がない」に該当するか確認する。該当する場合に限り、次の分岐内手順を行う。該当しない場合は分岐の後へ進む。

9.7.2-別.1-別.1-別.1-別.1-別.1.3.3.4.1. 条件成立時：関連情報を取得・設定する（処理99：詳細仕様参照）。

9.7.2-別.1-別.1-別.1-別.1-別.1.3.3.5. 繰返しの各回：「対象項目がない」に該当するか確認する。該当する場合に限り、次の分岐内手順を行う。該当しない場合は分岐の後へ進む。

9.7.2-別.1-別.1-別.1-別.1-別.1.3.3.5.1. 条件成立時：関連情報を取得・設定する（処理100：詳細仕様参照）。

9.7.3. 繰返しの各回：関連情報を取得・設定する（処理101：詳細仕様参照）。

10. 入力値の制約と変換結果を確認する。

11. 「条件102を満たす（原本条件は補足説明を参照）」に該当するか確認する。該当する場合に限り、次の分岐内手順を行う。該当しない場合は分岐の後へ進む。

11.1. 条件成立時：「Webon取得結果解析エラー」を設定する。

11.2. 条件成立時：「対象項目」を設定する。

11.3. 条件成立時：処理の異常を通知し、この経路を終了する。この経路の後続手順は実行しない。

#### 結果・例外時の扱い

| 到達条件 | 結果 |
| --- | --- |
| 対象項目がない | 処理の異常を通知し、この経路を終了する |
| NOT (webonBase が等しい 未設定)・条件103を満たす（原本条件は補足説明を参照）・条件104を満たす（原本条件は補足説明を参照）・「対象項目」 が等しい Node.ELEMENT_NODE、かつ「対象項目」.equals("統一顧客番号")・条件105を満たす（原本条件は補足説明を参照） | 処理の異常を通知し、この経路を終了する |
| NOT (webonBase が等しい 未設定)・条件106を満たす（原本条件は補足説明を参照）・条件107を満たす（原本条件は補足説明を参照）・NOT (「対象項目」 が等しい Node.ELEMENT_NODE &amp;&amp; 「対象項目」.equals("統一顧客番号"))・「対象項目」 が等しい Node.ELEMENT_NODE、かつ「対象項目」.equals("統一カナ氏名")・条件108を満たす（原本条件は補足説明を参照） | 処理の異常を通知し、この経路を終了する |
| NOT (webonBase が等しい 未設定)・条件109を満たす（原本条件は補足説明を参照） | 処理の異常を通知し、この経路を終了する |

### checkValue

#### 処理概要

Webon汎用照会クラス 名寄せ情報照会（統一カナ氏名・生年月日による照会）クラスで「checkValue」の要求を受け付ける。入力・確認・データ操作・応答の順と、条件が成立しない場合の処理を以下に示す。

#### 処理手順

1. 関連情報を取得・設定する（処理4：詳細仕様参照）。

2. 繰返し条件「条件5を満たす（原本条件は補足説明を参照）」に従い、次の手順を繰り返す。条件を満たさなくなった場合は繰返しの後へ進む。

2.1. 繰返しの各回：関連情報を取得・設定する（処理6：詳細仕様参照）。

2.2. 繰返しの各回：「店番」を設定する。

2.3. 繰返しの各回：「顧客番号」を設定する。

2.4. 繰返しの各回：「統一顧客番号」を設定する。

2.5. 繰返しの各回：「統一生年月日」を設定する。

### createWoException

#### 処理概要

Webon汎用照会クラス 名寄せ情報照会（統一カナ氏名・生年月日による照会）クラスで「createWoException」の要求を受け付ける。入力・確認・データ操作・応答の順と、条件が成立しない場合の処理を以下に示す。

#### 処理手順

1. 関連情報を取得・設定する（処理2：詳細仕様参照）。

2. 「対象項目」を設定する。

3. 「対象項目」を設定する。

4. 「対象項目」を設定する。

5. 処理結果を呼出元へ返す。この経路の後続手順は実行しない。

#### 結果・例外時の扱い

| 到達条件 | 結果 |
| --- | --- |
| この終了経路へ到達した場合 | 処理結果を呼出元へ返す |

### getSyokaiName

#### 処理概要

Webon汎用照会クラス 名寄せ情報照会（統一カナ氏名・生年月日による照会）クラスで「getSyokaiName」の要求を受け付ける。入力・確認・データ操作・応答の順と、条件が成立しない場合の処理を以下に示す。

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
| set統一顧客番号 | 処理1 | this.統一顧客番号 = 統一顧客番号 |
| set統一顧客番号 | 処理2 | this.統一顧客番号 = 統一顧客番号 |
| set統一カナ氏名 | 処理1 | this.統一カナ氏名 = 統一カナ氏名 |
| set統一カナ氏名 | 処理2 | this.統一カナ氏名 = 統一カナ氏名 |
| set統一生年月日 | 処理1 | this.統一生年月日 = 統一生年月日 |
| set統一生年月日 | 処理2 | this.統一生年月日 = 統一生年月日 |
| set統一電話番号 | 処理1 | this.統一電話番号 = 統一電話番号 |
| set統一電話番号 | 処理2 | this.統一電話番号 = 統一電話番号 |
| set統一人格Ｃ | 処理1 | 統一人格Ｃ = 統一人格ｃ |
| set統一人格Ｃ | 処理2 | 統一人格Ｃ = 統一人格ｃ |
| set店番 | 処理1 | this.店番 = 店番 |
| set店番 | 処理2 | this.店番 = 店番 |
| set顧客番号 | 処理1 | this.顧客番号 = 顧客番号 |
| set顧客番号 | 処理2 | this.顧客番号 = 顧客番号 |
| setEtc | 処理1 | this.etc = etc |
| setEtc | 処理2 | this.etc = etc |
| setErrFlg | 処理1 | this.errFlg = errFlg |
| setErrFlg | 処理2 | this.errFlg = errFlg |
| setCustNayoseInfoList | 処理1 | this.custNayoseInfoList = custNayoseInfoList |
| setCustNayoseInfoList | 処理2 | this.custNayoseInfoList = custNayoseInfoList |
| analyzeWeon | 条件1 | errFlg |
| analyzeWeon | 条件2 | int i=0; i&lt;loopNode.size(); i++ |
| analyzeWeon | 条件3 | int roopCount=0;roopCount&lt;FixedValue.SYS_WBNUMLIMIT;roopCount++ |
| analyzeWeon | 処理4 | elem=getNextElement(elem) |
| analyzeWeon | 処理5 | cif = getChildText(elem) |
| analyzeWeon | 処理6 | etc.add(map) |
| analyzeWeon | 処理7 | Map&lt;String, String&gt;map = new HashMap&lt;String, String&gt;() |
| analyzeWeon | 条件8 | !getChildText(elem).equals("") |
| analyzeWeon | 処理9 | kana = getChildText(elem) |
| analyzeWeon | 処理10 | etc.add(map) |
| analyzeWeon | 処理11 | Map&lt;String, String&gt;map = new HashMap&lt;String, String&gt;() |
| analyzeWeon | 条件12 | !getChildText(elem).equals("") |
| analyzeWeon | 処理13 | birthDate = getChildText(elem) |
| analyzeWeon | 処理14 | tel = getChildText(elem) |
| analyzeWeon | 処理15 | jinkaku = getChildText(elem) |
| analyzeWeon | 条件16 | int roopCount2=0;roopCount2&lt;FixedValue.SYS_WBNUMLIMIT;roopCount2++ |
| analyzeWeon | 処理17 | break |
| analyzeWeon | 処理18 | break |
| analyzeWeon | 処理19 | child2 = child2.getNextSibling() |
| analyzeWeon | 処理20 | child1 = child1.getNextSibling() |
| analyzeWeon | 処理21 | custNayoseInfoList.add(bean) |
| analyzeWeon | 処理22 | customerNayoseInfoBean bean = new customerNayoseInfoBean() |
| analyzeWeon | 条件23 | child1.hasChildNodes() |
| analyzeWeon | 条件24 | child2.hasChildNodes() |
| analyzeWeon | 処理25 | Node child2 = elemCif.getFirstChild() |
| analyzeWeon | 処理26 | Node child1 = elemBr.getFirstChild() |
| analyzeWeon | 条件27 | elemBr.hasChildNodes() |
| analyzeWeon | 条件28 | elemCif.hasChildNodes() |
| analyzeWeon | 処理29 | Node elemCif =getNextElement(elem) |
| analyzeWeon | 処理30 | Node elemBr =elem |
| analyzeWeon | 処理31 | break |
| analyzeWeon | 処理32 | Node elem=loopNode.get(i).getFirstChild() |
| analyzeWeon | 処理33 | String jinkaku = "" |
| analyzeWeon | 処理34 | String tel = "" |
| analyzeWeon | 処理35 | String birthDate = "" |
| analyzeWeon | 処理36 | String kana = "" |
| analyzeWeon | 処理37 | String cif = "" |
| analyzeWeon | 条件38 | int roopCount=0;roopCount&lt;FixedValue.SYS_WBNUMLIMIT;roopCount++ |
| analyzeWeon | 処理39 | root = root.getNextSibling() |
| analyzeWeon | 処理40 | break |
| analyzeWeon | 条件41 | int roopCount2=0;roopCount2&lt;FixedValue.SYS_WBNUMLIMIT;roopCount2++ |
| analyzeWeon | 処理42 | root2=root2.getNextSibling() |
| analyzeWeon | 処理43 | loopNode.add(root2) |
| analyzeWeon | 処理44 | break |
| analyzeWeon | 処理45 | root2=root.getFirstChild() |
| analyzeWeon | 処理46 | break |
| analyzeWeon | 処理47 | Node root2 = null |
| analyzeWeon | 処理48 | Node root = editData.getFirstChild() |
| analyzeWeon | 処理49 | ArrayList&lt;Node&gt; loopNode = new ArrayList&lt;Node&gt;() |
| analyzeWeon | 処理50 | Node editData = webonBase.getEditData() |
| analyzeWeon | 処理51 | StringBuilder errmsg=new StringBuilder() |
| analyzeWeon | 処理52 | StringBuilder errmsg=new StringBuilder() |
| analyzeWeon | 処理53 | Node editData = webonBase.getEditData() |
| analyzeWeon | 処理54 | ArrayList&lt;Node&gt; loopNode = new ArrayList&lt;Node&gt;() |
| analyzeWeon | 処理55 | Node root = editData.getFirstChild() |
| analyzeWeon | 処理56 | Node root2 = null |
| analyzeWeon | 条件57 | int roopCount=0;roopCount&lt;FixedValue.SYS_WBNUMLIMIT;roopCount++ |
| analyzeWeon | 処理58 | break |
| analyzeWeon | 処理59 | root2=root.getFirstChild() |
| analyzeWeon | 条件60 | int roopCount2=0;roopCount2&lt;FixedValue.SYS_WBNUMLIMIT;roopCount2++ |
| analyzeWeon | 処理61 | break |
| analyzeWeon | 処理62 | loopNode.add(root2) |
| analyzeWeon | 処理63 | root2=root2.getNextSibling() |
| analyzeWeon | 処理64 | break |
| analyzeWeon | 処理65 | root = root.getNextSibling() |
| analyzeWeon | 条件66 | int i=0; i&lt;loopNode.size(); i++ |
| analyzeWeon | 処理67 | String cif = "" |
| analyzeWeon | 処理68 | String kana = "" |
| analyzeWeon | 処理69 | String birthDate = "" |
| analyzeWeon | 処理70 | String tel = "" |
| analyzeWeon | 処理71 | String jinkaku = "" |
| analyzeWeon | 処理72 | Node elem=loopNode.get(i).getFirstChild() |
| analyzeWeon | 条件73 | int roopCount=0;roopCount&lt;FixedValue.SYS_WBNUMLIMIT;roopCount++ |
| analyzeWeon | 処理74 | break |
| analyzeWeon | 条件75 | !getChildText(elem).equals("") |
| analyzeWeon | 処理76 | cif = getChildText(elem) |
| analyzeWeon | 処理77 | Map&lt;String, String&gt;map = new HashMap&lt;String, String&gt;() |
| analyzeWeon | 処理78 | etc.add(map) |
| analyzeWeon | 条件79 | !getChildText(elem).equals("") |
| analyzeWeon | 処理80 | kana = getChildText(elem) |
| analyzeWeon | 処理81 | Map&lt;String, String&gt;map = new HashMap&lt;String, String&gt;() |
| analyzeWeon | 処理82 | etc.add(map) |
| analyzeWeon | 処理83 | birthDate = getChildText(elem) |
| analyzeWeon | 処理84 | tel = getChildText(elem) |
| analyzeWeon | 処理85 | jinkaku = getChildText(elem) |
| analyzeWeon | 処理86 | Node elemBr =elem |
| analyzeWeon | 処理87 | Node elemCif =getNextElement(elem) |
| analyzeWeon | 条件88 | elemBr.hasChildNodes() |
| analyzeWeon | 条件89 | elemCif.hasChildNodes() |
| analyzeWeon | 処理90 | Node child1 = elemBr.getFirstChild() |
| analyzeWeon | 処理91 | Node child2 = elemCif.getFirstChild() |
| analyzeWeon | 条件92 | int roopCount2=0;roopCount2&lt;FixedValue.SYS_WBNUMLIMIT;roopCount2++ |
| analyzeWeon | 条件93 | child1.hasChildNodes() |
| analyzeWeon | 条件94 | child2.hasChildNodes() |
| analyzeWeon | 処理95 | customerNayoseInfoBean bean = new customerNayoseInfoBean() |
| analyzeWeon | 処理96 | custNayoseInfoList.add(bean) |
| analyzeWeon | 処理97 | child1 = child1.getNextSibling() |
| analyzeWeon | 処理98 | child2 = child2.getNextSibling() |
| analyzeWeon | 処理99 | break |
| analyzeWeon | 処理100 | break |
| analyzeWeon | 処理101 | elem=getNextElement(elem) |
| analyzeWeon | 条件102 | errFlg |
| analyzeWeon | 条件103 | int i=0; i&lt;loopNode.size(); i++ |
| analyzeWeon | 条件104 | int roopCount=0;roopCount&lt;FixedValue.SYS_WBNUMLIMIT;roopCount++ |
| analyzeWeon | 条件105 | NOT (!getChildText(elem).equals("")) |
| analyzeWeon | 条件106 | int i=0; i&lt;loopNode.size(); i++ |
| analyzeWeon | 条件107 | int roopCount=0;roopCount&lt;FixedValue.SYS_WBNUMLIMIT;roopCount++ |
| analyzeWeon | 条件108 | NOT (!getChildText(elem).equals("")) |
| analyzeWeon | 条件109 | errFlg |
| checkValue | 条件1 | it.hasNext() |
| checkValue | 処理2 | customerNayoseInfoBean nb = it.next() |
| checkValue | 処理3 | Iterator&lt;customerNayoseInfoBean&gt; it = custNayoseInfoList.iterator() |
| checkValue | 処理4 | Iterator&lt;customerNayoseInfoBean&gt; it = custNayoseInfoList.iterator() |
| checkValue | 条件5 | it.hasNext() |
| checkValue | 処理6 | customerNayoseInfoBean nb = it.next() |
| createWoException | 処理1 | WebonException e = new WebonException(msg,webonBase) |
| createWoException | 処理2 | WebonException e = new WebonException(msg,webonBase) |

