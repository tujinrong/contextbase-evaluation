# webonオペレーションクラスのスーパークラス。 各種webon照会のオペレーションクラスは、必ずこのクラスを継承する

## 表紙

| 項目 | 内容 |
| --- | --- |
| 文書名 | 基本設計書 |
| システム名 |  |
| 機能ID | COM-072 |
| 画面名 | webonオペレーションクラスのスーパークラス。 各種webon照会のオペレーションクラスは、必ずこのクラスを継承する |
| 会社名 |  |
| 作成日 |  |


## 概要

### 概要説明

webonオペレーションクラスのスーパークラス。 各種webon照会のオペレーションクラスは、必ずこのクラスを継承するの入力・表示・要求処理を行う。

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

### getChildText

#### 処理概要

webonオペレーションクラスのスーパークラス。 各種webon照会のオペレーションクラスは、必ずこのクラスを継承するで「getChildText」の要求を受け付ける。入力・確認・データ操作・応答の順と、条件が成立しない場合の処理を以下に示す。

#### 処理手順

1. 関連情報を取得・設定する（処理7：詳細仕様参照）。

2. 関連情報を取得・設定する（処理8：詳細仕様参照）。

3. 繰返し条件「はい」に従い、次の手順を繰り返す。条件を満たさなくなった場合は繰返しの後へ進む。

3.1. 繰返しの各回：「対象項目がない」に該当するか確認する。該当する場合に限り、次の分岐内手順を行う。該当しない場合は分岐の後へ進む。

3.1.1. 条件成立時：関連情報を取得・設定する（処理9：詳細仕様参照）。

3.2. 繰返しの各回：「「対象項目」 が等しい Node.TEXT_NODE」に該当するか確認する。該当する場合に限り、次の分岐内手順を行う。該当しない場合は分岐の後へ進む。

3.2.1. 条件成立時：関連情報を取得・設定する（処理10：詳細仕様参照）。

3.2.2. 条件成立時：関連情報を取得・設定する（処理11：詳細仕様参照）。

3.3. 繰返しの各回：関連情報を取得・設定する（処理12：詳細仕様参照）。

4. 処理結果を呼出元へ返す。この経路の後続手順は実行しない。

#### 結果・例外時の扱い

| 到達条件 | 結果 |
| --- | --- |
| この終了経路へ到達した場合 | 処理結果を呼出元へ返す |

### getNextElement

#### 処理概要

webonオペレーションクラスのスーパークラス。 各種webon照会のオペレーションクラスは、必ずこのクラスを継承するで「getNextElement」の要求を受け付ける。入力・確認・データ操作・応答の順と、条件が成立しない場合の処理を以下に示す。

#### 処理手順

1. 繰返し条件「はい」に従い、次の手順を繰り返す。条件を満たさなくなった場合は繰返しの後へ進む。

1.1. 繰返しの各回：関連情報を取得・設定する（処理2：詳細仕様参照）。

1.2. 繰返しの各回：「対象項目がない」に該当するか確認する。該当する場合に限り、次の分岐内手順を行う。該当しない場合は分岐の後へ進む。

1.2.1. 条件成立時：処理結果を呼出元へ返す。この経路の後続手順は実行しない。

1.3. 繰返しの各回：「「対象項目」 が等しい Node.ELEMENT_NODE」に該当するか確認する。該当する場合に限り、次の分岐内手順を行う。該当しない場合は分岐の後へ進む。

1.3.1. 条件成立時：処理結果を呼出元へ返す。この経路の後続手順は実行しない。

#### 結果・例外時の扱い

| 到達条件 | 結果 |
| --- | --- |
| はい・対象項目がない | 処理結果を呼出元へ返す |
| はい・NOT (elem が等しい 未設定)・「対象項目」 が等しい Node.ELEMENT_NODE | 処理結果を呼出元へ返す |

### getNextElement2

#### 処理概要

webonオペレーションクラスのスーパークラス。 各種webon照会のオペレーションクラスは、必ずこのクラスを継承するで「getNextElement2」の要求を受け付ける。入力・確認・データ操作・応答の順と、条件が成立しない場合の処理を以下に示す。

