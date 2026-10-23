# C# / ASP.NET Core MVC 学生管理

Azure 免费测试部署（2026-10-23）：[部署、数据库账号与验证范围](deployment/README.md)。

独立生成版8.0／2026-10-12。原仕様は[当方式専用spec](spec/README.md)。当フォルダーのCore、database、maintenance、testsだけを使用する。フォルダーを単独で移してビルドできる。他プロジェクトへのProjectReferenceやCompile Linkはない。

.NET 10 SDKを使用する。

```powershell
dotnet build StudentManagement.slnx -c Release
$env:ConnectionStrings__StudentDb = 'Server=YOUR-SERVER;Database=YOUR-DB;Integrated Security=True;Encrypt=True;TrustServerCertificate=False'
dotnet run --project StudentManagement.Web.csproj --launch-profile https
```

SQL資源の作成と配備は[当方式のdatabase](database/README.md)を参照。初期値は5分類70コード、学生・クラス0。承認済みクラスは管理者が設定する。接続文字列・本番主体・秘密は環境設定で渡す。TLSとサーバー証明書検証を有効に保つ。

Secure/HttpOnly/SameSite Cookie認証、CSRF、主体・セッション・タブ所有者、受領したcontextRevisionによる状態更新を行う。LocalLoginを明示設定した単一所有者の利用者名・パスワードログイン、ログアウト、失敗回数制限を追加した。初期状態は無効。設定・Azure用資格情報は[配備手順](deployment/README.md)を参照。評価用POST /_evaluation/sessionはDevelopment環境かつEvaluationSession:Secretが設定された場合だけ有効。役割はサーバー設定で決め、要求本文から取得しない。外部認証製品との結合は未実施。

検索／登録の2画面に、原入力・正規化値・適用済み条件・読込時スナップショット・Busy・確認取消を分ける。IDと版は64bit整数。生年月日は和暦4原入力、一覧は11項目。クラス・コード保守は[当方式のmaintenance](maintenance/README.md)を使用する。

```powershell
dotnet run --project tests/Core/StudentManagement.Core.Tests.csproj -c Release
dotnet run --project tests/WebContracts.csproj -c Release --no-launch-profile
dotnet run --project database/tests/SqlServer.IntegrationTests.csproj -c Release
```

Core検査はUnicode・日付・正規化・導出カテゴリ・履歴操作を検証。HTTP契約検査は実HTTPS/Kestrelで認証・CSRF・状態・要求・応答を検査し、DBサービスは明示fakeを使用する。SQL実行用接続がない場合、integrationはSKIPと表示しDBを開かない。Windows UI受入・SQL実機競合・認証製品結合・逆生成採点を合格扱いしない。集約結果はtest-project1/test-reportに保存する。
