<!-- spec-meta: {"schema":"spec-md/1.0","documentId":"AG-BASIC-DESIGN-RULE-CONSOLIDATION","version":"1.0","path":"agents/designs/basic-design-agent/build/rule-consolidation/report.md","sheets":[{"heading":"対象と配置","kind":"GRID","sheet":"01_対象と配置"},{"heading":"検査結果","kind":"GRID","sheet":"02_検査結果"},{"heading":"適用範囲と未実施","kind":"GRID","sheet":"03_適用範囲と未実施"}]} -->
# 基本設計専用ルール・処理の集約記録

版1.0／2026-10-28。基本設計専用Agentの定義版1.7と、専用規則・工程版1.0を配置した。

## 対象と配置

利用者の指定により、基本設計の新規作成・改善・レビューと、それに必要な執筆・検査・描画・記録の専用定義をbasic-design-agentへ集約した。

- [専用ルール](../../rules/基本設計書作成ルール.md)：11列、空欄/-/〇、条件必須、備考、論理DB対応、検索ER、DB更新、階層化、整合性、MSGと復帰、Pilot。
- [処理手順](../../workflows/基本設計.md)：入力・確定前提の固定、作成・改善、構造/意味/描画確認、固定記録、引継ぎ。
- [Agent契約](../../AGENT.md)・[起動指示](../../PROMPT.md)・[運用案内](../../README.md)：基本設計専用の範囲と正本を参照。

docs/仕様書作成ルール.mdとdocs/MD構造・Excel変換規約.mdから基本設計専用本文を移動し、共通docsは専用正本への参照へ変更した。共通のMD/Excel・TABLE・画面分類・配置規約は元の責務で維持する。spec-agentは基本設計部分を専用契約へ引き継ぐ。別Agentの起動や別チャットへの送信は必須にしない。

## 検査結果

対象13文書のmetadata.path、本文版、H2/sheets、LISTの矩形・キー、相対リンク91件、専用ルールの保全観点と移動元の実行手順の保全を確認し、PASSだった。独立レビューは同じ13文書のSHA-256を対象としてPASS。git diff --checkもPASS。

sample-project1とsample-project2には今回の差分がない。過去の検査・生成記録、採用済み規約版と入力ハッシュ、原入力・QA・正式fixtureを維持した。根拠の移動元ハッシュ、入力commit、対象の版と出力SHA-256、独立レビューはmanifest.json・validation.json・review.jsonへ記録する。

## 適用範囲と未実施

今回は基本設計Agentのルール・処理・ルーティングの配置変更である。既存projectの採用済み規約や仕様書一式の更新、アプリ生成・ビルド、DB作成/実行、実Excel/印刷、受入試験、正式採点、Git commit/merge/pushは未実施。formalScore=null。

他フォルダに再利用可能な基本設計専用スクリプトの正本は見つからなかった。project固有の改名・固定方式/文書名・過去baselineに依存する一回用処理は中間物として元の.tmp/へ保持し、今回の共通処理正本へ昇格させていない。将来追加する再利用可能な基本設計専用の機械処理は当Agentのscripts/へ保存する。
