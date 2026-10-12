# SessionAgent セッション単位生成されるエージェント 修正履歴：2005/10/21 NEC Soft, Ltd. 「FormCraft Pro. for Web」から「Form Manag

## 表紙

| 項目 | 内容 |
| --- | --- |
| 文書名 | 基本設計書 |
| システム名 |  |
| 機能ID | COM-058 |
| 画面名 | SessionAgent セッション単位生成されるエージェント 修正履歴：2005/10/21 NEC Soft, Ltd. 「FormCraft Pro. for Web」から「Form Manag |
| 会社名 |  |
| 作成日 |  |


## 概要

### 概要説明

SessionAgent セッション単位生成されるエージェント 修正履歴：2005/10/21 NEC Soft, Ltd. 「FormCraft Pro. for Web」から「Form Managの入力・表示・要求処理を行う。

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

### invalidate

#### 処理概要

SessionAgent セッション単位生成されるエージェント 修正履歴：2005/10/21 NEC Soft, Ltd. 「FormCraft Pro. for Web」から「Form Managで「invalidate」の要求を受け付ける。入力・確認・データ操作・応答の順と、条件が成立しない場合の処理を以下に示す。

#### 処理手順

1. 関連情報を取得・設定する（処理3：詳細仕様参照）。

2. 通常処理と例外時の処理を区別して実行する。例外処理は対応する例外が発生した場合に限る。

2.1. 通常処理：関連情報を取得・設定する（処理4：詳細仕様参照）。

2-例外1. 例外条件「FMSystemException e」に該当した場合に次の手順を行う。型名は原本の表記。

### getLastResponse

#### 処理概要

SessionAgent セッション単位生成されるエージェント 修正履歴：2005/10/21 NEC Soft, Ltd. 「FormCraft Pro. for Web」から「Form Managで「getLastResponse」の要求を受け付ける。入力・確認・データ操作・応答の順と、条件が成立しない場合の処理を以下に示す。

#### 処理手順

1. 処理結果を呼出元へ返す。この経路の後続手順は実行しない。

#### 結果・例外時の扱い

| 到達条件 | 結果 |
| --- | --- |
| この終了経路へ到達した場合 | 処理結果を呼出元へ返す |

### canOverlay

#### 処理概要

SessionAgent セッション単位生成されるエージェント 修正履歴：2005/10/21 NEC Soft, Ltd. 「FormCraft Pro. for Web」から「Form Managで「canOverlay」の要求を受け付ける。入力・確認・データ操作・応答の順と、条件が成立しない場合の処理を以下に示す。

#### 処理手順

1. 処理結果を呼出元へ返す。この経路の後続手順は実行しない。

#### 結果・例外時の扱い

| 到達条件 | 結果 |
| --- | --- |
| この終了経路へ到達した場合 | 処理結果を呼出元へ返す |

### getMessage

#### 処理概要

SessionAgent セッション単位生成されるエージェント 修正履歴：2005/10/21 NEC Soft, Ltd. 「FormCraft Pro. for Web」から「Form Managで「getMessage」の要求を受け付ける。入力・確認・データ操作・応答の順と、条件が成立しない場合の処理を以下に示す。

#### 処理手順

1. 処理結果を呼出元へ返す。この経路の後続手順は実行しない。

#### 結果・例外時の扱い

| 到達条件 | 結果 |
| --- | --- |
| この終了経路へ到達した場合 | 処理結果を呼出元へ返す |

### clear

#### 処理概要

SessionAgent セッション単位生成されるエージェント 修正履歴：2005/10/21 NEC Soft, Ltd. 「FormCraft Pro. for Web」から「Form Managで「clear」の要求を受け付ける。入力・確認・データ操作・応答の順と、条件が成立しない場合の処理を以下に示す。

#### 処理手順

1. 通常処理と例外時の処理を区別して実行する。例外処理は対応する例外が発生した場合に限る。

1.1. 通常処理：関連情報を取得・設定する（処理2：詳細仕様参照）。

1-例外1. 例外条件「FMIllegalStatusException e」に該当した場合に次の手順を行う。型名は原本の表記。

### setFormFileName

#### 処理概要

SessionAgent セッション単位生成されるエージェント 修正履歴：2005/10/21 NEC Soft, Ltd. 「FormCraft Pro. for Web」から「Form Managで「setFormFileName」の要求を受け付ける。入力・確認・データ操作・応答の順と、条件が成立しない場合の処理を以下に示す。

