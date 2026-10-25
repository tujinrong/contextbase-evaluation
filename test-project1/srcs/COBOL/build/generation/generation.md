# COBOL 生成記録

実行ID: `20261025-regenerate`。状態: **PARTIAL / Text UI BLOCKED**。原仕様・QA・fixtureは変更していません。

入力は `test-project1/spec/COBOL/` の43ファイルと全体規則16ファイルを通常preflightで凍結（構造PASS59、意味適合の合格ではない）。README8.5、方式別共通8.4、共通16/17、最新詳細・DB定義・コード・規約を確認しました。入力hashはinputs.json、方式入力一覧は../input-manifest.jsonです。

旧CGIから27×132 Textへ変更されていますが、方式別共通仕様と設計判断の `QA-TEXT-COBOL` が端末製品・描画ライブラリ・入力/認証adapter・実行環境・IME/キー/Unicode実証を未決とし、実装前の選定/実証を要求しています。API・信頼境界・実証環境を任意選定せず、新TextのSTMAIN/STRENDERは生成を中断しました。根拠・影響・再開情報はinterruption.jsonです。既存CGI/HTMLの今回PASSをText適合へ使いません。

確定範囲ではSQL38命令のODBC型・ColumnSizeカタログ、7表（業務6＋runtime state）のSQLServer DDLと5分類70コードのseedを再生成しました。DBの業務89列・保存/監査/版/認可契約を維持し、DB適用は行っていません。全生成CLIは未決Textを旧HTMLへ黙って戻さず停止し、--reusable-onlyだけを用意しました。

今回のコマンドは tools/input_lock.py lock、tools/regenerate.py --reusable-only、tools/host_build.py current、tools/host_tests.py、tools/static_check.py、tools/test_compact.py、tools/write_report.py（Pythonは-X utf8）。GnuCOBOL3.2 Windows host構文検査/C変換・Zig0.14.1リンク、旧実装の業務境界86/86、HTTP/確認/HTML回帰95/95、静的12/12を新規実行し、コマンド/exit/rawログをbuild/test-resultsへ固定保存しました。確認状態や候補は隔離fixtureを含み、暗号状態表/実SQL保存の統合試験ではありません。

新端末UI、Linux、実SQLServer、実端末・IME・CCSID/Unicode往復、認証adapter、正式受入/逆生成採点はNOT_RUN。formalScore=null。source.zipと最終outputs manifestは親工程がこの状態を保持して作成します。
