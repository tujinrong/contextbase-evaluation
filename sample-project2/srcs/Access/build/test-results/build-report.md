# Access 文字コード修正と残る画面改善

2026-10-30。現在の配布候補は4629fe0c…acab0fc。文字コードの修正を確認し、画面全体の適合は未完了です。

- VBA正本33ファイルはCP932、Form native exportはUTF-16 BOM、文書/Python/JSONと業務データのUnicodeは保持。
- ホストACP936・Office UI1041で33モジュール意味一致、11文字列の実行とexport/reimport、5画面の固定文言、4MSGを確認。境界単体11件、業務API67件、認証39件を通過。
- 5Form/6表示を実Accessで確認。文字化けは観測せず、既存タイトル11pt/Label330twipは未改修として記録。全体のタイトル/入力高はDQA-UI11で後続再設計。
- 現source.zip47memberを別展開し、原仕様/試験を含めず通常build/11class/probe除去再compile/所有Office正常終了を確認。
- 既存5表の全typed row/schema、資格情報を保全。seed/資格情報resetなし。

[文字コード検査](japanese-encoding.json)、[日本語実画面](root-native-resume-review.json)、[配布再構築](source-package-rebuild.json)を参照。旧0810の属性475/Pending129/PDF等は新候補へ流用していません。Agent規約とQA改訂後の入力再凍結/独立期待値更新・全UI検査は未実施で、正式outputsは未発行、formalScore=nullです。
