<!-- spec-meta: {"schema":"spec-md/1.0","documentId":"PROJECT-README","version":"8.8","path":"test-project1/README.md","sheets":[{"heading":"対象","kind":"GRID","sheet":"01_対象"},{"heading":"方式一覧","kind":"LIST","sheet":"02_方式一覧","key":["方式ID"]},{"heading":"入力と報告","kind":"GRID","sheet":"03_入力と報告"},{"heading":"隔離境界","kind":"GRID","sheet":"04_隔離境界"}]} -->
# test-project1 学生管理

版8.8／2026-10-28。Access移行方式とContextBase一括起動を含む現行の独立配置。各実行結果は試験報告の範囲で判定する。

## 対象

sample-project1（旧test-project1）はフル方式パターンである。現在の標準7方式とAccess-To-CSharp_ASPNETの移行拡張を保持し、将来方式を追加できる。方式追加時はspec/README.md、方式プロファイル、Agentの登録・入力境界・検査を同期する。sample-project2はAccess・CSharp_ASPNETの2方式パターンで、今回の工程は基本設計。

今回、各標準方式の既存基本設計へ11列項目表・空欄/-/〇・処理手順の階層化・チェック/メッセージ・論理DB/ER/更新の記述規則を適用した。既存の業務条件・方式差は保持し、アプリ・DB・Excelの再生成/実行は行わない。改名はディレクトリと現在の入力経路に適用し、旧build/解析/評価のハッシュ・projectIdは当時の証跡として保持する。


仕様書解析Agent検証用の8つの独立方式。検索と登録・編集・参照・論理削除、およびクラス・コード保守を題材とする。各方式の原仕様はspec/方式ID/（specRoot）、ソース・DB資源・生成器・ビルド・試験はsrcs/方式ID/（sourceRoot）へ分離して置く。

## 方式一覧

| 方式ID | 言語 | DB | 独立入口 |
| --- | --- | --- | --- |
| VB.NET_WinForms | VB.NET / WinForms | SQL Server 2022 | [ソース・手順](srcs/VB.NET_WinForms/README.md) |
| CSharp_WPF | C# / WPF | SQL Server 2022 | [ソース・手順](srcs/CSharp_WPF/README.md) |
| CSharp_ASPNET | C# / ASP.NET Core MVC | SQL Server 2022 | [ソース・手順](srcs/CSharp_ASPNET/README.md) |
| Vue_CSharpAPI | Vue / TypeScript + C# API | SQL Server 2022 | [ソース・手順](srcs/Vue_CSharpAPI/README.md) |
| COBOL | GnuCOBOL / C / Windows標準Console（Text） | SQL Server 2022 | [ソース・手順](srcs/COBOL/README.md) |
| AS400_RPG | ILE RPG / DDS / CL | Db2 for i | [ソース・手順](srcs/AS400_RPG/README.md) |
| Access | VBA / DAO / Access forms | ACE | [ソース・手順](srcs/Access/README.md) |
| Access-To-CSharp_ASPNET | Access本体からASP.NET Core / C#への移行訓練 | SQL Server | [ソース・手順](srcs/Access-To-CSharp_ASPNET/README.md) |

## 入力と報告

[プロジェクト情報](プロジェクト情報.md)／[仕様索引](spec/README.md)／[試験結果](test-report/README.md)。入力版・入力SHA-256・構造検査・出力SHA-256は各方式build/generation/の固定JSONを参照する。最終配布物・最終試験結果は各方式build/へ更新し、試行・cache・隔離展開は各方式.tmp/だけに置く。履歴はGitで管理する。過去の中断報告や試験合格を現行版へ流用しない。

### ContextBase解析の設定と結果

[contextbase.toml](contextbase.toml)のprofileで入力・request・work・outputを切り替える。相対パスは設定ファイルの位置が基準。既定profileはcsharp_aspnet、sourceはsrcs/CSharp_ASPNET、workは選択profileのwork基点、最終出力は [spec-reverse](spec-reverse/README.md) の各Agent/contextbase.json。解析成果は通常の配布物build/とは分ける。csharp_wpf profileはsrcs/CSharp_WPF、spec-reverse/CSharp_WPF、.tmp/contextbase/csharp_wpfへ切り替える例で、今回解析を開始する指示ではない。

Windowsでは [run-discovery.cmd](run-discovery.cmd) をダブルクリックすると、既定profileでdiscoveryだけを一括起動できる。初回はPython 3.11以降から専用環境と依存を準備し、以後は互換な環境を再利用する。reverse-agentは不要。重複起動はロックで拒否し、設定work/discovery-agent-launch配下のcurrent／stagingを管理する。手動CLIのworkとは分け、既存の手動workや所有不明の内容を削除しない。

起動は新しい原文封印、抽出、独立検証、採用と同一版のreview出力までを行う。失敗時は前回の正式成果を保持し、後続relationship／behaviorや原アプリ・SQL・DBを実行しない。終わったら [discoveryのreview.md](spec-reverse/discovery-agent/review.md) を確認する。起動条件・保存先・終了コードは [discoveryの案内](../agents/reverses/discovery-agent/README.md)を参照する。

別profileや自動実行は `run-discovery.cmd --no-pause --profile NAME` を使う。ダブルクリックでは結果を読めるよう画面を残し、先頭の--no-pauseまたはCONTEXTBASE_DISCOVERY_NO_PAUSE=1で待機を省略できる。異なる作業ディレクトリからもcmd自身の場所を基準に設定を解決する。

設定ファイルの存在は解析・検証の完了を意味しない。paths --configは解決先の確認だけを行い、snapshot作成・LLM呼出しはしない。実行・採用の範囲は各回の結果で確認する。既存workは封印した入力に束縛し、元ソース変更へ自動追従しない。

## 隔離境界

各方式は他方式のコード、仕様、DB定義、生成器を引用しない。原仕様は選択方式のspec/方式ID/だけを正本とし、業務仕様と仕様間参照をこのspecRoot内で閉じる。順生成はspecRootを読み、対応するsourceRootへ生成する。旧sourceRoot/specをfallbackに使わない。旧版を作業ツリーへ別名保存せず、必要な過去版はGit履歴から参照する。逆解析の入力は選択方式のsource-onlyパッケージ、または利用者が明示許可したsourceRootの読取り専用ソースとする。今回の既定はcontextbase.tomlのsrcs/CSharp_ASPNETで、原仕様project/spec/全体、spec-eval、他方式、履歴の期待値は渡さない。業務仕様と工程制御のルールを区別し、配置修正だけでDBや権限の契約を変更しない。
