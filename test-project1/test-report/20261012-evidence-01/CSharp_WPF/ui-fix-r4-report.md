# WPF 検索UI修正・再検査 R4

検索済みの状態で上位条件に合わないクラスを解除するとW-STU-107が一般通知で上書きされる不具合と、未所属ONでも年度/学年/クラスが有効な不具合を修正した。既存検索詳細255-256行に従う局所実装修正であり、仕様・DB・Gateway契約は変更していない。

SearchVMはクラス解除フラグを持ち、解除した場合のW-STU-107を一般変更通知より優先する。その他の条件変更通知は維持する。CanSelectClassCriteriaはIsIdleかつ未所属OFFで、busy/未所属/候補再生成/Clear時に通知する。検索XAMLの3ComboBoxだけにbindした。未所属OFFでも以前の条件は復元しない。

同じ実Window回帰を修正前に実行し、検索済み状態のクラス解除警告が失われて期待失敗exit1になった。初回はここで停止したため、未所属非活性の修正前実行失敗まで確認したと主張しない。その欠陥はソース/仕様で確認し、修正後の実Windowで検証した。

修正後の **実検索Window11状態PASS**：初期NULL、適合クラス選択/保持、検索済み不適合ClassId=null＋W-STU-107保持、通常未反映通知、Clear、未所属ONの解除＋3非活性、OFFの3活性＋null保持、非同期busyの3非活性、完了後の活性復帰、不適合解除。busyはテスト専用fixture検索をTaskで実際に保留してから解放し、実WPF IsEnabledを確認した。

今回の同じ現行入力で **fixture自己試験15/15、Smoke7/7** を新規再実行した。撮影exeを含む本体/fixtureとSmokeビルドは警告0・エラー0。検査Windowは実Show/ContentRenderedを通過し、自動Closeした。画像撮影は親Agentが担当する。

R4本体変更はSearchVMとSearchView.xamlの2ファイルだけ。テスト側はGuiEvidence Program.csへ意味のあるWindow回帰とfixture一時停止委譲を追加。方式内spec46入力（Markdown42文書、8.0/8.1）はSHA不変。初期evidenceからの本体累積差分はR2/R3を含む4ファイルで、それ以外の基準35本体入力は不変。

|R4本体|修正前SHA256|修正後SHA256|
|---|---|---|
|test-project1/srcs/CSharp_WPF/ViewModels/StudentSearchViewModel.cs|4eecea7b557cab5e1dbfc729060197bd3ba7e30f440f1a1bd0eac90cbb9f507c|7059717a44d6e5a9d7978e3bec075a9a1028a015834bd6ca7604a6aa27ce8b8e|
|test-project1/srcs/CSharp_WPF/Views/StudentSearchView.xaml|256263c89edb5e14859f4f59ccd5fba1b8d4a383abcbec6673cdeb9ab4c1ad02|37c37f99ddf3304d3171fd1abedfb16f92d50a1e94ec06c3adad61d95acbaf43|

生ログはui-fix-r4.before/after-search.log、fixture-selftest.log、smoke.logと各build.log。実差分production.diff、修正前スナップショット、入力lock ui-fix-r4-inputs.json、出力DLL/exe・ログSHAをui-fix-r4-results.jsonへ保存した。過去R1-R3は上書きしない。

撮影入口は方式内 `tests/GuiEvidence/bin/Debug/net10.0-windows/Wpf.GuiEvidence.exe --screen search`。現行DLL/exeを再ビルド済み、通常の閉じる操作で停止する。fixtureには保存拒否/SQL未接続の制約がある。SQL接続/実行は0、DB認可/CRUD/SQLCLR hosting、DPI150/200%、Core/native再実行、新規/編集実起動のR4再実行は未実施。これらの旧合格は今回の新実行結果として流用しない。

build10 source ZIPは旧改訂の凍結成果としてSHAを確認し保持、今回更新していない。今回修正を含むのは現行srcsとR4入力manifestであり、旧ZIPを現行修正版として使わない。
