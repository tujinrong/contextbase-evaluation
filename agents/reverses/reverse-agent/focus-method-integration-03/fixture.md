<!-- spec-meta: {"schema": "spec-md/1.0", "documentId": "SYNTHETIC", "version": "1.0", "path": "fixture.md", "sheets": [{"heading": "自由な章", "kind": "GRID", "sheet": "自由な章"}]} -->
# 人工fixture

## 自由な章

<section class="random-container"><style>.random-container{width:620px;background:#f1f5ff;padding:12px}.random-container input{width:180px}</style><form><label>架空項目<input value="TEST-RENDER-0001" readonly></label><table><tr><th>架空列</th></tr><tr><td>表示のみ</td></tr></table></form></section>

```mermaid
flowchart LR
 A[開始] --> B{判定}
 B -->|成立| C[表示]
```

```mermaid
sequenceDiagram
 participant A as 呼出側
 participant B as 保持領域
 A->>B: 架空要求
 B-->>A: 架空応答
```

```mermaid
erDiagram
 ENTITY_A ||--o{ ENTITY_B : relates
 ENTITY_A { int id PK }
 ENTITY_B { int id PK }
```
