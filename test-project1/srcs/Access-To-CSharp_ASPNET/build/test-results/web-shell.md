# Webグループ見出し・左サイドメニューの検証

2026-10-28。対象はtest-project1／Access-To-CSharp_ASPNET。Agent正本はagents/converts/access-rebuilder-agent/。

グループ名を「01 基本情報」等の独立した太字見出しとして内容の上方へ配置した。枠線に見出しを重ねるGroupBox表現を廃止し、既存のfieldset無効化とaria名を保持した。メニューは左156pxの縦サイドバーへ変更し、現在位置と既存権限による項目表示を維持する。AgentにはAR031・AR032を追加した。

| 今回の検査 | 結果 | 根拠 |
| --- | --- | --- |
| Debug／Releaseビルド・Release publish | 警告0・エラー0 | build.json |
| PC配置・メニュー・Reader | 11 PASS、実SQL読取りのみ | web-shell-browser.json |
| カレンダーと既存配置の回帰 | 15 PASS、業務DB書込み0 | web-shell-calendar.json |
| 登録・更新・削除・取消・候補・CSRF回帰 | 15 PASS、VerificationMemory | web-shell-regression.json |
| 独立ソースレビュー | 指摘0、既存26コントロール属性維持 | web-shell-review.json |
| ZIP実隔離Release build | 警告0・エラー0、46ソース | package-isolation.json |
| 原本・DB・業務コード保全 | 30保護ファイル・7表93列・既存学生2件不変 | web-shell-preservation.json |

1280×650／1366×650 CSS pxで、22入力の最下端は569.23px、保存bar下端は629.73px。左メニューと入力欄が重ならず、主要入力・保存操作が画面内に収まった。[編集の表示](ui-editor.png)／[検索の表示](ui-search.png)。画面は親Agentと独立レビュアーが目視確認した。

Readerでは管理メニューを表示せず、直接のMasters URLは403、全22入力は無効、保存操作は表示しない。実Tab／Enterのメニュー移動と取消、日付・元号境界・閏日・クリアを確認した。実DBへの書込みはなく、CRUD回帰は隔離したメモリproviderで行った。

原Access、完了済み2回の訓練台帳、Core、Controller、Infrastructure、Model、JavaScript、DB資源、接続設定を保持する。訓練を追加せず、過去のPASSを今回へ転記していない。スマートフォン対応は利用者指定により対象外。原Access実画面による受入、別Accessへの一般適用性、本番配備・外部認証、Visual Studioデバッガー操作、正式採点は未実施。formalScore=null。
