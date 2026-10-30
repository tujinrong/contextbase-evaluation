# CSharp_ASPNET 再生成結果

実行 sp2-ui-regenerate-20261029、品質 high、改善3回。状態は **候補作成完了・正式UI検査未完**。最終publishは `4a60763579584af38749462f9792b51179249447080d610d2d9049a9bd3af651`（101資源）です。UI gateは必須操作23項目未観測のためFAILで、正式outputs.jsonは確定していません。formalScore=nullです。

共通ヘッダー・左メニュー・現在位置、独立見出し、14px以上の役割別文字、個別欄幅、対象社員の両タブ表示、行からの直接編集を実装しました。最大200件・ページングなしの理由付き採用例外と5画面6機能を維持します。検索raw4/適用条件/未検索・未適用・成功・失敗・上限を分離し、PH05の新規→無編集取消・保存復帰を具体化しました。現在明細を含む親子原子保存、失敗保持、離脱確認、履歴独立copy、UI失効/Unknownの再送禁止、JSON POST→一回GETを実装しています。

| 検査 | 今回の範囲と結果 |
|---|---|
| 構造/入力 | 66凍結入力、隔離200ファイル517参照・指摘0 |
| build | SDK10.0.401、locked restore/Release build、警告0/エラー0 |
| DB/業務 | 3回30/47/47件PASS。各新所有DBだけを作成・検査・終了 |
| 状態/追加単体 | 10件PASS。元独立設計テストの再実行はApplication35/Infrastructure28件PASS（後者SQLなしの範囲） |
| 作者ブラウザー | 最終製品28ケースPASS、pageerror0。0/200/201、raw/履歴/別Tab/失効、未反映明細保存、SQL子書込rollback、Unknown通信断、待機入力、キー、2シートXLSX読戻し |
| HTTP追加 | CSRF欠落/不正と指数入力を400拒否、社員/経歴不変。技術エラー全メッセージ分岐の合格ではない |
| 独立非操作UI | font202/dimensions86/render46/appearance3、計337rule実測・比較差異0。5画面×1366/1280/768/390/320/文字200%を別証拠化 |
| 実部品在庫 | native/role/属性/実子から204部品を独立分類、kind/textCapable408比較差異0。子owner169/direct929、未決0 |
| 正式UI gate | 343観測rule、896 property比較・実値不一致0。必須操作23ruleが未観測のためFAIL |
| 配布 | 原仕様・UI期待値/試験・私有設定を含まないZIP92member、別展開の通常Build.ps1から再build/publish、通常Setupで新DB5表48列→seed20行→SKIP。全行/schema/manifest不変 |

4観点の作者目視は最終製品のPC検索/社員基本/経歴/コードと390pxコードの5画像に限定しました。合理性は操作対象と保存単位、統一性はShell/見出し/主副操作、見やすさは幅・文字・整列、操作性は縦配置/表内スクロールと操作到達を確認しました。独立した全状態の目視受入ではありません。

未観測の必須操作は `DUI01.navigation`、`DUI04.row-edit`、`DUI05.ph05-untouched`、`DUI05.invalid-raw`、`DUI05.new-save-return`、`DUI06.searched-return`、`DUI08.cancel`、`DUI08.code-scope`、`DUI09.keyboard`、`DUI09.search-order`、`DUI09.busy-input`、`DUI11.history.Success`、`DUI11.history.Unsearched`、`DUI11.history.Unapplied`、`DUI11.history.Failed`、`DUI11.history.LimitExceeded`、`DUI11.bfcache`、`DUI11.tabs`、`DUI11.state-expiry`、`DUI11.commit-navigation`、`DUI11.transport`、`DUI11.get-errors`、`DUI12.export` です。一部の経路は実行済みでも、各ruleの全分岐/全propertyを実測していないためPASSへ補完しません。実pageshow.persistedはfalseで、合成イベントをBFCache証明にしていません。物理IME/clipboard、SQL Server2022実機、今回のNativeExcel/PDF/物理印刷、正式Pilot/利用者受入/採点も未実施です。

実DBは17.0.5005.3 Express/互換160です。既存DEMO7443は新publishで再起動し、DB再投入/DDL/業務書込を行わず既存profile/launchSettingsを保持しました。作者5182・監査5183は正式停止、利用者DEMOは稼働しています。Store Python初回のnative user-secrets前後SHAは未観測でした。別のNative PowerShell補足で同ZIP build/同DB SKIP中の実ファイル前後SHA一致を確認し、この区別を配布記録に残しました。

詳細は `final-verification.json`、`quality-cycles.json`、`ui-observations.json`、`ui-conformance.json`、`source-package-validation.json`、`source-package-preservation.json` と `generation/regeneration.json` を参照してください。過去候補のPASS/旧VS・認証・印刷結果を今回へ流用していません。

独立意味監査で、未計測の0回・HTTP回数だけによる内部SQL0の推定・lease有効だけによる旧状態全項目不変の推定・未準備のEditDraft/New条件を正式観測から除外しました。28実行ケースのassert済み部分は保持しますが、完全操作ruleは6/29だけです。元の部分記録を残し、期待値や製品を変更して合格へ合わせていません。
