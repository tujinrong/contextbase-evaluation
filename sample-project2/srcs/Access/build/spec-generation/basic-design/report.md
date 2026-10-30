<!-- spec-meta: {"schema":"spec-md/1.0","documentId":"SP2-Access-BASIC-RESULT","version":"1.0","path":"sample-project2/srcs/Access/build/spec-generation/basic-design/report.md","sheets":[{"heading":"対象と成果","kind":"GRID","sheet":"01_対象と成果"},{"heading":"検査と限界","kind":"GRID","sheet":"02_検査と限界"},{"heading":"次工程","kind":"GRID","sheet":"03_次工程"}]} -->
# Access 基本設計再生成結果

版1.0／2026-10-29。runId=sp2-ui-regenerate-20261029、generationMode=canonical-update、stage=basic-design。

## 対象と成果

sample-project2/spec/Accessだけを業務入力とし、基本設計Agent1.11・専用規則1.2・工程1.3を実行した。初回に48入力（業務29・規則19）の文書ID/版/SHAを[inputs.json](inputs.json)へ固定した。出力30文書の現版/SHAと変更/継承の区別は[manifest.json](manifest.json)に固定する。要件1.1・既存QA・DEMO認証・5論理表48項目を継承し、要件本文、詳細、物理DB、VBA/ACCDB、既存fixtureを変更していない。その他工程14ファイルは開始時SHAと一致を検査した。

12文書を改訂し、共通09を1文書追加した。5Form・基本情報/経歴の2Page・必要Dialog/出力状態を区分し、6機能×9カテゴリ54条件、4観点、通常起動/復帰、反映/保存/取消、未反映保護を具体化した。既存83項目ID・17イベントIDを保持し、画面/対象/領域の表示Labelを9項目追加した。DB項目・既存保存単位の変更はない。

screenFamily=WINFORMS、renderer=ACCESS。クラシック外観と全役割Yu Gothic UI11pt、氏名3900/カナ4950/日付2250twipを維持した。タイトル16pt推奨は不採用で、11pt太字・独立配置・余白を採用。モックroot1260px、外周24px、経歴一覧420px（開始80/終了80/案件240）・詳細約772pxは設計採用値で、実client/DPIの正式条件ではない。

「明細へ反映」は既存F04-I26のまま「経歴一覧へ反映」へ、「保存」はI28のまま「社員・経歴を保存」へ明確化した。確認分岐とDB0件の反映/除去、未反映を含む全体原子保存を維持する。F06は一件保存であることを表示する。F05は新Formを設けず、F03内の状態と標準保存先Dialogを使う。

## 検査と限界

[validation.json](validation.json)は対象30文書・106H2・29LIST・417データ行、5TABLE/48項目、342ローカル参照、83既存項目ID、17イベント、54UI条件を検査する。metadata/path/版/H2/sheets、LIST矩形/キー、参照、埋込静的HTMLと項目対応、凍結規則・保護文書のSHAを確認した。要件本文は入力のまま保持し、その根拠資料の旧版/SHAは当時の逆生成記録として扱う。

[render.json](render.json)はMD概要GRIDの同じ8断片（7画面状態断片とR01の2紙面を含む1帳票断片）の出典/断片SHA・環境・寸法を記録する。1366×768 CSS px、deviceScaleFactor=1、Microsoft Edge headlessで描画。5主要Form、F04両Page、F03内のF05作成中状態の計7画面断片は幅1260px・11pt相当14.6667pxを確認した。帳票見本は別字体/680px幅で、実Excelではない。PNG/抽出HTML/SVGは担当.tmpの一時物とし、仕様の別正本にしない。

[diagrams.json](diagrams.json)は現版のMermaid28図を構文解析・SVG描画した記録。初回の旧描画ライブラリ11.4.1では日本語ER識別子を受理しなかったため、Unicode対応11.17.2へ切替えて元の図をそのまま再検査した。図や論理名を描画器の制約へ合わせて改変していない。

本文と描画の自己レビュー、rootによる独立構造/意味/全8断片の目視を分け、[design-review.md](design-review.md)へ記録する。独立指摘の認証ロック表現とF06領域見出しを反映した。静的初期/編集/未反映/出力中の代表状態を描画しているが、エラー/空/最大長/停止/競合/結果不明の全画面状態、標準Dialogは実Accessで未観測。状態の設計済みと実観測済みを同一扱いにしない。

実Access・DB保存/取消再読込・実キー/クリップボード/IME・Office外枠/実client・100/125/150% DPI・性能/競合/障害注入・実Excel/印刷・利用者受入・正式採点は未実施。これらは下流の検証として残す。過去のPASSやPH-07を今版の合格へ転記していない。formalScore=null。

## 次工程

[handoff.md](handoff.md)に今回の採用差分、既存IDとの対応、詳細で具体化する部品/プロパティ/状態、未実施の検証を固定する。F05の横1ページ・縦自動は結果契約であり、FitTo API値の固定ではない。文字サイズ・全件全文・手動継続見出しを両立する方式を詳細で選び、長文20件を実Excelで検証する。Zoom100固定や全体一枚への縮小を未検証で採用しない。

この担当工程はレビュー可能な基本候補と固定記録までで停止する。親担当へ出力SHAを渡し、後続の詳細・実装は親担当の工程管理で開始する。
