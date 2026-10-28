# ContextBase 調査フローに活かせる参考実装

調査日：2026-10-28
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

## 設計・実装の正本

参考から得た示唆を反映した採用案・現行request上の全体義務・D03の段階境界は[段階的抽出・検証フロー](ContextBase段階的抽出・検証フロー.md)§18を参照する。工程順、実装範囲、未実装事項と完了条件は[実装計画](ContextBase実装計画.md)§12を参照する。本ノートは外部実装の調査記録であり、第三の設計正本ではない。

## 出典（一次資料）

1. Aider, “Repository map” — 地図の役割、token予算、依存グラフによる順位付け、原文追加の説明：<https://aider.chat/docs/repomap.html>
2. Aider source, `aider/repomap.py` — RepoMap、token上限、タグ順位付け・map生成の実装：<https://github.com/Aider-AI/aider/blob/main/aider/repomap.py>
3. Joern, “Code Property Graph” — attributed multigraph、共通IR、overlay、frontendの考え方：<https://docs.joern.io/code-property-graph/>
4. Joern, “Frontends” — 対応言語とfrontendごとの役割・成熟度：<https://docs.joern.io/frontends/>
5. Joern, “Calls” — call-siteをcallee関係と分けて探索するquery契約：<https://docs.joern.io/cpgql/calls/>
6. Joern, “Custom Data-Flow Semantics” — call解決不能時にmethod名が完全でないこと、曖昧な候補へregex semanticsを使う例：<https://docs.joern.io/dataflow-semantics/>
7. Egonex-AI, `understand-anything-plugin/skills/understand/SKILL.md` — scan、batch、merge、review、saveおよびincremental経路の手順：<https://github.com/Egonex-AI/Understand-Anything/blob/main/understand-anything-plugin/skills/understand/SKILL.md>
8. Egonex-AI, `understand-anything-plugin/skills/understand/merge-batch-graphs.py` — 実際の正規化・重複/参照処理を確認するための実装：<https://github.com/Egonex-AI/Understand-Anything/blob/main/understand-anything-plugin/skills/understand/merge-batch-graphs.py>

公開リポジトリのmainと外部ドキュメントは更新される。参照先は設計の着想を示し、ContextBaseで採用済みの契約・実装・性能保証を意味しない。
