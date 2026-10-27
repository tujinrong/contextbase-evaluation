# build-agent 実行指示

定義版7.8／2026-10-25。[契約](AGENT.md)と全体docsを読み、projectId・工程・方式・specRoot=project/spec/方式ID/・sourceRoot=project/srcs/方式ID/・許可範囲・入力版を固定する。原仕様は選択方式のspecRootだけとし、旧sourceRoot/specへfallbackしない。spec-eval・他方式の仕様／ソース・過去PASSは実装入力にしない。

preflight.mjs --project <projectId> --profile <方式ID> --run-id <今回識別>を実行し、build/generation/inputs.json・structure.jsonで構造と入力hashを固定する。構造PASSとは別に意味整合を確認する。配置移動など検査だけの工程は`--inspect-only true`を付け、標準出力JSONを確認する。この場合は既存のbuild/記録・outputs.json・source.zipを書き換えず、生成工程の凍結入力記録としては使わない。構造問題は同固定先へ記録して中断し、未決の業務／DB共有契約を推測補完しない。

選択方式のspecRootから読み、ソース・DDL・画面・手順はsourceRootの正本へ生成する。中間生成・失敗試行・cache・隔離展開は同方式.tmp/だけで処理する。最終配布物はbuild/、今回の最終検査結果はbuild/test-results/、仕様ID対応と入出力manifestはbuild/generation/の固定名へ更新する。実行ID別フォルダー・backup・archiveで旧生成物を残さず、Git履歴を使う。正式な入力・QA・試験コード・fixtureは保持する。

全方式で[テストデータ整備規約](../../../docs/テストデータ整備規約.md)を適用し、必要マスタ・架空の初期確認用業務データ・安全な投入/再投入・操作手順・件数manifestを用意する。既存利用者データと破壊試験fixtureを分け、正常な検索→選択→参照/編集→取消、新規→保存→再検索を確認する。旧仕様の空配布と新指示が異なる場合は差分根拠を残す。別方式の実データや認証前提を流用しない。

Accessは[Access生成チェック](docs/Access生成チェック.md)を読み、標準部品、文字サイズ/グループ見出し、新規業務キーの入力属性、InputMask/Format/保存値の区別を確認する。VBAコンパイル・プロパティ・実キー/貼付操作・画面目視を分け、モデルやValueへの代入だけで入力できると判定しない。方式固有の業務長・認証・保存契約は維持する。

生成後は今回の入力版で利用可能な検査を実行し、実行コマンド・処理系・終了値・検査範囲・未実施を記録する。失敗・未検証を過去のPASSで補わない。原仕様を含まない逆生成入力はsourceRoot/build/source.zipへ更新する。逆生成の取得・独立検証ではproject/spec/全体とspec-evalを除外する。最後に同じproject/profile/run-idでmanifest.mjsを実行し、凍結入力と最終出力のhashを再照合してbuild/generation/outputs.jsonを更新する。

全方式集約だけproject/build/、その中間物だけproject/.tmp/を使う。出力先の利用者指定は優先する。コード／仕様の横断共用は引き続き禁止。共有SQL Server、AccessのSQLフロントエンド化、IBM i接続などの未確定契約を配置修正だけで変更しない。生成・build・単体・結合・実機・正式受入・逆生成採点は別状態で報告する。
