<!-- spec-meta: {"schema":"spec-md/1.0","documentId":"AG-ACCESS-REBUILDER-OPS","version":"0.7","path":"agents/converts/access-rebuilder-agent/AGENTS.md","sheets":[{"heading":"適用","kind":"GRID","sheet":"01_適用"},{"heading":"現在の工程","kind":"GRID","sheet":"02_工程"},{"heading":"保全と記録","kind":"GRID","sheet":"03_保全"}]} -->
# access-rebuilder-agent 作業規則

版0.7／2026-10-28。

## 適用

ルートのAGENTS.md、docsの全体規則、[契約](AGENT.md)、[作成計画](docs/作成計画.md)を読む。選択project、入力ファイル、予定sourceRoot、工程、許可パスを固定する。汎用Agentの規則と訓練題材固有の事実を分ける。

## 現在の工程

利用者は2026-10-27に計画を確認し、「実装とtest-project1での訓練」「反復回数は２回まで」を指示した。現在はimplementation／verificationであり、抽出器・工程制御の実装、ACCDB定義の取得、C#／DDL生成と検証が許可されている。続いてローカルSQLEXPRESSへの新規訓練専用DB作成を選択した。対象はプロファイルに記録する専用DBに限定する。

変換反復は永続台帳のbegin-iterationからcomplete-iterationまでを1回とし、最大2回。取得準備の再試行と、同じ候補で発見した問題の修正・確認はその回の内部作業として記録する。上限到達後に新しい候補の反復を自動開始しない。訓練の追加には利用者の新しい指示が必要。

後続の明示的な実施指示を受けたら、その範囲をプロファイルと実行記録へ反映して進める。同じ許可を繰り返し要求しない。コードだけの指示からDB投入まで許可されたと解釈しない。

## 保全と記録

2026-10-28の利用者指示により、移行方式の現行IDをAccess-To-CSharp_ASPNET、sourceRootをtest-project1/srcs/Access-To-CSharp_ASPNET/、specRootをtest-project1/spec/Access-To-CSharp_ASPNET/へ変更する。フォルダー・設定の名称変更であり、DB名・接続先・原Access・訓練2回の台帳を変更しない。封印済み記録の旧識別子は履歴の根拠として保持する。

原ACCDB、既存Access／CSharp_ASPNET、入力、QA、fixture、spec-evalを変更しない。spec-evalと既存方式の原仕様は調査・変換入力から除外する。2026-10-27の利用者の追加指示により、CSharp_ASPNETのソースをWebアプリの設計・実装の参考に使える。[Web再構築方針](docs/Web再構築方針.md)を読み、Accessの操作形ではなく業務目的をWebへ実装する。参照元は読取り専用とし、認証・DBの異なる業務契約を無条件に上書きしない。

Web画面は有効スペースを節約し、PCでは左見出し・右項目の列を揃えた表形式を標準とする。日付・和暦はコンパクトなカレンダー入力と同期した和暦表示を使う（AR028～030）。ルール採用時の工程は設計更新だった。その後の利用者の「このルールで変換し直してください」を実施根拠として、test-project1のAccess-To-CSharp_ASPNETへ3規則を適用して検証する。既存DB構造・既存データ・完了済み2回の訓練台帳を維持し、今回版の検証結果を新たに記録する。

2026-10-28の追加指示として、グループ見出しは内容領域の上方に独立した太字で置き、Access風の枠線切欠き表示を既定にしない。主要なWebメニューは左の縦サイドメニューに配置し、選択中・権限・キーボード操作と本文の有効幅を保持する（AR031・AR032）。test-project1のAccess-To-CSharp_ASPNETへ適用し、PC向けの実装・検証を記録する。スマートフォン対応は対象外とする。

この追加指示のWeb化改訂は、完了済みの訓練2回を再開せずに実施する。台帳と原本のhashを保持し、新しい版の検証・出力manifestを固定パスへ更新する。

最終記録は固定build/、一時コピー・失敗試行は.tmp/。入力の版・SHA-256、実施範囲、未実施を明記し、前回のPASSを流用しない。今回作成した文書の主章とspec-meta.sheetsを同期する。
