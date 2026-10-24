# Access 仕様と実装の対応

実行ID `20261023-access-build-01`。各入力版・SHA-256は凍結入力 `20261023-access-build-01-inputs.json`、出力は `20261023-access-build-01-outputs.json` を参照する。仕様変更なし。

| 仕様ID・範囲 | 実装 | 今回の検査 |
| --- | --- | --- |
| SCR-STU-001 SRC-001/002/006/008、EV-SRC-001～006、COM12、OP-COUNT/PAGE | clsSearchCriteria、modStudentSearch、clsSearchContext、modStudentForms、frmStudentSearch | 4業務プロパティ、廃止/未知rawキー拒否、型付きクラス/在籍パラメーター、リテラル照合、7表示列、表示DTOの縮小、状態ID/認証セッション/フォーム/期限/版/Revision、旧検索・クリア拒否。検索42・実フォーム検査内で確認 |
| SCR-STU-001 SRC-020～026/030、SRC-019/031～033 | StudentListCallback、SelectedStudentDetails、SearchClick | 氏名/カナ合成、和暦、年度/学年、クラス、在籍、操作案内。隠し学生IDで編集/参照。20/50/100・許可4ソート・IDタイブレークを維持 |
| SCR-STU-002 REG-001～034、EV-REG-001～008 | frmStudentEdit、modStudentForms、clsStudentDraft、clsStudentService、clsStudentRepository | 34論理項目、19業務入力、新規19/通常更新18、連動・定員・権限・版・確認・履歴の境界を維持。業務31・拡張77・フォーム39 |
| COM-STU-004 UI01～15、編集省スペース | Build-Access.ps1、frmStudentSearch/frmStudentEdit、frmDuplicateConfirm/frmDeleteConfirm/frmDiscardConfirm | 18400×9600twips、9pt、入力510twips、3列編集、複数行備考/理由、別モーダル・既定取消。COM寸法/設定確認。手動ピクセル・キーボード確認は未実施 |
| 共通01～03 / Access配置・認証 | modSecurity、modClock、clsUnitOfWork | 実Windows主体/内包役割、UTC、日本業務日、単体専用Workspace、ゲート。既存業務/権限検査を今回再実行 |
| 共通04～05/07/16/17 | modUnicode、modJapaneseDate、modStudentRules | Unicodeスカラー・NFKC・和暦境界・厳密ISOの既存試験を今回再実行 |
| 共通11/13/14、DB制約 | clsConfirmation、modConfirmationForms、clsUnitOfWork、clsStudentRepository、database | 全候補確認、10分、業務/監査同一Tx、続柄4項目NULL、複合FK21、2プロセス最終1席 |
| 共通10、保守・初期値 | modMasterMaintenance、modInitialMasters、modApprovedSeed | 固定コード/保護/人数/監査/初期同値と差分検出の拡張試験を今回再実行 |
| Access単体成果、配備初期状態 | StudentManagement.accdb、Build-Access.ps1、modDeployment、tests/Test-Deployment.ps1 | 同一バイトコピー19検査。5フォーム、初期5分類70値、学生/クラス/監査0、試験モジュールなし、外部リンク0 |

REG-025の更新日時/者は既存の合成 `lblUpdated`、REG-026は `frmDeleteConfirm.txtReason`、REG-032～034は `frmDuplicateConfirm.lstCandidates/cmdConfirm/cmdCancel` へ対応する。論理削除理由は確認フォーム内だけに置き、一般入力を保存しない。

生成、ネイティブコンパイル、DAO/フォーム自動検査の通過は実施範囲だけの結果であり、実利用・受入・逆生成・正式採点の完了を意味しない。
