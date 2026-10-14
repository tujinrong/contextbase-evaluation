# 表示専用の辺ラベル改行 prototype

`edge_label_projection_r02.py` は `flowchart` / `graph` の plain pipe と `-- text -->` 形式の辺ラベルだけを対象にします。Latin 識別子・数値の境界へ `<br/>` を挿入し、原文字・引用符・entity・著者の改行を保持します。canonical Markdown、main、依存パッケージは変更していません。

`test_edge_label_projection_r02.py` の37試験は PASS。引用符付きpipe、arrow-like文字列、入れ子shape、YAML/init/comment、数値、可逆性、再実行時不変、巨大token拒否を含みます。`mermaid-edge-projection-r04/probe.json` は trusted bundled Mermaid12.1.0 の public render API で12ケースを比較し、`actually-viewed-final.json` は24画像すべてを原寸で実見した範囲です。承認済み索引の図005/008/011は node/edge/label signature 一致、識別子の途中折返し解消を確認しました。

合成負例2件では、矢印のような文字列の `>` を Mermaid の元表示が落とし、投影表示では残しました。この差を改善とみなさず signature 不一致として拒否します。別の巨大tokenは元文字を分割せず、実SVGの一行へ収まらないため作者の改訂が必要と判定しました。entityは元Mermaidのescaped字面を維持しており、元のentity解釈の修復を行いません。

root統合では、元MMDと派生MMDのSHA/挿入offsetを記録し、元の復元・二度目の投影不変を必須にしてください。その後同一trusted設定で両方を描画し、structured signature一致、原ラベルとの対応、実SVGの一行に全tokenがあることを検査します。描画された全図と各派生形式の原寸レビューが別途必要です。一般のMermaid構文の完全parserを主張せず、曖昧・非対応の入力は書換えず拒否または元表示へ戻します。

原因のprimary sourceは実probeにpath/SHA/行を記録しました。`insertEdgeLabel` は plain SVG辺へ width を渡さず、`createText` は200pxへ既定化します。nodeのtrusted `flowchart.wrappingWidth=320` は別経路です。public config単独ではこのplain辺ラベル幅を変えられないことを、先行 `mermaid-edge-width-probe-r01` でも検証しています。

production統合、索引全152 PDFページ、新rendererでの全書式納品、正式品質採点、公開はこのprototype検査に含みません。