#### 処理手順

1. 関連情報を取得・設定する（処理2：詳細仕様参照）。

### setFieldData

#### 処理概要

SessionAgent セッション単位生成されるエージェント 修正履歴：2005/10/21 NEC Soft, Ltd. 「FormCraft Pro. for Web」から「Form Managで「setFieldData」の要求を受け付ける。入力・確認・データ操作・応答の順と、条件が成立しない場合の処理を以下に示す。

#### 処理手順

1. 関連情報を取得・設定する（処理2：詳細仕様参照）。

### setDestination

#### 処理概要

SessionAgent セッション単位生成されるエージェント 修正履歴：2005/10/21 NEC Soft, Ltd. 「FormCraft Pro. for Web」から「Form Managで「setDestination」の要求を受け付ける。入力・確認・データ操作・応答の順と、条件が成立しない場合の処理を以下に示す。

#### 処理手順

1. 関連情報を取得・設定する（処理2：詳細仕様参照）。

### setAction

#### 処理概要

SessionAgent セッション単位生成されるエージェント 修正履歴：2005/10/21 NEC Soft, Ltd. 「FormCraft Pro. for Web」から「Form Managで「setAction」の要求を受け付ける。入力・確認・データ操作・応答の順と、条件が成立しない場合の処理を以下に示す。

#### 処理手順

1. 関連情報を取得・設定する（処理2：詳細仕様参照）。

### setType

#### 処理概要

SessionAgent セッション単位生成されるエージェント 修正履歴：2005/10/21 NEC Soft, Ltd. 「FormCraft Pro. for Web」から「Form Managで「setType」の要求を受け付ける。入力・確認・データ操作・応答の順と、条件が成立しない場合の処理を以下に示す。

#### 処理手順

1. 関連情報を取得・設定する（処理2：詳細仕様参照）。

### setDriver

#### 処理概要

SessionAgent セッション単位生成されるエージェント 修正履歴：2005/10/21 NEC Soft, Ltd. 「FormCraft Pro. for Web」から「Form Managで「setDriver」の要求を受け付ける。入力・確認・データ操作・応答の順と、条件が成立しない場合の処理を以下に示す。

#### 処理手順

1. 関連情報を取得・設定する（処理2：詳細仕様参照）。

### setServerSaveFile

#### 処理概要

SessionAgent セッション単位生成されるエージェント 修正履歴：2005/10/21 NEC Soft, Ltd. 「FormCraft Pro. for Web」から「Form Managで「setServerSaveFile」の要求を受け付ける。入力・確認・データ操作・応答の順と、条件が成立しない場合の処理を以下に示す。

#### 処理手順

1. 関連情報を取得・設定する（処理2：詳細仕様参照）。

### parseParameters

#### 処理概要

SessionAgent セッション単位生成されるエージェント 修正履歴：2005/10/21 NEC Soft, Ltd. 「FormCraft Pro. for Web」から「Form Managで「parseParameters」の要求を受け付ける。入力・確認・データ操作・応答の順と、条件が成立しない場合の処理を以下に示す。

#### 処理手順

1. 関連情報を取得・設定する（処理13：詳細仕様参照）。

2. 関連情報を取得・設定する（処理14：詳細仕様参照）。

3. 「対象項目がある」に該当するか確認する。該当する場合に限り、次の分岐内手順を行う。該当しない場合は分岐の後へ進む。

3.1. 条件成立時：関連情報を取得・設定する（処理15：詳細仕様参照）。

3.2. 条件成立時：関連情報を取得・設定する（処理16：詳細仕様参照）。

3.3. 条件成立時：「条件17を満たす（原本条件は補足説明を参照）」に該当するか確認する。成立時と不成立時の手順を分けて行う。

3.3.1. 条件成立時：関連情報を取得・設定する（処理18：詳細仕様参照）。

3.3.2. 条件成立時：関連情報を取得・設定する（処理19：詳細仕様参照）。

3.3-別.1. 条件不成立時：関連情報を取得・設定する（処理20：詳細仕様参照）。

4. 関連情報を取得・設定する（処理21：詳細仕様参照）。

5. 関連情報を取得・設定する（処理22：詳細仕様参照）。

6. 「対象項目がある」に該当するか確認する。成立時と不成立時の手順を分けて行う。

6.1. 条件成立時：関連情報を取得・設定する（処理23：詳細仕様参照）。

