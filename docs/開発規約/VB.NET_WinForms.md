<!-- spec-meta: {"schema":"spec-md/1.0","documentId":"DOC-3197C1E06BB0","version":"6.0","path":"docs/開発規約/VB.NET_WinForms.md","sheets":[{"heading":"状態・権限境界・配置","kind":"GRID","sheet":"01_状態・権限境界・配置"},{"heading":"共通規約の具体化","kind":"GRID","sheet":"02_共通規約の具体化"}]} -->
# VB.NET／WinForms 開発規約

| 項目 | 内容 |
| --- | --- |
| 版数・改訂日 | 6.0／2026-10-11 |
| 対象方式 | VB.NET／WinForms |
| 適用 | 設計上の実装契約。製品コードの実装・コンパイルは未実施 |

開発入力：[学生検索詳細](../../spec/詳細仕様書/VB.NET_WinForms/01_学生検索画面.md)／[学生登録詳細](../../spec/詳細仕様書/VB.NET_WinForms/02_学生登録画面.md)／[共通実装](../../spec/共通/方式別/VB.NET_WinForms/01_共通実装仕様.md)／[DB定義](../../spec/DB定義/PostgreSQL/01_DB定義書.md)／[方式別開発規約](VB.NET_WinForms.md)／[共通開発規約](../開発規約.md)。

## 状態・権限境界・配置

評価時SearchContextはフォーム別メモリー、30分、利用者失効で破棄。DuplicateConfirmationは10分、利用者・セッション・対象・版・正規化全業務値・全候補ID/版を保存し、保存時の再検索と比較。フォーム内の確認済Booleanだけでは続行しない。

ネイティブクライアント直結を選ぶため、本番では個別に認証したDB主体と実行専用のDB更新入口を組み合わせる。`student_api.prepare_save`は検査後に確認情報をサーバーに発行、`student_api.commit_save`は確認情報・理由を再検証し学生＋履歴を確定する契約とする。補助`t_confirmation`はtoken uuid PK、principal V64、session_id uuid、target_id L?、expected_version L?、payload_hash bytea、candidate_hash bytea、expires_at T、consumed Bを保持し、業務5表と別。直接DMLをREVOKE、共有パスワード埋込みを禁止。閲覧／編集／削除権限はDB更新入口でもDB主体から検査する。フォーム内評価サービスをそのまま改造可能なクライアントへ強いセキュリティ境界として配備しない。

ビルドは.vbprojでTargetFramework=net10.0-windows、UseWindowsForms=true、OptionStrict=On。デザイナー生成.vbと業務処理を分ける。Npgsqlパッチ版を固定、設定は環境の秘密管理から取得。GUIはUIスレッドで更新し、I/O完了をAwaitして戻す。キャンセル時に保存の確定を取り消せたと断定しない。依存版・DB入口実装・認証結合・DPI・障害復旧を配備前に試験する。これらは仕様でありビルド済み成果物ではない。

## 共通規約の具体化

本方式では[共通開発規約](../開発規約.md)を適用し、業務ルールや項目長は[詳細仕様](../../spec/詳細仕様書/VB.NET_WinForms/02_学生登録画面.md)と[DB定義](../../spec/DB定義/PostgreSQL/01_DB定義書.md)に一致させる。長さの計測単位はUnicodeスカラー値。処理系のバイト／コード単位の領域は余裕を確保し、業務最大長を拡大しない。

機能固有のイベントは機能別詳細、複数機能で使う接続・トランザクション・正規化・和暦・認可・確認・UI部品は方式別共通へ置く。コピーした定義の修正は同じ仕様IDを持つ文書へ同時に反映する。デザイナー生成物、業務ロジック、テスト資源を分ける。

ビルド設定・ライブラリ版・DB設定・文字コード・暦定義版を方式プロファイルに記録する。現行の採用版は仮定を維持し、勝手な最新版への変更は行わない。API署名や型を変更する際は両画面、共通、DB、試験条件を同一改訂で直す。
