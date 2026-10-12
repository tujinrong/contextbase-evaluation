# V2書式移植・職員番号入力Pilotの反映結果

確認日：2026-10-07。対象は `tujinrong/contextbase-chatgpt` のmain。v2リポジトリは読取り参照のみで、変更していない。

## main反映と再生成

| 対象 | 識別子・結果 |
| --- | --- |
| 変更前main | 6ae0e2b5b9bc6d280561064bf6d64482eabd1aa1 |
| 生成コード・Pilot追加 | bde21ca8b3ba324111f37745fa8f55bf62c9cf2d |
| 再生成成果物 | 9738c750ca629ed4c4a99d8090d9f369c8b999d0 |
| GitHub Actions | 37577142438、ジョブ112648456638、全工程success |
| 公開outputのGitツリー | 1d9c75a4d6d27ba2a79e3a8e7229ce60f4f0efd3 |
| inputのGitツリー | 807791c000c42b9b9074fe9b39f322a78a0a0066、変更なし |

実行記録：https://github.com/tujinrong/contextbase-chatgpt/actions/runs/37577142438

GitHub上の完全checkoutのinputから、新規作業領域で生成・検証した後、旧output配下を入れ替えた。旧outputと旧解析キャッシュは入力にしていない。QA回答とreportの記録は保持した。既存のMCTERP/TKL用コードは変更せず、職員番号入力用のレビュー材料を `src-dynamic/jsbrms-pilot/` に追加した。

| 検証対象 | 結果 |
| --- | --- |
| 入力 | 182ファイルを保持し、再生成前後で変更なし |
| MD | 32文書 |
| HTML | 33ページ、ブラウザー検査失敗0件 |
| PDF | 32文書、85ページ、生成時の読込み・文字列照合成功 |
| Excel | 32冊、154シート |
| Excel全非空セル照合 | 3,560セル一致 |
| 自動テスト | 184件成功（specgen 37、docsite 86、contextbase 61） |
| Pilot追加判定 | 20検査成功、5シート、216非空セル、2画像 |

32文書は旧33文書から、職員番号入力のPageModel単独文書を画面の仕様書へ統合した数。業務機能全体の承認済み件数を意味しない。

## V2の実生成PYと移植範囲

参照元リビジョンは `7bf3a20b724264c773edea1ee8193cb8a3bd4ca5`。実際の入口は `spec-tools/doc-tools/execute_step4_7_2_screen_excel_specs.py`、本体は `spec-tools/doc-tools/render_document_xlsx.py`。前回参照した旧系統の一般的なExcelスタイル説明だけではなく、この本体の表紙・本文格子・項目表・画像配置を調べた。

`src/docsite/v2/render_document_xlsx.py`、`upstream_layout.py`、`execute_step4_7_2_screen_excel_specs.py` を追加し、既存 `md-to-excel` と `contextbase excel` の標準経路へ接続した。V2の全量コピーではなく、必要な処理を既存ContextBaseのデータモデルとOOXML保存処理へ移植した版である。`proportional_spans` はV2由来の関数を使用し、プロジェクト固有コントローラー、openpyxl依存等は分離した。原本のファイル・blob・変更範囲は `src/docsite/v2/PROVENANCE.json`。

添付 `基本設計書_100008_職員番号入力.xlsx` のSHA-256は `8aa5984782c5a175bf727721153b6d528e795fc03d3765fbf804aeb7ce5cf6f6`。添付から得た書式条件は `reference_format.json`。

| 書式要素 | 今回の反映 |
| --- | --- |
| 表紙 | O6:AU36、添付と同じ14結合領域、システム名・機能ID・画面名・作成／査閲／承認欄 |
| 本文 | A:BJの62列、添付と同じヘッダー区画、本文B:BJ、一般表C:BJ |
| 項目一覧 | A:Jの10列、添付の列幅・列順。長い説明に応じて行高を増やす |
| 画像 | 画面と遷移図の2PNGをExcel内へ埋込み。URL文字列だけで代用しない |
| 見出し・印刷 | 灰色見出し、◆小見出し、繰り返しヘッダー、イベント境界の改ページ、絶対座標の印刷範囲 |
| 改善点 | 項目一覧タイトルをA:Jへ結合し、長文を固定18pt行へ詰め込まない |

## Pilotの仕様内容

現行inputの11ファイルをレビューし、正規化したソースハッシュが一致する場合のみPilot本文を採用する。原本変更時に古いレビュー本文をそのまま使用しない。入力条件・職員照合・セッション操作・メニュー表示・クリアの各経路を区別した。

初期表示、数字入力補助、照合成功、必須／範囲／未登録エラー、通常クリア、JSON指定時のHTTP 204について、処理順序と入力・出力・保持状態を具体化した。エラー時は既存のセッション職員情報を消去せず、クリア時は職員情報3項目を削除する。クリアをメニュー遷移として記載しない。現行はサンプル職員照合を使用するためDB2参照を転記せず、存在しないログアウトボタンも追加しない。

Excelの5シートは、表紙、概要、項目一覧、イベント仕様、補足説明。Pilotの専用項目は見出し1・入力1・操作2の4項目。共通ナビゲーションは専用項目数から分離した。

## 保存後の独立確認

Actions artifact ID `11463415754` を取得。元ZIPのSHA-256は `169f4c3a4875f3bb51c018da4a110a06829e68cae14d519aa10e0d68f6499e27`。展開したoutputからGitツリーを再計算し、mainの `1d9c75a4d6d27ba2a79e3a8e7229ce60f4f0efd3` と一致した。

生成時のZIP/XML検査とは別に、取得したExcel32冊をartifact_tool表計算エンジンへ読み込み、154シート・3,560非空セルを照合し、全て一致した。Pilotの表紙・項目一覧・イベント仕様冒頭を描画確認し、長文やタイトルの表示を確認した。埋込みPNG2枚をZIPから取り出して内容を目視確認し、生成時の画像ハッシュとも照合した。対応PDFの画面ページも描画確認した。

Pilot ExcelのSHA-256：`8dc3b2052169baf21dcf0220af710d186dd31f10ee3676a14d4d73dd4bf1355c`

## 未検証事項とQA

画面は現行HTML・共通レイアウト・CSSからの静的再構成であり、実アプリケーションを実行したスクリーンショットではない。原本に収録されていないBootstrapのコンテナ配置等は近似する。Q-PILOT-STYLE、Q-PILOT-BIND、Q-PILOT-DATAをQAへ追加し、表示近似、対象実行環境による数値変換エラー文言、本番データ取得先を区別した。

書式生成の変更は全32冊に適用した。今回、業務内容を重点的にレビュー・改善したのは職員番号入力Pilotであり、他機能が同じ意味解析精度に達したとは扱わない。全体実行の判定は `verified_structure_only`。実アプリ・本番DBとの同等性、Microsoft Excelデスクトップでの全シート印刷、全ページの目視承認は未実施。画像は埋込みPNGであり、編集可能なExcel図形への変換ではない。

詳細：`report/pilot/status.json`、`report/pilot/evaluation.json`、`report/incomplete/`。質問・回答：`QA/questions.json`、`QA/仕様確認.md`。納品用outputには未完成報告を混ぜていない。
