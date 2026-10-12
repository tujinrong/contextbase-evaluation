# VB.NET WinForms 最終独立化・native再試験

2026-10-12。入力は方式内spec46ファイル（版8.0/8.1）、ハッシュはmetadata/spec-inputs.jsonです。主アプリ・Tests・保守CLI・VB DBハーネス・SQLCLR・Framework試験の6プロジェクトを含むSLNXは0警告/0エラーです。新しいrun-idで実行し、以前のJSON・ログは保持しました。

VB実行111件PASS、実.NET Framework上のSQLCLR23件PASS、静的55件PASS、記録した11コマンドはすべて期待終了値です。実Frameworkのruntimeは4.0.30319.42000で、配備対象のRelease DLLとロードDLLのSHA512一致を確認しました。

SQLCLR SHA512: `80CB01ECF43DADE7644B55FE9583C74ED9F3B369997846401BC1E148A48CC9B780A62D356ECEF8E4B12167494F6BEACB34D868BAF10BE50250810ADED806F433`。

今回の実装訂正は学校年度の原入力を最大4 Unicode scalarで検査してからNFKC/trim・ASCII数字4桁・1900～9998へ変換することと、重複候補を学籍番号・氏名・生年月日・クラスの4表示カテゴリに限定することです。02026は拒否し、全角4桁は共通正規化規則に従って受け付けます。学生の補助年度とクラス保守年度をともに検査します。SQL生成器とVB readerも同じ返却契約へ更新しました。生年月日は既存の和暦表示に変換し、候補ID/版の照合hashはDB内で保持します。

DBハーネスはセットアップ用と一般アプリ用の2接続を要求します。専用empty contextbase_test_*、SQL Server2022、暗号化・証明書検証、既存の非dbo/db_owner/sysadminアプリUSER、CLR有効化・exact SHA512信頼登録をDDL前にread-only検査します。条件確認後に001/002/000/010/020を方式内から適用し、fixture内student_adminへアプリUSERを追加します。000のサーバー信頼登録batchは実行せず、グローバル設定・信頼登録は変更しません。今回接続設定はなく、SKIP0件でDBを開いていません。実DBの配備・CRUD・監査・競合・故障注入・権限、対話画面/IME/DPIはNOT_RUNです。

全アプリ業務層とTests/保守/DBハーネスはVB.NETです。SQLCLRだけはSAFE .NET Framework4.7.2ホスト用の独立C# DB資源です。方式外ソース・DLL・ProjectReference・生成器・仕様への依存はありません。build内の移植資源・変換器とbin/obj/cacheは配布ソースから除外します。

- [機械結果・全コマンド・終了値・入力ソースhash](20261012-isolated-final4-vb-results.json)
- [SLNX全体ビルド](20261012-isolated-final4-vb-build-solution.log)
- [nativeビルド・配備hash](20261012-isolated-final4-vb-build-native.log)
- [VB実行111件](20261012-isolated-final4-vb-boundary.log)
- [実.NET Framework23件](20261012-isolated-final4-vb-framework.log)
- [DB未接続SKIP](20261012-isolated-final4-vb-database.log)

final3は子PowerShellにGet-FileHashが存在せずnativeパッケージ生成を中断しました。そのログを保持し、方式内Build-Native.ps1を.NETのSHA512実装に置換後、final4で再実行して成功しました。passed=trueは、実DBや対話画面の合格を含みません。
