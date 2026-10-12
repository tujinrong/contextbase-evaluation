# 試験画面エビデンス

test-project1 ／ 20261012-evidence-01

実際に保存された画面画像の一覧です。画像の存在・ハッシュ一致は、正常CRUD・共有SQL Server接続・権限検証の合格を意味しません。方式ごとの実行範囲と各撮影メモを参照してください。

検証済み画像 43件、異なる画像ハッシュ 42件、明示的な重複撮影 1件。

共有SQL Serverへの業務データ投入は移行停止のため未実施。画像原本のバイト列は変更していません。

[HTML一覧](test-evidence.html) · [画像整合性・件数 JSON](capture-integrity.json) · [試験報告 README](../../test-report/README.md)

## VB.NET WinForms

実フォーム・Presenterを独立した試験fixtureで実行。SQL接続はなく、SQL Server上の正常な保存・削除は未実施。

- [VB.NET\_WinForms/01-search-results.jpg](VB.NET_WinForms/01-search-results.jpg) — 撮影済み。撮影日時 2026-10-12T14:01:16.153Z、1336 × 893px。実production Form/Presenter、独立fixture、検索2件。在学/休学、日本語/和暦表示。具体ApplicationServiceのみtest adapter、SQLなし。 SHA-256: `e2eb3b7594f86fe4ecb1039d036c732c9bf238bba0bfb24985c626832369825b`

- [VB.NET\_WinForms/02-clear.jpg](VB.NET_WinForms/02-clear.jpg) — 撮影済み。撮影日時 2026-10-12T14:01:27.094Z、1336 × 893px。クリアを実押下し一覧0、未検索へ戻る。SQLなし。 SHA-256: `7fcc2603c545adcfd5786896552f9f0d35f91fa6f6afb01b83b52303a38a70a8`

- [VB.NET\_WinForms/03-zero-results.jpg](VB.NET_WinForms/03-zero-results.jpg) — 撮影済み。撮影日時 2026-10-12T14:01:41.405Z、1336 × 893px。TEST-NONEで実検索し0件、I-SRC-001。検索条件を保持。fixture/SQLなし。 SHA-256: `6aa9d9c19614645811d69362716b4643022dac6cbcce1e14bd0b61e7398dcd05`

- [VB.NET\_WinForms/04-new.jpg](VB.NET_WinForms/04-new.jpg) — 撮影済み。撮影日時 2026-10-12T14:02:21.046Z、1086 × 923px。本物Form/Presenterの新規画面。学籍番号空/性別未回答/在学。fixture backend、SQLなし。 SHA-256: `cff7b6c463d299285ab21b15c26293e16dcb32db0b7bf0ab53b2bb220260f904`

- [VB.NET\_WinForms/05-fixture-write-refused.jpg](VB.NET_WinForms/05-fixture-write-refused.jpg) — 撮影済み。撮影日時 2026-10-12T14:02:30.433Z、1086 × 923px。fixture backend保存拒否を画面に明示（FIXTURE-NO-WRITE / DB未接続）。この操作は実DBの業務入力検査/保存を検査しない。 SHA-256: `21ad00f97880845e1dd789b36e7531431fdfcda4b8171b3484ac04b8f1c5c593`

- [VB.NET\_WinForms/06-edit-initial-scroll.jpg](VB.NET_WinForms/06-edit-initial-scroll.jpg) — 撮影済み。撮影日時 2026-10-12T14:08:37.457Z、1086 × 923px。実編集起動直後、AutoScroll84で基本情報が上に隠れた状態。学籍番号disabled/既存値はAXで確認。初期フォーカスを調査・修正対象とする。fixture、SQLなし。 SHA-256: `c7843647123421f44667af7aef3535033ac7b71c07c2c68f20ba73246e5c0cb0`

