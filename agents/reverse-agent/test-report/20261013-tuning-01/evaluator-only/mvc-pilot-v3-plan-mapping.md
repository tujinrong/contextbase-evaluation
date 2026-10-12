# EVALUATOR_ONLY — ASP.NET pilot-v3計画の意味対応

評価者 `/root/evaluate_pilot`。AI計画35文書（納品候補33・分析報告2）を責務・意味で確認した。旧IDは維持されているが、literalなID/path一致を合格条件にはしていない。これは本文生成前の対応候補であり、正式得点・率はnullである。

**原31文書・1118行（加点932、診断186）・1408点・95%最低1338点を維持する。** 新規の技術論理表や保守機能を母数へ追加せず、未計画の原成分も母数から除外しない。期待本文と本表はwriter入力へ渡さない。

## v3で変わった責務

論理表7文書がDTO/移送契約から分離された。原評価対象の基本論理表5文書には、独立した直接候補ができた。追加された技術論理表2文書は、新しい理解材料として扱い原評価の配点を増やさない。物理表7文書は別に維持され、業務型/上限/処理設定値と実DB型/容量/DEFAULTを区別する責務が明示されている。

共通UIの配置・表示・ブラウザー操作が独立した契約になった。初期コードの意味・順序・保護は論理表と基本コード保守にも明示されたため、共通UI・共通業務コード・基本コード設計は直接候補へ更新した。いずれも全属性が実原稿に書かれたことをまだ示していない。

索引は論理/物理の独立表へのリンクと業務/技術情報の区別を担当する。DTO契約と文書群で論理索引の意味へ対応できる候補になったため、v2の「候補なし」から分割候補へ変更した。単一の論理索引ファイル名を要求する判断は行わない。

チェック/メッセージの完全一覧、全フォーム項目の属性一覧、項目長の設計根拠は引続き本文での確認が必要である。設計判断・資料採用・履歴/受入を担う納品仕様は未計画。コードだけで観測不能な来歴を補うことは要求しないが、その不足を勝手な項目除外や点率の完成へ読み替えない。

分析報告2文書は納品batchから除外されている。報告の生成が必要ならreverse-agentのtest-reportへ別成果物として保存し、未完成報告を納品仕様へ混ぜない。

## 固定31文書への候補対応

補助候補・理由・原版/SHA・計画SHAは[JSON](mvc-pilot-v3-plan-mapping.json)に保存した。主候補が分割/統合されても元評価行の対象・条件・属性一式を照合し、原文書の点は一度だけ数える。

