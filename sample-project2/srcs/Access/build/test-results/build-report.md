# Access build検査記録

runId `sp2-ui-regenerate-20261029`。状態は **NON_UI_COMPLETE_UI_INCOMPLETE / UI_NOT_VERIFIED**、正式採点nullです。

最終配布 `build/CareerManagement.accdb` SHA `663d201286d38adcf69e7d21c5a1c3de339c0376fed78cd6d2826b358588ecf1`。元 `01b81b1d4c69c7bee1c512a91751ce3f5cdef9de8d567fe923203680dc901b88` の5表48列全型付き行・資格情報・内部ID・版を保ち、Forms/VBAのみ更新しました。seed/resetは実行していません。原子コピー公開後も同SHAです。

RunCommand126/IsCompiled、全11class初期化、probe除去/再compileは通過しました。3改善cycleは45/67/67 API件で、最終663の67件と認証39件がPASSです。旧候補5a45/451のPASSは最終へ転記していません。独立監査は最終663を別copyから439保存属性、149native在庫、31VBE token、compile、全5表データで再確認しました。

source-only ZIPは43member。原仕様・正式tests/期待値・検査結果を含めず独立展開からfresh DEMOを再構築し、全11class compileと別所有copyの認証39件を確認しました。fresh seedは利用者データを保持した最終ACCDBと区別します。

製品の実Excel WorkbookからPDFを出力しました。通常2頁、数字先頭40scalar氏名4頁、20件最大長120頁（sheet別4/116）です。本文10.5pt、Footer整数11ptと数字解釈境界はDQA-UI09で扱い、限定probe/製品PDF/APIを実Excelプレビュー/紙印刷PASSへ読み替えません。最終候補/今回配布検査の所有Office正常終了とApplication Error1000の照合はoffice-process-health.jsonを参照します。

**残件**：F03先頭可視社員IDの捕捉/復帰は未実装で、選択IDを代替にしません。Windowsロックでnative操作を止めたため、Header/Tab/Footer、通常復帰/下端、raw/Pending/未反映/取消、Dialog、実キー/clipboard/IME/viewport/他倍率は未検証です。rootのnative-ui-checklist.mdと新所有copyで継続します。実Excelプレビュー/紙印刷/別環境・正式受入も未実施です。

必須UI gateは現在観測ファイル欠落でFAIL、manifestは発行拒否し **outputs.jsonは存在しません**。gateを弱めずrequired-gates.jsonにCLIの実出力を残しました。候補在庫はcandidate-inventory.jsonへ記録しますが、正式outputsの代替や受入PASSではありません。

本文と全SHA/検査範囲はbuild-report.jsonを正とします。

初期の最小F04/コンパイラーprobeではIsCompiled=FalseやForm実体化COM待機があり、正確な原因は未確定です。所有probe46684は正常終了待機後の本人確認付きtimeout終了となりました。これらを製品PASSにせず、最終663の全業務版で再測定したコンパイル/正常終了と分けています。