- [VB.NET\_WinForms/07-edit-manual-scroll-top.jpg](VB.NET_WinForms/07-edit-manual-scroll-top.jpg) — 撮影済み。撮影日時 2026-10-12T14:08:45.401Z、1086 × 923px。実VB編集の上部を手動スクロールで表示。TEST-VB-001学籍番号固定、和暦/日本語/クラス値。fixture。 SHA-256: `af91012e0cad49d148d950d70080b39af1a0dae8bb790e9f113e8b9f0bd3de96`

- [VB.NET\_WinForms/08-new-after-fix.jpg](VB.NET_WinForms/08-new-after-fix.jpg) — 撮影済み。撮影日時 2026-10-12T14:19:02.243Z、1086 × 923px。修正後: 初期スクロール位置0、先頭の学籍番号が可視で入力フォーカス。実WinForms画面／独立fixture、SQL未接続。 SHA-256: `3aeb1dc6fe8128bfb49a97b5189a8d843acaafd6d171e5e3b8e2069bafb00576`

- [VB.NET\_WinForms/09-edit-after-fix.jpg](VB.NET_WinForms/09-edit-after-fix.jpg) — 撮影済み。撮影日時 2026-10-12T14:20:18.652Z、1086 × 923px。修正後: 編集画面は先頭から表示。学籍番号変更不可、氏名フォーカス、和暦20/05/15保持。実WinForms／独立fixture、SQL未接続。 SHA-256: `716e62f02ba0bbb61de148a7de35827db5ca1bfe4a865208969e4ed3778446c5`

## C# WPF

実WPF画面を独立した試験fixtureで実行。SQL接続はなく、SQL Server上の正常な保存・削除は未実施。

- [CSharp\_WPF/01-search-results.jpg](CSharp_WPF/01-search-results.jpg) — 撮影済み。撮影日時 2026-10-12T14:05:37.184Z、1306 × 893px。修正後実WPF検索Window/ViewModel、fixture2行、在学/休学、和暦、日本語。SQLなし。 SHA-256: `b382b09fc58e5495ed7580bb48d3a491eecfcd0da68d6082fe281d53bfd469db`

- [CSharp\_WPF/02-edit.jpg](CSharp_WPF/02-edit.jpg) — 撮影済み。撮影日時 2026-10-12T14:06:13.291Z、1086 × 872px。本物WPF編集画面、合成学生TEST-WPF-001。学籍番号編集不可、日本語/平成20年05月15日表示。fixture、SQL未実施。 SHA-256: `92580438cf592d4ba046c0dfe133a1e5b05bc7985571ce7c7ae4d9d041001ea7`

- [CSharp\_WPF/03-fixture-write-refused.jpg](CSharp_WPF/03-fixture-write-refused.jpg) — 撮影済み。撮影日時 2026-10-12T14:06:21.120Z、1086 × 872px。実画面にDB未接続/fixture保存拒否を表示、入力保持。SQL業務保存/ロール認証の合格ではない。 SHA-256: `526ed34649cbf7c165de7d577f964ade1f31a4bd2c167f23fff1dc5edbbdb80f`

- [CSharp\_WPF/04-new-after-fix.jpg](CSharp_WPF/04-new-after-fix.jpg) — 撮影済み。撮影日時 2026-10-12T14:07:25.138Z、1086 × 846px。実新規ボタンで開いた本物WPF画面。クラス選択の型変換例外を修正後、正常起動。空学籍番号/未回答/在学。fixture、SQLなし。 SHA-256: `59eb61ea3766b4d1184369b3a20da4d00447e817c0b1e3ffc30b464a8306b0c4`

- [CSharp\_WPF/05-search-after-fix.jpg](CSharp_WPF/05-search-after-fix.jpg) — 撮影済み。撮影日時 2026-10-12T14:20:34.125Z、1306 × 846px。修正後: 年度・学年・クラス・都道府県がすべてと表示。在学・休学2件表示、NULLフィルター意味維持。実WPF／独立fixture、SQL未接続。 SHA-256: `d318c2323dbf2fcb0caedb0d4fefcbdab454b3f6626faf6c6bb410a0f3e6408d`

