# 独立プログラム

2026-10-28。Access移行方式の名称変更を反映。各方式のフォルダーを単独で扱う。コード、DB(database)、生成器、試験はsrcs/方式ID/（sourceRoot）内で完結する。原仕様は[仕様索引](../spec/README.md)から選ぶspec/方式ID/（specRoot）へ分離し、仕様間参照も選択specRoot内で閉じる。順生成はこのspecRootからsourceRootへ生成し、旧sourceRoot/specや他方式を代替入力にしない。

| 方式ID | 言語 | DB | 独立入口 |
| --- | --- | --- | --- |
| VB.NET_WinForms | VB.NET / WinForms | SQL Server 2022 | [ソース・手順](VB.NET_WinForms/README.md) |
| CSharp_WPF | C# / WPF | SQL Server 2022 | [ソース・手順](CSharp_WPF/README.md) |
| CSharp_ASPNET | C# / ASP.NET Core MVC | SQL Server 2022 | [ソース・手順](CSharp_ASPNET/README.md) |
| Vue_CSharpAPI | Vue / TypeScript + C# API | SQL Server 2022 | [ソース・手順](Vue_CSharpAPI/README.md) |
| COBOL | GnuCOBOL / C / CGI | SQL Server 2022 | [ソース・手順](COBOL/README.md) |
| AS400_RPG | ILE RPG / DDS / CL | Db2 for i | [ソース・手順](AS400_RPG/README.md) |
| Access | VBA / DAO / Access forms | ACE | [ソース・手順](Access/README.md) |
| Access-To-CSharp_ASPNET | Access本体からASP.NET Core / C#への移行訓練 | SQL Server | [ソース・手順](Access-To-CSharp_ASPNET/README.md) |

Accessの配布成果はAccess/build/StudentManagement.accdb 1個。実行結果と未実施は[test-report](../test-report/README.md)を参照。仕様書解析には[ソース専用パッケージ](../agent-input/README.md)を使い、原仕様を入力に含めない。
