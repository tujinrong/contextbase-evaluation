# Access 通知文字化け修正 R6

2026-10-12、実Access 16.0／64 bit、システムANSIコードページ936で実行した。仕様は方式内45ファイル、業務8.0・配置8.1・DB索引8.2で、変更はない。入力SHA-256は [inputs.json](inputs.json)、集約結果は [results.json](results.json)。旧工程の記録は上書きしていない。

R5画面の `E-DATE-001` が「元号?年?月?日」と表示された不具合を再現した。UTF-8の共通05（版8.0、文書ID COM-STU-005、129行）の期待本文は「生年月日の元号・年・月・日を確認してください。」である。R5同一バイトのコピーを開いて58通知を実VBAで照合すると46一致・12不一致、項目ラベルも不一致だった。[修正前JSON](20261012-evidence-01-access-r6-message-before.json) と実VBEソースを保存した。これは不具合再現記録であり、合格結果ではない。

production全VBA文字列リテラルを現コードページで検査すると、非表現文字はU+30FBだけ、modMessagesの18・modCandidatesの3・modConfirmationFormsの2で計23文字だった。該当文字だけを `ChrW(&H30FB)` で結合する実装へ変更した。[変更ファイルと前後SHA](source-changes.json)。現コードページを文化設定の932と取り違えず、Windows GetACPの936を使用した。

最終ソースから新規clean ACCDBを作り、VBAコンパイルに成功した。修正後の新規検査は以下の91チェックである。

| 新規検査 | 件数 | 根拠 |
| --- | ---: | --- |
| UTF-8仕様原文と実VBAの通知完全一致 | 58 | [message-after](20261012-evidence-01-access-r6-message-after.json) |
| 卒業・退学日の項目ラベル完全一致 | 1 | 同JSONのfieldLabel |
| 実フォームのUnicode候補SQL／DAO照会／確認キャプション | 13 | [ui-encoding](20261012-evidence-01-access-r6-ui-encoding.json) |
| 配布ACCDBの起動・初期件数・独立構成・制約 | 19 | [deployment](20261012-evidence-01-access-r6-deployment.json) |

通知の期待値はPowerShellがUTF-8仕様から作り、VBEへ注入していない。実VBAの `E-DATE-001: 生年月日の元号・年・月・日を確認してください。` が完全一致した。修正後productionリテラルの非表現文字0、PS5構文5スクリプトのエラー0。SQL候補6件は検索クラス・登録クラス・性別・都道府県・在籍区分・続柄の実RowSourceをDAOで照会した。確認フォームもproductionのForm_Loadで作った実Captionを照合した。画像や別フォームは生成していない。

配布成果 `srcs/Access/StudentManagement.accdb` の最終SHA-256は `D1777167FD7423BF4399F05D006519FD5A8E005A6FEF2E56B1A8F11AAD73EC87`。FileFormat12、Standard ACE DB、学生・クラス・監査0、試験モジュールなし、SELF／外部リンク0を同一バイトのコピーで確認してから置換した。原本自体はCOMで開いていない。R5旧版は `build/20261012-evidence-01-backup/StudentManagement.r5-before-encoding.accdb` にSHA-256 `0547CB5FF9D70C5F17F97D42E8D14E5EAEAB6D3CDEDD2B3F0DA9744960B22E2A` のまま保存した。[置換記録](replacement.json)。

撮影用に別の新規SingleFile ACCDBを作り、production保守／保存で架空1クラス・3学生・4CREATE監査を登録した。[R6 UI報告](../Access-ui-r6/README.md)。Visible=false COMで閉鎖済み。手動撮影はroot担当で、この工程はGUIを表示していない。

R5の業務137・続柄21・形式Boolean10・検索21・２プロセス競合はR6で再実行していない。旧工程の合格を91件へ加算しない。共有SQLの配備・接続・認可、Office 32 bit、LAN切断、10,000／10,001件性能、確定応答喪失は未実施。build-10 ZIPは旧改訂の凍結成果として保持し、今回再生成していない。