- [CSharp\_WPF/06-clear-after-fix.jpg](CSharp_WPF/06-clear-after-fix.jpg) — 撮影済み。撮影日時 2026-10-12T14:20:40.532Z、1306 × 846px。修正後の実操作: クリアで未検索・一覧0行へ戻り、すべて表示と在学/休学の既定値を保持。実WPF、SQL未接続。 SHA-256: `1c11fd7f88b0b6fcd8f898c802fa1e20c5e405eb2877e015db03eb5a615b800a`

- [CSharp\_WPF/07-unassigned-after-final-fix.jpg](CSharp_WPF/07-unassigned-after-final-fix.jpg) — 撮影済み。撮影日時 2026-10-12T14:29:09.698Z、1306 × 893px。最終R4の実操作: 未所属ONで年度・学年・クラスがすべてへ解除され3ComboBoxが非活性。既存2件一覧は未反映表示を明示。実WPF fixture、SQL未接続。 SHA-256: `f45190dd79f3d65ced2c51f6321f11eb48d3208ff5fad76c1275b5ad904d70ce`

## C# ASP.NET MVC

実Controller・Razor Viewを独立した試験fixtureで実行。SQL接続はなく、SQL Server上の正常な保存・削除は未実施。

- [CSharp\_MVC/01-search-initial.jpg](CSharp_MVC/01-search-initial.jpg) — 撮影済み。撮影日時 2026-10-12T13:51:38.876Z、755 × 1387px。本物MVC Controller/View、Staff、fixtureサービス。初期画面は未検索、在学/休学ON、新規登録可。SQL接続なし。 SHA-256: `f35727024d554031bf7d775305343393ac11bd4e01fa0e7fcfb630bb65b28734`

- [CSharp\_MVC/02-search-results.jpg](CSharp_MVC/02-search-results.jpg) — 撮影済み。撮影日時 2026-10-12T13:53:36.159Z、755 × 867px。Staff、検索結果2件。在学/休学の仮名学生。BigInt IDの編集リンクを確認、fixture検索サービスでDB接続なし。 SHA-256: `93b4baacda3502f8f73e40c9261754dbe4db8760eb70cf379d22bde41f4bb263`

- [CSharp\_MVC/03-edit.jpg](CSharp_MVC/03-edit.jpg) — 同一画像あり。撮影日時 2026-10-12T13:52:24.798Z、755 × 1819px。本物MVC編集画面、fixture学生9007199254740993を損失なく読込。SQL接続なし、DB更新は未検査。 SHA-256: `e259d29895d4ed15a466710f64f42ae65ae169a0a5a2b0295fa029ba4e144d9d`。同一画像: [CSharp\_MVC/04-edit-lower.jpg](CSharp_MVC/04-edit-lower.jpg)

- [CSharp\_MVC/04-edit-lower.jpg](CSharp_MVC/04-edit-lower.jpg) — 重複撮影（DUPLICATE_CAPTURE）。撮影日時 2026-10-12T13:52:40.164Z、755 × 1819px。編集画面fullPageの再撮影。03と同一画像、下部の独立検証には05を参照。 SHA-256: `e259d29895d4ed15a466710f64f42ae65ae169a0a5a2b0295fa029ba4e144d9d`。同一画像: [CSharp\_MVC/03-edit.jpg](CSharp_MVC/03-edit.jpg)

- [CSharp\_MVC/05-edit-bottom.jpg](CSharp_MVC/05-edit-bottom.jpg) — 撮影済み。撮影日時 2026-10-12T13:53:09.721Z、755 × 867px。編集画面の実下部、Staffで更新あり/削除なし。保存済みJPEGをview\_imageで再確認し正常画像と確認。fixture/SQLなし。 SHA-256: `349811f096b777f9475e7ab493f03dc56d37a00f520e58ce0d726b164adedfe0`

