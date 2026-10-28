<!-- spec-meta: {"schema":"spec-md/1.0","documentId":"REPO-AGENTS","version":"7.6","path":"AGENTS.md","sheets":[{"heading":"対象","kind":"GRID","sheet":"01_対象"},{"heading":"配置","kind":"GRID","sheet":"02_配置"},{"heading":"完了","kind":"GRID","sheet":"03_完了"}]} -->
# 作業Agent向けルーティング

版7.6／2026-10-28。Agent定義をbuilds・converts・reverses・designsへ分類。明示指定projectの基本設計工程を追加。確定済み前提を次回の仕様生成へ継承し、最終結果と作業用出力を分離してGitで履歴を管理する。

## 対象

まずdocsの全体規則とagentsの役割定義を読む。実行要求でprojectIdと工程を確定し、選択projectだけを対象とする。方式ごとにspecRoot=対象project/spec/方式ID、sourceRoot=対象project/srcs/方式IDを分けて固定する。逆生成の評価実行では対象project/spec/全体とspec-evalへの読取りを許可しない。

仕様生成では、選択specRootに記録された利用者の確定前提、採用プロファイル、QAの決定を先に読み、根拠文書の版・ハッシュ・適用範囲を実行条件へ固定する。確定済みの回答は次回も継承し、変更指示や新たな矛盾がなければ再質問したり未決へ戻したりしない。方式固有の前提を他方式へ自動展開しない。実装・検査の実施状態は前提規則と分け、対象版の実行記録で確認する。

## 配置

sample-project1（旧test-project1）はフル方式パターンで、登録方式の将来拡張を許容する。sample-project2はAccess・CSharp_ASPNETの2方式パターン。対象方式は各projectの索引で確定し、project名から業務や認証を推測して展開しない。

Agent定義はagents/builds/（仕様からの実装）、agents/converts/（移行・変換）、agents/reverses/（コード解析）、agents/designs/（仕様・基本設計）へ分ける。解析用の共有runtimeはagents/reverses/shared/contextbase-runtime/へ置く。全体の変更はdocs/agents、題材の仕様索引は対象project/spec/README.md、独立方式の原仕様正本は対象project/spec/方式ID/、ソース正本は対象project/srcs/方式ID/、評価は対象project/spec-eval/へ隔離する。順生成は選択方式のspecRootを入力とし、sourceRootへ生成する。旧srcs/方式ID/specへの自動復帰や共用仕様の強制は行わない。未指定のprojectや方式を自動作成しない。実装やDB実行を指示されていない段階では設計更新だけを行う。重複は許容、矛盾は修正。

全方式共通で、最終ソースはsourceRootの正本を更新し、最終配布物・今回の最終検査記録・入出力manifestはsourceRoot/build/の固定パスへ更新する。生成日・実行ID・attempt別の過去成果、backup、archiveを累積しない。履歴はGitを使用する。中間生成・失敗試行・コンパイル途中・隔離展開・キャッシュはsourceRoot/.tmp/で処理し、.tmp/はGit管理しない。方式に属さない共通工程だけは担当Agentまたはprojectの.tmp/とbuild/を使う。入力・QA・正式な試験コード・fixtureは中間生成物として削除しない。

## 完了

入力/出力の版・ファイル・検査範囲・未実施を明示する。過去のレポートの合格を新改訂の検査結果として流用しない。
