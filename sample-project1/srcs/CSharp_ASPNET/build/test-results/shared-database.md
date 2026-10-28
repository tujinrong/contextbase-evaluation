# CSharp_ASPNET 共有DB・Debug検証

2026-10-27。対象はtest-project1／CSharp_ASPNET。実DBはローカルSQLEXPRESSのAccessRebuilderTraining_01a17be7。

Debug/Releaseの既定プロファイルはSharedTrainingSql。Visual StudioでStudentManagement.slnxを開き、StudentManagement.Webを起動プロジェクトにしてF5で実行する。URLはhttps://localhost:7241/students。保存済みのhttpsも同じ共有DB設定を使う。旧独立DBはNativeを選び接続と認証を設定する。

既存の物理型int・ISO日付文字列・UTC日時・監査Guid文字列をSharedAccessのデータアクセス層で変換する。DB初期化・DDL適用・列の破壊的変更は行っていない。SharedDatabaseTrainingはHTTPS/loopback専用で、役割は要求ごとにt_app_roleから取得する。

| 検査 | 今回の結果 | 根拠 |
| --- | --- | --- |
| Solution Debug/Releaseビルド | 警告0・エラー0 | shared-db-regression.json |
| Core境界 | 135 PASS | shared-db-regression.json |
| MVC HTTPS契約 | 129 PASS、業務サービスはfake | shared-db-regression.json |
| 認証契約 | 60 PASS | shared-db-host.json |
| 実DB結合 | 8 PASS、作成・無変更・競合・ガード・削除 | shared-db-integration.json |
| 両アプリの実ブラウザー連携 | 7 PASS、相互読取・更新・競合・削除・CSRF | shared-db-browser.json |
| 実DB Reader権限 | 5 PASS、直接新規URL403を含む | shared-db-reader.json |
| マスターCLI | 既存クラスの無変更保存PASS | shared-db-maintenance.json |
| Debug既定起動・https互換 | 実DB検索2件・編集表示・HTTP200 | shared-db-debug.json |
| DB/入力保全 | 7表93列・既存学生2件・相手側59ソース・Access原本が不変 | shared-db-preservation.json |
| ソース配布 | ZIP隔離ビルド | shared-db-package.json |

検証で追加した合成学生は論理削除し、監査を保持する。試行途中で追加された1件も通常の削除処理で整理済み（shared-db-cleanup.json）。既存TRN001/TRN002はデータハッシュが一致した。

今回のDebug検証はCLIでDebugビルド・既定起動し、実ブラウザーで画面とDB読取りを確認した。Visual Studioのデバッガー操作、外部認証、本番配備、正式採点は未実施。正式率はnull。旧2026-10-25レポートは当時の結果として区別する。
