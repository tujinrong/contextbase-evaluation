# build-agent 順生成・中断報告

報告版1.0／2026-10-12。projectId=`test-project1`、工程=`build`、出力記録版=`20261012-build-03`。**STR-ACCESS-001により全方式の生成・修正・ビルドを中断。7方式の実装完了・仕様適合・配備可能とは判定していない。**

build-agentを実行契約・指示・事前検査・入力再照合付きmanifestとして作成し、指定の7方式を `test-project1/srcs/` に生成した途中で、Accessの正当入力を通常の参照整合付き複合FKで保存できない構造適合問題を実機再現した。ユーザー指定どおり構造仕様は変更せず、[問題の根拠・再現・再開条件](structural-problem-STR-ACCESS-001.md)を保存して停止した。索引の代替設定は未検証であり、Access全般で絶対に実現不能という判定ではない。

## 変更範囲・Agent

書込みは `agents/build-agent/` と `test-project1/` に限定した。全体docs、他Agent、他project、rootのAGENTS/READMEは変更していない。spec-evalを生成入力として読まず、変更・逆生成・採点も行っていない。コミット・pushは行っていない。

| 作成・更新物 | 役割・状態 |
| --- | --- |
| [AGENT.md](../../agents/build-agent/AGENT.md) | AG-BUILD、7.0→7.2。対象限定・局所バグと構造問題の区別・全方式中断・検査状態の区別 |
| [PROMPT.md](../../agents/build-agent/PROMPT.md) | projectId/buildを明示する実行入口 |
| scripts/preflight.mjs | 入力版/ハッシュ固定、メタ・章/シート・LIST/TABLE・イベント・ローカル参照検査。機械検査だけで実装適合を判断しない |
| scripts/preflight-tests.mjs | 専用fixtureを使う9件の検査。既存報告の上書き拒否・評価入力除外・構造問題停止等 |
| scripts/manifest.mjs | 入力ハッシュ再照合、途中ソースと変更文書の版/ハッシュ保存。生成や合格判定ではない |
| [srcs一覧](../srcs/README.md) | 7方式・共有Core/CLI・DB資源・検査資源。中断時点の部分成果 |

build-agentの実行主体は本契約を読むCodex。preflightだけで各言語を自動変換する独立コンパイラーではない。

## 入力・出力の版と記録

基準コミットは `5bdde437cd587c4b2f840503c89f73a9012909f4`。初回 `20261012-build-01-inputs.json` と局所修正後の02/03を別ファイルで保持した。最終入力記録は [03-inputs.json](20261012-build-03-inputs.json) の114ファイル（7.0:35、7.1:1、7.2:36、7.3:14、HTML/PNG等版なし:28）。build-agent版は7.2。

仕様の局所誤記は14文書を7.3へ更新し、項目長、保護値、SQL確認情報型、サービス名称等を一意の正本に合わせた。[修正理由](spec-bug-fixes.md)と出力manifestのbefore/after版・SHA-256を参照。Accessの構造問題に関わるDB定義7.2・共通09の7.0は変更していない。

[03-structure.json](20261012-build-03-structure.json) はメタ/表/参照の**機械検査だけ**を通過（指摘0）。semantic consistency、アプリ生成/ビルド、実機、逆生成/採点は検査外。後から判明した意味適合問題による [03-status.json](20261012-build-03-status.json) の `interrupted-structural` を本実行の最終状態とする。保存済み03-structure.md見出しに残るAgent7.1表記は当時の出力テンプレート誤記であり、03-inputs.jsonと実AGENT.mdの7.2が正しい。過去記録は上書きしない。

[03-outputs.json](20261012-build-03-outputs.json) は入力ハッシュ再照合後の**中断ソース・生成資源の棚卸し**。bin/obj/node_modules/dist/build、ACCDB等の実行物、秘密設定を除外する。ただし既存スクリプトはCOBOLの `tools/__pycache__/emit_cobol.cpython-311.pyc` を除外しないため、これも途中生成資源として含まれる。JSONの `sourceOnly` は上記の限定した除外を示す欄であり、全項目が人が編集するソースという保証ではない。中断後に生成スクリプトや途中ファイルを変更していない。実装完了・全参照閉鎖・検査合格を意味しない。

manifest保存時の実測: 入力114件のハッシュ一致、出力232ファイル、変更文書15件（build-agent契約1件＋題材の局所修正14件）。出力の各ファイルサイズ/SHA-256と変更文書の前後版/SHA-256を記録した。

## 方式別の生成・検査状態

