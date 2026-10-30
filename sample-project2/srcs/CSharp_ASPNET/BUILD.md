# ソースだけからの再構築と初期配備

Windowsと.NET SDK 10.0、明示したSQL Server接続を使用します。展開先を作業ディレクトリーにして、通常のビルド入口を実行します。依存は同梱lockを使い、警告をエラーとして扱います。

```powershell
./tools/Build.ps1
```

この入口は復元・Releaseビルド・Web publishを行います。配布ZIPでは正式testsと任意のtest実行分岐を除きます。中間物は`.tmp/`、配布物は`build/publish/`です。原仕様・UI期待値・検査結果・ローカルdebug設定・user-secretsはZIPに含みません。

通常の初期設定では、管理者が明示した新規`SampleProject2_Career`だけを作成します。既存DBは停止条件で、削除/再作成/上書きしません。Windows統合認証と`Encrypt=True;TrustServerCertificate=False`を持つ接続を環境へ設定し、通常Setupを使います。

```powershell
$env:SP2_CONNECTION_STRING='Server=<管理者が指定したサーバー>;Database=SampleProject2_Career;Integrated Security=True;Encrypt=True;TrustServerCertificate=False'
dotnet run --project tools/CareerManagement.Setup -c Release --no-build -- create SampleProject2_Career
dotnet run --project tools/CareerManagement.Setup -c Release --no-build -- seed SampleProject2_Career
dotnet run --project tools/CareerManagement.Setup -c Release --no-build -- seed SampleProject2_Career
```

最初は5表を作成してから、SP2-DEMO-01 v1.1の架空20行（分類3/コード9/利用者2/社員3/経歴3）を一括投入します。公開DEMO認証はadmin/staff、共通パスワード123です。2回目は所有者・外部manifest・全業務値の一致を検査して`SkippedExactMatch`となります。差分やmanifest欠落は無変更で停止し、再投入のためにmanifestを削除しません。対話による別資格情報が必要な場合だけ、非表示入力の`seed-interactive`を使います。

Web起動にはDB自動作成/seedがありません。`SP2_DATABASE`、`SP2_CONNECTION_STRING`、環境に応じたキー保存先とHTTPS設定を管理者が明示してください。ローカル検証DBの`SP2_WebFixture_`許可範囲は専用fixture用で、通常の証明書検証を弱める根拠にはしません。既存DEMOのprofile・接続・VS設定は配布先へコピーしません。

このソースZIPの再構築は、正式UI適合・物理IME・ブラウザー履歴全経路・Excel/Office・利用者受入を証明しません。これらは対象配布物の別検査で確認し、未実施を過去のPASSで補いません。
