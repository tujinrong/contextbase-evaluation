# test-project1 最終検査結果の入口

2026-10-24。検査結果は各方式build/test-results/の固定先へ更新する。ここへ実行ID別の履歴を追加しない。履歴はGitで参照し、処理途中・試行・cacheは各方式.tmp/へ置く。

| 方式 | 最終検査結果 | 入出力記録 |
| --- | --- | --- |
| VB.NET_WinForms | [検査](../srcs/VB.NET_WinForms/build/test-results/) | [generation](../srcs/VB.NET_WinForms/build/generation/) |
| CSharp_WPF | [検査](../srcs/CSharp_WPF/build/test-results/) | [generation](../srcs/CSharp_WPF/build/generation/) |
| CSharp_ASPNET | [検査](../srcs/CSharp_ASPNET/build/test-results/) | [generation](../srcs/CSharp_ASPNET/build/generation/) |
| Vue_CSharpAPI | [検査](../srcs/Vue_CSharpAPI/build/test-results/) | [generation](../srcs/Vue_CSharpAPI/build/generation/) |
| COBOL | [検査](../srcs/COBOL/build/test-results/) | [generation](../srcs/COBOL/build/generation/) |
| AS400_RPG | [検査](../srcs/AS400_RPG/build/test-results/) | [generation](../srcs/AS400_RPG/build/generation/) |
| Access | [検査](../srcs/Access/build/test-results/) | [generation](../srcs/Access/build/generation/) |

全方式の配置・除外・入出力照合は[最終集約](../build/README.md)。生成・build・fixture・静的検査・実機・正式受入を区別し、未実施は各最終記録へ明記する。SQL Server業務結合、IBM i、正式採点等を過去の結果から合格にしない。
