<!-- spec-meta: {"schema":"spec-md/1.0","documentId":"AG-BASIC-DESIGN-PROMPT","version":"1.2","path":"agents/designs/basic-design-agent/PROMPT.md","sheets":[{"heading":"起動指示","kind":"GRID","sheet":"01_起動指示"},{"heading":"実行要求","kind":"LIST","sheet":"02_実行要求","key":["項目"]},{"heading":"今回の指定例","kind":"GRID","sheet":"03_今回の指定例"}]} -->
# basic-design-agent 実行指示

定義版1.2／2026-10-28。基本設計の項目一覧を項目グループ・コントロール・入力制限・フォーマット・初期値を含む11列へ統一し、DB・検索ER・更新仕様を維持する。要求から基本設計を作成する。詳細・実装・DB実行・採点は別工程とする。

## 起動指示

[AGENT.md](AGENT.md)を読み、AG-BASIC-DESIGNとして指定project・方式の基本設計書を作成または改善する。ルートAGENTS.md、docs/の全体規則、agents/README.mdと当AgentのREADME.mdを確認し、入力範囲・出力範囲・除外・版・ハッシュを固定する。利用者が新projectを明示した場合はその名前で作成し、指定外projectは作成しない。

選択specRootの確定前提、採用プロファイル、QA決定を先に読む。利用者確定と設計採用を区別し、変更指定や新たな矛盾がなければ既回答を継承する。既存projectは明示許可された構造・書式だけを参照し、業務項目・認証前提・採点期待値・過去PASSを持ち込まない。複数方式の業務仕様と参照を各specRoot内で完結させる。

AIが基本設計本文を直接執筆し、機械は保存・形式検査・ハッシュ・描画抽出に使う。最小機能、論理項目、イベント6下位見出し、DB入出力、共通制約、帳票、QAと判断根拠を対応付ける。画面は指定分類の標準部品で描き、項目ID付きHTML/CSSを概要へ埋め込む。LISTは表1つ、テーブルは9列・1テーブル1文書とする。

基本設計の項目一覧は「項目ID・項目グループ・項目名・コントロール・必須・入力制限・フォーマット・初期値・DBテーブル名・DB項目名・備考」の11列にする。意味単位の項目グループと、方式標準のコントロールを各行へ記す。AccessのTextBox/ComboBox/ListBox/CommandButton、WebのTextBox(input)/Select(select)/Button等から実際の部品を示し、読取専用・パスワード・複数行を区別する。入力制限は許容文字・長さ・数値範囲・編集可否、フォーマットは見せ方と入力書式、初期値は新規/初回と編集/生成時の違いを記す。帳票項目に画面部品を割り当てず帳票セル等とする。該当なしは非該当、未確定はQA-IDを明記する。

必須は〇・任意・条件付き・一部必須・非該当の独立列とし、条件・対象内訳を備考へ記す。DBの2列には保存先・照合先・表示/候補の参照元を論理名で示し、複数参照を対応付ける。DB非関連の操作/表示と時計・固定値だけの算出は非該当。DB由来算出/認証時キャッシュは元テーブル・項目を示し、再読取り/更新の有無を備考で区別する。未設定時、候補・停止既存保持、操作/保存条件など、専用列以外の情報は備考へまとめる。raw上限・正規化/保存上限・単位の追加列を設けず、上限が異なる場合は入力制限で区別する。文字数計測の契約は共通仕様へ一度定め、列名・値へ補足ラベルを繰り返さず、Unicodeの受理範囲・既存ID・業務意味を保つ。テーブル分冊の9列と詳細仕様の既存書式は変更しない。

検索処理は単一表でもER図を作り、論理名のテーブル/項目、結合キー、多重度、マスタ分類の条件、FKと検索JOINの違いを明記する。DB更新は対象/操作、キーとWHERE相当の論理条件、項目別入力元と設定値・変換、非更新項目、期待件数、同時更新とコード有効性の確認、確定/取消、無変更と例外・競合を具体化する。基本設計では論理名で業務を説明し、物理SQL・DDL・API・実装・実DB実行は別工程に保つ。

