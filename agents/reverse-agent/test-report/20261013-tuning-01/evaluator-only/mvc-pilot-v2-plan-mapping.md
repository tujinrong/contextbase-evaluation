# EVALUATOR_ONLY — ASP.NET pilot-v2計画の意味対応

評価者 `/root/evaluate_pilot`。AIの原計画27文書を、原評価セット31文書へ意味・責務で対応付けた。字面・文書IDの完全一致は要求しない。この対応は原稿の記載を審査した結果ではなく、計画上の候補であり、得点は付与していない。

**原31文書、1118行（加点932行・診断186行）、満点1408点、95%の最低1338点を維持する。** 欠落候補の削除、分母の縮小、元配点の変更は行っていない。期待本文・この対応表・評価snapshotはwriterの入力へ渡さない。

## 計画から分かること

検索・登録の基本/詳細2組と物理DB7表には、直接対応する責務がある。共通処理は状態、正規化/日付、候補、HTTP、トランザクション/監査へ組み替えられており、元文書数との単純比較では欠落を判断できない。各元評価行の対象・条件・属性一式を凍結原稿で照合する。

論理データ文書の主な責務はDTO・フォーム/DB/表示の移送契約である。これは基本の論理テーブル分冊とは別であり、論理テーブル5文書と論理索引を計画済みとは扱わない。物理DBテーブルの存在だけで、基本の業務型・業務長・処理初期値を再現したことにもならない。1表1文書は汎用の文書規則として改善できる。

共通UI、チェック/メッセージ、項目制約、業務コード、項目長の定義には、関連する責務の候補がある。一方、全対象・全属性を漏れなく一覧化する責務は明示されていない。初期値の説明や項目名の列挙だけでは1点属性行の全条件一致を判定しない。

設計判断・資料採用・受入の責務には、明確な納品仕様候補がない。analysis-reportを納品仕様へ混ぜたり、コードから観測できない選定日・改訂履歴・承認を生成したりしない。報告として不足を正確に説明することと、正式な再現採点の充足は別である。

## 原31文書への候補対応

主候補に加えて補助候補と理由を[JSON](mvc-pilot-v2-plan-mapping.json)へ記録した。主候補が複数でも原文書の点は一度だけ集計し、原稿が不足した場合に別文書の見出しだけで加点しない。

