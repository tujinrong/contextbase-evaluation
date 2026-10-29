<!-- spec-meta: {"schema":"spec-md/1.0","documentId":"SP2-BUILD-REPORT","version":"1.0","path":"sample-project2-build-report.md","sheets":[{"heading":"実行条件","kind":"GRID","sheet":"01_実行条件"},{"heading":"Agentの問題","kind":"GRID","sheet":"02_Agentの問題"},{"heading":"別工程の問題","kind":"GRID","sheet":"03_別工程の問題"},{"heading":"検証結果","kind":"GRID","sheet":"04_検証結果"}]} -->
# sample-project2 ビルド報告

2026-10-29。実行ID `20261029-sp2-build`。両方式のソース生成と3回の検証・改善を実施した。本書は問題・処置・検査範囲・残件の最終記録であり、製品受入や正式採点を示さない。

## 実行条件

|項目|内容|
|---|---|
|対象|sample-project2 / Access、CSharp_ASPNET|
|入力|各方式の要件定義・基本設計・詳細仕様・採用規約・QA。通常preflightの入力manifestに版とSHA-256を固定する|
|出力|sample-project2/srcs/方式ID のソース正本、同 build/ の配布物・入力/出力manifest・今回の検査記録|
|品質要求|高。方式ごとに3回の検証・改善を行い、自己検証と独立検査を区別して記録する|
|凍結入力|Access61ファイル、CSharp_ASPNET60ファイル。入力版・全SHAは各 build/generation/inputs.json。最終メタデータ更新は project/build/final-input-refresh.json に記録し、各試験時の元入力SHAを改変しない|
|試験資源|新規の隔離DB、ACCDB実行コピー、試験fixtureのみ。既存業務データを初期化しない|
|正式評価|実装・試験の実測記録を作成する。利用者受入・正式評価は未実施、formalScore=null|

## Agentの問題

