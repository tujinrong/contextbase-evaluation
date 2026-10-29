# 社員経歴管理 / CSharp_ASPNET

sample-project2専用の .NET 10 MVC サンプルです。社員検索・社員と最大20経歴の一括保存・2シートの経歴書・部署/案件役割の保守を備えます。STAFFは社員業務、ADMINは加えてコード保守を行えます。社員削除、利用者管理、パスワード変更の画面はありません。データは全て架空です。

Windows 11、.NET SDK **10.0.401** / ASP.NET Core **10.0.12**、SQL Server 2022 Express、HTTPS、メイリオが必要です。今回の実DB検査ホストは SQL Server **2025** Express 17.0、互換レベル160です。SQL Server 2022の物理ホスト、正式受入、印刷品質をその検査結果で代替していません。

VS2026では `CareerManagement.slnx` を開き、`CareerManagement.Web` をスタートアッププロジェクトにします。この作業環境の既存DEMOをF5で使う場合は、ソースルートで `./tools/Configure-DemoDebug.ps1` を一度実行してからデバッグを開始してください。明示した `.tmp/runtime/profile.json` のローカルfixture接続とキー保存先を、このWebプロジェクトのDevelopment用user-secretsへ保存します。さらに `Properties/launchSettings.json` の既存 `CareerManagement.Web` プロファイルに、両環境名のDevelopment指定、DB名・fixture指定・Windows統合接続の3設定、ログイン画面の起動先を同期します。これにより、起動済みVSから引き継いだ古い接続設定より明示したDEMO設定を優先します。launchSettingsの接続はSQLパスワードを含まないローカル専用値で、キー保存先はuser-secretsだけに保持します。他の起動プロファイルや設定値は維持します。DBの作成・投入・初期化は行わず、HTTPS証明書のパスワードやログイン情報もコピーしません。別の所有DEMO profileは `-ProfilePath` で明示し、検証だけなら `-ValidateOnly` を指定します。user-secretsはGit/配布物に含まれません。ソースだけを別環境へ配備する場合は、次の通常初期設定で専用DBを準備してください。通常環境のSQL証明書検証は維持します。

`tools/Build.ps1` でlocked restore・Release build・固定 `build/publish` への配布を行います。中間出力は `.tmp/bin` / `.tmp/obj` です。`tools/Build.ps1 -RunTests -Cycle 3` は下記の専用DB試験も行うため、SQL Expressへの新規fixture作成権限を必要とします。

通常の初期設定では、管理担当者が明示した **新規** `SampleProject2_Career` だけを作成します。既に存在する場合は停止し、初期化・再作成しません。接続は `SP2_CONNECTION_STRING` にWindows統合認証、`Encrypt=True;TrustServerCertificate=False`、明示DBを設定してください。サーバーや他DBを自動探索しません。

```powershell
# 接続先・サービス主体・HTTPS証明書は配備先管理者が指定します。秘密をこのファイルへ書きません。
dotnet run --project tools/CareerManagement.Setup -- create SampleProject2_Career
dotnet run --project tools/CareerManagement.Setup -- seed SampleProject2_Career
```

DEMOの初期ログインは **admin / staff、パスワードは両方123** です（2026-10-29利用者確定、最小3～最大128 Unicodeスカラー）。標準の`seed`はこのDEMO資格情報を設定します。明示的な別資格情報を使う場合だけ`seed-interactive`で非表示入力を2回行います。引数・環境変数による個別パスワード入力は受け付けません。Web起動にDDL/seedはありません。投入データは `fixtures/SP2-DEMO-01.json`、外部manifestは `build/generation/seed-manifest.json` です。新規SP2-DEMO-01 v1.1の初回は5表合計20行（分類3/コード9/利用者2/社員3/経歴3）を一括確定し、同一manifestと全業務値の一致時だけ再投入をスキップします。変更・不足・別所有なら無変更で停止します。マニフェストを削除して強制投入しないでください。

