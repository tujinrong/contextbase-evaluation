# MDからExcel仕様書

現在の標準変換は、添付V2形式を基準にした `src/docsite/v2/render_document_xlsx.py` の移植版を使用する。以前の汎用表紙・幅の少ない本文表は標準経路では使用しない。

```shell
python -m pip install -e ".[pdf]" playwright==1.57.0
python -m playwright install chromium
python -m contextbase rebuild --replace-output --pdf --excel
python -m contextbase excel
md-to-excel --markdown spec.md --xlsx spec.xlsx
```

Pilotの画面再構成にはPlaywrightとChromium、遷移図にはGraphvizの `dot` が必要。上記コマンドの前にGraphvizを導入し、dotをPATHへ追加する。PDFには既存のPango等のOS依存と日本語フォントも必要。既存MDからExcelだけを生成する場合は画像を作り直さないため、PlaywrightやGraphvizの起動は行わない。

`output/md`を正本として、同じ分類・同じ名前の編集可能なExcelを `output/Excel` へ出力する。画像はMDからのローカル相対パスを使用する。見出し・段落・表・画像を、表紙、章別シート、10列項目表、62列本文格子へ展開する。先頭ゼロ・数式に見える文字列は文字列として保存する。

詳細は [V2テンプレート移植と職員番号Pilot](V2テンプレート移植と職員番号Pilot.md)。原本の処理範囲、移植した関数、依存関係の変更点を明記している。

`report/excel/validation.json` は全非空セル・埋込み画像ハッシュの検査、`manifest.json` は生成物所有権と差分再利用、`checkpoint.json` は途中経過を記録する。MD・変換コード・画像のハッシュが変わると再生成する。手動編集された生成Excelを通常変換で無断上書きしない。

`--replace-output` の全体再生成では、原本から空の作業領域へ作成し、検証後に旧output配下を入れ替える。質問と回答は `QA/`、未完成・未検証事項は `report/` へ保存し、回答と過去の報告を保持する。仮定は仕様書の該当箇所でQA番号と区別する。