- [CSharp\_MVC/06-new.jpg](CSharp_MVC/06-new.jpg) — 撮影済み。撮影日時 2026-10-12T13:53:53.259Z、755 × 867px。Staff、新規登録。必須項目空、在学が初期選択。SQL登録は未実施。 SHA-256: `6a76dd7558e1a977d165d6373f95bc7dcfc5b0ff52ade6818fb34bbb5a712741`

- [CSharp\_MVC/07-required.jpg](CSharp_MVC/07-required.jpg) — 撮影済み。撮影日時 2026-10-12T13:54:09.596Z、755 × 867px。空の登録を押下。HTML必須検査が学籍番号へフォーカスし登録要求を阻止。DB保存成功としては扱わない。 SHA-256: `7ba4b1fd2612f3bc51d36a6758b4fc66c69ba4d490fd586c039e601c8c6d9e1e`

- [CSharp\_MVC/08-after-fix-search.jpg](CSharp_MVC/08-after-fix-search.jpg) — 撮影済み。撮影日時 2026-10-12T14:06:47.984Z、755 × 867px。修正後の実MVC初期画面。空の赤エラー枠/空bulletが消えたことを実ブラウザーで確認。Staff、fixture、SQLなし。 SHA-256: `b88fb4de2805e3e940d0f5c8f1f577b71688d71f1de01119e06da7e64b0659ec`

- [CSharp\_MVC/09-after-fix-new.jpg](CSharp_MVC/09-after-fix-new.jpg) — 撮影済み。撮影日時 2026-10-12T14:07:00.700Z、755 × 867px。修正後新規画面。空validation枠が消え、必須入力の正常UIが維持。契約42件の新規再検査は別after-fix報告。 SHA-256: `3704479cbcc82f2a37c1e5aca21f3d9b90b37b4d0d6e8610c8582dd1666af55c`

## Vue + C# API

実Vue画面・APIを独立した試験fixtureで実行。SQL接続はなく、SQL Server上の正常な保存・削除は未実施。

- [Vue/01-search-initial.jpg](Vue/01-search-initial.jpg) — 撮影済み。撮影日時 2026-10-12T13:54:27.878Z、1265 × 712px。本物Vueアプリ+本物API Controller、Staff、方式内fixture。初期未検索、在学/休学ON。SQL接続なし。 SHA-256: `ee45b644994a4ef7ad9f4b8618d9590e678c838b5d79b7719ca7610b6447b349`

- [Vue/02-search-results.jpg](Vue/02-search-results.jpg) — 撮影済み。撮影日時 2026-10-12T13:54:40.319Z、1265 × 712px。Vue Staffの架空データ2件。在学/休学、文字列BigInt IDの編集。fixture検索、SQLなし。 SHA-256: `bdebe759130591ac78c4400feddf732c4b858d3f6ffb41281ce5534bd72dbb53`

- [Vue/03-edit.jpg](Vue/03-edit.jpg) — 撮影済み。撮影日時 2026-10-12T13:54:53.229Z、1265 × 712px。本物Vue編集画面、BigInt学生ID9007199254740993を保持、生年月日平成20年05月15日を表示。Staff、fixtureのみ。 SHA-256: `86eb51f0adff1c9a97ae94ad7e2ed9f01efb309fcecf88bf32c0e081c5ccaa8b`

- [Vue/04-edit-bottom.jpg](Vue/04-edit-bottom.jpg) — 撮影済み。撮影日時 2026-10-12T13:55:23.346Z、1265 × 712px。編集画面下部。Staff更新ボタンあり、削除なし。fixtureのDB更新は拒否、未試験。 SHA-256: `58c10f8362fbcd79599179e93e1002561a03149fba96847a568ec0fff8a55690`

