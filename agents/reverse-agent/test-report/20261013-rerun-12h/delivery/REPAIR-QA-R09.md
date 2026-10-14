# 派生変換器の修正と実ファイルQA

2026-10-13。固定 source-only `search-basic-03` の派生変換器候補。**原稿 candidate03 の最終書式は不合格のまま。納品／仕様内容95%合格は承認していない。** 元MD、ソース、原仕様、spec-eval、固定render HTML・PNG、AI実行コードは変更していない。

機械検査と全画像の実見記録: [repair-qa-final-r09.json](repair-qa-final-r09.json)。SHA256 `8ab7e7deb0b5c14e928154afc6a757e6f872b97cc27f43b62d72fa76b7f766f2`。

## 修正と確認範囲

| 対象 | 実施内容 | 検査結果 |
| --- | --- | --- |
| XLSX罫線 | public API `range.clear({applyTo:'formats'})` 後、必要な枠だけ指定。`preset:none` を削除。public API probeで neutral／none／outside を実保存・XML・native PNGで比較。 | r04の独立XMLで標準無罫線、枠外無罫線、3パターン、merged continuation検査PASS。native全42 tiles実見で不要黒罫線解消。 |
| XLSX画像投影 | 元PNGのSHA・ID・source行対応を保持し、最大幅1100→1850、QA tile高さ1200へ機械変更。 | 原本文字列645、meta、章/sheet順、13 PNG、モデルのvisibleCoverageを修正前後で完全照合PASS。座標・印刷範囲の差はJSONへ記録。 |
| XLSX literal | 数式は別拒否し、保存XMLの `t=str` を許可。元の文字列をそのまま保持。 | 645非空セル、5 sheets、13埋込み画像、数式0、印刷メタ情報PASS。`表紙!X18` はXML `str` / `1.0`、public再importもstring `1.0`。native画像は `1`。native表示差は未解決、Excelアプリ表示は未試験。 |
| PDF停止 | `add_style_tag` を使う経路を廃止。固定canonical HTMLの派生印刷投影だけにtrusted CSSを最初の外側 `</head>` へ挿入。段階JSONL／faulthandler／owned-worker timeoutを追加。 | trusted Chromium、JS無効、service worker禁止、全通信abortを保持。r09は10:36:23〜10:36:37 UTCで終了code0。90秒のstage timeout、900秒の全体上限、停止時は当該worker PID treeのみ対象。 |
| PDF文字 | MS Gothicを使用。font probeで日本語・漢字のUnicode抽出を比較。 | pypdf strictで全662文字列PASS。抽出一致は空白・soft hyphenだけ正規化、NFKC等による文字同一視は行わない。 |
| PDF図付録 | 大図の原PNGを900×600、60 px重複で画素だけ分割。元本文と分けた閲覧補助。全RGB255領域だけ非印刷化。 | 全58 tilesのSHA・元画素一致・crop box・重複を独立確認。全画素100% coverage、印刷された55 tilesは元の非白画素を100%網羅。白3 tilesは監査PNGを保持。 |
| PDF実見 | Popplerで全ページPNG化し、原サイズで閲覧。 | r08全109ページ実見、白紙付録3ページを検出。r09全106ページ実見、白紙付録解消。ただし大図全体の文字縮小、境界をまたぐラベル・接続線中心の拡大ページ、改ページ余白が残る。公開用視覚判定はFAIL。 |

追加検査: `test_connections` と `test_literal_xml_types` の16 tests PASS、Node builder構文PASS、保存XLSXの独立XML再検査PASS。開始markerはrootで既に成功したものを使い、再実行していない。セル・罫線・画像のOOXML直接作者編集は行っていない。承認済みの印刷メタ情報だけの接続を保持。

## 固定入力と派生出力

- MD: `基本設計書/01_学生検索画面.md`、SHA256 `ef7967cf6f086e0475f7a747709afb3abdc1bd7e6813afa5d524956a6d8c3a21`。
- binding SHA256 `7173121452ede395c67e86b67f1f67a886520df6aa964c291b6fa47733ea9f69`。元MD・render pins・manifestを最後に再照合。
- canonical HTMLのコピーSHA256 `523103269041cc3538e8457ec17a06dd99191d10edbcea28b93b9177086aa49b`。文中のhead例を含む原HTML自体は不変。
- [r04 XLSX](xlsx-search-basic-r04/Excel/基本設計書/01_学生検索画面.xlsx)、SHA256 `61029ddcab28b54338984d746bbca637ac57112a5659e327f5d54187c7734ec1`。
- [r09 PDF](pdf-search-basic-r09/PDF/基本設計書/01_学生検索画面.pdf)、SHA256 `11e9866477ffe616801faa63b471aeb4d1e40674396a40a3e9f586cc88086684`。

失敗したr02以降の候補は保持。元stem／階層を維持し、既存の納品outputは入れ替えていない。

## 残件

この候補を納品する前に、原稿の最終書式不合格を本文担当工程で解消する必要がある。大図は原稿側の図の構造／幅／文字サイズを改善してから再描画・全ページ検査するか、原PNGを開く導線を伴う閲覧方式を別途採用判断する。機械的に追加した拡大tileは業務仕様の追記ではない。

nativeの数字らしい文字列表示差は元値を改変して合わせない。XLSX XMLのliteral完全一致とnative表示の不一致を残し、Excel実アプリ表示は別検査する。原アプリ実行、SQL実行、正式評価95%採点、全11件の納品合格は本担当では未実施。
