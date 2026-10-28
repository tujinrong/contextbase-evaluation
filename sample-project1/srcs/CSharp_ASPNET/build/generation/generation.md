# CSharp_ASPNET 共有DB対応とDebug起動

2026-10-27。Nativeの独立DB動作を保ち、SharedAccessの明示的な型変換・共通ガード・実DBの役割照合を追加した。Debug/Releaseの既定起動はSharedTrainingSql、保存済みhttpsも同じ共有DB設定。既存の独立DB起動はNativeに残す。

接続先は.\SQLEXPRESS／AccessRebuilderTraining_01a17be7。DDL・seed・DB作成は実行していない。入力DB構造・既存学生・相手側ソース・Access原本の実行前後の一致を確認した。

inputs.jsonは今回の採用仕様と利用者指示、shared-database-inputs.jsonは実DB検証前の読取り入力を記録する。outputs.jsonは現行ソースと最終配布・検査結果のハッシュである。specの索引/プロジェクト8.6、共通実装8.4、共有DBプロファイル1.0を固定する。既存の検索・登録仕様の業務契約は維持する。

今回の検証は[検証結果](../test-results/shared-database.md)。旧2026-10-25の再生成・構造レポートは当時の範囲であり、今回の実行結果として流用しない。正式採点は未実施、formalScore=null。