既存の所有DEMO DBでアカウントだけを更新するときは、接続先を明示して `dotnet run --project tools/CareerManagement.Setup -- demo-credentials <正確なDB名>` を実行します。SP2Ownerと安定user_id SP2ADMIN/SP2STAFF・既存ロール・login_idの対応を確認し、2名のlogin_id/ハッシュ/有効状態/失敗数/ロック期限だけを一つのトランザクションで更新します。ID・権限・表示名、他利用者と業務4表の全値/監査値を保持し、衝突・所有不一致・対象欠落は無変更で停止します。二度目は検証してSKIPし、既存seed-manifestは上書きしません。auth-onlyの系譜と全業務値の前後SHAは `build/generation/auth-migration.json` へ記録し、v1.1の全量再投入済みとは扱いません。稼働中Webは旧セッションを残さないため、更新後に対象ホストを再起動してログインし直します。

DB所有者の設定後、Web実行用Windows主体には `database/application-permissions.sql` の限定roleだけを割り当ててください。スクリプトは既存server loginを作成/変更しません。Web主体にsysadmin/db_owner/db_ddladminを付けず、利用者/社員/分類/コードのDELETE・DDLを拒否します。経歴DELETEは全体保存時の明示除去だけです。自己試験がWindows統合管理主体で接続した事実と、配備先の限定主体による稼働確認は区別してください。

HTTPSのURL/証明書はASP.NET Coreの通常構成で指定します。`SP2_DATA_KEYS` はサービス主体だけが読み書きするDPAPI鍵保存先を明示します。許可がない場合はWindowsの当該主体LocalAppDataを使います。CookieはSecure/HttpOnly/SameSite、無操作30分でサーバー認証と未保存値を失効し、各操作と確定直前に現在利用者を再照会します。停止利用者は次の操作から拒否します。

操作確認はSTAFFでログイン→検索（初期在職2件）→000001を選択→編集と取消→経歴書Excel（2経歴、最新順）→新規000004を入力して保存→再検索です。000003は在籍未指定で検索でき、経歴0のためExcelは拒否されます。ADMINは部署04を新規追加・停止できます。社員番号は6桁文字列、既存番号は変更できません。経歴追加/反映/除去は未保存状態で、上部の保存だけが親子全体を確定します。確定成否不明のMSG-034では再保存せず、破棄確認後の再読込みで現在値を確認してください。

既知制限 **PH05：OPEN／詳細設計の修正待ち**。未検索の状態で検索条件を編集し、再検索せず「新規登録」→社員欄を変更せず「取消・検索へ戻る」と進むと、未適用の検索条件raw値を保持できません。正式境界試験では社員番号`777777`が復帰後に空となり、DB変更は0件でした。現在のStateCommand/OpenInputは未適用raw条件を渡す契約を持たないため、追加APIを独断で作らず後続の詳細設計へ引き継いでいます。この境界は合格扱いにしていません。[実測記録](build/test-results/design-boundary.json)と[正式試験](tests/Web/design-boundary.cjs)を参照してください。保存成功後にAppliedCriteriaで再検索する採用済みの帰路は、この未検索→取消の制限とは別です。

経歴書は固定取得時点の全案件と全文を2枚の表示シートへ出力し、先頭ゼロ・アポストロフィ・式に見える原文を文字列として保存/再読込検査します。ブラウザーの「ダウンロードを開始しました」は端末保存成功を保証しません。保存済みファイルには社員経歴が含まれるので保存先と共有範囲を確認してください。サーバーにはブックを恒久保存しません。

正式自己試験は `dotnet run --project tests/CareerManagement.Tests -c Release -- --cycle 1`（通常）、`--cycle 2`（境界・競合・障害を追加）、`--cycle 3`（全回帰）です。各回は **新しい** `SP2_WebFixture_Test_<乱数>` のみを作成し、DB所有markerを照合してその1件だけを最後に削除します。既存DBやブラウザー用DBを再利用しません。ローカルfixtureの自己署名SQL証明書だけ `TrustServerCertificate=True` を明示しています。製品既定へこの例外を持ち込んでいません。失敗結果も `build/test-results/self-cycle-N.json` に保存します。

