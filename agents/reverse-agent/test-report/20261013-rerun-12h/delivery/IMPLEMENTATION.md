# 固定AI稿の派生変換補助

2026-10-13。実装準備まで。実稿からのPDF／XLSXの生成、実ファイル読戻し、視覚承認はまだ行っていない。元AI実行コード、原稿、題材ソース、原仕様、spec-evalは未変更。

## 実装

- `delivery_model.py`: 指定したMD／render-pins／renderer manifest／canonical HTML／全素材のSHAを照合し、原文の章・表・文章と固定描画の行位置から、機械的なセル／画像配置モデルを抽出する。LIST／GRID／TABLE／HEADER、宣言sheet名、章順、TABLE9列・1sheet、GRID120列を保持する。仕様本文を追加しない。
- `export_pdf.py`: 同じ固定入力から原stem HTMLをコピーし、信頼済みChromiumの入力JavaScript無効・通信拒否でPDFへ印刷する。pypdfで全章名、Markdownの全表セル、HTMLの表セル、段落・コード文字列を照合し、Popplerで全ページをPNG化する。出力は必ず`visualReview=PENDING`とする。
- `build_xlsx.mjs`: bundled `@oai/artifact-tool`だけで新規Workbook・セル・結合・罫線・PNG・XLSXを作る。開始markerの実施を明示した場合だけ起動する。原順序、原文字列、先頭ゼロ、数式らしい文字列を維持する。全sheetの領域を分割してPNGプレビューを出す。書出しだけで合格にしない。
- `verify_xlsx.py`: 元の固定MDからモデルを再抽出し、保存XLSXのZIP／XMLから全非空セル、型、sheet順、結合、画像ハッシュと配置、原稿ハッシュ、数式・マクロ・外部リンクなし、標準書式、枠外／結合内部の罫線を照合する。公開API資料と1回のread-only API検索で印刷設定を取得できなかったため、オプションで印刷範囲・用紙等のOOXMLメタ情報だけを接続する。値・セル・画像・書式の作者はArtifact Toolのまま。接続前後を同じ独立読戻しで照合し、ハッシュを残す。
- `probe_api.mjs`／`api-probe.ndjson`: `worksheet.pageLayout`の1回限定read-only公開API検索。0件。Workbookに値を入れる操作、export、saveは行っていない。
- `test_connections.py`: 変更されたMD／描画素材／snapshotの拒否、重複ID、絶対・親パス、未固定図、TABLE1sheet、番号付き手順、先頭ゼロ／桁文字列／数式文字列／改行・縦棒の保持を検査。11件PASS（最新`tests-r4.raw.log`）。Python構文・import、Node構文検査もPASS。PDF／XLSX作者工程の実動作試験ではない。

既存V2を踏まえ、表紙はO6:AU36内の分離した枠、通常GRIDは全範囲のmedium外枠＋ヘッダー直下のdouble罫線、LISTは表の枠のみとする。TABLEは表紙を追加せず、A1:I1のタイトル、元MDのpreamble全文と節見出しをA:I結合行、A:BとC:Iのヘッダー、A:Iの9列明細として、原順序で同じ宣言sheetへ置く。長文説明を末尾列に写し、列幅は `[5,18,20,6,8,17,16,10,95]` とする。最新規約の120列と宣言sheet名は旧62列rendererへ黙って変換しない。

## 入力binding

採用原稿のSHAは完成draft-resultから、render-pins／manifestのSHAは採用する固定描画から、source snapshot SHAは今回の封印snapshotから記入する。採点合格や視覚承認の有無をこれらの機械的SHAから推論しない。

```json
{
  "schema": "reverse-agent-delivery-binding/1",
  "referenceMode": "source-only",
  "permittedMarkdownRoot": "D:/開発/contextbase-evaluation/test-project1/spec-analysis/CSharp_ASPNET/20261013-rerun-12h/source-only/drafts",
  "permittedRenderRoot": "採用する描画フォルダ群を包含する明示的な絶対パス",
  "sourceSnapshotManifestSha256": "封印snapshot manifestのSHA256",
  "documents": [
    {
      "documentId": "採用稿の文書ID",
      "canonicalDocumentPath": "基本設計書/01_学生検索画面.md",
      "markdown": "採用する不変MDの絶対パス",
      "markdownSha256": "完成draft-resultのcontentSha256",
      "renderDirectory": "同MDを描画した不変render-pins／manifestのフォルダ",
      "renderPinsSha256": "render-pins.jsonのSHA256",
      "renderManifestSha256": "manifest.jsonのSHA256"
    }
  ]
}
```

## 利用手順

入力と出力は別の新しいフォルダとし、MDや描画元の配下へ出力しない。試行のPDF／XLSX／QAは本`delivery`配下に作成する。最終納品階層へ移す場合はrootが各形式の採用判定とリンク照合を行う。

```powershell
$taskDelivery='D:/開発/contextbase-evaluation/agents/reverse-agent/test-report/20261013-rerun-12h/delivery'
$taskPython='C:/Users/tujin/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe'
$taskNode='C:/Users/tujin/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node.exe'
$env:PYTHONPATH="$taskDelivery;D:/開発/contextbase-evaluation/agents/reverse-agent/.tmp/20261013-rerun-12h/engine-runtime-deps"
& $taskPython "$taskDelivery/delivery_model.py" --binding "$taskDelivery/selected-binding.json" --model "$taskDelivery/model-01.json"
& $taskPython "$taskDelivery/export_pdf.py" --binding "$taskDelivery/selected-binding.json" --output-root "$taskDelivery/pdf-01" --chromium 'C:/Users/tujin/AppData/Local/ms-playwright/chromium-1223/chrome-win64/chrome.exe'
```

