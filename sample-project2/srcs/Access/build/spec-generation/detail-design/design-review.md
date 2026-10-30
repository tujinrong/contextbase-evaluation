<!-- spec-meta: {"schema":"spec-md/1.0","documentId":"SP2-Access-DETAIL-REVIEW","version":"1.2","path":"sample-project2/srcs/Access/build/spec-generation/detail-design/design-review.md","sheets":[{"heading":"自己レビュー","kind":"GRID","sheet":"01_自己レビュー"},{"heading":"独立指摘と反映","kind":"GRID","sheet":"02_独立指摘"},{"heading":"限界","kind":"GRID","sheet":"03_限界"}]} -->
# Access 詳細設計レビュー

版1.2／2026-10-30。runId=sp2-ui-regenerate-20261029。DQA-UI10の7正本文書を対象とする。

## 自己レビュー

| 観点 | 照合 | 判定範囲 |
| --- | --- | --- |
| 合理性 | 6論理Comboへ6専用入力面。複数Pendingを禁止せず全原文を同時表示、親/子/分類の破棄範囲を保持 | 設計適合。新業務項目/機能/DB追加なし |
| 統一性 | 標準unbound TextBoxと実付属Label、11pt、元矩形/幅−360、同名対応、F06分類navigation例外を明記 | 設計適合。139実Controlの検査は後工程 |
| 見やすさ | 元Label同Caption/矩形、2Pending同時可視、Pageごと同期。shadowのみ/空欄/旧値の代替は不合格 | 静的根拠を確定。native可視/編集/長文は未検証 |
| 操作性 | Tab/逆Tabの論理置換、AltDown/F4/候補Esc、明示選択だけ採用、Noの焦点/原文とYes範囲、busy/MSG016 | 設計適合。実キーとサービス/DB0の証拠が必要 |

45文書/164H2/43LIST587行/427参照、92項目/17イベント、54DUI＋追加9条件、8厳密同一断片、論理/物理5表同48fieldIds、保護26文書を検査した。新6矩形/Labelと初期flagsは仕様表を検査し、製品を観測していない。

## 独立指摘と反映

Rootは3共有面案が部署/在籍の複数Pendingを同時表示できないと指摘し、6Comboごとへ改訂した。TabControl.SetFocusの旧指示を可視選択Page.SetFocus/安全Buttonへ置換し、対象owner同期・全件表示とfocus回復を分けた。TabIndexは既存値を維持して追加だけSection末尾採番、実順路は論理置換で定める。

RootはF06の幅480twipのCaptionを基本HTMLと同じ「分類」（※なし）へ統一し、必須/正常候補を維持するnavigation例外を承認した。通常preflight後の現入力SHAへ独立期待値を束縛する工程順にも同期した。検索復帰の全Pendingはfocus待ちでなく各面へ即時可視復元する。Rootはこれら修正済み7文書の意味を確認し、設計意味PASSと仕様freezeを許可した。対象ハッシュと認可範囲は[review.json](review.json)へ固定する。

## 限界

本設計のPASSは実Accessの可視性/候補キー/Tab/取消/保存前拒否・実DB/帳票/正式受入のPASSではない。前回と同じ8静的断片/51図の既存証拠は内容ハッシュ同一の範囲に限り、今回再描画/新製品合格と呼ばない。src/tests/UI契約/ACCDB/DBは本工程未変更・未実行、formalScore=null。
