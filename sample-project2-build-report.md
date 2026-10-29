<!-- spec-meta: {"schema":"spec-md/1.0","documentId":"SP2-BUILD-REPORT","version":"1.1","path":"sample-project2-build-report.md","sheets":[{"heading":"実行条件","kind":"GRID","sheet":"01_実行条件"},{"heading":"Agentの問題","kind":"GRID","sheet":"02_Agentの問題"},{"heading":"別工程の問題","kind":"GRID","sheet":"03_別工程の問題"},{"heading":"検証結果","kind":"GRID","sheet":"04_検証結果"}]} -->
# sample-project2 ビルド報告

2026-10-29。実行ID `20261029-sp2-ui-conformance`。コード修正・両方式の再生成と自動回帰は完了。実画面操作は利用者の物理Escで停止したため、Accessの最終UI適合・集約manifest確定は未完了。本書と方式別固定記録は今回の状態へ更新し、過去候補のPASSを新候補へ転用しない。

## 実行条件

|項目|内容|
|---|---|
|対象|build-agent / sample-project2 / Access・CSharp_ASPNET。共通適合検査は全登録方式に適用する|
|確定条件|Accessのクラシック風・適切な字体を明示し、各方式の標準機能に合う実現方法で再生成する|
|入力|方式別specRootと採用規約・QA。各build/generation/inputs.jsonへ文書版・SHAを固定。UI条件の更新はexact-fileのspec-update.jsonへ記録する|
|出力|方式別ソース正本とbuild/固定パス。中間生成・隔離試験は.tmp/、履歴はGit|
|検査資源|所有するACCDBコピー・新規SQL fixture・専用Office instance。既存データや利用者Officeは使用しない|
|評価境界|構造・属性・描画・実操作・業務実行・ソース再構築を分ける。正式受入・採点は未実施、formalScore=null|

## Agentの問題

|ID|原因|修正と予防|
|---|---|---|
|UI-01|クラシック風の具体値が入力条件と生成設定へ十分に展開されていなかった|Access生成チェックと方式別UI条件へ灰色/白入力/黒文字、標準四角ボタン、テーマ・グラデーション非依存、全テキスト部品Yu Gothic UI11ptを明示。業務エラー色とOS管理外枠は区別する|
|UI-02|Tab見出し等がフォント設定対象から漏れ、Office既定値が残った|Tab・付随ラベル・一覧見出しまで実Controlsを列挙して独立部品表と照合。未知部品・字体設定漏れを失敗にする|
|UI-03|位置/寸法の検査と構造PASSだけでは最終画面の不適合を拒否できなかった|共通UI適合検査を全方式へ適用。font/dimensions/appearance/render/interactionの5種を必須にし、独立期待値と実測を比較。入力・製品・期待値・収集器・判定器SHAの不一致、旧結果・未観測を拒否し、manifest確定を止める|
|UI-04|Webの項目別CSSに対応するRazor classが不足した|HTMLへ項目classを適用。氏名260px/カナ330px/日付150px等の基準幅、14px以上の本文、狭幅では字体を縮小せず配置とスクロールで対応。Login460pxは維持する|
|UI-05|AccessのLoad中busy保護がfooterへfocusを移し、初期focusだけ戻しても縦scrollが残った|通常のメニュー→検索→新規/既存遷移で再現。初期focus・activeTab・viewportを一組で確認し、Tab見出しを含む初期表示と再遷移を検査する。測定前の強制scroll補正だけで通常遷移を合格にしない|
|UI-06|再試験失敗や収集器変更後も以前のPASSが残る可能性があった|実測開始時RUNNING・失敗時FAILへ失効。measurementSourcesの現SHAを共通gateで再検証。部品追加やTab到達不能の負例も確認する|
|UI-07|Access試験journalのPython PID再利用で記録が上書きされる穴があった|PIDだけで識別せず、実行ごとの一意なjournalへ記録し、所有Officeの終了を直接確認する。記録がない旧終了結果を推定しない|

## 別工程の問題

|ID|問題|現在の扱い|
|---|---|---|
|PH-01|採用SQL Server2022 Expressに対し、実機は2025 Express17.0|専用fixture・互換160で検査。2022物理ホストの合格は主張しない|
|PH-05|Webの未検索raw条件→新規→無編集取消で条件が失われる。現在DTOはrawを運ばない|OPEN / 詳細設計補完待ち。777777が空へ戻りDB書込0を今回再現。保存後AppliedCriteriaによる再検索と区別し、独断でAPIや業務契約を拡張しない|
|PH-07|Access ExcelのFit Toと手動改ページ制御が衝突する|実装の数値Zoom/実印刷幅・境界検査による回避を維持。詳細工程への修正依頼は継続。低水準API指定の完全一致PASSにはしない|

## 検証結果

|対象|今回の実施範囲|記録|
|---|---|---|
|Access|最終00904338候補で全9工程PASS、状態85/入力保護19/業務境界65/障害3/初期化4/競合4/独立18/認証race3、37個の所有Access全Exit0。298規則中1,116 native属性一致。最終版の実キー・清浄な目視は利用者Esc停止で未完了|[最終業務検査](sample-project2/srcs/Access/build/test-results/current-runtime.json)、[UI判定](sample-project2/srcs/Access/build/test-results/ui-conformance.json)|
|CSharp_ASPNET|最終publishの18状態・527規則/2096属性、1366/1024/390pxでPASS。SQL23/40/40、HTTP12、独立35+35、ブラウザー24、DL2冊の再読取がPASS。実Excel3冊73頁をPDF化し本文全頁を再読取、通常4頁・最大69頁contactと1/35/69頁拡大を目視。PH05はOPEN|[最終検査](sample-project2/srcs/CSharp_ASPNET/build/test-results/final-verification.json)、[独立目視](sample-project2/srcs/CSharp_ASPNET/build/test-results/ui-independent-visual-review.json)|
|共通ツール|UI111、preflight87、梱包14、独立配置8、最終整合回帰14を実行。製品受入とは別範囲|[ツール回帰](agents/builds/build-agent/build/tool-tests/)|
|配布ソース|Web84ファイルを原仕様・試験期待値なしで別展開しRelease build PASS。37license/NOTICEはsource・ZIP・publishの全SHA一致。Access35ファイルも最新ZIPから原仕様なしで再構築し、全class/IsCompiled/一時probe除去/5form/48列/初期データ/所有Office正常終了を確認済み|[Web ZIP](sample-project2/srcs/CSharp_ASPNET/build/source.zip)、[ライセンス照合](sample-project2/srcs/CSharp_ASPNET/build/test-results/license-package-verification.json)|

実入力は実施項目だけをnative-ui.jsonへ記録する。値代入/API検査を実キーボード・Clipboard・IME変換の合格へ置換しない。Accessのログイン画面の実キーは手操作確認待ち。利用者は手操作可能と回答したが、結果はまだ確認していない。最終候補の画面操作はphysical Escで中止し、所有UIコピー23728を正常終了、元候補不変を確認した。desktop矩形画像は別アプリの遮蔽があり全10枚を証拠から撤回・削除し、WGC対象window画像の再採取待ちとした。別DPI/別Office・プリンタ、紙への印刷、利用者秘密による初期設定、全障害条件、原41Pilot全条件・正式受入・正式採点は未実施。

Webの方式別manifestは全373entryのSHAを再照合済み。Accessの最終UI gateと入出力manifest、集約manifest・最終整合検査は未完了で、再開後の実画面確認に続いて確定する。sample-project1の既存変更ACCDBは開始前SHAと一致し、今回の再生成対象にしていない。