XLSXの最初の作者コマンドの直前に、rootが技能の開始markerを成功させる。expected-output-countはその納品一式の予定件数に合わせる。既に開始markerが成功している場合は繰り返さない。

```powershell
& $taskNode 'C:/Users/tujin/.codex/plugins/cache/openai-primary-runtime/spreadsheets/26.1011.11113/skills/spreadsheets/container_tools/mark_artifact_operation_started.mjs' --operation-kind create --expected-output-count 11 --output-format xlsx
& $taskNode "$taskDelivery/build_xlsx.mjs" --model "$taskDelivery/model-01.json" --output-root "$taskDelivery/xlsx-01" --authoring-marker-completed
& $taskPython "$taskDelivery/verify_xlsx.py" --model "$taskDelivery/model-01.json" --manifest "$taskDelivery/xlsx-01/delivery-manifest.json" --connect-print-metadata
```

bundled node_modulesを指すjunctionは本delivery直下へ用意済みであり、依存ディレクトリ自体は変更していない。過去のCPython3.11専用`.tmp/pydeps`は混在させない。

## 採用前に必要な実稿QA

検索基本candidate03の変換器修正・実ファイルQAは[REPAIR-QA-R09.md](REPAIR-QA-R09.md)を参照。原稿最終書式はFAILEDであり、文字／XML照合合格を納品承認へ読み替えない。r04 XLSX全42 tiles、r09 PDF全106ページを実見したが、nativeの数字らしい文字列表示差、大図全体縮小／pixel tile境界の制約が残っている。

機械的な画像投影とbounded PDF実行は以下の引数で指定できる。各出力rootとmodel名は必ずfreshにする。既に成功した作者開始markerは再実行しない。

```powershell
& $taskPython "$taskDelivery/delivery_model.py" --binding "$taskDelivery/selected-binding.json" --model "$taskDelivery/model-fresh.json" --image-max-width 1850 --preview-max-height 1200
& $taskPython "$taskDelivery/export_pdf.py" --binding "$taskDelivery/selected-binding.json" --output-root "$taskDelivery/pdf-fresh" --chromium 'C:/Users/tujin/AppData/Local/ms-playwright/chromium-1223/chrome-win64/chrome.exe' --poppler 'C:/Users/tujin/.cache/codex-runtimes/codex-primary-runtime/dependencies/native/poppler/Library/bin/pdftoppm.exe' --diagram-tiles --stage-timeout 90
```

画像の拡大tile付録は業務説明を生成せず元PNGをcropする閲覧補助。元PNG SHA、crop box、60 px重複、全画素coverage、非白画素coverage、白領域の非印刷理由をmanifest・独立QAへ記録する。MS Gothicを含め実環境のフォントで抽出／表示を確認する。フォントが変われば過去の662文字列合格を流用しない。

PDFのmanifestに列挙された**全ページPNG**、XLSXのmanifestに列挙された**全sheet・全領域PNG**を実際に閲覧する。文字・数値・日本語の欠落、クリップ、重なり、画像縮小、表幅、行高、改ページ、画面モードを確認し、閲覧したファイルとSHAを別の視覚レビュー記録へ残す。機械的検査が成功しても視覚承認を自動でtrueにしない。

Artifact Toolが文字列やPNGを再符号化した場合、読戻しは相違を拒否する。セルの長さまたは行高で読めない場合も切り捨てず停止する。単純な配列の書出しから完成判定へ進めず、実稿で必要な接続修正を行ってから再検査する。印刷メタ情報の接続後もExcel実アプリでの印刷試験は未実施と区別する。

全11件の原稿品質採点、原ソースとの一致、原画面材料との視覚比較はroot／独立評価工程の担当であり、本派生変換コードの合格とは別である。

## TABLEの実稿検証と印刷用改ページ

コード分類TABLEの実稿検証は [M-CODE-CATEGORY-DELIVERY-R05.md](M-CODE-CATEGORY-DELIVERY-R05.md) を参照。TABLEのpreamble、元節見出し、空欄を含む全セル順序、元metadata、Noキー、XML列幅・罫線を照合した。元名HTML/Excel/PDFの候補は正式採点未合格・非公開のまま保存する。

Chromiumの自動継続ヘッダーに欠落が見つかった場合、rendererが所有するMarkdown表だけを、印刷投影で固定行数ごとに分割できる。`--table-page-rows 4` は本文行を変えず、同じheader・colgroupを正確に複製し、元行範囲とbody行HTMLの完全一致をmanifestへ記録する。canonical HTMLコピーと元MDは変えない。未対応のcolspan/rowspan/tfootや非canonical表fragmentは拒否する。入力によって各行の高さが異なるため、この引数自体は視覚合格の保証にならず、必ず実PDFの全ページを確認する。

```powershell
& $taskPython "$taskDelivery/export_pdf.py" --binding "$taskDelivery/selected-binding.json" --output-root "$taskDelivery/pdf-table-fresh" --chromium 'C:/Users/tujin/AppData/Local/ms-playwright/chromium-1223/chrome-win64/chrome.exe' --poppler 'C:/Users/tujin/.cache/codex-runtimes/codex-primary-runtime/dependencies/native/poppler/Library/bin/pdftoppm.exe' --stage-timeout 90 --table-page-rows 4
```

検索基本r04 `表紙!X18` のnative描画では `1.0` が `1` に見えたが、read-only実ExcelではValue2/Textとも `1.0`、前後bytesSHA不変を確認した。1セル限定の追跡証跡は `excel-literal-application-r01/result.json`。元セルの文字や書式を画像に合わせて変更していない。全ワークブックの実Excel表示・印刷検証は別途未実施として扱う。
