# Vue_CSharpAPI 新規テストと画面撮影入口

2026-10-12／projectId=test-project1／build／20261012-evidence-01-Vue_CSharpAPI。

今回の新規実行：Core境界 96件、実HTTP/Controller契約 44件、撮影fixture 16件がすべて成功。

契約テストは各方式の既存fake service、撮影ホストは実画面と新しい合成読取fixtureを使用。SQL Server統合や更新業務の合格ではない。

入力：独立spec 42文書（版8.0/8.1）、source/fixtureを含む124ファイル。現specのsqlserver-12 lockとのSHA差分0。詳細hashは同名.inputs.json。

テストデータは仮名3学生、明示TEST2026-0001～0003、2テストクラス、当方式seed由来70コード。実在の学生情報を使用していない。既定01/02検索2件、状態全offで3件。大きなIDは9007199254740993～9007199254740995。保存・削除は撮影サービスで拒否し、fixtureを変更しない。

撮影入口：https://localhost:7442/__evidence/login?role=Staff

起動（方式ルート）：`dotnet tests/EvidenceHost/bin/Release/net10.0/EvidenceHost.dll --port=7442 --minutes=60`。最大60分で自動停止。停止は`POST https://localhost:7442/__evidence/stop or Ctrl+C`。当方式tests/EvidenceHost/README.mdも参照。

既存QA開発証明書を使用。状態JSONのHTTPS確認だけcurl -kを使い、実TLSや認証基盤の適合に流用していない。Cookieは撮影ホスト専用。SQLサービスのDI登録は削除している。

画面操作・撮影は親Agentがtest-project1/test-evidence/20261012-evidence-01へ出力する。このAgentのUI操作・撮影は0件。

Vue型検査はNode24.16.0／vue-tsc --noEmitで成功。既存wwwroot配信物を再生成・上書きしていない。

変更は新規tests/EvidenceHostと本回レポートだけ。本体DDL・仕様・runtimeコード・共有DBは変更せず、既存記録を保存する。共有role/SQLCLRの構造衝突が未解消のため、DB導入の停止を維持する。

未実施：実SQL統合、実認証基盤/DBロール認可、永続保存/削除、競合・監査取消、当Agentの画面撮影。親の画面証拠と別レポートを合わせて確認する。

| 入力/出力 | SHA256 |
| --- | --- |
| fixture-data.json | 029a7bc38111f189e4575880e4ce1573550579ea5e8b47728faf556d2cf00d26 |
| test-project1/srcs/Vue_CSharpAPI/backend/bin/Release/net10.0/StudentManagement.Api.dll | 2cef731014acc009dda0324a7dbba812298423720962a2b7df18e42cd251ebeb |
| test-project1/srcs/Vue_CSharpAPI/Core/bin/Release/net10.0/StudentManagement.Core.dll | 57d531209311f2a68d55b9fd6338e2e45f34665355cd659b5226e3e4a6b0d45d |
| test-project1/srcs/Vue_CSharpAPI/tests/EvidenceHost/bin/Release/net10.0/EvidenceHost.dll | c3483736badd2311ef96e2cb9d97f3a11a466a69b0ee207ff2f1064a06aa77ad |

JSONは実行コマンド・合成データ・出力assembly・生ログSHAを記録する。runtimeログはホスト稼働中のため最終hashを固定していない。
