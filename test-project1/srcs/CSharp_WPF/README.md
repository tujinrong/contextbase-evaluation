# C# / WPF 学生管理

独立更新版8.1／2026-10-23（入力文書ごとの版・SHAはmetadata/spec-inputs.json）。原仕様は[当方式専用spec](spec/README.md)。当フォルダーのCore、database、maintenance、testsだけを使用する。フォルダーを単独で移してビルドできる。他プロジェクトへのProjectReferenceやCompile Linkはない。

.NET 10 SDKとWindowsを使用する。

```powershell
dotnet build StudentManagement.slnx -c Release
$env:STUDENT_DB_CONNECTION = 'Server=YOUR-SERVER;Database=YOUR-DB;Integrated Security=True;Encrypt=True;TrustServerCertificate=False'
dotnet run --project StudentManagement.Wpf.csproj
```

SQL資源の作成と配備は[当方式のdatabase](database/README.md)を参照。初期値は5分類70コード、学生・クラス0。承認済みクラスは管理者が設定する。接続文字列・本番主体・秘密は環境設定で渡す。TLSとサーバー証明書検証を有効に保つ。

DB接続のORIGINAL_LOGIN()とstudent_admin/student_staff/student_viewer役割を認証主体とする。保存・削除はdatabase/nativeのEXEC入口でRaw値をDB側へ渡す。SQLCLRと手続の実DB配備・結合は未確認。

検索／登録の2画面に、原入力・正規化値・適用済み条件・読込時スナップショット・Busy・確認取消を分ける。IDと版は64bit整数。生年月日は和暦4原入力。検索は4条件、一覧は氏名＋カナを同列にした7列。編集は基本6項目と下段3領域へ配置し、更新情報と操作バーを末尾に置く。クラス・コード保守は[当方式のmaintenance](maintenance/README.md)を使用する。

```powershell
dotnet run --project tests/Core/StudentManagement.Core.Tests.csproj -c Release
dotnet run --project tests/Smoke/NativeSmoke.csproj -c Release --no-launch-profile
dotnet run --project database/tests/SqlServer.IntegrationTests.csproj -c Release
```

Core検査はUnicode・日付・正規化・導出カテゴリ・履歴操作を検証。Smokeは当WPFのXAML部品とViewModelを表示・DBなしで実行する。SQL実行用接続がない場合、integrationはSKIPと表示しDBを開かない。Windows UI受入・SQL実機競合・認証製品結合・逆生成採点を合格扱いしない。集約結果はtest-project1/test-reportに保存する。

今回の実行IDは `20261023-csharp-wpf-build-01`。ReleaseのSLNXとGUI fixtureは0警告/0エラー。今回のCore 110件、fixture 35件、Smoke 8件、native境界102件、実.NET Framework 27件がPASS。実Windowは検索／新規／編集／参照の4起動を確認し、新規・編集・参照は1280×650／1366×650でスクロールなし。詳細は [今回の検証記録](../../test-report/20261023-csharp-wpf-build-01/README.md)。

検索状態は `student-search-compact-1`。所有者・ログインセッション・画面インスタンス・状態ID・期待Revision・30分期限を照合し、旧版／形式欠落は検索状態全体を初期化して通知する。現行形式の未知／廃止条件はE-COM-003で拒否する。住所・本人電話・更新情報は一覧DTOから除き、更新日時と入学日は許可ソートにだけ残す。原仕様は変更していない。
