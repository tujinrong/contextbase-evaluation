# Access form処理データの日次・月次 Excel 出力

## 表紙

| 項目 | 内容 |
| --- | --- |
| 文書名 | 基本設計書 |
| システム名 |  |
| 機能ID | COM-142 |
| 画面名 | Access form処理データの日次・月次 Excel 出力 |
| 会社名 |  |
| 作成日 |  |


## 概要

### 概要説明

Access form処理データの日次・月次 Excel 出力の入力・表示・要求処理を行う。

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

### PensionBatchExportService

#### 処理概要

Access form処理データの日次・月次 Excel 出力で「PensionBatchExportService」の要求を受け付ける。入力・確認・データ操作・応答の順と、条件が成立しない場合の処理を以下に示す。

#### 処理手順

1. 関連する処理へ制御を渡す。詳細な実行経路は原本対応を参照する。

### PensionBatchExportService

#### 処理概要

Access form処理データの日次・月次 Excel 出力で「PensionBatchExportService」の要求を受け付ける。入力・確認・データ操作・応答の順と、条件が成立しない場合の処理を以下に示す。

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

Access form処理データの日次・月次 Excel 出力で「getInstance」の要求を受け付ける。入力・確認・データ操作・応答の順と、条件が成立しない場合の処理を以下に示す。

#### 処理手順

1. 処理結果を呼出元へ返す。この経路の後続手順は実行しない。

#### 結果・例外時の扱い

| 到達条件 | 結果 |
| --- | --- |
| この終了経路へ到達した場合 | 処理結果を呼出元へ返す |

### build

#### 処理概要

Access form処理データの日次・月次 Excel 出力で「build」の要求を受け付ける。入力・確認・データ操作・応答の順と、条件が成立しない場合の処理を以下に示す。

#### 処理手順

1. 「対象項目がない」に該当するか確認する。該当する場合に限り、次の分岐内手順を行う。該当しない場合は分岐の後へ進む。

1.1. 条件成立時：処理の異常を通知し、この経路を終了する。この経路の後続手順は実行しない。

2. 「!「対象項目」、かつ!「対象項目」、かつ!「対象項目」」に該当するか確認する。該当する場合に限り、次の分岐内手順を行う。該当しない場合は分岐の後へ進む。

2.1. 条件成立時：処理の異常を通知し、この経路を終了する。この経路の後続手順は実行しない。

3. 関連情報を取得・設定する（処理20：詳細仕様参照）。

4. 関連情報を取得・設定する（処理21：詳細仕様参照）。

5. 「「対象項目」.trim().length() &gt; 0」に該当するか確認する。該当する場合に限り、次の分岐内手順を行う。該当しない場合は分岐の後へ進む。

5.1. 条件成立時：関連情報を取得・設定する（処理22：詳細仕様参照）。

6. 関連情報を取得・設定する（処理23：詳細仕様参照）。

7. 関連情報を取得・設定する（処理24：詳細仕様参照）。

8. 関連情報を取得・設定する（処理25：詳細仕様参照）。

9. 繰返し条件「条件26を満たす（原本条件は補足説明を参照）」に従い、次の手順を繰り返す。条件を満たさなくなった場合は繰返しの後へ進む。

9.1. 繰返しの各回：関連情報を取得・設定する（処理27：詳細仕様参照）。

9.2. 繰返しの各回：指定した条件でデータを照会する。

9.3. 繰返しの各回：「「対象項目」」に該当するか確認する。該当する場合に限り、次の分岐内手順を行う。該当しない場合は分岐の後へ進む。

9.3.1. 条件成立時：関連情報を取得・設定する（処理28：詳細仕様参照）。

9.3.2. 条件成立時：関連情報を取得・設定する（処理29：詳細仕様参照）。

9.4. 繰返しの各回：関連情報を取得・設定する（処理30：詳細仕様参照）。

9.5. 繰返しの各回：関連情報を取得・設定する（処理31：詳細仕様参照）。

9.6. 繰返しの各回：関連情報を取得・設定する（処理32：詳細仕様参照）。

9.7. 繰返しの各回：関連情報を取得・設定する（処理33：詳細仕様参照）。

9.8. 繰返しの各回：関連情報を取得・設定する（処理34：詳細仕様参照）。

9.9. 繰返しの各回：関連情報を取得・設定する（処理35：詳細仕様参照）。

10. 関連情報を取得・設定する（処理36：詳細仕様参照）。

11. 関連情報を取得・設定する（処理37：詳細仕様参照）。

12. 「「対象項目」」に該当するか確認する。成立時と不成立時の手順を分けて行う。

12.1. 条件成立時：年金一括出力結果を実行する。

12-別.1. 条件不成立時：「generated.size()  が等しい  1」に該当するか確認する。成立時と不成立時の手順を分けて行う。

12-別.1.1. 条件成立時：関連情報を取得・設定する（処理38：詳細仕様参照）。

12-別.1.2. 条件成立時：年金一括出力結果を実行する。

12-別.1-別.1. 条件不成立時：「年金予約データ明細リスト（月次）.zip」を設定する。

12-別.1-別.2. 条件不成立時：年金一括出力結果を実行する。

13. 処理結果を呼出元へ返す。この経路の後続手順は実行しない。

#### DB操作の詳細

#### DB操作 SQL-4F7E42ED747E

| 情報 | 内容 |
| --- | --- |
| 操作ID | SQL-4F7E42ED747E |
| 対象テーブル | 年金＿削除明細 |
| 操作 | 削除 |
| 処理説明 | 対象テーブルの条件に一致する行を削除する。設定項目・対象条件・確定取消は以下の定義に従う。 |
| 設定項目 | 当該SQL式の列指定・実行時引数を使用する。組立式と原本のパラメーター設定を参照。 |
| 対象条件 | 抽出・更新対象条件：データ更新日 &lt;= ? |
| 確定・取消 | 当該メソッド内で自動コミット設定・コミットを行う。例外時の処理順は詳細仕様の分岐に従う。 |
| 原本 | nenkin/WEB-INF/src/nenkin/service/PensionRepository.java:468 / purgeDeletedAuditsThrough@458 |

