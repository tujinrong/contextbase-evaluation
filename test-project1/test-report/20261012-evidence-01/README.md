# test-project1 新規試験・画面エビデンス

実行ID **20261012-evidence-01**、2026-10-12。対象は7方式の実装と、各方式に独立して用意した架空データです。修正前の失敗・画像は保持し、修正後の検証を別のphaseに記録しました。旧build-10の合格を今回の実行結果へ転記していません。

[画面エビデンスHTML](../../test-evidence/20261012-evidence-01/test-evidence.html)／[画像一覧](../../test-evidence/20261012-evidence-01/test-evidence.md)／[原画像の整合性](../../test-evidence/20261012-evidence-01/capture-integrity.json)／[JPEGデコード・HTML埋込み検証](evidence-decode-verification.json)。HTMLは原画像を内部に埋め込んだ単独ファイルです。各画像に日時、方式、修正phase、試験範囲、SHA-256を付けています。

43画像を保存しました。同一画像1件を区別した固有画像は42件です。43件すべてのJPEGを完全デコードし、HTMLに埋め込んだバイト列と原画像の一致を確認しました。修正前・途中段階・修正後の撮影を含むため、43件を機能合格の件数として扱いません。

## 実行結果と範囲

| 方式 | 今回実行した検査 | 実画面・データの範囲 |
| --- | --- | --- |
| VB.NET WinForms | 修正後に境界111、実Framework23、fixture15、実Show回帰18件がPASS | 3学生・2クラスの独立fixture。検索・0件・クリア・新規・編集・保存拒否・修正後初期位置を撮影。実SQLサービスは試験用同型アダプターに置換 |
| C# WPF | 初期phaseでCore96・境界102・実Framework27。最終R4でSmoke7・fixture15・実Window11状態がPASS | 3学生・2クラスの独立gateway。実XAML/VMによる検索・クリア・新規・編集・保存拒否・未所属条件の非活性。Core/CLR未変更部分の初期phaseとUI修正後の実行を別集計 |
| C# ASP.NET MVC | 初期phaseのCore96・fixture16、修正後の実HTTP/Controller/Razor42件がPASS | 3学生・2クラス・70コード。実MVC画面、検索・編集・新規・HTML必須入力・空エラー枠の修正後を撮影 |
| Vue + C# API | Core96、実HTTP/API44、fixture16件がPASS。Vue型検査成功 | 3学生・2クラス・70コード。実Vue/API画面、検索・編集・新規・HTML必須入力を撮影。ID 9007199254740993の文字列保持も確認 |
| COBOL | 実COBOL/Cホスト86、新規入力9、静的12、GnuCOBOL構文28、実HTTP3件がPASS。C bridge正式コンパイル成功 | 独立した架空入力3組。production CGIの401認証エラー・400不正要求エラーを撮影。正常CRUD画面は未実施 |
| AS400 RPG | production C補助35、新規入力9、静的89件がPASS | 独立した架空入力3組。IBM i処理系・Db2・5250端末がないため、RPG業務実行と画面撮影はNOT_RUN |
| Access | R5で業務137・関係21・配布19・初期状態10・検索連動21と実2プロセス競合がPASS。最終R6は通知58・ラベル1・フォーム/DAO13・配布19の91件がPASS。R5業務等のR6再実行は未実施 | 独立したローカルACEに3学生・1クラスをproduction入口で登録。実フォーム検索・登録・編集・入力エラーを撮影。R6実画面で中点3文字の修正を確認。配布用accdbは試験データなし |

WPF/VB/MVC/Vueのfixtureは永続保存を拒否します。画面の保存拒否は実SQLの入力検証・正常保存・監査・競合の合格証拠には含めません。fixtureの役割は画面の表示制御だけで、実Windows認証やDB認可の検証ではありません。実Framework検査は当方式のDLLをCLRで実行しており、SQL Server hostingを検査していません。

## 不具合修正

今回の画面実行・レビューで判明した不具合は実装原因と判定しました。原仕様の要件に従って修正しており、仕様書本文は変更していません。

| 方式 | 修正内容 | 再検証の根拠 |
| --- | --- | --- |
| MVC | エラー0件でも表示される空エラー枠を除去。実エラーと情報メッセージは維持 | [修正報告](../20261012-evidence-01-CSharp_ASPNET-after-fix.md)、実HTTP/Razor42件、08/09の修正後画像 |
| VB | 登録・編集画面の初期スクロールとフォーカス、Tab順を修正。readonlyメッセージをTab対象外に設定 | [修正報告](../20261012-evidence-01-VB.NET_WinForms-after-fix.md)、実Show18件、08/09の修正後画像 |
| WPF | 新規登録で空ClassIdを数値変換してクラッシュする問題、検索候補の「すべて」表示と選択保持を修正 | [新規登録修正](CSharp_WPF/ui-fix-r2-report.md)、[検索R3記録](CSharp_WPF/ui-fix-r3-results.json) |
| WPF | 未所属ON時の条件非活性、クラス解除警告W-STU-107の保持を修正 | [最終R4報告](CSharp_WPF/ui-fix-r4-report.md)、実Window11状態、07の最終修正後画像 |
| Access | MDBをaccdb拡張子で出力する形式指定、初期BooleanのNull、検索候補の「すべて」表示・順序・解除警告を修正 | [R5報告](Access-r5/README.md)、VBAコンパイル・実ACE・UI回帰、04〜07の検索/編集/登録画像 |
| Access | 実OSコードページ936のVBEで「・」が「?」になる文字化け。対象23文字だけChrWで保持 | [最終R6報告](Access-r6/README.md)、実VBA通知58件と仕様原文の完全一致、08の修正前と[09の修正後実画面](../../test-evidence/20261012-evidence-01/Access/09-invalid-date-after-final-fix.jpg) |

