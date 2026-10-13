# Provider の途中証跡と期限停止の読取り監査

監査時刻: 2026-10-13 01:26 UTC。対象は現行 AI Provider、第5稿の凍結 Provider・Workflow、凍結した試行 runner、描画 runner、実際に使用する Python 3.12.14 の `subprocess` 実装です。実行中ジョブの唯一の状態根拠は `focus-continuation-handoff-05.json` としました。ジョブ・プロセス・原稿・原ソース・原仕様・採点資料は変更していません。原稿、解析回答、prompt、event、stderr の内容と評価期待値は読みません。保存ファイルの存在・サイズ・更新時刻だけを観測しました。

現行と凍結の Provider、Workflow、描画コードはそれぞれ同一 SHA-256、試行 runner と保存 runner-source も同一です。詳細は `audit.json` と `code-pins-validation.json` に記録します。

## 保存できている証跡と未保証の範囲

Provider は `events.jsonl` と `stderr.log` を排他的に作成し、CLI の stdout/stderr をそのファイルへ直接渡します（provider.py:227-230,292-297）。Python が CLI の stdout を完了後にまとめてファイルへコピーする経路ではありません。既に CLI が OS へ書いた bytes はファイルに残ります。ただし CLI 自身の出力頻度・内部 buffer の flush、強制停止時の未書込み bytes、電源断時の耐久性まではこの実装から保証できません。

01:25 UTC 頃の属性観測で、検索の analysis/events.jsonl は 477111 bytes、編集は 624349 bytes でした。編集の analysis/answer.txt は 119980 bytes、result.json は 147242 bytes あり、01:24:13 UTC に作成されていました。検索の answer/result はこの観測時点ではありません。**属性だけの観測であり、結果の status・成功・JSON 妥当性・内容の完成は判定していません。** 初期に events が空だった事実だけでは停止や保存不能を推定できません。

## 問題と原文根拠

| ID | 条件・問題 | 根拠 | 次の汎用改善 |
|---|---|---|---|
| PPA-01 | result.json の保存は finish に入った場合だけ。外部から Python を強制終了すると KeyboardInterrupt 分岐を通らず、終了理由・command/CLI hash・usage 集計を含む provider result を保証できない。 | provider.py:209-236,287-297,301-313。result を開始時には保存していない。 | 現在のジョブは変更せず、外部の停止前/後 inventory、所有証跡、未完了状態を別の report に保存する。将来は排他的な launch 記録に PID/creation time/command/input hash を保存し、final result と区別する。 |
| PPA-02 | Windows の同期 stdin 書込みは `subprocess.run(timeout=...)` の時間制限を完全には覆わない。CLI が入力を読まず pipe が詰まる条件では、入力を書き終わる前に timeout 待機へ進めない。 | provider.py:294-296。実 Python subprocess.py:506-545 は input から stdin=PIPE を設定し、1603-1634 の Windows `_communicate` は1621-1622で同期 `_stdin_write` を先に呼ぶ。1140-1143 は stdin.write(input)。 | 既に UTF-8 bytes で保存済みの prompt.txt を rb で開き、run の stdin=file stream、input 引数なしで渡す。bytes・CLI 引数・stdout/stderr 保存を保ち、親プロセスの pipe 書込み待ちを除く。現在の凍結ジョブには適用しない。 |
| PPA-03 | Python の timeout/KeyboardInterrupt 経路で kill されるのは直接の CLI プロセス。CLI が生成した子プロセスの停止はこの実装だけでは保証されない。 | provider.py:293-297 は CREATE_NO_WINDOW と run を使用。実 Python subprocess.py:548-568 は process.kill()、1667-1682 は Windows TerminateProcess(handle) と kill=terminate。process tree/job object を扱っていない。 | 外部期限処理は exact PID/creationDate/commandLine を照合し、確認できる所有 descendant だけを記録・停止する。将来の provider に子 PID と起動時刻を保存し、必要なら所有された Job Object 等の containment を追加する。 |
| PPA-04 | KeyboardInterrupt の保存テストは mocked run の例外を直接 provider へ渡す。現在の runner は ThreadPoolExecutor の worker 内で run_job を呼ぶため、親 main thread の Ctrl-C が worker の provider 保存分岐へ届くことをこのテストは証明しない。強制終了は Python 例外として届かない。 | test_ai_provider.py:1,34-59,222-285。runner-source.py:138-168 は worker task/except Exception/ThreadPoolExecutor。provider.py:301-313 は受信した KeyboardInterrupt の保存だけ。 | 将来、main/controller から明示する cancellation と所有子プロセスの停止・worker の回収を設計する。現ジョブの期限は外部停止記録で補い、interrupted result が必ずあるとは報告しない。 |
| PPA-05 | 描画 runner の deadline は外側 while の条件だけ。期限前に render_document が始まった後の描画全体には絶対期限を渡していないため、呼出中の終了を保証できない。 | render_cycle.py:25-28,42-44,56-59。凍結 rendering.py:325-327 の引数に deadline はない。 | 現 renderer は再起動せず、所有を確認して外部期限処理で止め、残った画像/HTML/manifest の完成・部分状態を別記録する。将来は renderer に絶対期限と cancellation を渡し、各描画の前後で検査する。 |