|ID|根拠・問題|影響|処置・状態|
|---|---|---|---|
|AG-01|build-agentの全project共通記述に、別題材で決めた共有SQL Server/Accessフロントエンド構成が固定されていた|sample-project2の独立ACE構成と認証要件を上書きする恐れ|AGENT/PROMPT/README 7.9で選択project・方式の採用プロファイルに従うよう修正済み|
|AG-02|固定入力が存在しないproject/docs/開発規約.mdを必須とし、7方式の固定一覧を走査していた|登録2方式の通常生成を開始できない|登録方式と方式内規約による選択へ修正。両方式通常preflight PASS。preflight回帰85 assertions通過|
|AG-03|詳細イベント検査が旧EV形式・01/02文書のみを対象としていた|F01〜F06の現契約を正しく検査できない|Fxx-Eyyと全対象詳細文書に対応。F06を含む回帰、両方式通常preflight PASS|
|AG-04|他projectへの案内リンクとコード内C#ジェネリック型を入力漏れ/HTML違反と誤検知した|正当な入力が構造検査で拒否される|案内リンクの範囲判定とコード内判定を修正。実HTMLの拒否を維持し回帰検査通過|
|AG-05|梱包・manifestにsample-project1/StudentManagement/7方式の固定値が残っていた|別題材の名前・成果物数で検証する恐れ|明示project・登録方式・実entrypoint/実ACCDB名で判定。梱包回帰14 tests、preflight回帰内のsample2配布照合が通過|
|AG-06|品質要求と改善回数を結果へ結び付ける固定記録がなかった|3回の実施根拠と対象版が曖昧になる|方式別 build/test-results/quality-cycles.json に入力・ソース版、試験、指摘、修正、再検査、未実施を記録する契約を追加済み|
|AG-07|独立配置・最終整合検査にも旧題材/7方式固定があり、VBAファイルが参照検査対象から漏れていた。新規の正式fixtureを既存入力の無断変更と誤認した|今回のソース/配布を正しく検査できない|明示project/方式・登録表・実成果物へ修正。VBAも検査し、欠落/破損記録はFAILで旧PASSを更新。Accessの正規seed-manifestもhash coverage必須で許可。独立配置8 checks、最終整合7 testsで検査|
|AG-08|toolsを一律除外していたため、Access再構築入口とWeb通常初期設定CLIがsource.zipから欠落した|原仕様なしで配布ソースを再構築・初期設定できない|profile.jsonのproductionHelpers完全相対ファイル宣言を導入。リンク/範囲外/テスト/不在等を拒否し、nested builder・Setupを含む回帰14 tests通過|
|AG-09|ファイル名にtestを含むという過剰な部分一致で本番StateStore.csも除外された|実Web ZIP別展開buildでSessionRegistry/State欠落のCS0234/CS0246を再現|単語境界/テスト命名による判定へ修正。14 testsと実Web ZIP別展開buildで再確認済み|
|AG-10|生成帳票の初期検査は原文往復・型・生成成功を中心とし、章配置/見出し11pt太字/色線・罫線/和文作成分時刻/完全Footerの照合が不足した|実装漏れを自己検査PASSだけでは検出できなかった。長文では実印刷の重なり・欠けも発生|両方式の帳票実装を補完し、独立OOXML契約、実Excelのページ境界、通常/最大データのPDF検査で修正を確認。目視は全頁contact＋代表頁拡大。各PASSは対象版・検査層だけへ適用|
|AG-11|Access初期化保護試験が期待VBAエラーをCOMへ直接発生させ、実行時エラーのmodalで停止した|再投入拒否の試験プロセスが終了せず、旧結果を最新候補の根拠にできなかった|専用fixtureのmodalを終了し、期待例外をVBA内で捕捉する試験wrapperへ修正。b9候補で再投入拒否/業務値不変とmanifest同一SKIP・変更STOPの4件を再実行PASS。所有プロセスだけを処理|
|AG-12|AccessのgBusyは後続ボタンを拒否するが、入力欄の操作と非Escキーを抑止していなかった|DoEventsを伴う待機中に編集中の値や選択が変わる恐れ。API層の待ち時間検査だけではUI要件を証明できない|blocking service中だけ入力を保護し、解除後に業務モデルの新状態を反映。独自19件と独立18件中のbusy3件で成功/失敗/取消、非Esc遮断・Export中Esc・readonly/編集可復元を確認。rootもd6のnative disabled状態を観察。物理キーの全再実行とは区別|
|AG-13|Accessの再生成JSONでstatusが未設定だった|ソースZIPの生成状態がNOT_RECORDEDとなり、最終工程状態を説明できなかった|最終状態GENERATED_VERIFICATION_CANDIDATE_WITH_TECHNICAL_DEVIATIONを明示し再梱包・別展開実構築済み。WebはGENERATED_WITH_OPEN_DESIGN_ISSUE。技術差分/未解決/未実施を全合格へ置き換えない|
|AG-14|処理中入力抑止を追加した5aaa候補で、clsUiBusyState.Public Releaseが既存メンバー識別子と衝突し、実使用時にコンパイルエラーとなった|DoCmd126と初期投入の通過だけでは、未使用classを含む全コードの実使用可能性を証明できなかった|5aaaを失敗版として記録しRestoreへ改名。126＋[Application.IsCompiled](https://learn.microsoft.com/en-us/office/vba/api/access.application.iscompiled)=True必須＋全class実初期化＋staging probe除去後再compileへ補強。[603](https://learn.microsoft.com/en-us/office/vba/api/access.acsyscmdaction)は当該COMで引数数エラーとなり未採用。最終d6と原仕様なし最終ZIP再構築の両方でgate/IsCompiled/一時probe不在を実確認|
|AG-15|Python補助/試験のimportが4か所の__pycache__をAccess正本の.tmp外へ作った。集約検査driverもAgent scriptsへ1個作った|固定配置の最終検査でWORK_OUTSIDE_TMPとなった|builderでprivate import前にbytecode生成を抑止し、READMEの全Python入口と集約driverを-B起動へ補正。検証した生成済み.pyc5個だけを除去、入力/正式試験/fixtureは保全。VBA/DB/候補d6と元実行SHAは不変で、helper変更はcache-only差分として別記し、新ZIPから再構築|

## 別工程の問題

|ID|担当工程|根拠・問題|実装への影響|処置・状態|
|---|---|---|---|---|
|PH-01|実行環境・配備検証|採用プロファイルはSQL Server 2022 Expressだが、現在の .\\SQLEXPRESS は実測17.0.5005.3 / Express Edition (64-bit)（2025）。登録instanceは当該1個で、2022 LocalDBも未導入|現環境の試験をSQL Server 2022実機の合格根拠にはできない|2025の専用fixture・互換性レベル160で検査済み。SQL Server 2022実機検証は未実施。採用プロファイルは変更しない|
|PH-02|詳細設計の依存採用・導入検証|設計対象SqlClient 6.1.3から推移取得したSystem.Security.Cryptography.Pkcs 9.0.4が初回restoreでNU1902/NU1903となった。公式advisory GHSA-846f-f764-76mx / GHSA-2fmv-rv2c-59x7|警告をエラーとして扱う条件でビルド停止。脆弱な推移依存のまま配布できない|SqlClient/ClosedXMLの設計対象版を維持し、Pkcs修正版10.0.13を明示上書き。再restore・監査・API/帳票回帰PASS。監査とTreatWarningsAsErrorsを維持|
|PH-03|Windows実UI検証環境|当初Computer Useのclick/activateがGetCursorPos failed: アクセスが拒否されました。(0x80070005)となり、画像もぼかし背景だった|ロック中はnative入力・目視を実施できなかった|利用者のロック解除後に再開。実キー/Ctrl+V/日本語入力/コンボ/日付/保存再読込/編集番号保護を7e6e155候補で実確認。4c1c7ffで5画面・careerタブ・検索無効化と表示修正、現d6でbusy時入力disabled/選択保持をnative観察。native-ui.jsonは版を分けて記録。物理IME変換と現版の全キー再実行は未実施|
|PH-04|実行環境・Access再構築互換性|実機Windows ANSI codepageは936。VBEへのAddFromStringで、UTF-8正本にある半角カナliteralが?へ変換された|コンパイル成功だけでは正本どおりの文字列を保証できない|再構築helperで非往復文字literalをUTF-16 ChrWへ変換し、UTF-8正本を保持。検索NFKCと実COMの再検査で修正を確認済み|
|PH-05|詳細設計・Web HTTP状態契約|詳細仕様F03の条件保持とF04取消の未検索復帰に対し、共通実装仕様23～24行のStateCommand/OpenInputは未適用raw条件を運ばない。社員番号777777を入力し検索せず新規→無編集取消で空へ戻ることを最終版の実ブラウザーで再現（DB変更0）|検索前に編集した条件が取消で失われる。検索済AppliedCriteriaによる保存後再検索は共通実装67行で別に明示されており、この問題と混同しない|OPEN / REQUIRES_DETAIL_DESIGN_FIX。SearchStateのraw/適用済条件の分離と、既存invalidate等のDTO拡張又は所有raw保存APIを詳細設計担当で補完する必要がある。勝手なAPI/仕様変更は行わず、当該境界を合格にしない。Web build/test-results/design-boundary.jsonへ再現を固定|
|PH-06|詳細設計への実機技術補足|Accessの協調2プロセスで認証失敗3から同時失敗してもDAO cacheにより最終4になる場合を検出。排他取得だけでは別processの最新確定値を保証しなかった|認証失敗の加算喪失、ロック条件未成立の恐れ|ゲート取得後・Tx前にDBEngine.Idle dbRefreshCacheを追加。実2processで最終5/ロック成立を確認し、独立3反復でも再確認。業務値を変えず実装で解消。詳細DB/排他の技術補足へ引継ぎ|
|PH-07|Access詳細設計・Excel印刷方式|F05のZoom=False/FitToPagesWide=1と手動改ページによる章・継続制御が衝突する。[Microsoft一次資料](https://support.microsoft.com/en-us/excel/scale-a-worksheet)はFit to使用時に手動改ページを無視すると明記|初回回避版b9でも計算幅504pt/Zoom100と実印刷可能幅に差があり、列Xが横2頁目へはみ出した（縦140区画に対し実PDF280頁）|実装で回避済み、詳細工程への修正依頼は継続。Normal書体/実幅486pt・Zoom100・H/V位置/総頁の保存再読戻し検査を採用し、17fb版で横1頁・最大135/通常2頁を実PDF確認。現d6の帳票moduleは同SHA。本文10.5pt以上と縦継続を維持し、低水準API指定の完全一致PASSにはしない。元specは変更しない|

## 検証結果

|対象|現在の実施状態|結果記録|
|---|---|---|
|Access|自己検査3回44/64/65件。最終d6aed17b候補でbusy独自19・独立18・最新全文OOXML18、全class初期化/IsCompiledがPASS。17fbの印刷境界21・全文18・書式3とroot実PDF最大135/通常2頁は同版へ固定し、現帳票moduleとのSHA一致を別記。4c版の実2process競合4/独立認証race3、b9初期化保護4等は旧版scopeの実証として保持。83項目/17イベント/43CHK/41Pilotの対応は全Pilot受入とは区別する|[方式別検査](sample-project2/srcs/Access/build/test-results/)、[監査](sample-project2/srcs/Access/build/test-results/independent-review/evidence-audit.json)、[印刷](sample-project2/srcs/Access/build/test-results/print-review/record.json)|
|CSharp_ASPNET|自己検査3回23/40/40件＋帳票書式追補40件、独立Application35/Infrastructure35件（既存17＋書式18）、HTTPS境界12件がPASS。UI/HTTP24件と実DL2ブックは書式補完前の対象版、HTTP/UIが同一の最終ReportService版0028c44では帳票を別途再生成し通常2冊各2頁・最大20経歴69頁を実Excel/PDF全頁目視PASS。文字列原文・LF・式に見える値・Unicode/先頭ゼロを照合。PH-05は未解決の別境界として保持|[方式別検査](sample-project2/srcs/CSharp_ASPNET/build/test-results/)、[印刷](sample-project2/srcs/CSharp_ASPNET/build/test-results/print-review/record.json)|
|Agentツール|preflight 85 assertions、梱包14 tests、独立配置8 checks、最終整合7 testsが使い捨てfixtureで通過。製品の実行合格とは区別する|[ツール回帰](agents/builds/build-agent/build/tool-tests/)|
|配布物|Access source.zip35ファイルを原仕様なしで別展開し、実ACCDB再構築・強化compile gate・一時probe不在・5画面/5表48列/初期件数をPASS確認。Web source.zip84ファイルは別展開Release build PASS、37ライセンス/noticeはソース/ZIP/publish全SHA一致。Access正本は検証用candidate、利用者秘密で初期設定した配布版とは区別。業務仕様変更なし|[Access ZIP](sample-project2/srcs/Access/build/source.zip)、[Web ZIP](sample-project2/srcs/CSharp_ASPNET/build/source.zip)、各方式 build/generation/outputs.json|

印刷の目視は全頁contactと先頭/中間/末尾の拡大、通常帳票の全頁を対象とした。文字列の全量一致は別のOOXML/API検査による。古いnative入力・認証競合・印刷を新しい候補で再実行した結果へ置き換えていない。[Access入出力](sample-project2/srcs/Access/build/generation/outputs.json)・[Web入出力](sample-project2/srcs/CSharp_ASPNET/build/generation/outputs.json) と [最終整合検査](sample-project2/build/test-results/final-integrity.json) により、凍結入力SHA、243最終ファイルのhash/網羅性、独立閉包・固定配置・Git対象/除外を照合済み（指摘0）。

未実施はSQL Server 2022実機、物理IME変換、別DPI/別Office・プリンタ、紙への実印刷、利用者秘密の伏字Form初期設定、電源断等の全障害条件、41Pilotの全条件・利用者受入・正式採点。PH-05の挙動は未解決、PH-07は実装回避済みの設計差分として残す。Web試験サーバーと所有Officeは終了し、Web専用fixture DBは保持した。通常配備DBを作成せず、既存利用者データを変更していない。
