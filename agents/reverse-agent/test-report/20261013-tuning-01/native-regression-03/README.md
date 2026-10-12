# 汎用経路の局所修正と回帰確認

2026-10-13。現reverse-agentのPython共通経路だけを修正した。新AI driver／CLIは親Agentの所有で、この変更はAIによる解析・執筆を実装したものではない。人工fixtureによる回帰だけを行い、nenkin／n2framework原本やtest-project1のソース／原仕様／spec-evalは変更・実行・テスト入力への読取りを行っていない。

変更したproductionは detail/semantics.py、detail/core.py、detail/event_templates.py の3ファイル。新規テストは src/contextbase/tests/test_generic_provenance.py である。

| 変更 | 動作と検査 |
| --- | --- |
| 用語辞書の採用 | schema=contextbase.terminology.v1、trust=repository-reviewed、project_id、input_root、source_hashesの全原本スナップショット一致を必須にした。同名型・同名フォルダーだけでは別案件の名称を採用しない。未固定旧辞書は保存したまま不採用理由を記録する。既存QA回答は変更しない。矛盾する一致辞書はエラーとする。 |
| P2辞書経路 | type/field辞書を1回ずつ上記契約で読む。coreから未固定load_namesを再投入せず、原文UI項目のfield_labelsは保持する。 |
| セッション名称 | 任意Sessionを「職員情報等」と断定せず「セッション保持情報」とする。kind・CRUD・guards・行根拠は保持した。 |
| セッション確認 | method本文にsession参照があるだけでログイン済み職員を断定しない。「セッション情報の確認結果」を中立に説明し、肯定・否定の条件を保つ。 |
| 文字列保持 | explainの日本語置換・空白整形から文字列リテラルを保護し、700文字の切捨てを解除した。長い原値・全半角空白・true/null/演算子・先頭ゼロを保持する。 |

新しい人工fixture17件は、案件／入力／hash不一致、同名型別業務、部分snapshot、未レビュー／不正値／衝突、QA不変、セッション断定、分岐の正負、return内の委譲呼出先解決、4,000文字を超える引数原文保持、説明文の長いリテラルと空白の非損失を検査する。return内委譲は既存SemanticIndex.traceの到達を実検査した。入力コードを実行して意味を取得していない。

重点試験は [前工程focused.raw.log](../native-regression-01/focused.raw.log) に30件PASS。新規17件と既存predicate／procedure13件を含む。続いて既存specgen／contextbase／docsiteを既存のunittest方式で読み、Graphviz依存の統合グループを除外して回帰した。[生ログ](unittest.raw.log)、[JSON](results.json)。293件実行、280PASS、13SKIP、失敗0、エラー0。Graphviz未導入による57件は未実行であり、完全suite合格とは扱わない。

13SKIPの理由と57未実行の個別IDはJSONに保存した。PDF追加依存、旧Pilot原本未配置、symlink可否などをPASSへ置換していない。図を偽生成したりdotをmockして合格させたりしていない。P3原本非依存の図込み統合、実AI呼出・日本語原稿品質、現業務原本全量の逆生成、HTMLブラウザー目視、PDF実生成は本局所修正工程では未実施である。

一時材料は reverse-agent/.tmp/native-tests 配下。Python3.11.9と、同範囲への --no-user --target 依存を使用した。元Python／OS／globaldocs／他repositoryを変更していない。準備時の既定pip --userと--targetの競合はログを保持し、--no-userで解消した。namespace testsにtop_level_dirを明示した準備失敗は [native-regression-02](../native-regression-02/preflight-failure.json) へ保存し、別IDの本結果で隠していない。

既存genericに残る制限: foundationの用語／feature overrideが全src-dynamicから候補を読む経路、既存キーワードによる文章解釈、csharp_flowの表示expression上限、現global様式との不整合は本3ファイルの変更だけでは解消していない。全案件汎用性・全言語完全解析・AI執筆成功を保証する結果ではない。新AI経路の source capsule と独立レビューは別工程で検査する。