| 方式・資源 | 保存したもの | 実際の検査 | 未完成・未実施 |
| --- | --- | --- | --- |
| VB.NET_WinForms | 2画面・Designer/Presenter・プロジェクト・README | 中断前ビルド0警告/0エラー。Native smokeはWPFと合わせ12件 | 後の候補順/表示補助変更は未再ビルド。実画面受入・実SQLServer未実施 |
| CSharp_WPF | 2画面XAML/MVVM・プロジェクト・README | 同上 | 同上。最終ソースの12件合格とは扱わない |
| CSharp_ASPNET | 2画面Razor/MVC・セッション/CSRF/検索状態・README | .NETビルド0/0、Web39件（実HTTPS/Kestrel＋fakeサービス） | 実DB、ブラウザーE2E、本番認証/配備未実施 |
| Vue_CSharpAPI | Vue/TypeScript2画面、C# API、ロック/README | APIビルド0/0、Vue strict型検査/Vite bundle成功、npm audit0件。Web39件はMVC/API合同 | 実DB、ブラウザーE2E、負荷/受入未実施 |
| COBOL | 16 COBOL、11 COPY、25 SQL、C/ODBC bridge等 | ファイル/CALL/COPYの読取り棚卸し | STRENDER未定義、画面/保守/配備/Make等未生成。未コンパイル・未稼働 |
| AS400_RPG | 19担当ファイル＋Db2 DB資源4、RPG/C/COPY等 | 生成器実行とソース棚卸し | DDS/UI/STUMNT/CL/BNDDIR等未生成、参照未閉鎖、既知残件。未コンパイル・未実機 |
| Access | VBA12モジュール/6クラス、4非連結フォーム生成手順、ACE資源 | 専用ACCDBでVBA実行、11検査通過後に学生CREATEでDAO3201。独立SQL/DAO FK再現 | 正当学生の保存往復未達。全保守・画面・競合試験未実施。正式初期backend未生成 |
| Shared Core/CLI | .NETサービス・正規化/和暦・検索/保存/確認/監査・マスタ保守CLI | CLIビルド0/0、最新Core79件の独立境界/入力規則検査 | SQLServerの保存/監査/競合/保守結合は未実施。ネイティブ本番EXEC-only手続とDB側正規化入口は未実装 |
| SQLServer/Db2/ACE DDL | 方式別schema/seedと生成器 | SQLServerは7表（業務5表89列＋技術2表）、5分類70値生成。Db2/ACEは6表91列 | SQLServer/Db2へ未接続・未実行。ACEの実行は専用fixtureだけで本件が未解決 |

SQLServer seedに実クラス・学生は作成しない。Access fixtureのクラス1件・監査1件は実施検査で発生したデータであり、正式seedとは区別する。`StudentManagement.slnx`は保存したが、solution全体としてのビルドは未実施。

読取り棚卸しで残った未検証のコード問題: `Shared/StudentManagement.Core/MasterMaintenanceService.cs` 119行の監査種別選択は、既に停止中のコードの名称等を変更する場合にもSTOPとなる可能性がある。実DB往復は未検証で、停止後は修正していない。RPGの認可メッセージ残件、COBOLの未定義呼出し等とともに、再開後の修正・検査対象にする。

方式別の仕様ID対応・ファイル・残件: [Native](native-implementation.md)、[Web](web-implementation.md)、[COBOL](cobol-implementation.md)、[RPG](rpg-implementation.md)、[Access/Db2](legacy-implementation.md)、[Shared説明](../srcs/Shared/README.md)。

## 検査の証拠・限界

| 記録 | 内容 |
| --- | --- |
| [build-agent-verification.json](build-agent-verification.json) | preflight専用fixture9件PASS。意味整合の全自動検査ではない |
| [03-verification.json](20261012-build-03-verification.json)、[log](20261012-build-03-verification.log) | .NET5プロジェクトのビルドとCore63/Native12/Web39の実行。全8コマンドexit0 |
| [core-verification.json](core-verification.json) | その後に項目組合せ等を増やして実行したCore79件PASS。63件の記録とは別 |
| [web-build.log](web-build.log) | API/MVC、Vue型検査/bundle、監査。SDK10.0.401、Node24.16.0、npm11.13.0、Vue3.5.43、Vite7.3.7 |
| [legacy-evidence.json](legacy-evidence.json)、[fixtures](legacy-fixtures.json) | Access実機11通過後の失敗、通常FK2経路独立再現、入力/試験DBハッシュ |

未実施: 実SQLServer/Db2のDDL・学生CRUD・監査原子性・2主体最終席/版競合・確認期限/候補変化・確定応答喪失、全方式の画面受入、COBOL/RPG処理系適合、負荷・性能、本番認証/最小権限/配備、逆生成、採点。fakeサービスや非表示smokeの成功をこれらの合格へ拡張しない。過去レビューの合格を現改訂へ流用しない。

## 範囲外の留保・引継ぎ

全体の設計/評価ステータスや他Agentの入口は今回の書込み許可外なので更新していない。評価側の版/ハッシュ整合は別工程であり、spec-evalを参照して調整していない。現入力・途中出力を引継ぎ、新改訂と今回の証拠を混在させないこと。

次の実装作業は [STR-ACCESS-001の再開条件](structural-problem-STR-ACCESS-001.md) を満たした仕様を別Agentが確定した後に行う。現在は報告と途中成果保存で停止している。