- [Vue/05-new.jpg](Vue/05-new.jpg) — 撮影済み。撮影日時 2026-10-12T13:55:36.695Z、1265 × 712px。実Vue新規画面。必須空、在学初期選択。fixtureのみ、SQL未試験。 SHA-256: `63154a3643fe195e46b53c4e9295f0ee777afe0c3f02f151b406e1d37c8a15f4`

- [Vue/06-required.jpg](Vue/06-required.jpg) — 撮影済み。撮影日時 2026-10-12T13:55:50.507Z、1265 × 712px。空の登録押下でHTML必須検査が学籍番号にフォーカス。fixture/SQL保存は呼ばれていない。 SHA-256: `10b3afffa917a57bfc109fc7ced2fc0590d1922cbeea3dafdfba45e14e2bd60f`

## COBOL

実production CGIの401認証エラー・400不正要求エラーだけを撮影。認証済み正常CRUD画面はNOT_RUN。SQL接続・業務データ投入は未実施。

- [COBOL/01-authentication-error.jpg](COBOL/01-authentication-error.jpg) — 撮影済み。撮影日時 2026-10-12T13:55:56.397Z、1280 × 720px。production student.cgi.exeが生成した401画面 E-COM-001。認証無しでSQL接続前に拒否。正常業務画面/CRUD合格ではない。 SHA-256: `44010350acb5dce033812a539af9ced56ecd2eb7d10765044ddabd9abb59941e`

- [COBOL/02-request-error.jpg](COBOL/02-request-error.jpg) — 撮影済み。撮影日時 2026-10-12T13:56:12.320Z、1280 × 720px。production CGIの400 E-COM-003。不正なroleパラメータは拒否され、SQLなし。CGI要求境界のみ合格。 SHA-256: `1c5acd54ac252f9fb8fd60ad7ed00a774a2645e3c3666f1df5a71142af4aa925`

## AS400 RPG

IBM i実機がないため5250画面撮影はNOT_RUN。C補助処理のホスト試験は別の試験報告に記録。5250画面画像は生成しない。

NOT_RUN：IBM i / 5250の画像はありません。

## Microsoft Access

原本と区別したローカルfixtureで実フォーム・DAOを試験。形式指定や初期表示の修正前・途中段階の画像も保持し、メモで区別。最終修正後は実ACE/accdb形式。SQL Server接続・共有DB移行は未実施。

- [Access/00-fixture-guard.jpg](Access/00-fixture-guard.jpg) — 撮影済み。撮影日時 2026-10-12T13:45:15.530Z、427 × 194px。Fresh test fixture path rejected by old hardcoded path guard; actual VBA runtime dialog, failed attempt preserved (JPEG原画像、拡張子を実形式に合わせた。) SHA-256: `dd4d5ab795c53fc48f751f0de10725fa506390a69d3a21372c91a694d3c6066d`

- [Access/01-search-initial.jpg](Access/01-search-initial.jpg) — 撮影済み。撮影日時 2026-10-12T14:03:55.404Z、1906 × 1025px。修正前の実Access検索フォーム。MDB形式をaccdb拡張子で出力した不具合、NULLチェックのダッシュを発見。独立3合成学生/1クラス、SQLなし。 SHA-256: `f81d0d315f03cdb6e1cf1deff9451fefb29c819d6d3109b348b0b7c547006ed5`

- [Access/02-search-initial-after-fix.jpg](Access/02-search-initial-after-fix.jpg) — 撮影済み。撮影日時 2026-10-12T14:20:55.527Z、1906 × 1025px。修正後: タイトルにAccess 2007–2016形式。検索初期の卒業・退学・クラス未割当がFalse、在学・休学True。3架空学生・1クラスの独立ACE fixture、SQL未接続。 R4は形式・Boolean修正後で、候補のすべて表示は追加修正前。 SHA-256: `707209fe3b7638367b2148f95eafd865c659c55978cd14bb467221564c1f46ab`

