# Assistedテーブル2件の派生形式QA

2件の同名HTML・PDF・Excel候補を作成し、文字・順序・空欄・罫線の機械検査と全45画像の原寸レビューを完了した。正式採点・最終公開の合格は本記録に含めない。

対象はtraining-assistedの固定manifest `e76a6c40e8927011fff9145d5f5ab2fa94ad89acefc9a03bbad0cbf09b85a0e7`。原稿・固定描画・AI receipt・別承認レビューのSHAを文書ごとに独立して記録した。原仕様/spec-evalは読まず、元アプリ/DBを実行せず、本文を編集していない。

| 原名 | 版 | MD SHA256 | PDF全ページ | Excel literal/空欄 | 原寸画像 |
| --- | --- | --- | --- | --- | --- |
| 03_m_code_category.md | 1.0 | `abf9dfb20de0e68223d75ace8f9fdb78fa6069b470c2265c5c7d18404246cd06` | 10 | 142/26 | HTML 4・PDF 10・XLSX 4 |
| 02_m_class.md | 1.1 | `713c201ef07b7b815fcae3b19468990097d3feca39da9263910272c1570b9384` | 15 | 208/40 | HTML 6・PDF 15・XLSX 6 |

Excelはbundled `@oai/artifact-tool`で著作し、開始markerは再実行していない。各原宣言の単一sheet、9列、原順序の全文preamble/節見出し/表セル・空欄・11件と17件の項目キー、正本IDと版を保持した。全350非空セルはliteralで数式0。枠外無罫線、結合・列幅・印刷範囲を独立XML検査した。printメタ情報だけを既存接続器で追加し、セル・罫線のOOXML著作はしていない。native画像はprint接続前のArtifact Tool描画であり、実Excel全体表示・印刷は未実施。

PDFは信頼済ChromiumでJS無効・通信拒否、所有worker 90秒stage timeoutのまま作成した。同一canonical HTML bytesを同名で保存し、印刷投影だけ4データ行ごとに元の見出し/colgroupを複製した。全95本文行はHTML bytesと原順序が一致し、pypdfで全文と全25ページの列見出しを確認した。Poppler全25ページを原寸で実見し、切れ・行重なり・見出し欠落は見つからなかった。

HTMLの元PNGは1440×4464と1440×6412。計10個の原寸切出しは全画素一致・80px重複・全キャンバスcoverageを確認した。XLSX native全10tilesも9列・全行を覆い、日本語・長文折返し・罫線・節見出しを確認した。単語の折返しは元文字列を変更せず表示上で行われる。

監査コードの一律版1.0仮定で初回検査を停止した。classの原版は1.1であり、原spec-meta JSON全項目と厳密照合する検査へ修正した。旧監査コードを保存した。この修正で稿や生成物の文字を変更していない。

`03_m_code_category` の成果とSHA：

- [HTML](<D:\開発\contextbase-evaluation\agents\reverse-agent\test-report\20261013-rerun-12h\delivery\pdf-assisted-tables-r01\html\基本設計書\テーブル\03_m_code_category.html>) — `0be6a3710bcaf8867898c49ce2369c80fe81b539932873e0eea152b2ef56f789`
- [PDF](<D:\開発\contextbase-evaluation\agents\reverse-agent\test-report\20261013-rerun-12h\delivery\pdf-assisted-tables-r01\PDF\基本設計書\テーブル\03_m_code_category.pdf>) — `46de81bf47466f71cc5241a7b3aba9867b68855b971a4ab663b9eb0d3a6ccbc6`
- [XLSX](<D:\開発\contextbase-evaluation\agents\reverse-agent\test-report\20261013-rerun-12h\delivery\xlsx-assisted-tables-r01\Excel\基本設計書\テーブル\03_m_code_category.xlsx>) — `64efa89b77e6315e94f5ce95f05b0751ee71c63b435ca1a19f45f41842b529fc`

`02_m_class` の成果とSHA：

- [HTML](<D:\開発\contextbase-evaluation\agents\reverse-agent\test-report\20261013-rerun-12h\delivery\pdf-assisted-tables-r01\html\基本設計書\テーブル\02_m_class.html>) — `f36cd12311da43bd3712672d817b688577f6a60cd009770a4546541db6bb503d`
- [PDF](<D:\開発\contextbase-evaluation\agents\reverse-agent\test-report\20261013-rerun-12h\delivery\pdf-assisted-tables-r01\PDF\基本設計書\テーブル\02_m_class.pdf>) — `9306d87d474e4fcdedd68463adac64e3b22edcb23be48377f32de6c4742af1a4`
- [XLSX](<D:\開発\contextbase-evaluation\agents\reverse-agent\test-report\20261013-rerun-12h\delivery\xlsx-assisted-tables-r01\Excel\基本設計書\テーブル\02_m_class.xlsx>) — `fa10aeb61e440df35f5a2dc608f27c12956f24930280282f34a3f9bfd1a3551d`

詳細証跡は [assisted-tables-r01-final-qa.json](<D:\開発\contextbase-evaluation\agents\reverse-agent\test-report\20261013-rerun-12h\delivery\assisted-tables-r01-final-qa.json>)、SHA256 `441c7ddfe6a81a4a8294e7c10d01307e91b3f4ed3b4f81ef0198134a2498d4f5`。正式採点と公開の判断はrootに残す。リンク先計画文書の公開状態は本QAの対象外。