#### 処理手順

1. 繰返し条件「はい」に従い、次の手順を繰り返す。条件を満たさなくなった場合は繰返しの後へ進む。

1.1. 繰返しの各回：「対象項目がない」に該当するか確認する。該当する場合に限り、次の分岐内手順を行う。該当しない場合は分岐の後へ進む。

1.1.1. 条件成立時：処理結果を呼出元へ返す。この経路の後続手順は実行しない。

1.2. 繰返しの各回：「「対象項目」 が等しい Node.ELEMENT_NODE」に該当するか確認する。該当する場合に限り、次の分岐内手順を行う。該当しない場合は分岐の後へ進む。

1.2.1. 条件成立時：処理結果を呼出元へ返す。この経路の後続手順は実行しない。

1.3. 繰返しの各回：関連情報を取得・設定する（処理2：詳細仕様参照）。

#### 結果・例外時の扱い

| 到達条件 | 結果 |
| --- | --- |
| はい・対象項目がない | 処理結果を呼出元へ返す |
| はい・NOT (elem が等しい 未設定)・「対象項目」 が等しい Node.ELEMENT_NODE | 処理結果を呼出元へ返す |

### getLineByXML

#### 処理概要

webonオペレーションクラスのスーパークラス。 各種webon照会のオペレーションクラスは、必ずこのクラスを継承するで「getLineByXML」の要求を受け付ける。入力・確認・データ操作・応答の順と、条件が成立しない場合の処理を以下に示す。

#### 処理手順

1. 「通帳部宛」を設定する。

2. 関連情報を取得・設定する（処理17：詳細仕様参照）。

3. 関連情報を取得・設定する（処理18：詳細仕様参照）。

4. 関連情報を取得・設定する（処理19：詳細仕様参照）。

5. 関連情報を取得・設定する（処理20：詳細仕様参照）。

6. 繰返し条件「条件21を満たす（原本条件は補足説明を参照）」に従い、次の手順を繰り返す。条件を満たさなくなった場合は繰返しの後へ進む。

6.1. 繰返しの各回：「対象項目がない」に該当するか確認する。該当する場合に限り、次の分岐内手順を行う。該当しない場合は分岐の後へ進む。

6.1.1. 条件成立時：関連情報を取得・設定する（処理22：詳細仕様参照）。

6.2. 繰返しの各回：「「対象項目」 が等しい Node.ELEMENT_NODE」に該当するか確認する。該当する場合に限り、次の分岐内手順を行う。該当しない場合は分岐の後へ進む。

6.2.1. 条件成立時：「「対象項目」.equals(WOKEY_TSUCYO)」に該当するか確認する。該当する場合に限り、次の分岐内手順を行う。該当しない場合は分岐の後へ進む。

6.2.1.1. 条件成立時：関連情報を取得・設定する（処理23：詳細仕様参照）。

6.3. 繰返しの各回：関連情報を取得・設定する（処理24：詳細仕様参照）。

7. 関連情報を取得・設定する（処理25：詳細仕様参照）。

8. 関連情報を取得・設定する（処理26：詳細仕様参照）。

9. 繰返し条件「条件27を満たす（原本条件は補足説明を参照）」に従い、次の手順を繰り返す。条件を満たさなくなった場合は繰返しの後へ進む。

9.1. 繰返しの各回：「対象項目がない」に該当するか確認する。該当する場合に限り、次の分岐内手順を行う。該当しない場合は分岐の後へ進む。

9.1.1. 条件成立時：関連情報を取得・設定する（処理28：詳細仕様参照）。

9.2. 繰返しの各回：「「対象項目」 が等しい Node.ELEMENT_NODE」に該当するか確認する。該当する場合に限り、次の分岐内手順を行う。該当しない場合は分岐の後へ進む。

9.2.1. 条件成立時：「「対象項目」.equals(WOKEY_LINE)」に該当するか確認する。該当する場合に限り、次の分岐内手順を行う。該当しない場合は分岐の後へ進む。

