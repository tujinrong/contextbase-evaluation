# 期限 capture wrapper の実装・人工条件検査

2026-10-13 01:51 UTC。新規 `.tmp/20261013-session-pilot-01/deadline_capture_cycle.py` を作成しました。本番 wrapper は起動していません。現在の生成・描画・原稿・評価・原本には触れていません。既存 capture_owned_cycle.py は変更しておらず、SHA-256 は `f870d7917e3cb1590a67075ffa7c70b09161c50a74cb4291f0dcae873896e6bf` です。現行の production AI module と production test はこの作業で修正していません。

wrapper は起動時に最新継続ファイルと絶対 deadline を保存し、最大15秒以下（既定1秒）の待機単位で期限を待ちます。latest は capture helper と同じ数値 suffix の最大値です。owner の os PID/argv/cwd/UTC/runner SHA と read-only CIM の実 identity を別々に記録します。owner identity が得られない場合は helper を呼ばず UNKNOWN で終了します。

capture helper は起動時 bytes を同じ `.tmp/session` ディレクトリの固有名へ排他的に凍結します。これにより既存 helper の `__file__.parents[4]` 契約を維持します。runner/helper source のコピーと SHA も保存します。期限 callback で最新 handoff を再取得し、deadline が起動時と違えば fail closed。callback 中の byte/選択 handoff 変更、wrapper/frozen helper 改変も実行前に拒否します。

期限 callback は凍結 helper を `--stop-at-deadline` 付きで1回呼びます。helper stdout/stderr/transport、helper 自身が保存する scope・raw before/after・process request/actions/result は独立した証跡です。helper は既存の config/root/PID/creationDate/commandLine 検査を担当します。wrapper は別の read-only CIM で captureされた roots と descendants の exact identity を照合します。`STOP_REQUESTED` 自体は停止成功になりません。確認できた対象が残れば `EXACT_OWNED_IDENTITIES_REMAIN`、未知・不完全・helper error は UNKNOWN。absence の独立確認でも `processStopSucceeded` は null のままです。原因を推定して「停止成功」へ読み替えません。

初期・callback・終了観測 handoff、開始・cancel・fail・終了を別ファイルへ排他的に保存します。既定の cancel-request.json または指定 cancel ファイルは待機を取り消し、helper を起動しません。KeyboardInterrupt は partial を残して cancellation を記録します。OS の強制終了は Python finalizer を実行しないため、終了記録は保証せず開始/raw 証跡が残ります。wrapper 自身や共有 app を停止するコードはありません。

人工13条件PASS、失敗0、error0、skip0、3件の source pins 不変。人工 clock・transport・CIM response を使用し、実プロセス停止と実 CIM は未試験です。対象条件は deadline 到達、期限時の最新継続採用、deadline 変更、同一 handoff の callback 変更、helper failure/raw保持、STOP_REQUESTED後の残存、未知の照合、欠けた action、cancel signal、KeyboardInterrupt、凍結helper改変、owner不明、capture中のhandoff変更、read-only CIM scriptの無停止命令です（read-only命令検査を含め13 test methods）。

初回の13 error は人工 fixture の Windows パス長制限でした。短い `.tmp/dwtest-*` と短い人工 case ID にして修正し、旧 `synthetic-tests-01.log/json` は保持しました。最終は `synthetic-tests-02.log/json`。実運用 report も短い `focus-deadline-01/capture` 等を選び、raw nested path の上限に注意します。helper/report のコピー対象に長いパスがあれば captureError が残ります。

制限: 既存 capture helper は期限 callback 後に before をコピーしてから停止を要求するため、deadline ぴったりの停止時刻は保証しません。CIM の問い合わせ時点間の自然終了・PID再利用もあり、照合は各観測時刻の状態です。handoff が実行後に変われば全体を UNKNOWN へ戻します。helper transport が不完全で captured identities の完全な記録が得られない場合、独立 absence 承認は行いません。review/grading agent の停止は root が別に担当します。本文、採点期待値、原本には読み書きしていません。

監査用 source snapshot と pins は `source/` と `source-pins-01.json` に保存済みです。root が独立監査した後に本番を起動する想定で、この担当から本番を起動しません。
