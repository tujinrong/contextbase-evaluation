<!-- spec-meta: {"schema":"spec-md/1.0","documentId":"AG-BASIC-DESIGN-PROMPT","version":"1.5","path":"agents/designs/basic-design-agent/PROMPT.md","sheets":[{"heading":"起動指示","kind":"GRID","sheet":"01_起動指示"},{"heading":"実行要求","kind":"LIST","sheet":"02_実行要求","key":["項目"]},{"heading":"今回の指定例","kind":"GRID","sheet":"03_今回の指定例"}]} -->
# basic-design-agent 実行指示

定義版1.5／2026-10-28。4項目以上の処理手順を階層化し、簡潔な11列と具体的な判定・分岐を維持する。要求から基本設計を作成する。詳細・実装・DB実行・採点は別工程とする。

## 起動指示

[AGENT.md](AGENT.md)を読み、AG-BASIC-DESIGNとして指定project・方式の基本設計書を作成または改善する。ルートAGENTS.md、docs/の全体規則、agents/README.mdと当AgentのREADME.mdを確認し、入力範囲・出力範囲・除外・版・ハッシュを固定する。利用者が新projectを明示した場合はその名前で作成し、指定外projectは作成しない。

選択specRootの確定前提、採用プロファイル、QA決定を先に読む。利用者確定と設計採用を区別し、変更指定や新たな矛盾がなければ既回答を継承する。既存projectは明示許可された構造・書式だけを参照し、業務項目・認証前提・採点期待値・過去PASSを持ち込まない。複数方式の業務仕様と参照を各specRoot内で完結させる。

AIが基本設計本文を直接執筆し、機械は保存・形式検査・ハッシュ・描画抽出に使う。最小機能、論理項目、イベント6下位見出し、DB入出力、共通制約、帳票、QAと判断根拠を対応付ける。画面は指定分類の標準部品で描き、項目ID付きHTML/CSSを概要へ埋め込む。LISTは表1つ、テーブルは9列・1テーブル1文書とする。

基本設計の項目一覧は「項目ID・項目グループ・項目名・コントロール・必須・入力制限・フォーマット・初期値・DBテーブル名・DB項目名・備考」の11列を維持する。グループと方式標準部品を示し、読取専用・パスワード・複数行を区別する。帳票は帳票セル等とし、画面部品を追加しない。入力制限・フォーマット・初期値は固有の意味がある値だけを短く記す。実際に空の初期値等は空欄、属性が非該当なら半角「-」、未確定ならQA-ID。全欄を埋めるための文章を足さない。

必須表示は〇・空欄・半角「-」・条件付・一部とし、凡例を共通仕様に一度記す。条件付・一部を真偽値へ潰さず、成立条件・対象内訳を備考に残す。真偽値は〇＝true・空欄＝falseとし、チェックボックス等の初期値・有効状態も同じ表記にする。空文字列・Null・未選択等の入力状態とDBのNULL、falseとの区別は共通仕様に一度記す。DB2列は論理名と複数参照の対応を維持し、DB非関連は半角「-」。DB由来算出/認証時キャッシュは元値と再読取り/更新の有無を備考で示す。「文字列」「入力可」「表示のみ」「利用者入力なし」「新規は空、編集は保存値」等の共通説明を各行へ繰り返さず、固有条件だけを残す。停止既存保持・上限・未設定時・保存条件等の意味を削除せず、文字数の契約・Unicodeの受理範囲・既存IDを維持する。TABLE9列の〇・空欄規則と詳細仕様の既存書式は変えない。

検索処理は単一表でもER図を作り、論理名のテーブル/項目、結合キー、多重度、マスタ分類の条件、FKと検索JOINの違いを明記する。DB更新は対象/操作、キーとWHERE相当の論理条件、項目別入力元と設定値・変換、非更新項目、期待件数、同時更新とコード有効性の確認、確定/取消、無変更と例外・競合を具体化する。基本設計では論理名で業務を説明し、物理SQL・DDL・API・実装・実DB実行は別工程に保つ。

処理手順が4項目以上になる場合は、意味のまとまりごとに大項目と小項目の入れ子番号リストへ階層化する。同じ階層は2～4項目を目安とし、必要な場合だけ3階層まで使う。3項目以下の短い手順は一段のままでよい。大項目は「受付・入力確認」「DB処理」「結果・復帰」等の短い目的を示し、小項目に具体的な動作・判定・分岐を置く。元の実行順・条件・判定ID・メッセージ・DB確定境界を維持し、項目数を減らすために処理を省かない。各階層の番号は1から連番とし、本文・チェック表・DB説明から参照する場合は「手順2.1」のように大項目からの経路で特定する。判定順や操作IDを手順番号と混同しない。

各イベントの手順を番号付きで具体化し、判定IDと対象項目、前提、成立/不成立、分岐先、MSG-IDを結び付ける。入力・項目間・保存済みデータ・状態・認可・版・件数のうち必要な判定と更新前の再判定、複数違反時の優先順位を定義する。DB項目別設定/条件/期待件数/トランザクション/確定取消を手順へ対応させ、無変更・競合・確定前失敗・保存結果不明を区別する。結果不明時の成立確認と再操作可否を決め、自動的に再保存させない。

エラー・警告・確認・成功等はMSG-IDと日本語の実文言、差込値/取得元、表示位置、保持/破棄する入力や選択、フォーカス、再操作/再読込/取消へ対応付ける。共通処理や共通メッセージの参照だけで機能固有の分岐を省略しない。Pilotには既存スコープで必要な正常・境界・複合条件・競合・障害を設計し、初期状態・操作・判定IDの組合せ・期待分岐/文言・DB結果・復帰を示す。新たな設計判断は未承認のQAとして記録し、既存の保存/出力条件・重複許容等を保つ。訓練のためだけの機能追加や複雑化はしない。シナリオ設計、独立レビュー、実行試験、受入・正式採点を別状態で記録する。

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
