# V2テンプレート移植と職員番号入力Pilot

## 今回の基準

ユーザー添付 `基本設計書_100008_職員番号入力.xlsx` を書式の基準とした。添付ファイルの意味解析結果を無条件で採用せず、現行 `input/JSBRMS.Web` の職員照合経路を確認した。

従来の少数列・汎用表紙による出力から、添付の表紙・62列本文格子・項目表へ変更した。表紙はO6:AU36、本文ヘッダーはA1:BJ1、本文はB:BJ、一般表はC:BJ、項目表はA:Jの10列である。本文画像をExcel内へ埋め込み、長文の行高とイベント境界の改ページを設定する。項目一覧タイトルは元の狭いA列からA:Jへ結合し、文字切れを防止した。

## 実際のV2生成プログラム

リビジョン：`7bf3a20b724264c773edea1ee8193cb8a3bd4ca5`

| V2のファイル | 役割 |
| --- | --- |
| spec-tools/doc-tools/execute_step4_7_2_screen_excel_specs.py | 基本・詳細MDとテンプレートを選択してレンダラーを起動する工程4.7.2の入口。 |
| spec-tools/doc-tools/render_document_xlsx.py | テンプレートの表紙・本文・一覧シートを複製し、Markdownの章、表、画像、イベントをExcelへ展開する本体。 |
| spec-tools/doc-tools/document_render_common.py | Markdown解析、メタデータ、画像解決などの共通処理。 |
| spec-tools/doc-tools/execute_step4_6_screen_documents.py | 列配分、画像・図の配置などの機能も提供するV2側の大きなコントローラー。 |

https://github.com/tujinrong/source-to-doc-v2/blob/7bf3a20b724264c773edea1ee8193cb8a3bd4ca5/spec-tools/doc-tools/render_document_xlsx.py

https://github.com/tujinrong/source-to-doc-v2/blob/7bf3a20b724264c773edea1ee8193cb8a3bd4ca5/spec-tools/doc-tools/execute_step4_7_2_screen_excel_specs.py

## 本repoへ追加した実装

`src/docsite/v2/render_document_xlsx.py` は上記本体から必要な処理を移植した版である。**V2の全ファイル・依存関係をそのまま複製したものではない。** プロジェクト固有コントローラーとopenpyxl依存を、既存ContextBaseのデータモデル・OOXML出力処理へ置き換えた。

V2由来の列配分・シート名の関数は `upstream_layout.py`、原本と変更範囲は `PROVENANCE.json`、添付から取得したセル位置・列幅・印刷設定は `reference_format.json` に記録する。既存の `md-to-excel`、`contextbase excel` はこの移植版を呼ぶ。`python -m docsite.v2.execute_step4_7_2_screen_excel_specs` も同じ入口へ接続する。

処理の流れ：MD読込み → 表紙メタデータと章を解析 → V2配置モデル作成 → ローカルPNG/JPEG画像を検証・埋込み → Excel保存 → 全非空セルと埋込み画像ハッシュの照合 → outputへ公開。

外部画像取得、マクロ、数式文字列の実行は行わない。画像の欠落を黙って省略せず、変換エラーはreportへ記録する。Mermaid定義そのものの画像化は既存経路とは別扱いとし、移植版へ渡す画像はローカルPNGを使用する。

## Pilotの内容改善

`src-dynamic/jsbrms-pilot/職員番号入力.md` は現行ソースをレビューした外部仕様の材料である。`pilot.json`の11ソースのハッシュが一致した場合のみ採用する。原本変更時はこの本文を流用せず、QAへ変更確認を記録し、汎用解析から仮定付きで出力する。

添付から改善した点は、入力値の必須・数値範囲・全角数字補助、初期表示、職員照合成功時の3項目保持、エラー時の入力・既存状態の保持、通常クリアとJSON要求時の204応答、メニューの8桁表示、セッション無操作8時間である。現行ではサンプル職員照合を使用するため、添付のDB2参照を転記しない。現行レイアウトにないログアウト操作を追加せず、クリアをメニュー遷移として記載しない。

Pilotは5シート：表紙、概要、項目一覧、イベント仕様、補足説明。画面と遷移図の2画像を概要に埋め込む。画面はHTML・共通レイアウト・CSSからの再構成であり、アプリ実行のキャプチャではない。Bootstrapの配布CSS等が原本にない部分は近似し、QAで区別する。

## 出力・QA・検証

全体再生成：`python -m contextbase rebuild --replace-output --pdf --excel`

Pilot Excel：`output/Excel/基本設計書/基本設計書_100008_職員番号入力.xlsx`

対応MD・HTML・PDFも同一名で出力する。Pilotが採用したPageModelは同じ画面の仕様へ統合し、別の暫定機能として重複出力しない。従来の他機能の意味解析を、Pilotと同じ精度に改善したとは扱わない。

質問は `QA/`、未完成・表示近似・実行同等性などの未検証事項は `report/`。`report/pilot/status.json` にソース一致とPilot採用状態を記録する。テストには表紙の結合セル一致、本文62列、項目表の10列、章構成、画像欠落検知、画像改変検知、原本変更時の採用停止、主要な状態仕様を含む。

Excelへの画像埋込み検査と、Microsoft Excelでの全シート印刷承認は別である。実アプリ・本番DBとの同等性は未検証のままreportへ記録する。
