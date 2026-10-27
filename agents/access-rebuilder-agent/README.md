<!-- spec-meta: {"schema":"spec-md/1.0","documentId":"AG-ACCESS-REBUILDER-README","version":"0.4","path":"agents/access-rebuilder-agent/README.md","sheets":[{"heading":"現在の状態","kind":"GRID","sheet":"01_状態"},{"heading":"入口","kind":"LIST","sheet":"02_入口","key":["文書"]},{"heading":"訓練と配置","kind":"GRID","sheet":"03_訓練"}]} -->
# access-rebuilder-agent

版0.4／2026-10-27。指定されたAccessファイルからASP.NET Core／C#／SQL Serverのシステムを再構築するAgent。

## 現在の状態

利用者の追加指示により、[Web再構築方針](docs/Web再構築方針.md)を採用した。CSharp_ASPNETソースを参照し、Accessの業務目的をWebとして使いやすいUI・操作へ再設計する。抽出器・SQL構造変換・入力検査・反復制御とtest-project1のC#／Web／SQL Server成果物を持つ。初回の[訓練結果](docs/訓練結果.md)2回は台帳を保持し、その後の明示されたWeb化改訂の結果を別に記録する。

2026-10-27の確定ルール：Web画面は有効スペースを節約し、PCでは左見出し・右項目の列を揃えた表形式を標準とする。日付・和暦はコンパクトなカレンダー入力と同期した和暦表示を使う（AR028～030）。正本は[Web再構築方針](docs/Web再構築方針.md)。今回の追加はルール更新であり、新配置のアプリ実装・ブラウザー検証は未実施。

## 入口

| 文書 | 内容 |
| --- | --- |
| [作成計画](docs/作成計画.md) | 確認対象。実装順序、出力構成、訓練方法、完了条件 |
| [調査結果](docs/調査結果.md) | 入力ACCDB・参考ソリューション・環境・技術上の課題 |
| [Agent契約](AGENT.md) | 汎用的な役割、入力の境界、出力、実施状態 |
| [運用規則](AGENTS.md) | このフォルダーを更新する作業Agentへの指示 |
| [実行指示](PROMPT.md) | 計画工程と実装工程の依頼方法 |
| [変換ルール案](docs/変換ルール.md) | 今回の初期仮説。訓練結果で検証して改訂する |
| [訓練プロファイル](profiles/test-project1.json) | 指定入力と出力先、参考資料の許可範囲、未承認状態 |
| [調査manifest](build/research.json) | 今回読んだ根拠ファイルの版・SHA-256 |

## 訓練と配置

最初の対象は`test-project1`。入力は`test-project1/srcs/Access/build/StudentManagement.accdb`、予定sourceRootは`test-project1/srcs/Access-CSharp_ASPNET/`。C#をその`src/`、DB構成とSQLを`database/`へ分け、ルートの`StudentManagement.slnx`から開ける形を目指す。

ここでの訓練は、変換・独立比較・失敗分析を反復してAgentルールを改善することを指す。モデルの追加学習は行わない。学生管理固有の値はこの訓練プロファイルと対象方式側に保持し、汎用Agentへ組み込まない。

今回のsourceRootとspecRootを作成した。共通の調査・計画記録はこのAgentの`build/`、方式別の抽出・生成・検査・反復台帳は対象sourceRootの`build/`、中間作業は`.tmp/`へ置く。今回の台帳は上限2回で、3回目を開始しない。