試験装置側のWPF resource URI、Access COM解放・PS5競合呼出し、CGIホストのCRCRLF解析も修正しました。これらの初回失敗ログはそのphaseのまま保持しています。修正前画像、途中の失敗、重複撮影を正常合格へ数えません。

## 個別報告・独立データ

- [VB初期phase](VB.NET_WinForms/README.md)、[修正後](../20261012-evidence-01-VB.NET_WinForms-after-fix.md)、[VB架空データ](../../srcs/VB.NET_WinForms/Tests/GuiEvidence/fixture.json)
- [WPF初期phase](CSharp_WPF/README.md)、[最終R4](CSharp_WPF/ui-fix-r4-report.md)、[WPF架空データ](../../srcs/CSharp_WPF/tests/GuiEvidence/fixture.json)
- [MVC初期phase](../20261012-evidence-01-CSharp_ASPNET.md)、[修正後](../20261012-evidence-01-CSharp_ASPNET-after-fix.md)、[MVC架空データ](../../srcs/CSharp_ASPNET/tests/EvidenceHost/fixture-data.json)
- [Vue今回試験](../20261012-evidence-01-Vue_CSharpAPI.md)、[Vue架空データ](../../srcs/Vue_CSharpAPI/tests/EvidenceHost/fixture-data.json)
- [COBOL今回試験](COBOL/evidence.md)、[COBOL架空入力](../../srcs/COBOL/tests/20261012-evidence-01/input-fixtures.json)
- [RPG今回試験](AS400_RPG/evidence.md)、[RPG架空入力](../../srcs/AS400_RPG/tests/20261012-evidence-01/input-fixtures.json)
- [Access R4記録](Access-r4/results.json)、[R5報告](Access-r5/README.md)、[最終R6](Access-r6/README.md)、[R6架空データと登録結果](Access-ui-r6/synthetic-data.json)、[配布用StudentManagement.accdb](../../srcs/Access/StudentManagement.accdb)

配布用Accessは最終R6の実ACE/accdb 1個です。FileFormat12、SELF、外部リンク0、学生・クラス・監査0、試験モジュールなしを確認しました。SHA-256は `D1777167FD7423BF4399F05D006519FD5A8E005A6FEF2E56B1A8F11AAD73EC87`。撮影は独立fixtureで行い、[撮影終了記録](Access-ui-r6-screen/ui-closed.json)でも原本不変を確認しました。

[終了確認](close-verification.json)で、撮影用MVC/Vue/COBOLのポート7441/7442/49191に待受がないこと、Access撮影fixtureの閉鎖と原本SHA-256の一致を確認しました。rootの終了確認スクリプトで生じた初回PS5構文エラーと修正は[別記録](close-verification-harness-fix.md)に保持しています。

## 未実施・構造問題

共有SQL ServerはWindows認証で稼働しています。[初期の読取検証](sql-readonly.json)と[最終の13条件の読取検証](sql-readonly-final.json)はPASSで、共有DB `contextbase_test_project1` の業務表・assembly・アプリroleは0件です。最終検査は4本のSELECTだけで、DDL/DMLは0件です。SQLへ学生・クラス・監査のテストデータは投入していません。

[共有DB移行中断報告](../../report/20261012-shared-sql-migration-stop.md)に記録したrole/SQLCLR競合、AccessのSELF/ACE契約、IBM i接続・認証・トランザクション契約が未確定のため、共有schema配備・SQL業務CRUD・監査・競合・実認可・Access/AS400のSQL接続は未実施です。構造変更による解決は別Agentの修正待ちです。IBM iのコンパイル・Db2・5250、Linux CGI配備、Office32bit、IME/DPIや切断/性能境界の網羅受入、仕様書逆生成・採点も未実施です。

変更範囲はagents/build-agentとtest-project1のみ。[最終隔離監査](isolation-audit-final.md)で855ファイル・1511参照に検出0件、補助検査の110プロジェクト項目/47 fixtureファイルに方式間参照0件を確認しました。仕様入力335件とDB資源31件はSHA-256不変です。各方式のソース・仕様・fixtureは独立しており、方式間参照や共通実装は導入していません。build-10の7方式ZIP/lockは旧改訂の凍結成果として保持しています。今回修正後の入力・出力は[生成報告](../../report/20261012-evidence-01-generation.md)と[出力manifest](../../report/20261012-evidence-01-outputs.json)を参照してください。
