# VB.NET / WinForms 学生管理

2026-10-23更新。この方式内の `spec/`（検索・登録詳細／方式別共通8.1、他文書は凍結した各現行版）を入力とする独立プロジェクトです。画面・Designer・Presenter、Application、Domain、Infrastructureの業務層はVB.NETで実装し、他方式のコード・DLL・共通プロジェクトを参照しません。DB定義・seed・生成器・保守CLI・VB試験も方式内にあります。

Windows、.NET 10 SDK（検査時10.0.401）、Microsoft.Data.SqlClient 6.1.3、SQL Server 2022を使用します。Option Strict/Explicit/InferはOnです。`database/README.md` の手順で個別主体とDB入口を配備し、接続は秘密管理から環境変数 `STUDENT_DB_CONNECTION` に設定してください。

```powershell
dotnet build .\StudentManagement.WinForms.vbproj
dotnet run --project .\StudentManagement.WinForms.vbproj
```

実行主体はSQL ServerのORIGINAL_LOGIN()、権限はstudent_admin/student_staff/student_viewerから毎要求取得します。保存はstudent_api.prepare_save/persist_student、削除はdelete_student、保守はsave_class/save_codeを呼びます。原入力だけをXMLで渡し、DB側が正規化、認可、マスタ・定員・候補・版・理由を再検査します。確認待ち情報と保存結果は呼出側のトランザクションでCOMMITし、確定成功後に結果を返します。既知の拒否結果をROLLBACK済み例外で上書きせず、確定不明時は再保存前の照会を案内します。暗号化と証明書検証を強制し、共有資格情報を埋め込みません。

検索は原条件と実行済み条件を分け、20/50/100件、4種の順序、10,000件上限、30分保持を扱います。登録は19業務入力、和暦4原入力、年度・学年補助、任意NULL、元スナップショット、確認情報を分けます。不正日付を文字列のまま保持し、確認は取消を既定にします。

```powershell
dotnet run --project .\Tests\StudentManagement.WinForms.Tests.vbproj
dotnet run --project .\Maintenance\StudentMaintenance.vbproj -- class approved-input.json
python .\tools\test_project.py --run-id 20261012-run1
```

VB独立試験は和暦、Unicode、正規化、複合チェック、監査種別、Raw XML、型付きSQLパラメーター、非表示画面構築を実行します。保守入力はJSONの未知・重複項目を拒否し、DBが管理者を再検査します。JSON項目はDomain/ClassChange.vbまたはCodeChange.vbのcamelCaseです。処理結果と受付番号を保存し、確定不明時は照会してから再投入してください。

SQL Server実試験は `database/tests/SqlServer.IntegrationTests.vbproj` です。STUDENT_TEST_DB_CONNECTION（セットアップ用）とSTUDENT_TEST_NATIVE_DB_CONNECTION（一般アプリ主体）のどちらかが未設定ならSKIPとしてDBを開きません。同じcontextbase_test_*専用空DB、作成済みの非dbo・非db_owner・非sysadminアプリUSER、管理者によるCLR有効化とexact SHA512の信頼登録を要求します。事前条件のread-only検査後に当方式のDDL/seed/native入口を適用し、fixture内のAdmin役割にアプリUSERを追加して作成・確認・版競合・NULL往復・論理削除・監査を試験します。グローバル設定・信頼登録は変更せず、試験後の行は検査用に残します。2026年度のfixtureを使用します。

今回の実行IDは `20261023-vbnet-winforms-build-01`。ReleaseのSLNXとGUI fixtureは0警告/0エラー。今回の検査はCore 125件、fixture 36件、実フォームの配置・初期ActiveControl・Tab 216件、実.NET Framework 23件がPASS。実フォームは96DPI、1280×650／1366×650の各new/edit/viewerで確認し、描画PNGを保存した。検査の詳細・試行ごとの生ログは [今回の検証記録](../../test-report/20261023-vbnet-winforms-build-01/README.md)。

SQL Server実機、DPI/IME/アクセシビリティの網羅、実DBの競合・障害、製品認証結合、配備、逆生成採点、受入は未実施。DB専用SQLCLRは方式内の独立C#アセンブリーであり、VB業務層は独立VB.NETを維持する。生成と検査を正式受入へ読み替えない。

| 仕様 | 実装 |
| --- | --- |
| SCR-STU-001 / SRC / EV-SRC / OP-PAGE | Forms/FrmStudentSearch.*、Presenters/StudentSearchPresenter.vb |
| SCR-STU-002 / REG / EV-REG / UPD | Forms/FrmStudentEdit.*、Presenters/StudentEditPresenter.vb |
| DATE-R / UI-15 | Controls/JapaneseBirthDateControl.vb、Domain/JapaneseDateService.vb |
| 共通正規化・長さ・任意NULL | Domain/StudentNormalizer.vb、NormalizedStudent.vb、Contracts群 |
| COM-VB.NET_WinForms / DB更新・確定 | Application/StudentApplicationService.vb、Infrastructure/SqlServerStudentService.vb、NativeStoredProcedureClient.vb |
| 管理者保守 | Maintenance/Program.vb、Infrastructure/MasterMaintenanceService.vb、方式内DB入口 |

`build/migration` と `build/converter` は一度のVB移植で使用した開発資源です。ビルド・実行に使用せず、配布ソースから除外します。EXE/DLL/obj/cacheもsourceOnlyとは区別します。

検索状態は `student-search-compact-1`。所有者・ログインセッション・画面インスタンス・状態ID・期待Revision・30分期限を照合し、旧版／形式欠落は検索状態全体を初期化して通知する。現行形式の未知／廃止条件はE-COM-003で拒否する。住所・本人電話・更新情報は一覧DTOから除き、更新日時と入学日は許可ソートにだけ残す。原仕様は変更していない。
