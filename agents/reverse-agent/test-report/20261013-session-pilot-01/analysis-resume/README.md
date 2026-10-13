# 完了解析の安全な再利用

2026-10-13。実装と来歴検査を実施。新しいAI原稿、業務意味の採点、モデル重みの訓練はこの作業では未実施。

## 入力と変更

入力は封印済みsource capsule、snapshotにbindされた文書計画、既存AI解析応答とprovider証跡。新形式は `reverse-ai-analysis-handoff/1` と `reverse-ai-analysis-resume/1`。実装は `src/contextbase/ai/workflow.py`、CLIは `src/contextbase/ai/__main__.py`、追加検査は `src/contextbase/tests/test_ai_resume.py`。

新規解析はdraft開始前に `analysis-handoff.json` を保存する。解析原稿のSHA、providerの原応答/result/schema/prompt、解析前後のsnapshot、現在のplanとhandoff、文書定義のID/path/kind、referenceModeを対応付ける。provider原証跡を残さないcustom/test実装は通常のdraftを生成できるが、NOT_RESUMABLEを記録し、解析再利用を受理しない。

`document --analysis-job <旧document job root>` はこのcheckpointを検査し、新しいjob rootでAI執筆だけを行う。以前の原応答は編集しない。批評を渡せるほか、writerは封印snapshotを再読して訂正できる。返された `factCorrections` をdraft-resultへ保持する。原稿生成後にもcheckpointと原証跡を再検査し、途中改変なら公開しない。文書種別と出力pathを含む同じbound planだけを許可し、analysis-reportを別種別へ転用しない。

旧完了ジョブは `--analysis-job <root> --recover-analysis-job` または `recover_analysis_checkpoint(...)` で明示的に回復する。successful provider result、原応答/schemaの一致、有効な根拠、解析前後snapshot、原解析prompt中の文書定義を検査する。originは `deferred-bind:legacy-provider-and-before-after-evidence-verified`。planBindingScopeは現在のbound planと原promptの文書対応であり、過去の解析開始時にplan全体のSHAを別に記録したと偽装しない。

## 今回の検査

最終回帰は79件、25.040秒、exit 0。追加resume検査24件、既存provenance 27件、CLI 11件、改訂iteration 10件、改訂batch 7件。原応答・verified facts・provider result/schema・checkpoint・source・plan・文書種別・原prompt・snapshot前後の改変、不一致の旧解析、途中checkpoint改変、既存出力の上書き防止、AI解析を再起動しない再利用を含む。合格は来歴と工程の検査であり、文書の業務意味が完全だという採点ではない。

`final-tests-before.json` と `final-tests-after.json` は検査対象の正確なSHAを記録し、検査前後の対象ファイル不変を確認した。最終終了時刻は2026-10-13 06:21:14 JST。raw logは `final-tests.raw.log`。前段の75件/78件の合格は新しいiteration改訂の合格に流用せず、`test-manifest.json` は後から観測したhashと明記した。

実資料の回復検査は `.tmp/20261013-tuning-01/pilot-v3/physical-tables/` の7件で全件成功。計画は同pilotの `plan/plan-verified.json`、capsuleは `.tmp/20261013-tuning-01/capsules/CSharp_ASPNET-assisted`。training-assistedを維持し、原provider/解析/snapshot証跡のhash不変を確認した。新しいAIジョブ開始は0件。文書ID・mode・hash・回復状態のみを結果へ記録し、業務fact本文を表示・転記していない。詳細は `legacy-recovery-results.json`、再現helperは `legacy-recovery.py`、raw logは `legacy-recovery.raw.log`。

## 観測した継続の障害と限界

2026-10-13 06:09頃のsession plan-r2は実行中。初期のGet-Content相対パス読取りが失敗し、POSIXパスによるrg/NoProfile読取りへ切り替えると成功した。06:08:05のstderrにwebsocket切断のretry 1/5があった。これは当時の観測であり、現在も同じprocessが動いていることを意味しない。

従来はprovider resultが終了時にのみ保存され、batch終了前の完了文書記録も不足した。既存job rootへ上書きする経路は設けず、完了解析だけをcheckpointとして再利用することで再解析の重複を減らす。生きたjobは重複起動せず、完了または明示的失敗を確認したうえで、新しいjob/outputへ進む。

read-only sandboxは書込み制限であり、任意host読取りの完全な隔離証明ではない。model tool actionの自動監査をこの変更の成果とは報告しない。原文と参照設計の区別、期待値の隔離、同じ封印材料内のAI判断という既存境界を保持する。
