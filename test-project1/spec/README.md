<!-- spec-meta: {"schema":"spec-md/1.0","documentId":"PROJECT-SPEC-INDEX","version":"8.6","path":"test-project1/spec/README.md","sheets":[{"heading":"正本","kind":"GRID","sheet":"01_正本"},{"heading":"方式一覧","kind":"LIST","sheet":"02_方式一覧","key":["方式ID"]},{"heading":"旧版","kind":"GRID","sheet":"03_旧版"}]} -->
# 独立仕様書への入口

版8.6／2026-10-28。現行の独立配置。各実行結果は試験報告の範囲で判定する。

## 正本

フル方式パターンの現在の登録一覧を以下に示す。7標準方式は今回の基本設計書式適用対象、Access-To-CSharp_ASPNETは基本設計分冊を持たない既存移行拡張として保持する。方式数は固定上限ではなく、追加時にこの索引・方式前提・Agent登録・入力境界・検査を更新する。

この索引は配置情報だけを持つ。業務仕様を横断して共有する文書は置かない。各方式の仕様セットはspec/方式ID/（specRoot）内だけで閉じる。順生成は選択specRootを読み、対応するsrcs/方式ID/（sourceRoot）へ生成する。旧sourceRoot/specへのfallbackや他方式仕様の共用は行わない。

追加する画面の設計系統はWEB系・WinForms系・Text系の3種類とし、方式一覧に採用系統を示す。WPFは利用者指定によりWEB系、Accessは標準フォームを使うWinForms系に分類する。具体的な画面配置・操作・方式固有の制約は各独立仕様で定める。

## 方式一覧

| 方式ID | 言語・画面方式 | 画面設計系統 | DB | 独立入口 |
| --- | --- | --- | --- | --- |
| VB.NET_WinForms | VB.NET / WinForms | WinForms系 | SQL Server 2022 | [専用仕様](VB.NET_WinForms/README.md) |
| CSharp_WPF | C# / WPF | WEB系 | SQL Server 2022 | [専用仕様](CSharp_WPF/README.md) |
| CSharp_ASPNET | C# / ASP.NET Core MVC | WEB系 | SQL Server 2022 | [専用仕様](CSharp_ASPNET/README.md) |
| Vue_CSharpAPI | Vue / TypeScript + C# API | WEB系 | SQL Server 2022 | [専用仕様](Vue_CSharpAPI/README.md) |
| COBOL | GnuCOBOL / C / Windows標準Console（Text） | Text系 | SQL Server 2022 | [専用仕様](COBOL/README.md) |
| AS400_RPG | ILE RPG / DDS / CL / 5250 | Text系 | Db2 for i | [専用仕様](AS400_RPG/README.md) |
| Access | VBA / DAO / Access forms | WinForms系 | ACE | [専用仕様](Access/README.md) |
| Access-To-CSharp_ASPNET | Access本体からの移行訓練 / ASP.NET Core MVC | WEB系 | SQL Server | [移行設計](Access-To-CSharp_ASPNET/README.md) |

## 旧版

改訂前の仕様と移動前のパスはGit履歴から参照する。作業ツリーへ別名の旧版を置かず、現行生成入力へ含めない。方式別の現行仕様へ変更を自動伝播しない。
