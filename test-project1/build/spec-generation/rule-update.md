# 仕様生成の前提規則 更新結果

確定済みの前提を自身の仕様正本から継承する手順を、ルート規則とspec-agent 8.5へ反映しました。COBOL Windows環境1.1を次回の生成前提とし、認証なしサンプルの範囲をCOBOLに固定します。全方式で最終成果の固定パス更新・中間.tmp/・Git履歴を継承し、実施状態を設計前提と分けます。

| 文書 | 版 |
| --- | --- |
| AGENTS.md | 7.2 → 7.3 |
| docs/仕様書作成ルール.md | 7.5 → 7.6 |
| docs/開発規約.md | 7.2 → 7.3 |
| agents/spec-agent/AGENT.md | 8.4 → 8.5 |
| agents/spec-agent/PROMPT.md | 8.4 → 8.5 |
| agents/spec-agent/README.md | 8.4 → 8.5 |
| test-project1/README.md | 8.2 → 8.3 |
| test-project1/プロジェクト情報.md | 8.1 → 8.2 |
| test-project1/spec/README.md | 8.2 → 8.3 |
| test-project1/spec/COBOL/README.md | 8.6 → 8.7 |
| test-project1/spec/COBOL/プロジェクト情報.md | 8.5 → 8.6 |
| test-project1/spec/COBOL/共通/方式別/01_共通実装仕様.md | 8.5 → 8.6 |
| test-project1/spec/COBOL/共通/方式別/02_Windows実行環境.md | 1.0 → 1.1 |

13文書の構造・62ローカルリンク、全方式316入力のinspect-only検査、diff確認はPASS。前回ソース622ファイルと方式別成果498件のハッシュは不変です。仕様書一式・アプリの再生成、実機/DB/IME検証、正式採点は今回は未実施です。前回の最終整合性結果は入力改訂によりSTALEと表示し、当時の版・ハッシュを保持しています。
