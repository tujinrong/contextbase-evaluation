# VB.NET WinForms 独立化・試験記録

2026-10-12。入力は方式内specの46ファイル、独立化版8.0と方式内参照の明確化版8.1です。metadata/spec-inputs.jsonに現行各ファイルのSHA256を保存し、旧共有C#の検査結果をVB改訂の合格として流用していません。

主画面、Designer、Presenter、Application、Domain、Infrastructure、保守CLI、試験ハーネスはVB.NETです。VBの主/Tests/Maintenance/DBハーネスの各ProjectReferenceは自方式内へ閉じ、Option Strict/Explicit/Infer=On、SqlClient6.1.3です。C#移植元と変換器はbuild内の開発資源に退避し、製品ビルドで参照しません。DB生成器も方式内specだけを入力とします。詳細対応はmetadata/spec-mapping.jsonです。

DB側のSQLCLRはSQL Server .NET Frameworkホスト向けの独立C# DB資源をdatabase/nativeへ固定しました。VBアプリの業務層はVB.NETで完結します。CLRでDateOnly/Runeが使えないホストと、厳密なサーバー正規化・XML・ハッシュ契約を維持するDB専用実装です。DB資源にも他方式へのソース共有・ProjectReferenceはありません。DB側の配備や実行は未検証です。

最終VB4プロジェクトは全てビルド0警告/0エラー。VB独立試験106件PASS/0件FAIL、静的51確認PASSでした。和暦境界、スカラー値/不正UTF16、原長と保存長、正規化、複合チェック、任意日付・緊急続柄NULL、監査種別、Raw XMLのCRLF/原値/NULL/Boolean/権限情報除外、型付きSQLパラメーター、非表示フォーム構築を実行しました。保守CLIはDB接続設定なしの拒否exit2を確認しました。

SQL Serverハーネスは環境変数なしでSKIP、検査数0、DBは開いていません。DDL/seed/SQLCLR/EXEC-only入口配備、保存・確認・版競合・論理削除・監査の実DB往復、別DB主体の権限、2ジョブ競合、監査障害・確定不明、対話画面・IME・DPI・アクセシビリティはNOT_RUNです。非表示画面構築を対話画面の合格とは扱いません。DB専用ハーネスは事前配備済みcontextbase_test_*専用fixtureを要求し、実行後の行を保持します。

- [機械結果・コマンド・終了値・ケース・ソースハッシュ](20261012-isolated-vb-results.json)
- [VB主プロジェクトビルド](20261012-isolated-vb-build-main.log)
- [VB独立試験生ログ](20261012-isolated-vb-boundary.log)
- [DB試験SKIP生ログ](20261012-isolated-vb-database.log)
- [独立ソリューションビルド](20261012-isolated-vb-build-solution.log)

ソース成果物からbuild/bin/obj/キャッシュを除外します。完全なDB/GUI仕様適合は実機試験完了まで確定しません。
