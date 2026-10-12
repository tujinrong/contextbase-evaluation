# build-agent 実行指示

定義版7.1／2026-10-12。Codexの作業指示として使用する。

`agents/build-agent/AGENT.md`を読んでAG-BUILDとして作業する。実行要求からprojectId・工程・許可範囲を固定し、全体docs/agentsを読んだ後、選択projectの仕様・開発規約を検査する。入力セットの各版とSHA-256をreportに記録する。spec-evalを実装の入力にしない。

生成後は同じ実行IDの `scripts/manifest.mjs` で入力が変わっていないことを確認し、出力ファイルのSHA-256を記録する。入力が変わった場合は新規実行IDで再検査する。既存レポートを上書きしない。

各方式のプログラムは選択projectの`srcs/方式ID/`へ作成する。仕様の局所バグは、業務判断なしで一意に直せる場合に修正する。仕様構造や共有契約の問題は`report/`に根拠付きで報告して中断し、別Agentへ修正を委ねる。明示的な指示がない限り`agents/build-agent/`と選択project以外を変更しない。

事前検査は次のように実行する。実行IDは毎回変更する。

```powershell
node agents/build-agent/scripts/preflight.mjs --project test-project1 --run-id 20261012-build-01
```

終了コード0でも意味上の整合性検査が必要。2なら生成を中断して出力された構造検査報告を読む。生成再開時は別Agentの修正を新しい入力セットとして検査し直す。入力コミットと作業ツリーの差分を区別し、全方式の生成/コンパイル/試験/未実施を最終報告する。
