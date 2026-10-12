<!-- spec-meta: {"schema":"spec-md/1.0","documentId":"CSHARP_WPF-DOC-D58CD06F2DF9","version":"8.0","path":"test-project1/srcs/CSharp_WPF/spec/規約/CSharp_WPF.md","sheets":[{"heading":"確認情報・権限・配置","kind":"GRID","sheet":"01_確認情報・権限・配置"},{"heading":"共通規約の具体化","kind":"GRID","sheet":"02_共通規約の具体化"}],"isolationProfile":"CSharp_WPF"} -->
# C#／WPF 開発規約

| 項目 | 内容 |
| --- | --- |
| 版数・改訂日 | 8.0／2026-10-12 |
| 対象方式 | C#／WPF |
| 適用 | 設計上の実装契約。製品コードの実装・コンパイルは未実施 |

開発入力：[学生検索詳細](../詳細仕様書/CSharp_WPF/01_学生検索画面.md)／[学生登録詳細](../詳細仕様書/CSharp_WPF/02_学生登録画面.md)／[共通実装](../共通/方式別/CSharp_WPF/01_共通実装仕様.md)／[DB定義](../DB定義/SQLServer/01_DB定義書.md)／[方式別開発規約](CSharp_WPF.md)／[共通開発規約](開発規約.md)。

## 確認情報・権限・配置

メモリーSearchContextはWindowインスタンス別30分。警告は10分、正規化全業務値・対象・旧版・全候補ID/版を対応付け、確認ダイアログを開く前にTx終了。DBに対する不正なクライアント直結を防ぐ本番境界は、DBで認証された個別主体＋実行専用保存手続`student_api.prepare_save / persist_student / delete_student`を基準とする。直接DMLは許可せず、DB入口でも主体の役割と権限を検査する。

`t_confirmation`補助表はtoken uniqueidentifier PK、principal nvarchar(128)、session_id uniqueidentifier、target_id bigint NULL、expected_version bigint NULL、payload_hash binary(32)、candidate_hash binary(32)、expires_at datetimeoffset(7)、consumed bit。学生業務5表ではない。DB入口は発行済み確認情報を照合して業務値を更新する。保存手続内部でCOMMITせず、UnitOfWorkが確定する。理由だけで警告を迂回させない。秘密をWPFバイナリーやappsettingsへ埋め込まない。

ネイティブエラー2601/2627はDB入口の固定エラーコードで番号重複／マスタ重複、547は参照不整合、版0件はE-STU-105、ロック待ち・デッドロックは自動業務再送せず再確認、その他は受付番号付きE-COM-004。Commit後通信断は結果不明。

.csprojはTargetFramework=net10.0-windows、UseWPF=true、Nullable=enable。Microsoft.Data.SqlClient版を固定しWindows環境でXAMLをビルド。ViewModel単体試験、独立した2本の実DB接続の競合試験、UI自動化・DPI・日付入力・アクセシビリティを行う。実装とコンパイル結果は未提供であり、例は構造と契約を示す。

## 共通規約の具体化

本方式では[共通開発規約](開発規約.md)を適用し、業務ルールや項目長は[詳細仕様](../詳細仕様書/CSharp_WPF/02_学生登録画面.md)と[DB定義](../DB定義/SQLServer/01_DB定義書.md)に一致させる。長さの計測単位はUnicodeスカラー値。処理系のバイト／コード単位の領域は余裕を確保し、業務最大長を拡大しない。

機能固有のイベントは機能別詳細、複数機能で使う接続・トランザクション・正規化・和暦・認可・確認・UI部品は方式別共通へ置く。コピーした定義の修正は同じ仕様IDを持つ文書へ同時に反映する。デザイナー生成物、業務ロジック、テスト資源を分ける。

ビルド設定・ライブラリ版・DB設定・文字コード・暦定義版を方式プロファイルに記録する。現行の採用版は仮定を維持し、勝手な最新版への変更は行わない。API署名や型を変更する際は両画面、共通、DB、試験条件を同一改訂で直す。
