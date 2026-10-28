<!-- spec-meta: {"schema":"spec-md/1.0","documentId":"ACCESS-DESIGN-AGENT-GENERATION-CHECK","version":"1.0","path":"sample-project1/srcs/Access/build/spec-generation/design-generation-check/report.md","sheets":[{"heading":"確認条件","kind":"GRID","sheet":"01_確認条件"},{"heading":"ファイル照合一覧","kind":"LIST","sheet":"02_ファイル照合一覧","key":["No"]},{"heading":"検査結果","kind":"GRID","sheet":"03_検査結果"},{"heading":"未決・未実施","kind":"GRID","sheet":"04_未決と未実施"}]} -->
# Access 基本・詳細設計Agentの仕様書生成確認

版1.0／2026-10-28。最新Access一式44文書を漏れなく照合した採用前の試験生成記録。

## 確認条件

利用者指定によりsample-project1のAccessだけを対象に、AG-BASIC-DESIGN（生成準備時の契約1.8・規則1.0・工程1.1）で基本設計9文書、AG-DETAIL-DESIGN（生成準備時1.0）で詳細仕様2文書をAIが試験生成した。詳細は今回生成した基本の2機能版を入力に含め、同一の静的画面配置と項目/イベント/業務意味を引き継いだ。完了時点の契約は並行した要件Agent整備に伴う引継ぎ案内の更新で基本1.9・詳細1.1となったが、専用規則と処理手順は不変で、生成物への業務影響がないことを独立確認した。現在の定義版とハッシュはmanifest.jsonへ記録した。要件定義Agent0.2の実行確認は本記録に含めない。

入力正本はsample-project1/spec/Access/。出力は本記録のspec/Access/で、正式正本とは別のverification-draft・未採用版である。共通・DB定義・規約・索引等33文書は既存採用した支援文書として含め、今回AI生成した11文書と区別した。支援文書はメタ情報の実出力パス等以外の本文を保持し、参照する入力版・ハッシュを試験生成版の根拠へ偽装していない。

開始時は43入力だったが、作業中の正本更新で要件定義書1件と索引2件の改訂が入った。更新を上書きせず最新44入力へ再固定し、要件の確定区分/QA追跡の追記も確認した。既存11基本・詳細の元入力ハッシュと生成した基本9文書は変わらず、最終固定後の全44正本SHAを確認した。差分の根拠はinput-changes.jsonへ保存した。

## ファイル照合一覧