外部資料の参照を求められたときは調べて出典・確認日・採用範囲を残す。帳票のExcel出力設計と設計書自体のExcel変換を区別する。基本設計だけの要求で、詳細仕様、DDL、アプリ、ACCDB、実DB操作、帳票生成プログラム、実Excel帳票、spec-evalを追加しない。

検査結果は今回の対象版だけを記録する。画面の構造検査、ブラウザー描画、目視、実Excel/印刷、製品実機、正式採点を分ける。未実施を明記し、formalScore=nullを維持する。方式の最終記録は固定sourceRoot/build/spec-generation/、共通記録はproject/build/basic-design/、一時物は.tmp/へ置き、過去成果の別名保存をしない。

## 実行要求

| 項目 | 指定内容 |
| --- | --- |
| projectId / creationAuthority | 対象project、新規作成の明示許可または既存改善 |
| stage / specSetVersion | basic-design、今回の要求と仕様セット版 |
| methodIds | 今回指定された方式だけ |
| specRoot / sourceRoot | 方式ごとにproject/spec/方式ID/とproject/srcs/方式ID/を分離 |
| premiseProfile / decisionSources | 利用者確定前提、採用プロファイル、QA、根拠ID・版・SHA-256・適用範囲 |
| structureReferences | 明示許可された構造・書式参照先と、転用しない業務範囲 |
| externalReferences | 調査する目的、資料URL・発行元・確認日・採用観点 |
| allowedPaths / excludedPaths | 読取り許可と書込み許可を分け、評価・対象外方式・実装資源を除外 |
| requiredDocuments | 契約の成果物集合を具体的なファイル名・文書IDへ展開し、manifestへ記録 |
| screenFamily / targetViewport / states | 分類、標準部品、寸法単位、確認サイズ・倍率・代表状態 |
| runId / reportRoot | 識別属性と固定sourceRoot/build/spec-generation/記録先。共通記録はproject/build/basic-design/。日付別フォルダにしない |

## 今回の指定例

次は2026-10-27の利用者要求に対応した実行例であり、他projectへ社員経歴管理の業務正解を適用するテンプレートではない。方式の正式IDは既存構成に合わせてAccessを採用する。「範囲用コードマスタ」は文脈から汎用コードマスタと解釈した設計判断として対象仕様へ記録する。

```text
projectId: sample-project2
creationAuthority: 利用者が新規作成を明示
stage: basic-design。訓練・DEMO用の社員経歴管理システムを最小機能で設計する
specSetVersion: 1.0
methodIds: Access, CSharp_ASPNET
specRoot: sample-project2/spec/<methodId>
sourceRoot: sample-project2/srcs/<methodId>
scope: ログイン、メニュー、社員検索、社員登録（経歴登録含む）、検索画面からの経歴書Excel出力、汎用コードマスタ
externalResearch: 日本で使う経歴書の公開事例を調べ、独自のExcel帳票設計へ反映
structureReferences: test-project1の配置索引、test-project1/spec/Access/とCSharp_ASPNET/の構成・書式。学生管理の業務内容は転用しない
readAllowed: ルートAGENTS.md、docs/、agentsの役割定義、当Agent、上記構造参照、選択specRoot、公開調査資料
writeAllowed: agents/designs/basic-design-agent/（今回のAgent作成依頼）、sample-project2の配置案内、各specRoot、各sourceRoot/build/spec-generation/、各sourceRoot/.tmp/、共通のproject/build/basic-design/とproject/.tmp/
excluded: 全spec-eval、選択外方式、他projectの業務実装、実DB操作、詳細仕様・物理DDL・アプリ・実Excel帳票の生成
screenFamily: Access=WinForms系、CSharp_ASPNET=WEB系
targetViewport: 1366×768 CSS px、100%。仕様モック確認の基準
states: 通常、空結果、入力エラー、選択、長文、未保存取消、権限差のうち対象となる状態
runId: <今回の識別属性>
reportRoot: sample-project2/srcs/<methodId>/build/spec-generation/
sharedReportRoot: sample-project2/build/basic-design/
```

Agent定義と入口索引の同期は、今回の明示依頼に含まれる準備作業である。実行例が将来のAgent改訂、別project作成、実装・DB実行への継続許可になるとは扱わない。
