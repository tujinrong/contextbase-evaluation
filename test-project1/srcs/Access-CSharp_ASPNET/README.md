# Access → ASP.NET Core 学生管理

2026-10-27。`StudentManagement.accdb`本体の抽出内容から作成した独立方式。Visual Studioで[StudentManagement.slnx](StudentManagement.slnx)を開き、`StudentManagement.Web`を起動プロジェクト、`TrainingSql`を起動プロファイルにする。今回は作成済みの専用SQL Server DBへ接続する。CLIは.NET SDK 10.0.401以降の同パッチ系列を使用する。

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

検索で学籍番号`TRN`、在籍区分「在学」を指定すると架空の`TRN001`と`TRN002`が表示される。新規登録は未使用番号（例`TRN003`）、氏名8文字以内、全角カナ、生年月日の和暦、性別、郵便番号、都道府県、住所、本人連絡先、入学日を入力する。所属は年度2026、学年1年、訓練一組を選ぶ。新規保存後に再検索し、編集・取消・再読込み・確認操作を試せる。

確認データの基準日は2026-10-27、クラスの適用期間は2026-04-01～2027-03-31。期限後は対応する新しい架空データセットを作り、既存データをリセットしない。原ACCDBの学生行は移行していない。

初回構築用`tools/New-TrainingDatabase.ps1`は、既存DBがあれば変更せず停止する。今回のDBに再実行する必要はない。別の専用DBへ作成する場合は新しい`AccessRebuilderTraining_`接頭辞の名前を指定する。`002-seed.sql`は同じ管理対象の値が一致する場合に無変更で終了し、既存値が異なれば停止する。

## 検査と根拠

```powershell
dotnet run --project tests/StudentManagement.Core.Tests -- database/seed/approved-masters.json
```

実DB・ブラウザー検査の条件と最新結果は[訓練結果](build/test-results/training.md)を参照。Access本体の構造と原文は`build/generation/access-extraction.json`と`access-export/`、オブジェクト対応は`build/generation/object-map.json`、入力と出力hashは同じ`generation/`にある。

抽出・変換・ビルド・試験と、元Accessの業務画面による受入・別Accessファイルへの一般適用性は区別する。訓練反復は最大2回で、今回の台帳は`build/generation/training.json`へ固定保存する。
