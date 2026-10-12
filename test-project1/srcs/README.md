# 独立プログラム

2026-10-12。各方式のフォルダーを単独で扱う。コード、仕様(spec)、DB(database)、生成器、試験は当該フォルダー内で完結し、他方式を参照しない。

| 方式ID | 言語 | DB | 独立入口 |
| --- | --- | --- | --- |
| VB.NET_WinForms | VB.NET / WinForms | SQL Server 2022 | [ソース・手順](VB.NET_WinForms/README.md) |
| CSharp_WPF | C# / WPF | SQL Server 2022 | [ソース・手順](CSharp_WPF/README.md) |
| CSharp_ASPNET | C# / ASP.NET Core MVC | SQL Server 2022 | [ソース・手順](CSharp_ASPNET/README.md) |
| Vue_CSharpAPI | Vue / TypeScript + C# API | SQL Server 2022 | [ソース・手順](Vue_CSharpAPI/README.md) |
| COBOL | GnuCOBOL / C / CGI | SQL Server 2022 | [ソース・手順](COBOL/README.md) |
| AS400_RPG | ILE RPG / DDS / CL | Db2 for i | [ソース・手順](AS400_RPG/README.md) |
| Access | VBA / DAO / Access forms | ACE | [ソース・手順](Access/README.md) |

Accessの配布成果はAccess/StudentManagement.accdb 1個。実行結果と未実施は[test-report](../test-report/README.md)を参照。仕様書解析には[ソース専用パッケージ](../agent-input/README.md)を使い、原仕様を入力に含めない。
