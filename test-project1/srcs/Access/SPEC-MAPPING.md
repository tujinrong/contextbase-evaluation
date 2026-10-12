# Access 仕様と実装の対応

仕様正本はすべて `spec` 内です。配置・認証の４文書は8.1、DB索引は書式修正版8.2、それ以外は8.0。生成時のファイル別 SHA は配布検査 JSON に保存しました。

| 仕様 | 実装 | 状態・実検査 |
| --- | --- | --- |
| 学生検索詳細 / 共通12 | modStudentSearch、clsSearchContext、modStudentForms、frmStudentSearch | 実 DAO 検索、最小一覧 DTO、AppliedCriteria、ソート・ページ、30分状態、停止値表示、全文欄。フォーム起動・検索・編集条件と適用条件の分離を検査 |
| 学生登録詳細 / 共通06〜11 | clsStudentDraft、clsStudentService、clsStudentRepository、frmStudentEdit | 正規化後の19入力、所属・期間・人数・状態、変更なし、版一致更新・論理削除、全候補確認。実 CRUD・古い版・定員・権限を検査 |
| 共通01〜03 / 方式別共通8.1 | modSecurity、modClock、clsUnitOfWork | Windows 実主体＋内包役割、UTC時点・日本業務日、同一ファイル専用 DAO Workspace・ゲート。Reader/Staff/Admin と不成立、別プロセス競合を検査 |
| 共通04〜05 / 共通07 | modUnicode、modJapaneseDate、modStudentRules | NFKC・スカラー数・英字・カナ・電話・厳密 ISO・和暦。補助文字往復、昭和/平成/令和境界、フォーム4原入力を検査 |
| 共通11 / 登録の確認 | clsConfirmation、modConfirmationForms、modCandidates、frmDuplicateConfirm、frmDeleteConfirm | 主体・認証世代・フォーム・対象・版・19入力・全候補集合・10分期限。別フォーム拒否、全候補消失時の再確認、実ダイアログ0/21候補・理由・既定取消を検査 |
| 共通13〜14 / DB制約C-001〜018 | clsUnitOfWork、clsStudentRepository、Build-Access.ps1、database | 同一ゲート・業務＋履歴一括確定、失敗取消、採番、属性0の参照整合 FK。監査失敗の両方取消、緊急4項目の全16NULL組合せ、親参照拒否を検査 |
| 共通15 / メッセージ一覧 | modMessages、modFailure | 58メッセージ、項目キー・ラベル・上限、受付番号、DAO番号の診断。E-COM001/002/004、E-STU105、長さパラメーターを検査。SQLや学生原値を診断へ出力しない |
| 基本クラス / 共通10 / 保守 | modMasterMaintenance、modInitialMasters、modApprovedSeed | クラス/コード CRUD入口、固定意味と保護、在籍人数、同名警告、状態遷移の CREATE/UPDATE/DISABLE/ENABLE 監査。保護拒否・停止中名称変更・初期同値/差分を検査 |
| DB索引8.1 / 物理6文書8.0 | tools/generate_schema.py、database、Build-Access.ps1 | 業務89列＋ゲート＋評価役割表。5分類70コード。単体成果の７FK、双方NULL列プロパティ、初期０学生/クラス/監査、外部リンク０を検査 |
| 配置8.1 | StudentManagement.accdb、modDeployment、tests/Test-Deployment.ps1 | １ファイル、４フォーム、VBAと全物理表内包、起動画面。試験モジュールなし、初期状態19項目通過 |

実機試験の成功と未実施の範囲は README と新規試験報告に記載しています。設計で列挙した全共通試験や複数 Office 環境の成功を意味しません。
