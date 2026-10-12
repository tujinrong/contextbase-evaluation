# PDF出力と項目一覧

## 適用範囲

汎用解析経路にv2形式の基本設計項目一覧を追加し、検証済みHTMLからPDFを生成します。MCTERP/TKL専用の項目表レンダラーは変更しません。参照元は `source-to-doc-v2` の `projects/008-PENJV/spec/screens/{100006,100008}/document-input/items/basic-itemlist.md` 等、リビジョン `7bf3a20b724264c773edea1ee8193cb8a3bd4ca5` です。別プロジェクトの業務値は転記しません。

## 項目一覧

列順は `No / グループ / 項目名 / 種類 / 入出力 / DB連携項目 / 候補取得元 / 必須 / 形式・桁 / 説明` の10列です。

入出力は `I`、`O`、`I／O`、`‐`（U+2010）。操作ボタンにはDB連携・候補・必須・桁制約を付けません。表示項目に入力必須を設定しません。同じ名称の別コントロールは統合せず、定義順を維持し、非表示値は公開項目数と分離します。

解析上で根拠のない必須・DB対応は未確定として保持し、納品文書には必要な仮定とQA番号を付けて出力します。HTMLのrequired属性がないことだけで任意と断定せず、モデル属性による制約と実際に検証が実行されることを区別します。

`.cshtml`、対応するPageModel、一意な同名モデルファイルを照合します。単純プロパティ、Required、最大長、数値範囲、bool型の入力、条件付きreadonlyに対応します。モデル参照は最大4階層。動的添字、カスタムTag Helper、継承、共有レイアウト合成、実行時画面の完全再現は未対応です。

質問・回答は `QA/questions.json` と `QA/仕様確認.md`、未完成事項は `report/incomplete/`、解析照合は `report/generic/itemlist-review.json` に集約します。確認事項の報告書はoutputには置きません。構造検証通過は業務仕様の承認ではありません。

## 実行

Python 3.11以上を使用します。

```shell
python -m pip install -e ".[pdf]"
python -m contextbase rebuild --replace-output --pdf --excel
```

既存MDを保ってHTML/PDFを更新する場合は `python -m contextbase build --pdf`、PDFだけの場合は `python -m contextbase pdf`。用紙指定は `python -m docsite.pdf --paper "A3 landscape"`。

出力は `output/PDF`。MDと同じ相対パスで拡張子だけを変更します。対応MDのないHTML一覧indexはPDF件数に含めません。

## 環境

PDF依存はWeasyPrint 68.0とpypdf 5.9.0。日本語フォントとPango等のOSライブラリも必要です。

```shell
sudo apt-get install -y graphviz fonts-noto-cjk libpango-1.0-0 libharfbuzz0b libpangoft2-1.0-0 libharfbuzz-subset0
```

Windowsは公式WeasyPrint手順に従いMSYS2/Pango、またはWSLを使用してください。Windowsでの実行検証は未実施です。フォントファイルはリポジトリへ追加しません。

公式手順: https://doc.courtbouillon.org/weasyprint/v68.0/first_steps.html

## PDF検証

MDとHTMLのハッシュ整合を確認し、新しい作業領域でPDFを作成します。JavaScriptは実行せず、外部取得と許可領域外の参照を拒否します。読み込み可能性、ページ数、タイトル、項目表セル文字列を照合し、画像取得・描画エラーを検知します。全件成功後のみ公開PDFを置換し、失敗時は既存PDFを保持します。管理外または手動編集PDFを無断で上書きしません。

`report/pdf/validation.json` に検証結果、`output/PDF/_manifest.json` に所有権と再利用用ハッシュを保存します。同一入力・印刷CSS・エンジン・素材・用紙のPDFは再検証して再利用します。

横長表はA4横、表見出し反復、ページ番号、日本語折り返し、相対PDFリンクに対応します。文字列存在検査は完全なレイアウト検査ではありません。代表PDFの画像確認を別に行ってください。信頼境界外の巨大文書には実行環境側で時間・メモリー制限を設定してください。

## CI

`rebuild --pdf` を段階生成・検証・入替えへ統合しています。PDF生成失敗時はoutputを公開しません。GitHub Actionsは完全checkoutのinputから再生成し、全ゲート成功後に成果物をmainへ保存します。実行結果は `report/rebuild/result.json` とActionsログを正とします。
