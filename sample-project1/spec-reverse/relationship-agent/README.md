# relationship-agent の未採用レビュー資料

**改名前test-project1の実行記録。** project移動後も証拠内のprojectId・絶対パス・hashは原値を保持する。新sample-project1は未解析で、現在の既定成果先は`spec-reverse/CSharp_ASPNET/`。ここに保持する旧成果・targetを新projectへ転用しない。ソースリンクは移動後の参照位置を示し、当時の根拠は記録されたsnapshotとhashで識別する。

**未採用・独立原文検証が未完了。正式ContextBaseではない。**

2026-10-28。確認入口は [review.md](review.md)。

- 入力: CSharp_ASPNET、78ファイル（共有DDLと由来記録を含む）
- 関係候補: 35件。ホストの候補機械検査を通過。
- Relationship側のDiscovery前提再検証は完了。関係義務は未採用。
- Discovery前提 SHA-256: `9c1f24b11ba15a7adc80a2497b19d2f989212eab1a613eafb7dbcb53ae0e627d`
- 候補 SHA-256: `5c3ea3ca057d6e2ad68a2fe75f773474fc3d5ab7492becbef361829763a2377b`
- Source snapshot: `24746f8d3f11ba3cfce6d2f0d6e0fafc811a9ad27c3076923bfd672c7c220ae0`

全量原文を含む最終検証は入力長上限で停止した。原文をファイルから読む方式では環境が読取りプロセスを起動できず、応答もunknownChecksの機械契約に違反して未受理となった。
これらは今回の検証経路の故障であり、補足DDLの正しさ・誤りやSharedAccess関係の意味検証結果を示さない。

contextbase.json・target.json・合格扱いの検証JSONは作成していない。behavior、原アプリ、SQL、DB、人手受入れは未実施。
