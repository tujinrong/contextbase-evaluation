<!-- spec-meta: {"schema":"spec-md/1.0","documentId":"ACCESS-CSHARP-MIGRATION-INDEX","version":"0.6","path":"test-project1/spec/Access-To-CSharp_ASPNET/README.md","sheets":[{"heading":"対象と根拠","kind":"GRID","sheet":"01_対象"},{"heading":"配置と判断","kind":"GRID","sheet":"02_判断"}]} -->
# Access-To-CSharp_ASPNET 移行設計

版0.6／2026-10-28。

## 対象と根拠

projectId=test-project1、sourceRoot=srcs/Access-To-CSharp_ASPNET/。利用者が計画の実施と最大2回の訓練、およびローカルSQLEXPRESSへの新規専用DB作成を指定した。原入力はsrcs/Access/build/StudentManagement.accdb、SHA-256 F5FF069C5D7AA45CFAE80584319FD11F0A0B8A6C52E141DA51D5263532D82CA4。

業務の根拠は同本体のDAO構造とフォーム・VBAの抽出内容である。初期の訓練2回ではWebソースを構成参考に限定したが、利用者の追加指示により、現在はCSharp_ASPNETソースを読取り専用の設計・実装参照として使う。Accessのコントロールやイベント順を忠実に再現することは目標としない。既存方式の原仕様・spec-evalは入力にしない。

2026-10-28の名称変更指示により、方式ID・sourceRoot・specRootを上記の新名称へ揃える。既存DB名・接続先・所有者マーカーおよび封印済み2回の訓練記録は変更しない。過去の記録内の旧パスは当時の証跡として保持し、今回の配置検証と区別する。

## 配置と判断

C#はsrc/StudentManagement.Coreとsrc/StudentManagement.Web、SQLとDB構成はdatabase/へ分離し、StudentManagement.slnxから開く。採用技術はASP.NET Core MVC／Razor、net10.0、SQL Server。DDLは2022互換構文を基準とし、実検証環境はExpress 17.0.5005.3である。

Web化改訂では、CSharp_ASPNETの検索・登録ビュー、CSS、JavaScript、MVCの状態管理を参照する。検索は4条件を維持し、結果の並び替え・表示件数・ページ移動を設ける。編集は基本情報と関連する入力群、項目別エラー、保存操作を読みやすく配置し、画面幅に応じて組み直す。候補連動は認証・CSRF・編集所有束縛を維持したJSON更新とし、全画面POSTに依存しない。生年月日はWebのdate入力と和暦の補助表示を使い、Coreの業務型へ境界で変換する。

利用者の「このルールで変換し直してください」により、AR028～030を今回のWeb再構築へ適用する。PCの基準表示領域は1366×650／1280×650 CSS pxとし、検索・編集・参照は左見出し／右項目の列を揃える。グループ、余白、入力幅、補助説明を整理し、主要入力・保存を近接させる。利用者の追加指定によりスマートフォン対応は対象外とする。PCでの表示拡大時は入力と見出しの対応を保持し、必要な縦スクロールを許容する。生年月日・入学日・卒業退学日は1つのカレンダー入力と同期した和暦表示とし、保存値はISO日付のまま維持する。日付の必須条件、範囲、閏日・元号境界、クリア・再表示を検証する。業務Core、SQL構造、既存データ、参照方式ソース、訓練2回台帳は変更しない。実装・検証の実施状態はsourceRoot/build/test-results/の今回記録で確認する。

2026-10-28の追加指定（AR031～032）：グループ見出しは「01 基本情報」等の太字を内容グループの上方へ独立して置く。Accessの枠線へ見出しが重なるGroupBox風の表現を既定にしない。Webメニューは左の縦サイドメニューとし、現在の画面を明示する。管理者だけの項目表示、直接URLでの権限検査、キーボード操作を維持する。サイドメニューで主領域を過度に狭めず、PC1280×650／1366×650の見出し・入力・主要操作を確認する。参照モードの入力無効化、保存・取消・日付・候補連動・CSRF・競合・監査の業務契約は変更しない。スマートフォン対応は引き続き対象外。実行結果はsourceRoot/build/test-results/web-shell.jsonへ記録する。

Accessの整数row_versionをintとして維持し、ISO日付文字列と物理容量、業務上の文字数制限を分ける。SQL Serverで外部キー列の文字容量一致が必要な箇所は親列へ合わせた物理容量とし、CHECKで元の子列容量を維持する。実行結果から業務長を緩和しない。

Webの主体は認証済みリクエストから供給する。訓練環境だけ、明示した架空のverification主体を使用し、SQLのt_app_roleから権限を解決する。通常環境へ固定Adminやメモリfallbackを持ち込まない。

元のWin32処理はブラウザーの標準入力・検証・スクロールへ設計し直す。保持するのは保存/取消の意味、権限・制約・版・競合・監査の業務契約であり、Accessと同じボタン数・配置・イベント順は受入条件にしない。原Access実画面の業務比較、参照ライブラリーの完全目録、任意のActiveX依存、別Accessへの一般適用性は未確認として残す。

必要マスタは抽出VBAの定数を出所付きJSONとSQLに変換し、学生・クラスは完全に架空の確認データを使用する。既存運用データの移行、本番配備とWindows認証ホスト設定は今回の範囲外。最新の検査と未実施はsourceRoot/build/で管理する。
