# AS400_RPG 試験・実装記録

2026-10-12。現行入力は方式内 `AS400_RPG/spec` 版8.0、45ファイル。入力ハッシュは `metadata/spec-inputs.json`、業務契約の直前固定入力は20261012-build-06-inputs.jsonです。版8.0独立化後の最終ソースを再確認しました。過去版の実機合格は使用していません。

検索・登録のSQLRPGLE、業務/共通サービス、COPY、DDS、C Unicode/承認入力補助、バインダー/STUBND、ビルド・起動・保守・権限/Journaling CL、Db2 DDL/seed、方式専用生成器、設定例と配備手順を生成しました。詳細対応は方式内 `metadata/spec-mapping.json` に記録しています。全コード/DB/仕様/生成器は方式内にあり、他方式または退避した共有元を参照しません。

Windows上のZig 0.14.1とICU77.1でC補助を警告エラー扱いでコンパイルし、35件（Unicode/正規化/厳密CCSID/エスケープ/ハッシュ31件、承認IFSパス拒否4件）を実行して35件PASS/0件FAIL、プロセス終了0でした。最終静的確認89件/0指摘はCOPY、公開シンボル、DDSレコード/キー/桁位置、CLソース、メッセージ、ローカルDBと生成器参照です。

IBM iのSQLRPGLE、ILE C、DDS、CL、バインド、Db2 DDL/seed/CRUD/監査/ROLLBACK、5250 UIとCCSID1399表示、2ジョブ競合と確定不明、承認IFSの正しいファイルの読み取りは **NOT_RUN** です。ホストC試験と文字列の静的確認だけではIBM i構文・配備成功や仕様完全適合を確定できません。処理系診断による修正、DB/権限/UI/並行更新の実機試験が残ります。

ソース成果物と `build` 内のコンパイラー/DLL/EXE/キャッシュは区別してください。実行対象C入力・RPG入力のSHA256とコマンド/終了値/全ケースは results.json に保存しています。配備再検証の条件は方式内 docs/deployment.md を参照してください。

- [Cコンパイル生ログ](20261012-build-04-rpg-c-compile.log)
- [C実行生ログ](20261012-build-04-rpg-c-run.log)
- [静的確認生ログ](20261012-build-04-rpg-static.log)
- [機械結果・入力ハッシュ](20261012-build-04-rpg-results.json)
