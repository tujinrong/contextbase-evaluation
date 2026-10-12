# VB.NET WinForms 最終独立化試験

2026-10-12。方式内の現行spec46ファイル、版8.0/8.1をmetadata/spec-inputs.jsonへハッシュ固定しました。版8.1は方式内参照の明確化です。VBの主/Tests/Maintenance/DBハーネス4件、独立SQLCLRを含むSLNX全体は0警告/0エラー。実行試験111件PASS、静的51件PASSです。

106件の和暦/Unicode/複合チェック/NULL/監査種別/Raw XML/型付きパラメーター/非表示フォーム構築に、マスタXML不正文字の拒否と原値保持4件、Boolean trueの小文字化1件を追加しました。マスタXML変換の失敗はValidationFailedとして返し、原値を修正しません。先の106件と111件R2のJSONはtest-project1/test-reportに残し、新しいrun-idで最終試験を保存しました。

DBハーネスは接続設定がなくSKIP0件、DBを開いていません。保守CLIの接続設定なし拒否は期待exit2です。実DBのDDL/seed/SQLCLR/手続/CRUD/確認・監査・並行更新・故障注入、個別DB主体の権限、対話画面/IME/DPIはNOT_RUNです。非表示構築とVBのビルドはこれらの代替合格ではありません。DBfixtureは実行ごとに一意の番号を発行し、専用空fixtureの生成物を保持します。

全アプリ業務層と独立Tests/保守/DBハーネスはVB.NETです。SQLCLRだけはSQL ServerのSAFE .NET Framework4.7.2ホスト契約を維持する独立C# DB資源を方式内に固定しました。コード、DLL、ProjectReference、生成器、仕様の他方式参照はありません。build内の移植元と変換器、bin/obj/cacheはソース成果物から除外します。

- [機械結果・全コマンド・終了値・ケース・入力ソースハッシュ](20261012-isolated-final2-vb-results.json)
- [SLNX全体ビルド](20261012-isolated-final2-vb-build-solution.log)
- [独立VB試験生ログ](20261012-isolated-final2-vb-boundary.log)
- [実DB SKIP生ログ](20261012-isolated-final2-vb-database.log)

同run-idの再実行は上書きを拒否します。初回最終runnerは記録リストの初期化不足で中断し、既存ログを保存して修正後にfinal2として再実行しました。最終機械結果のpassed=trueはDBや対話画面の合格を含みません。
