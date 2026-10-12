# SQL Server 管理者実行前レビュー

2026-10-12。対象3scriptのレビュー時SHAと実Windows PowerShell 5.1.26100.9549 検査、署名済みexe根拠は同名JSONへ保存。昇格、インストーラー起動、SQL、システム設定変更は未実施です。

明確な不備は2件です。

- INSTALL-REVIEW-001（P1、root修正確認済み）: Install L77のJapanese_XJIS_140_CI_AS_SCは無効。140にSCを付けられず、既に補助文字対応です。現在はJapanese_XJIS_140_CI_ASを確認。[Microsoft公式](https://learn.microsoft.com/en-us/sql/relational-databases/collations/collation-and-unicode-support?view=sql-server-ver17#japanese-collations-added-in-sql-server-2017)
- INSTALL-REVIEW-002（P1、root修正依頼済み）: 実PS5でGet-Command sqlcmd/sqlcmd.exeがSQLCMD16（x64 ODBC170）とSQLCMD9（x86 SQL90）の2件を返します。Setup L65/66/72/73は絶対パスを渡さず、配備scriptの複数Sourceを配列/連結文字列として扱います。modern SQLCMDの絶対パスを1個事前固定し、WPF/VBへSqlcmdPath、MVC/VueへSqlCmdPathを渡してください。推薦現在パスは `C:\Program Files\Microsoft SQL Server\Client SDK\ODBC\170\Tools\Binn\SQLCMD.EXE`。SQL実行なしに解決結果とコードで確認しました。

署名Validのbootstrap（17.0.1000.9、SHA256 FA7E1FABC9A2E9C9CDAB0D1512BCB30D2949133147DB057AC530F510E5270680）をReflectionOnlyLoadで読取り、embedded InstallerEngine.dll 3,849,728bytesのLanguageSetting属性Language/Alias=Langとsample en-USを確認。/LANG=en-USは維持できます。MediaTypeSetting.CalculateのILはExpress向けallowedValuesへenum Core(3)/LocalDB(2)を設定するため/MEDIATYPE=Coreも維持できます。helpのExpr例だけで値を変更しません。entry point/メソッドは起動していません。

3scriptの実PS5 Parseはすべて0errors。ASCII本文で、PS5のUTF8/BOM問題はありません。引数引用、サービス名のドル文字、エラーstate/exit、既存instance/DBの保護、確認済み3 LocalDB GUID、loopback限定設定、localhost SAN証明書の公開証明書のみ保存・サービスRead ACL、厳密TLS検証を読取り確認しました。実配備での稼働は未確認です。

3010の再起動要求後も次工程へ進む経路は、pending rebootで後続が失敗する可能性を運用留保として記録しました。loopbackキー/1433は実配備で検証が必要です。レビュー用PythonからPS5を起動するとCodexのPS7 module pathを継承しSecurity自動ロードが失敗しましたが、system PS5 Security module明示importと直接powershell.exe起動は成功しました。UAC launcherでの再現は未実施なので明確なlauncher不具合とは断定しません。失敗後のinstance/DBは削除・自動修復しない構成です。

CU9 17.0.5005.3 / KB5122048は[Microsoft版一覧](https://learn.microsoft.com/en-us/troubleshoot/sql/releases/sqlserver-2025/build-versions)で確認。実インストール・TLS・DB適用・非sysadmin権限・業務CRUDの合格をこのレビューは意味しません。
