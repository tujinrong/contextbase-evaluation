# Excel仕様書・QA分離・main再生成の確認

確認日：2026-10-07（日本時間）。変更先は `tujinrong/contextbase-chatgpt` のみ。`source-to-doc-v2` は読取り参照のみで、変更していない。

## 反映

| 対象 | 識別子 |
| --- | --- |
| 修正前main | e0b207f5d65e727ebce67a3294643b9ac6141321 |
| プログラム・AGENTS.md・設定更新 | e645c874a9a638895e77af9fb8b7f3eadfad932d |
| 再生成成果物・QA保存 | 848d89093aec141d13ab84b641d083264495f6d0 |
| Actions実行 | 37571431109 / success |
| Actionsジョブ | 112630724489 / rebuild / success |
| 公開output Gitツリー | 2b3782448b1f02cc7889182d62fe5f05d8b199e7 |

実行記録：https://github.com/tujinrong/contextbase-chatgpt/actions/runs/37571431109

inputのGitツリーは修正前後とも `807791c000c42b9b9074fe9b39f322a78a0a0066`。既存src-dynamicも同一ツリー `7e2ea9e89b7c472f01c750a97f834f0e43e28466` を保持した。

## 成果物と検証

完全なGitHub checkoutのinputから、新規作業領域に生成した。以前のoutput・解析キャッシュは入力にしていない。検証成功後に旧output配下を除去して新しい出力へ入れ替えた。QAとreportの記録は保持した。

| 内容 | 結果 |
| --- | --- |
| input | 182ファイル、再生成前後で変更なし |
| 旧解析キャッシュ読込み | 0件 |
| MD | 33文書 |
| HTML | 34ページ、indexを含む |
| PDF | 33文書・79ページ、生成時検証成功 |
| Excel | 33冊・159シート |
| Excel全非空セル照合 | 3,316セル一致 |
| 自動テスト | 170件成功：specgen 37、docsite 72、contextbase 61 |
| HTMLブラウザー検査 | 34ページ、失敗0件 |
| HTMLローカルリンク検査 | 289件、エラー0件 |
| QA台帳 | 177件：仕様の仮定123件、解析確認54件 |
| 仕様書内QA参照 | 123種類、QA台帳への参照不整合0件 |

旧 `output/md/共通/項目一覧の確認事項.md` と対応HTML/PDFは新outputに存在しない。今回の33文書は旧34文書からその確認事項文書を除いた数であり、業務画面数を意味しない。

正本記録は `report/rebuild/result.json`、`report/excel/validation.json`、`report/pdf/validation.json`、`report/docsite/validation.json`、`report/docsite/browser.json`、`report/rebuild/logs/`。

## 保存後の照合

Actions artifact `contextbase-reorganized-37571431109`、ID `11461475299` を取得。ZIPのSHA-256は `4cd1e8b274d71810a4daa9e5ffd22e164dd33fe5bae4cda2597e7924a706d8f8`。展開したoutputのGitツリーSHAを再計算し、上記mainの出力ツリーと一致した。

Excel生成プログラムのZIP/XML照合とは別に、ローカルで33冊をartifact_tool表計算エンジンに読み込み、159シート・3,316非空セルを比較した。GitHubで再生成して取得した33冊は、その独立読込み確認済みファイルと33/33冊でバイト単位一致した。職員番号入力・新規変更削除の項目一覧の表示範囲を描画し、日本語、見出し、折返し、罫線、列配置を確認した。Microsoft Excelデスクトップでの全シート印刷確認を行ったという意味ではない。

代表ファイルのSHA-256：

| 文書 | SHA-256 |
| --- | --- |
| 職員番号入力 | efcb0ac5335d54efd62063a590bf392ddb83af01c6402c033854173fdfc909bb |
| 新規・変更・削除 画面 | df9b55e8a8fdd06e8d30784f08dfda540f5fd8c3b5866a98ff209cafcbdfa990 |

## 導入プログラムと出力ルール

MDを正本とし、`src/docsite/excel.py`、`excel_model.py`、`excel_package.py` でMDから編集可能なExcel仕様書へ変換する。表紙・章別シート・10列の項目表、固定見出し、オートフィルター、折返し、A4/A3横の印刷設定、ページ番号を備える。先頭ゼロ・日本語・改行を保持し、数式に見える文字列も数式として実行しない。

`AGENTS.md`へ以下の運用を記録した。

- `output/`：仕様書の成果物。情報不足でも合理的な仮定を明記して出力する。推測を確定事実としない。
- `QA/`：質問、暫定採用値、根拠、影響、回答、状態。`questions.json`を正本とし、再生成しても回答を保持する。
- `report/`：未完成、未検証、変換警告、検証結果。納品用outputには未完成報告を置かない。
- 書込み先は本リポジトリのみ。v2は参照専用。inputは変更しない。

仮定は仕様書の該当欄に `（仮定 Q-xxxxxxxxxx）` と付け、QAへ接続する。物理DB名を根拠なく創作せず、既存の確定済み必須・型・範囲を上書きしない。

## v2との関係と未完成範囲

参照リビジョンは `7bf3a20b724264c773edea1ee8193cb8a3bd4ca5`。`source-to-spec/scripts/excel_spec_tool.py`、`excel_workbook_style.py`、008-PENJVの項目一覧MDを読み、表紙／仕様／一覧の構成、日本語書体、節見出し、灰色の表ヘッダー、10列項目表を採用した。v2のExcelファイルの存在・名称は確認したが、バイナリを読み込んだ直接の見た目比較は未実施。様式とコードの参照であり、完全一致を保証しない。

納品本文は現在のソースと明示した仮定を優先する。業務仕様の完全性・動的画面・DB対応・実行同等性は未承認であり、詳細は `report/incomplete/未完成事項.md`、質問は `QA/仕様確認.md` に記録した。今回の判定は `verified_structure_only`。

画像のExcel直接埋込み、Mermaidの編集可能図形化は現行範囲外。該当するMDでは参照先／定義文字列を保存して `report/excel/incomplete.json` に警告する。今回の生成MDではこれらの変換警告は0件。

## 再実行

```shell
python -m pip install -e ".[pdf]"
python -m contextbase rebuild --replace-output --pdf --excel

# MDを保持しExcelのみ更新
python -m contextbase excel

# 単一MDを変換
md-to-excel --markdown spec.md --xlsx spec.xlsx
```

出力先：`output/Excel/`。利用方法の詳細：`docs/doc/MDからExcel仕様書.md`。
