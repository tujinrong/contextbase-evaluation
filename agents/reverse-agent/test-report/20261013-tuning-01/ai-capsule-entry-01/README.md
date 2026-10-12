# evaluator専用領域・参照リンクの入口拒否

2026-10-13。production変更はsrc/contextbase/ai/capsule.pyだけ、試験変更はtest_ai_capsule.pyだけである。source root／明示authorized reference rootの全祖先でspec-evalを拒否し、resolve前safe_pathでsymlink／reparseを検査する。参照ツリーをfollowlinks=Falseで歩き、ディレクトリ・ファイルのリンクと評価専用領域を、読取り前に拒否する。

source側の既存EXCLUDED scopeは維持している。通常source配下のspec-evalは引き続き除外記録へ残り、source rootそのものをspec-eval配下へ指定した場合は拒否する。明示許可された設計資料だけをコピーし、共通仕様／期待表等へ参照範囲を自動拡張しない。業務名、表数、正解値はcodeへ固定していない。

[unittest.raw.log](unittest.raw.log) は54件PASS／FAIL・ERROR・SKIP 0。内訳はcapsule17（新入口8含む）、current provenance26、CLI11。provenance26は親担当の後続構造／根拠修復テストを含む現在版で、旧23や前工程74へ加算しない。新8は評価root、明示参照root、参照下評価領域、参照rootのsymlink、nestedディレクトリ・ファイルsymlink、reparse属性、source側の除外維持を検査する。reparse属性の負例はsynthetic lstatであり、実junctionの作成・操作試験ではない。symlink負例は実ホストで実施しskip0だった。

capsule試験のTemporaryDirectoryも.tmp内へ明示した。実AI・業務原本・原仕様・criteria・spec-eval内容は不使用。synthetic expected.md／expected.jsonだけを負例として作った。既存liveカプセルのmanifest／raw／indexedや元AI応答は本担当のツールで読んで書き換えていない。既に読み込まれた旧moduleのlive挙動とは別の、今後の新snapshot入口の修正である。

この試験は汎用境界検査であり、plan27文書の品質、正式採点、実SQL・UIの結果を保証しない。read-only独立レビューの指摘と一般修復ループ案は[generic-workflow-review.md](../generic-workflow-review.md)に保存した。
