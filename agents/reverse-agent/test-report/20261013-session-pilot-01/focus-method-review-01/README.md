# 作成方法の検査改善：文書IDの対応

2026-10-13。今回の入力は汎用validator、bound planを使用するworkflow、人工fixtureのテストだけ。業務期待値、spec-eval、evaluator-only、案件の原仕様はこの改善の入力として読んでいない。

従来は外側DRAFT JSONのdocumentId/pathをplanと比較していたが、Markdown内のspec-meta.documentIdは非空確認だけだった。外側のIDとpathが正しくても、本文に別文書のIDを持つ原稿を構造合格へ進め得る。作成工程の対応漏れとして `finding.json` に記録した。

`validate_document(content, path, *, expected_document_id=None)` を追加し、指定時は実際のspec-meta IDをbound document IDと完全一致で比較する。不一致はメタ情報の行にERROR `META_DOCUMENT_ID`。workflow.document/reviewの2箇所から `definition['id']` を渡す。大小文字や空白を勝手に補正せず、原Markdownを書き換えない。2引数またはNoneで呼ぶ独立converter等は従来の動作を保持する。

AIは引き続き解析facts、本文、批評、訂正を執筆する。Pythonはsource-derived planとの識別対応を検査し、原応答を保持する。固定業務名、業務値辞書、案件別の正解IDをproduction codeへ加えていない。AIが承認を返しても、このID不一致は既存ReviewStructureConflictで受理しない。

最終検査は112件、22.478秒、exit 0。内訳はvalidation 57、provenance 28、resume 24、plan_context 3。負例では外側JSONが正しい人工CART原稿に本文ID OTHERを埋め、STRUCTURE_INVALID、原稿不変、独立AI承認の拒否、review-verified非生成を確認した。正常ID、既存呼出し互換、本文やfence内の偽装一致、大小文字・空白差、欠落ID、不正なexpected引数も検査した。

`tests-before.json` と `tests-after.json` は対象6ファイルの正確なSHAと検査前後不変を記録する。終了時刻は2026-10-13 06:34:48 JST。raw logは `tests.raw.log`。rootが追加した全AI計画のcontext伝達テストもこの最終SHAで検査した。過去の回帰合格は今回の改訂の検査結果へ流用しない。

今回未実施：新しいAIジョブ起動、業務意味の採点、実アプリの実行、既存成果物本文の書換え。既に実行中のPython工程がこの改訂を読込済みであることも、このunit検査からは主張しない。
