<!-- spec-meta: {"schema":"spec-md/1.0","documentId":"SP2-BUILD-REPORT","version":"1.3","path":"sample-project2-build-report.md","sheets":[{"heading":"実行条件","kind":"GRID","sheet":"01_実行条件"},{"heading":"Agentの問題","kind":"GRID","sheet":"02_Agentの問題"},{"heading":"別工程の問題","kind":"GRID","sheet":"03_別工程の問題"},{"heading":"検証結果","kind":"GRID","sheet":"04_検証結果"}]} -->
# sample-project2 ビルド報告

2026-10-29。今回の実行ID `20261029-sp2-vs-debug` はASP.NETのVS2026起動不具合を修正した。実際のVS Debugホストと最終Release publishの両方で `admin / 123`・`staff / 123` のログイン、メニュー、社員画面、管理者/担当者権限を確認し、既存5表の全値digestは不変だった。Accessは前回 `20261029-sp2-demo-login` の成果物を保持し、今回変更・再試験していない。レイアウト改修・実キー・印刷・正式受入は今回の検証範囲に含めない。

## 実行条件

|項目|内容|
|---|---|
|対象|今回はsample-project2 / CSharp_ASPNETのVS2026起動設定。Accessの前回認証変更は成果物・実行IDを区別して保持|
|確定条件|QA-025 / DQA-AUTH01 / 各方式の規約/DEMO認証条件.md。admin=ADMIN、staff=STAFF、共通初期パスワード123。入力長3～128 Unicodeスカラー|
|既存データ|内部user_id、role、社員・経歴・コード・分類・監査値を保全。全量seed・表再作成なし|
|新規データ|SP2-DEMO-01 v1.1は新規の空のDEMO環境向け。既存DBへの認証移行を全量v1.1投入済みと扱わない|
|暗号方式|Accessの既存CNG/PBKDF2-SHA256/600000、Webの既存IdentityV3/100000を維持。DBはソルト付き検証情報のみ|
|凍結入力|今回Web63。build/generation/inputs.jsonへ版・SHAを固定。仕様本文の変更なし。前回認証仕様24文書の変更履歴は各spec-update.json|
|配置|最終ファイル・今回証拠は固定build/、中間・実行copy・失敗harnessは.tmp/、履歴はGit|

## Agentの問題

|項目|今回の処置|
|---|---|
|VSのDB接続設定不足|slnxは7参照すべて正常。VSのSQL例外はSSL対象名の不一致。専用helperが既存DEMOの接続をDevelopment起動プロファイルへ明示し、キー保存先をuser-secretsで設定。通常配備の厳格TLS既定とWeb起動時のDDL/seed禁止を維持|
|認証失敗の内部原因が見えない|認証外向けメッセージは維持し、VS出力へ内部の例外型・DB provider数値コードだけを記録。秘密・SQL・接続文字列をログへ出さない|
|デバッグ操作|ログインを止めていた既存ブレークポイントを無効化。操作中の未保存一文字はUndoで復元し、AccountController.csの差分なしを確認|
|旧12文字下限と指定123が衝突|sample-project2に限り最小3へ明示変更し、認証サービス・フォーム検査・新規seed・CLI・仕様・試験を整合|
|旧ランダムDEMO資格情報|通常の新規DEMO生成はadmin/staff123を採用。既存データは所有者・安定ID・role・login衝突を検証し2行のみ更新|
|既存データを含むAccessが開かれていた|検証候補を先に作成。利用者の保存・閉鎖回答後、閉鎖時の最新49db0f92候補から再準備して置換。元業務値を保持|
|試験VBAモジュールの保存待ち|失敗した専用copyだけを終了し.tmpへFAIL保存。明示モジュール保存を追加し、新copyで39項目・正常終了を確認。失敗試行をPASSへ流用しない|
|確定直前の所有確認|Web移行のUPDATE前とCommit直前で所有を再確認。2行書込み後の故障注入と完全rollbackを追加|
|変更の追跡|明示的認証変更のexact-file保護検査を追加。HEAD/current/frozen SHA・利用者指示・理由の検査を保った17件回帰PASS。利用者の並行Git commit・Agent更新を保全|

