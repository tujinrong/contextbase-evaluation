# C# / ASP.NET Core MVC 学生管理

2026-10-27：Debug/Releaseとも既定の起動設定を共有DB用に変更した。保存済みの`https`プロファイルも同じ設定で起動し、独立DBの旧設定は`Native`として残す。

`Access-To-CSharp_ASPNET`と同じローカルSQL Server DBで確認する`SharedTrainingSql`起動プロファイルを追加した。Visual Studioで`StudentManagement.Web`を起動プロジェクト、`SharedTrainingSql`をプロファイルに選ぶか、方式ルートから次を実行する。

```powershell
dotnet run --project StudentManagement.Web.csproj --launch-profile SharedTrainingSql
```

接続先は`.\SQLEXPRESS`／`AccessRebuilderTraining_01a17be7`、URLは`https://localhost:7241`。列・型の差は`StudentDatabase:Profile=SharedAccess`で対応する。共有DBに既存のNative用`database/001_schema.sql`や`002_seed.sql`を適用せず、学生・クラス・コードを初期化しない。

このプロファイルは`SharedDatabaseTraining`環境、HTTPS、ローカル接続に限定した確認用の主体を明示する。`verification-admin`の権限を共有DBの`t_app_role`から要求ごとに取得し、`Reader/Staff/Admin`を当方式の`Viewer/Staff/Administrator`へ対応付ける。役割未設定・未知値は拒否し、フォームの役割やサーバープロセス利用者を使わない。暗号化Cookieのセッションを使い、当プロファイル外では確認用Cookieを拒否する。通常のLocalLoginと評価用セッションは従来の有効化条件を維持する。

今回の共有DB検証はCore 135件、MVC契約129件、認証契約60件、実DB結合8件、両アプリ連携7件、Reader権限5件がPASS。Debugの既定起動から既存学生の検索・編集表示も確認した。[現在の共有DB検証結果](build/test-results/shared-database.md)を参照。

2026-10-25 再生成（`20261025-regenerate`）：`test-project1/spec/CSharp_ASPNET/` の索引8.5、検索詳細8.4、登録詳細8.5を入力凍結しました。独立DB定義からDDL・初期コードを再生成し、現在のソースをビルド・試験しました。検索4条件・7列と登録34項目の既存Razor/C#実装は最新契約と一致するため維持しています。詳細は [今回の生成記録](build/generation/generation.md) を参照してください。

2026-10-24 配置更新。最終アプリは `build/publish/`、現在の検査は `build/test-results/`、生成記録は `build/generation/`、ソース配布は `build/source.zip` へ固定更新します。これらはGit管理し、日付・run-idごとの履歴ディレクトリーは増やしません。コンパイラのbin/obj、NuGet、npm、キャッシュ、試行ログは方式内 `.tmp/`（Git除外）です。`Directory.Build.props` は通常のdotnetコマンドにも適用します。

```powershell
python -X utf8 tools/build.py
# 既知の監査警告を切り分ける場合だけ。この実行の監査を省略し、依存版は更新しない。
python -X utf8 tools/build.py --no-audit
```

2026-10-25の再実行では Core 114件、MVC HTTPS契約129件、ログイン契約47件、実Razor/JavaScriptのブラウザー操作53件がPASS。当時の実DB・配備・手動GUI受入は未実施です。固定依存System.Security.Cryptography.Pkcs 9.0.21を維持し、NuGet監査有効で実行しました。ブラウザー検査は不変の合成サービスを使い、SQL Serverへ接続していません。詳細は[現在の結果](build/test-results/README.md)を参照してください。

単独ビルド／`--skip-tests` は検査済みPASSにしません。helper開始時に前回結果を失効し、今回実行した検査だけを記録します。`source.zip` は試験・toolsを含まない配布ソースなので、solutionではなくproduction projectを直接指定します。

```powershell
dotnet publish StudentManagement.Web.csproj -c Release -o .tmp/source-package-publish
```

Azure 免费测试部署（2026-10-23）：[部署、数据库账号与验证范围](deployment/README.md)。

実装更新版8.2／2026-10-23（独立生成版8.0を更新）。原仕様は[当方式専用spec](../../spec/CSharp_ASPNET/README.md)。当フォルダーのCore、database、maintenance、testsだけを使用する。確定済みソースのビルド資源は当フォルダー内にあり、仕様からの再生成は上位の専用仕様も入力にする。他プロジェクトへのProjectReferenceやCompile Linkはない。

