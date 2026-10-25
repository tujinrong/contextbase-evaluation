# C# / WPF 学生管理

2026-10-25 配置更新：仕様入力は `test-project1/spec/CSharp_WPF/`、ソースと生成出力は `test-project1/srcs/CSharp_WPF/` に分離します。入力ロックは生成時の版・ハッシュを保持し、新しい仕様で再生成する際に検査して更新します。この配置更新ではアプリ・DBの再生成と実行試験を行っていません。

2026-10-24 配置更新。最終アプリは `build/app/`、現在の検査は `build/test-results/`、生成記録は `build/generation/`、ソース配布は `build/source.zip` へ固定更新します。これらはGit管理し、日付・run-idごとの履歴ディレクトリーは増やしません。コンパイラのbin/obj、NuGet、npm、キャッシュ、試行ログは方式内 `.tmp/`（Git除外）です。`Directory.Build.props` は通常のdotnetコマンドにも適用します。

```powershell
python -X utf8 tools/build.py
# 既知の監査警告を切り分ける場合だけ。この実行の監査を省略し、依存版は更新しない。
python -X utf8 tools/build.py --no-audit
```

この配置更新で Core 110件、非表示GUI fixture 35件、Smoke 8件、native境界102件、実.NET Framework 27件 がPASS。実DB・配備・今回の手動GUI受入は未実施です。通常restoreでは固定依存System.Security.Cryptography.Pkcs 9.0.4のNU1902/NU1903を検出します。監査を警告として扱う方式以外は通常restoreが失敗するため、今回のコンパイル検査は実行限定 `--no-audit` で切り分けました。監査は既定で有効であり、このリスクの修正は未実施です。詳細は[現在の結果](build/test-results/README.md)を参照してください。

単独ビルド／`--skip-tests` は検査済みPASSにしません。helper開始時に前回結果を失効し、今回実行した検査だけを記録します。`source.zip` は試験・toolsを含まない配布ソースなので、solutionではなくproduction projectを直接指定します。

```powershell
dotnet publish StudentManagement.Wpf.csproj -c Release -o .tmp/source-package-publish
```

独立更新版8.1／2026-10-23（入力文書ごとの版・SHAはbuild/generation/inputs.json）。原仕様は[当方式専用spec](../../spec/CSharp_WPF/README.md)。当フォルダーのCore、database、maintenance、testsだけを使用する。確定済みソースのビルド資源は当フォルダー内にあり、仕様からの再生成は上位の専用仕様も入力にする。他プロジェクトへのProjectReferenceやCompile Linkはない。

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

Core検査はUnicode・日付・正規化・導出カテゴリ・履歴操作を検証。Smokeは当WPFのXAML部品とViewModelを表示・DBなしで実行する。SQL実行用接続がない場合、integrationはSKIPと表示しDBを開かない。Windows UI受入・SQL実機競合・認証製品結合・逆生成採点を合格扱いしない。現在の結果は当方式のbuild/test-resultsへ固定更新する。

業務更新は2026-10-23に実施した。生成・検査の過去履歴はGitで管理する。

検索状態は `student-search-compact-1`。所有者・ログインセッション・画面インスタンス・状態ID・期待Revision・30分期限を照合し、旧版／形式欠落は検索状態全体を初期化して通知する。現行形式の未知／廃止条件はE-COM-003で拒否する。住所・本人電話・更新情報は一覧DTOから除き、更新日時と入学日は許可ソートにだけ残す。原仕様は変更していない。

出力パスは方式内の `build_paths.py` で検査し、lexicalなbuild/.tmpだけに書き込む。既存の祖先・操作対象ツリーにあるjunction/symlinkを拒否し、同方式spec/QAへのredirectも許可しない。Vueのfrontend/node_modulesだけは自方式.tmp/frontend/node_modulesへの専用linkを使う。旧metadataの生成・試験記録は.tmp/legacy-workへ分離し、現在の正本はbuild/generation/inputs.jsonとbuild/test-results/results.json。仕様ID対応のspec-mapping.jsonは保持する。
