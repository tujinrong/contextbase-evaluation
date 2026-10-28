<!-- spec-meta: {"schema":"spec-md/1.0","documentId":"SP2-REQUIREMENT-RUN","version":"1.0","path":"sample-project2/build/requirement-definition/report.md","sheets":[{"heading":"成果物と範囲","kind":"GRID","sheet":"01_成果物と範囲"},{"heading":"検査と保全","kind":"GRID","sheet":"02_検査と保全"},{"heading":"判断と未実施","kind":"GRID","sheet":"03_判断と未実施"}]} -->
# sample-project2 要件定義書の仕様逆生成

版1.0／2026-10-28。stage=requirement-definition、generationMode=spec-to-requirements、AG-REQUIREMENT 0.2。

## 成果物と範囲

Access・CSharp_ASPNETの2方式の直下に要件定義書.md 1.0を作成した。目的/範囲、利用者/権限、機能/データ/非機能、受入条件、QA、根拠を各方式内で独立して整理した。方式/全体の索引とproject案内・現在工程、リポジトリ全体案内の工程表示を同期した。

| 方式 | 要件定義書 | 要件数 | 受入条件数 | QA/引継ぎ数 | 文書検査 |
| --- | --- | --- | --- | --- | --- |
| Access | [1.0](../../spec/Access/要件定義書.md) | 35 | 26 | 15 | PASS |
| CSharp_ASPNET | [1.0](../../spec/CSharp_ASPNET/要件定義書.md) | 41 | 30 | 7 | PASS |

既存基本設計が入力であり、sample-project1の業務・認証・評価・実装を転用していない。要件定義Agentの仕様逆生成機能を使用し、汎用Agent定義自体の改訂は行わない。

## 検査と保全

全76要件へ受入条件を対応し、56条件の実施状態をすべて未実施と記録した。方式別根拠36文書のID・版・SHA-256、リンク、LIST/spec-meta、要件/QA対応を今回の実ファイルで検査しPASS。作成担当とは別の/root/req_desktopが原文へ照合して独立レビューし、最終版の対象ハッシュを記録した。

開始時のspec内51 Markdown中、48既存仕様はハッシュ一致で保全。既存変更は方式README2件と配置索引1件、新規業務文書は要件定義書2件だけ。project直下のREADMEとプロジェクト情報は入口/工程案内を局所更新した。元の基本・共通・QA・既存検査記録、正式試験コード・fixtureを変更していない。

[manifest](manifest.json)へ入力/出力の版・ファイル・ハッシュと方式別記録を保存し、[検査記録](validation.json)へ範囲・独立レビュー・未実施を固定した。方式別は各sourceRoot/build/spec-generation/requirement-definition/で、以前の基本設計build記録は上書きしていない。

## 判断と未実施

6機能という利用者確定と、5画面/5表・ADMIN/STAFF・200社員/20経歴・2シート・10秒排他等の設計採用を区別した。認証あり、社員削除なし、経歴の明示除去を全体保存、固定時点からの帳票全量取得、生成後の再認可、Access保存とWebダウンロードの差を継承した。SP2-DEMO-01の定義済み初期データを未確定へ戻していない。

具体的な暗号API/初期設定、物理型/排他手段、Excel生成/長文継続/印刷実測、実機DPI/IME/競合/性能/回復は既存の詳細工程残件として保持した。利用者承認、基本/詳細設計改訂、アプリ、実DB、実Excel帳票・印刷、実機/性能/受入試験、仕様書のExcel/PDF変換、正式採点は未実施。formalScore=null。