6-別.1. 条件不成立時：関連情報を取得・設定する（処理24：詳細仕様参照）。

### setFMParameters

#### 処理概要

SessionAgent セッション単位生成されるエージェント 修正履歴：2005/10/21 NEC Soft, Ltd. 「FormCraft Pro. for Web」から「Form Managで「setFMParameters」の要求を受け付ける。入力・確認・データ操作・応答の順と、条件が成立しない場合の処理を以下に示す。

#### 処理手順

1. 関連情報を取得・設定する（処理4：詳細仕様参照）。

2. 関連情報を取得・設定する（処理5：詳細仕様参照）。

3. 「対象項目」を設定する。

4. 関連情報を取得・設定する（処理6：詳細仕様参照）。

5. 「対象項目」を設定する。

6. 「対象項目」を設定する。

7. 「対象項目」を設定する。

8. 「対象項目」を設定する。

### makeFieldData

#### 処理概要

SessionAgent セッション単位生成されるエージェント 修正履歴：2005/10/21 NEC Soft, Ltd. 「FormCraft Pro. for Web」から「Form Managで「makeFieldData」の要求を受け付ける。入力・確認・データ操作・応答の順と、条件が成立しない場合の処理を以下に示す。

#### 処理手順

1. 関連情報を取得・設定する（処理52：詳細仕様参照）。

2. 関連情報を取得・設定する（処理53：詳細仕様参照）。

3. 関連情報を取得・設定する（処理54：詳細仕様参照）。

4. 関連情報を取得・設定する（処理55：詳細仕様参照）。

5. 関連情報を取得・設定する（処理56：詳細仕様参照）。

6. 関連情報を取得・設定する（処理57：詳細仕様参照）。

7. 「対象項目がない、または条件58を満たす（原本条件は補足説明を参照）」に該当するか確認する。成立時と不成立時の手順を分けて行う。

7-別.1. 条件不成立時：関連情報を取得・設定する（処理59：詳細仕様参照）。

7-別.2. 条件不成立時：繰返し条件「条件60を満たす（原本条件は補足説明を参照）」に従い、次の手順を繰り返す。条件を満たさなくなった場合は繰返しの後へ進む。

7-別.2.1. 繰返しの各回：関連情報を取得・設定する（処理61：詳細仕様参照）。

8. 関連情報を取得・設定する（処理62：詳細仕様参照）。

9. 関連情報を取得・設定する（処理63：詳細仕様参照）。

10. 関連情報を取得・設定する（処理64：詳細仕様参照）。

11. 「条件65を満たす（原本条件は補足説明を参照）」に該当するか確認する。成立時と不成立時の手順を分けて行う。

11.1. 条件成立時：関連情報を取得・設定する（処理66：詳細仕様参照）。

11.2. 条件成立時：繰返し条件「条件67を満たす（原本条件は補足説明を参照）」に従い、次の手順を繰り返す。条件を満たさなくなった場合は繰返しの後へ進む。

11.2.1. 繰返しの各回：関連情報を取得・設定する（処理68：詳細仕様参照）。

11.2.2. 繰返しの各回：繰返し条件「条件69を満たす（原本条件は補足説明を参照）」に従い、次の手順を繰り返す。条件を満たさなくなった場合は繰返しの後へ進む。

11.2.2.1. 繰返しの各回：関連情報を取得・設定する（処理70：詳細仕様参照）。

11.2.2.2. 繰返しの各回：「条件71を満たす（原本条件は補足説明を参照）」に該当するか確認する。該当する場合に限り、次の分岐内手順を行う。該当しない場合は分岐の後へ進む。

11.2.2.2.1. 条件成立時：関連情報を取得・設定する（処理72：詳細仕様参照）。

11.2.2.3. 繰返しの各回：関連情報を取得・設定する（処理73：詳細仕様参照）。

11.2.2.4. 繰返しの各回：関連情報を取得・設定する（処理74：詳細仕様参照）。

11.2.2.5. 繰返しの各回：繰返し条件「条件75を満たす（原本条件は補足説明を参照）」に従い、次の手順を繰り返す。条件を満たさなくなった場合は繰返しの後へ進む。

11.2.2.5.1. 繰返しの各回：関連情報を取得・設定する（処理76：詳細仕様参照）。

11.2.2.5.2. 繰返しの各回：「条件77を満たす（原本条件は補足説明を参照）」に該当するか確認する。該当する場合に限り、次の分岐内手順を行う。該当しない場合は分岐の後へ進む。

