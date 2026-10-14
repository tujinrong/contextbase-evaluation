# 納品形式の準備調査

後続の実ファイル変換器QAは[REPAIR-QA-R09.md](REPAIR-QA-R09.md)と[機械・全画像レビュー記録](repair-qa-final-r09.json)に保存した。検索基本candidate03は最終書式不合格のため、派生候補を正式納品へ採用していない。以下は準備時点の調査記録。

調査日: 2026-10-13。対象工程: ASP.NET再実施の不変AI Markdownから派生形式への変換準備。原仕様・spec-eval・原アプリは参照／実行していない。原稿、ソース、AI実行コードの変更、実納品PDF／XLSXの作成は未実施。

この文書は最初の調査記録。後続の補助実装と利用手順は[IMPLEMENTATION.md](IMPLEMENTATION.md)に記載する。実稿での作者実行・全ページ／全sheet視覚QAは未実施。

結論: 既存の配置・静的描画・XLSXパッケージ検査は再利用できる。一方、現行AI原稿の形式と従来docsiteの上位変換器には互換差があり、`docsite build/pdf/excel`の単純な一括実行で最新様式に合格するとは扱えない。

## 配置と固定

採用稿11件のID・相対パス・Markdownのbytes SHA256・source snapshot SHA256・draft-result SHA256・描画結果SHA256を固定する。新しい作業領域の`output/md/`へ採用稿をbytesコピーし、全形式で同じ相対階層とstemを用いる。例: `基本設計書/01_学生検索画面.md`に対して`output/html/基本設計書/01_学生検索画面.html`、`output/PDF/基本設計書/01_学生検索画面.pdf`、`output/Excel/基本設計書/01_学生検索画面.xlsx`。同じstemの基本／詳細は階層で区別する。

正本MDは変換都合で編集しない。派生物のためのHTMLメタ情報、印刷CSS、画像配置、章とセルの対応は別の変換モデル／manifestへ記録する。AI本文・Mermaid原文・HTML原文・項目値・順序を保持し、変換処理は業務説明を追加しない。試行の失敗・検査・未対応は納品仕様の本文と分けて本report配下へ保存する。

## 現行経路と互換差

| 経路 | 利用できる機能 | 今回の注意点 |
| --- | --- | --- |
| `contextbase.ai.rendering.render_document` | 不変MD検査、静的HTML、画面PNG、隔離された信頼済みMermaidによるSVG/PNG、原稿行位置とハッシュの記録 | 入力JavaScriptを実行せず外部通信を拒否。`structure=PASS`、`display=PASS`、除去要素なし、全図／画面のPASSを確認してから使う。描画成功と意味／視覚合格は別。 |
| 今回の`render_pinned.py` | capsuleとdraft-result照合、原稿不変検査、原stem HTMLコピー、render-pins | 生成物は文書ごとの新規フォルダ。採用稿選択後にmanifest付きで納品階層へ配置する。 |
| `docsite build` | `output/md`から同じ階層のHTML、索引、ローカル画像、MDハッシュ、リンク検査 | Graphvizの厳密な限定構文を使用。現AIのMermaid構文すべての互換性は未確認。旧安全検査はformとmeta、非`.screen-layout`のCSSを拒否するため、現AI稿をそのまま渡せるとは限らない。AI rendererの安全なHTMLを優先する。 |
| `docsite.pdf` | HTMLからオフラインPDF、用紙・改ページ・日本語文字検査、項目表セル文字列照合、入力HTML/MDハッシュ照合、全件成功後の段階入替 | HTML内の`docsite-source-sha256`が必須。AI renderer HTMLにはこのmetaがない。WeasyPrintは今回のCPython3.12環境にない。旧`docsite check`はAI rendererの図画像／HTMLシェルを検査する仕様ではない。 |
| `docsite.excel` / V2 renderer | 段落・表・ローカルPNGを編集可能XLSXへ配置、旧V2表紙・62列格子・10列項目一覧、同じ階層の出力、ZIP/XML読戻し、全非空セル・画像SHA・罫線・数式なしの検査 | `spec-meta`のLIST/GRID/TABLEを読んでいない。章名と10列ヘッダーによる旧分類で、最新の通常GRID120列・LIST1行目ヘッダー・TABLE1シート特例を満たさない。Mermaidは文字列保持＋警告、HTML画面は画像化されず部品値も完全には保持されない。単純変換を最新様式合格にしない。 |

## 推奨する接続手順