最終公開物のブラウザー検査では、テスト専用 `--prepare-ui` が新しい `SP2_WebFixture_UI_<乱数>` と `.tmp/ui-runtime/profile.json` / HTTPS証明書を作ります。同プロファイルが残っていれば停止し、既存DBを再初期化しません。`tools/Start-Fixture.ps1 -ProfilePath .tmp/ui-runtime/profile.json -Published` で `build/publish` だけをHTTPS 7445に起動します。終了時は `tools/Stop-UIFixture.ps1 -DropOwnedDatabase` が生成DB名・所有marker・PID開始時刻・実行DLLを照合して自分の資源だけを終了します。ランダム秘密はGit除外領域だけへ保存し、配布・ログ・manifestへ含めません。旧 `--prepare-browser` の固定名fixtureはこの検査で再利用しません。

実装上の受渡し補足：EditVmの `removedCareerIds` はサーバー確認済み明示除去集合、`isNew` は番号欄の読取専用表示に使用します。停止確認MSG-038のYesだけ `X-SP2-Confirm-Stop: Yes` と改訂後StateRevisionで再送し、サーバーが同一の正規化入力/所有Stateとの一致を検査します。GET `/employees/edit?state=<乱数>` は表示専用で、URLに氏名/番号/経歴本文を含みません。その他の公開DTOは方式別共通契約に従います。

採用依存はSqlClient6.1.3/ClosedXML0.105.1、推移Pkcsのみ **10.0.13** を明示固定しました。2026-10-29の復元監査で旧Pkcs9.0.4がNU1902/1903となり、Microsoft公式の [GHSA-846f-f764-76mx](https://github.com/dotnet/runtime/security/advisories/GHSA-846f-f764-76mx) / [GHSA-2fmv-rv2c-59x7](https://github.com/dotnet/runtime/security/advisories/GHSA-2fmv-rv2c-59x7) と [修正版NuGet](https://www.nuget.org/packages/System.Security.Cryptography.Pkcs/10.0.13) を確認した補正です。監査やwarnings-as-errorsは無効化していません。依存ロックと今回のSBOM/検査記録を固定buildへ保存します。

入力版と実装対応は `build/generation/inputs.json` / `spec-implementation-map.json` を参照してください。今回のDEMO認証変更は `build/test-results/self-cycle-3.json` の47件と `demo-credentials-http.json` の14件、既存DBの限定移行は `demo-credentials-migration.json` へ対象版付きで記録します。仕様の設計採用・ソース生成・実行試験・独立レビュー・利用者受入・正式採点は別状態です。

今回のUI再生成では、採用済みUI条件をRazorの項目classとCSSへ反映しました。基準幅1366pxでは氏名260px・氏名カナ330px・日付150px、狭幅ではmax-widthで収縮し、文字は14px以上を維持します。実測前に仕様根拠から固定した [UI期待値](tests/ui-contract.json) と、最終publishをEdgeで測る [収集器](tests/Web/ui-observations.cjs) を共通ゲートで照合します。未知の文字部品・Tab到達不能の負例も検査します。公開物tree・入力・期待値・収集器・判定器のSHAが変われば以前のUI合格は使用できません。UI実測の標準保存先は `build/test-results/ui-observations.json` と `ui-conformance.json` です。今回の認証改訂ではUI再測定を行っておらず、旧publishのUI/ブラウザー/印刷PASSを最新として提示しません。共通UIゲートは未実施として失敗状態を記録します。

今回の認証・SQL検査の実施範囲とPH05 OPENは別状態です。以前の3回品質検査やUI検査を今回のPASSへ転用しません。入力・実装・検査の対応は [生成記録](build/generation/regeneration.json) と今回の固定build記録を参照してください。

この作業環境の既存DEMOは `https://localhost:7443` です。停止中は `./tools/Start-Fixture.ps1 -ProfilePath .tmp/runtime/profile.json -Published` で最新 `build/publish` を起動します。既存の専用profileと所有DBを使い、生成済み業務データを初期化しません。これは当リポジトリの明示DEMO環境向けであり、source-only ZIPの配備先は前述の通常初期設定で用意します。
