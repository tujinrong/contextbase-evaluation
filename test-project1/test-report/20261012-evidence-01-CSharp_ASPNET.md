# CSharp_ASPNET 新規テストと画面撮影入口

2026-10-12／projectId=test-project1／build／20261012-evidence-01-CSharp_ASPNET。

今回の新規実行：Core境界 96件、実HTTP/Controller契約 31件、撮影fixture 16件がすべて成功。

契約テストは各方式の既存fake service、撮影ホストは実画面と新しい合成読取fixtureを使用。SQL Server統合や更新業務の合格ではない。

入力：独立spec 42文書（版8.0/8.1）、source/fixtureを含む107ファイル。現specのsqlserver-12 lockとのSHA差分0。詳細hashは同名.inputs.json。

テストデータは仮名3学生、明示TEST2026-0001～0003、2テストクラス、当方式seed由来70コード。実在の学生情報を使用していない。既定01/02検索2件、状態全offで3件。大きなIDは9007199254740993～9007199254740995。保存・削除は撮影サービスで拒否し、fixtureを変更しない。

撮影入口：https://localhost:7441/__evidence/login?role=Staff

起動（方式ルート）：`dotnet tests/EvidenceHost/bin/Release/net10.0/EvidenceHost.dll --port=7441 --minutes=60`。最大60分で自動停止。停止は`POST https://localhost:7441/__evidence/stop or Ctrl+C`。当方式tests/EvidenceHost/README.mdも参照。

既存QA開発証明書を使用。状態JSONのHTTPS確認だけcurl -kを使い、実TLSや認証基盤の適合に流用していない。Cookieは撮影ホスト専用。SQLサービスのDI登録は削除している。

画面操作・撮影は親Agentがtest-project1/test-evidence/20261012-evidence-01へ出力する。このAgentのUI操作・撮影は0件。

親の実ブラウザー確認：検索2行、BigInt学生の編集、必須入力native bubble。SQL未実施。

UI-OBS-MVC-001（軽微）：初期・編集・新規の空validation-summary赤枠/空bulletが恒常表示（親スクショ01/03/06）。本体変更は行わず観察として報告。構造ブロッカーではない。

CAPTURE-MVC-005：tab.screenshot(fullPage:false)の空白画像はINVALID_CAPTURE。CUA getScreenshotは正常で撮影方法を切り替えたとの親報告。撮影装置の失敗をアプリ失敗や合格に混ぜない。

変更は新規tests/EvidenceHostと本回レポートだけ。本体DDL・仕様・runtimeコード・共有DBは変更せず、既存記録を保存する。共有role/SQLCLRの構造衝突が未解消のため、DB導入の停止を維持する。

未実施：実SQL統合、実認証基盤/DBロール認可、永続保存/削除、競合・監査取消、当Agentの画面撮影。親の画面証拠と別レポートを合わせて確認する。

| 入力/出力 | SHA256 |
| --- | --- |
| fixture-data.json | 7e9b94e6306ac6c5ead644793ede74a661ad8505fc4e3f20033d3e801b092c67 |
| test-project1/srcs/CSharp_ASPNET/bin/Release/net10.0/StudentManagement.Web.dll | 09fd29f896d13900a21be19dc70fb6ace9490cb24ae1498d37508541d73affc2 |
| test-project1/srcs/CSharp_ASPNET/Core/bin/Release/net10.0/StudentManagement.Core.dll | 759cc94561800e743f8a6844df94e2165b05a5991c0e3f08626c15c50e2329a4 |
| test-project1/srcs/CSharp_ASPNET/tests/EvidenceHost/bin/Release/net10.0/EvidenceHost.dll | ccecb21d242cc5c68296f99f423cbcba8bfa9d083f7863e6773dbe94d7b46517 |

JSONは実行コマンド・合成データ・出力assembly・生ログSHAを記録する。runtimeログはホスト稼働中のため最終hashを固定していない。
