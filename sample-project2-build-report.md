<!-- spec-meta: {"schema":"spec-md/1.0","documentId":"SP2-BUILD-REPORT","version":"2.1","path":"sample-project2-build-report.md","sheets":[{"heading":"実行条件","kind":"GRID","sheet":"01_実行条件"},{"heading":"工程の状態","kind":"GRID","sheet":"02_工程の状態"},{"heading":"検証の範囲","kind":"GRID","sheet":"03_検証の範囲"}]} -->
# sample-project2 追加画面品質対応

2026-11-04。今回の追加対象はAccessの入力高・整列・描画制御・スクロール復帰です。本文11pt、単行入力高360twip、ログイン同幅4800twip、タイトル18pt/540twipを適用しました。最終候補のコード/API検査は実施済みで、最終実画面の確認はデスクトップの解除状態の確認待ちです。

## 実行条件

| 項目 | 内容 |
| --- | --- |
| 今回の実行ID | sp2-access-ui-compact-20261104 |
| 対象 | sample-project2 / Access。CSharp_ASPNETは今回変更・再検査していない |
| 仕様 | Accessの基本/詳細・共通・QA等19文書をUI限定で同期。DQA-UI12/13を採用 |
| 入力凍結 | 70入力、構造指摘0、独立期待663条件/170部品 |
| データ | 元5表48列の全typed row/schema・認証情報を保持。seed/資格情報resetなし |
| 配置 | 固定build/、試行.tmp/、履歴Git。commit/pushは実施していない |

## 工程の状態

| 工程 | 現在の状態 |
| --- | --- |
| 画面/Agent規約 | 過大な単行高、自動サイズ機能の誤認、短い描画scopeと復元責務を共通Access規約・build契約/チェックへ反映 |
| Accessコード | 高さ/余白・同型ペア・タイトル・操作/ラベル、描画scope、同値更新抑止とセクション別スクロール復帰を実装 |
| 配布物 | Access/build/CareerManagement.accdbとsource.zipを固定先へ更新 |
| 正式UI適合 | 最終実画面と全663条件の証拠は未完。正式outputs未発行、formalScore=null |

## 検証の範囲

コンパイル/全11クラス、保存属性475条件、描画制御11条件/7状態、画面状態API104条件、認証39条件、日本語34モジュール/11文字列、全データ保全、48ファイルのZIPと独立source-only再構築を確認しました。中間候補の5Form/6表示の結果を、最終候補の実画面PASSへ流用していません。

Excel出力は44条件通過後に内容検査MSG-037で失敗しました。変更前の元ACCDBでも同じ失敗を対照確認し、今回Excel出力の実装は変更していません。原因は未確定です。

最終候補のSHAと詳しい範囲・未実施は[Access修正報告](sample-project2/srcs/Access/build/test-results/ui-compact-review.md)と[検査記録](sample-project2/srcs/Access/build/test-results/ui-compact-review.json)を参照してください。IME/clipboard/他環境、同値Pendingのマウス採用、実Excelプレビュー/紙印刷、利用者受入・正式採点は別に残ります。
