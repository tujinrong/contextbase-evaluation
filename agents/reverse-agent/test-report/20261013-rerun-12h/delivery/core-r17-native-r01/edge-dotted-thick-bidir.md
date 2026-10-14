<!-- spec-meta: {"schema": "spec-md/1.0", "documentId": "SYNTHETIC", "version": "1.0", "path": "edge-dotted-thick-bidir.md", "sheets": [{"heading": "自由な章", "kind": "GRID", "sheet": "自由な章"}]} -->
# 人工fixture

## 自由な章

```mermaid
flowchart LR
 A[入力] -. 条件ArgumentException発生 .-> B[判定]
 B == 条件InputValidationException発生 ==> C[結果]
 C <-- 値10001件 --> D[終了]
 D <== 条件ErrorCode発生 ==> E[参照]
 E <-. 値1.0の場合 .-> F[完了]
```
