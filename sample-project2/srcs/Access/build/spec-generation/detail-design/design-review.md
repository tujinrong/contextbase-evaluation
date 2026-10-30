<!-- spec-meta: {"schema":"spec-md/1.0","documentId":"SP2-Access-DETAIL-REVIEW","version":"1.1","path":"sample-project2/srcs/Access/build/spec-generation/detail-design/design-review.md","sheets":[{"heading":"自己レビュー","kind":"GRID","sheet":"01_自己レビュー"},{"heading":"独立指摘と反映","kind":"GRID","sheet":"02_独立指摘"},{"heading":"限界","kind":"GRID","sheet":"03_限界"}]} -->
# Access 詳細設計レビュー

版1.1／2026-10-30。runId=sp2-ui-regenerate-20261029。DQA-UI08/09の技術補正と新SHAを対象とする。

## 自己レビュー

| 観点 | 照合 | 状態 |
| --- | --- | --- |
| 合理性 | 既存の社員/経歴編集・原子保存/取消・一件コード保存・保存済みSnapshot出力を保持 | 業務/要件/基本/DB/auth/seed変更0 |
| 統一性 | 全管理文字11pt/固定幅と127Controlを保持。Section下限/標準Tab帯の物理配分だけ再設計 | 新候補で属性再検査、OS子文字は管理外理由を維持 |
| 見やすさ | F03選択時全文1980/固定Footer、F04 Header2400/Tab900の余白、Footer専用11pt | 静的8HTMLは同一。native通常/最大長/実clientは未検証 |
| 操作性 | 畳む前のfocus退避、Pending保護、未反映と保存境界、数字先頭氏名の書式境界 | source/個別期待値へ接続し、新候補で実操作/再読込が必要 |

45文書/164H2/43LIST586行/423参照、92項目/17イベント、54DUI、8厳密同一断片と保護26を再検査。51図の構文/SVGと実業務/DB/印刷の意味を混同しない。

## 独立指摘と反映

旧候補5a45…e584の独立DesignViewは非表示全文欄下端によるDetail9090、Tab780/Header2145を発見した。F03は初期330/Hidden→選択1980、F04はTab900/Header2400へ必要余白付きで再設計する。実測3値を期待値へ逆写ししていない。

Excel小試験の&10.5は読戻しだけでは誤りを検出できず、PDFで約10pt/.5混入を確認した。Footerだけ整数11ptを採用し、セル本文10.5を維持する。rootの独立PDF確認は製品帳票/実印刷のPASSと分ける。意味/新11候補SHA/76入力/根拠の再確認を[review.json](review.json)へ固定する。

## 限界

8HTMLの再描画は基本の代表配置図だけで、native物理Sectionの新寸法を証明しない。旧候補のcompile/45件API/データ保持は対象SHAだけに属する。新候補の全属性/GUI/キー/TopVisible/製品帳票/印刷/倍率/IME/正式受入・正式採点は別の実施状態とし、formalScore=null。UI未完をPASSへ集約しない。