PPA-02 は条件付きの実装上の穴です。今回の両 analysis は実 bytes の events があり、編集では answer/result も保存されています。**Round5 で同期 stdin の停止が発生した証拠はありません。** prompt の観測サイズは検索208103 bytes、編集229850 bytesですが、サイズだけで障害発生を結論しません。

正常 timeout は provider の `status=timeout` と raw events/stderr を保存し、Workflow が exit_code=0 かつ status=passed を要求するため、途中回答は受理されません（provider.py:314-365、workflow.py:27-33）。KeyboardInterrupt 分岐も answer/exit_code を None のまま保存して再送出します。ただし `_bound_job` の snapshot-after 保存は run_job の正常復帰後で、強制停止や伝播した KeyboardInterrupt のときは欠けます（workflow.py:121-136）。その場合も外部の停止後 snapshot hash 検査が必要です。

## 期限処理の補完案

1. 最新 handoff と owned-processes を pin し、対象 PID の creationDate/commandLine を実際のプロセスと照合する。所有が確認できない PID は停止しない。
2. 停止前に prompt/schema/events/stderr/answer/result、checkpoint/handoff、progress、派生画像/HTML/manifest の存在・サイズ・時刻・SHA-256 を inventory に保存する。稼働中ファイルは観測 snapshot と明記する。
3. この依頼が所有する未完了処理だけを止め、終了確認後に別名の final partial inventory と stop 結果を保存する。残るファイルを削除・書換えしない。
4. provider result の欠落を捏造した result で埋めず、`not-completed`/`not-assessed`/formal score=null を外部 report に記録する。終了後の pin と元の snapshot を照合し、欠けた snapshot-after も未実施として明記する。

## 次の実装とテスト

最小の将来修正は PPA-02 の file stdin です。CLI が受け取る prompt の UTF-8 bytes を保存ファイルと同一にする検査、input 引数を渡さない検査、stdout/stderr/answer を書換えない検査を追加します。Windows の人工的な子プロセスが stdin を消費せず待機する例を使い、実 timeout により親が規定時間で復帰して raw artifacts を保持することを確認します。これを model/業務アプリの試験として扱いません。

PPA-01/PPA-03/PPA-04 は別途、起動記録・所有照合・子プロセス停止・main/worker cancellation の失敗例を検査します。既存の timeout/KeyboardInterrupt raw 保存の回帰は維持します。現在の test_ai_provider.py はすべて subprocess.run を fixture に差し替えるため、実 Windows stdin/強制停止/process tree の証明にはなりません。この監査ではテストを新規実行していません。

未実施: 実行中ジョブの中断、再起動、コード修正、実強制停止試験、raw 内容の審査、仕様本文の審査、採点、原ソース/原仕様/spec-eval の読取り。実際の残存内容と完全性は root の独立検査に引き継ぎます。
