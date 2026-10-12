# 和暦・西暦表示と内部 ISO 日付の変換

## 表紙

| 項目 | 内容 |
| --- | --- |
| 文書名 | 基本設計書 |
| システム名 |  |
| 機能ID | COM-148 |
| 画面名 | 和暦・西暦表示と内部 ISO 日付の変換 |
| 会社名 |  |
| 作成日 |  |


## 概要

### 概要説明

和暦・西暦表示と内部 ISO 日付の変換の入力・表示・要求処理を行う。

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

### DateUtil

#### 処理概要

和暦・西暦表示と内部 ISO 日付の変換で「DateUtil」の要求を受け付ける。入力・確認・データ操作・応答の順と、条件が成立しない場合の処理を以下に示す。

#### 処理手順

1. 関連する処理へ制御を渡す。詳細な実行経路は原本対応を参照する。

### toIsoDate

#### 処理概要

和暦・西暦表示と内部 ISO 日付の変換で「toIsoDate」の要求を受け付ける。入力・確認・データ操作・応答の順と、条件が成立しない場合の処理を以下に示す。

#### 処理手順

1. 関連情報を取得・設定する（処理13：詳細仕様参照）。

2. 「input.length()  が等しい  0」に該当するか確認する。該当する場合に限り、次の分岐内手順を行う。該当しない場合は分岐の後へ進む。

2.1. 条件成立時：処理結果を呼出元へ返す。この経路の後続手順は実行しない。

3. 関連情報を取得・設定する（処理14：詳細仕様参照）。

4. 「条件15を満たす（原本条件は補足説明を参照）」に該当するか確認する。該当する場合に限り、次の分岐内手順を行う。該当しない場合は分岐の後へ進む。

4.1. 条件成立時：指定した条件でデータを照会する（照会結果1）。

4.2. 条件成立時：「元」を設定する。

4.3. 条件成立時：「条件16を満たす（原本条件は補足説明を参照）」に該当するか確認する。該当する場合に限り、次の分岐内手順を行う。該当しない場合は分岐の後へ進む。

4.3.1. 条件成立時：処理の異常を通知し、この経路を終了する。この経路の後続手順は実行しない。

4.4. 条件成立時：関連情報を取得・設定する（処理17：詳細仕様参照）。

4.5. 条件成立時：関連情報を取得・設定する（処理18：詳細仕様参照）。

4.6. 条件成立時：関連情報を取得・設定する（処理19：詳細仕様参照）。

4.7. 条件成立時：「条件20を満たす（原本条件は補足説明を参照）、または(era.end  が異なる  未設定 &amp;&amp; date.after(era.end))」に該当するか確認する。該当する場合に限り、次の分岐内手順を行う。該当しない場合は分岐の後へ進む。

4.7.1. 条件成立時：処理の異常を通知し、この経路を終了する。この経路の後続手順は実行しない。

4.8. 条件成立時：処理結果を呼出元へ返す。この経路の後続手順は実行しない。

5. 関連情報を取得・設定する（処理21：詳細仕様参照）。

6. 「条件22を満たす（原本条件は補足説明を参照）」に該当するか確認する。該当する場合に限り、次の分岐内手順を行う。該当しない場合は分岐の後へ進む。

6.1. 条件成立時：処理結果を呼出元へ返す。この経路の後続手順は実行しない。

7. 関連情報を取得・設定する（処理23：詳細仕様参照）。

8. 「条件24を満たす（原本条件は補足説明を参照）」に該当するか確認する。該当する場合に限り、次の分岐内手順を行う。該当しない場合は分岐の後へ進む。

8.1. 条件成立時：処理結果を呼出元へ返す。この経路の後続手順は実行しない。

9. 処理の異常を通知し、この経路を終了する。この経路の後続手順は実行しない。

#### 結果・例外時の扱い

