<!-- spec-meta: {"schema":"spec-md/1.0","documentId":"SP2-DETAIL-RUN","version":"1.0","path":"sample-project2/build/detail-design/report.md","sheets":[{"heading":"成果物と入力","kind":"GRID","sheet":"01_成果物と入力"},{"heading":"検査・レビュー・保全","kind":"GRID","sheet":"02_検査・レビュー・保全"},{"heading":"採用判断と残件","kind":"GRID","sheet":"03_採用判断と残件"}]} -->
# sample-project2 詳細設計の生成・確認記録

版1.0／2026-10-29。AG-DETAIL-DESIGN 1.1、stage=detail-design、generationMode=canonical-update。

## 成果物と入力

AccessとCSharp_ASPNETの2方式で、各6機能の詳細仕様、方式別共通、物理DB定義の総則と5テーブル分冊、開発規約、詳細設計QAを作成した。新規は各15文書・計30文書で、各1.0。README/工程案内へ入口を追加した。アプリや実DBを生成する工程へは進めていない。

| 方式 | 入口 | 新規文書 | 基本対応項目 | 基本対応イベント | 画面/帳票描画ケース | 図解析・描画 | 文書検査 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Access | [一覧](../../spec/Access/README.md) | 15 | 83 | 17 | 21 | 23 | PASS |
| CSharp_ASPNET | [一覧](../../spec/CSharp_ASPNET/README.md) | 15 | 83 | 17 | 21 | 26 | PASS |

入力は各方式内の要件1.0・基本設計・共通・QA・採用プロファイル・論理TABLE・規約の25文書ずつ。入力/出力のID・版・SHA-256、Agent/共通規約、方式別記録を[manifest](manifest.json)に固定した。リポジトリ案内は工程表示だけを同期し、当初の規約ハッシュと最終検査時ハッシュを区別した。Agent定義自体の改訂は行っていない。

## 検査・レビュー・保全

全166項目・34イベントのID/順序、各イベント6下位見出し、基本と同一の埋込みHTML、TABLE9列/fieldIds・基本の業務上限/必須/キー、リンクと独立方式内の依存を照合してPASS。SQL/型/認証/保存/帳票/初期データを作成担当と異なる/root/req_desktopが横断レビューし、指摘修正後の対象ハッシュを記録した。

画面はEdge 156.0.4314.42、図はMermaid 12.2.0で今回のMDから解析・描画した。通常/狭幅の正本モックと、値/状態だけを変えた静的fixtureを区別し、目視範囲は各方式の描画記録へ明示した。静的描画は製品の状態/入力/認可/IMEを実証しない。

開始時のproject内55 Markdownのうち50文書はハッシュ一致で保全。既存変更は方式README2件・project入口/工程3件だけ。元の要件・基本・共通・QA・採用規約、既存build記録、正式試験コード/fixtureは保持した。別project/方式の業務・source-only解析・spec-eval・実装ソースを入力へ流用していない。

## 採用判断と残件

パスワード検証・初期設定・認可・排他・DAO/SQLServer・物理型/容量/NULL/制約・API/DTO・Excel生成/保存と失敗境界を方式ごとの設計採用へ具体化した。社員削除なし・経歴明示除去・親子全体保存・11編集値完全重複・無変更/版競合/成否不明の区別、固定時点帳票と受渡前再認可を継承した。定義済みのSP2-DEMO-01を未定義へ戻さず、既存利用者データを起動時に初期化しない。

詳細設計QAは採用した技術判断と未実証の受渡し条件を分ける。実装、ビルド、実DB/DDL/投入、ACCDB/VBA実機・IME/DPI、競合/性能/回復、実Excel帳票/印刷、仕様書のExcel/PDF変換、利用者承認/受入、正式採点は未実施。formalScore=null。文書の検査・AIレビュー・静的描画を製品受入と扱わない。
