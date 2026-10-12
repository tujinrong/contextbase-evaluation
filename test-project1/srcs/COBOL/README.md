# COBOL 学生管理

このディレクトリだけで仕様、COBOL/Cソース、SQLServer DDL・初期値、画面資源、ビルド・試験を扱います。生成入力は `spec/` 版8.0／8.1の46ファイル、SHA256と文書版は `build/input-manifest.json` に固定しています。

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

Linux x86_64/little-endian、GnuCOBOL3.2、C11、ICU、OpenSSL、unixODBC開発ファイル、Microsoft ODBC Driver18が必要です。Makefileは `pkg-config` の `icu-uc openssl odbc` を使用します。Linux依存物の解決・取得・リンクは未実施です。[依存記録](dependencies.lock.json)のLinux欄は未解決です。配備環境で取得版・ハッシュを固定し、`build/linux/dependencies.txt` を保存してください。

## Windowsホスト検査

処理系・DLLはすべて `build/toolchain/` 内です。永続PATH変更は不要です。版・取得先・SHA256は `dependencies.lock.json` と `build/toolchain/msys2/packages.lock.json` に記録しています。試験の既定出力は方式内 `test-report/`、既存の連番は上書きしません。

```powershell
python tools/host_build.py 20
python tools/host_tests.py 21
python tools/static_check.py 22
```

手書きCは `-Wall -Wextra -Werror` で検査します。GnuCOBOL生成Cの旧形式プロトタイプ警告だけを `-Wno-deprecated-non-prototype` で抑制しています。DB実行をmockで代替して合格を付けていません。

保守CLIは承認したURLエンコード入力ファイルを `student-maint class file.form` または `student-maint code file.form` として受け取ります。DBの `student_admin` をTx内で再検査します。実在クラス・学生・ログインを自動生成しません。

```text
schoolYear=2026&gradeCode=00&classCode=C-A&className=Approved&validFrom=2026-04-01&validTo=2027-03-31&displayOrder=1&isActive=1
categoryId=GRADE&codeValue=01&codeName=Approved&displayOrder=1&isActive=1&validFrom=1900-01-01&expectedVersion=1&reason=Approved
```

上記は承認値への置換を要するCLI例です。接続資格情報・暗号鍵は保護したサーバー秘密管理から渡します。共通認証済みWebサーバーが信頼する利用者・セッション・権限をCGIへ設定することが前提です。
