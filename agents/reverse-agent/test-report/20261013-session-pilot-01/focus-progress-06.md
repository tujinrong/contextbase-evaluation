# 継続記録 06

記録時点: 2026-10-13 10:44 JST。期限: 同日12:20:58 JST。対象は test-project1 / CSharp_ASPNET の学生検索と学生登録・編集の2画面です。第5稿の新規AI解析は両件完了し、AIが本文を執筆中です。新しい本文、画像、意味採点はこの記録時点で未完成です。

| 反復 | 確認点 / 316 | 欠落点 | 矛盾点 | 保留点 | 正式率・95%判定 |
|---|---:|---:|---:|---:|---|
| 開始時 | 269 | 39 | 0 | 8 | null |
| 第1稿 | 274 | 35 | 0 | 7 | null |
| 第2稿 | 286 | 20 | 3 | 7 | null |
| 第3稿 | 266 | 40 | 3 | 7 | null |
| 第4稿 | 283 | 20 | 6 | 7 | null |
| 第5稿 | 未採点 | 未確定 | 未確定 | 未確定 | null |

第4稿は検索133/147、登録・編集150/169です。第2稿は行と理由の誤結合を訂正した評価を採用し、点数は変わっていません。第4稿の最終281行は独立検証・凍結済みですが、編集評価の初期暫定JSON/文脈確認の全文bytesは上書き前に保存できませんでした。旧hash、残存MD、遷移記録は保持し、失った原bytesの復元は主張しません。過去の承認や採点は第5稿へ流用していません。

## 第5稿の入力・工程

- 版5.0の出力先: `test-project1/spec-analysis/CSharp_ASPNET/20261013-focus-round-05`。現在は完成本文未作成です。
- 試行: `.tmp/20261013-session-pilot-01/focus-round-05`。開始時に汎用runtime13ファイルとrunner全文を凍結しました。生成session71665、描画session86475を継続し、追加の解析・執筆・描画は起動していません。
- 入力は原ソース43ファイルと許可された参考設計11ファイルを持つtraining-assisted capsuleです。legacy-v1のraw/index/metadata再検査を使用し、sealed snapshotやblind source-only生成精度の主張はしません。plan SHAは `232c3f10288f4d6363ac6995dd7f6780bf703d07e35872cfb43ea0d5e4df25bd`、capsule manifest SHAは `3a722dc206dbf2ce850b594aa1bee65117e472a8144531adb731d354fb9a5a24` です。
- 検索解析: 69 facts、43 declared source paths、未解決10件、analysis SHA `ca091396fe147f52ac67e914d403249f06517eb8f63e67d09224901ef5c04441`。
- 編集解析: 91 facts、37 declared source paths、未解決8件、analysis SHA `461ec0be4b635c1abda4d42532f8a81a4cba1f8cb4a8b802474a444969a36eba`。
- pathsはAIの読取り宣言です。全tool accessの独立監査やOSによるread-only強制を意味しません。編集解析の実result/answer/events/checkpoint/handoffを評価担当が新規照合し、raw-provenance-progress-02を排他保存しました。検索の同等監査と両執筆の完成証明は待機中です。
- 評価担当は88入力pinを固定し、元281行・316点は全件未採点/nullです。生成側へ期待セルや採点値を渡しません。独立視覚レビューも準備だけで、第5稿の画像閲覧0件、承認nullです。

## 今回確認した作成手順の不備と改修

Windowsの`subprocess.run(input=..., timeout=...)`は、子がstdinを読まない条件で、同期PIPE書込みがtimeout待機より前に止まり得ます。新しいProviderは保存済みUTF-8 promptをregular file stdinから同一bytesで渡します。実子へのbytes一致とstdin非消費timeoutを含むProvider49試験が通りました。初回の人工stderr改行期待1失敗はWindows CRLF fixtureを直し、旧試行を保存しています。今回の実AIジョブでstdin障害が発生した証拠はありません。

改修後の全体工程検査は `method-integration-10/results.json` で **301試験PASS、失敗/error/skip各0、検査前後のcode/test pins変更0件** です。これは汎用工程と信頼したブラウザの試験件数であり、仕様の301/316点を達成した意味ではありません。現在の第5稿は起動時の旧Providerを含む凍結13ファイルを保持し、今回の改修は次の試行へ適用します。

強制終了ではProviderのKeyboardInterrupt処理やfinal result保存を通らないため、期限用に `capture_owned_cycle.py` を追加しました。最新継続記録、config、所有PID・creationDate・commandLineを照合し、稼働中ファイルを停止前後に別名でコピーして各SHAとcopy中の変化を記録します。早期停止、古いhandoff、config/root不一致は拒否します。停止処理のtimeout/不正応答/例外/interruptでもraw出力、UNKNOWN状態、停止後inventoryを保存し、欠けたProvider結果を補完しません。

独立検査13ケースPASS、実dryrun2回の所有2processと132コピーSHAを照合済みです。実停止は未試験です。`STOP_REQUESTED`は終了確定ではなく、残存process・新descendantの別CIM確認が必要です。helper旧版のtransport保存欠落は抜粋再現で確認し、旧版全文bytesの保存は未実施、新版全文snapshotの保存と区別しました。期限時の自動実行wrapperは準備中です。

この前から改善しているNULL/版の図合流、NULLキー例外とcatch順序、同機能の参考設計範囲、Markdown表のcode pipe、テキスト未解決と未実施scopeの分離、評価の排他保存は第5稿の凍結runtimeへ含まれます。仕様本文の修正はAIに任せ、Pythonによる業務条件hardcoding・定型本文組立て・本文差替えは行いません。

## 保護・未実施

`focus-protected-check-06.json`で元のセッション対象179ファイルのSHA一致、欠落0・変更0を再確認しました。全repositoryや未登録ファイルまで不変と主張しません。

構造検査、AIテキスト承認、描画成功、実画像/原ソースの独立視覚確認、意味採点は別判定です。第5稿のこれらの完成判定はまだありません。実アプリ・DB/SQL実行、狭幅と全モードの実機確認、全1408行の評価、PDF/Excel出力、別題材への汎化確認は未実施です。正確なモデル名/推論設定は記録がなく、推定しません。最新の継続JSONと各scope/progress/resultsを実行状態の判断元にし、期限で新規解析を止め、所有が確認できた処理の証跡を保存して最終報告します。
