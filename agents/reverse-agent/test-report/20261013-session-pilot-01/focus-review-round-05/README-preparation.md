# 第5稿の独立原文・実画像レビュー準備

新しい出力20261013-focus-round-05とjobs focus-round-05だけを対象にする。現在は新MD/PNG未完成のため、approved=null、visualFidelityVerified=false。完了した稿のdraft-resultとcanonical manifestを照合し、新しく全layout/処理図/SQL・ER図/全文tileを実閲覧してSHA付き一覧を保存する。旧レビューを新稿合格へ流用しない。

review-preparation.jsonに6つの重点を原ソース位置で固定した。今回はsourceのController Save/Search/Load/Reset/FormGuard、service入力catchと確認key判定、保存DTO移送を読み直した。source-pins-before.jsonは32ファイルを新しくhash取得した開始時記録で、全32ファイル意味読取りの主張ではない。新稿の手順/図/結果は未確認である。

保護対象はprotected-before.jsonの179 distinct pinsを現在とSHAだけ比較した。focus-protected-check-05.jsonは179unchanged、0changed、0missing。元ファイル内容を意味読取りせず、原仕様/spec-eval/evaluator-onlyの本文を開いていない。protected baselineそのもののSHAも不変を確認した。チェックscriptはcheck_protected_sha.ps1で、workspace内の絶対path確認後にGet-FileHashだけを行う。

同機能の許可reference-designを次の照合で使う場合は出自と閲覧範囲を別記録にする。今回の準備では参考設計本文、正式評価期待値、採点内容は読まない。原アプリ/SQL/DBを実行せず、外部AI解析/執筆/描画を起動せず、source/生成MD/productionを変更していない。現在第5稿runner c63aca…/frozen runtime13を、旧第4稿runner cae525…や将来のproduction改訂と同じ版に扱わない。
