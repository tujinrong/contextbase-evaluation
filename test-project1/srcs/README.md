# test-project1 生成プログラム

2026-10-12、順生成。**構造問題 STR-ACCESS-001 により全方式の生成を中断しました。以下は保存した途中成果であり、7方式の実装完了や配備可能を意味しません。** 入力は仕様セット7.2＋局所修正版7.3、出力の記録版は `20261012-build-03` です。

| 方式 | ソース・手順／中断記録 | 実装言語とDB | 中断時点の状態 |
| --- | --- | --- | --- |
| VB.NET_WinForms | [README](VB.NET_WinForms/README.md) | VB.NET/.NET10、SQL Server 2022 | 中断前ビルド成功。候補順の最終変更後は未再ビルド |
| CSharp_WPF | [README](CSharp_WPF/README.md) | C#/XAML/.NET10、SQL Server 2022 | 中断前ビルド成功。候補順の最終変更後は未再ビルド |
| CSharp_ASPNET | [README](CSharp_ASPNET/README.md) | C#/Razor/.NET10、SQL Server 2022 | ビルド・fake HTTP検査実施。実DB未接続 |
| Vue_CSharpAPI | [README](Vue_CSharpAPI/README.md) | Vue3/TypeScript＋C# API、SQL Server 2022 | APIビルド・Vue型検査/bundle実施。実DB未接続 |
| COBOL | [中断記録](../report/cobol-implementation.md) | GnuCOBOL3.2 CGI＋C/ODBC18、SQL Server 2022 | 部分生成。画面等未生成・参照未閉鎖・未コンパイル |
| AS400_RPG | [中断記録](../report/rpg-implementation.md) | ILE RPG/SQLRPGLE＋DDS5250、Db2 for i | 部分生成。DDS/UI/CL等未生成・未コンパイル |
| Access | [中断記録](../report/legacy-implementation.md) | VBA7/DAO＋非連結フォーム、ACE | 試験ACCDB生成。正当入力の保存でDAO3201、未完成 |

.NET4方式は [共有Core・マスタ保守CLI](Shared/README.md) と [SQL Server DDL/seed](Database/SQLServer/README.md) を使用します。Access/RPGは方式別DB資源を使います。実クラスや学生を初期データへ作りません。秘密情報とローカル認証設定はソースへ含めません。

ビルド・検査の結果、方式別の未実施、配備上の留保は [生成報告](../report/build-report.md)、修正理由は [仕様修正記録](../report/spec-bug-fixes.md) を参照してください。ソース生成、コンパイル、実DB動作、実機受入、逆生成、採点はそれぞれ別の状態です。

本生成は評価用の途中実装です。ネイティブ本番のEXEC-only保存入口、実認証基盤・配備運用、未導入処理系によるコンパイルなど、未確認・未実装の範囲を報告書に明記しています。[構造問題報告](../report/structural-problem-STR-ACCESS-001.md)の再開条件が満たされるまで追加生成を行いません。
