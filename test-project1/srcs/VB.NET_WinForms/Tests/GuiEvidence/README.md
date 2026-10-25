# VB production画面ソースの撮影fixture

原本Forms/Presenters/Controls/Domain/Infrastructureを、当方式内の相対Linkで変更せずコンパイルするテスト専用プロジェクト。production Form/Presenterが具象 `StudentApplicationService` を要求するため、そのクラスだけを `IStudentService` fixtureへ委譲するテスト用同型アダプターに置換する。production実行ファイルのDB認証アダプターはこの試験に含まれない。画面・配置・イベント・入力保持処理の代替実装は作っていない。

`fixture.json` は当方式専用の仮名3件、TEST-VB学籍番号、example.invalidメール、撮影用クラス・コード。SQL接続や永続化をせず、共有DB初期データに使用しない。保存・削除は明示拒否して入力を保持する。検索初期条件では在学/休学の2件、編集入口ではTEST-VB-001を表示する。

当方式フォルダーからのコマンド:

```powershell
dotnet build Tests/GuiEvidence/GuiEvidence.vbproj
dotnet run --project Tests/GuiEvidence/GuiEvidence.vbproj -- --self-test
dotnet run --project Tests/GuiEvidence/GuiEvidence.vbproj -- --ui-regression
dotnet run --project Tests/GuiEvidence/GuiEvidence.vbproj -- --screen search
dotnet run --project Tests/GuiEvidence/GuiEvidence.vbproj -- --screen new
dotnet run --project Tests/GuiEvidence/GuiEvidence.vbproj -- --screen edit
```

任意で `--role viewer` / `--role staff` / `--role admin` を追加できる。これらは表示制御用fixtureで、Windows主体・DB roleの認可試験ではない。引数なしは使用方法を返して終了2。

`--self-test` は未表示のFormと原本Presenterで検索・読込・新規・入力保持を実行する。Show/Application.Runは呼ばず、スクリーンショットを生成しない。GUIモードは通常の原本Shownイベントで初期化する。検索画面から通常の新規登録/行の編集操作も可能。登録画面下部はスクロールして撮影する。

`--ui-regression` は実際のFormをSTAメッセージループで新規・編集・参照の順に表示し、自動で閉じる。初期フォーカス、上端スクロール、先頭行の可視性、Tab順、長文メッセージ欄の維持を18項目で検証する。DB・認可・永続化・画面撮影の検証は含まれない。

既存TestsプロジェクトにはGuiEvidenceのVBファイルをコンパイル対象から除外する1箇所の変更を加えた。productionプロジェクト・仕様・業務DDLは変更していない。他方式を参照しない。

現在の自己検査はbuild/test-results/fixture.logへ保存する。今回の配置変更では新しいGUI画像を撮影していない。過去の実画面検査はGit履歴を参照する。