| 原評価文書ID | v3の主候補 | 計画判定 | 原行数 / 原満点 |
| --- | --- | --- | --- |
| DBDEF-SQLSERVER | SM-DB-INDEX | DIRECT_FAMILY_CANDIDATE | 32 / 29 |
| COM-STU-001 | SM-BAS-SYSTEM | DIRECT_FAMILY_CANDIDATE | 6 / 18 |
| COM-STU-002 | SM-DEP-PROCESS、SM-COM-TRANSACTION-AUDIT、SM-COM-RUNTIME-STATE | SPLIT_FAMILY_CANDIDATE | 3 / 9 |
| COM-STU-003 | SM-COM-RUNTIME-STATE、SM-COM-NORMALIZATION-DATE、SM-COM-TRANSACTION-AUDIT | SPLIT_FAMILY_CANDIDATE | 7 / 21 |
| COM-STU-004 | SM-COM-UI-PRESENTATION | DIRECT_FAMILY_CANDIDATE | 13 / 23 |
| COM-STU-005 | SM-COM-NORMALIZATION-DATE、SM-COM-HTTP-SECURITY | PARTIAL_PLAN_COVERAGE | 94 / 98 |
| COM-STU-006 | 未計画 | NO_DELIVERY_SPEC_CANDIDATE | 5 / 15 |
| COM-STU-007 | SM-COM-NORMALIZATION-DATE | DIRECT_FAMILY_CANDIDATE | 7 / 21 |
| COM-STU-008 | SM-COM-TRANSACTION-AUDIT、SM-DET-STUDENT-SEARCH、SM-DET-STUDENT-EDITOR | SPLIT_FAMILY_CANDIDATE | 17 / 27 |
| COM-STU-009 | SM-DATA-LOGICAL-CONTRACTS、SM-COM-NORMALIZATION-DATE | PARTIAL_PLAN_COVERAGE | 69 / 73 |
| COM-STU-010 | SM-DATA-M-CODE、SM-BAS-CODE-MAINTENANCE | DIRECT_FAMILY_CANDIDATE | 78 / 84 |
| COM-STU-011 | SM-COM-NORMALIZATION-DATE | PARTIAL_PLAN_COVERAGE | 16 / 22 |
| COM-CSharp_ASPNET | SM-COM-HTTP-SECURITY、SM-DEP-PROCESS、SM-COM-TRANSACTION-AUDIT、SM-COM-RUNTIME-STATE | SPLIT_FAMILY_CANDIDATE | 4 / 12 |
| BAS-STU-01 | SM-BAS-STUDENT-SEARCH | DIRECT_FAMILY_CANDIDATE | 80 / 147 |
| BAS-STU-02 | SM-BAS-STUDENT-EDITOR | DIRECT_FAMILY_CANDIDATE | 113 / 169 |
| BAS-STU-03 | SM-DB-INDEX、SM-DATA-LOGICAL-CONTRACTS | SPLIT_FAMILY_CANDIDATE | 8 / 9 |
| BAS-STU-04 | SM-BAS-CODE-MAINTENANCE、SM-DATA-M-CODE | DIRECT_FAMILY_CANDIDATE | 78 / 84 |
| DET-CSharp_ASPNET-SCR-STU-001 | SM-DET-STUDENT-SEARCH | DIRECT_FAMILY_CANDIDATE | 120 / 147 |
| DET-CSharp_ASPNET-SCR-STU-002 | SM-DET-STUDENT-EDITOR | DIRECT_FAMILY_CANDIDATE | 161 / 169 |
| DBDEF-SQLSERVER-M_STUDENT | SM-DB-M-STUDENT | DIRECT_TABLE_CANDIDATE | 36 / 38 |
| DBDEF-SQLSERVER-M_CLASS | SM-DB-M-CLASS | DIRECT_TABLE_CANDIDATE | 18 / 20 |
| DBDEF-SQLSERVER-M_CODE_CATEGORY | SM-DB-M-CODE-CATEGORY | DIRECT_TABLE_CANDIDATE | 12 / 14 |
| DBDEF-SQLSERVER-M_CODE | SM-DB-M-CODE | DIRECT_TABLE_CANDIDATE | 15 / 17 |
| DBDEF-SQLSERVER-T_OPERATION_LOG | SM-DB-T-OPERATION-LOG | DIRECT_TABLE_CANDIDATE | 13 / 15 |
| DBDEF-SQLSERVER-T_CONFIRMATION | SM-DB-T-CONFIRMATION | DIRECT_TABLE_CANDIDATE | 10 / 12 |
| DBDEF-SQLSERVER-T_RUNTIME_STATE | SM-DB-T-RUNTIME-STATE | DIRECT_TABLE_CANDIDATE | 9 / 11 |
| BAS-STU-03-M_STUDENT | SM-DATA-M-STUDENT | DIRECT_LOGICAL_TABLE_CANDIDATE | 36 / 38 |
| BAS-STU-03-M_CLASS | SM-DATA-M-CLASS | DIRECT_LOGICAL_TABLE_CANDIDATE | 18 / 20 |
| BAS-STU-03-M_CODE_CATEGORY | SM-DATA-M-CODE-CATEGORY | DIRECT_LOGICAL_TABLE_CANDIDATE | 12 / 14 |
| BAS-STU-03-M_CODE | SM-DATA-M-CODE | DIRECT_LOGICAL_TABLE_CANDIDATE | 15 / 17 |
| BAS-STU-03-T_OPERATION_LOG | SM-DATA-T-OPERATION-LOG | DIRECT_LOGICAL_TABLE_CANDIDATE | 13 / 15 |

## 固定した証拠と未実施

v3 plan-verifiedとplan-handoffのSHAを新たに記録し、同一jobの前後snapshot検証がある範囲として扱った。source-only baselineへ転記しない。原評価73、現行原仕様31、source43、訓練参考11のSHAは今回再度すべて一致した。旧mappingを新原稿の検証済み結果として流用せず、旧ファイルも変更していない。

既存の保留4行（観測不能な設計資料/履歴成分3、重要な設計意図・実装対応の差分1）は未裁定で保持する。意図の意味再現とソース忠実度を分け、差分の正確な記述自体をAIのcritical矛盾と決め付けない。根拠なしの実装保証は別にcritical評価する。

未実施は、生成MDの意味採点、実機SQL/HTTP/UI試験、元source/spec/spec-evalの修正、他方式採点、95%資格判定である。現在の状態は本文凍結待ちである。
