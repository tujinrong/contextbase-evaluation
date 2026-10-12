# WPF 専用の保存・マスタ保守入口

当方式のローカル仕様、Core、database だけで完結します。SQL Server 2022 の `student_api.prepare_save` / `persist_student` / `delete_student` / `save_class` / `save_code` が保存境界です。通常主体の表への直接 INSERT / UPDATE / DELETE を拒否し、参照用 SELECT と承認した EXECUTE だけを許可します。

`Normalization/NativeNormalizer.cs` は SQLCLR 用 .NET Framework 4.7.2 DLLです。原入力 XML を受け取り、NFKC、Unicode scalar 数、かな、和暦４項目、ISO 日付、連絡先、在籍状態、任意続柄カテゴリをサーバー側で検証・再導出します。年度は原入力４文字以内、NFKC後ASCII数字ちょうど４桁、1900～9998を専用検査します。`02026` を汎用IDとして受理しません。クラス・コードも原入力を再検証します。ファイル、通信、ネイティブ API、DB へアクセスしません。クライアント生成の検索キー・導出カテゴリは受け付けません。

生成・試験は Windows、Python 3、.NET SDK 10、.NET Framework 4.7.2 以上を使います。DLLのコンパイル用 reference assemblies は NuGet パッケージとして取得します。

```powershell
./database/native/Build-Native.ps1
dotnet run --project database/native/tests/NativeBoundary.Tests.csproj -c Release
dotnet build database/native/tests/Framework/NativeFramework.Tests.csproj -c Release
./database/native/tests/Framework/bin/Release/net472/NativeFramework.Tests.exe
./database/native/tests/Test-SqlSyntax.ps1 -ReportPath "$PWD/test-report/native-syntax.json"
```

最後の構文検査には Microsoft SQL ScriptDom が必要です。既定はインストール済み Visual Studio の DLL、別配置はスクリプトの `-ScriptDomPath` で指定します。構文検査は SQL Server への配備・権限・手続実行を確認しません。

DB管理者は空の当方式専用 DB へ `database/001_schema.sql`、`002_seed.sql`、`native/000_sqlclr.sql`、`010_student_api.sql`、`020_master_api.sql` の順で配備します。`Build-Native.ps1` は当方式の生成器から固定 SQL を再生成し、実 DLL の SHA512 とバイト列を `000_sqlclr.sql` に埋め込みます。配備時に CLR を管理者が明示的に有効化し、sysadmin または CONTROL SERVER 権限の配備主体が当 DLL のハッシュを信頼済みアセンブリへ登録します。CLR strict security を維持し、TRUSTWORTHY は有効化しません。[信頼済みアセンブリの公式手順](https://learn.microsoft.com/en-us/sql/relational-databases/system-stored-procedures/sys-sp-add-trusted-assembly-transact-sql?view=sql-server-ver15)、[SQLCLR の対応 Framework ライブラリ](https://learn.microsoft.com/en-us/sql/relational-databases/clr-integration/database-objects/supported-net-framework-libraries?view=sql-server-ver16) を参照してください。資格情報・接続文字列は資源に含めません。既存アセンブリの置換は別途変更管理が必要です。初期値の再適用は配備管理者による承認済み `002_seed.sql` の手順です。

全入口は呼出元の READ COMMITTED トランザクションを必須にし、DB主体 `ORIGINAL_LOGIN()` と役割を毎回再判定します。内部 COMMIT / ROLLBACK はありません。共通の DB applock をトランザクション所有で獲得し、最新状態・版・定員・参照・期間・保護コードを確認します。保存と CREATE / UPDATE / DELETE / DISABLE / ENABLE 監査、確認情報の消費は同じトランザクションです。監査挿入失敗を握りつぶしません。

`prepare_save` の Ready 後、`persist_student` が同じ Raw を再正規化します。重複確認は主体・セッション・対象・期待版・正規化値・**全候補** ID/版集合・期限・未消費を DB で照合します。集合が０件へ変わった場合も再確認します。UI へ表示するのは先頭20候補の学籍番号・氏名・和暦生年月日・クラスだけ、判定ハッシュは全候補ID/版をサーバー内部に保ちます。候補の住所・電話・在籍区分等を返しません。確認を待つ前に呼出元が ConfirmationRequired を COMMIT してゲートを解放します。Saved は呼出元の COMMIT 成功後に画面へ返します。その他は ROLLBACK、確定結果不明は呼出元が Unknown とし自動再送しません。

クライアント API と戻り列は [契約](INTERFACE.md)。日本語エラーは当方式のメッセージ仕様から `Core/NativeMessages.cs` に生成します。サーバーが返す field/max_length/request_id を使って項目名・上限・照合 ID を解決します。

SQLCLR DLL のビルド、原入力/正規化境界102項目、実 .NET Framework DLL27項目、SQL３ファイルの構文検査と候補４列制限検査は通過しました。SQL Server 実機の CLR ロード、手続実行、DB権限、確認永続化、監査・競合・異常時トランザクションの結合試験は未実施です。これらを構文検査や pure 試験の合格に含めません。
