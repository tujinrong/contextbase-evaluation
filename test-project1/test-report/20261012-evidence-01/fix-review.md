# 現行UI修正の独立ソースレビュー

2026-10-12。read-onlyレビュー。Accessは別担当のR5作業中のため除外。spec-evalは読まない。本記録以外の変更・試験実行はこのレビューでは行っていない。

対象はWPF `Services/NativeModels.cs`、`ViewModels/StudentSearchViewModel.cs`、`Views/StudentSearchView.xaml`、`Views/StudentEditView.xaml`、VB `Forms/FrmStudentEdit.Designer.vb`、`Forms/FrmStudentEdit.vb`、MVC `Views/Shared/_MessagePanel.cshtml`。補助の方式内View/Presenter/Gateway・新回帰のソース・同方式specを読んだ。WPFはSHAを確認した凍結build10 ZIP内の同方式ソースと実差分を照合し、R3の3対象ソースSHAも現在と一致した。方式間の共用や相互参照を追加していない。

今回の修正差分による新たな確定副作用は0件。以下の従来からの局所UI不具合2件を発見し、親へ報告した。親はui-fix-r4として修正・新回帰の追加を指示したため、以下は修正前レビューの記録であり、修正後判定はR4の別記録を参照する。

|問題ID|箇所・トリガ|影響・根拠|局所修正案|
|---|---|---|---|
|WPF-REVIEW-001|`StudentSearchViewModel.cs:122,125`。検索済み（appliedあり）の状態で年度/学年変更により選択クラスが候補から消える。|122行でClassIdをnullにしてW-STU-107を設定した後、125行が一般の未反映通知へ必ず上書きする。クラス値の解除は正しいが解除警告が見えない。検索詳細spec `01_学生検索画面.md:256` は不適合クラス解除＋W-STU-107要求。凍結build10にも同処理が存在する。|解除した状態を保持し、一般変更通知は解除しなかった場合だけ設定。実検索済みWindowで警告保持と通常通知を両方検査。|
|WPF-REVIEW-002|`StudentSearchView.xaml:10-12`。未所属ON時の年度/学年/クラスComboBox。|3選択部品のIsEnabledは未所属と連動せず、Viewコード裏にも制御がない。`StudentSearchViewModel.cs:115` は値を解除するが、操作可能な外観のまま選択が取り消される。検索詳細spec `01_学生検索画面.md:255` は解除して非活性と要求。これも従来からの差。|3部品をIsIdleかつ未所属OFFの方式内派生状態へbind。ONでnull＋非活性、OFFで活性＋null保持、busyでは非活性を実Windowで検査。|

WPFのNULL検索意味は維持されている。`NativeModels.cs:6` は空コードだけnull、学年なし00は実コードのまま。11行は未指定のsentinel ID0だけnull、13行は登録用raw文字列を空/InvariantCultureの十進IDへ合わせる。`StudentSearchView.xaml:11,12,15` は検索用nullableキー、登録側は `StudentEditView.xaml:32` の文字列Valueで、空文字をlongへ無理に変換しない。Gatewayはnullable年度/学年/クラス/都道府県をそのまま方式内Coreへ渡す。

`StudentSearchViewModel.cs:32-35,109-124` のSelectedClassと候補再生成ガードは、一時的なSelectionChangedによる適合ClassId消失を防ぎ、不適合だけnullにする。Clear後も新しいDraftをObserveDraftへ接続する。R3の既存実Window試験は初期・適合クラス選択/保持・Clear・未所属・不適合解除を含む。ただし上記警告保持/非活性までは確認していなかったため今回指摘した。

VB/MVCは別Agent audit_legacyにも短いread-only確認を依頼し、独立の確定指摘0件だった。VBはメッセージのreadonly/multiline/縦スクロール/高さ70を維持してTabStopだけ除外し、入力と操作のTabIndexを指定する。Shown後の初期化完了を待ってFocusしscroll0へ戻す。新規/編集/参照と次Tabは現行18項目の実Form検査で覆う。MVCはErrorCount>0の場合に既存All summaryを描画し、情報表示は独立したまま。実binding/全体/サービス入力エラーが可視で、エラー0件だけ空枠を出さない契約を現行42項目が覆う。

この記録はソースレビューであり、新しい処理系実行合格ではない。引用したR3・MVC/VB after-fixの試験結果はそれぞれの実行IDの証跡であり、本レビューの新実行結果へ流用しない。SQL/DB認可/SQLCLR hosting、DPI150/200%は未検証。旧build10 ZIPは凍結成果で、現行UI修正を含む更新ZIPではない。
