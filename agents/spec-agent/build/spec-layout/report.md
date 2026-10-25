# test-project1 仕様フォルダ整理

2026-10-25。対象はAccess、AS400_RPG、COBOL、CSharp_ASPNET、CSharp_WPF、VB.NET_WinForms、Vue_CSharpAPIの7方式。工程はspec-folder-layout。仕様書のみを修正する指示に従い、業務プログラム・accdb・DB・ビルド処理は変更していない。

各方式のspec/詳細仕様書/<方式ID>/にあった検索・学生登録の2文書をspec/詳細仕様書/直下へ、spec/共通/方式別/<方式ID>/の共通実装仕様をspec/共通/方式別/直下へ移動した。移動は21ファイル、旧空フォルダ削除は14箇所。関連リンク・コード表記の参照・spec-meta.pathを更新し、変更文書は改訂版を上げた。入力時点の既存ローカル差分は維持した。

docs/リポジトリ構成.mdを7.3から7.4へ改訂し、独立方式内では方式名の階層を繰り返さない規則を明記した。7方式の規約コピーも同期した。DB定義/Access/等はDBプロファイルを表すため維持した。入力と出力の全ファイル・版・SHA-256・移動対応はmanifest.jsonに記録した。

299文書（方式内298文書＋全体配置規則1文書）を独立レビューし、構造・版・相対リンク・方式内閉包・旧階層参照の検査は指摘0件。旧14ディレクトリは不存在、基本/詳細の14画面組はHTMLと項目IDが一致する。埋込みHTML28断片とDB定義54文書は入力SHA-256と一致した。詳細はvalidation.jsonと各方式のbuild/spec-generation/に記録した。

今回の画面再描画・追加目視・状態試験は未実施。各方式のrender.jsonでは既存の描画検査を当時の出典のまま保持し、folderRelocationに現行ファイルとの対応とHTML同一性を明記した。過去の描画PASSを今回改訂版の検査結果として使用していない。アプリ実装、ビルド、Access/WinForms実機試験、DB実行、Excel/PDF変換、正式採点は未実施。formalScore=null。

既存のagents/build-agent/scripts/isolate-specs.mjsには旧階層を作成する処理がある。プログラムを修正しない指示に従って保持した。再生成時はdocs/リポジトリ構成.mdの独立方式配置を適用する必要がある。旧入力manifest・spec-mapping等の履歴上の出典は入力を指す記録として保持し、現行ファイル参照へ一括置換していない。
