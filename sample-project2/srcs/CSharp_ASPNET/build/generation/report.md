# CSharp_ASPNET 再生成結果

実行 sp2-ui-regenerate-20261029、品質high、改善3回。状態は **候補作成完了・正式UI検査未完**。最終publishは `aad4998ca745296c2b670bc2a1f2fdc3159ec5e4112c4f9123088521f24deca4`（101資源）、source ZIPは `ca522790240bf1cec9f5f7828ff5af25323211131220f82fd9360e712b4eb17d`（92member）です。正式UI gateは実値不一致0、必須操作3ruleの未観測によりFAILです。outputs.jsonは発行していません。formalScore=nullです。

共通ヘッダー・左メニュー・現在位置、独立見出し、14px以上の役割別文字、個別欄幅、対象社員の両タブ表示、行からの直接編集を実装しました。5画面6機能、最大200件・ページングなしの採用例外を維持します。検索raw4/適用条件/未検索・未適用・成功・失敗・上限、PH05の新規→無編集取消・保存復帰を分離しました。現在明細を含む親子原子保存、失敗保持、離脱確認、履歴の独立copy、UI失効/Unknownの再送禁止、JSON POST→一回GETを実装しています。

追加実測で、出力取消後にUIの更新番号が古く残り、再出力が409になる不具合を確認して修正しました。所有workerの終了を要求の取消期限内・最大30秒で待ち、取消・通常失敗の現UI状態を同期してから待機を解除します。重複拒否後の元出力完了/取消、即時の手動再出力、実読取失敗と復旧を専用DBで検査しました。旧4aの合格を新版へ付け替えていません。

| 検査 | 現対象の範囲と結果 |
|---|---|
| 入力/構造 | 66凍結入力を維持、隔離217ファイル・517参照、指摘0 |
| build/業務 | SDK10.0.401、Release警告0/エラー0。3回30/47/47件、最終47件は修正後DLLで再実行 |
| 状態/独立単体 | 状態12件、Application35件、Infrastructure28件PASS。後者のSQL試験は未実行 |
| 作者ブラウザー | 既存28件を新版で再実行、追加20件、pageerror0。別途CSRF/技術HTTP拒否3件 |
| 独立非操作UI | font202/dimensions86/render46/appearance3、計337rule。5画面×6環境を新版で再計測し比較差異0 |
| 実部品在庫 | native/role/属性/実子から204部品、kind/textCapable408比較差異0、子owner169/direct929、未決0 |
| 操作適合 | 29rule中26ruleで全propertyの実値が揃い、SQL0/1・旧live全公開項目・別TabDraft・実確認数/POST数を採用 |
| 正式UI gate | 363観測rule・1017property比較、実値不一致0。未観測3ruleによりFAIL |
| 配布 | 原仕様/期待値/試験/私有設定なしのZIPを隔離展開、通常Build.ps1で再構築、新所有DB5表48列→seed20→SKIP。全行/schema/manifest不変 |
| 保全 | 初回ZIPと補足build/SKIPをそれぞれNative親で観測し、user-secrets/profile/launchSettings前後SHA一致。既存DEMO5表全行/列schemaも再起動前後一致 |

残る未観測ruleは `DUI08.code-scope`、`DUI09.keyboard`、`DUI11.bfcache` です。具体的には読取専用コードの物理クリップボード、Windows IME変換中Enter、実BFCache persisted経路です。実BFCacheはキャッシュ可能な陽性対照でtrusted persisted=trueを確認しましたが、製品ではno-store理由によりfalseで、合成イベントを合格にしていません。その他の実測済みpropertyは部分記録に保持し、期待値を変更して合格へ合わせません。

Rootの4観点目視は現製品のPC検索/社員基本/経歴/コード、390pxコードの5画像に限定します。合理性は対象/保存単位、統一性はShell/見出し/操作、見やすさは幅/文字/整列、操作性は縦配置/表内スクロールと到達を確認しました。全状態の利用者受入ではありません。

実SQLは17.0.5005.3 Express/互換160です。SQLServer2022実機、今回のNativeExcel/PDF/物理印刷、正式Pilot/利用者受入/採点は未実施です。既存DEMO7443は同じDB/profileで現publishを稼働し、ログイン画面GETのみで確認しました。DDL/seed/認証試行/業務書込を行っていません。作者5182/5184・監査5183/5185は正式停止済みです。過去4a/28abdの初回Store-Python nativeファイル未観測は履歴として残し、今回のNative初回測定と区別しています。

詳細は final-verification.json、quality-cycles.json、ui-observations.json、ui-conformance.json、source-package-validation.json、source-package-initial-native.json、source-package-preservation.json、demo-restart-preservation.json、generation/regeneration.json を参照してください。
