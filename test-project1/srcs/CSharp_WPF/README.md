# C# / WPF 学生管理

独立生成版8.0／2026-10-12。原仕様は[当方式専用spec](spec/README.md)。当フォルダーのCore、database、maintenance、testsだけを使用する。フォルダーを単独で移してビルドできる。他プロジェクトへのProjectReferenceやCompile Linkはない。

.NET 10 SDKとWindowsを使用する。

```powershell
dotnet build StudentManagement.slnx -c Release
$env:STUDENT_DB_CONNECTION = 'Server=YOUR-SERVER;Database=YOUR-DB;Integrated Security=True;Encrypt=True;TrustServerCertificate=False'
dotnet run --project StudentManagement.Wpf.csproj
```

SQL資源の作成と配備は[当方式のdatabase](database/README.md)を参照。初期値は5分類70コード、学生・クラス0。承認済みクラスは管理者が設定する。接続文字列・本番主体・秘密は環境設定で渡す。TLSとサーバー証明書検証を有効に保つ。

DB接続のORIGINAL_LOGIN()とstudent_admin/student_staff/student_viewer役割を認証主体とする。保存・削除はdatabase/nativeのEXEC入口でRaw値をDB側へ渡す。SQLCLRと手続の実DB配備・結合は未確認。

検索／登録の2画面に、原入力・正規化値・適用済み条件・読込時スナップショット・Busy・確認取消を分ける。IDと版は64bit整数。生年月日は和暦4原入力、一覧は11項目。クラス・コード保守は[当方式のmaintenance](maintenance/README.md)を使用する。

```powershell
dotnet run --project tests/Core/StudentManagement.Core.Tests.csproj -c Release
dotnet run --project tests/Smoke/NativeSmoke.csproj -c Release --no-launch-profile
dotnet run --project database/tests/SqlServer.IntegrationTests.csproj -c Release
```

Core検査はUnicode・日付・正規化・導出カテゴリ・履歴操作を検証。Smokeは当WPFのXAML部品とViewModelを表示・DBなしで実行する。SQL実行用接続がない場合、integrationはSKIPと表示しDBを開かない。Windows UI受入・SQL実機競合・認証製品結合・逆生成採点を合格扱いしない。集約結果はtest-project1/test-reportに保存する。
