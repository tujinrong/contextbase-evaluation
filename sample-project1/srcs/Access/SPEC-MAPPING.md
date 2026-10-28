# Access 仕様と実装の対応

runId `20261025-access-quality`。正本は [Access仕様](../../spec/Access/README.md)。今回の利用者要求による可読性と初期データの変更は `build/generation/user-overrides.json`、次回仕様への引継ぎはルートの `test-project1-spec-bug-report.md` に分けます。凍結入力は `build/generation/inputs.json`、最終検査は `build/test-results/summary.json` に記録します。原仕様は今回変更しません。

| 仕様ID・版・範囲 | 実装 | 更新と今回の検査 |
| --- | --- | --- |
| SCR-STU-001 8.4、SRC-001/002/006/008、COM12、OP-COUNT/LIST | clsSearchCriteria、modStudentSearch、clsSearchContext、modStudentForms | 4条件、未知/廃止rawキーは空でも拒否、範囲引数とPage/PageSizeプロパティ廃止、全一致0～10000件・10001件上限。検索契約50・全件境界7 |
| SRC-020～026/030、SRC-INT、EV-SRC-004/006 | StudentListCallback、modListScroll、SearchClick、OpenStudent | 非表示ID＋7表示列、許可4ソート＋IDタイブレーク、format3、所有者/session/form/30分/Revision。AppliedCriteria、未反映通知、実ListBoxスクロール・選択ID復元・消失解除をnative確認 |
| SCR-STU-002 8.4、REG-001～034、EV-REG-001～008 | frmStudentEdit、modStudentForms、clsStudentDraft、clsStudentService、clsStudentRepository | 34論理項目・19保存入力・更新18項目、連動・定員・権限・版・履歴を維持。未保存raw比較を追加。業務31・拡張77・実フォーム66 |
| COM-STU-004 UI01～15、各詳細の画面寸法、ACC-SPEC-001 | Build-Access.ps1、検索/編集/重複/削除/破棄フォーム | Single Form、幅18240twips、11pt、入力390・ボタン420基準、標準Rectangle枠と可変幅見出し、2列編集、一覧高4020、複数行690。利用者要求による旧9ptからの変更を別記。実フォーム入力と画像確認はnative-quality記録 |
| 共通01～03、方式別共通8.6、Access規約 | modSecurity、modClock、clsUnitOfWork | 実Windows主体・内包役割、UTC・日本業務日、専用Workspace/保存ゲートを維持。今回の業務/権限/実競合検査を再実行 |
| 共通04/05/07、Unicode・日付、ACC-DESIGN-003 | modUnicode、modJapaneseDate、modStudentRules、modMessages、modAccessInput | Unicodeスカラー・NFKC・和暦境界・厳密ISOを維持。郵便はnative必須7桁マスク、区切り非保存。全角数字キー入力と全clipboard正規化・桁検査を追加し、サービスで再検証 |
| 共通08 8.4、共通11/13/14、DB定義8.5・物理表8.1 | clsConfirmation、modConfirmationForms、clsUnitOfWork、clsStudentRepository、database | 10分確認、全候補再確認、業務/監査同一Tx、続柄4項目NULL、複合FK21、別2プロセス最終1席。6表/業務89列＋guard2列の物理内容は既存ソースと同一、由来情報を最新入力へ再生成 |
| 共通10 8.2、保守・初期値 | modMasterMaintenance、modInitialMasters、modApprovedSeed | 5分類70値、保護/人数/監査/初期同値・差分検出を維持。最新定義から再生成し拡張試験を再実行 |
| Access単体成果・配備初期状態、ACC-SPEC-002、共通データ整備規約 | Build-Access.ps1、modDeployment、modSampleData、Test-SampleData.ps1、Test-Deployment.ps1 | 最終1ACCDBの同一バイトコピーで検査。架空学生12/クラス4/監査16、初期検索9、試験モジュールなし、外部リンク0。新要求により旧0件から変更。再投入は既存sample/利用者行/版/監査/削除状態を保持 |
| 全体固定build/.tmp運用 | GeneratedPaths.ps1、Invoke-Verification.ps1、Test-GeneratedPaths.ps1 | 方式内絶対パス/reparse point境界、試験DB混入拒否、生成直後の旧検証無効化、固定名最新記録、パス境界8・PS構文17 |

REG-025は合成 `lblUpdated`、REG-026は `frmDeleteConfirm.txtReason`、REG-032～034は `frmDuplicateConfirm.lstCandidates/cmdConfirm/cmdCancel` に対応します。論理削除には編集中の一般項目を渡しません。再読込は値と版を一緒に置換し、通常取消は読込時スナップショットへ戻します。

生成・VBEコンパイル・DAO/フォーム自動検査は記録された実施範囲の結果です。32bit、手動受入、性能保証、実本番データ、共有SQL移行、逆生成・正式採点は完了していません。

現在の配置はsample-project1（旧test-project1）。過去の生成日・runId・凍結入力パスは当時の記録として保持し、今回の改名で再生成/再検証済みとはしない。