#### 結果・例外時の扱い

| 到達条件 | 結果 |
| --- | --- |
| 対象項目がない | 処理の異常を通知し、この経路を終了する |
| NOT (request  が等しい  未設定)・!「対象項目」、かつ!「対象項目」、かつ!「対象項目」 | 処理の異常を通知し、この経路を終了する |
| NOT (request  が等しい  未設定)・NOT (!「対象項目」 &amp;&amp; !「対象項目」 &amp;&amp; !「対象項目」) | 処理結果を呼出元へ返す |

### resolveRange

#### 処理概要

Access form処理データの日次・月次 Excel 出力で「resolveRange」の要求を受け付ける。入力・確認・データ操作・応答の順と、条件が成立しない場合の処理を以下に示す。

#### 処理手順

1. 「「対象項目」が未設定」に該当するか確認する。該当する場合に限り、次の分岐内手順を行う。該当しない場合は分岐の後へ進む。

1.1. 条件成立時：処理の異常を通知し、この経路を終了する。この経路の後続手順は実行しない。

2. 「「対象項目」  が等しい  PensionBatchRunMode.DAILY」に該当するか確認する。該当する場合に限り、次の分岐内手順を行う。該当しない場合は分岐の後へ進む。

2.1. 条件成立時：「年月日を入力してください。」を設定する。

2.2. 条件成立時：処理結果を呼出元へ返す。この経路の後続手順は実行しない。

3. 「月初日を入力してください。」を設定する。

4. 「月末日を入力してください。」を設定する。

5. 「条件2を満たす（原本条件は補足説明を参照）」に該当するか確認する。該当する場合に限り、次の分岐内手順を行う。該当しない場合は分岐の後へ進む。

5.1. 条件成立時：処理の異常を通知し、この経路を終了する。この経路の後続手順は実行しない。

6. 処理結果を呼出元へ返す。この経路の後続手順は実行しない。

#### 結果・例外時の扱い

| 到達条件 | 結果 |
| --- | --- |
| 「対象項目」が未設定 | 処理の異常を通知し、この経路を終了する |
| NOT (「対象項目」  が等しい  未設定)・「対象項目」  が等しい  PensionBatchRunMode.DAILY | 処理結果を呼出元へ返す |
| NOT (「対象項目」  が等しい  未設定)・NOT (「対象項目」  が等しい  PensionBatchRunMode.DAILY)・条件3を満たす（原本条件は補足説明を参照） | 処理の異常を通知し、この経路を終了する |
| NOT (「対象項目」  が等しい  未設定)・NOT (「対象項目」  が等しい  PensionBatchRunMode.DAILY)・条件4を満たす（原本条件は補足説明を参照） | 処理結果を呼出元へ返す |

### requiredDate

#### 処理概要

Access form処理データの日次・月次 Excel 出力で「requiredDate」の要求を受け付ける。入力・確認・データ操作・応答の順と、条件が成立しない場合の処理を以下に示す。

#### 処理手順

1. 「対象項目がない、またはvalue.trim().length()  が等しい  0」に該当するか確認する。該当する場合に限り、次の分岐内手順を行う。該当しない場合は分岐の後へ進む。

1.1. 条件成立時：処理の異常を通知し、この経路を終了する。この経路の後続手順は実行しない。

2. 処理結果を呼出元へ返す。この経路の後続手順は実行しない。

#### 結果・例外時の扱い

