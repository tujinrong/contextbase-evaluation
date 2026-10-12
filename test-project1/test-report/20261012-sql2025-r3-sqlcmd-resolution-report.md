# SQL2025導入スクリプト sqlcmd選択訂正

2026-10-12。WPF/VBの独立Install-ProjectDatabase2025.ps1だけを訂正し、対応する導入手順を更新した。Get-Command sqlcmd.exeがmodern16と旧SQL90の2件を返す現環境で、Source配列を実行対象へ渡す不具合を修正した。

候補はVersionInfo.ProductMajorPart>=16を満たす最初の1件へ絞る。FileVersionはmodernが2022.0160.1000.06、旧版が2005.090.3042.00のように年版で始まるため、FileVersionのmajorでは判定しない。明示パスは単一ファイルへ解決し、旧版や欠落パスを拒否する。

両方式ともPowerShell Parse、既定modern単一選択、明示modern単一選択、旧ProductMajor9拒否、欠落明示パス拒否の5件PASS。Plan/PrepareOnlyをR3新IDで実行し、TSql170Parserによる方式ごと16 SQLファイルの構文エラー0件。選択した実ファイルはC:\Program Files\Microsoft SQL Server\Client SDK\ODBC\170\Tools\Binn\SQLCMD.EXE、ProductVersion16.0.1000.6である。現行script SHA256と証拠の一致を確認した。

SQL接続・sqlcmd実行・SQL実行・昇格・サーバー設定変更は行っていない。-E -N、証明書検証、既存DBの保存、exact SQLCLR hashの前条件は維持する。以前のR2レポート・Plan・SQLは保持し、新しい試験成功へ流用していない。仕様文書とnative DLL/DDLは変更していない。

- WPF: srcs/CSharp_WPF/test-report/20261012-sql2025-r3-sqlcmd-resolution.json、20261012-sql2025-r3-setup-static-results.json
- VB: srcs/VB.NET_WinForms/test-report/20261012-sql2025-r3-sqlcmd-resolution.json、20261012-sql2025-r3-setup-static-results.json

管理者wrapperはSqlcmdPathへ上記modern絶対パスを明示できる。既定でも同じmodern1件を選択する。SQL2025実配備・CLRホスト・アプリ認可/CRUDは未実施である。
