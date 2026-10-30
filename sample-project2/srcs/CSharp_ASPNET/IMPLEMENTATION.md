# 今回のUI実装

実行sp2-ui-regenerate-20261029、方式CSharp_ASPNET、範囲ui_behavior。5画面6機能、認証・DB・原子保存・帳票/Excelの業務契約を継承します。

Razor SharedのLayout/PageHeader/FieldErrors/UiErrorがサイト枠・現在位置・見出し・ラベル・エラー状態を構成します。site.cssは役割別14px以上と個別幅、狭幅の縦配置、表内スクロールを担当します。自然なDOM順を使用し、正のtabindexで迂回しません。site.jsはJSON POSTのenvelopeから一度GETし、失敗時はDOM入力とGET URLを保持します。待機中は入力を止め元disabledを復元します。

既存ScreenStateStore内でraw4/適用条件/選択/scroll/検索専用immutable snapshot/所有State・lease/短期一回ticketを管理します。コピー先の変更は元liveStateを変更しません。社員の現在明細を含む保存は既存EmployeeServiceのトランザクション、コード保存は現在1件です。DB保存結果とticket/GET表示失敗を区別します。

認証なしの保護操作はCSRF検査の前に401/MSG-002へ分類します。有効認証は従来のCSRF検査必須です。権限・認証・DBを変更する新機能は加えていません。製品はOffice Automationを使用しません。

対応とSHAはbuild/generation/spec-implementation-map.json、UI期待値はtests/ui-contract.json、実観測/gateはbuild/test-results/ui-observations.json・ui-conformance.jsonです。部分実測/静的対応/ZIP再構築と正式受入を区別します。
