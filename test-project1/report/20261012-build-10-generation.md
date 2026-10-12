# test-project1 独立生成完了記録

2026-10-12／runId **20261012-build-10**。利用者の指定どおり7方式を独立化し、方式外の仕様・ソース・共通ライブラリー・DB定義・生成器を参照しない配置へ生成しました。変更対象はagents/build-agentとtest-project1だけです。

| 方式 | プログラム構成 | DB/保存方式 | 独立配置 |
| --- | --- | --- | --- |
| VB.NET_WinForms | VB.NET WinForms、VB業務/保守/DBハーネス | SQL Server2022、native EXEC、当方式専用SQLCLR | srcs/VB.NET_WinForms |
| CSharp_WPF | C# WPF/MVVM、保守CLI | SQL Server2022、native EXEC、当方式専用SQLCLR | srcs/CSharp_WPF |
| CSharp_ASPNET | C# ASP.NET Core MVC/Razor、保守CLI | SQL Server2022、当方式専用サービス | srcs/CSharp_ASPNET |
| Vue_CSharpAPI | Vue/TypeScript、C# API、保守CLI | SQL Server2022、当方式専用サービス | srcs/Vue_CSharpAPI |
| COBOL | GnuCOBOL、C/ODBC/ICU bridge、CGI、保守CLI | SQL Server2022 | srcs/COBOL |
| AS400_RPG | ILE RPG/SQLRPGLE、DDS、CL、ILE C/ICU | Db2 for i、5250 | srcs/AS400_RPG |
| Access | VBA/DAO、Access forms、ローカル役割表 | 単一ACE accdb | srcs/Access |

各方式のspec・database・生成器・ビルド入口・試験は当該方式内に閉じています。VBのアプリ業務層はVBです。SQL ServerのSAFE .NET Framework4.7.2ホスト用SQLCLRだけは、当方式が所有する独立C#のDB資源として配置しています。方式外DLLやC#アプリCoreを参照しません。

元の修正入力はcommit `35a6e57d78985448309a77a59d914d4a070ac854` の改訂7.4系（個別文書版は混在）。初期分割の記録は[移送manifest](20261012-isolation-spec-materialization.json)、横断参照の修正は[隔離改訂記録](20261012-isolation-spec-reference-fixes.json)。移送manifestのhashは分割時点の記録であり、現在版の判定には使用しません。

現行の入力は[335ファイルの版・SHA-256](20261012-build-10-inputs.json)。方式内の原仕様320ファイル、全体ルーティング・規約・当Agent・プロジェクト索引15ファイルを検査し、[構造検査](20261012-build-10-structure.md)は問題0件です。独立仕様は8.0を基準とし、横断参照を除いた規約/配置/データアクセス文書は8.1、Access DB索引のLIST説明移動だけ8.2です。業務項目・制約を共有する正本は残していません。

生成時に、方式外リンクと全方式同時改訂の指示、不要なDB方言参照を各方式内で取り除きました。Access DB索引のLIST内説明は生成した独立文書のGRIDへ移しました。年度の原入力4桁検査と重複候補4表示カテゴリの返却制限は、WPF/VBの実装を原仕様へ合わせて訂正しました。現在の入力に未解決の構造問題はありません。

旧横断仕様・共有ソース・共有solution・旧toolingはreport/archive/20261012-pre-isolationへ履歴として保存し、現行生成・解析の入力から外しています。srcsにShared/Database/_toolsや横断solutionはありません。rootのREADMEは方式の索引であり、共通業務仕様・共通実装ではありません。

配布成果は [Access/StudentManagement.accdb](../srcs/Access/StudentManagement.accdb) **1個**。SHA256 `C477C908EC3081DD1CEEB16885922BF3CBD5A04E79645E2ACE9E8A3FF002ACFB`。外部リンク表なし、5分類70コード、学生/クラス/監査0、4フォーム、評価主体を内部に保持します。試験fixtureと中間backendは方式内buildに限定し、配布原本から引用しません。accdbはGitの除外対象ですが、実ファイルとhashを出力manifestへ記録しています。

仕様書解析Agentへ渡す材料は [agent-inputの7個のZIP](../agent-input/README.md)。原仕様・評価・試験期待値・入力manifest・生成工程toolsを除外し、各ZIPに当方式のproductionソースとDB資源を格納しました。[包装記録](20261012-build-10-source-packages.json)に375ファイルの元hash、包装後hash、変換内容、ZIP hashを保存しています。source-onlyのbuild入口から除外された仕様/試験への依存を外し、COBOLのLinux用入口はLFとUnix実行modeを保持します。初版09のZIPはarchiveへ保存しました。

実行可能な構成は[試験一覧](../test-report/README.md)の範囲で試験しました。4.NET構成は警告0/エラー0、Accessは独立VBA構築、COBOLはWindowsホストで単独コンパイル・実行、RPGはC連携と静的検査です。SQL接続未提供の4integrationは検査0件のSKIPで、DBを開いていません。SQL Server実配備・実認証・競合・故障注入、IBM i、Linux、対話画面受入、逆生成採点は未実施です。

最終の[隔離検査](../test-report/20261012-build-10-isolation.md)と[出力manifest](20261012-build-10-outputs.json)に検査範囲・未実施・出力版/hashを記録します。既存報告を上書きせず、合格と失敗・未実施を分けました。commit/pushは行っていません。
