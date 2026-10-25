# VB.NET / WinForms 学生管理

2026-10-25 配置更新：仕様入力は `test-project1/spec/VB.NET_WinForms/`、ソースと生成出力は `test-project1/srcs/VB.NET_WinForms/` に分離します。入力ロックは生成時の版・ハッシュを保持し、新しい仕様で再生成する際に検査して更新します。この配置更新ではアプリ・DBの再生成と実行試験を行っていません。

2026-10-24 配置更新。最終アプリは `build/app/`、現在の検査は `build/test-results/`、生成記録は `build/generation/`、ソース配布は `build/source.zip` へ固定更新します。これらはGit管理し、日付・run-idごとの履歴ディレクトリーは増やしません。コンパイラのbin/obj、NuGet、npm、キャッシュ、試行ログは方式内 `.tmp/`（Git除外）です。`Directory.Build.props` は通常のdotnetコマンドにも適用します。

```powershell
python -X utf8 tools/build.py
# 既知の監査警告を切り分ける場合だけ。この実行の監査を省略し、依存版は更新しない。
python -X utf8 tools/build.py --no-audit
```

この配置更新で Core 125件、非表示GUI fixture 36件、実.NET Framework 23件 がPASS。実DB・配備・今回の手動GUI受入は未実施です。通常restoreでは固定依存System.Security.Cryptography.Pkcs 9.0.4のNU1902/NU1903を検出します。当方式の最終restore/buildでは監査を有効に保ち、警告を記録して完了しました。この依存リスクの修正は未実施です。詳細は[現在の結果](build/test-results/README.md)を参照してください。

単独ビルド／`--skip-tests` は検査済みPASSにしません。helper開始時に前回結果を失効し、今回実行した検査だけを記録します。`source.zip` は試験・toolsを含まない配布ソースなので、solutionではなくproduction projectを直接指定します。

```powershell
dotnet publish StudentManagement.WinForms.vbproj -c Release -o .tmp/source-package-publish
```

2026-10-23更新。`../../spec/VB.NET_WinForms/` を仕様正本とする独立プロジェクトです。画面・Designer・Presenter、Application、Domain、Infrastructureの業務層はVB.NETで実装し、他方式のコード・DLL・共通プロジェクトを参照しません。DB定義・seed・生成器・保守CLI・VB試験も方式内にあります。

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
python -X utf8 tools/test_project.py
```

VB独立試験は和暦、Unicode、正規化、複合チェック、監査種別、Raw XML、型付きSQLパラメーター、非表示画面構築を実行します。保守入力はJSONの未知・重複項目を拒否し、DBが管理者を再検査します。JSON項目はDomain/ClassChange.vbまたはCodeChange.vbのcamelCaseです。処理結果と受付番号を保存し、確定不明時は照会してから再投入してください。

SQL Server実試験は `database/tests/SqlServer.IntegrationTests.vbproj` です。STUDENT_TEST_DB_CONNECTION（セットアップ用）とSTUDENT_TEST_NATIVE_DB_CONNECTION（一般アプリ主体）のどちらかが未設定ならSKIPとしてDBを開きません。同じcontextbase_test_*専用空DB、作成済みの非dbo・非db_owner・非sysadminアプリUSER、管理者によるCLR有効化とexact SHA512の信頼登録を要求します。事前条件のread-only検査後に当方式のDDL/seed/native入口を適用し、fixture内のAdmin役割にアプリUSERを追加して作成・確認・版競合・NULL往復・論理削除・監査を試験します。グローバル設定・信頼登録は変更せず、試験後の行は検査用に残します。2026年度のfixtureを使用します。

業務更新は2026-10-23に実施した。生成・検査の過去履歴はGitで管理する。

SQL Server実機、DPI/IME/アクセシビリティの網羅、実DBの競合・障害、製品認証結合、配備、逆生成採点、受入は未実施。DB専用SQLCLRは方式内の独立C#アセンブリーであり、VB業務層は独立VB.NETを維持する。生成と検査を正式受入へ読み替えない。

| 仕様 | 実装 |
| --- | --- |
| SCR-STU-001 / SRC / EV-SRC / OP-PAGE | Forms/FrmStudentSearch.*、Presenters/StudentSearchPresenter.vb |
| SCR-STU-002 / REG / EV-REG / UPD | Forms/FrmStudentEdit.*、Presenters/StudentEditPresenter.vb |
| DATE-R / UI-15 | Controls/JapaneseBirthDateControl.vb、Domain/JapaneseDateService.vb |
| 共通正規化・長さ・任意NULL | Domain/StudentNormalizer.vb、NormalizedStudent.vb、Contracts群 |
| COM-VB.NET_WinForms / DB更新・確定 | Application/StudentApplicationService.vb、Infrastructure/SqlServerStudentService.vb、NativeStoredProcedureClient.vb |
| 管理者保守 | Maintenance/Program.vb、Infrastructure/MasterMaintenanceService.vb、方式内DB入口 |

一度の移植で使用したconverter/migrationや旧source-isolationは.tmp/legacy-workへ分離し、現在のビルド・配布には使用しません。

検索状態は `student-search-compact-1`。所有者・ログインセッション・画面インスタンス・状態ID・期待Revision・30分期限を照合し、旧版／形式欠落は検索状態全体を初期化して通知する。現行形式の未知／廃止条件はE-COM-003で拒否する。住所・本人電話・更新情報は一覧DTOから除き、更新日時と入学日は許可ソートにだけ残す。原仕様は変更していない。

出力パスは方式内の `build_paths.py` で検査し、lexicalなbuild/.tmpだけに書き込む。既存の祖先・操作対象ツリーにあるjunction/symlinkを拒否し、同方式spec/QAへのredirectも許可しない。Vueのfrontend/node_modulesだけは自方式.tmp/frontend/node_modulesへの専用linkを使う。旧metadataの生成・試験記録は.tmp/legacy-workへ分離し、現在の正本はbuild/generation/inputs.jsonとbuild/test-results/results.json。仕様ID対応のspec-mapping.jsonは保持する。