- [Access/03-search-results-r4.jpg](Access/03-search-results-r4.jpg) — 撮影済み。撮影日時 2026-10-12T14:21:48.052Z、1906 × 1025px。R4: production検索が独立ACEへ照会し在学/休学2件を表示。原データ3学生、卒業1人を既定条件で除外。候補のすべて空表示は追加修正前。SQL未接続。 SHA-256: `5e28d2d354979157bfaac98406c11036b7455c486052e18f79c6d24058cf99f9`

- [Access/04-search-initial-final.jpg](Access/04-search-initial-final.jpg) — 撮影済み。撮影日時 2026-10-12T14:32:58.360Z、1906 × 1025px。最終R5: 正しいACE/accdb形式。年度・学年・クラス・都道府県すべて表示、在学/休学True、卒業/退学/未所属False。独立ACE fixture、SQL未接続。 SHA-256: `d10d0da0ad67c092dbe76bd80accb38c8cc2ac4c97b4db769de6b01043894b4e`

- [Access/05-search-results-final.jpg](Access/05-search-results-final.jpg) — 撮影済み。撮影日時 2026-10-12T14:33:32.108Z、1906 × 1025px。最終R5の実SearchClick: 独立ACEの3学生から在学・休学2件を照会、卒業1件除外。検索4候補すべて表示維持。SQL未接続。 SHA-256: `2878cd50558e51a22367b1e16f638e59dc1ff87b6fce37b7d05c33b324740065`

- [Access/06-edit-final.jpg](Access/06-edit-final.jpg) — 撮影済み。撮影日時 2026-10-12T14:33:59.936Z、1906 × 1025px。最終R5: 実検索一覧のTEST-ACE-001行をダブルクリックしてproduction編集フォームを開く。ACE読込の氏名・和暦20/05/15・所属・人数2/定員30・更新情報。保存は実行していない。SQL未接続。 SHA-256: `f7679d554826cf4fdbfa94e00014882671f9ccab26c91580729a846030ccf884`

- [Access/07-new-final.jpg](Access/07-new-final.jpg) — 撮影済み。撮影日時 2026-10-12T14:34:14.414Z、1906 × 1025px。最終R5: 実新規登録ボタンでproductionフォームを開く。入力空、性別未回答、在学、年度2026、クラス未選択、削除ボタン非表示。独立ACE、SQL未接続。 SHA-256: `93a45fdc51e19abde11d50cc6735266e0cb037fcefe84b3e71a6095a7cc31d11`

- [Access/08-invalid-date-r5.jpg](Access/08-invalid-date-r5.jpg) — 撮影済み。撮影日時 2026-10-12T14:34:48.243Z、1906 × 1025px。R5の実保存操作: 空入力でproductionの和暦入力検証E-DATE-001を表示し保存しない。メッセージの区切りが?に置換される文字化けを追加調査中。独立ACE、SQL未接続。 R6で文字化けを修正済み。修正後は09-invalid-date-after-final-fix.jpgを参照。 SHA-256: `475b08499ce3a443bf41bfa72b65f3101306df4f4a9f52e746913c037f85d6db`

- [Access/09-invalid-date-after-final-fix.jpg](Access/09-invalid-date-after-final-fix.jpg) — 撮影済み。撮影日時 2026-10-12T14:50:08.791Z、1906 × 1025px。R6最終修正後の実Access新規登録画面。空入力で保存を押し、E-DATE-001「生年月日の元号・年・月・日を確認してください。」を表示。3個の中点が仕様書と一致。使い捨てACE fixtureを使用し、SQL Serverへの登録は未実施。 SHA-256: `6eda85e1fe033ee17198358bd1664f381d06b429c00ca1a999880f70f4f740dc`

一覧生成日時：2026-10-12T14:50:45.241Z。JPEGの完全デコードと機能合否は、この一覧生成の検査範囲に含みません。