## 別工程の問題

|ID|状態|
|---|---|
|PH-05|Webの未検索raw条件→新規→無編集取消の条件保持は既知OPEN。今回UI再検査なし、修正済みにしない|
|PH-07|Access帳票のFit Toと手動改ページの設計差分は継続。既存実装回避を維持、今回印刷再検査なし|
|UIレイアウト|案件名の切れ・対象社員表示・反映/保存の分かりやすさ等、利用者画像レビューの指摘は今回未改修。旧候補のUI/印刷PASSは.tmpへ失効し、資格情報変更後の合格へ転記していない|

## 検証結果

|対象|今回の実測|記録|
|---|---|---|
|Access最終ACCDB|SHA01b81b1d…、最終copy39/39PASS。admin/staff123、フォームの入力検査→イベントAPI→メニュー、旧ID/旧秘密拒否、1/2/129拒否・Unicode境界、塩分離・独立PBKDF2、ロック・役割を確認。全class初期化/126/IsCompiled/probe除去、所有Office正常終了|[認証](sample-project2/srcs/Access/build/test-results/credentials.json)、[移行](sample-project2/srcs/Access/build/test-results/credential-migration.json)|
|Access配布ソース|ZIP35件を原仕様・試験期待値なしで別展開し実ACCDB再構築。新規seed1.1・認証39/39PASS、再構築/試験Office終了コード0。元最終ACCDB不変|[ソースZIP](sample-project2/srcs/Access/build/source.zip)、[再構築](sample-project2/srcs/Access/build/test-results/source-package-rebuild.json)|
|Web VS2026|実VSホストのPID・開始時刻・Debug DLL SHAへ結合し、admin/staff123、認証cookie/CSRF、メニュー、社員画面、コード権限を確認。既存5表不変|[VSログイン](sample-project2/srcs/CSharp_ASPNET/build/test-results/visual-studio-login.json)|
|Web最終publish|Release build/publishを実行し、最終製品の別ホストでも同じログイン・権限・既存5表不変を確認。前回SQL47件/HTTP14件を今回候補のPASSへ流用しない|[配布物ログイン](sample-project2/srcs/CSharp_ASPNET/build/test-results/published-login.json)、[今回生成記録](sample-project2/srcs/CSharp_ASPNET/build/generation/regeneration.json)|
|Web既存DB|明示された所有DEMO DB SP2_WebFixture_20261029のみ移行。社員6/経歴6/コード12/分類3と他利用者全値digest不変。2回目は0変更SKIP。元seed版のmanifestがないため、元版を断定せずauth-only系譜として記録|[移行](sample-project2/srcs/CSharp_ASPNET/build/test-results/demo-credentials-migration.json)|
|Web配布ソース|今回のZIP87件を原仕様・試験期待値なしで別展開し、locked Release build PASS。最終SHAは方式別source-packages.json|[ソースZIP](sample-project2/srcs/CSharp_ASPNET/build/source.zip)、[配布検査](sample-project2/srcs/CSharp_ASPNET/build/test-results/source-package-validation.json)|

Accessは[CareerManagement.accdb](sample-project2/srcs/Access/build/CareerManagement.accdb)を開いて利用する。Webは[VS起動のログイン](https://localhost:61184/account/login)と[最終publishのログイン](https://localhost:7443/account/login)を起動した状態。実行主体・URLは[稼働記録](sample-project2/srcs/CSharp_ASPNET/build/generation/demo-runtime.json)で確認する。

今回のWeb入力・製品・証拠・ZIPのSHAはbuild/generation/regeneration.jsonへ固定した。Accessの認証検査39項目・再構築結果は前回の同一ACCDB版の記録であり、今回再実行した結果ではない。UI適合の再実行と全体outputs manifestの確定は未完了。ネイティブ実キー/IME・別DPI・実SQL Server2022・紙への印刷・全Pilot/正式受入・採点は未実施、formalScore=null。今回の対象外方式・DBは変更していない。
