# 原減点を保持する採点指示

R5のm_code_category初回正式batchは採用しない。S001は引用183件すべて有効だったが、誤り・粒度不足の判定2行を減点0として返したため検証失敗。S002はprovider通信失敗で原回答なし。原回答・CLIイベント・失敗receiptを保存し、Pythonによる回答修復や減点変更を行っていない。

R6は採点指示だけを明確化した。反復する欠陥も各行で許可済み負の原減点を返し、別の独立AIが同じ原因と意味単位を確認した後に集計で最大減点を1回計上する。分母、許可減点、固定期待値、検証条件は変更していない。コードを新しいbatchに封印し、同じ原稿SHAを再評価する。

基盤29件・集計29件がPASS。別のimmutable retry helperは、未完了原job・採用回答のSHA違いを拒否し、採用回答だけbyte-copyで再利用する4件の検査がPASS。既存batchのgrader版が異なる場合に旧回答を流用する機能ではない。

- [基盤検査](infrastructure-verification-raw-deduction-r6.json)
- [集計検査](combiner-verification-raw-deduction-r6.json)
- [原引用の診断](batches/source-m-code-category-r03-r5/evidence-diagnostic.json)

仕様書の正式得点・95%達成は未確定。
