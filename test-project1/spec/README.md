<!-- spec-meta: {"schema":"spec-md/1.0","documentId":"PROJECT-SPEC-INDEX","version":"8.0","path":"test-project1/spec/README.md","sheets":[{"heading":"正本","kind":"GRID","sheet":"01_正本"},{"heading":"方式一覧","kind":"LIST","sheet":"02_方式一覧","key":["方式ID"]},{"heading":"旧版","kind":"GRID","sheet":"03_旧版"}]} -->
# 独立仕様書への入口

版8.0／2026-10-12。現行の独立配置。各実行結果は試験報告の範囲で判定する。

## 正本

この索引は配置情報だけを持つ。業務仕様を横断して共有する文書は置かない。各方式の仕様セットはその方式のsrcs/方式/spec内だけで閉じる。

## 方式一覧

| 方式ID | 言語 | DB | 独立入口 |
| --- | --- | --- | --- |
| VB.NET_WinForms | VB.NET / WinForms | SQL Server 2022 | [専用仕様](../srcs/VB.NET_WinForms/spec/README.md) |
| CSharp_WPF | C# / WPF | SQL Server 2022 | [専用仕様](../srcs/CSharp_WPF/spec/README.md) |
| CSharp_ASPNET | C# / ASP.NET Core MVC | SQL Server 2022 | [専用仕様](../srcs/CSharp_ASPNET/spec/README.md) |
| Vue_CSharpAPI | Vue / TypeScript + C# API | SQL Server 2022 | [専用仕様](../srcs/Vue_CSharpAPI/spec/README.md) |
| COBOL | GnuCOBOL / C / CGI | SQL Server 2022 | [専用仕様](../srcs/COBOL/spec/README.md) |
| AS400_RPG | ILE RPG / DDS / CL | Db2 for i | [専用仕様](../srcs/AS400_RPG/spec/README.md) |
| Access | VBA / DAO / Access forms | ACE | [専用仕様](../srcs/Access/spec/README.md) |

## 旧版

改訂前の横断仕様はreport/archive/20261012-pre-isolation/specに履歴として保存する。現行生成入力へ含めず、方式別の現行仕様へ変更を自動伝播しない。
