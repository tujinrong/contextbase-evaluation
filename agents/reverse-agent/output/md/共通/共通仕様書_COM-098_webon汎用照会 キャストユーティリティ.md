# webon汎用照会 キャストユーティリティ

## 表紙

| 項目 | 内容 |
| --- | --- |
| 文書名 | 基本設計書 |
| システム名 |  |
| 機能ID | COM-098 |
| 画面名 | webon汎用照会 キャストユーティリティ |
| 会社名 |  |
| 作成日 |  |


## 概要

### 概要説明

webon汎用照会 キャストユーティリティの入力・表示・要求処理を行う。

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

### genelicToStringList

#### 処理概要

webon汎用照会 キャストユーティリティで「genelicToStringList」の要求を受け付ける。入力・確認・データ操作・応答の順と、条件が成立しない場合の処理を以下に示す。

#### 処理手順

1. 関連情報を取得・設定する（処理6：詳細仕様参照）。

2. 繰返し条件「条件7を満たす（原本条件は補足説明を参照）」に従い、次の手順を繰り返す。条件を満たさなくなった場合は繰返しの後へ進む。

2.1. 繰返しの各回：関連情報を取得・設定する（処理8：詳細仕様参照）。

2.2. 繰返しの各回：関連情報を取得・設定する（処理9：詳細仕様参照）。

2.3. 繰返しの各回：関連情報を取得・設定する（処理10：詳細仕様参照）。

3. 処理結果を呼出元へ返す。この経路の後続手順は実行しない。

#### 結果・例外時の扱い

| 到達条件 | 結果 |
| --- | --- |
| この終了経路へ到達した場合 | 処理結果を呼出元へ返す |

### genelicToStringMap

#### 処理概要

webon汎用照会 キャストユーティリティで「genelicToStringMap」の要求を受け付ける。入力・確認・データ操作・応答の順と、条件が成立しない場合の処理を以下に示す。

#### 処理手順

1. 関連情報を取得・設定する（処理7：詳細仕様参照）。

2. 関連情報を取得・設定する（処理8：詳細仕様参照）。

3. 繰返し条件「条件9を満たす（原本条件は補足説明を参照）」に従い、次の手順を繰り返す。条件を満たさなくなった場合は繰返しの後へ進む。

3.1. 繰返しの各回：関連情報を取得・設定する（処理10：詳細仕様参照）。

3.2. 繰返しの各回：関連情報を取得・設定する（処理11：詳細仕様参照）。

3.3. 繰返しの各回：関連情報を取得・設定する（処理12：詳細仕様参照）。

4. 処理結果を呼出元へ返す。この経路の後続手順は実行しない。

#### 結果・例外時の扱い

| 到達条件 | 結果 |
| --- | --- |
| この終了経路へ到達した場合 | 処理結果を呼出元へ返す |

### genelicToStringList2

#### 処理概要

webon汎用照会 キャストユーティリティで「genelicToStringList2」の要求を受け付ける。入力・確認・データ操作・応答の順と、条件が成立しない場合の処理を以下に示す。

#### 処理手順

1. 関連情報を取得・設定する（処理6：詳細仕様参照）。

2. 繰返し条件「条件7を満たす（原本条件は補足説明を参照）」に従い、次の手順を繰り返す。条件を満たさなくなった場合は繰返しの後へ進む。

2.1. 繰返しの各回：関連情報を取得・設定する（処理8：詳細仕様参照）。

2.2. 繰返しの各回：関連情報を取得・設定する（処理9：詳細仕様参照）。

2.3. 繰返しの各回：関連情報を取得・設定する（処理10：詳細仕様参照）。

3. 処理結果を呼出元へ返す。この経路の後続手順は実行しない。

#### 結果・例外時の扱い

| 到達条件 | 結果 |
| --- | --- |
| この終了経路へ到達した場合 | 処理結果を呼出元へ返す |

### genelicToStringMap2

#### 処理概要

webon汎用照会 キャストユーティリティで「genelicToStringMap2」の要求を受け付ける。入力・確認・データ操作・応答の順と、条件が成立しない場合の処理を以下に示す。

#### 処理手順

1. 関連情報を取得・設定する（処理7：詳細仕様参照）。

2. 関連情報を取得・設定する（処理8：詳細仕様参照）。

3. 繰返し条件「条件9を満たす（原本条件は補足説明を参照）」に従い、次の手順を繰り返す。条件を満たさなくなった場合は繰返しの後へ進む。

3.1. 繰返しの各回：関連情報を取得・設定する（処理10：詳細仕様参照）。

3.2. 繰返しの各回：関連情報を取得・設定する（処理11：詳細仕様参照）。

3.3. 繰返しの各回：関連情報を取得・設定する（処理12：詳細仕様参照）。

