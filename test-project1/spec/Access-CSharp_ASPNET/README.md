<!-- spec-meta: {"schema":"spec-md/1.0","documentId":"ACCESS-CSHARP-MIGRATION-INDEX","version":"0.2","path":"test-project1/spec/Access-CSharp_ASPNET/README.md","sheets":[{"heading":"対象と根拠","kind":"GRID","sheet":"01_対象"},{"heading":"配置と判断","kind":"GRID","sheet":"02_判断"}]} -->
# Access-CSharp_ASPNET 移行設計

版0.2／2026-10-27。

## 対象と根拠

projectId=test-project1、sourceRoot=srcs/Access-CSharp_ASPNET/。利用者が計画の実施と最大2回の訓練、およびローカルSQLEXPRESSへの新規専用DB作成を指定した。原入力はsrcs/Access/build/StudentManagement.accdb、SHA-256 F5FF069C5D7AA45CFAE80584319FD11F0A0B8A6C52E141DA51D5263532D82CA4。

移行の業務根拠は同本体のDAO構造とフォーム・VBAの抽出内容である。既存方式の原仕様・spec-eval・Web業務ソースは使用していない。本体の保存クエリ、フォーム内イベント、VBA中のSQLと取得後の比較も対象とする。

## 配置と判断

C#はsrc/StudentManagement.Coreとsrc/StudentManagement.Web、SQLとDB構成はdatabase/へ分離し、StudentManagement.slnxから開く。採用技術はASP.NET Core MVC／Razor、net10.0、SQL Server。DDLは2022互換構文を基準とし、今回の実検証環境はExpress 17.0.5005.3である。

Accessの整数row_versionをintとして維持し、ISO日付文字列と物理容量、業務上の文字数制限を分ける。SQL Serverで外部キー列の文字容量一致が必要な箇所は親列へ合わせた物理容量とし、CHECKで元の子列容量を維持する。実行結果から業務長を緩和しない。

Webの主体は認証済みリクエストから供給する。訓練環境だけ、明示した架空のverification主体を使用し、SQLのt_app_roleから権限を解決する。通常環境へ固定Adminやメモリfallbackを持ち込まない。

元のWin32貼付・スクロール処理はブラウザーの入力・検証・スクロールへ対応付ける。監査・保存/取消・版・競合・和暦表示は抽出コードとの比較対象。完全なAccess実機操作一致、参照ライブラリーの完全目録、任意のActiveX依存、別Accessへの一般適用性は未確認として残す。

必要マスタは抽出VBAの定数を出所付きJSONとSQLに変換し、学生・クラスは完全に架空の確認データを使用する。既存運用データの移行、本番配備とWindows認証ホスト設定は今回の範囲外。最新の検査と未実施はsourceRoot/build/で管理する。
