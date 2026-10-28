<!-- spec-meta: {"schema":"spec-md/1.0","documentId":"AG-ACCESS-REBUILDER-PROMPT","version":"0.7","path":"agents/converts/access-rebuilder-agent/PROMPT.md","sheets":[{"heading":"共通の指定","kind":"GRID","sheet":"01_指定"},{"heading":"今回の計画工程","kind":"GRID","sheet":"02_計画"},{"heading":"確認後の実施工程","kind":"GRID","sheet":"03_実施"}]} -->
# access-rebuilder-agent 実行指示

版0.7／2026-10-28。Codexへの依頼文と実行機構の運用契約。

## 共通の指定

[契約](AGENT.md)と[運用規則](AGENTS.md)、[Web再構築方針](docs/Web再構築方針.md)を読み、projectId、phase、入力Accessファイル、出力方式、Web参照ソースと許可範囲を固定する。現行プロファイルはweb-nativeであり、Accessの操作形を同じにする要求はない。完了済みの訓練2回は再開せず、その後の利用者が明示した改訂として実装・検証する。

Web画面は有効スペースを節約し、PCでは左見出し・右項目の列を揃えた表形式を標準とする。日付・和暦はコンパクトなカレンダー入力と同期した和暦表示を使う（AR028～030）。設計時に対象表示領域と狭幅時の配置を固定し、実装時には列揃え・カレンダー選択・和暦変換・保存値を検証する。ルール更新の依頼だけではアプリやDBの再生成を開始しない。

グループ見出しは内容領域の上方に独立した太字で置き、Access風の枠線切欠き表示を既定にしない。主要なWebメニューは左の縦サイドメニューに配置し、選択中・権限・キーボード操作と本文の有効幅を保持する（AR031・AR032）。見出しの独立配置と左ナビゲーションを実画面で検査し、既存の業務・認証・権限・未保存状態を維持する。

## 今回の計画工程

> projectId=sample-project1、phase=planning。入力はsample-project1/srcs/Access/build/StudentManagement.accdb、予定出力はsample-project1/srcs/Access-To-CSharp_ASPNET/。骨格、読取り調査、作成計画を作成する。StudentManagement.slnxは構成の参考にする。Access起動・実抽出・変換器実装・C#／SQL生成・DB実行は行わず、計画を利用者へ提示する。

## 確認後の実施工程

> 計画確認後の利用者の実施指示を根拠として、許可範囲とphaseを更新する。入力hashを再照合し、作成計画のP1から実装する。入力が変更されていれば今回版の差分を調査して記録する。C#は対象sourceRoot/src/、DB構成とSQLはdatabase/へ出力し、StudentManagement.slnxから開ける構成とする。対応表・未対応一覧・今回の検査結果を固定build/へ記録する。DB接続・投入はその実施範囲と接続先の指定がある場合に実行する。

未実装の抽出・変換コマンドを実行済みと報告しない。既存build-agentのpreflightは仕様からの順生成用であり、このsource-file入力へ無変更で適用しない。
