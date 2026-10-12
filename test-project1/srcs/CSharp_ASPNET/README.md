# C# ASP.NET Core MVC/Razor 学生管理

生成版1.0／2026-10-12。入力：仕様セット7.2＋担当詳細4文書の局所修正版7.3。業務2画面、SQL Server 2022、net10.0。生成・コンパイル・HTTP契約検査を実施。実SQL Server結合、実認証基盤、負荷・受入試験は未実施。

## 起動

```powershell
dotnet restore --locked-mode
dotnet build --no-restore
# 接続先は先に ../Database/SQLServer のDDL/seedで準備し、学校承認クラスを設定する。
$env:ConnectionStrings__StudentDb = 'Server=YOUR-SERVER;Database=YOUR-DB;Integrated Security=True;Encrypt=True;TrustServerCertificate=False'
dotnet run --launch-profile https
```

接続文字列は環境設定で渡す。接続先の証明書は検証する。SQL ServerのALLOW_SNAPSHOT_ISOLATIONが有効でなければ共有サービスが診断エラーを返す。学生値・秘密はソースへ記録しない。URLは`https://localhost:7241/students`。HTTPS開発証明書は利用環境で準備する。本番のAllowedHostsは実ホスト名へ設定し、KestrelのTLSまたは信頼元を明示したリバースプロキシ設定を採用する。

## QA-AUTH 評価用認証

共通認証基盤製品は未確定。生成したCookie認証境界は認証主体・役割・ログインセッションを信頼側から取得する。外部基盤との本番結合は未実施。

評価専用の技術入口`POST /_evaluation/session`は、Development環境かつサーバー設定`EvaluationSession:Secret`がある場合だけ有効。役割はサーバー設定のViewer／Staff／Administratorから取得し、要求本文の役割は受理しない。ログイン画面・利用者マスタは追加していない。

```powershell
$env:ASPNETCORE_ENVIRONMENT = 'Development'
$env:EvaluationSession__Secret = 'SET-A-LOCAL-TEST-SECRET'
$env:EvaluationSession__Role = 'Staff'
# HTTPクライアントのCookieセッションを保持し、HTTPSでPOSTする。
Invoke-WebRequest 'https://localhost:7241/_evaluation/session' -Method Post -Headers @{'X-Evaluation-Secret'=$env:EvaluationSession__Secret} -SessionVariable evaluationSession
```

本番では評価秘密を設定しない。実認証基盤は同一保護鍵・明示Cookieスキーム・信頼主体の連携設計を確定して結合する。転送認証ヘッダーを無条件に受け入れる処理はない。

## 実装対応

| 仕様ID | 実装 |
| --- | --- |
| SCR-STU-001／EV-SRC-001～006 | Web/Controllers/StudentsController.cs、Views/Students/Search.cshtml |
| SCR-STU-002／EV-REG-001～007 | Web/Controllers/StudentsController.cs、Views/Students/Edit.cshtml |
| SRC-001～033、REG-001～034 | 上記2View、Web/Models、Web/Inputs |
| 共通01／02、S-14 | Infrastructure/RequestIdentity.cs、WebHostSetup.cs、AntiforgeryResultFilter.cs |
| 共通12 | Infrastructure/SearchContextStore.cs（主体・セッション・タブ、hex64、30分、Revision、Context別排他） |
| UI-10／12、EV-REG-007 | Infrastructure/EditorSnapshotStore.cs、wwwroot/js/site.js、読込時スナップショットの取消・再読込確認 |
| 共通15、成功時PRG | Infrastructure/WebPresentation.cs、FlashMessageStore.cs、303復帰 |
| 共通04～11／13／14／16／17、OP-* | ../Shared/StudentManagement.Core（正規化・検査・和暦・同時保存・重複確認・監査） |
| DBDEF-SQLSERVER | ../Database/SQLServer、共有SqlServerStudentService |

JavaScriptを使用しない場合も検索・候補更新・ページ・保存をPOSTで操作可能。ブラウザー閉じる際の未保存確認はJavaScriptの離脱制御を使用する。ブラウザーのダイアログ抑止条件は実機で確認が必要。

## 検証と範囲

```powershell
dotnet run --project tests/WebContracts.csproj --no-launch-profile
```

39件のWeb契約検査を通過した。テストは実HTTPS/Kestrel、Cookie・CSRF、API／Razorを使用し、DBサービスを明示fakeへ差し替える。所有者・セッション・タブ・期限・旧版、64bitID、JSON未知／重複／型／64KiB、401／400／403／409、和暦、一覧応答の列限定、no-store、CSP、2View描画を検証した。テストクライアントだけがローカル開発証明書を許容し、製品のDB証明書検証は変更しない。

この検査はSQL Server競合、実データ保存、共有マスタ保守、認証基盤結合、ブラウザーE2E、性能、受入の合格を意味しない。検索・保存のDB処理は共有サービスの実コードを呼ぶ。本番導入前の認証製品・保護鍵・保持／消去運用・実クラスはQAとして残る。

## 管理者マスタ保守

クラス／コード保守は共有CLI `../Shared/StudentMaintenance/` を使用する。業務画面は検索／登録の2画面に保つ。CLIの実行主体はDB側のstudent_admin権限で再検査され、承認済みJSON入力を受け取る。

```powershell
$env:STUDENT_DB_CONNECTION = 'Server=YOUR-SERVER;Database=YOUR-DB;Integrated Security=True;Encrypt=True;TrustServerCertificate=False'
dotnet run --project ../Shared/StudentMaintenance/StudentMaintenance.csproj -- class approved-class.json
dotnet run --project ../Shared/StudentMaintenance/StudentMaintenance.csproj -- code approved-code.json
```

入力契約は共有Coreの `ClassChange`／`CodeChange` とCLI手順を参照する。保護値・期間・定員・参照・期待版・理由・履歴・共通ゲートをDBトランザクションで検査する。実DBでの保守結合試験は今回未実施。
