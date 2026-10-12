# main反映・再生成の確認記録

確認日：2026-10-07（日本時間）

## 反映結果

コード修正と、GitHub上の完全なチェックアウトにあるinputからの再生成・成果物保存を完了した。業務仕様全体の承認や実行時の同等性を意味しない。

| 対象 | 識別子 |
| --- | --- |
| 修正前main | 8cf7b5c7e8fcc907833d45293abb1bf0ef657bcc |
| コード修正コミット | 4a8ad5803d9320e11e3bc8f1aec9c9d4b5984889 |
| 再生成成果物コミット | d1657edbf7c8dfe9759b2ff3bd9e4b1504f3e7de |
| GitHub Actions実行 | 37565402460 / Rebuild specifications from clean source / success |
| Actionsジョブ | 112611834343 / rebuild / success |
| 出力ツリーSHA | 30849f33212fd897471cc94489875780b6865008 |

Actions： https://github.com/tujinrong/contextbase-chatgpt/actions/runs/37565402460

コード修正コミットにはv2形式の項目表、Razorの静的抽出、PDF生成、CLI、CI設定、テストを含む。inputとsrc-dynamicは変更していない。inputのGitツリーSHAは修正前後とも `807791c000c42b9b9074fe9b39f322a78a0a0066`。

## 再生成とテスト

正本記録は `report/rebuild/result.json`、`report/generic/evaluation.json`、`report/generic/itemlist-review.json`、`report/pdf/validation.json`、`report/docsite/validation.json`、`report/docsite/browser.json`。

| 検証対象 | 結果 |
| --- | --- |
| input | 全182ファイルを保持し、再生成前後のハッシュ一致 |
| 作業領域 | 新規作成、以前のキャッシュ読込0件 |
| 静的抽出 | 46ファイル、抽出エラー0件 |
| 生成MD | 34文書 |
| 生成HTML | 35ページ（indexを含む） |
| 生成PDF | 34文書、86ページ |
| 項目定義 | 151項目 |
| specgenテスト | 37件成功 |
| docsiteテスト | 55件成功 |
| contextbaseテスト | 56件成功 |
| テスト合計 | 148件成功、各ログにOKを確認 |
| HTMLリンク検査 | 293件、エラー0件 |
| Chromium検査 | 35ページ、失敗0件 |
| PDF生成時検査 | 読み込み、タイトル、項目表セルの文字列照合を通過 |

46ファイルは解析対象であり、182ファイルすべてに業務解析を行ったという意味ではない。ビルド成果物等は除外または一覧記録のみ。31件の暫定機能文書には実装単位も含むため、承認済みの業務機能数として扱わない。

## 保存後の追加確認

Actions artifact `contextbase-reorganized-37565402460`（ID 11458287804）を取得した。ZIPのSHA-256は `50cb8f590b209a9b012959ca2eb0bf7d3ac01147ba646d068523e87375f0a63b`。展開したoutputからGitツリーSHAを再計算し、成果物コミットの `30849f33212fd897471cc94489875780b6865008` と完全一致した。

MD内の項目表について、31文書の10列構造、Noの連番、宣言件数、151項目の入出力表記、ボタンの非該当欄、表示項目の必須欄を追加照合し、整合を確認した。この照合は生成物間の構造整合であり、原本に対する意味の独立承認ではない。

PyMuPDFによる全34文書・86ページの読み込み、単語領域の用紙外はみ出し、置換文字の検査では異常を検出しなかった。職員番号入力1ページ目、新規・変更・削除画面2・3ページ目、確認事項1ページ目を画像で確認し、確認範囲で表の文字切れや日本語の表示崩れを認めなかった。職員番号入力1ページ目はPopplerでも描画確認した。全ページの人による目視承認や、全ての文字重なりを数学的に検証したという意味ではない。

## v2参照と未確認範囲

参照元は `tujinrong/source-to-doc-v2` のリビジョン `7bf3a20b724264c773edea1ee8193cb8a3bd4ca5`、`projects/008-PENJV/spec/screens/100006/document-input/items/basic-itemlist.md`、100008の関連MDと項目規約。列は次の順序とする。

`No / グループ / 項目名 / 種類 / 入出力 / DB連携項目 / 候補取得元 / 必須 / 形式・桁 / 説明`

入出力は `I`、`O`、`I／O`、`‐`。別プロジェクトの値や根拠不明のDB対応を転記せず、現行inputを優先した。未確認事項は `output/md/共通/項目一覧の確認事項.md` に集約している。

v2の `projects/008-PENJV/output/PDF/基本設計書/基本設計書_100008_職員番号入力.pdf` 等の存在とGit blobは確認したが、参照PDFのバイナリ取得・直接描画比較は完了していない。対応MDとの照合と、今回生成したPDFの描画確認を区別する。

今回の実行プロファイルはgeneric、判定は `verified_structure_only`、意味解析は `partial`。共有レイアウトの合成、実行時画面、動的HTML、完全なDB連携、全業務経路、実装再構築の同等性は未検証。今回の汎用出力に埋め込み画面レイアウトやMermaid図は含まれず、外部レイアウト専用検査は対象なし（not_applicable）。native Pilotは実行されていない。MCTERP/TKL専用項目表レンダラーは変更していない。

## 出力先と再実行

MDは `output/md/`、HTMLは `output/html/`、PDFは `output/PDF/`。それぞれ分類と文書名を対応させている。説明は `docs/doc/PDF出力と項目一覧.md`。

```shell
python -m pip install -e ".[pdf]"
python -m contextbase rebuild --replace-output --pdf
```

PDFのみ再生成する場合は `python -m contextbase pdf`。日本語フォントとPango等のOS依存が必要。フォントファイルは成果物一式に同梱していない。
