# COBOL 学生管理

2026-10-25 / `20261025-regenerate`。入力は `../../spec/COBOL/` の43ファイル（README8.5、方式別共通8.4）と全体規則16ファイルです。通常preflight59ファイルを凍結し、今回の入力版・差分・中断条件は [生成記録](build/generation/generation.md) に保存しています。

**新Text画面の生成は QA-TEXT-COBOL により中断しています。** 最新仕様は27×132の固定端末へ変更されましたが、端末製品、描画ライブラリ、入力/認証アダプターと実証環境が未決です。仕様が要求する選定・実証を推測で補えないため、既存のCGIとHTML画面は旧実装として保持します。これを新Textシステムの完成とは扱いません。`tools/regenerate.py` は通常の全再生成を停止し、`--reusable-only` でSQLカタログとDDLだけを更新できます。

今回、再利用SQL38命令の型・バインドカタログと、方式専用SQLServer DDL/seedを再生成しました。DBには接続・適用していません。旧CGI/保守CLIを既存 GnuCOBOL3.2 と Zig0.14.1 で再コンパイルし、業務境界86件、既存HTTP/確認/HTML回帰95件、静的12件を新規実行しました。[今回の検査](build/test-results/README.md) は旧実装と再利用境界だけの結果です。Text描画・キー・IME・Unicode往復・信頼認証の適合、Linux配備、実SQL、正式採点は未実施です。formalScore=null。

ソース、SQLServer資源、生成器、試験はこの方式内で完結します。仕様ID対応は [IMPLEMENTATION.md](IMPLEMENTATION.md)、中断に必要な情報は [中断記録](build/generation/interruption.json) を参照してください。

## 生成・Linuxビルド

COBOLディレクトリを作業ディレクトリにします。生成器はDBへ接続しません。

```sh
python3 tools/input_lock.py
python3 tools/regenerate.py --reusable-only
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