| No | 区分 | 処理 | 文書 | 文書ID | 入力版 | 出力版 | 結果 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | 支援文書 | 既存採用 | [DB定義/Access/01_DB定義書.md](spec/Access/DB定義/Access/01_DB定義書.md) | ACCESS-DBDEF-ACCESS | 8.5 | 8.5 | PASS |
| 2 | 支援文書 | 既存採用 | [DB定義/Access/テーブル/01_m_student.md](spec/Access/DB定義/Access/テーブル/01_m_student.md) | ACCESS-DBDEF-ACCESS-M_STUDENT | 8.1 | 8.1 | PASS |
| 3 | 支援文書 | 既存採用 | [DB定義/Access/テーブル/02_m_class.md](spec/Access/DB定義/Access/テーブル/02_m_class.md) | ACCESS-DBDEF-ACCESS-M_CLASS | 8.1 | 8.1 | PASS |
| 4 | 支援文書 | 既存採用 | [DB定義/Access/テーブル/03_m_code_category.md](spec/Access/DB定義/Access/テーブル/03_m_code_category.md) | ACCESS-DBDEF-ACCESS-M_CODE_CATEGORY | 8.1 | 8.1 | PASS |
| 5 | 支援文書 | 既存採用 | [DB定義/Access/テーブル/04_m_code.md](spec/Access/DB定義/Access/テーブル/04_m_code.md) | ACCESS-DBDEF-ACCESS-M_CODE | 8.1 | 8.1 | PASS |
| 6 | 支援文書 | 既存採用 | [DB定義/Access/テーブル/05_t_operation_log.md](spec/Access/DB定義/Access/テーブル/05_t_operation_log.md) | ACCESS-DBDEF-ACCESS-T_OPERATION_LOG | 8.1 | 8.1 | PASS |
| 7 | 支援文書 | 既存採用 | [DB定義/Access/テーブル/06_t_write_guard.md](spec/Access/DB定義/Access/テーブル/06_t_write_guard.md) | ACCESS-DBDEF-ACCESS-T_WRITE_GUARD | 8.1 | 8.1 | PASS |
| 8 | 支援文書 | 既存採用 | [README.md](spec/Access/README.md) | ACCESS-SPEC-INDEX | 8.7 | 8.7 | PASS |
| 9 | 支援文書 | 既存採用 | [プロジェクト情報.md](spec/Access/プロジェクト情報.md) | ACCESS-PROJECT | 8.6 | 8.6 | PASS |
| 10 | 支援文書 | 既存採用 | [共通/00_設計書一覧.md](spec/Access/共通/00_設計書一覧.md) | ACCESS-COM-STU-000 | 8.4 | 8.4 | PASS |
| 11 | 支援文書 | 既存採用 | [共通/01_システム概要.md](spec/Access/共通/01_システム概要.md) | ACCESS-COM-STU-001 | 8.3 | 8.3 | PASS |
| 12 | 支援文書 | 既存採用 | [共通/02_CRUD図.md](spec/Access/共通/02_CRUD図.md) | ACCESS-COM-STU-002 | 8.2 | 8.2 | PASS |
| 13 | 支援文書 | 既存採用 | [共通/03_共通モジュール設計.md](spec/Access/共通/03_共通モジュール設計.md) | ACCESS-COM-STU-003 | 8.3 | 8.3 | PASS |
| 14 | 支援文書 | 既存採用 | [共通/04_共通UI部品設計.md](spec/Access/共通/04_共通UI部品設計.md) | ACCESS-COM-STU-004 | 8.5 | 8.5 | PASS |
| 15 | 支援文書 | 既存採用 | [共通/05_チェック・メッセージ設計.md](spec/Access/共通/05_チェック・メッセージ設計.md) | ACCESS-COM-STU-005 | 8.4 | 8.4 | PASS |
| 16 | 支援文書 | 既存採用 | [共通/06_要件対応・設計判断.md](spec/Access/共通/06_要件対応・設計判断.md) | ACCESS-COM-STU-006 | 8.6 | 8.6 | PASS |
| 17 | 支援文書 | 既存採用 | [共通/07_日付・和暦仕様.md](spec/Access/共通/07_日付・和暦仕様.md) | ACCESS-COM-STU-007 | 8.2 | 8.2 | PASS |
| 18 | 支援文書 | 既存採用 | [共通/08_データアクセス仕様.md](spec/Access/共通/08_データアクセス仕様.md) | ACCESS-COM-STU-008 | 8.4 | 8.4 | PASS |
| 19 | 支援文書 | 既存採用 | [共通/09_項目制約定義.md](spec/Access/共通/09_項目制約定義.md) | ACCESS-COM-STU-009 | 8.4 | 8.4 | PASS |
| 20 | 支援文書 | 既存採用 | [共通/10_業務コード定義.md](spec/Access/共通/10_業務コード定義.md) | ACCESS-COM-STU-010 | 8.2 | 8.2 | PASS |
| 21 | 支援文書 | 既存採用 | [共通/11_項目長設計基準.md](spec/Access/共通/11_項目長設計基準.md) | ACCESS-COM-STU-011 | 8.1 | 8.1 | PASS |
| 22 | 支援文書 | 既存採用 | [共通/方式別/01_共通実装仕様.md](spec/Access/共通/方式別/01_共通実装仕様.md) | ACCESS-COM-Access | 8.6 | 8.6 | PASS |
| 23 | 基本設計 | 試験生成 | [基本設計書/01_学生検索画面.md](spec/Access/基本設計書/01_学生検索画面.md) | ACCESS-BAS-STU-01 | 8.4 | 0.1 | PASS |
| 24 | 基本設計 | 試験生成 | [基本設計書/02_学生登録画面.md](spec/Access/基本設計書/02_学生登録画面.md) | ACCESS-BAS-STU-02 | 8.4 | 0.1 | PASS |
| 25 | 基本設計 | 試験生成 | [基本設計書/03_テーブル仕様書.md](spec/Access/基本設計書/03_テーブル仕様書.md) | ACCESS-BAS-STU-03 | 8.1 | 0.1 | PASS |
| 26 | 基本設計 | 試験生成 | [基本設計書/04_コード設計書.md](spec/Access/基本設計書/04_コード設計書.md) | ACCESS-BAS-STU-04 | 8.2 | 0.1 | PASS |
| 27 | 基本設計 | 試験生成 | [基本設計書/テーブル/01_m_student.md](spec/Access/基本設計書/テーブル/01_m_student.md) | ACCESS-BAS-STU-03-M_STUDENT | 8.1 | 0.1 | PASS |
| 28 | 基本設計 | 試験生成 | [基本設計書/テーブル/02_m_class.md](spec/Access/基本設計書/テーブル/02_m_class.md) | ACCESS-BAS-STU-03-M_CLASS | 8.1 | 0.1 | PASS |
| 29 | 基本設計 | 試験生成 | [基本設計書/テーブル/03_m_code_category.md](spec/Access/基本設計書/テーブル/03_m_code_category.md) | ACCESS-BAS-STU-03-M_CODE_CATEGORY | 8.1 | 0.1 | PASS |
| 30 | 基本設計 | 試験生成 | [基本設計書/テーブル/04_m_code.md](spec/Access/基本設計書/テーブル/04_m_code.md) | ACCESS-BAS-STU-03-M_CODE | 8.1 | 0.1 | PASS |
| 31 | 基本設計 | 試験生成 | [基本設計書/テーブル/05_t_operation_log.md](spec/Access/基本設計書/テーブル/05_t_operation_log.md) | ACCESS-BAS-STU-03-T_OPERATION_LOG | 8.1 | 0.1 | PASS |
| 32 | 支援文書 | 既存採用 | [画面最適化記録.md](spec/Access/画面最適化記録.md) | Access-COMPACT-20261023 | 1.2 | 1.2 | PASS |
| 33 | 支援文書 | 既存採用 | [要件定義書.md](spec/Access/要件定義書.md) | ACCESS-REQ-STU-001 | 1.0 | 1.0 | PASS |
| 34 | 支援文書 | 既存採用 | [規約/Access.md](spec/Access/規約/Access.md) | ACCESS-DOC-5AA4A3B1E208 | 8.4 | 8.4 | PASS |
| 35 | 支援文書 | 既存採用 | [規約/全体/MD構造・Excel変換規約.md](spec/Access/規約/全体/MD構造・Excel変換規約.md) | ACCESS-DOC-MD-EXCEL | 8.4 | 8.4 | PASS |
| 36 | 支援文書 | 既存採用 | [規約/全体/テストデータ整備規約.md](spec/Access/規約/全体/テストデータ整備規約.md) | ACCESS-DOC-TEST-DATA | 1.0 | 1.0 | PASS |
| 37 | 支援文書 | 既存採用 | [規約/全体/テーブル仕様書記述規約.md](spec/Access/規約/全体/テーブル仕様書記述規約.md) | ACCESS-DOC-TABLE-FORMAT | 8.1 | 8.1 | PASS |
| 38 | 支援文書 | 既存採用 | [規約/全体/リポジトリ構成.md](spec/Access/規約/全体/リポジトリ構成.md) | ACCESS-DOC-REPOSITORY | 8.4 | 8.4 | PASS |
| 39 | 支援文書 | 既存採用 | [規約/全体/仕様書作成ルール.md](spec/Access/規約/全体/仕様書作成ルール.md) | ACCESS-DOC-SPEC-RULES | 8.5 | 8.5 | PASS |
| 40 | 支援文書 | 既存採用 | [規約/全体/評価規約.md](spec/Access/規約/全体/評価規約.md) | ACCESS-DOC-EVAL-GLOBAL | 8.1 | 8.1 | PASS |
| 41 | 支援文書 | 既存採用 | [規約/全体/開発規約.md](spec/Access/規約/全体/開発規約.md) | ACCESS-DOC-DEV-GLOBAL | 8.1 | 8.1 | PASS |
| 42 | 支援文書 | 既存採用 | [規約/開発規約.md](spec/Access/規約/開発規約.md) | ACCESS-DOC-BADE67AD5324 | 8.3 | 8.3 | PASS |
| 43 | 詳細仕様 | 試験生成 | [詳細仕様書/01_学生検索画面.md](spec/Access/詳細仕様書/01_学生検索画面.md) | ACCESS-DET-Access-SCR-STU-001 | 8.4 | 0.1 | PASS |
| 44 | 詳細仕様 | 試験生成 | [詳細仕様書/02_学生登録画面.md](spec/Access/詳細仕様書/02_学生登録画面.md) | ACCESS-DET-Access-SCR-STU-002 | 8.4 | 0.1 | PASS |