| 原評価文書ID | AI計画の主候補 | 計画判定 | 原行数 / 原満点 |
| --- | --- | --- | --- |
| DBDEF-SQLSERVER | SM-DB-INDEX | DIRECT_FAMILY_CANDIDATE | 32 / 29 |
| COM-STU-001 | SM-BAS-SYSTEM | DIRECT_FAMILY_CANDIDATE | 6 / 18 |
| COM-STU-002 | SM-DEP-PROCESS、SM-COM-TRANSACTION-AUDIT、SM-COM-RUNTIME-STATE | SPLIT_FAMILY_CANDIDATE | 3 / 9 |
| COM-STU-003 | SM-COM-RUNTIME-STATE、SM-COM-NORMALIZATION-DATE、SM-COM-TRANSACTION-AUDIT | SPLIT_FAMILY_CANDIDATE | 7 / 21 |
| COM-STU-004 | SM-BAS-STUDENT-SEARCH、SM-BAS-STUDENT-EDITOR | PARTIAL_PLAN_COVERAGE | 13 / 23 |
| COM-STU-005 | SM-COM-NORMALIZATION-DATE、SM-COM-HTTP-SECURITY | PARTIAL_PLAN_COVERAGE | 94 / 98 |
| COM-STU-006 | 未計画 | NO_DELIVERY_SPEC_CANDIDATE | 5 / 15 |
| COM-STU-007 | SM-COM-NORMALIZATION-DATE | DIRECT_FAMILY_CANDIDATE | 7 / 21 |
| COM-STU-008 | SM-COM-TRANSACTION-AUDIT、SM-DET-STUDENT-SEARCH、SM-DET-STUDENT-EDITOR | SPLIT_FAMILY_CANDIDATE | 17 / 27 |
| COM-STU-009 | SM-DATA-LOGICAL-CONTRACTS、SM-COM-NORMALIZATION-DATE | PARTIAL_PLAN_COVERAGE | 69 / 73 |
| COM-STU-010 | SM-COM-LOOKUPS、SM-DB-M-CODE、SM-DB-M-CODE-CATEGORY | PARTIAL_PLAN_COVERAGE | 78 / 84 |
| COM-STU-011 | SM-COM-NORMALIZATION-DATE | PARTIAL_PLAN_COVERAGE | 16 / 22 |
| COM-CSharp_ASPNET | SM-COM-HTTP-SECURITY、SM-DEP-PROCESS、SM-COM-TRANSACTION-AUDIT、SM-COM-RUNTIME-STATE | SPLIT_FAMILY_CANDIDATE | 4 / 12 |
| BAS-STU-01 | SM-BAS-STUDENT-SEARCH | DIRECT_FAMILY_CANDIDATE | 80 / 147 |
| BAS-STU-02 | SM-BAS-STUDENT-EDITOR | DIRECT_FAMILY_CANDIDATE | 113 / 169 |
| BAS-STU-03 | 未計画 | NO_LOGICAL_TABLE_INDEX_CANDIDATE | 8 / 9 |
| BAS-STU-04 | SM-BAS-CODE-MAINTENANCE | PARTIAL_PLAN_COVERAGE | 78 / 84 |
| DET-CSharp_ASPNET-SCR-STU-001 | SM-DET-STUDENT-SEARCH | DIRECT_FAMILY_CANDIDATE | 120 / 147 |
| DET-CSharp_ASPNET-SCR-STU-002 | SM-DET-STUDENT-EDITOR | DIRECT_FAMILY_CANDIDATE | 161 / 169 |
| DBDEF-SQLSERVER-M_STUDENT | SM-DB-M-STUDENT | DIRECT_TABLE_CANDIDATE | 36 / 38 |
| DBDEF-SQLSERVER-M_CLASS | SM-DB-M-CLASS | DIRECT_TABLE_CANDIDATE | 18 / 20 |
| DBDEF-SQLSERVER-M_CODE_CATEGORY | SM-DB-M-CODE-CATEGORY | DIRECT_TABLE_CANDIDATE | 12 / 14 |
| DBDEF-SQLSERVER-M_CODE | SM-DB-M-CODE | DIRECT_TABLE_CANDIDATE | 15 / 17 |
| DBDEF-SQLSERVER-T_OPERATION_LOG | SM-DB-T-OPERATION-LOG | DIRECT_TABLE_CANDIDATE | 13 / 15 |
| DBDEF-SQLSERVER-T_CONFIRMATION | SM-DB-T-CONFIRMATION | DIRECT_TABLE_CANDIDATE | 10 / 12 |
| DBDEF-SQLSERVER-T_RUNTIME_STATE | SM-DB-T-RUNTIME-STATE | DIRECT_TABLE_CANDIDATE | 9 / 11 |
| BAS-STU-03-M_STUDENT | 未計画 | NO_LOGICAL_TABLE_DOCUMENT_CANDIDATE | 36 / 38 |
| BAS-STU-03-M_CLASS | 未計画 | NO_LOGICAL_TABLE_DOCUMENT_CANDIDATE | 18 / 20 |
| BAS-STU-03-M_CODE_CATEGORY | 未計画 | NO_LOGICAL_TABLE_DOCUMENT_CANDIDATE | 12 / 14 |
| BAS-STU-03-M_CODE | 未計画 | NO_LOGICAL_TABLE_DOCUMENT_CANDIDATE | 15 / 17 |
| BAS-STU-03-T_OPERATION_LOG | 未計画 | NO_LOGICAL_TABLE_DOCUMENT_CANDIDATE | 13 / 15 |

## 保留と採点軸

以前に審査された4行の保留を継承するが、旧結果を新原稿の評価として流用しない。3行はソースだけでは観測できない設計資料/履歴成分、1行は重要な設計意図と実装対応の差分である。

原仕様の意味再現、現在ソースへの忠実度、実装に関する保証の主張を分けて採点する。設計意図と実装差分を明示したこと自体をAIのcritical矛盾と判定しない。根拠なしに実装が保証を満たすと断定した場合はcriticalになり得る。原稿到着後に、意図の全条件が再現されたか、観測結果を偽装していないかを個別に審査する。

観測不能を理由に原3点を除外しない。原仕様自身の矛盾、入力不足による観測不能、生成器の欠落は別の状態で記録する。正式点・率は現時点でnull、95%達成の判定は未実施である。

## 入出力の固定と検査範囲

原評価MD73個の版/SHA、現在の採点対象仕様31文書の版/SHA、source43ファイルのSHA、訓練参考11ファイルのSHA、AI原計画とmanifestのSHAをJSONへ保存し、現在のバイトと照合した。訓練入力はtraining-assistedであり、source-only baselineの得点へ転記しない。旧schema1 snapshotは開始時のsealではなく、現在の対応が検証された範囲として記録する。

元test-project1のsource/spec/spec-evalは変更していない。未実施は生成MDの意味採点、実機SQL/HTTP/UI試験、他方式採点、95%認定である。
