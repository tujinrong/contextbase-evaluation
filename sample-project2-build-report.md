<!-- spec-meta: {"schema":"spec-md/1.0","documentId":"SP2-BUILD-REPORT","version":"2.0","path":"sample-project2-build-report.md","sheets":[{"heading":"実行条件","kind":"GRID","sheet":"01_実行条件"},{"heading":"工程の状態","kind":"GRID","sheet":"02_工程の状態"},{"heading":"検証の範囲","kind":"GRID","sheet":"03_検証の範囲"}]} -->
# sample-project2 再生成・追加品質対応

2026-10-30。実行ID `sp2-ui-regenerate-20261029`。関連Agentへタイトル・文字と入力高・日本語文字コードの規約を横展開し、Accessの文字コードを修正して配布候補を更新した。**文字コードの確認と、画面レイアウト全体の完成は別であり、全体UIは未完了。** タイトル拡大・入力高の全面再設計は今回は実行していない。

## 実行条件

|項目|内容|
|---|---|
|元の依頼|sample-project2 / Access・CSharp_ASPNETの基本設計→詳細設計→実装。要件の業務条件は継承|
|今回の追加|関連Agentの改善と、AccessのCP932修正・実行/表示確認。DQA-UI11/DQA-ENC01へ確定指示を保持|
|Agent横展開|要件規則、基本/詳細の契約・規則・工程、build契約/生成チェック、共通Access品質規約の計10文書|
|保全|5表48列の全typed row/schema・認証情報を保持。seed/資格情報resetなし。他project・Web製品は更新しない|
|配置|方式別specRoot/sourceRoot、固定build/、試行.tmp/、履歴Git。commit/pushは実施していない|

## 工程の状態

|工程|状態|
|---|---|
|既実行の基本・詳細設計|元の要求に対する記録を保持。今回のタイトル/入力高要求へ全面改訂済みとは扱わない|
|Agent改善|タイトル18pt標準/最低16ptかつ本文より4pt以上、Label/Header高も連動。TextBoxは実フォント行高＋上下余白＋境界から算定。全Form/Page/Dialogへ同種指摘を展開|
|文字コード修正|VBA正本33ファイルをCP932（Windows版Shift-JIS/BOMなし）、VBE輸送をASCII/正確なChrW式へ。Form native exportはUTF-16 BOM、文書/Python/JSON・業務データUnicodeを保持|
|Access候補|[CareerManagement.accdb](sample-project2/srcs/Access/build/CareerManagement.accdb) SHA4629fe0c…acab0fc、[source.zip](sample-project2/srcs/Access/build/source.zip) 47member。文字コード確認済み/全UI未確認の候補|
|Web|publish SHAaad4998c…deca4を変更していない。前回の363rule/1017propertyは元の対象版/規約での結果で、新Agent改訂後の再評価ではない|
|残る設計/実装|タイトル/入力高の基本→詳細→期待値→画面への全面反映、正常入力/離脱/Tab/同値マウス選択等。新規約/QAの通常入力再凍結も必要|

## 検証の範囲

|対象|今回の確認と限界|
|---|---|
|文字コード|Office UI=1041（日本語）、Windows ACP=936を実取得。33モジュールの意味一致/ASCII輸送readback、11文字列の実行＋export/reimport、4MSG・5Formの文言を確認。[詳細](sample-project2/srcs/Access/build/test-results/japanese-encoding.json)|
|実画面|5Form/6表示（ログイン/メニュー/検索/社員基本/経歴/コード）で日本語文字化けを観測しなかった。準備は通常業務API、見た目は実Accessで確認。ログインへの入力/送信なし。全操作や他環境の合格ではない。[実画面記録](sample-project2/srcs/Access/build/test-results/root-native-resume-review.json)|
|タイトル/高さ|実値は全5タイトル11pt/330twip。利用者の指摘を残し、文字コード修正で改善済みとしない。18pt等の新設計とTextBox高の組合せはDQA-UI11の後続再設計|
|回帰とデータ|境界単体11件、業務API67件、認証39件、11class初期化/probe除去再compileを確認。既存データ/資格情報保持、全所有プロセスは今回記録の終了0を確認|
|ソース配布|現47member ZIPを原仕様/試験なしで別展開し、通常build/初期設定/compile/所有Office正常終了。CP932 payloadとGit変換規則を確認。[再構築](sample-project2/srcs/Access/build/test-results/source-package-rebuild.json)|
|規約検査|改訂10文書のpath/版/H2-sheets/ローカルファイル参照を確認。構造検査で意味/実機/受入を代替しない。[Agent改訂](agents/builds/build-agent/build/access-ui-quality/typography-encoding-adoption.json)|
|未実施|全UI契約の再観測、属性/描画/操作の網羅、物理IME/clipboard/倍率/Dialog、同値マウス確定、現版Tab2110回帰、全帳票/印刷、Windows ACP932の別環境とVBE自体の表示条件|
|判定|正式ui-observations/outputsは未発行。旧0810の属性475/Pending129/PDF等を新4629の合格に流用しない。正式受入・採点は未実施、formalScore=null|

新規約の採用は後続生成へ引き継ぐ。現在の候補・ソースZIP・検査記録と、未実施のレイアウト再設計を区別した継続地点である。
