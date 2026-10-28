<!-- spec-meta: {"schema":"spec-md/1.0","documentId":"SP2-BASIC-DESIGN-REPORT","version":"1.5","path":"sample-project2/build/basic-design/report.md","sheets":[{"heading":"入力と改訂範囲","kind":"GRID","sheet":"01_入力と改訂範囲"},{"heading":"検査結果","kind":"LIST","sheet":"02_検査結果","key":["検査"]},{"heading":"未実施と引継ぎ","kind":"GRID","sheet":"03_未実施と引継ぎ"}]} -->
# 基本設計 生成・検査記録

仕様セット版1.5／2026-10-28／projectId=sample-project2／stage=basic-design。

## 入力と改訂範囲

対象：Access・CSharp_ASPNET。変更前仕様セット1.4を入力とし、利用者の『4、5個以上の処理手順は階層化』をQA-023で継承する。入力/出力の各文書版とSHA-256はmanifest.jsonに固定した。Agent1.5、仕様書作成ルール7.12、MD構造・Excel変換規約7.9を適用する。

4手順以上は目的別の大項目と具体手順の小項目へ分け、同階層2～4項目を目安とする。手順2.1等の本文/CHK参照も同期した。両方式で32イベントを2階層化し、F01-E02の2イベントは3手順の平坦リストを維持。共通04の6検査とAgentの9実行手順も階層化した。業務条件・実行順・CHK/MSG・DB・項目表・画面と図は維持する。

## 検査結果

| 検査 | 結果 | 対象・根拠 |
| --- | --- | --- |
| 文書構造・参照 | PASS | 61文書のspec-meta、章、LIST矩形/キー、ローカルリンク、方式内依存、MSG/CHK参照 |
| 階層・原文・順序 | PASS | 34イベント、32階層化・2短手順維持、元216手順を保持。階層連番、インデント、参照経路を確認 |
| 意味保持・独立レビュー | PASS | 番号変更とグループ見出しを除き処理内容・順序・分岐・エラーを維持。内部参照とCHK対応を独立確認 |
| 不変部分 | PASS | 166項目行、14HTML断片、56Mermaid定義、10テーブル分冊の前版比較。DB/メッセージ/Pilot条件も維持 |
| Markdown解釈・目視 | PASS | CommonMark/GFM解釈で34イベントの親子リスト/216末端項目を確認。F01-E01/F04-E03を1366×900・100%・Edge headlessで描画し目視 |

## 未実施と引継ぎ

今回の描画は仕様文書の手順階層の確認。変更のない画面HTMLやMermaid図の再描画は実施せず、現版と入力版の断片一致を確認した。過去の描画合格を今回の新規描画結果として転記していない。

実装/ビルド、物理DB/実DB、実アプリ操作、Pilot41シナリオの実行、実Excel帳票、設計書のExcel変換/読戻し、印刷、性能、利用者受入、正式採点、Git commit/merge/pushは未実施。formalScore=null。既存Excel変換器での入れ子保持は別途対応・読戻し検証が必要であり、本改訂からExcel互換PASSとしない。固定JSONは今回の入力/出力と検査範囲を示す。
