<!-- spec-meta: {"schema":"spec-md/1.0","documentId":"PROJECT-README","version":"8.1","path":"test-project1/README.md","sheets":[{"heading":"対象","kind":"GRID","sheet":"01_対象"},{"heading":"方式一覧","kind":"LIST","sheet":"02_方式一覧","key":["方式ID"]},{"heading":"入力と報告","kind":"GRID","sheet":"03_入力と報告"},{"heading":"隔離境界","kind":"GRID","sheet":"04_隔離境界"}]} -->
# test-project1 学生管理

版8.1／2026-10-24。現行の独立配置。各実行結果は試験報告の範囲で判定する。

## 対象

仕様書解析Agent検証用の7つの独立プロジェクト。検索と登録・編集・参照・論理削除、およびクラス・コード保守を題材とする。各方式の原仕様、ソース、DB資源、生成器、ビルド、試験を当該方式内に置く。

## 方式一覧

| 方式ID | 言語 | DB | 独立入口 |
| --- | --- | --- | --- |
| VB.NET_WinForms | VB.NET / WinForms | SQL Server 2022 | [ソース・手順](srcs/VB.NET_WinForms/README.md) |
| CSharp_WPF | C# / WPF | SQL Server 2022 | [ソース・手順](srcs/CSharp_WPF/README.md) |
| CSharp_ASPNET | C# / ASP.NET Core MVC | SQL Server 2022 | [ソース・手順](srcs/CSharp_ASPNET/README.md) |
| Vue_CSharpAPI | Vue / TypeScript + C# API | SQL Server 2022 | [ソース・手順](srcs/Vue_CSharpAPI/README.md) |
| COBOL | GnuCOBOL / C / CGI | SQL Server 2022 | [ソース・手順](srcs/COBOL/README.md) |
| AS400_RPG | ILE RPG / DDS / CL | Db2 for i | [ソース・手順](srcs/AS400_RPG/README.md) |
| Access | VBA / DAO / Access forms | ACE | [ソース・手順](srcs/Access/README.md) |

## 入力と報告

[プロジェクト情報](プロジェクト情報.md)／[仕様索引](spec/README.md)／[試験結果](test-report/README.md)。入力版・入力SHA-256・構造検査・出力SHA-256は各方式build/generation/の固定JSONを参照する。最終配布物・最終試験結果は各方式build/へ更新し、試行・cache・隔離展開は各方式.tmp/だけに置く。履歴はGitで管理する。過去の中断報告や試験合格を現行版へ流用しない。

## 隔離境界

各方式は他方式のコード、仕様、DB定義、生成器を引用しない。原仕様は各方式内のspecだけを正本とする。旧版を作業ツリーへ別名保存せず、必要な過去版はGit履歴から参照する。逆生成の入力は当該方式build/source.zipだけとし、元のspec、spec-eval、履歴、入力manifestは渡さない。業務仕様と工程制御のルールを区別し、配置修正だけでDBや権限の契約を変更しない。