11.2.2.5.2.1. 条件成立時：関連情報を取得・設定する（処理78：詳細仕様参照）。

11.2.2.5.3. 繰返しの各回：関連情報を取得・設定する（処理79：詳細仕様参照）。

11.2.2.5.4. 繰返しの各回：関連情報を取得・設定する（処理80：詳細仕様参照）。

11.2.3. 繰返しの各回：関連情報を取得・設定する（処理81：詳細仕様参照）。

11.2.4. 繰返しの各回：「条件82を満たす（原本条件は補足説明を参照）」に該当するか確認する。該当する場合に限り、次の分岐内手順を行う。該当しない場合は分岐の後へ進む。

11.2.4.1. 条件成立時：関連情報を取得・設定する（処理83：詳細仕様参照）。

11.2.4.2. 条件成立時：関連情報を取得・設定する（処理84：詳細仕様参照）。

11.2.4.3. 条件成立時：「対象項目がない、または条件85を満たす（原本条件は補足説明を参照）」に該当するか確認する。成立時と不成立時の手順を分けて行う。

11.2.4.3-別.1. 条件不成立時：関連情報を取得・設定する（処理86：詳細仕様参照）。

11.2.4.3-別.2. 条件不成立時：繰返し条件「条件87を満たす（原本条件は補足説明を参照）」に従い、次の手順を繰り返す。条件を満たさなくなった場合は繰返しの後へ進む。

11.2.4.3-別.2.1. 繰返しの各回：関連情報を取得・設定する（処理88：詳細仕様参照）。

11.2.4.4. 条件成立時：関連情報を取得・設定する（処理89：詳細仕様参照）。

11.2.4.5. 条件成立時：関連情報を取得・設定する（処理90：詳細仕様参照）。

11-別.1. 条件不成立時：繰返し条件「条件91を満たす（原本条件は補足説明を参照）」に従い、次の手順を繰り返す。条件を満たさなくなった場合は繰返しの後へ進む。

11-別.1.1. 繰返しの各回：関連情報を取得・設定する（処理92：詳細仕様参照）。

11-別.1.2. 繰返しの各回：「条件93を満たす（原本条件は補足説明を参照）」に該当するか確認する。該当する場合に限り、次の分岐内手順を行う。該当しない場合は分岐の後へ進む。

11-別.1.2.1. 条件成立時：関連情報を取得・設定する（処理94：詳細仕様参照）。

11-別.1.3. 繰返しの各回：関連情報を取得・設定する（処理95：詳細仕様参照）。

11-別.1.4. 繰返しの各回：関連情報を取得・設定する（処理96：詳細仕様参照）。

11-別.1.5. 繰返しの各回：繰返し条件「条件97を満たす（原本条件は補足説明を参照）」に従い、次の手順を繰り返す。条件を満たさなくなった場合は繰返しの後へ進む。

11-別.1.5.1. 繰返しの各回：関連情報を取得・設定する（処理98：詳細仕様参照）。

11-別.1.5.2. 繰返しの各回：「条件99を満たす（原本条件は補足説明を参照）」に該当するか確認する。該当する場合に限り、次の分岐内手順を行う。該当しない場合は分岐の後へ進む。

11-別.1.5.2.1. 条件成立時：関連情報を取得・設定する（処理100：詳細仕様参照）。

11-別.1.5.3. 繰返しの各回：関連情報を取得・設定する（処理101：詳細仕様参照）。

11-別.1.5.4. 繰返しの各回：関連情報を取得・設定する（処理102：詳細仕様参照）。

12. 指定した条件でデータを照会する。

13. 処理結果を呼出元へ返す。この経路の後続手順は実行しない。

#### 結果・例外時の扱い

| 到達条件 | 結果 |
| --- | --- |
| この終了経路へ到達した場合 | 処理結果を呼出元へ返す |

### resetOutputStream

#### 処理概要

SessionAgent セッション単位生成されるエージェント 修正履歴：2005/10/21 NEC Soft, Ltd. 「FormCraft Pro. for Web」から「Form Managで「resetOutputStream」の要求を受け付ける。入力・確認・データ操作・応答の順と、条件が成立しない場合の処理を以下に示す。

#### 処理手順

1. 通常処理と例外時の処理を区別して実行する。例外処理は対応する例外が発生した場合に限る。

