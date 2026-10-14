# Excel 3様式の再使用監査

2026-10-14、新run `20261014-nenkin-high-01`／AG-SPEC。コードと形式定義だけを確認。年金・n2framework業務入力、原仕様、評価資料、旧業務MDは読んでいない。

採用候補は Artifact Tool の公開APIを使う既存builderと、MDから文字列・図の対応を機械抽出する既存modelの作業コピー。旧PythonのOOXML作者経路は今回のExcel作者には使わない。

| 形式 | 今回の配置 | 候補と制限 |
| --- | --- | --- |
| 表紙 | O6:AU36。タイトルO6:AU9、属性O12:W14/X12:AU14ほか、枠外は無罫線 | 旧Artifact modelの位置を維持。表紙は最初3属性の抜粋で、全属性・ID・版・本文前置きは最初GRIDへ原順序で保持する。V2原添付の承認欄の業務値は新規に埋めない。 |
| 通常 | A:BJの62列、幅3。大見出しA:BJ、本文B:BJ | 旧Artifact modelの120列、本文21列開始、120固定の表配分を明示profileで変更。章分類はspec-meta宣言を維持。画像最大幅1100px。縮小後の可読性は実画像で別途確認する。 |
| 項目LIST | A:Jの10列。見出し1行目、データ2行目以降 | 項目一覧の列数10を必須化。1論理レコード1行、データ結合・長文レコード分割をしない。その他の明示LISTは元の列数・値・順序を維持する。 |
| TABLE特例 | 1文書1シート、9列 | schema1.1のHEADERとLISTを同一シートへ置く既存処理を維持。非該当空欄を埋めない。 |

今回の62列は利用者指定のV2様式であり、docs/MD構造・Excel変換規約.mdのプロジェクト配置設定120列を変更しない。新runのformatProfileに例外を明示した。

3罫線は、表紙の個別枠・通常全周medium＋見出し下double・LIST見出しmedium/detail thinを公開APIで保持する。初期範囲はformats clearとし、過去の`preset:none`描画不具合を再導入しない。枠外に罫線がないこと、結合領域の内部に不要な線がないことは実XLSX読戻しで再確認する。

先頭ゼロ、長いID、ISO/和暦表記、正規表現、`= + - @`等は元MD由来の仕様文字列として保持する。builderは文字列value＋number format `@`を使い、`=`と先頭アポストロフィのliteral処理を維持する。日付serialへの変換や和暦の独自補正はしない。式セル・型変換の拒否を独立OOXML検査で確認する。

図は同じMDの行範囲へ束縛されたrenderer PNGを公開images APIで埋め込み、媒体SHA・位置・元図IDをmodel/manifestへ保存する。画像化成功だけで内容合格とせず、原寸全領域・改ページ・縮小可読性を確認する。

元V2は62列配置と3罫線の参照には使えるが、章名分類、LISTのタイトル1行目/見出し2行目、長文レコード分割、HTMLの平文化、Mermaidの文字表示という契約差がある。この旧経路のテスト合格を今回のArtifact経路の合格へ流用しない。

## 準備済み証拠

- `candidate-preparation.json`：候補model/builder/profileのSHA、旧files前後不変、合成10件。
- `model-guard-probes-r01.json`：合成16件。62列の3形式、元LIST文字列、全preamble保存、単一LIST表・宣言順・シート名・TABLE9・画像幅上限を確認。安全境界とMarkdown parser関数は旧ASTと一致。
- JS構文検査のみ実行。Artifact Tool・provider・marker・実XLSX作成・既存outputの変更は0。

## 実納品前の残件

bundled Pythonには`markdown_it`と`bs4`が提供されていない。実MD parserの実行はまだ行っていない。解析専用の不足依存を固定SHAで使う経路を、Excel作者のbundled Node依存と分けて記録する必要がある。

印刷設定の公開APIはquick referenceで確認できていない。利用者の会話内で限定承認されたPRINT_METADATA_ONLY接続はfresh helperを別途準備中。印刷範囲・向き・余白・繰返しだけを変更し、セル値/型/罫線/画像/結合と非印刷ZIP内容を不変にする。旧のworksheet全体再serializeをそのまま流用しない。

Excel内メタ情報の保存方法は未実装。現状は外部model/manifestの文書ID・版・元パス・元SHA・シート順・元図source bindingで追跡する。元MDの業務情報を隠し情報だけへ移さない。

文書計画件数の確定後に、新runのArtifact authoring markerをrootと同期して一度だけ実行する。旧11件markerは反復しない。実XLSXの全値/空欄/型/列順/3罫線/図/印刷設定と全シート原寸表示を確認するまで形式納品合格にはしない。
