# HTML画面振分処理

## 表紙

| 項目 | 内容 |
| --- | --- |
| 文書名 | 基本設計書 |
| システム名 |  |
| 機能ID | COM-051 |
| 画面名 | HTML画面振分処理 |
| 会社名 |  |
| 作成日 |  |


## 概要

### 概要説明

HTML画面振分処理の入力・表示・要求処理を行う。

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

### GoHtml

#### 処理概要

HTML画面振分処理で「GoHtml」の要求を受け付ける。入力・確認・データ操作・応答の順と、条件が成立しない場合の処理を以下に示す。

#### 処理手順

1. 「対象項目」を設定する。

2. 「対象項目」を設定する。

3. 「対象項目」を設定する。

4. 「対象項目」を設定する。

5. 関連情報を取得・設定する（処理14：詳細仕様参照）。

6. 通常処理と例外時の処理を区別して実行する。例外処理は対応する例外が発生した場合に限る。

6.1. 通常処理：「対象項目がない」に該当するか確認する。該当する場合に限り、次の分岐内手順を行う。該当しない場合は分岐の後へ進む。

6.1.1. 条件成立時：関連情報を取得・設定する（処理15：詳細仕様参照）。

6.2. 通常処理：関連情報を取得・設定する（処理16：詳細仕様参照）。

6-例外1. 例外条件「Exception e」に該当した場合に次の手順を行う。型名は原本の表記。

6-例外1.1. 例外発生時：関連情報を取得・設定する（処理17：詳細仕様参照）。

6-例外1.2. 例外発生時：「&lt;H1&gt;画面表示ができませんHtmlDispatcher&lt;BR&gt;\n」を設定する。

6-例外1.3. 例外発生時：関連情報を取得・設定する（処理18：詳細仕様参照）。

6-例外1.4. 例外発生時：関連情報を取得・設定する（処理19：詳細仕様参照）。

6-例外1.5. 例外発生時：関連情報を取得・設定する（処理20：詳細仕様参照）。

6-例外1.6. 例外発生時：関連情報を取得・設定する（処理21：詳細仕様参照）。

6-例外1.7. 例外発生時：「&lt;a href=/webap/n2cif/Ciflogin.html&gt;ログインへ&lt;/a&gt;\n」を設定する。

7. 関連情報を取得・設定する（処理22：詳細仕様参照）。

8. 関連情報を取得・設定する（処理23：詳細仕様参照）。

9. 使用した接続・処理資源を解放する。

10. 関連情報を取得・設定する（処理24：詳細仕様参照）。

11. 関連情報を取得・設定する（処理25：詳細仕様参照）。

12. 「対象項目がある」に該当するか確認する。該当する場合に限り、次の分岐内手順を行う。該当しない場合は分岐の後へ進む。

12.1. 条件成立時：通常処理と例外時の処理を区別して実行する。例外処理は対応する例外が発生した場合に限る。

12.1.1. 通常処理：関連情報を取得・設定する（処理26：詳細仕様参照）。

12.1-例外1. 例外条件「Exception e」に該当した場合に次の手順を行う。型名は原本の表記。

12.1-例外1.1. 例外発生時：「ディスパッチャ・エラー」を設定する。


## 補足説明

### 適用条件

各仮定のQA番号を確認する。静的に確認できた操作・条件を適用する。

### 処理・条件の原本対応

文書内の条件番号・処理番号は次の原本表記に対応する。完全な業務用語への置換を行っていない箇所はQA・reportで確認する。

| イベント | 参照番号 | 原本条件・処理 |
| --- | --- | --- |
| GoHtml | 処理1 | rd.forward(req,res) |
| GoHtml | 処理2 | RequestDispatcher rd =sc.getRequestDispatcher("/servlet/Bye") |
| GoHtml | 処理3 | ServletContext sc = this.getServletContext() |
| GoHtml | 処理4 | pw.println(htmlFile) |
| GoHtml | 処理5 | PrintWriter pw = res.getWriter() |
| GoHtml | 処理6 | htmlFile += "&lt;BR&gt;\n" |
| GoHtml | 処理7 | htmlFile += "&lt;BR&gt;\n" |
| GoHtml | 処理8 | htmlFile += e.getMessage() + " --&gt;\n" |
| GoHtml | 処理9 | htmlFile += "&lt;!-- Error : SubMenu File Cannot Read\n" |
| GoHtml | 処理10 | htmlFile += "&lt;BODY BGCOLOR='#d0d0d0'&gt;" |
| GoHtml | 処理11 | htmlFile = cCom.CifComonHTMLRead(htmlFileName,addHtmlData) |
| GoHtml | 処理12 | addHtmlData="" |
| GoHtml | 処理13 | String htmlFile = "" |
| GoHtml | 処理14 | String htmlFile = "" |
| GoHtml | 処理15 | addHtmlData="" |
| GoHtml | 処理16 | htmlFile = cCom.CifComonHTMLRead(htmlFileName,addHtmlData) |
| GoHtml | 処理17 | htmlFile += "&lt;BODY BGCOLOR='#d0d0d0'&gt;" |
| GoHtml | 処理18 | htmlFile += "&lt;!-- Error : SubMenu File Cannot Read\n" |
| GoHtml | 処理19 | htmlFile += e.getMessage() + " --&gt;\n" |
| GoHtml | 処理20 | htmlFile += "&lt;BR&gt;\n" |
| GoHtml | 処理21 | htmlFile += "&lt;BR&gt;\n" |
| GoHtml | 処理22 | PrintWriter pw = res.getWriter() |
| GoHtml | 処理23 | pw.println(htmlFile) |
| GoHtml | 処理24 | ServletContext sc = this.getServletContext() |
| GoHtml | 処理25 | RequestDispatcher rd =sc.getRequestDispatcher("/servlet/Bye") |
| GoHtml | 処理26 | rd.forward(req,res) |

