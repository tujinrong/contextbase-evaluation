# 撮影用fixtureホスト

2026-10-23／CSharp_ASPNET。検索条件スキーマ8.1に対応。Razorの実Controller/Viewを配信します。 本番コードやSQL Serverのテーブルを変更せず、tests内のIStudentServiceだけを合成データへ差し替えます。

`fixture-data.json`は仮名3学生（TEST2026-0001～0003）、テスト2クラス、当方式の002_seed.sqlから取得した70コード。学生IDはInt64の正確性を確認する9007199254740993～9007199254740995です。個人情報の実データは含みません。既定状態01/02では2件、状態をすべて外すと3件、卒業fixtureは1件です。検索条件は学籍番号・氏名・クラス・在籍区分の4項目で、一覧は7列です。住所・電話・更新日時は一覧DTOへ返しません。

DBサービス登録をRemoveAllし、ConnectionStrings:StudentDbを空にします。保存・削除はForbiddenを返し、JSONもメモリーも更新しません。SQL統合・実認証基盤・実DB権限・更新業務の試験ではありません。独立契約テストのmockはその既存testプログラム内にある別fixtureであり、撮影データを契約テストの合否へ混同しません。

方式のルートで実行します。

```powershell
dotnet restore tests/EvidenceHost/EvidenceHost.csproj --locked-mode --ignore-failed-sources
dotnet run --project tests/EvidenceHost/EvidenceHost.csproj -c Release --no-restore -- --self-check
dotnet run --project tests/EvidenceHost/EvidenceHost.csproj -c Release --no-restore -- --port=7441 --minutes=60
```

撮影入口は https://localhost:7441/__evidence/login?role=Staff 。landingの /__evidence からViewer/Administratorの表示も選択できます。これはループバック限定の撮影用認証で、本番アプリの認証入口ではありません。/studentsで検索を実行して一覧を表示し、一覧から既存編集、画面の新規登録から初期登録画面を開きます。撮影・画面操作は親Agentが行います。

Cookie/CSRF cookie名はこのホスト専用。既存.NET開発証明書を使用し、本番TLSの合格にしません。ブラウザーで開発証明書が信頼されない場合はその状態を記録し、システム証明書やSQL Server設定を勝手に変更しません。

最大60分で自動終了（--minutes=1～60）。Ctrl+C、またはループバックの /__evidence/stop へPOSTして停止します。既存QA開発証明書の停止確認だけなら `curl.exe -k -X POST https://localhost:7441/__evidence/stop`。この-kを本番接続の設定へ転用しません。停止後もfixtureファイルは保持され、再起動すれば同じ合成データを読めます。

独立テストの実行入口は `dotnet run --project tests/WebContracts.csproj -c Release --no-restore`、Core境界は `dotnet run --project tests/Core/StudentManagement.Core.Tests.csproj -c Release --no-restore`。実行結果は該当実行IDのtest-project1/test-reportを参照してください。SQL Server統合はこのfixtureホストでは実施しません。


`--ui-scenarios` はブラウザー操作専用の合成シナリオです。同じ不変3学生fixtureからプロセス内だけで24学生を生成し、20件＋4件のページングを確認できます。保存はテスト用の重複確認応答を返し、確認後の保存は意図した入力エラーを返します。業務・fixtureファイル・DBへの書込みはありません。`/__evidence/status` と `X-Evidence-UI-Scenarios` ヘッダーでこの状態を明示します。既定の3学生・保存削除拒否は維持します。

```powershell
dotnet run --project tests/EvidenceHost/EvidenceHost.csproj -c Release --no-restore -- --ui-scenarios --self-check
dotnet run --project tests/EvidenceHost/EvidenceHost.csproj -c Release --no-restore -- --ui-scenarios --port=7441 --minutes=60
```
