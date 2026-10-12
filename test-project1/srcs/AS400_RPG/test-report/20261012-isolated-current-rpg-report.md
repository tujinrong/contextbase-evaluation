# AS400_RPG 現行独立入力での試験

2026-10-12。方式内spec45ファイルの独立化版8.0と方式内参照の明確化版8.1をmetadata/spec-inputs.jsonへ固定しました。現行入力でC補助を再コンパイルし35件PASS/0件FAIL、COPY/export/binder/DDS/CL/DB/生成器の静的89確認0指摘でした。旧build04結果を新入力の合格として流用していません。同run-idの上書きを拒否し旧生ログとJSONを保持します。

SQLRPGLE/ILE C/DDS/CL/バインド、Db2 DDL/seed/CRUD/監査/ROLLBACK、5250/CCSID表示、2ジョブ競合・確定不明、承認IFSの正しいファイル入力はIBM iがないためNOT_RUNです。ホストCと静的確認だけではRPG構文・配備・完全適合を証明しません。生成物と配備条件はREADME.mdとmetadata/spec-mapping.json、docs/deployment.mdを参照してください。方式内でコード/DB/仕様/生成器が閉じ、他方式を参照しません。buildのtoolchain/DLL/EXE/cacheはsourceOnlyから除外します。

- [Cコンパイル生ログ](20261012-isolated-current-rpg-c-compile.log)
- [C実行生ログ](20261012-isolated-current-rpg-c-run.log)
- [機械結果・入力/ソースハッシュ](20261012-isolated-current-rpg-results.json)
- [静的確認生ログ](20261012-isolated-current-rpg-static.log)
