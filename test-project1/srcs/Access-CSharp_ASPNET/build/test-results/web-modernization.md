# PC向けWeb再構築の検証

2026-10-27。Access-CSharp_ASPNETにAR028～030を適用した。利用者の明示指示によりPCブラウザー1280×650／1366×650 CSS pxを対象とし、スマートフォン対応は対象外。

検索・学生編集／参照・確認・クラス／コード保守を左見出し・右項目の列が揃う配置へ変更した。ヘッダー・余白・説明・入力幅を整理し、PCの650px高で全22入力と保存barが収まる。生年月日・入学日・卒業退学日とマスター有効日はカレンダー入力＋和暦表示とし、元号4欄を常設しない。

| 今回の検査 | 結果 | 根拠 |
| --- | --- | --- |
| Debug／Releaseビルド・Release publish | 警告0・エラー0 | build.json |
| Core境界 | 45 PASS、メモリprovider | core.json |
| Webアダプター | 31 PASS | web-adapter.json |
| 実SQLのブラウザー操作 | 15 PASS、登録・更新・取消・削除・候補連動・CSRF | browser.json |
| PC配置とカレンダー実操作 | 15 PASS | ui-rules-browser.json |
| マスター新規／編集画面 | 4 PASS、DB書込みなし | ui-rules-masters.json |
| Debugからの実DB検索・編集表示 | PASS | ui-rules-debug.json |
| 独立ソースレビュー | 指摘0 | ui-rules-review.json |
| 配布ZIPの隔離build | 警告0・エラー0、production46ファイル | package-isolation.json |
| 原本・台帳・業務・DB保全 | 52保護ファイル、7表93列、既存TRN2件が不変 | ui-rules-preservation.json |

カレンダーは実キーボードとマウスでネイティブpopupを開き、日付選択による昭和→平成／平成→令和境界、2000年の閏日、1900年の非閏年を検証した。実キー入力・クリア・範囲・再表示・候補変更時の終了日クリアも確認した。JST・Los Angeles・AucklandでISO日付と和暦表示が一致した。

[学生編集の表示](ui-editor.png)／[検索の表示](ui-search.png)。スクリーンショットと計測値を目視で確認した。カレンダー試験は業務POST0、実SQL回帰で追加した合成学生は通常の論理削除で整理し監査を保持した。

原Access・完了済み2回の訓練台帳・Core・DB資源・参照CSharp_ASPNETソースを保持した。抽出は原本hashが一致する既存の検証済み抽出を再利用し、Access起動・DB再作成・seed再投入・第3回訓練は行っていない。過去のPASSを今回へ転記していない。

原Access実画面による業務受入、別Accessファイルへの一般適用性、本番配備・外部認証、正式採点は未実施。formalScore=null。
