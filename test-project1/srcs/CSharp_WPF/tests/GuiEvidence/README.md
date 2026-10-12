# WPF production画面の撮影fixture

架空データだけを返す `IStudentGateway` を、原本 `StudentSearchView` / `StudentEditView` とViewModelへ注入する。方式内のproductionプロジェクトを参照し、他方式のコード・仕様・DBを参照しない。SQL接続、Windows主体の認可、CRUD永続化はこのfixtureの対象外。保存・削除は明示拒否して入力を保持する。

`fixture.json` は当方式専用の仮名3件、TEST-WPF学籍番号、example.invalidメール、撮影用クラス・コードを収録する。共有SQLの配備初期データとして使用しない。検索初期条件では在学/休学の2件、編集入口ではTEST-WPF-001を表示する。

当方式フォルダーからのコマンド:

```powershell
dotnet build tests/GuiEvidence/GuiEvidence.csproj
dotnet tests/GuiEvidence/bin/Debug/net10.0-windows/Wpf.GuiEvidence.dll --self-test
tests/GuiEvidence/bin/Debug/net10.0-windows/Wpf.GuiEvidence.exe --screen search
tests/GuiEvidence/bin/Debug/net10.0-windows/Wpf.GuiEvidence.exe --screen new
tests/GuiEvidence/bin/Debug/net10.0-windows/Wpf.GuiEvidence.exe --screen edit
```

任意で `--role viewer` / `--role staff` / `--role admin` を追加できる。権限表示のfixture値でありDB認可合格ではない。引数を指定しない起動は使用方法を返して終了2。

`--self-test` はWindowとViewModelを生成して検索・読込・新規初期値・入力保持を検査するが、Show/Runを呼ばず、スクリーンショットを作らない。GUIモードでは通常のApplicationへ、原本App.xamlから無変更コピーしたProduction.App.xmlのApplication.Resourcesを読み込み、原本Windowを使用する。production AppのSQL起動は呼ばない。検索画面から通常の新規登録/行の開く操作も可能。編集画面下部はスクロールして撮影する。

`--verify-startup search` / `--verify-startup new` / `--verify-startup edit` は実Application.RunとWindow.Showを実行し、ContentRenderedでVisible/Loaded/HWND/resourcesとfixture値を検査して自動で閉じる。検索モードでは実ComboBoxの初期「すべて」、選択したクラスの保持、クリア、未所属、不適合クラス解除をfixtureで検査する。手動操作・撮影・SQL接続はしない。

初回の実Runで発見したApp継承のresource初期化不良はテストハーネスだけで修正した。続く実新規画面で、productionクラス候補のlong選択キーと空文字raw入力の変換例外を検出したため、ClassOption.Valueを文字列キーとして登録画面へバインドした。業務StudentDraft.ClassIdと検索画面のIDは従来どおりlong?のまま。

実検索画面で見つかった「すべて」の空表示も修正した。学年・都道府県の検索専用キーはNULL、クラスのSelectedItemはNULL条件に対応する「すべて」候補へ一致させる。候補再構成中の一時的な未選択で有効クラスを消さず、上位条件と合わない場合だけ解除する。初期値はownspec SRC-004/005/006/009どおりで、SQL検索契約は変更していない。修正後はselftest15・Smoke7・実起動３モードと検索５状態を新規実行した。

今回の新規実行証拠は `test-project1/test-report/20261012-evidence-01/CSharp_WPF/`。GUI操作とスクリーンショットはrootの実施記録を別に参照する。
