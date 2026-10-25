# build-agent 実行指示

定義版7.6／2026-10-24。[契約](AGENT.md)と全体docsを読み、projectId・工程・方式・許可範囲・入力版を固定する。原仕様は各方式specだけ、spec-eval・他方式の仕様／ソース・過去PASSは実装入力にしない。

preflight.mjs --project <projectId> --profile <方式ID> --run-id <今回識別>を実行し、build/generation/inputs.json・structure.jsonで構造と入力hashを固定する。構造PASSとは別に意味整合を確認する。構造問題は同固定先へ記録して中断し、未決の業務／DB共有契約を推測補完しない。

各方式のソース・DDL・画面・手順は方式内の正本を更新する。中間生成・失敗試行・cache・隔離展開は同方式.tmp/だけで処理する。最終配布物はbuild/、今回の最終検査結果はbuild/test-results/、仕様ID対応と入出力manifestはbuild/generation/の固定名へ更新する。実行ID別フォルダー・backup・archiveで旧生成物を残さず、Git履歴を使う。正式な入力・QA・試験コード・fixtureは保持する。

生成後は今回の入力版で利用可能な検査を実行し、実行コマンド・処理系・終了値・検査範囲・未実施を記録する。失敗・未検証を過去のPASSで補わない。原仕様を含まない逆生成入力は方式内build/source.zipへ更新する。最後に同じproject/profile/run-idでmanifest.mjsを実行し、凍結入力と最終出力のhashを再照合してbuild/generation/outputs.jsonを更新する。

全方式集約だけproject/build/、その中間物だけproject/.tmp/を使う。出力先の利用者指定は優先する。コード／仕様の横断共用は引き続き禁止。共有SQL Server、AccessのSQLフロントエンド化、IBM i接続などの未確定契約を配置修正だけで変更しない。生成・build・単体・結合・実機・正式受入・逆生成採点は別状態で報告する。
