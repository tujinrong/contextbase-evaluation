# Markdown表の列幅・折返し：凍結r15調査と未実装案

対象はsource-onlyの派生表示器。原稿・ソース・共有コード・凍結runtimeを変更していない。業務仕様や採点期待値は使用していない。下記CSSは提案であり、実装・描画合格・採用を意味しない。

## 固定した入力

- 調査ファイル：`agents/reverse-agent/.tmp/20261013-rerun-12h/source-only/runtime-code/source-09/src/contextbase/ai/rendering.py`
- ファイルSHA-256：`e5c0cfe3bb668f05655b6550af12a3a094164cad6245d19ff606142baf38bdf0`
- runtime receipt：`source-pilot/runtime-code-source-09.json`、SHA-256 `6566357d3989760c1bbd19afe751109bb5e85f2121c7a337d80d7ab8a805ce98`
- 実見根拠：`source-*-r15-02-native-review.json` の7文書、52原寸画像、129 lossless tiles。全tileを実際に閲覧し、原稿SHA・画像SHA・画素範囲を照合済み。合格を統計的に推測したものではない。

## 原因

`_markdown_table_open` 362–377行はMarkdown parser所有の表だけに属性とcolgroupを追加する。列数1は100%、2は24%/76%、3以上は先頭4%、末尾40%、残り56%を中間列へ均等分配する。先頭がNo列であるという前提を全表へ適用するため、分類ID・物理識別子・処理結果の列にも4%が割り当てられる。

`BASE_STYLE` 33行は `width:100%; table-layout:fixed` と各セル `padding:6px; overflow-wrap:anywhere` を指定する。1440px viewport・body両側16pxでは表幅は通常約1408pxで、先頭列は約56px、左右paddingと境界線を引いた文字領域は約43px。9列の中間列は約113px、文字領域は約100pxになる。最小内容幅より狭くても固定幅を維持し、anywhereが識別子の任意位置を折る。

実見例は category_name の末尾e、grade_category の末尾ry、長いphysical name、uniqueidentifier、分類ID、NoChange等。文字は残り、隣接セルとの重なりや欠落は観測していないが、途中折れで読みづらい。Mermaid図内の折返しは別経路であり、このCSS案では変更しない。

## 最小CSS案

3列以上のparser所有表だけを対象に、既存のcolgroup・DOM・セル順・文字列を保持したまま、trusted CSSで固定の列幅ヒントを無効化し、内容に応じた通常のtable layoutへ変更する。

```css
table[data-renderer-markdown]:not([data-renderer-columns="1"]):not([data-renderer-columns="2"]) {
  table-layout: auto;
}
table[data-renderer-markdown]:not([data-renderer-columns="1"]):not([data-renderer-columns="2"]) col {
  width: auto !important;
}
table[data-renderer-markdown]:not([data-renderer-columns="1"]):not([data-renderer-columns="2"]) th,
table[data-renderer-markdown]:not([data-renderer-columns="1"]):not([data-renderer-columns="2"]) td {
  overflow-wrap: normal;
  word-break: normal;
  white-space: normal;
}
```

`width:100%` と既存の境界線・padding・背景を維持する。1/2列表と埋込みのsource-screen表は対象外。auto layoutは通常の最小内容幅を考慮し、短いNo列には短い幅、識別子列には必要幅を配る。幅不足時には表全体がviewportより広がることを許し、既存のscrollWidth全幅captureへ渡す。列番号ごとの一律固定割合を増やすだけでは、別の表で問題が移動するため採用しない。

anywhereの削除だけでは、現行fixed幅を識別子が越えて隣セルへ重なる可能性があるため、列幅変更と同時に行う。全セルのnowrapは日本語説明も一行にして全幅を増やすため第一案にしない。normalは明示brや合法な句読点位置の折返しを無効化しないため、すべてのASCII tokenを一行にできるという保証はせず、下記の実測で判定する。

## synthetic実ブラウザ検査案

1. 現行r15とfresh提案版を別outputへ描画する。fixtureは合成の1/2/3/6/9/10列表にし、短いNo、長いunderscore識別子、datatype、分類ID、hyphen付き結果code、空/日本語説明/複数段落/inline code/明示改行を含める。source App・DBを実行せず、業務本文をfixtureへ転記しない。
2. CSS以外のDOMを前後照合する。table/colgroup/thead/tbody/行/セル数・順番・innerHTML・textContent・rowspan/colspanが完全一致し、原稿bytes/SHAが不変であること。埋込み画面表と1/2列表のcomputed style・bboxも変わらないこと。
3. フォント読込み完了後、各text nodeのRangeからglyph領域を測定する。合成fixtureでatomicと宣言した各tokenが同じ行にあること、文字矩形が所属セル内に収まること、隣セルの文字と重ならないことを許容誤差1pxで検査する。セルscrollWidthだけの判定では途中折れを見落とすため、tokenごとのRange.getClientRectsも確認する。既存brを削ることは許可しない。
4. 日本語の長い説明は通常改行され、tableが無制限に横長にならないことを複数viewportで測定する。全幅scrollWidthと全高をcapture metadata/PNG寸法に照合し、端や末尾を切らず全画素coverageを検査する。16000px幅・500000px高・250000000px面積という既存complete capture上限を越えた場合は明示失敗とし、縮小・切取りで合格にしない。
5. 旧anywhere＋4%配分を対照としてfixtureの途中折れを再現し、新CSSで直ることを確認する。負例はfixed＋normalだけで起こる長いtokenのセル越境、明示br入りtoken、capture上限越えで、誤ってPASSしないことを確認する。
6. 合成検査後、固定済み同じ原稿SHAをfresh derived outputへ再描画し、変更した表の全原寸tileを実見する。glyph欠落・セル順変更・見出し/出典の欠落・重なり・途中折れを確認する。synthetic PASSだけで実文書の視覚合格を宣言しない。

実装は親の合意後に別fresh版へ行う。現在deliveryが修正・検査中のmain、稼働中writer、原稿、既存描画は上書きしない。