1. 採用AI MDと既に成功・確認済みの静的描画一式を封印し、bytesハッシュを照合する。画面・図の対応にはrenderer manifestの`sourceLines`、`sourceSha256`、artifact SHAを用いる。描画素材を別稿／別snapshotと混ぜない。
2. HTMLは現AI rendererの`document.html`から原stemへコピーして採用する。派生HTMLのローカル文書リンクを納品ルートに合わせる場合は変更前後を別ハッシュで記録し、各リンク先とアンカーを検査する。MD本文は変更しない。原稿行範囲と各図／画面のPNG対応をmanifestへ残す。
3. PDFはまず現依存で利用できるChromiumによる、安全な派生HTMLの印刷を選べる。信頼済み印刷CSSだけを追加し、JavaScript無効、service worker無効、ネットワーク要求を全拒否した新しいcontextで印刷する。既存`docsite.pdf.prepare_html`／`PRINT_CSS`／`validate_pdf`の形式処理・抽出検査を再利用できるが、この接続用補助スクリプトは未作成／未検証。PDF内の文章を新規に組み立てない。
4. 従来WeasyPrint経路を選ぶ場合は、派生HTMLに実際に照合したMDの`docsite-source-sha256`を変換メタ情報として付与し、元HTML／変更後HTML／MDのハッシュを記録する。これは旧docsite経由で生成した証明ではなく、今回の変換接続を示すだけ。必要依存を分離領域に準備してから`python -m docsite.pdf --root <新規作業領域>`を実行する。Windows/Pangoの実動作検証が別途必要。
5. Excelは最新版spec-metaの宣言を正とする機械的変換モデルが必要。通常文書は指定sheet名と章順・LIST/GRIDを尊重し、TABLEはヘッダーと9列明細を同じ1シートへ置く。画面HTMLのブロックとMermaidは行範囲で固定済みPNGへ対応させて画像を配置し、原定義・ID・ハッシュを変換メタ情報に保存する。長さ超過は切捨てずエラーにする。既存`excel_package.package`／`verify`と3パターン罫線検査の再利用を基本に、上位マッピングだけを別の補助変換器で接続する。この接続用補助スクリプトも未作成／未検証。
6. PDF／Excelを各原stemで書き、派生変換の全件検査と視覚レビューが終わってから納品一式へ採用する。旧成果物への上書きや既存`output/`入替は本調査では行わない。

## 今回確認した依存

| 依存 | 現在の確認 |
| --- | --- |
| bundled Python | `C:/Users/tujin/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe`。今回のengine-runtime-depsをPYTHONPATHへ追加した状態で確認。 |
| markdown-it-py / BeautifulSoup / tinycss2 / Pillow / Playwright | import先の存在を確認。過去`.tmp/pydeps`のCPython3.11 ABIを混ぜない。 |
| pypdf | bundled環境に存在を確認。PDF生成・読戻しは未実施。 |
| WeasyPrint | bundled CPython3.12＋今回engine-runtime-depsには未導入。Pango等も実動作未確認。 |
| Chromium／Mermaid | 今回のengine/render作業で指定した既存実行ファイル・信頼済みpackageを使う。配布HTMLは入力JavaScriptを実行しない。 |
| Graphviz `dot` | 現PowerShellのPATH上には見つからなかった。旧HTML変換を選ぶなら追加確認が必要。 |
| `pdftoppm` | bundled Popplerの実行ファイルをPATH上で確認。生成後PDF全ページのPNG化に使用できる。 |
| 日本語フォント | Windowsの`meiryo.ttc`／`meiryob.ttc`を確認。文字抽出と実表示は別に検査する。 |
| Artifact Tool | bundled Nodeの`@oai/artifact-tool`ディレクトリが存在。XLSXの読取り／プレビュー用の候補。API実動作・描画は未実施。 |

## 必要なQA

- 11件のID・パス・stem・MD SHAが採用manifestと完全一致し、入力／原稿／原仕様は不変。変換ごとにエンジン・依存・素材・用紙の版とハッシュを記録。
- HTML: 章・表・セル・項目data属性・図原文・画面対応の欠落、リンク先、アンカー、画像破損、外部依存、描画除去要素を検査。表示を実際に画像で見て確認。
- PDF: 全件の読み込み・ページ数・タイトル・全表セル文字列を照合。既存`validate_pdf`はタイトルと指定10列項目表のセルだけを検査するため、他の表／章の全量照合は補助検査が必要。Popplerで全ページをPNG化し、日本語、表見出し反復、改ページ、図縮小、切れ／重なり／余白を確認。
- Excel: spec-metaから独立に取り出した章・sheet・列・行・ID・元文字列との対応を照合。変換モデルとXLSXが一致するだけでは原MD由来の全量を証明しない。TABLE1シート、通常GRID120列、LISTヘッダー位置、画像、文字列／先頭ゼロ／改行／数式らしい文字列、32,767文字上限、sheet名制限、印刷範囲、枠外無罫線を再読込して検査。
- Excelの全sheetを実際にrenderして確認する。PDFとExcelの変換検査合格は仕様内容95%／原アプリ実行試験合格には読み替えない。

## 技能

準備のため`C:/Users/tujin/.codex/skills/pdf/SKILL.md`とSpreadsheets技能の契約／QA部分を確認した。今回は実納品PDF／XLSXを作成していない。実適用を開始する前にrootから利用者へ技能利用を知らせる。

PDF技能は最新PDFのPNG実見を要求する。Spreadsheets技能は新規作者工程ではbundled Artifact Toolを標準とし、開始マーカー・全sheet描画・保存後検査を要求する。本件は利用者指定の既存変換アーキテクチャを保つため、既存docsite変換・検査を活かす場合もArtifact Toolの読取り／描画QAを組み合わせ、正式に作者工程を選ぶ場合は技能本文とAPIガイドを全て読んでから実施する。今回の調査は開始マーカーを実行していない。
