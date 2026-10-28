# build-agent 構造検査 20261025-regenerate

対象：test-project1 / Vue_CSharpAPI。Agent版7.7。入力版・SHA-256はinputs.jsonを参照。

判定：structure-check-passed。現行入力59ファイルを検査。問題0件。


検査範囲：メタ情報、章/シート対応、LIST矩形・キー、TABLE列/項目ID/PK、イベント6節、入力範囲内のローカル参照先の存在。

方式指定時はproject/spec/方式IDと固定の全体規則・Agent・project入口だけを入力とし、共有入口から範囲外への参照先は検査しない。

未実施：意味上の整合性検査、外部URL確認、画面描画・Excel変換、アプリ生成・コンパイル・業務試験、逆生成・採点。

構造検査通過は生成/ビルド/試験合格を意味しない。構造問題は別Agentが修正し、新しい実行IDで再検査してから再開する。
