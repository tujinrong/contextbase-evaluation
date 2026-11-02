# ContextBase 調査フローに活かせる参考実装

調査日：2026-10-28／知識・文脈管理の追補：2026-10-29
目的：ContextBase の調査・成果保存・独立検証・再開設計に役立つ実装上の考え方を、一次資料から限定して整理する。

## 結論

この資料から採用する中心点は、①構文・静的導出・業務解釈の由来を分ける、②索引を原文へたどる検索基盤にする、③構造や形式の検査結果を業務上の正しさと取り違えない、の3点である。調査単位、全体義務、Agent間の前提、実装順序、実装状態は[段階的抽出・検証フロー](ContextBase段階的抽出・検証フロー.md)§18と[実装計画](ContextBase実装計画.md)§12を正本とする。

## 一次資料から得られる示唆

| 参考 | 実装で確認できること | ContextBaseに使える考え方 | そのまま使わない点 |
| --- | --- | --- | --- |
| [Aider Repository Map（公式説明・実装）](https://aider.chat/docs/repomap.html) / [repomap.py](https://github.com/Aider-AI/aider/blob/main/aider/repomap.py) | ファイル依存と抽出した定義・署名を順位付けし、会話と予算に応じて地図を絞る。 | 索引を原文へたどる構造ナビゲーションとして使う。 | ランキングは業務上の重要性・完全性・分類の正しさを証明しない。 |
| [Joern CPG](https://docs.joern.io/code-property-graph/) / [frontends](https://docs.joern.io/frontends/) | 言語別frontendがCPGを生成する。CPGは構文・制御・データ依存などの表現を統合し、追加の抽象度をoverlayで表す。schemaはnode/edge/propertyを明示する。 | 「構文事実→明示規則で導出したリンク→業務解釈」を由来別に保つ。 | CPG schemaやdataflowの妥当性は、業務機能・責務・全体coverageを証明しない。 |
| [Understand-Anything skill](https://github.com/Egonex-AI/Understand-Anything/blob/main/understand-anything-plugin/skills/understand/SKILL.md) / [merge source](https://github.com/Egonex-AI/Understand-Anything/blob/main/understand-anything-plugin/skills/understand/merge-batch-graphs.py) | skillはscan→batch→merge→review/saveとinventory照合を指示する。merge sourceは重複nodeを後勝ちにし、参照先nodeのないedgeを落とす。 | inventoryとbatchを分け、処理失敗・未解析をレビューに渡す。 | merge sourceの機械修復は表示graphには有用でも、意味上の矛盾を解決しない。skillのLLM review指示は欠損欄補充やinvalid node除去を認めるが、これは手順上の指示であり、ここで確認したmerge sourceの処理とは区別する。 |

### 1. Aider：索引は選択の道具

Aider の[公式説明](https://aider.chat/docs/repomap.html)は、ファイル一覧・重要シンボル・型・署名を簡潔な地図にし、ファイル依存の順位付けで会話に関係する部分を予算に合わせて選ぶと説明する。利用者は地図から特定ファイルの原文へ進める。[実装](https://github.com/Aider-AI/aider/blob/main/aider/repomap.py)も `RepoMap` のtoken上限とタグ順位付けを持つ。

ContextBaseでは、Tree-sitter索引を「AIに全部読ませる成果」ではなく、入口・宣言・参照・設定・SQL候補を検索し、原文を検証可能な単位で取得するナビゲーション層として位置づける。候補の重要度ランキングと、義務を満たした証明は別物である。indexで表現できなかったファイル、対応外grammar、動的呼出しは、取得台帳の状態として残す。

### 2. Joern：異なる解析表現を層として合成する

[JoernのCPG資料](https://docs.joern.io/code-property-graph/)は、syntax・control-flow・intra-procedural dataflow表現を統合した共通IRと、異なる抽象度を加えるoverlayを説明する。ASTやCFGをすべて後付けoverlayとして扱う説明ではない。各言語の[source frontend](https://docs.joern.io/frontends/)がASTを生成し、対応能力や成熟度は言語ごとに異なる。CPGは型付きnode、ラベル付き有向edge、propertyを持つ。

ContextBaseでは、最低でも次の由来を分ける。

* **構文事実**：宣言、構文call site、参照名、source位置など、parserが実際に観測した内容。
* **静的導出**：設定登録、名前束縛、型候補、route/model/table接続など、版付きの決定規則で導出した内容。
* **業務解釈**：入口の目的、機能の主/子/共通、責務、ユーザー可視の動作など、根拠付きでAIが提案・レビューする内容。

同じ「call」でも、call-siteの存在とcalleeへの関係は別に扱う。[Joern Calls](https://docs.joern.io/cpgql/calls/)はcall-siteとcaller/calleeを別のtraversalとして公開する。[Data-flow semantics](https://docs.joern.io/dataflow-semantics/)も、依存・外部methodを完全にモデル化することは高コストで、未定義semanticsが過剰かつ不精密な伝播を生む例を説明する。ContextBaseでは未解決callや複数候補を確定辺へ潰さず、業務上の機能関係は根拠のある別recordとして扱う。

### 3. Understand-Anything：batchとreviewを分けるが、統合修復を監視する

公開されている[/understand skill](https://github.com/Egonex-AI/Understand-Anything/blob/main/understand-anything-plugin/skills/understand/SKILL.md)は、scan manifest、semantic batch、batch別解析、merge、review/saveの手順を記述する。incremental経路では前回scan/hashから変更範囲を選び、reviewerにはscan inventoryと出力graphの両方向の対応確認を指示する。ここから「作業計画が調査範囲を独占しない」「元inventoryから漏れを別に検査する」を参考にできる。

機械統合の実装（[merge-batch-graphs.py](https://github.com/Egonex-AI/Understand-Anything/blob/main/understand-anything-plugin/skills/understand/merge-batch-graphs.py)）は重複node IDを後勝ちで保持し、参照先nodeがないedgeを削除する。これはソースコードで確認できる。一方、欠損欄に既定値を入れる・invalid nodeを削除するといった修復は[skillのreview手順](https://github.com/Egonex-AI/Understand-Anything/blob/main/understand-anything-plugin/skills/understand/SKILL.md)の指示であり、merge sourceの実装として混同しない。いずれもgraphの整形・構造検査であって、業務意味の正しさの証明ではない。

同じ[skillのincremental symbol-loss path](https://github.com/Egonex-AI/Understand-Anything/blob/main/understand-anything-plugin/skills/understand/SKILL.md)は別の厳格な扱いを定める。決定的parserとdeclaration-coverage adapterの両方で削除を確認できる場合だけ既存symbolの欠落を許容し、未対応構文・宣言coverage不足・空抽出・曖昧identityは `unknown` として公開を止める。限定retryは一度だけで、再解析後も不成立なら診断を保持して停止し、古いnodeやsemantic edgeを足してgateを通さない。このincremental gateは、full/default経路のLLM review後に構造修復を試み、重大問題が残ればwarning付きでgraphを保存しdashboardを止める手順と異なる。したがってUnderstand-Anythingを「常に部分graphを公開する」と一般化せず、経路ごとの採用条件を読む。

## 知識・文脈管理の参考実装（2026-10-29追補）

ContextBaseは既に封印snapshot、構文Fact索引、未採用草稿、検証記録、採用版、checkpointを外部保存している。追補では、保存した情報から各taskに必要な範囲を選び、版と信頼状態を保って利用する機構を比較する。下表は外部実装の観測とContextBaseへの設計上の示唆を分けたもので、各製品の導入決定ではない。

| 参考 | 一次資料で確認した機構 | ContextBaseへの示唆 | 保証の限界 |
| --- | --- | --- | --- |
| OpenViking | L0の摘要、L1の概観から内容を探し、必要に応じてL2の原文を読む。要約sidecarにfreshnessを持つ | task単位の地図と原文取得を分け、必要な対象と根拠を選ぶ | 要約の内容・新鮮さと原文の存在・内容hashは別に照合する |
| Graphiti | entity、fact・relation、元データのepisodeと時間的有効期間を関連付け、増分更新する | Fact・候補・依存・出典と失効理由を追跡する | 出典追跡や有効期間は、モデルの意味判断の正確性やコード変更の全影響を証明しない |
| Letta | git-backedなMemFSで記憶を管理し、Dreamingが会話を振り返って記憶を整理する | 作業上の決定、失敗した方法、復旧条件を簡潔に保持する | 反省・要約を、ソース観測Factや採用済み検証receiptへ昇格させない |
| DeepSeek Harness | Cordisを用いるplugin中心のharness。READMEはdeveloper previewと明記する | 保存・検索・取証・制御の責務を小さいInterfaceへまとめる参考とする | 確認したREADMEから、特定の長期記憶機構やContextBaseの性能改善は立証できない |

### 4. OpenViking：探すための要約と確認する原文を分ける

[Context Layers](https://github.com/volcengine/OpenViking/blob/main/docs/en/concepts/03-context-layers.md)は、L0/L1をディレクトリー単位のsemantic sidecar、L2を原ファイル・下位ディレクトリーとして説明する。これは内容を探して読み進める粒度である。ContextBaseのD05で採用していない「索引・概要・詳細を全件生成する固定情報量」の再導入には用いない。

同資料のfreshnessは直接の子要素と未反映の変更を数える。`pending_child_changes`が残る要約も読取り可能で、閾値未満の変更に時間内の更新を保証しない。したがって、検索で見つかった要約の読取りだけを、現snapshotでの根拠確認に置き換えない。

ContextBaseで参考にするのは、対象ID・版・未確認項目を含む小さな地図から、必要なrecordと結び付いた原文へ進む流れである。要約は候補選択に用い、採用判断には許可されたsnapshotの正確な行区間と内容hashを使う。出力名やL0/L1/L2という呼称をそのまま共有runtimeへ追加する必要はない。

### 5. Graphiti：由来と失効を保持する

[Graphiti README](https://github.com/getzep/graphiti)は、entityと時間的有効期間を持つfact・relationを、元データであるepisodeへ結び付ける。新しいデータを増分で統合し、過去の状態と由来を残す機構が参考になる。Graphitiはframeworkであり、利用側がgraph database、LLM、周辺の運用を用意する。

ContextBaseへの設計上の示唆は、Fact ID、source版・位置、導出規則、候補版、検証対象版、置換・失効理由を結ぶことである。ソース変更ではファイルhashだけでなく、設定、呼出し・データ依存、解析器・規則版から再確認する範囲を決める。依存が未解決なら影響不明を残し、変更の伝播範囲が完全に求まったとは表示しない。

由来が追跡できることと、業務意味が確認済みであることは別の状態である。Graphitiの時間管理を採用しても、候補と採用版の区別、原文照合、独立検証をContextBase側で維持する。今回はGraphitiやgraph databaseを依存へ追加しない。

### 6. Letta：作業経験とソース知識を分ける

[MemFSの公式prompt](https://github.com/letta-ai/letta-code/blob/main/src/agent/prompts/letta_local_memfs.md)は、記憶をgit-backedなfilesystemへ投影し、簡潔な索引・行動規則と外部記憶を分ける。[Memory & dreaming](https://github.com/letta-ai/letta-docs-md/blob/main/configuration/memory/index.md)は、背景subagentが会話を振り返り、持続的な教訓を記憶へ反映する機構を説明する。

ContextBaseでは「どのtaskまで終えたか」「どの失敗を再試行するか」「何を直す必要があるか」という進行情報の参考になる。モデルの反省文から完了状態や原文Factを推測せず、実際のtask、候補、指摘、取得実績と照合する。MemFSのGit運用を、このリポジトリの中間物・テスト実行記録をGitへ追加する理由にはしない。

### 7. DeepSeek Harness：責務の配置を参考にする

[公式README](https://github.com/deepseek-ai/deepseek-harness)では、pluginを中心とした構成とCordisの利用が確認できる。developer previewで互換性を壊す変更があるとも記載される。ここではharnessの責務を明示する参考にとどめ、長期知識の正確性や効率を解決済みの製品として扱わない。

### ContextBaseへの反映範囲

次の区別を設計へ持ち込む。保存先の追加だけでこれらが実現したことにはしない。

1. **taskごとの参照範囲**：地図、関連record、必要な原文を選び、全履歴や無関係な候補を毎回複製しない。
2. **信頼状態**：構文Fact、未検証のseed・候補、独立検証、採用版を分ける。前の候補や指摘は調査材料として参照する。
3. **明示した変更**：固定した候補へ版拘束付き差分を適用し、未変更record・未知・根拠を保持する。指摘ごとの処置も別に確認する。
4. **現在の取証**：保存済み引用は原文を探す手掛かりとし、当該taskへ必要な行区間を実際に渡したことを記録する。
5. **再開と失効**：完了片、未完了の要求、失敗理由と再開条件を保存し、変更したsource・規則・前提へ旧合格を移さない。

候補の部分改訂の設計案は[ContextBase候補の部分改訂設計](ContextBase候補の部分改訂設計.md)へ集約する。この追補はその動機を示す参考資料であり、Interface、移行、試験、実モデルでの改善を実装済みとするものではない。OpenViking、Graphiti、Letta、DeepSeek Harnessの追加導入や互換性・性能保証は今回の対象に含めない。

共有するのは版・検索・取証・保存の仕組みであり、discovery、relationship、behaviorの独立起動と担当義務は維持する。共通知識層を3つのAgentを統括する親Agentへ置き換えない。

効果の確認では、同じsource・要求・モデル設定を用い、送信量、モデル往復、処理時間、修訂の保持範囲と独立検証の結果を比較する。外部製品の説明からContextBaseでの短縮率を約束しない。

## 設計・実装の正本

基本フロー・現行request上の全体義務・D03の段階境界は[段階的抽出・検証フロー](ContextBase段階的抽出・検証フロー.md)§18、今回の候補部分改訂は同§19と[追加設計](ContextBase候補の部分改訂設計.md)を参照する。既存実装の履歴は[実装計画](ContextBase実装計画.md)§12、今後の部分改訂工程・検査条件は同§13へ分離する。本ノートは参考調査資料であり、規範の別正本を作らない。

## 出典（一次資料）

1. Aider, “Repository map” — 地図の役割、token予算、依存グラフによる順位付け、原文追加の説明：<https://aider.chat/docs/repomap.html>
2. Aider source, `aider/repomap.py` — RepoMap、token上限、タグ順位付け・map生成の実装：<https://github.com/Aider-AI/aider/blob/main/aider/repomap.py>
3. Joern, “Code Property Graph” — attributed multigraph、共通IR、overlay、frontendの考え方：<https://docs.joern.io/code-property-graph/>
4. Joern, “Frontends” — 対応言語とfrontendごとの役割・成熟度：<https://docs.joern.io/frontends/>
5. Joern, “Calls” — call-siteをcallee関係と分けて探索するquery契約：<https://docs.joern.io/cpgql/calls/>
6. Joern, “Custom Data-Flow Semantics” — call解決不能時にmethod名が完全でないこと、曖昧な候補へregex semanticsを使う例：<https://docs.joern.io/dataflow-semantics/>
7. Egonex-AI, `understand-anything-plugin/skills/understand/SKILL.md` — scan、batch、merge、review、saveおよびincremental経路の手順：<https://github.com/Egonex-AI/Understand-Anything/blob/main/understand-anything-plugin/skills/understand/SKILL.md>
8. Egonex-AI, `understand-anything-plugin/skills/understand/merge-batch-graphs.py` — 実際の正規化・重複/参照処理を確認するための実装：<https://github.com/Egonex-AI/Understand-Anything/blob/main/understand-anything-plugin/skills/understand/merge-batch-graphs.py>
9. OpenViking, “Context Layers (L0/L1/L2)” — 要約による探索、原文のオンデマンド取得、freshnessの意味：<https://github.com/volcengine/OpenViking/blob/main/docs/en/concepts/03-context-layers.md>
10. Graphiti README — temporal context graph、episodeへの由来、利用側が用意する実行基盤：<https://github.com/getzep/graphiti>
11. Letta Code, `letta_local_memfs.md` — MemFS、簡潔な記憶と外部記憶、Gitによる記憶の履歴：<https://github.com/letta-ai/letta-code/blob/main/src/agent/prompts/letta_local_memfs.md>
12. Letta Docs, “Memory & dreaming” — 記憶の更新と背景subagentによるDreaming：<https://github.com/letta-ai/letta-docs-md/blob/main/configuration/memory/index.md>
13. DeepSeek Harness README — plugin中心の構成とdeveloper previewの状態：<https://github.com/deepseek-ai/deepseek-harness>

公開リポジトリのmainと外部ドキュメントは更新される。参照先は設計の着想を示し、ContextBaseで採用済みの契約・実装・性能保証を意味しない。