## 検査結果

期待44件・出力44件で欠落0・余分0。実出力からの相対参照375件、LIST/TABLEの構造50表、メタ情報と章/sheets、ID・PK/fieldIds・分冊・方式内依存を確認しPASS。入力索引31文書IDと全ファイルの参照閉包も確認した。実装Agentのinspect-only入力検査はAccessでstructure-check-passed、指摘0。構造検査は業務の承認や実装実行の代わりにはしない。

基本2機能は54項目・13イベント・候補12行・更新26行を維持し、11列、階層手順、既存CHK/N/DATE/OP、実メッセージと復帰を照合した。5論理表89項目の属性・PK順・fieldIds、5分類70コードの全レコードを保持。詳細2機能は26列の項目表を含む9LIST・164データ行と15OP定義表を保持し、DAO/ACE・単一ACCDB・Windows主体・30分状態・10分確認・全候補版・定員・学生/監査の一括確定と結果不明を具体化した。基本9と支援33、詳細2の独立レビューはPASS。

Mermaid 57図をすべて構文解析・描画し、うちER 22図を確認した。基本/詳細の同一HTMLを照合し、画面2種の静的モックを1366×768 CSS px・100%で描画・目視した。確認状態は検索完了/選択行あり/管理者と、登録の編集/管理者。日本語、項目、一覧、主要操作に重なり・切れは見つからなかった。この2状態以外の実機確認へ拡張していない。

## 未決・未実施

新しい要件定義書は既存仕様からの再構成で、新規の利用者承認ではない。初期5分類70コードと学生/クラス/監査0件を維持し、操作用架空データとの適用差はQA-REQ-SEED、性能・日付下限・運用保持等の未決は既存QAとして継承した。試験生成の都合で業務条件を承認・変更していない。

今回の仕様書は採用前ドラフトで、正式specRootへの採用・上書き、アプリ生成/コンパイル/Access実機/IME、DB作成/接続/投入/SQL実行、実Excel/PDF/印刷、性能・業務受入れ・正式採点、Git commit/merge/pushは未実施。formalScore=null。静的描画・構造・本文レビューのPASSと実アプリの検証を区別する。
