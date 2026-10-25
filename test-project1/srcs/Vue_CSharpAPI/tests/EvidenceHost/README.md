# 撮影用fixtureホスト

2026-10-25／Vue_CSharpAPI／20261025-regenerate。実API Controllerと今回の `build/publish/wwwroot` を同じHTTPSホストで配信します。先に `tools/build.py` で生成してください。ソース上の旧bundleやDevelopmentの静的アセットmanifestを使わず、Productionの設定で配信先を固定します。本番コードやSQL Serverのテーブルを変更せず、tests内のIStudentServiceだけを合成データへ差し替えます。

`fixture-data.json`は仮名3学生（TEST2026-0001～0003）、テスト2クラス、当方式の002_seed.sqlから取得した70コード。学生IDはInt64の正確性を確認する9007199254740993～9007199254740995です。個人情報の実データは含みません。既定状態01/02では2件、状態をすべて外すと3件、未所属の卒業fixtureは1件です。

DBサービス登録をRemoveAllし、ConnectionStrings:StudentDbを空にします。保存・削除はForbiddenを返し、JSONもメモリーも更新しません。SQL統合・実認証基盤・実DB権限・更新業務の試験ではありません。独立契約テストのmockはその既存testプログラム内にある別fixtureであり、撮影データを契約テストの合否へ混同しません。

方式のルートで実行します。

```powershell
dotnet restore tests/EvidenceHost/EvidenceHost.csproj --locked-mode --ignore-failed-sources
dotnet run --project tests/EvidenceHost/EvidenceHost.csproj -c Release --no-restore -- --self-check
dotnet run --project tests/EvidenceHost/EvidenceHost.csproj -c Release --no-restore -- --port=7442 --minutes=60
```

撮影入口は https://localhost:7442/__evidence/login?role=Staff 。landingの /__evidence からViewer/Administratorの表示も選択できます。これはループバック限定の撮影用認証で、本番アプリの認証入口ではありません。/studentsで検索を実行して一覧を表示し、一覧から既存編集、画面の新規登録から初期登録画面を開きます。撮影・画面操作は親Agentが行います。

Cookie/CSRF cookie名はこのホスト専用。既存.NET開発証明書を使用し、本番TLSの合格にしません。ブラウザーで開発証明書が信頼されない場合はその状態を記録し、システム証明書やSQL Server設定を勝手に変更しません。

最大60分で自動終了（--minutes=1～60）。Ctrl+C、またはループバックの /__evidence/stop へPOSTして停止します。既存QA開発証明書の停止確認だけなら `curl.exe -k -X POST https://localhost:7442/__evidence/stop`。この-kを本番接続の設定へ転用しません。停止後もfixtureファイルは保持され、再起動すれば同じ合成データを読めます。

現行の独立テストは `dotnet run --project tests/ApiContracts.csproj -c Release --no-restore`、Core境界は `dotnet run --project tests/Core/StudentManagement.Core.Tests.csproj -c Release --no-restore`。現在の自己検査・接続検査はbuild/test-resultsへ固定更新します。検索は4条件だけで、専用の未所属条件はありません。共有role/SQLCLR構造衝突の修正・SQL Server統合は未実施です。