9.2.1.1. 条件成立時：関連情報を取得・設定する（処理29：詳細仕様参照）。

9.2.1.2. 条件成立時：「対象項目がない」に該当するか確認する。該当する場合に限り、次の分岐内手順を行う。該当しない場合は分岐の後へ進む。

9.2.1.2.1. 条件成立時：関連情報を取得・設定する（処理30：詳細仕様参照）。

9.2.1.3. 条件成立時：関連情報を取得・設定する（処理31：詳細仕様参照）。

9.3. 繰返しの各回：関連情報を取得・設定する（処理32：詳細仕様参照）。

10. 処理結果を呼出元へ返す。この経路の後続手順は実行しない。

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
| getChildText | 処理1 | child = child.getNextSibling() |
| getChildText | 処理2 | break |
| getChildText | 処理3 | textValue=child.getNodeValue() |
| getChildText | 処理4 | break |
| getChildText | 処理5 | Node child =elem.getFirstChild() |
| getChildText | 処理6 | String textValue="" |
| getChildText | 処理7 | String textValue="" |
| getChildText | 処理8 | Node child =elem.getFirstChild() |
| getChildText | 処理9 | break |
| getChildText | 処理10 | textValue=child.getNodeValue() |
| getChildText | 処理11 | break |
| getChildText | 処理12 | child = child.getNextSibling() |
| getNextElement | 処理1 | elem=elem.getNextSibling() |
| getNextElement | 処理2 | elem=elem.getNextSibling() |
| getNextElement2 | 処理1 | elem=elem.getNextSibling() |
| getNextElement2 | 処理2 | elem=elem.getNextSibling() |
| getLineByXML | 条件1 | int roopCount=0;roopCount&lt;FixedValue.SYS_WBNUMLIMIT;roopCount++ |
| getLineByXML | 処理2 | line = line.getNextSibling() |
| getLineByXML | 処理3 | lineList.add(lineString) |
| getLineByXML | 処理4 | lineString="" |
| getLineByXML | 処理5 | lineString=WebonBase.getChildText(line) |
| getLineByXML | 処理6 | break |
| getLineByXML | 処理7 | String lineString |
| getLineByXML | 処理8 | Node line=root.getFirstChild() |
| getLineByXML | 条件9 | int roopCount=0;roopCount&lt;FixedValue.SYS_WBNUMLIMIT;roopCount++ |
| getLineByXML | 処理10 | root = root.getNextSibling() |
| getLineByXML | 処理11 | break |
| getLineByXML | 処理12 | break |
| getLineByXML | 処理13 | Node root=output.getFirstChild() |
| getLineByXML | 処理14 | Node output = webonBase.getOutputData() |
| getLineByXML | 処理15 | ArrayList&lt;String&gt; lineList = new ArrayList&lt;String&gt;() |
| getLineByXML | 処理16 | final String WOKEY_LINE="LINE" |
| getLineByXML | 処理17 | final String WOKEY_LINE="LINE" |
| getLineByXML | 処理18 | ArrayList&lt;String&gt; lineList = new ArrayList&lt;String&gt;() |
| getLineByXML | 処理19 | Node output = webonBase.getOutputData() |
| getLineByXML | 処理20 | Node root=output.getFirstChild() |
| getLineByXML | 条件21 | int roopCount=0;roopCount&lt;FixedValue.SYS_WBNUMLIMIT;roopCount++ |
| getLineByXML | 処理22 | break |
| getLineByXML | 処理23 | break |
| getLineByXML | 処理24 | root = root.getNextSibling() |
| getLineByXML | 処理25 | Node line=root.getFirstChild() |
| getLineByXML | 処理26 | String lineString |
| getLineByXML | 条件27 | int roopCount=0;roopCount&lt;FixedValue.SYS_WBNUMLIMIT;roopCount++ |
| getLineByXML | 処理28 | break |
| getLineByXML | 処理29 | lineString=WebonBase.getChildText(line) |
| getLineByXML | 処理30 | lineString="" |
| getLineByXML | 処理31 | lineList.add(lineString) |
| getLineByXML | 処理32 | line = line.getNextSibling() |

