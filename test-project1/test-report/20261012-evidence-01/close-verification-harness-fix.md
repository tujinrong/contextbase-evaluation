# 終了確認スクリプトの初回構文エラー

2026-10-12。rootが追加したclose-verification.ps1の初回PS5実行は、BOMなしUTF-8の日本語文字列をOSコードページ936で読み、構文エラーで停止した。アプリ実行や終了検証には到達せず、close-verification.jsonも作成されなかった。この失敗は製品アプリの不具合や終了確認の合格ではない。

実行結果exit1の先頭診断は「Unexpected token 'Closure' in expression or statement.」「The hash literal was incomplete.」「The string is missing the terminator: '.」だった。日本語定数をスクリプトから除去し、既存R6結果のexactDateMessageを明示的なUTF-8指定で読むASCIIスクリプトへ修正した。修正後の新規実行結果はclose-verification.jsonに記録する。
