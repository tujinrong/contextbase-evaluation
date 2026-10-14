# Assistedテーブル2件の派生形式QA

m_studentとm_codeの同名HTML・PDF・Excel候補を作成し、全セル・空欄・行順・書式の機械検査と全105画像の原寸レビューを完了した。正式採点と公開はrootの判断に残す。

| 原名 | 版 | PDF全頁 | 非空literal／空欄 | 原寸画像 HTML／PDF／XLSX |
| --- | --- | --- | --- | --- |
| 01_m_student.md | 1.0 | 36 | 312／90 | 11／36／11 |
| 04_m_code.md | 1.1 | 32 | 209／32 | 7／32／8 |

ExcelはArtifact Tool公開APIで著作。各原宣言の単一9列sheet、原順序の全文preamble・節見出し・表セル・空欄・キーを保持し、521非空literalと122空欄、数式0、結合・列幅・印刷範囲・枠外無罫線を独立検査した。24ptのNOT NULL見出しが下端で切れた旧候補を保存し、4見出し行の高さだけ36ptへ変更したfresh r03で解消した。変更前後のモデルは行高以外完全一致、実XLSXのstyles/sharedStrings/table bytesも一致した。sheet XML差分は4行の高さとArtifact Toolが生成するtable relationship IDであり、同一targetとtarget bytesを解決照合した上で他の全XML一致を検査した。native全4範囲を原寸19切出しで全画素実見。print metadata接続前のnative描画であり、実Excel全体表示・印刷は未実施。

PDFは同一canonical HTMLを元にJS無効・通信拒否・90秒stage timeoutで生成。元表の2データ行ごとに同一列見出し/colgroupを印刷投影へ複製し、2表目は新頁から開始する。全135本文行の値と順序、全68頁の列見出しを機械照合し、Poppler全頁を原寸実見した。切れ・行重なり・列見出し欠落は見つからなかった。安全側の2行単位のため頁内余白は多い。

HTML全キャンバスは18切出しで原画素一致・80px重複・全coverageを確認し、今回実見した。rootが現main rendererをr14へ変更したため、r12の不変を現mainに対しては主張しない。生成時renderer0c87…と同byteの凍結assisted05 rendererを基準に既存HTML/PNGのSHAを再確認し、生成・別review・構造検査runtime receipt各124ファイルの完全inventoryも再確認した。原稿・source・元spec/evalを変更せず、元アプリ/DB・開始markerを実行していない。

`01_m_student.md` — 原MD SHA256 `d049a245c2862d82fc48a4e4b32f7fc6f5ac1e8e1645449bc60dc08e98a769d8`。

- [HTML](<D:\開発\contextbase-evaluation\agents\reverse-agent\test-report\20261013-rerun-12h\delivery\pdf-assisted-tables-r04\html\基本設計書\テーブル\01_m_student.html>) — `2c795d6d76eb21dd05d32abc432f3347085c7b0313091b15762c4fac74bbda83`
- [PDF](<D:\開発\contextbase-evaluation\agents\reverse-agent\test-report\20261013-rerun-12h\delivery\pdf-assisted-tables-r04\PDF\基本設計書\テーブル\01_m_student.pdf>) — `bd5d7ee799972d8a6c93c61c6987df32f889d9c2ee0182d165774d6f9a4b6e65`
- [XLSX](<D:\開発\contextbase-evaluation\agents\reverse-agent\test-report\20261013-rerun-12h\delivery\xlsx-assisted-tables-r03\Excel\基本設計書\テーブル\01_m_student.xlsx>) — `0dd8c2c45d2292607143dcc5c0da550c08c6a9ca30d6283afecbdc60f84ef941`

`04_m_code.md` — 原MD SHA256 `982bc171fd46eb50032833b992c702bc60e9efcdfc31a7fa5997e81c459c3cca`。

- [HTML](<D:\開発\contextbase-evaluation\agents\reverse-agent\test-report\20261013-rerun-12h\delivery\pdf-assisted-tables-r04\html\基本設計書\テーブル\04_m_code.html>) — `7522a1e614ebd7536989c858c55acab14e862a718cbd4a2e84113c56432bf84e`
- [PDF](<D:\開発\contextbase-evaluation\agents\reverse-agent\test-report\20261013-rerun-12h\delivery\pdf-assisted-tables-r04\PDF\基本設計書\テーブル\04_m_code.pdf>) — `839d3a2f2142809a36c4f00e0e3d6664f035fa5c3714c9d449f1f9054fb71dc6`
- [XLSX](<D:\開発\contextbase-evaluation\agents\reverse-agent\test-report\20261013-rerun-12h\delivery\xlsx-assisted-tables-r03\Excel\基本設計書\テーブル\04_m_code.xlsx>) — `68cbbd518a88bc5438a243c8d7c55c5b485c562d3e82fe50dd77a463aae73af4`

[詳細QA](<D:\開発\contextbase-evaluation\agents\reverse-agent\test-report\20261013-rerun-12h\delivery\assisted-tables-r03-final-qa.json>) SHA256 `cd1e6356fef25d0b49a0cea5325a29117312d1b9e461835194951c094be405f5`。
[候補manifest](<D:\開発\contextbase-evaluation\agents\reverse-agent\test-report\20261013-rerun-12h\delivery\assisted-tables-r03-final-manifest.json>) SHA256 `11967b484f64ea1befbe371ae779ff92d2026ab0dfec9c6ca713741de1cf6139`。
