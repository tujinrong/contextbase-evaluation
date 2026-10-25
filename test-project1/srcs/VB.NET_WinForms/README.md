# VB.NET / WinForms 学生管理

2026-10-25、build-agent 7.7、run-id `20261025-regenerate` で、自方式の最新仕様8.1～8.4・画面最適化1.3からソースを更新しました。仕様正本は `../../spec/VB.NET_WinForms/`、入力59ファイルの版・SHA-256は [inputs.json](build/generation/inputs.json)、変更の判断は [generation.md](build/generation/generation.md) に記録します。他方式の業務実装を参照しない独立プロジェクトです。

検索は4条件、7列・8論理項目、10,000件以下の全一致を同じSNAPSHOT読取で取得し、DataGridView内をスクロールします。ページ選択・ページ移動はありません。原入力と検証済み実行条件を分け、並び替え・編集復帰では最後の実行条件を使います。選択学生ID・スクロール位置と `student-search-scroll-2`、所有者・認証セッション・フォーム・状態ID・明示期待Revision・30分期限を検査します。旧compact形式は全初期化、現行形式の廃止／未知キーは空やnullでも拒否します。

検索・編集はClientSize 1180×610、96DPI、Segoe UI 9ptの標準WinForms部品です。編集は基本、住所・本人連絡先、在籍・所属、緊急連絡先・備考・理由へ配置し、長文はカーソル移動と縦スクロールで全文を確認できます。エラー時は内容を押し下げ、狭い画面では最小幅を保ってスクロールします。確認は所有者付き別Form、取消が既定です。和暦4原入力、19登録入力／18更新入力＋生成照合値2、任意NULL、認証・保存・競合の契約を維持します。

Windows、.NET 10 SDK、Microsoft.Data.SqlClient 6.1.3、SQL Server 2022を使用します。Option Strict/Explicit/InferはOn。接続は秘密管理から `STUDENT_DB_CONNECTION` へ設定し、[DBの配備条件](database/README.md)を確認します。ORIGINAL_LOGINとDB権限を毎要求検査し、保存は方式内SQL入口が再認可・正規化・マスタ・定員・確認・版を検査します。確定不明時は再保存前の検索確認を案内します。

```powershell
python -X utf8 tools/build.py
dotnet run --project StudentManagement.WinForms.vbproj
```

最終アプリは `build/app/`、最新試験は `build/test-results/`、生成記録は `build/generation/`、配布ソースは `build/source.zip` へ固定更新します。これらはGit管理し、中間bin/obj・NuGet・試行ログは `.tmp/` に置きます。`Directory.Build.props` は直接のdotnetコマンドにも適用します。source.zipには試験・toolsを含めないため、配布ソースではproduction projectを直接ビルドします。

```powershell
dotnet publish StudentManagement.WinForms.vbproj -c Release -o .tmp/source-package-publish
```

今回のRelease build/publish、Core138件、非表示fixture39件、実フォーム245件、実.NET Framework SQLCLR23件、出力パスguard21件がPASSしました。入力・DDL型/NULL・検索SQL・維持ファイル177項目も今回確認しました。[最新結果](build/test-results/results.json)を参照してください。実フォームは方式内の架空fixtureを使い、実DBへ接続していません。通常NuGet監査は有効で、固定Pkcs9.0.4のNU1902/NU1903警告を検出しています。依存更新・監査の恒久無効化は実施していません。

SQL Server実機・保存競合/障害・SQLCLR hosting・製品認証結合・配備、DPI/IME/アクセシビリティの網羅、正式受入・逆生成採点は未実施です。SQL専用C#アセンブリーは方式内に閉じ、VB業務層は他方式DLL・共有プロジェクトを参照しません。物理表・seed・保存SQLは現仕様が変更不要と定めるため保持し、未確定のDB移行を実行しません。

仕様IDの対応は [spec-mapping.json](metadata/spec-mapping.json)。過去の生成履歴はGit、旧試行ファイルは `.tmp/legacy-work/` へ分離し、現在のPASSとして流用しません。出力は `build_paths.py` がlexical build/.tmpと祖先を検査し、入力・QAへのjunction/symlinkを拒否します。単独ビルド・`--skip-tests`は前回PASSを失効し未検証結果を記録します。
