# COBOL source ZIP 独立ホスト検査（20261012-build-09）

実結果: FAIL。展開済みproduction COBOL 25本をGnuCOBOLで構文検査・C変換し、CブリッジとともにWindows x64向けCGI・保守CLIへリンクしました。実行試験 0/0、コンパイラ警告 0。

- ソースZIP: `test-project1/agent-input/COBOL-source.zip`
- SHA256: `bf47077c96d4cd4687079c6dfc77cbe21b92d4b7cec92f0c6db8b198670f37de`
- 入力: `srcs/COBOL/build/source-isolation`。同梱ファイル 92件のZIP登録hashと展開hashが一致し、検査前後の入力hashも一致しました。
- 出力: 同展開先 `build/host/student.cgi.exe`、`build/host/student-maint.exe`。原本ソース・原仕様・他方式ソース・旧記録・ZIPは変更していません。
- 外部処理系: 同方式 `srcs/COBOL/build/toolchain` のGnuCOBOL 3.2 / Zig 0.14.1 / ICU・OpenSSLヘッダー/import library/runtimeとWindows ODBC32。生成Cに限る旧style prototype警告抑制を使用し、手書きCブリッジは `-Wall -Wextra -Werror` で検査しました。
- 実行: CGIの未認証401、不明role/不正percent/HTTP method/POSTサイズ不一致400、CLI usage・不在入力・不正保守種別のexit 2。SQL接続前の処理だけを実行しました。
- 全7ZIPの実member一覧・登録hashを読取監査: 375件、原仕様/evaluation/テスト・旧oracle・tools/build出力の禁止member 0件、危険path 0件。内容の逆生成採点は行っていません。
- 他方式を含むZIP登録hash不一致: VB.NET_WinForms, CSharp_WPF, CSharp_ASPNET。任意の読取監査として記録し、COBOLコンパイルの合否とは区別します。

Linux x86_64のmake・配備・CGIサーバー、実SQL Server/ODBC Driver18によるCRUD・transaction・保守、ブラウザー・実認証連携は未実施です。ホスト処理系成功をLinux配備合格として扱いません。ZIPに含めない旧境界probe試験結果も今回の実行件数には含めません。

失敗理由: syntax STAUDIT exited 1
