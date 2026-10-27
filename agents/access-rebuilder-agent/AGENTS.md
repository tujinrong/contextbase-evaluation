<!-- spec-meta: {"schema":"spec-md/1.0","documentId":"AG-ACCESS-REBUILDER-OPS","version":"0.2","path":"agents/access-rebuilder-agent/AGENTS.md","sheets":[{"heading":"適用","kind":"GRID","sheet":"01_適用"},{"heading":"現在の工程","kind":"GRID","sheet":"02_工程"},{"heading":"保全と記録","kind":"GRID","sheet":"03_保全"}]} -->
# access-rebuilder-agent 作業規則

版0.2／2026-10-27。

## 適用

ルートのAGENTS.md、docsの全体規則、[契約](AGENT.md)、[作成計画](docs/作成計画.md)を読む。選択project、入力ファイル、予定sourceRoot、工程、許可パスを固定する。汎用Agentの規則と訓練題材固有の事実を分ける。

## 現在の工程

利用者は2026-10-27に計画を確認し、「実装とtest-project1での訓練」「反復回数は２回まで」を指示した。現在はimplementation／verificationであり、抽出器・工程制御の実装、ACCDB定義の取得、C#／DDL生成と検証が許可されている。続いてローカルSQLEXPRESSへの新規訓練専用DB作成を選択した。対象はプロファイルに記録する専用DBに限定する。

変換反復は永続台帳のbegin-iterationからcomplete-iterationまでを1回とし、最大2回。取得準備の再試行と、同じ候補で発見した問題の修正・確認はその回の内部作業として記録する。上限到達後に新しい候補の反復を自動開始しない。訓練の追加には利用者の新しい指示が必要。

後続の明示的な実施指示を受けたら、その範囲をプロファイルと実行記録へ反映して進める。同じ許可を繰り返し要求しない。コードだけの指示からDB投入まで許可されたと解釈しない。

## 保全と記録

原ACCDB、既存Access／CSharp_ASPNET、入力、QA、fixture、spec-evalを変更しない。spec-evalと既存方式の原仕様は調査・変換入力から除外する。参考ソリューションは許可された構成資料だけを使う。既存の業務実装や期待値のコピーをACCDB変換として扱わない。

最終記録は固定build/、一時コピー・失敗試行は.tmp/。入力の版・SHA-256、実施範囲、未実施を明記し、前回のPASSを流用しない。今回作成した文書の主章とspec-meta.sheetsを同期する。
