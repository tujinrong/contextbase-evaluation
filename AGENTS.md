<!-- spec-meta: {"schema":"spec-md/1.0","documentId":"REPO-AGENTS","version":"7.11","path":"AGENTS.md","sheets":[{"heading":"対象","kind":"GRID","sheet":"01_対象"},{"heading":"配置","kind":"GRID","sheet":"02_配置"},{"heading":"完了","kind":"GRID","sheet":"03_完了"}]} -->
# 作業Agent向けルーティング

版7.11／2026-10-29。要件定義・基本設計・詳細設計の3担当へ整理し、旧汎用仕様Agentを廃止する。入力隔離・確定前提の継承と固定出力の運用を維持する。仕様書から要件への逆生成はrequirement-agentの担当とし、コードからの逆仕様評価とは入力契約を区別する。

## 対象

まずdocsの全体規則とagentsの役割定義を読む。実行要求でprojectIdと工程を確定し、選択projectだけを対象とする。方式ごとにspecRoot=対象project/spec/方式ID、sourceRoot=対象project/srcs/方式IDを分けて固定する。逆生成の評価実行では対象project/spec/全体とspec-evalへの読取りを許可しない。

仕様生成では、選択specRootに記録された利用者の確定前提、採用プロファイル、QAの決定を先に読み、根拠文書の版・ハッシュ・適用範囲を実行条件へ固定する。確定済みの回答は次回も継承し、変更指示や新たな矛盾がなければ再質問したり未決へ戻したりしない。方式固有の前提を他方式へ自動展開しない。実装・検査の実施状態は前提規則と分け、対象版の実行記録で確認する。

## 配置

設計工程は要件定義・基本設計・詳細設計の3担当へ分ける。[requirement-agent](agents/designs/requirement-agent/AGENT.md)は要件定義専用（0.4、既存仕様からの逆生成を含む）、[basic-design-agent](agents/designs/basic-design-agent/AGENT.md)は基本設計専用、[detail-design-agent](agents/designs/detail-design-agent/AGENT.md)は詳細仕様書専用とする。旧spec-agentは廃止し、同フォルダと互換入口を残さない。複合依頼は要求・確定前提・QA・各IDを担当工程へ引き継ぎ、依頼されていない後工程を自動開始しない。

基本設計の新規作成・改善・レビューは[基本設計専用Agent](agents/designs/basic-design-agent/AGENT.md)が担当する。基本設計専用のルールは同Agentの[rules/](agents/designs/basic-design-agent/rules/基本設計書作成ルール.md)、処理手順は[workflows/](agents/designs/basic-design-agent/workflows/基本設計.md)を正本とし、共通docsや他Agentへ別正本を保存しない。業務仕様と既存の採用済み規約・QAは対象specRootに保持する。

sample-project1（旧test-project1）はフル方式パターンで、登録方式の将来拡張を許容する。sample-project2はAccess・CSharp_ASPNETの2方式パターン。対象方式は各projectの索引で確定し、project名から業務や認証を推測して展開しない。

Agent定義はagents/builds/（仕様からの実装）、agents/converts/（移行・変換）、agents/reverses/（コード解析）、agents/designs/（要件定義・基本設計・詳細設計）へ分ける。解析用の共有runtimeはagents/reverses/shared/contextbase-runtime/へ置く。全体の変更はdocs/agents、題材の仕様索引は対象project/spec/README.md、独立方式の原仕様正本は対象project/spec/方式ID/、ソース正本は対象project/srcs/方式ID/、評価は対象project/spec-eval/へ隔離する。順生成は選択方式のspecRootを入力とし、sourceRootへ生成する。旧srcs/方式ID/specへの自動復帰や共用仕様の強制は行わない。未指定のprojectや方式を自動作成しない。実装やDB実行を指示されていない段階では設計更新だけを行う。重複は許容、矛盾は修正。

全方式共通で、最終ソースはsourceRootの正本を更新し、最終配布物・今回の最終検査記録・入出力manifestはsourceRoot/build/の固定パスへ更新する。生成日・実行ID・attempt別の過去成果、backup、archiveを累積しない。履歴はGitを使用する。中間生成・失敗試行・コンパイル途中・隔離展開・キャッシュはsourceRoot/.tmp/で処理し、.tmp/はGit管理しない。方式に属さない共通工程だけは担当Agentまたはprojectの.tmp/とbuild/を使う。入力・QA・正式な試験コード・fixtureは中間生成物として削除しない。

UIは[UIパターン規約](docs/UIパターン規約.md)と[WEB](docs/WEB画面品質規約.md)・[WinForms](docs/WinForms画面品質規約.md)・[Text](docs/Text画面品質規約.md)の3系統を採用する。配置のscreenFamilyと実装のrendererを分け、WPFはWEB系でもXAML/DIP・ネイティブ操作を維持する。要件→基本→詳細→実装で用途パターン・状態・個別合格条件・根拠を引き継ぎ、該当方式の規約を入力凍結する。WebのCSS/URL/ページングをWinForms/Textへ強制しない。

Accessの画面品質はWinForms系の下で[工程横断規約](docs/Access画面品質規約.md)を併用し、合理性・統一性・見やすさ・操作性の条件を要件→基本→詳細→実装/実画面検査へ引き継ぐ。専用の文書形式・手順は各Agentの正本に保持し、画面タイプや保存方式を一律化しない。Agent改善だけの依頼では既存仕様・アプリを自動再生成しない。

## 完了

入力/出力の版・ファイル・検査範囲・未実施を明示する。過去のレポートの合格を新改訂の検査結果として流用しない。
