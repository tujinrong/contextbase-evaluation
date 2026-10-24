# Vue / TypeScript + C# Web API 学生管理

実装更新版8.1／2026-10-23（独立生成版8.0を更新）。原仕様は[当方式専用spec](spec/README.md)。当フォルダーのCore、database、maintenance、testsだけを使用する。フォルダーを単独で移してビルドできる。他プロジェクトへのProjectReferenceやCompile Linkはない。

今回の実行IDは20261023-vue-csharpapi-build-01。検索を学籍番号・氏名・クラス・在籍区分の4条件、一覧を7列へ更新し、住所・電話・更新日時は検索DTO/SQL投影から除外した。原入力と型付き正規化値を分離する。廃止・未知の検索キーは空値でも422/E-SRC-002。保持状態の形式版はsearch-compact-1で、所有者・期限・Revisionを確認した後、旧形式は警告W-SRC-002と未検索へ初期化する。旧Revisionや他者の状態を初期化の根拠にはしない。

.NET 10 SDKを使用する。フロントエンド依存はpackage-lock.jsonで固定する。

```powershell
Set-Location frontend
npm ci --ignore-scripts
npm run build
Set-Location ..
```

```powershell
dotnet build StudentManagement.slnx -c Release
$env:ConnectionStrings__StudentDb = 'Server=YOUR-SERVER;Database=YOUR-DB;Integrated Security=True;Encrypt=True;TrustServerCertificate=False'
dotnet run --project backend/StudentManagement.Api.csproj --launch-profile https
```

SQL資源の作成と配備は[当方式のdatabase](database/README.md)を参照。初期値は5分類70コード、学生・クラス0。承認済みクラスは管理者が設定する。接続文字列・本番主体・秘密は環境設定で渡す。TLSとサーバー証明書検証を有効に保つ。

Secure/HttpOnly/SameSite Cookie認証、CSRF、主体・セッション・タブ所有者、受領したcontextRevisionによる状態更新を行う。評価用POST /_evaluation/sessionはDevelopment環境かつEvaluationSession:Secretが設定された場合だけ有効。役割はサーバーのEvaluationSession:Roleで決め、要求本文から取得しない。本番の外部認証製品との結合は未実施。

検索／登録の2画面に、原入力・正規化値・適用済み条件・読込時スナップショット・Busy・確認取消を分ける。IDと版は10進文字列。生年月日は和暦4原入力。学生編集は全34項目を維持し、上段の基本情報と下段3列に配置する。通常の1366×650・1280×650で主要操作へ到達し、多数行は一覧内だけをスクロールする。重複・削除・未保存破棄は個別のネイティブdialogで表示し、取消へ初期フォーカスを置く。狭幅・拡大では折返しとページの縦スクロールを許容する。クラス・コード保守は[当方式のmaintenance](maintenance/README.md)を使用する。

```powershell
dotnet run --project tests/Core/StudentManagement.Core.Tests.csproj -c Release
dotnet run --project tests/ApiContracts.csproj -c Release --no-launch-profile
dotnet run --project database/tests/SqlServer.IntegrationTests.csproj -c Release
node frontend/tests/browser.mjs UNIQUE-RUN-ID
```

Core検査はUnicode・日付・正規化・導出カテゴリ・履歴操作を検証。HTTP契約検査は実HTTPS/Kestrelで認証・CSRF・状態・要求・応答を検査し、DBサービスは明示fakeを使用する。ブラウザ検査は実Vue/Edgeを使用し、API応答はmock。既定の報告先は当方式frontend/test-report。SQL実行用接続がない場合、integrationはSKIPと表示しDBを開かない。Windows UI受入・SQL実機競合・認証製品結合・逆生成採点を合格扱いしない。集約結果はtest-project1/test-reportに保存する。

ビルド済みVueと実APIの接続確認には、別端末で読取り専用の[方式内fixtureホスト](tests/EvidenceHost/README.md)を起動して次を実行する。Python PlaywrightとChromiumが必要。ローカル開発証明書の検証省略はこの試験だけで、本番のTLS検証は維持する。

```powershell
dotnet run --project tests/EvidenceHost/EvidenceHost.csproj -c Release -- --port=7444 --minutes=10
python -X utf8 tests/fullstack_browser.py --url https://localhost:7444 --output build/fullstack-unique-id
```

今回の検証は[実行記録](../../test-report/20261023-vue-csharpapi-build-01/README.md)を参照。SQL実機・配備・正式受入・逆生成採点は未実施。
