# Access → ASP.NET Core 学生管理

2026-10-28：グループ名を内容の上方に独立した太字見出し（例：01 基本情報）で配置し、メニューを左サイドバーへ変更した。PC画面の省スペース化と、既存の権限・入力・日付・保存の契約を維持する。今回の検証は[Web見出し・サイドメニュー](build/test-results/web-shell.md)を参照。

2026-10-28：方式ID・フォルダー名を`Access-To-CSharp_ASPNET`へ変更した。Agent正本は`agents/converts/access-rebuilder-agent/`。既存DB・訓練台帳は維持し、旧名は過去の証跡内に残す。

2026-10-27。Accessから業務ルールを抽出し、利用者指定の`CSharp_ASPNET`ソースを参考にWeb向けの検索・一覧・編集へ再構築した独立方式。AR028～030により、PC向けの左見出し／右入力の表形式へ改修し、余白・入力幅・説明を整理した。生年月日・入学日・卒業退学日はカレンダー入力と和暦表示を同じ行に配置する。対象はPCブラウザー1280×650／1366×650で、スマートフォン対応は対象外。Visual Studioで[StudentManagement.slnx](StudentManagement.slnx)を開き、`StudentManagement.Web`を起動プロジェクト、`TrainingSql`を起動プロファイルにする。作成済みの専用SQL Server DBへ接続する。CLIは.NET SDK 10.0.401以降の同パッチ系列を使用する。

```powershell
dotnet build StudentManagement.slnx
```

C#／Razorは`src/`、DB構成・型対応は`database/schema/`、DDL・投入SQLは`database/sql/`、確認データは`database/seed/`、正式試験は`tests/`へ分離した。中間生成・bin/obj・NuGetは`.tmp/`、配布物・manifest・今回の検査結果は`build/`に置く。

## 今回の専用DBで起動

利用者の指定により、ローカルSQLEXPRESSに`AccessRebuilderTraining_01a17be7`を新規作成した。既存の他方式DBには接続していない。このDBは架空データと検証用主体を含む訓練専用である。

```powershell
$env:ASPNETCORE_ENVIRONMENT='Verification'
$env:Storage__Provider='SqlServer'
$env:Verification__User='verification-admin'
$env:ConnectionStrings__StudentManagement='Server=.\SQLEXPRESS;Database=AccessRebuilderTraining_01a17be7;Integrated Security=True;Encrypt=True;TrustServerCertificate=True;Application Name=AccessRebuilderTraining'
dotnet run --project src/StudentManagement.Web --urls http://127.0.0.1:5091
```

検証画面には専用環境であることを表示する。`verification-reader`は参照、`verification-staff`は学生の登録・編集、`verification-admin`はマスタと論理削除を含む操作を確認できる。SQL使用時の役割は`t_app_role`から解決する。検証用の主体指定は`Verification`環境だけで有効である。

通常環境はSQL Serverを既定とし、ホスト側の認証済み利用者と`t_app_role`が必要。サーバープロセスのWindows利用者を画面利用者として扱わず、接続失敗時にメモリへ切り替えない。IIS等のWindows認証の配備・本番TLS設定は今回の検証対象外。

## 操作確認

検索で学籍番号`TRN`、在籍区分「在学」を指定すると架空の`TRN001`と`TRN002`が表示される。結果には並び順・表示件数・ページ移動がある。新規登録は未使用番号（例`TRN003`）、氏名8文字以内、全角カナ、生年月日の日付入力、性別、郵便番号、都道府県、住所、本人連絡先、入学日を入力する。和暦は補助表示する。所属は年度2026、学年1年、訓練一組を選び、候補と人数はページを移動せず更新する。

確認データの基準日は2026-10-27、クラスの適用期間は2026-04-01～2027-03-31。期限後は対応する新しい架空データセットを作り、既存データをリセットしない。原ACCDBの学生行は移行していない。

初回構築用`tools/New-TrainingDatabase.ps1`は、既存DBがあれば変更せず停止する。今回のDBに再実行する必要はない。別の専用DBへ作成する場合は新しい`AccessRebuilderTraining_`接頭辞の名前を指定する。`002-seed.sql`は同じ管理対象の値が一致する場合に無変更で終了し、既存値が異なれば停止する。

## 検査と根拠

```powershell
dotnet run --project tests/StudentManagement.Core.Tests -- database/seed/approved-masters.json
```

今回のWeb配置・カレンダー改訂の条件と最新結果は[Web化検証](build/test-results/web-modernization.md)、先行した2回の記録は[訓練結果](build/test-results/training.md)を参照。Access本体の構造と原文は`build/generation/access-extraction.json`と`access-export/`、オブジェクト対応は`build/generation/object-map.json`、Web参照の出所と現在の入出力hashは同じ`generation/`にある。

抽出・変換・ビルド・試験と、元Accessの業務画面による受入・別Accessファイルへの一般適用性は区別する。訓練反復は最大2回で、今回の台帳は`build/generation/training.json`へ固定保存する。
