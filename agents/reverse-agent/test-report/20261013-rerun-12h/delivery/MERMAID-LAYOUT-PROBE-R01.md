# Mermaid配置の短期試作

本文のgeometry改訂を避けられる修正は、まずtrusted label CSSの不透明化である。両図とも元SVGの全座標・path・tspan配置を変えず、辺ラベルへの線の透過を解消できた。core・MD・source・grade cap・bindingは変更していない。

公式[Flowchart config schema](https://mermaid.js.org/config/schema-docs/config-defs-flowchart-diagram-config.html)にはnode/rank spacing、padding、wrappingWidth、minNodeWidthがあり、公式[theming](https://mermaid.js.org/config/theming.html)はinitializeでの設定とedgeLabelBackgroundを説明する。今回のbundled Mermaidは12.1.0で、これらの公開型定義も確認した。自動折返しの公開スイッチは[Flowcharts syntax](https://mermaid.js.org/syntax/flowchart.html)のmarkdownAutoWrapである。設定の存在と、この2図での実効果を分けて検証した。

元SVGの `.edgeLabel rect` はopacity=0.5である。次のtrusted themeCSSをMermaid初期化へ固定すれば、アプリのMD文字列を変えずに適用できる。CSS自体はネットワーク資源を含まず、既存SVG検査も通った。

```css
.edgeLabel rect { opacity: 1 !important; fill: #ffffff !important; }
.edgeLabel .labelBkg { background-color: #ffffff !important; }
```

| 試作 | source detail図25 | assisted register図19 | 原寸での結果 |
| --- | --- | --- | --- |
| opaque CSSのみ | 1835×322 | 1049×3043 | 線の透過が解消。geometry完全不変。単語途中の折れ／長図の高さは不変 |
| wrappingWidth320 / minNodeWidth120 / nodeSpacing50 / rankSpacing60 / padding15 | 2102×308 | 1110×3191 | ノードの折返しは改善するが、sourceのFK辺ラベル末尾折れは残る。長図は高くなった |
| wrappingWidth240 / minNodeWidth100 / nodeSpacing28 / rankSpacing25 / padding10 | 2054×311 | 1051×2995 | 長図の高さは48px、約1.58％減に留まる。PDFの一頁縮小問題は解消しない |
| 追加markdownAutoWrap=false | 上記と同一 | 上記と同一 | 6候補すべてSVG/PNG SHAが同一。この2つのtraditional-string図には効果なし |

6候補で元節点ID・節点文字・辺ID・矢印の有無・solid/dotted/dashed・条件ラベルの対応を照合した。sourceは6節点10辺10ラベル、assistedは21節点26辺25ラベルを保持する。再配置版の文字照合は折返しによる空白を除いた文字列署名であり、MMDはbytes SHA不変。CSSのみの候補は全SVG geometryも完全一致する。

全6候補を14個の原寸cropで実見した。各cropは元PNGと全画素一致、全キャンバスcoverageを検査済み。寸法が2048pxを超える全体表示は原寸判定に使わず、横100px／縦80px重複のcropで全領域を確認した。trusted MermaidだけJSを有効にし、静的SVG画像化はJS無効・通信拒否で行った。アプリHTML/JS/C#/SQLは実行していない。

source図25の改善候補は [opaque CSS PNG](mermaid-layout-probe-r01/source-search-detail-025/opaque-css-only/diagram-025.png)。辺ラベルの `grade_code` の途中折れは公開wrappingWidth設定だけでは残り、さらにspacingを触っても有効な改善を確認できなかった。全体を無条件にwide/compact設定へ切り替える根拠はない。今回は不透明CSSだけをrootが採用検討し、残りの図レビューへ戻すのが適切である。

register図19は設定だけで一頁の可読性を保証できない。元の全体図を維持し、印刷では機械的な領域分割・拡大の閲覧補助を別QAする方法が残る。分割時の線の連続性とcrop境界を確認し、図本文の工程を新規に組み立てない。

根拠は [layout-review-final.json](mermaid-layout-probe-r01/layout-review-final.json)、SHA256 `c9745930a11ad4d3d7cb0182a6b2eb159ffab162719a07149b3816c2b01ddf03`。節点/辺/ラベル対応、原寸画像SHA・crop領域、元出力とcoreの前後SHA、公式URLを収録した。全候補は非公開で、業務意味・正式採点・実アプリ試験の合格を主張しない。
