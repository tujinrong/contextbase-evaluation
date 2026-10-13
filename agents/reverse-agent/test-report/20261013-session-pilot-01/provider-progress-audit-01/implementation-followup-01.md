# File stdin の将来工程修正と検査

2026-10-13 01:32 UTC。読取り監査を保存した後、root の指示で現行 `src/contextbase/ai/provider.py` と `src/contextbase/tests/test_ai_provider.py` だけを修正しました。現在実行中の第5稿は凍結 runtime を使っており、この修正は適用していません。監査記録の旧 SHA と各指摘はその版の証跡として保存しました。

Provider は保存済み UTF-8 の `prompt.txt` を rb で開き、`subprocess.run(stdin=...)` に渡します。`input=prompt_bytes` を除いたため、Python 親プロセスが入力 pipe へ全 prompt を同期書込みする経路がなくなりました。CLI の指定、prompt の bytes、raw stdout/stderr、answer 保存、構造検査、timeout/KeyboardInterrupt の扱いは維持しました。絶対期限や強制停止・所有 descendant の保証は別問題で、PPA-01/PPA-03/PPA-04/PPA-05 の外部停止証跡補完は引き続き必要です。

49件の provider suite が PASS（失敗0、error0、skip0、1.906秒）。追加は3件です。保存ファイルが rb の regular stdin で input 引数を渡さないこと、実人工子プロセスが受け取った UTF-8（改行・日本語・emoji）の SHA/bytes が保存 prompt と一致すること、1 MiB超の stdin を読まない実人工子が1秒 timeoutで復帰して raw events/stderr と未受理 result を残すことを検査しました。既存の timeout と KeyboardInterrupt 部分証跡保存も全件に含みます。実子はローカルの人工 Python code で、Codex model・業務アプリ・DB の実行ではありません。

初回49件には人工子の stderr を LF と期待する fixture の1失敗がありました。実 Windows の CRLF をそのまま保つ `os.linesep` の期待値へ直し、再実行で合格しました。初回の失敗は `implementation-attempt-01.json` に残し、最終の全ログと before/after pins は `implementation-tests-02.log` / `implementation-tests-02.json` に排他的に保存しました。初回の完全 raw log は独立ファイルに保存しておらず、chat の tool output が残ります。

最終コード:

- Provider SHA-256: `9e5a10ab196cf30127a4596ba77538bb9c9e772f783aea240c25baa25bccf26d`
- Provider test SHA-256: `5e2f060346523426ce8ac1a4b74e915761162b97550408dcbb22a36bb008a382`
- 最終検査JSON SHA-256: `4415258fd204cea421253e43d8e7304c45653dfc8ccadab5a1cc8b65ee6d87a9`

全13件の第5稿凍結 runtime を起動時 scope の SHA と再照合し、変更0件でした。`frozen-runtime-check-after-implementation-01.json` の SHA は `1ae3ebd2fdabed3996957311558f09ec6a673d6e66033250df7075887db36783` です。監査11件の変更前照合も変更0、最終検査中の12 code pins も drift0でした。モデル回答の内容、生成原稿、原ソース、原仕様、spec-eval、evaluator-only は読みません。現在ジョブの中断・再起動、正式意味採点、全 AI module の統合試験はこの担当では未実施です。
