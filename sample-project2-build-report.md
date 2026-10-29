<!-- spec-meta: {"schema":"spec-md/1.0","documentId":"SP2-BUILD-REPORT","version":"1.2","path":"sample-project2-build-report.md","sheets":[{"heading":"実行条件","kind":"GRID","sheet":"01_実行条件"},{"heading":"Agentの問題","kind":"GRID","sheet":"02_Agentの問題"},{"heading":"別工程の問題","kind":"GRID","sheet":"03_別工程の問題"},{"heading":"検証結果","kind":"GRID","sheet":"04_検証結果"}]} -->
# sample-project2 ビルド報告

2026-10-29。実行ID `20261029-sp2-demo-login`。今回の資格情報変更は完了。Access・ASP.NETとも `admin / 123`、`staff / 123` を使用する。既存業務データを初期化せず、対象2利用者の認証列だけを移行した。レイアウト改修・実キー・印刷・正式受入は今回の検証範囲に含めない。

## 実行条件

|項目|内容|
|---|---|
|対象|sample-project2 / Access・CSharp_ASPNET。利用者が明示したDEMO資格情報変更のみ|
|確定条件|QA-025 / DQA-AUTH01 / 各方式の規約/DEMO認証条件.md。admin=ADMIN、staff=STAFF、共通初期パスワード123。入力長3～128 Unicodeスカラー|
|既存データ|内部user_id、role、社員・経歴・コード・分類・監査値を保全。全量seed・表再作成なし|
|新規データ|SP2-DEMO-01 v1.1は新規の空のDEMO環境向け。既存DBへの認証移行を全量v1.1投入済みと扱わない|
|暗号方式|Accessの既存CNG/PBKDF2-SHA256/600000、Webの既存IdentityV3/100000を維持。DBはソルト付き検証情報のみ|
|凍結入力|Access65 / Web63 / 集約108。方式別build/generation/inputs.jsonへ文書版・SHAを固定。仕様24文書の変更は各spec-update.jsonへ記録|
|配置|最終ファイル・今回証拠は固定build/、中間・実行copy・失敗harnessは.tmp/、履歴はGit|

## Agentの問題

|項目|今回の処置|
|---|---|
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
|Web最終publish|treeSHAd0d6b6fa…/104files。SQL47件・最終publish HTTPS認証14件PASS。所有/衝突拒否・Commit前再確認・2行書込み後rollback、旧ID/旧秘密拒否・CSRF・管理者/担当者権限を確認|[検査まとめ](sample-project2/srcs/CSharp_ASPNET/build/test-results/credential-update.json)、[HTTP](sample-project2/srcs/CSharp_ASPNET/build/test-results/demo-credentials-http.json)|
|Web既存DB|明示された所有DEMO DB SP2_WebFixture_20261029のみ移行。社員6/経歴6/コード12/分類3と他利用者全値digest不変。2回目は0変更SKIP。元seed版のmanifestがないため、元版を断定せずauth-only系譜として記録|[移行](sample-project2/srcs/CSharp_ASPNET/build/test-results/demo-credentials-migration.json)|
|Web配布ソース|ZIP86件のoriginal/member/archive全SHA一致、原仕様・試験期待値なしの別展開Release build PASS|[ソースZIP](sample-project2/srcs/CSharp_ASPNET/build/source.zip)、[配布検査](sample-project2/srcs/CSharp_ASPNET/build/test-results/source-package-validation.json)|

Accessは[CareerManagement.accdb](sample-project2/srcs/Access/build/CareerManagement.accdb)を開いて利用する。Webは最終publishの[https://localhost:7443](https://localhost:7443)をDEMO用に起動した状態。実行主体・URLは[稼働記録](sample-project2/srcs/CSharp_ASPNET/build/generation/demo-runtime.json)で確認する。

今回の入力・製品・証拠・ZIPのSHAは両方式build/generation/credential-update.json、集約状態はsample-project2/build/generation/regeneration.jsonへ固定した。UI適合の再実行と全体outputs manifestの確定は別工程として未完了。ネイティブ実キー/IME・別DPI・実SQL Server2022・紙への印刷・全Pilot/正式受入・採点は未実施、formalScore=null。sample-project1の既存ACCDBは開始時SHAと一致し変更していない。
