# 年金自動受取予約管理システム Java / N2 Framework 版

`input/年金画面【W10_W11】.accdb` の解析結果を、既存 `WEB/` 版と同じ業務導線で N2 Framework の独立業務プロジェクトへ移行したものです。

## 構成

- `JSP/MENU/Login.jsp`: N2 Framework 共通認証の入口。
- `JSP/NENKIN/`: メニュー、年金CRUD、参照、帳票、Excel、日次/月次処理。
- `WEB-INF/src/nenkin/`: Action、ViewBean、JDBC Repository、帳票・Excel service。
- `WEB-INF/resources/db/`: ローカルH2と本番SQL ServerのDDL、ローカル確認データ。
- `assets/`: Access風画面CSS、共通JavaScript、和暦・西暦カレンダー。
- `tools/`: ビルド、起動、停止、スモークテスト。

## DB方針

年金データの正本はn2frameworkのJNDIデータソースです。業務Repositoryは `jdbc/RAROA_DB` の `年金1_LK`、`年金＿削除明細`、`店名テーブル`、`性別テーブル`、`裁定請求テーブル`、`受給有無テーブル`、`年金種類テーブル` をAccessと同じ表名・列名で参照し、PreparedStatementで接続します。N2ログイン成功後、ログイン職員番号を使って `jdbc/Oracle_SP2NM` の `DB2.Ｕ職員名簿表` を自動確認し、職員参照・権限判定に使う業務職員セッションを作成します。顧客基本情報は `jdbc/Oracle_DWH` の `N2_SIGHT.Ｂ顧客基本表` を使用します。年金側へ職員・顧客・店舗マスターを別名で複製しません。

`H2JndiSetupListener` は既定で無効です。ローカル用 `tools/start.ps1` だけが JVM オプション `-Dn2nenkin.localDb=true` を設定し、組み込みH2へ上記と同じ表名・必要列を作成します。正式なWebOTX配備ではこのオプションを設定せず、環境側のJNDIをそのまま使用してください。

正式環境では、配備前に `WEB-INF/resources/db/schema-raroa-sqlserver.sql` を `jdbc/RAROA_DB` の接続先SQL Serverへ実行します。DDLにはAccess由来の年金業務7表だけを含み、N2共通表、職員・顧客マスター、サンプルデータは含みません。コード表と店舗表の本番データはAccessリンク元から移行してください。アプリ実行ユーザーには7表への必要なDML権限、`jdbc/Oracle_SP2NM` の `DB2.Ｕ職員名簿表` と `jdbc/Oracle_DWH` の `N2_SIGHT.Ｂ顧客基本表` への `SELECT` 権限が必要です。SQL Server実機での適用確認は配備先環境で実施してください。

## 起動

```powershell
cd output\nenkin
powershell -NoProfile -ExecutionPolicy Bypass -File .\tools\start.ps1
```

- URL: `http://127.0.0.1:8089/n2nenkin/`
- N2ログイン職員番号: `00001234`
- パスワード: `samplepass`

ログイン成功後は同じ職員番号を職員名簿で自動確認してメニューへ遷移します。業務職員番号の再入力画面はありません。

ローカル認証情報はローカルDB有効時だけログイン画面へ表示され、本番既定では表示されません。

停止:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\tools\stop.ps1
```

## ローカル検証

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\tools\smoke-test.ps1
```

既定ポートはサンプルアプリの `8088` と競合しない `8089` です。Tomcatの実行データは `output/nenkin/.runtime/`、ローカルDBは `WEB-INF/local-db/` に生成され、Git管理対象外です。

## 根拠

- `Context/Form/`, `Context/Query/`, `Context/Module/`, `Context/Report/`
- `analysis/fact/`
- `convert/`
- `WEB/JSBRMS.Web/`
- `output/sampleapp/`
