# build-agent 構造検査 20261012-isolation-draft-03

対象：test-project1。Agent版7.4。入力版・SHA-256は同実行IDのinputs.jsonを参照。

判定：interrupted-structure。現行入力335ファイルを検査。問題3件。

- STR-001：test-project1/README.md:24 / LINK_MISSING / Missing local reference: test-report/README.md
- STR-002：test-project1/srcs/Access/spec/DB定義/Access/01_DB定義書.md:20 / LIST_CONTENT / テーブル一覧: a single rectangular pipe table is required.
- STR-003：test-project1/プロジェクト情報.md:36 / LINK_MISSING / Missing local reference: test-report/README.md

検査範囲：メタ情報、章/シート対応、LIST矩形・キー、TABLE列/項目ID/PK、イベント6節、ローカル参照先の存在。

未実施：意味上の整合性検査、外部URL確認、画面描画・Excel変換、アプリ生成・コンパイル・業務試験、逆生成・採点。

構造検査通過は生成/ビルド/試験合格を意味しない。構造問題は別Agentが修正し、新しい実行IDで再検査してから再開する。