| 到達条件 | 結果 |
| --- | --- |
| input.length()  が等しい  0 | 処理結果を呼出元へ返す |
| NOT (input.length()  が等しい  0)・条件25を満たす（原本条件は補足説明を参照）・条件26を満たす（原本条件は補足説明を参照） | 処理の異常を通知し、この経路を終了する |
| NOT (input.length()  が等しい  0)・条件27を満たす（原本条件は補足説明を参照）・条件28を満たす（原本条件は補足説明を参照）・条件29を満たす（原本条件は補足説明を参照）、または(era.end  が異なる  未設定 &amp;&amp; date.after(era.end)) | 処理の異常を通知し、この経路を終了する |
| NOT (input.length()  が等しい  0)・条件30を満たす（原本条件は補足説明を参照）・条件31を満たす（原本条件は補足説明を参照）・NOT (date.before(era.start) &#124;&#124; (era.end  が異なる  未設定 &amp;&amp; date.after(era.end))) | 処理結果を呼出元へ返す |
| NOT (input.length()  が等しい  0)・条件32を満たす（原本条件は補足説明を参照）・条件33を満たす（原本条件は補足説明を参照） | 処理結果を呼出元へ返す |
| NOT (input.length()  が等しい  0)・条件34を満たす（原本条件は補足説明を参照）・条件35を満たす（原本条件は補足説明を参照）・条件36を満たす（原本条件は補足説明を参照） | 処理結果を呼出元へ返す |
| NOT (input.length()  が等しい  0)・条件37を満たす（原本条件は補足説明を参照）・条件38を満たす（原本条件は補足説明を参照）・条件39を満たす（原本条件は補足説明を参照） | 処理の異常を通知し、この経路を終了する |

### toGregorianDisplay

#### 処理概要

和暦・西暦表示と内部 ISO 日付の変換で「toGregorianDisplay」の要求を受け付ける。入力・確認・データ操作・応答の順と、条件が成立しない場合の処理を以下に示す。

#### 処理手順

1. 関連情報を取得・設定する（処理2：詳細仕様参照）。

2. 処理結果を呼出元へ返す。この経路の後続手順は実行しない。

#### 結果・例外時の扱い

| 到達条件 | 結果 |
| --- | --- |
| この終了経路へ到達した場合 | 処理結果を呼出元へ返す |

### toWarekiDisplay

#### 処理概要

和暦・西暦表示と内部 ISO 日付の変換で「toWarekiDisplay」の要求を受け付ける。入力・確認・データ操作・応答の順と、条件が成立しない場合の処理を以下に示す。

#### 処理手順

1. 関連情報を取得・設定する（処理6：詳細仕様参照）。

2. 「iso.length()  が等しい  0」に該当するか確認する。該当する場合に限り、次の分岐内手順を行う。該当しない場合は分岐の後へ進む。

2.1. 条件成立時：処理結果を呼出元へ返す。この経路の後続手順は実行しない。

3. 関連情報を取得・設定する（処理7：詳細仕様参照）。

4. 関連情報を取得・設定する（処理8：詳細仕様参照）。

5. 関連情報を取得・設定する（処理9：詳細仕様参照）。

6. 「対象項目」を設定する。

7. 関連情報を取得・設定する（処理10：詳細仕様参照）。

8. 処理結果を呼出元へ返す。この経路の後続手順は実行しない。

#### 結果・例外時の扱い

| 到達条件 | 結果 |
| --- | --- |
| iso.length()  が等しい  0 | 処理結果を呼出元へ返す |
| NOT (iso.length()  が等しい  0) | 処理結果を呼出元へ返す |

### toAccessWareki

#### 処理概要

和暦・西暦表示と内部 ISO 日付の変換で「toAccessWareki」の要求を受け付ける。入力・確認・データ操作・応答の順と、条件が成立しない場合の処理を以下に示す。

#### 処理手順

1. 関連情報を取得・設定する（処理4：詳細仕様参照）。

2. 「display.length()  が等しい  0」に該当するか確認する。該当する場合に限り、次の分岐内手順を行う。該当しない場合は分岐の後へ進む。

2.1. 条件成立時：処理結果を呼出元へ返す。この経路の後続手順は実行しない。

3. 関連情報を取得・設定する（処理5：詳細仕様参照）。

4. 関連情報を取得・設定する（処理6：詳細仕様参照）。

5. 処理結果を呼出元へ返す。この経路の後続手順は実行しない。

#### 結果・例外時の扱い

| 到達条件 | 結果 |
| --- | --- |
| display.length()  が等しい  0 | 処理結果を呼出元へ返す |
| NOT (display.length()  が等しい  0) | 処理結果を呼出元へ返す |

### isValid

#### 処理概要

和暦・西暦表示と内部 ISO 日付の変換で「isValid」の要求を受け付ける。入力・確認・データ操作・応答の順と、条件が成立しない場合の処理を以下に示す。

#### 処理手順

1. 通常処理と例外時の処理を区別して実行する。例外処理は対応する例外が発生した場合に限る。

1.1. 通常処理：処理結果を呼出元へ返す。この経路の後続手順は実行しない。

1-例外1. 例外条件「IllegalArgumentException e」に該当した場合に次の手順を行う。型名は原本の表記。

1-例外1.1. 例外発生時：不成立の結果を返す。この経路の後続手順は実行しない。

#### 結果・例外時の扱い

| 到達条件 | 結果 |
| --- | --- |
| この終了経路へ到達した場合 | 処理結果を呼出元へ返す |
| 条件1を満たす（原本条件は補足説明を参照） | 不成立の結果を返す |

### todayIso

#### 処理概要

和暦・西暦表示と内部 ISO 日付の変換で「todayIso」の要求を受け付ける。入力・確認・データ操作・応答の順と、条件が成立しない場合の処理を以下に示す。

#### 処理手順

1. 処理結果を呼出元へ返す。この経路の後続手順は実行しない。

#### 結果・例外時の扱い

| 到達条件 | 結果 |
| --- | --- |
| この終了経路へ到達した場合 | 処理結果を呼出元へ返す |

### currentTime

#### 処理概要

和暦・西暦表示と内部 ISO 日付の変換で「currentTime」の要求を受け付ける。入力・確認・データ操作・応答の順と、条件が成立しない場合の処理を以下に示す。

#### 処理手順

1. 処理結果を呼出元へ返す。この経路の後続手順は実行しない。

#### 結果・例外時の扱い

| 到達条件 | 結果 |
| --- | --- |
| この終了経路へ到達した場合 | 処理結果を呼出元へ返す |

### firstDayOfMonth

#### 処理概要

和暦・西暦表示と内部 ISO 日付の変換で「firstDayOfMonth」の要求を受け付ける。入力・確認・データ操作・応答の順と、条件が成立しない場合の処理を以下に示す。

#### 処理手順

1. 関連情報を取得・設定する（処理2：詳細仕様参照）。

2. 処理結果を呼出元へ返す。この経路の後続手順は実行しない。

#### 結果・例外時の扱い

| 到達条件 | 結果 |
| --- | --- |
| この終了経路へ到達した場合 | 処理結果を呼出元へ返す |

### lastDayOfMonth

#### 処理概要

和暦・西暦表示と内部 ISO 日付の変換で「lastDayOfMonth」の要求を受け付ける。入力・確認・データ操作・応答の順と、条件が成立しない場合の処理を以下に示す。

#### 処理手順

1. 関連情報を取得・設定する（処理5：詳細仕様参照）。

2. 「iso.length()  が等しい  0」に該当するか確認する。該当する場合に限り、次の分岐内手順を行う。該当しない場合は分岐の後へ進む。

2.1. 条件成立時：処理結果を呼出元へ返す。この経路の後続手順は実行しない。

3. 関連情報を取得・設定する（処理6：詳細仕様参照）。

4. 関連情報を取得・設定する（処理7：詳細仕様参照）。

5. 「対象項目」を設定する。

6. 関連情報を取得・設定する（処理8：詳細仕様参照）。

7. 処理結果を呼出元へ返す。この経路の後続手順は実行しない。

#### 結果・例外時の扱い

| 到達条件 | 結果 |
| --- | --- |
| iso.length()  が等しい  0 | 処理結果を呼出元へ返す |
| NOT (iso.length()  が等しい  0) | 処理結果を呼出元へ返す |

### normalizeInput

#### 処理概要

和暦・西暦表示と内部 ISO 日付の変換で「normalizeInput」の要求を受け付ける。入力・確認・データ操作・応答の順と、条件が成立しない場合の処理を以下に示す。

#### 処理手順

1. 「対象項目がない」に該当するか確認する。該当する場合に限り、次の分岐内手順を行う。該当しない場合は分岐の後へ進む。

1.1. 条件成立時：処理結果を呼出元へ返す。この経路の後続手順は実行しない。

2. 関連情報を取得・設定する（処理3：詳細仕様参照）。

3. 関連情報を取得・設定する（処理4：詳細仕様参照）。

4. 処理結果を呼出元へ返す。この経路の後続手順は実行しない。

#### 結果・例外時の扱い

| 到達条件 | 結果 |
| --- | --- |
| 対象項目がない | 処理結果を呼出元へ返す |
| NOT (value  が等しい  未設定) | 処理結果を呼出元へ返す |

### findEra

#### 処理概要

和暦・西暦表示と内部 ISO 日付の変換で「findEra」の要求を受け付ける。入力・確認・データ操作・応答の順と、条件が成立しない場合の処理を以下に示す。

#### 処理手順

1. 関連情報を取得・設定する（処理5：詳細仕様参照）。

2. 繰返し条件「条件6を満たす（原本条件は補足説明を参照）」に従い、次の手順を繰り返す。条件を満たさなくなった場合は繰返しの後へ進む。

2.1. 繰返しの各回：「条件7を満たす（原本条件は補足説明を参照）、または条件8を満たす（原本条件は補足説明を参照）」に該当するか確認する。該当する場合に限り、次の分岐内手順を行う。該当しない場合は分岐の後へ進む。

2.1.1. 条件成立時：処理結果を呼出元へ返す。この経路の後続手順は実行しない。

3. 処理の異常を通知し、この経路を終了する。この経路の後続手順は実行しない。

#### 結果・例外時の扱い

| 到達条件 | 結果 |
| --- | --- |
| 条件9を満たす（原本条件は補足説明を参照）・条件10を満たす（原本条件は補足説明を参照）、または条件11を満たす（原本条件は補足説明を参照） | 処理結果を呼出元へ返す |
| この終了経路へ到達した場合 | 処理の異常を通知し、この経路を終了する |

### eraFor

#### 処理概要

和暦・西暦表示と内部 ISO 日付の変換で「eraFor」の要求を受け付ける。入力・確認・データ操作・応答の順と、条件が成立しない場合の処理を以下に示す。

#### 処理手順

1. 繰返し条件「条件3を満たす（原本条件は補足説明を参照）」に従い、次の手順を繰り返す。条件を満たさなくなった場合は繰返しの後へ進む。

1.1. 繰返しの各回：「条件4を満たす（原本条件は補足説明を参照）」に該当するか確認する。該当する場合に限り、次の分岐内手順を行う。該当しない場合は分岐の後へ進む。

1.1.1. 条件成立時：処理結果を呼出元へ返す。この経路の後続手順は実行しない。

2. 処理の異常を通知し、この経路を終了する。この経路の後続手順は実行しない。

#### 結果・例外時の扱い

| 到達条件 | 結果 |
| --- | --- |
| 条件5を満たす（原本条件は補足説明を参照）・条件6を満たす（原本条件は補足説明を参照） | 処理結果を呼出元へ返す |
| この終了経路へ到達した場合 | 処理の異常を通知し、この経路を終了する |

### formatIso

#### 処理概要

和暦・西暦表示と内部 ISO 日付の変換で「formatIso」の要求を受け付ける。入力・確認・データ操作・応答の順と、条件が成立しない場合の処理を以下に示す。

#### 処理手順

1. 関連情報を取得・設定する（処理3：詳細仕様参照）。

2. 関連情報を取得・設定する（処理4：詳細仕様参照）。

3. 処理結果を呼出元へ返す。この経路の後続手順は実行しない。

#### 結果・例外時の扱い

| 到達条件 | 結果 |
| --- | --- |
| この終了経路へ到達した場合 | 処理結果を呼出元へ返す |

### parseIso

#### 処理概要

和暦・西暦表示と内部 ISO 日付の変換で「parseIso」の要求を受け付ける。入力・確認・データ操作・応答の順と、条件が成立しない場合の処理を以下に示す。

#### 処理手順

1. 関連情報を取得・設定する（処理2：詳細仕様参照）。

2. 「対象項目」を設定する。

3. 通常処理と例外時の処理を区別して実行する。例外処理は対応する例外が発生した場合に限る。

3.1. 通常処理：処理結果を呼出元へ返す。この経路の後続手順は実行しない。

3-例外1. 例外条件「ParseException e」に該当した場合に次の手順を行う。型名は原本の表記。

3-例外1.1. 例外発生時：処理の異常を通知し、この経路を終了する。この経路の後続手順は実行しない。

#### 結果・例外時の扱い

| 到達条件 | 結果 |
| --- | --- |
| この終了経路へ到達した場合 | 処理結果を呼出元へ返す |
| 条件3を満たす（原本条件は補足説明を参照） | 処理の異常を通知し、この経路を終了する |

### twoDigits

#### 処理概要

和暦・西暦表示と内部 ISO 日付の変換で「twoDigits」の要求を受け付ける。入力・確認・データ操作・応答の順と、条件が成立しない場合の処理を以下に示す。

#### 処理手順

1. 処理結果を呼出元へ返す。この経路の後続手順は実行しない。

#### 結果・例外時の扱い

| 到達条件 | 結果 |
| --- | --- |
| この終了経路へ到達した場合 | 処理結果を呼出元へ返す |

### twoOrMoreDigits

#### 処理概要

和暦・西暦表示と内部 ISO 日付の変換で「twoOrMoreDigits」の要求を受け付ける。入力・確認・データ操作・応答の順と、条件が成立しない場合の処理を以下に示す。

#### 処理手順

1. 処理結果を呼出元へ返す。この経路の後続手順は実行しない。

#### 結果・例外時の扱い

| 到達条件 | 結果 |
| --- | --- |
| この終了経路へ到達した場合 | 処理結果を呼出元へ返す |

### fourDigits

#### 処理概要

和暦・西暦表示と内部 ISO 日付の変換で「fourDigits」の要求を受け付ける。入力・確認・データ操作・応答の順と、条件が成立しない場合の処理を以下に示す。

#### 処理手順

1. 関連情報を取得・設定する（処理4：詳細仕様参照）。

2. 繰返し条件「条件5を満たす（原本条件は補足説明を参照）」に従い、次の手順を繰り返す。条件を満たさなくなった場合は繰返しの後へ進む。

2.1. 繰返しの各回：関連情報を取得・設定する（処理6：詳細仕様参照）。

3. 処理結果を呼出元へ返す。この経路の後続手順は実行しない。

#### 結果・例外時の扱い

| 到達条件 | 結果 |
| --- | --- |
| この終了経路へ到達した場合 | 処理結果を呼出元へ返す |

### invalid

#### 処理概要

和暦・西暦表示と内部 ISO 日付の変換で「invalid」の要求を受け付ける。入力・確認・データ操作・応答の順と、条件が成立しない場合の処理を以下に示す。

#### 処理手順

1. 処理結果を呼出元へ返す。この経路の後続手順は実行しない。

#### 結果・例外時の扱い

| 到達条件 | 結果 |
| --- | --- |
| この終了経路へ到達した場合 | 処理結果を呼出元へ返す |

### Era

#### 処理概要

和暦・西暦表示と内部 ISO 日付の変換で「Era」の要求を受け付ける。入力・確認・データ操作・応答の順と、条件が成立しない場合の処理を以下に示す。

#### 処理手順

1. 関連情報を取得・設定する（処理6：詳細仕様参照）。

2. 関連情報を取得・設定する（処理7：詳細仕様参照）。

3. 関連情報を取得・設定する（処理8：詳細仕様参照）。

4. 関連情報を取得・設定する（処理9：詳細仕様参照）。

5. 関連情報を取得・設定する（処理10：詳細仕様参照）。


## 補足説明

### 適用条件

各仮定のQA番号を確認する。静的に確認できた操作・条件を適用する。

### 処理・条件の原本対応

文書内の条件番号・処理番号は次の原本表記に対応する。完全な業務用語への置換を行っていない箇所はQA・reportで確認する。

| イベント | 参照番号 | 原本条件・処理 |
| --- | --- | --- |
| toIsoDate | 条件1 | compact.matches() |
| toIsoDate | 処理2 | Matcher compact = COMPACT_DATE.matcher(input) |
| toIsoDate | 条件3 | western.matches() |
| toIsoDate | 処理4 | Matcher western = GREGORIAN_DATE.matcher(input) |
| toIsoDate | 条件5 | date.before(era.start) |
| toIsoDate | 処理6 | Date date = parseIso(iso, value) |
| toIsoDate | 処理7 | String iso = formatIso(year, Integer.parseInt(eraMatcher.group(3)), Integer.parseInt(eraMatcher.group(4)), value) |
| toIsoDate | 処理8 | int year = era.baseYear + eraYear - 1 |
| toIsoDate | 条件9 | eraYear &lt;= 0 |
| toIsoDate | 条件10 | eraMatcher.matches() |
| toIsoDate | 処理11 | Matcher eraMatcher = ERA_DATE.matcher(input) |
| toIsoDate | 処理12 | String input = normalizeInput(value) |
| toIsoDate | 処理13 | String input = normalizeInput(value) |
| toIsoDate | 処理14 | Matcher eraMatcher = ERA_DATE.matcher(input) |
| toIsoDate | 条件15 | eraMatcher.matches() |
| toIsoDate | 条件16 | eraYear &lt;= 0 |
| toIsoDate | 処理17 | int year = era.baseYear + eraYear - 1 |
| toIsoDate | 処理18 | String iso = formatIso(year, Integer.parseInt(eraMatcher.group(3)), Integer.parseInt(eraMatcher.group(4)), value) |
| toIsoDate | 処理19 | Date date = parseIso(iso, value) |
| toIsoDate | 条件20 | date.before(era.start) |
| toIsoDate | 処理21 | Matcher western = GREGORIAN_DATE.matcher(input) |
| toIsoDate | 条件22 | western.matches() |
| toIsoDate | 処理23 | Matcher compact = COMPACT_DATE.matcher(input) |
| toIsoDate | 条件24 | compact.matches() |
| toIsoDate | 条件25 | eraMatcher.matches() |
| toIsoDate | 条件26 | eraYear &lt;= 0 |
| toIsoDate | 条件27 | eraMatcher.matches() |
| toIsoDate | 条件28 | NOT (eraYear &lt;= 0) |
| toIsoDate | 条件29 | date.before(era.start) |
| toIsoDate | 条件30 | eraMatcher.matches() |
| toIsoDate | 条件31 | NOT (eraYear &lt;= 0) |
| toIsoDate | 条件32 | NOT (eraMatcher.matches()) |
| toIsoDate | 条件33 | western.matches() |
| toIsoDate | 条件34 | NOT (eraMatcher.matches()) |
| toIsoDate | 条件35 | NOT (western.matches()) |
| toIsoDate | 条件36 | compact.matches() |
| toIsoDate | 条件37 | NOT (eraMatcher.matches()) |
| toIsoDate | 条件38 | NOT (western.matches()) |
| toIsoDate | 条件39 | NOT (compact.matches()) |
| toGregorianDisplay | 処理1 | String iso = toIsoDate(value) |
| toGregorianDisplay | 処理2 | String iso = toIsoDate(value) |
| toWarekiDisplay | 処理1 | int eraYear = calendar.get(Calendar.YEAR) - era.baseYear + 1 |
| toWarekiDisplay | 処理2 | Calendar calendar = new GregorianCalendar() |
| toWarekiDisplay | 処理3 | Era era = eraFor(date) |
| toWarekiDisplay | 処理4 | Date date = parseIso(iso, value) |
| toWarekiDisplay | 処理5 | String iso = toIsoDate(value) |
| toWarekiDisplay | 処理6 | String iso = toIsoDate(value) |
| toWarekiDisplay | 処理7 | Date date = parseIso(iso, value) |
| toWarekiDisplay | 処理8 | Era era = eraFor(date) |
| toWarekiDisplay | 処理9 | Calendar calendar = new GregorianCalendar() |
| toWarekiDisplay | 処理10 | int eraYear = calendar.get(Calendar.YEAR) - era.baseYear + 1 |
| toAccessWareki | 処理1 | int year = Integer.parseInt(fields[0]) |
| toAccessWareki | 処理2 | String[] fields = display.substring(2).split("/") |
| toAccessWareki | 処理3 | String display = toWarekiDisplay(value) |
| toAccessWareki | 処理4 | String display = toWarekiDisplay(value) |
| toAccessWareki | 処理5 | String[] fields = display.substring(2).split("/") |
| toAccessWareki | 処理6 | int year = Integer.parseInt(fields[0]) |
| isValid | 条件1 | IllegalArgumentException e |
| firstDayOfMonth | 処理1 | String iso = toIsoDate(value) |
| firstDayOfMonth | 処理2 | String iso = toIsoDate(value) |
| lastDayOfMonth | 処理1 | int lastDay = calendar.getActualMaximum(Calendar.DAY_OF_MONTH) |
| lastDayOfMonth | 処理2 | Calendar calendar = new GregorianCalendar() |
| lastDayOfMonth | 処理3 | Date date = parseIso(iso, value) |
| lastDayOfMonth | 処理4 | String iso = toIsoDate(value) |
| lastDayOfMonth | 処理5 | String iso = toIsoDate(value) |
| lastDayOfMonth | 処理6 | Date date = parseIso(iso, value) |
| lastDayOfMonth | 処理7 | Calendar calendar = new GregorianCalendar() |
| lastDayOfMonth | 処理8 | int lastDay = calendar.getActualMaximum(Calendar.DAY_OF_MONTH) |
| normalizeInput | 処理1 | result = result.replace('　', ' ') |
| normalizeInput | 処理2 | String result = Normalizer.normalize(value, Normalizer.Form.NFKC).trim() |
| normalizeInput | 処理3 | String result = Normalizer.normalize(value, Normalizer.Form.NFKC).trim() |
| normalizeInput | 処理4 | result = result.replace('　', ' ') |
| findEra | 条件1 | int i = 0; i &lt; values.length; i++ |
| findEra | 条件2 | values[i].code.equalsIgnoreCase(token) |
| findEra | 条件3 | values[i].name.equals(token) |
| findEra | 処理4 | Era[] values = ERAS |
| findEra | 処理5 | Era[] values = ERAS |
| findEra | 条件6 | int i = 0; i &lt; values.length; i++ |
| findEra | 条件7 | values[i].code.equalsIgnoreCase(token) |
| findEra | 条件8 | values[i].name.equals(token) |
| findEra | 条件9 | int i = 0; i &lt; values.length; i++ |
| findEra | 条件10 | values[i].code.equalsIgnoreCase(token) |
| findEra | 条件11 | values[i].name.equals(token) |
| eraFor | 条件1 | int i = ERAS.length - 1; i &gt;= 0; i-- |
| eraFor | 条件2 | !date.before(ERAS[i].start) |
| eraFor | 条件3 | int i = ERAS.length - 1; i &gt;= 0; i-- |
| eraFor | 条件4 | !date.before(ERAS[i].start) |
| eraFor | 条件5 | int i = ERAS.length - 1; i &gt;= 0; i-- |
| eraFor | 条件6 | !date.before(ERAS[i].start) |
| formatIso | 処理1 | parseIso(iso, original) |
| formatIso | 処理2 | String iso = fourDigits(year) + "-" + twoDigits(month) + "-" + twoDigits(day) |
| formatIso | 処理3 | String iso = fourDigits(year) + "-" + twoDigits(month) + "-" + twoDigits(day) |
| formatIso | 処理4 | parseIso(iso, original) |
| parseIso | 処理1 | SimpleDateFormat format = new SimpleDateFormat("yyyy-MM-dd", Locale.ROOT) |
| parseIso | 処理2 | SimpleDateFormat format = new SimpleDateFormat("yyyy-MM-dd", Locale.ROOT) |
| parseIso | 条件3 | ParseException e |
| fourDigits | 条件1 | result.length() &lt; 4 |
| fourDigits | 処理2 | result = "0" + result |
| fourDigits | 処理3 | String result = Integer.toString(value) |
| fourDigits | 処理4 | String result = Integer.toString(value) |
| fourDigits | 条件5 | result.length() &lt; 4 |
| fourDigits | 処理6 | result = "0" + result |
| Era | 処理1 | this.end = end == null ? null : parseIso(end, end) |
| Era | 処理2 | this.start = parseIso(start, start) |
| Era | 処理3 | this.baseYear = baseYear |
| Era | 処理4 | this.name = name |
| Era | 処理5 | this.code = code |
| Era | 処理6 | this.code = code |
| Era | 処理7 | this.name = name |
| Era | 処理8 | this.baseYear = baseYear |
| Era | 処理9 | this.start = parseIso(start, start) |
| Era | 処理10 | this.end = end == null ? null : parseIso(end, end) |

