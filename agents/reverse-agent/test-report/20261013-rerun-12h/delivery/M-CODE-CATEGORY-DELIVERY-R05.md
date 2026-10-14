# コード分類テーブルの派生形式QA

`03_m_code_category.md` の同名HTML・PDF・Excel候補を作成した。派生形式の文字・順序・罫線・画像検査は合格。正式採点と最終公開の判断は未完了として保持する。

対象は `source-only/drafts/remaining-batch-03/基本設計書/テーブル/03_m_code_category.md`、文書ID `CSHARP_ASPNET-BAS-STU-03-M_CODE_CATEGORY`、版 `1.0`。元MD SHA256は `c43b8c5de33de810413b9b5cf306f1fd60ae4a9d054fd2be7c1a7bd6f6adab46`、封印snapshot manifest SHA256は `2f64e2211b1fcd7850203927fc75b5a7f2ce37457cc2afe88c8065d9f931273b`。元MD・ソース・固定描画HTML/PNGを変更せず、原仕様・spec-evalを読まず、アプリ・DBを実行していない。

| 形式 | 候補ファイル | SHA256 |
| --- | --- | --- |
| HTML | [03_m_code_category.html](pdf-m-code-category-r05/html/基本設計書/テーブル/03_m_code_category.html) | `9bd4478328b504f913e4363917173ca2c9d17f2c48e645368aee88c0a614a32e` |
| PDF | [03_m_code_category.pdf](pdf-m-code-category-r05/PDF/基本設計書/テーブル/03_m_code_category.pdf) | `7c7beb1f6bccc768b68072f6add0c619fe8d4a16611ac3e0154fa4a5bf5d51e1` |
| Excel | [03_m_code_category.xlsx](xlsx-m-code-category-r05/Excel/基本設計書/テーブル/03_m_code_category.xlsx) | `093ce0b4060a930fb64c03feab1f323f40633e192bb8295a340a74753c9d6ec7` |

HTMLはrenderer r10のcanonical bytesと一致する。旧r03→新r04は全可視文字列と全表セルの値・順序が一致し、Markdown表にだけ列幅と罫線が適用された。1440×4758 PNGから切り出した5画像を原寸で実見した。元PNGとの全画素一致、80px重複、全キャンバスcoverageも確認した。旧rendererの縦折れは解消している。

PDFは信頼済ChromiumでJavaScript無効・通信拒否のまま作成した。印刷用投影だけ、4データ行ごとに同じ表見出し・列定義を複製する。本文38行のHTML bytesと順序は不変で、元HTMLの同名コピーも不変。実PDF文字照合142/142、全データ行の順序一致、全10ページの全列見出しを確認し、Poppler全10 PNGを原寸で実見した。r04で見つかった継続表ヘッダーの欠落をr05で解消した。試行r04を失敗証跡として保持する。

Excelの作者はbundled `@oai/artifact-tool`。開始markerは再実行していない。TABLE宣言の `m_code_category` 1sheet・9列を維持し、タイトルA1:I1、文書ID/版/パスの全文A3:I3、見出しA5:I5・A35:I35、ヘッダー表A6:I33、9列明細A36:I47として、元の可視順序を保持した。全168値（空欄26を含む）の順序、142非空literalセル、全11項目キー、26空欄、declared sheet名・元metadataを照合した。数式は0件。XML列幅 `[5,18,20,6,8,17,16,10,95]` と60結合枠・罫線・印刷範囲A1:I47も確認した。全5 native画像で日本語・罫線・長文折返し・両節見出しを実見した。r04候補では節見出しがセルに入っていなかったため不採用、r05で元文字列だけを追加し、他セルの値・style役割・sourceLines不変と座標移動を記録した。

印刷メタ情報だけ既存接続器で追加した。セル・数式・結合・罫線・画像のOOXML authorshipは行っていない。native画像はその接続前のArtifact Tool描画であり、実Excelの全体表示・印刷試験は未実施である。

検索基本Excel r04の `表紙!X18` を別のread-only helperで実Excel確認した。Value2は文字列 `1.0`、Textも `1.0`、NumberFormatは `@`。非表示・UpdateLinks=0・マクロ無効・ReadOnly=trueで開き、保存せずClose/Quitした。前後SHAは `61029ddcab28b54338984d746bbca637ac57112a5659e327f5d54187c7734ec1` で一致し、所有Excel PID 104764の終了を確認した。この1セルについてnative previewの `1` 表示と実Excelの表示差を分離できた。ワークブック全体や印刷の合格には読み替えない。

機械検査20件PASS。詳細証跡は [m-code-category-delivery-r05-qa.json](m-code-category-delivery-r05-qa.json)、SHA256 `2d9c38afd55e294eeabc5361a85ce44d2cce5f0863ebdba5d22670d0c62d4622`。全実見画像のpath/SHA、座標移動、binding、helperのSHA、過去候補の不合格理由を記録した。両delivery manifestは `published=false`・正式採点未合格の候補状態である。参照先の予定文書への記述は原文どおり保持したが、参照先の公開完了は本QAの範囲外。
