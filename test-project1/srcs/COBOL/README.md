# COBOL 学生管理

2026-10-25 配置更新：仕様入力は `test-project1/spec/COBOL/`、ソースと生成出力は `test-project1/srcs/COBOL/` に分離します。入力ロックは生成時の版・ハッシュを保持し、新しい仕様で再生成する際に検査して更新します。この配置更新ではアプリ・DBの再生成と実行試験を行っていません。

COBOL/Cソース、SQLServer DDL・初期値、画面資源、ビルド・試験はこのディレクトリで扱い、仕様正本は [専用仕様](../../spec/COBOL/README.md) へ配置します。前回生成時の入力（旧 `spec/` 版8.0／8.1／8.2の49ファイル）のSHA256と文書版は `build/input-manifest.json` に保存されています。入力更新時は同名ロックを置換し、過去版はGit履歴で管理します。

検索の外部名はstudentNo／name／classId／statusCodeの4名（statusCodeだけ反復可）で、一覧は氏名／カナを同じセルにした7列へ更新しました。旧検索キーは空値でも拒否し、暗号化検索状態の所有者・セッション・画面・Revisionを確認してから `search-compact-1` を検査します。氏名raw8文字と照合値160文字を分けています。編集は全REG-001～034を維持する基本情報横並び＋下段3列です。重複、削除、取消・再読込・復帰はサーバー保持状態による別HTML確認画面で操作し、JavaScriptなしでも確認できます。

今回のWindowsホストはGnuCOBOL構文検査・C変換・リンク成功、境界／日付／保存入力86件、今回追加のHTTP／確認状態／生成HTML／SQL形状95件、静的閉包12件がPASSです。HTML試験の候補と確認状態I/Oはfixtureであり、SQL・暗号化状態テーブル・実時間による期限判定・確認後保存の実結合試験ではありません。[今回の試験記録](build/test-results/README.md)。Linux CGI配備、実SQL、実ブラウザーと正式採点は未実施です。

学生検索と学生登録・編集・参照は `STMAIN` を入口とするCGI、クラス・コード保守は公開しない `student-maint` CLIです。業務判定はCOBOL、HTTP/Unicode/暗号/ODBCの境界はCです。[仕様対応・ABI](IMPLEMENTATION.md)、[配備手順](deploy/README.md)、[DB手順](database/README.md)を参照してください。

WindowsではGnuCOBOL3.2による構文検査・C変換、Zig0.14.1のリンク、実バイナリーの境界・入力検証テストを実施しています。Linux CGI、SQLServer実接続、ブラウザー操作、競合・応答喪失試験は未実施です。ホストの成功をLinux配備の合格へ移し替えません。

## 生成・Linuxビルド

COBOLディレクトリを作業ディレクトリにします。生成器はDBへ接続しません。

```sh
python3 tools/input_lock.py
python3 tools/regenerate.py
make all
make check
```

Linux x86_64/little-endian、GnuCOBOL3.2、C11、ICU、OpenSSL、unixODBC開発ファイル、Microsoft ODBC Driver18が必要です。Makefileは `pkg-config` の `icu-uc openssl odbc` を使用します。Linux依存物の解決・取得・リンクは未実施です。[依存記録](dependencies.lock.json)のLinux欄は未解決です。配備環境で取得版・ハッシュを固定し、`build/test-results/linux/dependencies.txt` を保存してください。

## Windowsホスト検査

処理系・DLLはすべて `.tmp/toolchain/` 内です。永続PATH変更は不要です。版・取得先・SHA256は `dependencies.lock.json` と `.tmp/toolchain/msys2/packages.lock.json` に記録しています。試験の既定出力は方式内 `build/test-results/` の固定名です。同じコマンドを再実行すると最新結果で置換します。実行IDはJSON内のメタデータだけに残します。

```powershell
python tools/input_lock.py lock
python tools/host_build.py
python tools/host_tests.py
python tools/static_check.py
python tools/test_compact.py
python tools/write_report.py
```

手書きCは `-Wall -Wextra -Werror` で検査します。GnuCOBOL生成Cの旧形式プロトタイプ警告だけを `-Wno-deprecated-non-prototype` で抑制しています。DB実行をmockで代替して合格を付けていません。

保守CLIは承認したURLエンコード入力ファイルを `student-maint class file.form` または `student-maint code file.form` として受け取ります。DBの `student_admin` をTx内で再検査します。実在クラス・学生・ログインを自動生成しません。

```text
schoolYear=2026&gradeCode=00&classCode=C-A&className=Approved&validFrom=2026-04-01&validTo=2027-03-31&displayOrder=1&isActive=1
categoryId=GRADE&codeValue=01&codeName=Approved&displayOrder=1&isActive=1&validFrom=1900-01-01&expectedVersion=1&reason=Approved
```

上記は承認値への置換を要するCLI例です。接続資格情報・暗号鍵は保護したサーバー秘密管理から渡します。共通認証済みWebサーバーが信頼する利用者・セッション・権限をCGIへ設定することが前提です。

## 出力配置

`build/app/windows/` は最終CGI・保守CLI、`build/test-results/` は最新の検査結果・生ログ、`build/input-manifest.json` は現行入力ロックです。これらをGit管理し、日付別・試行別の成果履歴を並べません。親工程の固定メタデータは `build/generation/`、ソース配布は `build/source.zip` です。

`.tmp/toolchain/` に処理系、`.tmp/host/` に生成C・obj・検査exe、`.tmp/cache/` にコンパイラーキャッシュ、`.tmp/runtime/` に描画一時ファイルを置きます。Windows最終exeはruntime.jsonに示す方式内ランタイム依存を使います。Linux最終appは `build/app/linux/`、中間物・probeは `.tmp/linux/` です。`--report-dir`／COBOL_TEST_REPORT_DIRは方式内のbuild/test-resultsまたは.tmp配下だけを指定できます。試行・隔離検査は.tmpを指定してください。正式な tests/ とfixtureは削除しません。