1.1. 通常処理：「対象項目がある」に該当するか確認する。該当する場合に限り、次の分岐内手順を行う。該当しない場合は分岐の後へ進む。

1.1.1. 条件成立時：使用した接続・処理資源を解放する。

1.2. 通常処理：関連情報を取得・設定する（処理2：詳細仕様参照）。

1-例外1. 例外条件「SocketException e」に該当した場合に次の手順を行う。型名は原本の表記。

1-例外2. 例外条件「IOException e」に該当した場合に次の手順を行う。型名は原本の表記。

### setSessionTimer

#### 処理概要

SessionAgent セッション単位生成されるエージェント 修正履歴：2005/10/21 NEC Soft, Ltd. 「FormCraft Pro. for Web」から「Form Managで「setSessionTimer」の要求を受け付ける。入力・確認・データ操作・応答の順と、条件が成立しない場合の処理を以下に示す。

#### 処理手順

1. 「対象項目がない」に該当するか確認する。成立時と不成立時の手順を分けて行う。

1.1. 条件成立時：関連情報を取得・設定する（処理3：詳細仕様参照）。

1-別.1. 条件不成立時：関連情報を取得・設定する（処理4：詳細仕様参照）。

2. 「対象項目」を設定する。

3. 「対象項目」を設定する。

4. 「対象項目」を設定する。

### stopTimer

#### 処理概要

SessionAgent セッション単位生成されるエージェント 修正履歴：2005/10/21 NEC Soft, Ltd. 「FormCraft Pro. for Web」から「Form Managで「stopTimer」の要求を受け付ける。入力・確認・データ操作・応答の順と、条件が成立しない場合の処理を以下に示す。

#### 処理手順

1. 「対象項目がある」に該当するか確認する。該当する場合に限り、次の分岐内手順を行う。該当しない場合は分岐の後へ進む。

1.1. 条件成立時：関連情報を取得・設定する（処理2：詳細仕様参照）。

### getJob

#### 処理概要

SessionAgent セッション単位生成されるエージェント 修正履歴：2005/10/21 NEC Soft, Ltd. 「FormCraft Pro. for Web」から「Form Managで「getJob」の要求を受け付ける。入力・確認・データ操作・応答の順と、条件が成立しない場合の処理を以下に示す。

#### 処理手順

1. 処理結果を呼出元へ返す。この経路の後続手順は実行しない。

#### 結果・例外時の扱い

| 到達条件 | 結果 |
| --- | --- |
| この終了経路へ到達した場合 | 処理結果を呼出元へ返す |

### isCallback

#### 処理概要

SessionAgent セッション単位生成されるエージェント 修正履歴：2005/10/21 NEC Soft, Ltd. 「FormCraft Pro. for Web」から「Form Managで「isCallback」の要求を受け付ける。入力・確認・データ操作・応答の順と、条件が成立しない場合の処理を以下に示す。

#### 処理手順

1. 処理結果を呼出元へ返す。この経路の後続手順は実行しない。

#### 結果・例外時の扱い

| 到達条件 | 結果 |
| --- | --- |
| この終了経路へ到達した場合 | 処理結果を呼出元へ返す |

### getRequestHost

#### 処理概要

SessionAgent セッション単位生成されるエージェント 修正履歴：2005/10/21 NEC Soft, Ltd. 「FormCraft Pro. for Web」から「Form Managで「getRequestHost」の要求を受け付ける。入力・確認・データ操作・応答の順と、条件が成立しない場合の処理を以下に示す。

#### 処理手順

1. 処理結果を呼出元へ返す。この経路の後続手順は実行しない。

#### 結果・例外時の扱い

| 到達条件 | 結果 |
| --- | --- |
| この終了経路へ到達した場合 | 処理結果を呼出元へ返す |

### getRequestHostIP

#### 処理概要

SessionAgent セッション単位生成されるエージェント 修正履歴：2005/10/21 NEC Soft, Ltd. 「FormCraft Pro. for Web」から「Form Managで「getRequestHostIP」の要求を受け付ける。入力・確認・データ操作・応答の順と、条件が成立しない場合の処理を以下に示す。

#### 処理手順

1. 処理結果を呼出元へ返す。この経路の後続手順は実行しない。

#### 結果・例外時の扱い

| 到達条件 | 結果 |
| --- | --- |
| この終了経路へ到達した場合 | 処理結果を呼出元へ返す |

### getRequestUri

#### 処理概要

