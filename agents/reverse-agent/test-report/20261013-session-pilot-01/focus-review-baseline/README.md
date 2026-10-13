# 学生検索・登録の独立レビュー

入力は `test-project1/spec-analysis/CSharp_ASPNET/20261013-pilot-v2-r2/spec/detail/student-search.md` と `student-editor.md`（各文書version 1.0）。照合は封印済み `.tmp/20261013-tuning-01/capsules/CSharp_ASPNET-assisted` のsources/indexed、ユーザー許可済みreference-designsに限定した。spec-eval、evaluator-only、リポジトリ外の原仕様は読んでいない。

本Agentの独立したAI判断を `student-search-review.json`、`student-editor-review.json` へ保存した。両方とも現行 `schemas.REVIEW` に適合し、参照位置はsnapshot内の原ソース相対pathと行番号で検査した。新しいCodex CLIジョブは0件。原ソース・既存MDは変更していない。正確な入力/出力SHAとsnapshot世代は `review-manifest.json`。

検索はmajor 1件、minor 2件。検索用項目ごとの受信値、正規化値、DB型/NULL、SQLバインドの直接対応を完成させる。氏名のNameKey 160、DB nvarchar(320)、検索@name NVarChar(642)は既存本文の別箇所に既に正しく存在するため、誤値・全欠落とは採点しない。特に年度のint?とsmallint NOT NULL、本人/緊急電話の2列と同一@phone、2つの日付入力と同じdate NOT NULL列、未所属とclass_id IS NULLを区別する。その他は状態契約の重複と、未検索Viewer図だけに留まる主要状態例。

登録はmajor 1件、minor 3件。静的画面図に共通ヘッダーがなく、原CSSの候補表min-width:1050pxを再現していない。実候補sectionはwarningでありdialogのmin-width解除は適用されない。修正はソースにないモーダル化やスクロール枠追加を避け、適用CSSと条件付きモードを再構成する。主要19項目の物理型/NULLは既存移送表で正しく記載されている。改善はパラメーター名/実SqlDbType/SizeとUI項目の直接対応、成立するモード別の図、Lookup等の反復説明の整理。

criticalとなる新たなソース矛盾は発見していない。確認理由入力によるキー解除と再確認、ResumeのApplied.Page未補正、Web確認のメモリ保持、保存確定と303後の復帰成功の違いは、既存本文が既にソースに沿って区別している。改善指摘のためにこれらを未記載と扱わない。

このレビューは今回の再解析・執筆への批評であり、原仕様採点表の点数、実画面撮影、実機試験、完全性の監査済み証明ではない。主要な契約不足と静的再構成差が残るため、両reviewのapprovedはfalseとした。新しい改訂はfresh AI analysisで原文からfactsを作り直し、writerへこれらの指摘を渡した後、改訂本文を再評価する。
