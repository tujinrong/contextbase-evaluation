# test-project1 試験結果

2026-10-12。現行生成・隔離記録は **20261012-build-10**。入力版は方式内文書ごとの8.0/8.1（Access DB索引だけ8.2）。途中の失敗や過去の合格もその実行IDのまま保持しました。

| 方式 | 現在の検証 | 未実施 |
| --- | --- | --- |
| VB.NET_WinForms | 6プロジェクトの独立ビルド警告0/エラー0、VB111件、実Framework SQLCLR23件、静的55件、SQL3ファイル構文0件、ZIP単体ビルド | 実SQL配備・CRUD・監査・競合・権限、表示/IME/DPI受入 |
| CSharp_WPF | 独立ビルド警告0/エラー0、Core96件、非表示XAML/画面7件、native境界102件、実Framework SQLCLR27件、SQL3ファイル構文0件、ZIP単体ビルド | 実SQL配備・CRUD・監査・競合・権限、表示/IME/DPI受入 |
| CSharp_ASPNET | 独立ビルド警告0/エラー0、Core96件、実HTTPS MVC契約31件、ZIP単体ビルド | 実SQL、実認証結合、ブラウザー受入 |
| Vue_CSharpAPI | 独立APIビルド、Core96件、実HTTPS API44件、実Vue/Edge23件、型検査/bundle、npm監査0、ZIPのnpm ci/build | 実SQL、実認証結合 |
| COBOL | Windowsホストビルド警告0/エラー0、境界実行86件、静的12件、ZIP単独で25 productionプログラム/CGI/CLIをビルドして実行8件 | Linux CGI配備、実SQL・認証・競合 |
| AS400_RPG | C連携35件、静的89件、SQLRPGLE/DDS/CL/Db2資源生成 | IBM iコンパイル、Db2、5250実機 |
| Access | 単一accdb、最新ZIPから独立構築/VBAコンパイル、業務31/拡張77/実フォーム29件、配布19件、FK最小21件 | Office32bit、共有切断/性能境界、確定応答喪失、画面目視受入 |

[4方式の最終ビルド・実行結果](20261012-isolation-10-independent.json)／[生ログ](20261012-isolation-10-independent.raw.log)。4つのSQL integrationは接続設定なしで **SKIPPED**、検査0件、DBを開いていません。VBのJSON形式SKIPも合格とは別集計です。

方式別の詳細：

- [VB.NETの最終試験](../srcs/VB.NET_WinForms/test-report/20261012-isolated-final4-vb-report.md)、[VBのSQL構文](20261012-build-10-vb-native-syntax.json)
- [WPF native](20261012-build-09-wpf-native-implementation.md)、[WPFのpure Core試験訂正](20261012-final10-wpf-core-boundary-report.md)
- [Vue実ブラウザー23件](20261012-isolation-04-vue-browser.json)。API応答は試験用で、実DB・実認証の証拠ではありません。
- [COBOL現行仕様の86/12件](20261012-build-04-cobol-isolation-30-report.md)、[ソースZIP単独ビルド](20261012-build-09-cobol-source-package.md)
- [RPG現行試験](../srcs/AS400_RPG/test-report/20261012-isolated-current-rpg-results.json)
- [Access現行入力・FK・配布検査](20261012-build-08-access-implementation.md)、[独立ソースZIPの構築・業務試験](20261012-build-09-access-source-package.md)

[7方式の解析用ZIP](../agent-input/README.md)は原仕様・評価資料・試験期待値・生成工程toolsを除外しました。[独立展開と.NET/Vueビルド](20261012-build-10-source-package-validation.json)は全375メンバーのhashを検証し、各方式の別フォルダーで実施しています。Access/COBOLの09/10版ZIPは同一hashで、別報告に単独ビルドを記録しています。

構造・隔離・出力の根拠は[生成報告](../report/20261012-build-10-generation.md)、[入力manifest](../report/20261012-build-10-inputs.json)、[構造検査](../report/20261012-build-10-structure.md)、[隔離検査](20261012-build-10-isolation.md)、[出力manifest](../report/20261012-build-10-outputs.json)。

途中のisolation-09はWPF試験の旧契約と展開XAML混入で失敗し、10で修正・再試験しました。初版09のZIPはreport/archive/20261012-build-09-source-packagesへ保存し、現行10とは区別しています。Accessの試験装置準備、COBOLのホストpath、VBの子PowerShell cmdlet不足、VB構文検査のクラス表示式の期待違いも、失敗記録を保持して訂正しています。

Accessの実2プロセス競合は旧04の実行結果です。当回の再試験へ読み替えていません。SQL/IBM i/Linux/実認証の結合、対話画面の受入、仕様書逆生成・採点は未実施です。