4. 処理結果を呼出元へ返す。この経路の後続手順は実行しない。

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
| genelicToStringList | 条件1 | int i=0; i&lt;list.size(); i++ |
| genelicToStringList | 処理2 | resultList.add(resultMap) |
| genelicToStringList | 処理3 | resultMap=genelicToStringMap((Map&lt;?,?&gt;)list.get(i)) |
| genelicToStringList | 処理4 | HashMap&lt;String,String&gt; resultMap = new HashMap&lt;String,String&gt;() |
| genelicToStringList | 処理5 | ArrayList&lt;HashMap&lt;String,String&gt;&gt; resultList=new ArrayList&lt;HashMap&lt;String,String&gt;&gt;() |
| genelicToStringList | 処理6 | ArrayList&lt;HashMap&lt;String,String&gt;&gt; resultList=new ArrayList&lt;HashMap&lt;String,String&gt;&gt;() |
| genelicToStringList | 条件7 | int i=0; i&lt;list.size(); i++ |
| genelicToStringList | 処理8 | HashMap&lt;String,String&gt; resultMap = new HashMap&lt;String,String&gt;() |
| genelicToStringList | 処理9 | resultMap=genelicToStringMap((Map&lt;?,?&gt;)list.get(i)) |
| genelicToStringList | 処理10 | resultList.add(resultMap) |
| genelicToStringMap | 条件1 | Iterator&lt;?&gt; it = keys.iterator(); it.hasNext(); |
| genelicToStringMap | 処理2 | resultMap.put(key, value) |
| genelicToStringMap | 処理3 | String value = (String)map.get(key) |
| genelicToStringMap | 処理4 | String key = (String)it.next() |
| genelicToStringMap | 処理5 | Set&lt;?&gt; keys=map.keySet() |
| genelicToStringMap | 処理6 | HashMap&lt;String,String&gt; resultMap = new HashMap&lt;String,String&gt;() |
| genelicToStringMap | 処理7 | HashMap&lt;String,String&gt; resultMap = new HashMap&lt;String,String&gt;() |
| genelicToStringMap | 処理8 | Set&lt;?&gt; keys=map.keySet() |
| genelicToStringMap | 条件9 | Iterator&lt;?&gt; it = keys.iterator(); it.hasNext(); |
| genelicToStringMap | 処理10 | String key = (String)it.next() |
| genelicToStringMap | 処理11 | String value = (String)map.get(key) |
| genelicToStringMap | 処理12 | resultMap.put(key, value) |
| genelicToStringList2 | 条件1 | int i=0; i&lt;list.size(); i++ |
| genelicToStringList2 | 処理2 | resultList.add(resultMap) |
| genelicToStringList2 | 処理3 | resultMap=genelicToStringMap2((Map&lt;?,?&gt;)list.get(i)) |
| genelicToStringList2 | 処理4 | Map&lt;String,String&gt; resultMap = new HashMap&lt;String,String&gt;() |
| genelicToStringList2 | 処理5 | List&lt;Map&lt;String,String&gt;&gt; resultList=new ArrayList&lt;Map&lt;String,String&gt;&gt;() |
| genelicToStringList2 | 処理6 | List&lt;Map&lt;String,String&gt;&gt; resultList=new ArrayList&lt;Map&lt;String,String&gt;&gt;() |
| genelicToStringList2 | 条件7 | int i=0; i&lt;list.size(); i++ |
| genelicToStringList2 | 処理8 | Map&lt;String,String&gt; resultMap = new HashMap&lt;String,String&gt;() |
| genelicToStringList2 | 処理9 | resultMap=genelicToStringMap2((Map&lt;?,?&gt;)list.get(i)) |
| genelicToStringList2 | 処理10 | resultList.add(resultMap) |
| genelicToStringMap2 | 条件1 | Iterator&lt;?&gt; it = keys.iterator(); it.hasNext(); |
| genelicToStringMap2 | 処理2 | resultMap.put(key, value) |
| genelicToStringMap2 | 処理3 | String value = (String)map.get(key) |
| genelicToStringMap2 | 処理4 | String key = (String)it.next() |
| genelicToStringMap2 | 処理5 | Set&lt;?&gt; keys=map.keySet() |
| genelicToStringMap2 | 処理6 | Map&lt;String,String&gt; resultMap = new HashMap&lt;String,String&gt;() |
| genelicToStringMap2 | 処理7 | Map&lt;String,String&gt; resultMap = new HashMap&lt;String,String&gt;() |
| genelicToStringMap2 | 処理8 | Set&lt;?&gt; keys=map.keySet() |
| genelicToStringMap2 | 条件9 | Iterator&lt;?&gt; it = keys.iterator(); it.hasNext(); |
| genelicToStringMap2 | 処理10 | String key = (String)it.next() |
| genelicToStringMap2 | 処理11 | String value = (String)map.get(key) |
| genelicToStringMap2 | 処理12 | resultMap.put(key, value) |