20261023-aspnet-build-01では、検索を学籍番号・氏名・クラス・在籍区分の4条件、一覧を7列へ更新した。氏名とカナは同セルへ表示し、住所・電話・更新日時は検索取得応答から除外する。検索の原入力と正規化済み条件を分離し、検索状態schemaVersion=8.1を照合する。廃止した検索項目は空値でも422、旧検索候補更新URLは404、互換性のない検索状態は409として新規検索を案内する。

.NET 10 SDKを使用する。

```powershell
dotnet build StudentManagement.slnx -c Release
$env:ConnectionStrings__StudentDb = 'Server=YOUR-SERVER;Database=YOUR-DB;Integrated Security=True;Encrypt=True;TrustServerCertificate=False'
dotnet run --project StudentManagement.Web.csproj --launch-profile Native
```

SQL資源の作成と配備は[当方式のdatabase](database/README.md)を参照。初期値は5分類70コード、学生・クラス0。承認済みクラスは管理者が設定する。接続文字列・本番主体・秘密は環境設定で渡す。TLSとサーバー証明書検証を有効に保つ。

Secure/HttpOnly/SameSite Cookie認証、CSRF、主体・セッション・タブ所有者、受領したcontextRevisionによる状態更新を行う。LocalLoginを明示設定した単一所有者の利用者名・パスワードログイン、ログアウト、失敗回数制限を追加した。初期状態は無効。設定・Azure用資格情報は[配備手順](deployment/README.md)を参照。評価用POST /_evaluation/sessionはDevelopment環境かつEvaluationSession:Secretが設定された場合だけ有効。役割はサーバー設定で決め、要求本文から取得しない。外部認証製品との結合は未実施。

検索／登録の2画面に、原入力・正規化値・適用済み条件・読込時スナップショット・Busy・確認取消を分ける。IDと版は64bit整数。生年月日は和暦4原入力。登録・編集・参照は全34項目を維持し、基本情報と下段3列へ配置する。重複・削除・変更破棄は必要時だけ別ダイアログで表示し、取消への初期フォーカスと起動元への復帰を行う。1366×650・1280×650では主要操作まで同画面に収まり、20行の検索結果は一覧内でスクロールする。狭幅・拡大時は折返しとページの縦スクロールを許容する。クラス・コード保守は[当方式のmaintenance](maintenance/README.md)を使用する。

```powershell
dotnet run --project tests/Core/StudentManagement.Core.Tests.csproj -c Release
dotnet run --project tests/WebContracts.csproj -c Release --no-launch-profile
dotnet run --project database/tests/SqlServer.IntegrationTests.csproj -c Release
```

Core検査はUnicode・日付・正規化・導出カテゴリ・履歴操作を検証。HTTP契約検査は実HTTPS/Kestrelで認証・CSRF・状態・要求・応答を検査し、DBサービスは明示fakeを使用する。SQL実行用接続がない場合、integrationはSKIPと表示しDBを開かない。Windows UI受入・SQL実機競合・認証製品結合・逆生成採点を合格扱いしない。現在の結果は当方式のbuild/test-resultsへ固定更新する。

ブラウザー検証には[方式内の撮影・UI用ホスト](tests/EvidenceHost/README.md)を使用する。Python PlaywrightとChromiumを用意し、別端末で次を実行する。UI用の保存応答は合成の重複確認・検証失敗であり、DBやfixtureファイルへ書き込まない。

```powershell
dotnet run --project tests/EvidenceHost/EvidenceHost.csproj -c Release -- --ui-scenarios --port=7443 --minutes=60
python -X utf8 tests/Browser/verify_ui.py --base-url https://localhost:7443 --output build/test-results/browser
```

現在のローカル検査結果は[build/test-results](build/test-results/README.md)。Azure配備とSQL実機試験はこの配置更新では実施していない。

出力パスは方式内の `build_paths.py` で検査し、lexicalなbuild/.tmpだけに書き込む。既存の祖先・操作対象ツリーにあるjunction/symlinkを拒否し、同方式spec/QAへのredirectも許可しない。Vueのfrontend/node_modulesだけは自方式.tmp/frontend/node_modulesへの専用linkを使う。旧metadataの生成・試験記録は.tmp/legacy-workへ分離し、現在の正本はbuild/generation/inputs.jsonとbuild/test-results/results.json。仕様ID対応のspec-mapping.jsonは保持する。

現在の配置はsample-project1（旧test-project1）。過去の生成日・runId・凍結入力パスは当時の記録として保持し、今回の改名で再生成/再検証済みとはしない。