| 到達条件 | 結果 |
| --- | --- |
| 対象項目がない、またはvalue.trim().length()  が等しい  0 | 処理の異常を通知し、この経路を終了する |
| NOT (value  が等しい  未設定 &#124;&#124; value.trim().length()  が等しい  0) | 処理結果を呼出元へ返す |

### parseStaffNo

#### 処理概要

Access form処理データの日次・月次 Excel 出力で「parseStaffNo」の要求を受け付ける。入力・確認・データ操作・応答の順と、条件が成立しない場合の処理を以下に示す。

#### 処理手順

1. 関連情報を取得・設定する（処理3：詳細仕様参照）。

2. 「text.length()  が等しい  0、または条件4を満たす（原本条件は補足説明を参照）」に該当するか確認する。該当する場合に限り、次の分岐内手順を行う。該当しない場合は分岐の後へ進む。

2.1. 条件成立時：戻り先画面を指定せず処理を終了する。この経路の後続手順は実行しない。

3. 通常処理と例外時の処理を区別して実行する。例外処理は対応する例外が発生した場合に限る。

3.1. 通常処理：処理結果を呼出元へ返す。この経路の後続手順は実行しない。

3-例外1. 例外条件「NumberFormatException e」に該当した場合に次の手順を行う。型名は原本の表記。

3-例外1.1. 例外発生時：処理の異常を通知し、この経路を終了する。この経路の後続手順は実行しない。

#### 結果・例外時の扱い

| 到達条件 | 結果 |
| --- | --- |
| text.length()  が等しい  0、または条件5を満たす（原本条件は補足説明を参照） | 戻り先画面を指定せず処理を終了する |
| NOT (text.length()  が等しい  0 &#124;&#124; "ALL".equalsIgnoreCase(text)) | 処理結果を呼出元へ返す |
| NOT (text.length()  が等しい  0 &#124;&#124; "ALL".equalsIgnoreCase(text))・条件6を満たす（原本条件は補足説明を参照） | 処理の異常を通知し、この経路を終了する |

### selectedSpecs

#### 処理概要

Access form処理データの日次・月次 Excel 出力で「selectedSpecs」の要求を受け付ける。入力・確認・データ操作・応答の順と、条件が成立しない場合の処理を以下に示す。

#### 処理手順

1. 関連情報を取得・設定する（処理5：詳細仕様参照）。

2. 「「対象項目」」に該当するか確認する。該当する場合に限り、次の分岐内手順を行う。該当しない場合は分岐の後へ進む。

2.1. 条件成立時：関連情報を取得・設定する（処理6：詳細仕様参照）。

3. 「「対象項目」」に該当するか確認する。該当する場合に限り、次の分岐内手順を行う。該当しない場合は分岐の後へ進む。

3.1. 条件成立時：関連情報を取得・設定する（処理7：詳細仕様参照）。

4. 「「対象項目」」に該当するか確認する。該当する場合に限り、次の分岐内手順を行う。該当しない場合は分岐の後へ進む。

4.1. 条件成立時：関連情報を取得・設定する（処理8：詳細仕様参照）。

5. 処理結果を呼出元へ返す。この経路の後続手順は実行しない。

#### 結果・例外時の扱い

| 到達条件 | 結果 |
| --- | --- |
| この終了経路へ到達した場合 | 処理結果を呼出元へ返す |

### buildSpec

#### 処理概要

Access form処理データの日次・月次 Excel 出力で「buildSpec」の要求を受け付ける。入力・確認・データ操作・応答の順と、条件が成立しない場合の処理を以下に示す。

#### 処理手順

1. 関連情報を取得・設定する（処理7：詳細仕様参照）。

2. 「mode  が等しい  PensionBatchRunMode.DAILY」に該当するか確認する。成立時と不成立時の手順を分けて行う。

2.1. 条件成立時：関連情報を取得・設定する（処理8：詳細仕様参照）。

2-別.1. 条件不成立時：関連情報を取得・設定する（処理9：詳細仕様参照）。

3. 関連情報を取得・設定する（処理10：詳細仕様参照）。

4. 関連情報を取得・設定する（処理11：詳細仕様参照）。

5. 関連情報を取得・設定する（処理12：詳細仕様参照）。

6. 「_データ明細リスト」を設定する。

7. 「全担当者」を設定する。

8. 「月次」を設定する。

9. 「】データ明細リスト（」を設定する。

10. 処理結果を呼出元へ返す。この経路の後続手順は実行しない。

#### 結果・例外時の扱い

| 到達条件 | 結果 |
| --- | --- |
| この終了経路へ到達した場合 | 処理結果を呼出元へ返す |

### emptyMessage

#### 処理概要

Access form処理データの日次・月次 Excel 出力で「emptyMessage」の要求を受け付ける。入力・確認・データ操作・応答の順と、条件が成立しない場合の処理を以下に示す。

#### 処理手順

1. 「月次」を設定する。

2. 「条件2を満たす（原本条件は補足説明を参照）」に該当するか確認する。該当する場合に限り、次の分岐内手順を行う。該当しない場合は分岐の後へ進む。

2.1. 条件成立時：エラーまたは処理結果「入力した担当者の【" + type.getDisplayName() + "分（" + period + "）】の該当明細はありませんでした」を返す。この経路の後続手順は実行しない。

3. 「入力年月の」を設定する。

4. 処理結果を呼出元へ返す。この経路の後続手順は実行しない。

#### 結果・例外時の扱い

| 到達条件 | 結果 |
| --- | --- |
| 条件3を満たす（原本条件は補足説明を参照） | エラーまたは処理結果「入力した担当者の【" + type.getDisplayName() + "分（" + period + "）】の該当明細はありませんでした」を返す |
| 条件4を満たす（原本条件は補足説明を参照） | 処理結果を呼出元へ返す |

### sortAudits

#### 処理概要

Access form処理データの日次・月次 Excel 出力で「sortAudits」の要求を受け付ける。入力・確認・データ操作・応答の順と、条件が成立しない場合の処理を以下に示す。

#### 処理手順

1. 関連情報を取得・設定する（処理2：詳細仕様参照）。

### compareInteger

#### 処理概要

Access form処理データの日次・月次 Excel 出力で「compareInteger」の要求を受け付ける。入力・確認・データ操作・応答の順と、条件が成立しない場合の処理を以下に示す。

#### 処理手順

1. 「対象項目がない」に該当するか確認する。該当する場合に限り、次の分岐内手順を行う。該当しない場合は分岐の後へ進む。

1.1. 条件成立時：処理結果を呼出元へ返す。この経路の後続手順は実行しない。

2. 処理結果を呼出元へ返す。この経路の後続手順は実行しない。

#### 結果・例外時の扱い

| 到達条件 | 結果 |
| --- | --- |
| 対象項目がない | 処理結果を呼出元へ返す |
| NOT (left  が等しい  未設定) | 処理結果を呼出元へ返す |

### toRows

#### 処理概要

Access form処理データの日次・月次 Excel 出力で「toRows」の要求を受け付ける。入力・確認・データ操作・応答の順と、条件が成立しない場合の処理を以下に示す。

#### 処理手順

1. 関連情報を取得・設定する（処理5：詳細仕様参照）。

2. 繰返し条件「条件6を満たす（原本条件は補足説明を参照）」に従い、次の手順を繰り返す。条件を満たさなくなった場合は繰返しの後へ進む。

2.1. 繰返しの各回：関連情報を取得・設定する（処理7：詳細仕様参照）。

2.2. 繰返しの各回：「type  が等しい  AuditType.NEW」に該当するか確認する。成立時と不成立時の手順を分けて行う。

2.2.1. 条件成立時：関連情報を取得・設定する（処理8：詳細仕様参照）。

2.2-別.1. 条件不成立時：「確」を設定する。

3. 処理結果を呼出元へ返す。この経路の後続手順は実行しない。

#### 結果・例外時の扱い

| 到達条件 | 結果 |
| --- | --- |
| この終了経路へ到達した場合 | 処理結果を呼出元へ返す |

### buildLayout

#### 処理概要

Access form処理データの日次・月次 Excel 出力で「buildLayout」の要求を受け付ける。入力・確認・データ操作・応答の順と、条件が成立しない場合の処理を以下に示す。

#### 処理手順

1. 関連情報を取得・設定する（処理25：詳細仕様参照）。

2. 繰返し条件「条件26を満たす（原本条件は補足説明を参照）」に従い、次の手順を繰り返す。条件を満たさなくなった場合は繰返しの後へ進む。

2.1. 繰返しの各回：関連情報を取得・設定する（処理27：詳細仕様参照）。

3. 関連情報を取得・設定する（処理28：詳細仕様参照）。

4. 関連情報を取得・設定する（処理29：詳細仕様参照）。

5. 関連情報を取得・設定する（処理30：詳細仕様参照）。

6. 関連情報を取得・設定する（処理31：詳細仕様参照）。

7. 関連情報を取得・設定する（処理32：詳細仕様参照）。

8. 「spec.type  が等しい  AuditType.NEW」に該当するか確認する。成立時と不成立時の手順を分けて行う。

8.1. 条件成立時：関連情報を取得・設定する（処理33：詳細仕様参照）。

8.2. 条件成立時：「処理日」を設定する。

8.3. 条件成立時：関連情報を取得・設定する（処理34：詳細仕様参照）。

8.4. 条件成立時：「職員番号」を設定する。

8.5. 条件成立時：関連情報を取得・設定する（処理35：詳細仕様参照）。

8.6. 条件成立時：関連情報を取得・設定する（処理36：詳細仕様参照）。

8.7. 条件成立時：関連情報を取得・設定する（処理37：詳細仕様参照）。

8.8. 条件成立時：関連情報を取得・設定する（処理38：詳細仕様参照）。

8.9. 条件成立時：関連情報を取得・設定する（処理39：詳細仕様参照）。

8.10. 条件成立時：関連情報を取得・設定する（処理40：詳細仕様参照）。

8-別.1. 条件不成立時：関連情報を取得・設定する（処理41：詳細仕様参照）。

8-別.2. 条件不成立時：「処理日」を設定する。

8-別.3. 条件不成立時：関連情報を取得・設定する（処理42：詳細仕様参照）。

8-別.4. 条件不成立時：「職員番号」を設定する。

8-別.5. 条件不成立時：関連情報を取得・設定する（処理43：詳細仕様参照）。

8-別.6. 条件不成立時：関連情報を取得・設定する（処理44：詳細仕様参照）。

8-別.7. 条件不成立時：関連情報を取得・設定する（処理45：詳細仕様参照）。

8-別.8. 条件不成立時：関連情報を取得・設定する（処理46：詳細仕様参照）。

8-別.9. 条件不成立時：関連情報を取得・設定する（処理47：詳細仕様参照）。

8-別.10. 条件不成立時：関連情報を取得・設定する（処理48：詳細仕様参照）。

9. 処理結果を呼出元へ返す。この経路の後続手順は実行しない。

#### 結果・例外時の扱い

| 到達条件 | 結果 |
| --- | --- |
| この終了経路へ到達した場合 | 処理結果を呼出元へ返す |

### wareki

#### 処理概要

Access form処理データの日次・月次 Excel 出力で「wareki」の要求を受け付ける。入力・確認・データ操作・応答の順と、条件が成立しない場合の処理を以下に示す。

#### 処理手順

1. 処理結果を呼出元へ返す。この経路の後続手順は実行しない。

#### 結果・例外時の扱い

| 到達条件 | 結果 |
| --- | --- |
| この終了経路へ到達した場合 | 処理結果を呼出元へ返す |

### staffCode

#### 処理概要

Access form処理データの日次・月次 Excel 出力で「staffCode」の要求を受け付ける。入力・確認・データ操作・応答の順と、条件が成立しない場合の処理を以下に示す。

#### 処理手順

1. 処理結果を呼出元へ返す。この経路の後続手順は実行しない。

#### 結果・例外時の扱い

| 到達条件 | 結果 |
| --- | --- |
| この終了経路へ到達した場合 | 処理結果を呼出元へ返す |

### toFileResults

#### 処理概要

Access form処理データの日次・月次 Excel 出力で「toFileResults」の要求を受け付ける。入力・確認・データ操作・応答の順と、条件が成立しない場合の処理を以下に示す。

#### 処理手順

1. 関連情報を取得・設定する（処理4：詳細仕様参照）。

2. 繰返し条件「条件5を満たす（原本条件は補足説明を参照）」に従い、次の手順を繰り返す。条件を満たさなくなった場合は繰返しの後へ進む。

2.1. 繰返しの各回：関連情報を取得・設定する（処理6：詳細仕様参照）。

2.2. 繰返しの各回：年金一括出力ファイル結果を実行する。

3. 処理結果を呼出元へ返す。この経路の後続手順は実行しない。

#### 結果・例外時の扱い

| 到達条件 | 結果 |
| --- | --- |
| この終了経路へ到達した場合 | 処理結果を呼出元へ返す |

### buildZip

#### 処理概要

Access form処理データの日次・月次 Excel 出力で「buildZip」の要求を受け付ける。入力・確認・データ操作・応答の順と、条件が成立しない場合の処理を以下に示す。

#### 処理手順

1. 関連情報を取得・設定する（処理10：詳細仕様参照）。

2. 関連情報を取得・設定する（処理11：詳細仕様参照）。

3. 通常処理と例外時の処理を区別して実行する。例外処理は対応する例外が発生した場合に限る。

3.1. 通常処理：繰返し条件「条件12を満たす（原本条件は補足説明を参照）」に従い、次の手順を繰り返す。条件を満たさなくなった場合は繰返しの後へ進む。

3.1.1. 繰返しの各回：関連情報を取得・設定する（処理13：詳細仕様参照）。

3.1.2. 繰返しの各回：関連情報を取得・設定する（処理14：詳細仕様参照）。

3.2. 通常処理：「!「対象項目」」に該当するか確認する。該当する場合に限り、次の分岐内手順を行う。該当しない場合は分岐の後へ進む。

3.2.1. 条件成立時：関連情報を取得・設定する（処理15：詳細仕様参照）。

3.2.2. 条件成立時：繰返し条件「条件16を満たす（原本条件は補足説明を参照）」に従い、次の手順を繰り返す。条件を満たさなくなった場合は繰返しの後へ進む。

3.2.2.1. 繰返しの各回：関連情報を取得・設定する（処理17：詳細仕様参照）。

3.2.3. 条件成立時：指定した条件でデータを照会する。

3.3. 通常処理：関連情報を取得・設定する（処理18：詳細仕様参照）。

3.4. 通常処理：終了時の共通後処理を行ってから、処理結果を呼出元へ返す。この経路の後続手順は実行しない。

3-例外1. 例外条件「IOException e」に該当した場合に次の手順を行う。型名は原本の表記。

3-例外1.1. 例外発生時：終了時の共通後処理を行ってから、処理の異常を通知し、この経路を終了する。この経路の後続手順は実行しない。

3-後処理. 通常終了・例外・途中のreturnのいずれでも、この範囲を抜ける前に次の共通後処理を行う。

3-後処理.1. 終了時の共通後処理：通常処理と例外時の処理を区別して実行する。例外処理は対応する例外が発生した場合に限る。

3-後処理.1.1. 通常処理：使用した接続・処理資源を解放する。

3-後処理.1-例外1. 例外条件「IOException e」に該当した場合に次の手順を行う。型名は原本の表記。

#### 結果・例外時の扱い

| 到達条件 | 結果 |
| --- | --- |
| この終了経路へ到達した場合 | 処理結果を呼出元へ返す |
| 条件19を満たす（原本条件は補足説明を参照） | 処理の異常を通知し、この経路を終了する |

### writeZipEntry

#### 処理概要

Access form処理データの日次・月次 Excel 出力で「writeZipEntry」の要求を受け付ける。入力・確認・データ操作・応答の順と、条件が成立しない場合の処理を以下に示す。

#### 処理手順

1. 関連情報を取得・設定する（処理5：詳細仕様参照）。

2. 「対象項目」を設定する。

3. 関連情報を取得・設定する（処理6：詳細仕様参照）。

4. 関連情報を取得・設定する（処理7：詳細仕様参照）。

5. 関連情報を取得・設定する（処理8：詳細仕様参照）。

### DateRange

#### 処理概要

Access form処理データの日次・月次 Excel 出力で「DateRange」の要求を受け付ける。入力・確認・データ操作・応答の順と、条件が成立しない場合の処理を以下に示す。

#### 処理手順

1. 関連情報を取得・設定する（処理3：詳細仕様参照）。

2. 関連情報を取得・設定する（処理4：詳細仕様参照）。

### ExportSpec

#### 処理概要

Access form処理データの日次・月次 Excel 出力で「ExportSpec」の要求を受け付ける。入力・確認・データ操作・応答の順と、条件が成立しない場合の処理を以下に示す。

#### 処理手順

1. 関連情報を取得・設定する（処理6：詳細仕様参照）。

2. 関連情報を取得・設定する（処理7：詳細仕様参照）。

3. 関連情報を取得・設定する（処理8：詳細仕様参照）。

4. 関連情報を取得・設定する（処理9：詳細仕様参照）。

5. 関連情報を取得・設定する（処理10：詳細仕様参照）。

### WorkbookLayout

#### 処理概要

Access form処理データの日次・月次 Excel 出力で「WorkbookLayout」の要求を受け付ける。入力・確認・データ操作・応答の順と、条件が成立しない場合の処理を以下に示す。

#### 処理手順

1. 関連情報を取得・設定する（処理4：詳細仕様参照）。

2. 関連情報を取得・設定する（処理5：詳細仕様参照）。

3. 関連情報を取得・設定する（処理6：詳細仕様参照）。

### GeneratedFile

#### 処理概要

Access form処理データの日次・月次 Excel 出力で「GeneratedFile」の要求を受け付ける。入力・確認・データ操作・応答の順と、条件が成立しない場合の処理を以下に示す。

#### 処理手順

1. 関連情報を取得・設定する（処理4：詳細仕様参照）。

2. 関連情報を取得・設定する（処理5：詳細仕様参照）。

3. 関連情報を取得・設定する（処理6：詳細仕様参照）。

### DB関連処理


## 補足説明

### 適用条件

各仮定のQA番号を確認する。静的に確認できた操作・条件を適用する。

### 処理・条件の原本対応

文書内の条件番号・処理番号は次の原本表記に対応する。完全な業務用語への置換を行っていない箇所はQA・reportで確認する。

| イベント | 参照番号 | 原本条件・処理 |
| --- | --- | --- |
| PensionBatchExportService | 処理1 | this.repository = repository |
| PensionBatchExportService | 処理2 | this.repository = repository |
| build | 処理1 | GeneratedFile file = generated.get(0) |
| build | 処理2 | PensionBatchExportResult result |
| build | 処理3 | List&lt;PensionBatchExportFileResult&gt; files = toFileResults(generated) |
| build | 条件4 | int i = 0; i &lt; specs.size(); i++ |
| build | 処理5 | generated.add(new GeneratedFile(spec, rows.size(), content)) |
| build | 処理6 | byte[] content = OpenXmlWorkbookWriter.buildWorkbook(spec.sheetName, headers, rows, layout.leadingRows, layout.mergedRanges, layout.printScale) |
| build | 処理7 | WorkbookLayout layout = buildLayout(spec, request, range, headers.size()) |
| build | 処理8 | List&lt;Object[]&gt; rows = toRows(audits, spec.type) |
| build | 処理9 | List&lt;String&gt; headers = spec.type == AuditType.NEW ? NEW_HEADERS : CHANGE_DELETE_HEADERS |
| build | 処理10 | sortAudits(audits) |
| build | 処理11 | continue |
| build | 処理12 | messages.add(emptyMessage(spec.type, request.getRunMode(), updatedBy != null)) |
| build | 処理13 | ExportSpec spec = specs.get(i) |
| build | 処理14 | List&lt;String&gt; messages = new ArrayList&lt;String&gt;() |
| build | 処理15 | List&lt;GeneratedFile&gt; generated = new ArrayList&lt;GeneratedFile&gt;() |
| build | 処理16 | List&lt;ExportSpec&gt; specs = selectedSpecs(request, updatedBy != null) |
| build | 処理17 | repository.purgeDeletedAuditsThrough(request.getDeleteCutoffDate()) |
| build | 処理18 | Integer updatedBy = parseStaffNo(request.getStaffNo()) |
| build | 処理19 | DateRange range = resolveRange(request) |
| build | 処理20 | DateRange range = resolveRange(request) |
| build | 処理21 | Integer updatedBy = parseStaffNo(request.getStaffNo()) |
| build | 処理22 | repository.purgeDeletedAuditsThrough(request.getDeleteCutoffDate()) |
| build | 処理23 | List&lt;ExportSpec&gt; specs = selectedSpecs(request, updatedBy != null) |
| build | 処理24 | List&lt;GeneratedFile&gt; generated = new ArrayList&lt;GeneratedFile&gt;() |
| build | 処理25 | List&lt;String&gt; messages = new ArrayList&lt;String&gt;() |
| build | 条件26 | int i = 0; i &lt; specs.size(); i++ |
| build | 処理27 | ExportSpec spec = specs.get(i) |
| build | 処理28 | messages.add(emptyMessage(spec.type, request.getRunMode(), updatedBy != null)) |
| build | 処理29 | continue |
| build | 処理30 | sortAudits(audits) |
| build | 処理31 | List&lt;String&gt; headers = spec.type == AuditType.NEW ? NEW_HEADERS : CHANGE_DELETE_HEADERS |
| build | 処理32 | List&lt;Object[]&gt; rows = toRows(audits, spec.type) |
| build | 処理33 | WorkbookLayout layout = buildLayout(spec, request, range, headers.size()) |
| build | 処理34 | byte[] content = OpenXmlWorkbookWriter.buildWorkbook(spec.sheetName, headers, rows, layout.leadingRows, layout.mergedRanges, layout.printScale) |
| build | 処理35 | generated.add(new GeneratedFile(spec, rows.size(), content)) |
| build | 処理36 | List&lt;PensionBatchExportFileResult&gt; files = toFileResults(generated) |
| build | 処理37 | PensionBatchExportResult result |
| build | 処理38 | GeneratedFile file = generated.get(0) |
| resolveRange | 条件1 | from.compareTo(to) &gt; 0 |
| resolveRange | 条件2 | from.compareTo(to) &gt; 0 |
| resolveRange | 条件3 | from.compareTo(to) &gt; 0 |
| resolveRange | 条件4 | NOT (from.compareTo(to) &gt; 0) |
| parseStaffNo | 条件1 | "ALL".equalsIgnoreCase(text) |
| parseStaffNo | 処理2 | String text = value == null ? "" : value.trim() |
| parseStaffNo | 処理3 | String text = value == null ? "" : value.trim() |
| parseStaffNo | 条件4 | "ALL".equalsIgnoreCase(text) |
| parseStaffNo | 条件5 | "ALL".equalsIgnoreCase(text) |
| parseStaffNo | 条件6 | NumberFormatException e |
| selectedSpecs | 処理1 | specs.add(buildSpec(AuditType.DELETED, request.getRunMode(), staffSpecified)) |
| selectedSpecs | 処理2 | specs.add(buildSpec(AuditType.CHANGED, request.getRunMode(), staffSpecified)) |
| selectedSpecs | 処理3 | specs.add(buildSpec(AuditType.NEW, request.getRunMode(), staffSpecified)) |
| selectedSpecs | 処理4 | List&lt;ExportSpec&gt; specs = new ArrayList&lt;ExportSpec&gt;() |
| selectedSpecs | 処理5 | List&lt;ExportSpec&gt; specs = new ArrayList&lt;ExportSpec&gt;() |
| selectedSpecs | 処理6 | specs.add(buildSpec(AuditType.NEW, request.getRunMode(), staffSpecified)) |
| selectedSpecs | 処理7 | specs.add(buildSpec(AuditType.CHANGED, request.getRunMode(), staffSpecified)) |
| selectedSpecs | 処理8 | specs.add(buildSpec(AuditType.DELETED, request.getRunMode(), staffSpecified)) |
| buildSpec | 処理1 | String category = type.getDisplayName() |
| buildSpec | 処理2 | String number = queryNumber &lt; 100 ? "0" + queryNumber : Integer.toString(queryNumber) |
| buildSpec | 処理3 | int queryNumber = base + (type == AuditType.NEW ? 0 : type == AuditType.CHANGED ? 10 : 20) |
| buildSpec | 処理4 | base = staffSpecified ? 10 : 40 |
| buildSpec | 処理5 | base = staffSpecified ? 70 : 100 |
| buildSpec | 処理6 | int base |
| buildSpec | 処理7 | int base |
| buildSpec | 処理8 | base = staffSpecified ? 10 : 40 |
| buildSpec | 処理9 | base = staffSpecified ? 70 : 100 |
| buildSpec | 処理10 | int queryNumber = base + (type == AuditType.NEW ? 0 : type == AuditType.CHANGED ? 10 : 20) |
| buildSpec | 処理11 | String number = queryNumber &lt; 100 ? "0" + queryNumber : Integer.toString(queryNumber) |
| buildSpec | 処理12 | String category = type.getDisplayName() |
| emptyMessage | 条件1 | staffSpecified |
| emptyMessage | 条件2 | staffSpecified |
| emptyMessage | 条件3 | staffSpecified |
| emptyMessage | 条件4 | NOT (staffSpecified) |
| sortAudits | 処理1 | Collections.sort(audits, new Comparator&lt;PensionAuditRecord&gt;() { public int compare(PensionAuditRecord left, PensionAuditRecord right) { PensionReservation a = left.getReservation(); PensionReservation b = right.getReservation(); int branch = compareInteger(a.getBranchNo(), b.getBranchNo()); if (branch != 0) { return branch; } int customer = compareInteger(a.getCustomerNo(), b.getCustomerNo()); return customer != 0 ? customer : Long.valueOf(left.getAuditId()) .compareTo(Long.valueOf(right.getAuditId())); } }) |
| sortAudits | 処理2 | Collections.sort(audits, new Comparator&lt;PensionAuditRecord&gt;() { public int compare(PensionAuditRecord left, PensionAuditRecord right) { PensionReservation a = left.getReservation(); PensionReservation b = right.getReservation(); int branch = compareInteger(a.getBranchNo(), b.getBranchNo()); if (branch != 0) { return branch; } int customer = compareInteger(a.getCustomerNo(), b.getCustomerNo()); return customer != 0 ? customer : Long.valueOf(left.getAuditId()) .compareTo(Long.valueOf(right.getAuditId())); } }) |
| toRows | 条件1 | int i = 0; i &lt; audits.size(); i++ |
| toRows | 処理2 | rows.add(new Object[] { Integer.valueOf(i + 1), wareki(row.getReservationRequestDate()), row.getKanaName(), row.getCustomerName(), row.getGender(), row.getAddress(), wareki(row.getBirthDate()), row.getPhoneNumber(), row.getPensionType(), row.getPlannedAge(), wareki(row.getClaimScheduledDate()), row.getNotes(), row.getSpouseName(), wareki(row.getSpouseBirthDate()), row.getBranchNo(), row.getCustomerNo(), staffCode(row.getStaffCode()) }) |
| toRows | 処理3 | PensionReservation row = audits.get(i).getReservation() |
| toRows | 処理4 | List&lt;Object[]&gt; rows = new ArrayList&lt;Object[]&gt;() |
| toRows | 処理5 | List&lt;Object[]&gt; rows = new ArrayList&lt;Object[]&gt;() |
| toRows | 条件6 | int i = 0; i &lt; audits.size(); i++ |
| toRows | 処理7 | PensionReservation row = audits.get(i).getReservation() |
| toRows | 処理8 | rows.add(new Object[] { Integer.valueOf(i + 1), wareki(row.getReservationRequestDate()), row.getKanaName(), row.getCustomerName(), row.getGender(), row.getAddress(), wareki(row.getBirthDate()), row.getPhoneNumber(), row.getPensionType(), row.getPlannedAge(), wareki(row.getClaimScheduledDate()), row.getNotes(), row.getSpouseName(), wareki(row.getSpouseBirthDate()), row.getBranchNo(), row.getCustomerNo(), staffCode(row.getStaffCode()) }) |
| buildLayout | 処理1 | mergedRanges.add("L5:M6") |
| buildLayout | 処理2 | mergedRanges.add("J5:K6") |
| buildLayout | 処理3 | mergedRanges.add(request.getRunMode() == PensionBatchRunMode.DAILY ? "F5:H6" : "F5:I6") |
| buildLayout | 処理4 | mergedRanges.add("D5:E6") |
| buildLayout | 処理5 | mergedRanges.add("D1:M3") |
| buildLayout | 処理6 | metaRow[11] = staff |
| buildLayout | 処理7 | metaRow[5] = period |
| buildLayout | 処理8 | titleRow[3] = spec.title |
| buildLayout | 処理9 | mergedRanges.add("N5:P6") |
| buildLayout | 処理10 | mergedRanges.add("L5:M6") |
| buildLayout | 処理11 | mergedRanges.add(request.getRunMode() == PensionBatchRunMode.DAILY ? "G5:H6" : "G5:I6") |
| buildLayout | 処理12 | mergedRanges.add("E5:F6") |
| buildLayout | 処理13 | mergedRanges.add("E1:P3") |
| buildLayout | 処理14 | metaRow[13] = staff |
| buildLayout | 処理15 | metaRow[6] = period |
| buildLayout | 処理16 | titleRow[4] = spec.title |
| buildLayout | 処理17 | Object[] metaRow = leadingRows.get(4) |
| buildLayout | 処理18 | Object[] titleRow = leadingRows.get(0) |
| buildLayout | 処理19 | String staff = request.getStaffNo() == null &#124;&#124; request.getStaffNo().trim().length() == 0 ? "ALL" : request.getStaffNo().trim() |
| buildLayout | 処理20 | String period = request.getRunMode() == PensionBatchRunMode.DAILY ? wareki(range.from) : wareki(range.from) + "～" + wareki(range.to) |
| buildLayout | 処理21 | List&lt;String&gt; mergedRanges = new ArrayList&lt;String&gt;() |
| buildLayout | 条件22 | int i = 0; i &lt; 7; i++ |
| buildLayout | 処理23 | leadingRows.add(new Object[columnCount]) |
| buildLayout | 処理24 | List&lt;Object[]&gt; leadingRows = new ArrayList&lt;Object[]&gt;() |
| buildLayout | 処理25 | List&lt;Object[]&gt; leadingRows = new ArrayList&lt;Object[]&gt;() |
| buildLayout | 条件26 | int i = 0; i &lt; 7; i++ |
| buildLayout | 処理27 | leadingRows.add(new Object[columnCount]) |
| buildLayout | 処理28 | List&lt;String&gt; mergedRanges = new ArrayList&lt;String&gt;() |
| buildLayout | 処理29 | String period = request.getRunMode() == PensionBatchRunMode.DAILY ? wareki(range.from) : wareki(range.from) + "～" + wareki(range.to) |
| buildLayout | 処理30 | String staff = request.getStaffNo() == null &#124;&#124; request.getStaffNo().trim().length() == 0 ? "ALL" : request.getStaffNo().trim() |
| buildLayout | 処理31 | Object[] titleRow = leadingRows.get(0) |
| buildLayout | 処理32 | Object[] metaRow = leadingRows.get(4) |
| buildLayout | 処理33 | titleRow[3] = spec.title |
| buildLayout | 処理34 | metaRow[5] = period |
| buildLayout | 処理35 | metaRow[11] = staff |
| buildLayout | 処理36 | mergedRanges.add("D1:M3") |
| buildLayout | 処理37 | mergedRanges.add("D5:E6") |
| buildLayout | 処理38 | mergedRanges.add(request.getRunMode() == PensionBatchRunMode.DAILY ? "F5:H6" : "F5:I6") |
| buildLayout | 処理39 | mergedRanges.add("J5:K6") |
| buildLayout | 処理40 | mergedRanges.add("L5:M6") |
| buildLayout | 処理41 | titleRow[4] = spec.title |
| buildLayout | 処理42 | metaRow[6] = period |
| buildLayout | 処理43 | metaRow[13] = staff |
| buildLayout | 処理44 | mergedRanges.add("E1:P3") |
| buildLayout | 処理45 | mergedRanges.add("E5:F6") |
| buildLayout | 処理46 | mergedRanges.add(request.getRunMode() == PensionBatchRunMode.DAILY ? "G5:H6" : "G5:I6") |
| buildLayout | 処理47 | mergedRanges.add("L5:M6") |
| buildLayout | 処理48 | mergedRanges.add("N5:P6") |
| toFileResults | 条件1 | int i = 0; i &lt; generated.size(); i++ |
| toFileResults | 処理2 | GeneratedFile file = generated.get(i) |
| toFileResults | 処理3 | List&lt;PensionBatchExportFileResult&gt; results = new ArrayList&lt;PensionBatchExportFileResult&gt;() |
| toFileResults | 処理4 | List&lt;PensionBatchExportFileResult&gt; results = new ArrayList&lt;PensionBatchExportFileResult&gt;() |
| toFileResults | 条件5 | int i = 0; i &lt; generated.size(); i++ |
| toFileResults | 処理6 | GeneratedFile file = generated.get(i) |
| buildZip | 処理1 | zip.finish() |
| buildZip | 条件2 | int i = 0; i &lt; messages.size(); i++ |
| buildZip | 処理3 | text.append(messages.get(i)).append("\r\n") |
| buildZip | 処理4 | StringBuilder text = new StringBuilder() |
| buildZip | 条件5 | int i = 0; i &lt; files.size(); i++ |
| buildZip | 処理6 | writeZipEntry(zip, file.spec.fileName, file.content) |
| buildZip | 処理7 | GeneratedFile file = files.get(i) |
| buildZip | 処理8 | ZipOutputStream zip = new ZipOutputStream(output) |
| buildZip | 処理9 | ByteArrayOutputStream output = new ByteArrayOutputStream() |
| buildZip | 処理10 | ByteArrayOutputStream output = new ByteArrayOutputStream() |
| buildZip | 処理11 | ZipOutputStream zip = new ZipOutputStream(output) |
| buildZip | 条件12 | int i = 0; i &lt; files.size(); i++ |
| buildZip | 処理13 | GeneratedFile file = files.get(i) |
| buildZip | 処理14 | writeZipEntry(zip, file.spec.fileName, file.content) |
| buildZip | 処理15 | StringBuilder text = new StringBuilder() |
| buildZip | 条件16 | int i = 0; i &lt; messages.size(); i++ |
| buildZip | 処理17 | text.append(messages.get(i)).append("\r\n") |
| buildZip | 処理18 | zip.finish() |
| buildZip | 条件19 | IOException e |
| writeZipEntry | 処理1 | zip.closeEntry() |
| writeZipEntry | 処理2 | zip.write(content) |
| writeZipEntry | 処理3 | zip.putNextEntry(entry) |
| writeZipEntry | 処理4 | ZipEntry entry = new ZipEntry(name) |
| writeZipEntry | 処理5 | ZipEntry entry = new ZipEntry(name) |
| writeZipEntry | 処理6 | zip.putNextEntry(entry) |
| writeZipEntry | 処理7 | zip.write(content) |
| writeZipEntry | 処理8 | zip.closeEntry() |
| DateRange | 処理1 | this.to = to |
| DateRange | 処理2 | this.from = from |
| DateRange | 処理3 | this.from = from |
| DateRange | 処理4 | this.to = to |
| ExportSpec | 処理1 | this.title = title |
| ExportSpec | 処理2 | this.sheetName = sheetName |
| ExportSpec | 処理3 | this.fileName = fileName |
| ExportSpec | 処理4 | this.queryName = queryName |
| ExportSpec | 処理5 | this.type = type |
| ExportSpec | 処理6 | this.type = type |
| ExportSpec | 処理7 | this.queryName = queryName |
| ExportSpec | 処理8 | this.fileName = fileName |
| ExportSpec | 処理9 | this.sheetName = sheetName |
| ExportSpec | 処理10 | this.title = title |
| WorkbookLayout | 処理1 | this.printScale = printScale |
| WorkbookLayout | 処理2 | this.mergedRanges = mergedRanges |
| WorkbookLayout | 処理3 | this.leadingRows = leadingRows |
| WorkbookLayout | 処理4 | this.leadingRows = leadingRows |
| WorkbookLayout | 処理5 | this.mergedRanges = mergedRanges |
| WorkbookLayout | 処理6 | this.printScale = printScale |
| GeneratedFile | 処理1 | this.content = content |
| GeneratedFile | 処理2 | this.rowCount = rowCount |
| GeneratedFile | 処理3 | this.spec = spec |
| GeneratedFile | 処理4 | this.spec = spec |
| GeneratedFile | 処理5 | this.rowCount = rowCount |
| GeneratedFile | 処理6 | this.content = content |

