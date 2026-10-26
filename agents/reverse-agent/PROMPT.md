# reverse-agent 実行指示

版1.5／2026-10-26。取得・目録化→関係構築→動作深化のv2の依頼と実行手順。実行コマンドは [ガイド](docs/ContextBase初期実装.md)を参照する。

## 依頼を確定する

[共通契約](AGENT.md)を読み、projectId、元目標、対象範囲、必要義務、許可入力、基準版、検証条件、作業先を確定する。実行種別は抽出と独立検証を区別する。requestにはschema=contextbase-analysis/2を必須とし、各義務にid／question／stage／scope／requiresを記載する。task.operationはextract／verify、抽出stageは3層とする。

原仕様全体・spec-evalは実行権限で禁止し、入力根の外へ隔離する。CLIパスは入力根内の相対パスに限定する。配置、原文保護、build／.tmp、QA等の共通条件は共通契約に従う。

## 必要な層を選ぶ

| 必要な成果 | 抽出担当 |
| --- | --- |
| 概要・業務機能・入口・データ・共通の目録、対象追加 | [discovery](roles/discovery/AGENT.md) |
| 定義・呼出し・データ・共通・外部との接続と条件 | [relationship](roles/relationship/AGENT.md) |
| 条件・値・状態・順序・例外・副作用・呼出差 | [behavior](roles/behavior/AGENT.md) |

ホストは該当領域の検証済み前提を確認して抽出作業を依頼する。関係判断に必要な引数・条件の読取りはrelationshipでも行う。behaviorは未確認関係を確定扱いせず、関係構築へ補査要求を返す。全層で必要なアダプターと原文を利用できる。

目標が前層だけで満たされればそこで返し、検証・適用性が有効な既存成果があれば不要な再抽出を避ける。全リポジトリの完了待ち、全対象の3層直列実行、情報量の固定3段階を要求しない。

## 独立検証と採用

各層の候補は共通の独立検証実行へ渡す。検証は作者と別task・文脈で原文・登録点・未調査領域を確認し、候補を直接書き換えず指摘・範囲・未知を返す。第4の段階子Agentや作者の自己検査にはしない。

ホストが版、根拠、依存、競合、検証と指摘処置を確認して採用・範囲受入れを判断する。上流の修正は依存成果を失効確認し、新しい版で再検証する。元目標が未達なら部分成果と未完了を維持する。

未知のライフサイクルはrecordのowner失効と分離する。上流候補の置換や明示reviseでも既存unknownのid・内容・hashを保持し、作者が省略しても消さない。影響を受けた旧検証decisionは失効させ、後続verifyが各未知を独立に再判定する。

followupが採用予定viewで有効な上流義務を指す場合、当候補のcoverageがsupportedでverifyがpassでもadoptを阻止する。runも補査要求を保存して停止し、明示reviseと再調査を待つ。現在候補のrequirementsだけを調べて上流への補査を見逃さない。まだ採用していない将来義務への質問はhandoffQuestionsとして後続層のcontextへ渡し、現在の前層採用を一律には妨げない。

## v2の実行と報告

step --stageで単独抽出、verifyで独立検証、adoptでホスト採用を行う。runは要求グラフ内のready義務を自動進行し、阻害時はpendingを返して止まる。同basisで再実行しても新モデル呼出しを増やさない。未定義の補査・scope拡大はホスト判断に戻す。

採用済み内容を再調査する場合はreviseで義務と依存下流を撤回し、step --feedbackで旧候補を材料に原文を読む。未知のrelatedRequirementsとblocksRequirementsを分け、非阻害でもverifyの根拠付き判定を要する。recordはownerRequirementを持ち、ホストが依存key／versionを固定する。旧v1 request／sessionや --role は自動移行せず、明示v2を新規作成する。

固定総予算、取消・再開、原文保持、未知と失効、storeの信頼境界は共通契約に従う。入出力・契約の版、採用範囲、検査、未達・未実施を報告する。清掃済みの旧試行workspaceを再開せず、再試行は新しい範囲・request・workspaceで行う。旧仕様書経路は明示依頼時だけ [旧契約](docs/legacy/README.md)を参照する。