SessionAgent セッション単位生成されるエージェント 修正履歴：2005/10/21 NEC Soft, Ltd. 「FormCraft Pro. for Web」から「Form Managで「getRequestUri」の要求を受け付ける。入力・確認・データ操作・応答の順と、条件が成立しない場合の処理を以下に示す。

#### 処理手順

1. 処理結果を呼出元へ返す。この経路の後続手順は実行しない。

#### 結果・例外時の扱い

| 到達条件 | 結果 |
| --- | --- |
| この終了経路へ到達した場合 | 処理結果を呼出元へ返す |

### getUniqueId

#### 処理概要

SessionAgent セッション単位生成されるエージェント 修正履歴：2005/10/21 NEC Soft, Ltd. 「FormCraft Pro. for Web」から「Form Managで「getUniqueId」の要求を受け付ける。入力・確認・データ操作・応答の順と、条件が成立しない場合の処理を以下に示す。

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
| invalidate | 処理1 | _agent.removeJob(getJob()) |
| invalidate | 処理2 | clear() |
| invalidate | 処理3 | clear() |
| invalidate | 処理4 | _agent.removeJob(getJob()) |
| clear | 処理1 | getJob().clear() |
| clear | 処理2 | getJob().clear() |
| setFormFileName | 処理1 | getJob().getRequest().put("fm-formfilename",formFileName) |
| setFormFileName | 処理2 | getJob().getRequest().put("fm-formfilename",formFileName) |
| setFieldData | 処理1 | getJob().getRequest().put("fm-fielddata",fieldData) |
| setFieldData | 処理2 | getJob().getRequest().put("fm-fielddata",fieldData) |
| setDestination | 処理1 | getJob().getRequest().put("fm-target",dest) |
| setDestination | 処理2 | getJob().getRequest().put("fm-target",dest) |
| setAction | 処理1 | getJob().getRequest().put("fm-action",act) |
| setAction | 処理2 | getJob().getRequest().put("fm-action",act) |
| setType | 処理1 | getJob().getRequest().put("fm-outputtype",type) |
| setType | 処理2 | getJob().getRequest().put("fm-outputtype",type) |
| setDriver | 処理1 | getJob().getRequest().put("fm-driver",driver) |
| setDriver | 処理2 | getJob().getRequest().put("fm-driver",driver) |
| setServerSaveFile | 処理1 | getJob().getRequest().put("fm-outfile",fileName) |
| setServerSaveFile | 処理2 | getJob().getRequest().put("fm-outfile",fileName) |
| parseParameters | 処理1 | _callback = true |
| parseParameters | 処理2 | _callback = false |
| parseParameters | 処理3 | value = request.getParameter(RETRIEVE) |
| parseParameters | 処理4 | _requestUri = request.getRequestURI() |
| parseParameters | 処理5 | _requestHostIP = requestHostIP |
| parseParameters | 処理6 | String requestHostIP = requestHost.substring(0, pos) |
| parseParameters | 処理7 | _requestHostIP = requestHost |
| parseParameters | 条件8 | pos &gt;= 0 |
| parseParameters | 処理9 | int pos = requestHost.indexOf(":") |
| parseParameters | 処理10 | _requestHost = requestHost |
| parseParameters | 処理11 | String requestHost = request.getHeader("Host") |
| parseParameters | 処理12 | String key, value |
| parseParameters | 処理13 | String key, value |
| parseParameters | 処理14 | String requestHost = request.getHeader("Host") |
| parseParameters | 処理15 | _requestHost = requestHost |
| parseParameters | 処理16 | int pos = requestHost.indexOf(":") |
| parseParameters | 条件17 | pos &gt;= 0 |
| parseParameters | 処理18 | String requestHostIP = requestHost.substring(0, pos) |
| parseParameters | 処理19 | _requestHostIP = requestHostIP |
| parseParameters | 処理20 | _requestHostIP = requestHost |
| parseParameters | 処理21 | _requestUri = request.getRequestURI() |
| parseParameters | 処理22 | value = request.getParameter(RETRIEVE) |
| parseParameters | 処理23 | _callback = true |
| parseParameters | 処理24 | _callback = false |
| setFMParameters | 処理1 | byte[] fieldData = makeFieldData(fixedData, variableData, formCount) |
| setFMParameters | 処理2 | ServletOutputStream out = null |
| setFMParameters | 処理3 | InputStream stream = null |
| setFMParameters | 処理4 | InputStream stream = null |
| setFMParameters | 処理5 | ServletOutputStream out = null |
| setFMParameters | 処理6 | byte[] fieldData = makeFieldData(fixedData, variableData, formCount) |
| makeFieldData | 条件1 | int page = 0; page &lt; variableData.size(); page++ |
| makeFieldData | 処理2 | isFirstRow = true |
| makeFieldData | 処理3 | sb.append("[Body Data Section]\r\n") |
| makeFieldData | 条件4 | int i=0; i &lt; fixedData.length; i++ |
| makeFieldData | 処理5 | sb.append(fixedData[i][0] + "=" + QT + fixedData[i][1] + QT + "\r\n") |
| makeFieldData | 処理6 | sb.append("[Fixed Data Section]\r\n") |
| makeFieldData | 条件7 | fixedData[0][0].equals("") |
| makeFieldData | 処理8 | sb.append("NEXTPAGE\r\n") |
| makeFieldData | 処理9 | sb.append("\r\n[Form Section]\r\n") |
| makeFieldData | 条件10 | pageCount &lt; formCount |
| makeFieldData | 処理11 | pageCount++ |
| makeFieldData | 条件12 | int row = 0; row &lt; pagedata.size(); row++ |
| makeFieldData | 条件13 | int col = 0; col &lt; rowdata.size(); col++ |
| makeFieldData | 処理14 | isFirstCol = false |
| makeFieldData | 処理15 | sb.append(QT + dt + QT) |
| makeFieldData | 処理16 | sb.append(SP) |
| makeFieldData | 条件17 | !isFirstCol |
| makeFieldData | 処理18 | String dt = rowdata.get(col).toString().replaceAll("\\\\","\\\\\\\\") |
| makeFieldData | 処理19 | List rowdata = (List)pagedata.get(row) |
| makeFieldData | 処理20 | isFirstRow = false |
| makeFieldData | 処理21 | sb.append("\r\n") |
| makeFieldData | 条件22 | !isFirstRow |
| makeFieldData | 処理23 | isFirstCol = true |
| makeFieldData | 処理24 | List pagedata = (List)variableData.get(page) |
| makeFieldData | 処理25 | int pageCount = 0 |
| makeFieldData | 条件26 | int row = 0; row &lt; variableData.size(); row++ |
| makeFieldData | 条件27 | int col = 0; col &lt; rowdata.size(); col++ |
| makeFieldData | 処理28 | isFirstCol = false |
| makeFieldData | 処理29 | sb.append(QT + dt + QT) |
| makeFieldData | 処理30 | sb.append(SP) |
| makeFieldData | 条件31 | !isFirstCol |
| makeFieldData | 処理32 | String dt = rowdata.get(col).toString().replaceAll("\\\\","\\\\\\\\") |
| makeFieldData | 処理33 | List rowdata = (List)variableData.get(row) |
| makeFieldData | 処理34 | isFirstRow = false |
| makeFieldData | 処理35 | sb.append("\r\n") |
| makeFieldData | 条件36 | !isFirstRow |
| makeFieldData | 処理37 | isFirstCol = true |
| makeFieldData | 条件38 | formCount &gt; 1 |
| makeFieldData | 処理39 | boolean isFirstCol = true |
| makeFieldData | 処理40 | boolean isFirstRow = true |
| makeFieldData | 処理41 | sb.append("[Body Data Section]\r\n") |
| makeFieldData | 条件42 | int i=0 ; i &lt; fixedData.length ; i++ |
| makeFieldData | 処理43 | sb.append(fixedData[i][0] + "=" + QT + fixedData[i][1] + QT + "\r\n") |
| makeFieldData | 処理44 | sb.append("[Fixed Data Section]\r\n") |
| makeFieldData | 条件45 | fixedData[0][0].equals("") |
| makeFieldData | 処理46 | sb.append("VERSION=5.0\r\n") |
| makeFieldData | 処理47 | sb.append("[Control Section]\r\n") |
| makeFieldData | 処理48 | StringBuffer sb = new StringBuffer() |
| makeFieldData | 処理49 | byte[] fielddata = null |
| makeFieldData | 処理50 | final String QT = "\"" |
| makeFieldData | 処理51 | final String SP = "," |
| makeFieldData | 処理52 | final String SP = "," |
| makeFieldData | 処理53 | final String QT = "\"" |
| makeFieldData | 処理54 | byte[] fielddata = null |
| makeFieldData | 処理55 | StringBuffer sb = new StringBuffer() |
| makeFieldData | 処理56 | sb.append("[Control Section]\r\n") |
| makeFieldData | 処理57 | sb.append("VERSION=5.0\r\n") |
| makeFieldData | 条件58 | fixedData[0][0].equals("") |
| makeFieldData | 処理59 | sb.append("[Fixed Data Section]\r\n") |
| makeFieldData | 条件60 | int i=0 ; i &lt; fixedData.length ; i++ |
| makeFieldData | 処理61 | sb.append(fixedData[i][0] + "=" + QT + fixedData[i][1] + QT + "\r\n") |
| makeFieldData | 処理62 | sb.append("[Body Data Section]\r\n") |
| makeFieldData | 処理63 | boolean isFirstRow = true |
| makeFieldData | 処理64 | boolean isFirstCol = true |
| makeFieldData | 条件65 | formCount &gt; 1 |
| makeFieldData | 処理66 | int pageCount = 0 |
| makeFieldData | 条件67 | int page = 0; page &lt; variableData.size(); page++ |
| makeFieldData | 処理68 | List pagedata = (List)variableData.get(page) |
| makeFieldData | 条件69 | int row = 0; row &lt; pagedata.size(); row++ |
| makeFieldData | 処理70 | isFirstCol = true |
| makeFieldData | 条件71 | !isFirstRow |
| makeFieldData | 処理72 | sb.append("\r\n") |
| makeFieldData | 処理73 | isFirstRow = false |
| makeFieldData | 処理74 | List rowdata = (List)pagedata.get(row) |
| makeFieldData | 条件75 | int col = 0; col &lt; rowdata.size(); col++ |
| makeFieldData | 処理76 | String dt = rowdata.get(col).toString().replaceAll("\\\\","\\\\\\\\") |
| makeFieldData | 条件77 | !isFirstCol |
| makeFieldData | 処理78 | sb.append(SP) |
| makeFieldData | 処理79 | sb.append(QT + dt + QT) |
| makeFieldData | 処理80 | isFirstCol = false |
| makeFieldData | 処理81 | pageCount++ |
| makeFieldData | 条件82 | pageCount &lt; formCount |
| makeFieldData | 処理83 | sb.append("\r\n[Form Section]\r\n") |
| makeFieldData | 処理84 | sb.append("NEXTPAGE\r\n") |
| makeFieldData | 条件85 | fixedData[0][0].equals("") |
| makeFieldData | 処理86 | sb.append("[Fixed Data Section]\r\n") |
| makeFieldData | 条件87 | int i=0; i &lt; fixedData.length; i++ |
| makeFieldData | 処理88 | sb.append(fixedData[i][0] + "=" + QT + fixedData[i][1] + QT + "\r\n") |
| makeFieldData | 処理89 | sb.append("[Body Data Section]\r\n") |
| makeFieldData | 処理90 | isFirstRow = true |
| makeFieldData | 条件91 | int row = 0; row &lt; variableData.size(); row++ |
| makeFieldData | 処理92 | isFirstCol = true |
| makeFieldData | 条件93 | !isFirstRow |
| makeFieldData | 処理94 | sb.append("\r\n") |
| makeFieldData | 処理95 | isFirstRow = false |
| makeFieldData | 処理96 | List rowdata = (List)variableData.get(row) |
| makeFieldData | 条件97 | int col = 0; col &lt; rowdata.size(); col++ |
| makeFieldData | 処理98 | String dt = rowdata.get(col).toString().replaceAll("\\\\","\\\\\\\\") |
| makeFieldData | 条件99 | !isFirstCol |
| makeFieldData | 処理100 | sb.append(SP) |
| makeFieldData | 処理101 | sb.append(QT + dt + QT) |
| makeFieldData | 処理102 | isFirstCol = false |
| resetOutputStream | 処理1 | _outputStream = stream |
| resetOutputStream | 処理2 | _outputStream = stream |
| setSessionTimer | 処理1 | _timer = new SessionTimer(msec, handler) |
| setSessionTimer | 処理2 | _timer.cancel() |
| setSessionTimer | 処理3 | _timer = new SessionTimer(msec, handler) |
| setSessionTimer | 処理4 | _timer.cancel() |
| stopTimer | 処理1 | _timer.cancel() |
| stopTimer | 処理2 | _timer.cancel() |

