# 第1稿の新規独立レビュー

入力は `test-project1/spec-analysis/CSharp_ASPNET/20261013-focus-round-01/spec/detail/student-search.md` と `student-editor.md`（文書version各1.0）。今回の原稿本文と各layout-001.pngを新たに読み、assisted capsuleのraw sources/Views/CSS/処理と照合した。原仕様・spec-eval・evaluator-onlyは参照せず、このレビューでreference-designs本文も追加読取りしていない。

今回のsource、MD、render manifest、実際に見た画像のSHAを `review-manifest.json` に記録した。review JSONは現行REVIEW schemaへ適合し、原ソース行番号、MDとrenderのsource hash、画像とartifact manifestのhash対応を今回検査した。前稿の合格は流用していない。新しいAI/CLIジョブとアプリ実行は0件、原ソース・MD・画像の変更はない。

検索はcritical 0、major 0、minor 2。この限定した原ソースレビューではapproved=true。前稿で不足した検索項目ごとの要求型、正規化、DDL型/NULL、述語、SQL型/Sizeの対応は今回の項目表で改善されている。残る指摘は未検索Viewerだけの静的図と、保存復帰まわりの文章量・別責務の重複。正式採点表の合格や意味の完全性を保証するapprovalではない。

登録はcritical 0、major 2、minor 2、approved=false。新しい画像にも共通headerがなく、原h1/24pxの主見出しがh3へ変わる。候補表min-width1050は復元されたが、原Editのwarning直下tableを、原文にないgridスクロール枠で包む差が新たにある。狭幅での挙動はDOM/CSSからの指摘であり、今回画像は幅1440の静的投影、狭幅実機試験は未実施。追加状態の併記と本文反復も残る。次稿では原_Layoutと適用CSSをAI解析の素材へ含め、ソースにないUI改善を生成途中で加えない。

登録の要求DTO→正規化列→保存DB型/NULL→パラメーターの直接対応も今回改善している。確認理由入力による確認キー解除と再確認、Snapshotと最新DBの区別、既存席保持と席増加、Unknownと確定成功、Resumeの保持page未補正を、欠落や誤りとして再掲していない。検索のPageSize=0描画例外もソース推論と明記されている。

現render manifestは両文書のstructure/display PASSを報告する。検索14図・10document tiles、登録19図・12tiles。このレビューで目視したのは2つのlayout画像であり、全tile/全図の目視合格を主張しない。display PASSを原画面構成や業務意味の一致へ読み替えず、今回の残存欠陥をfresh AI analysisと執筆の第2稿へ渡す。
