<!-- spec-meta: {"schema": "spec-md/1.0", "documentId": "SYNTHETIC", "version": "1.0", "path": "edge-whole-token.md", "sheets": [{"heading": "自由な章", "kind": "GRID", "sheet": "自由な章"}]} -->
# 人工fixture

## 自由な章

```mermaid
flowchart TD
 subgraph SG[架空の領域]
 A[入力] -->|条件InputValidationException又はArgumentException発生| B{判定}
 B -- 値10001件または1.0の場合 --> C[完了]
 end
```
