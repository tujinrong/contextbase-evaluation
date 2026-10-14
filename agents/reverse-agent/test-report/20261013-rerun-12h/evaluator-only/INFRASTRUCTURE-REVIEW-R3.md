# 評価実行基盤の点検・修正記録

2026-10-13 10:10 UTC。対象は test-project1 / CSharp_ASPNET の evaluator-only。原仕様・原ソース・固定rubric・期待値は変更していない。生成Agentへ採点・期待内容を送っていない。

初回 `search-basic-r01-probe` は 09:25:23Z に開始し、09:47:16Z に自然終了した。初期観測では events/stderr が 0 B だったが、終端には thread/turn と23件のcommand実行が残ったため、0 B だけを停止判定に使えない。実時間約1,312.8秒。CLI exit 0 に対し、評価結果は `VALIDATION_OR_PROVIDER_FAILED`。回答・event・stderr・result は原bytesを保持している。相対 `manifest.json` / request 読取りの失敗があり、その後はcapsule絶対パスで読まれた。初回の引用全走査は `batches/search-basic-r01-probe/evidence-diagnostics-r3-complete.json` に保存した。73回答行・Safety6項目・254引用のうち17件（採点行16、Safety1）が空quoteで無効。正式得点はない。

許可された共通基盤修正は次の通り。旧graderは `code-history/grader-before-evidence-boundary-r3.py` へ保存した。

- 引用はgenerated/source各canonical root内、封印manifestの掲載pathと完全一致、canonical POSIX path表記一致を要求する。`generated/../reference/...` 等の越境・role交換・未掲載pathを拒否する。既存の行範囲・非空exact quote・全行一度だけの検査を維持する。
- jobが失敗なら `run` のprocess exitを非0にする。
- promptへcapsule root、manifest、requestの絶対パスとtool workdir/cwd明示を追加する。引用は実際の最小文字列を要求し、欠落判定でも実在する見出し等の非空引用を付ける。rubric意味行は減らしていない。

grader合成チェック21件はPASS。記録は `infrastructure-verification-evidence-boundary-r3.json` と同名 `.raw.log`。grader SHA-256 は `32397d3af2dc6c7a8baf262ae0028721d272620b63c20ce5c3787d521602ddc1`。

fresh batchは `batches/search-basic-r03-probe-40-r3`。basic03 canonical MD SHA-256 `ef7967cf6f086e0475f7a747709afb3abdc1bd7e6813afa5d524956a6d8c3a21` を封印した。23shard、first shard36行。全batch/requestのIDは854件すべてuniqueで固定選択文書rubric setと一致する。全11文書の固定値は7079行・満点8682点。試行は正式な95%採点ではない。rootがsession47439で開始したと通知した。点検担当は推論を再実行せず、live graderは終端まで固定する。

combinerとselection schemaへ `referenceMode` を追加した。source-onlyとtraining-assistedの成績は別のimmutable JSONへ集計し、同じmodeと固定snapshot SHAだけを受け入れる。未記載legacyはsource-only。capsuleの既存sourceModeを読み、referenceModeとの衝突を拒否する。文書seal、snapshot、視覚review、画像bytes、raw source resource hashの不一致を拒否する。許可参考資料はraw source resourceに含めない。元の分母・採点規則・本文得点とsource観測の区分は変更していない。

- source-only固定manifest SHA: `2f64e2211b1fcd7850203927fc75b5a7f2ce37457cc2afe88c8065d9f931273b`。41 sourceファイルを実bytesで確認した。
- training-assisted固定manifest SHA: `e76a6c40e8927011fff9145d5f5ab2fa94ad89acefc9a03bbad0cbf09b85a0e7`。41 sourceと11許可referenceファイルを実bytesで確認した。

mode混在の両方向、legacy、snapshot/source/reference drift、別稿、失敗shard、視覚mode/snapshot/rawresource/image drift、重複ID、全固定分母の維持を含む合成チェック29件はPASS。記録は `combiner-verification-reference-modes-r2.json` と同名 `.raw.log`。schema検査・Python AST検査・対象diff whitespace検査も通過した。live snapshotとfresh probeの再照合は `mode-and-probe-readiness-r3.json`。combiner SHA-256 は `ad169dbb0a987ad7fe71724a254a7212c2dce198e6655418fbf1d9578e078010`。使用runtimeは封印済みbundled Python3.12.14 / jsonschema4.25.1で、モデル・推論設定は変更していない。

未実施: 新probeの完了確認、全shard正式採点、独立欠陥正規化、全11文書の採点結果統合、視覚レビューの実画像確認、実アプリ/DB実行。合成チェックは評価基盤の検査であり、生成仕様の合格を意味しない。
