# WPF 実起動不具合の修正・再検査 R2

実行ID `20261012-evidence-01-wpf-ui-fix-r2`。初回の自己試験では未通過だった実Application.Runで、testハーネスのresource初期化不良と登録画面本体の空ID変換不良を検出した。利用者の不具合修正指示の下で修正した。**最終ビルド0警告0エラー、自己試験14件、影響範囲Smoke7件、実検索/新規/編集Windowの起動3モードが通過した。** 画面操作・撮影はrootへ引継いだまま。

## 修正

test-only EvidenceAppはproduction Appからの継承をやめ、通常のApplicationへ原本App.xamlのApplication.Resourcesをロードする。App.xamlをProduction.App.xmlというデータファイル名で無変更コピーし、resource dictionaryを構成する。同じloaderを自己試験でも実行する。原本AppのSQL起動は呼ばない。

本体の登録画面ではModel.ClassIdがraw文字列、候補のSelectedValuePathがlongのIdだった。新規の空文字をInt64へ変換しようとしてFormatExceptionとなった。ClassOptionに文字列Valueを追加し、登録XAMLだけSelectedValuePath=Valueへ変更した。未選択は空文字、実IDはInvariantCulture十進文字列として一致させる。StudentDraft.ClassId long?、検索画面のnullable longキー、DB契約は変更しない。これは実装不良で、仕様のaccdb/共有DB契約変更を必要としない。

## 新規検査と証拠

実起動検査はApplication.Run→Window.Show→ContentRenderedで、Visible=true、Loaded=true、非0 HWND、原本resources4件、検索2行/新規初期値/編集TEST-WPF-001を確認した。各ウィンドウは検査後自動Closeし、終了0。静的画像の描画や仕様モックによる代替ではない。

- 最終build: `fixture-build-r6-class-key-fix.log`
- 自己試験14件: `fixture-selftest-r2-class-key.log`
- 影響Smoke7件: `smoke-build-r2-class-key.log`, `smoke-run-r2-class-key.log`
- 実起動: `fixture-real-startup-r3-search.log`, `fixture-real-startup-r3-new.log`, `fixture-real-startup-r3-edit.log`, `fixture-real-startup-r3-commands.json`
- 変更前後hash/現在source/binary hash/機械結果: `ui-fix-r2-results.json`

初回rootのWindows Application Event1026は `ui-initial-launch-failure.json` に保存されたまま。修正中のresource loaderのnamespace不足と、データファイルを.xamlとしてコピーしたことによる重複generated Appビルド失敗も別ログで保持した。最初のnew起動のFormatExceptionは `fixture-real-startup-r2-new.log` に保持した。旧results.jsonや旧PASSは上書きしていない。

方式内spec46ファイルは変更なし。productionソースの変更は `Services/NativeModels.cs` と `Views/StudentEditView.xaml` の2ファイルだけで、残りの原本hashは一致する。fixture JSONも変更なし。今回の検査前に実行したCore96/native102/Framework27は同じevidence-01内の別記録で、それらのsourceは変更されていない。UI修正後に再実行した合格と区別する。

rootの撮影入口は従来と同じ `tests/GuiEvidence/bin/Debug/net10.0-windows/Wpf.GuiEvidence.exe --screen search|new|edit`。本体2ファイルのsourceが変わったため、ソース配布ZIPを更新する場合は新しいhashで作成する。共有SQL接続/DDL/認可/CRUD/SQLCLR hostingは未実施のまま。本文R1のGUI_READYは初回実起動失敗で保留となり、本R2の実起動合格で更新される。
