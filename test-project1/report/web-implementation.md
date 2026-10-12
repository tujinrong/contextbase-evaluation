# Web方式生成・検査記録

最終状態: **STR-ACCESS-001 により全方式の生成を中断**。Webの下記ソースと中断前検査は保存した。これらは実DB・実機適合や7方式の実装完了を示さない。[全体報告](build-report.md)を参照。

記録版1.0／2026-10-12。projectId=test-project1。工程=build。担当=CSharp_ASPNET／Vue_CSharpAPI。

## 入力と修正

仕様セット7.2の詳細／方式別共通／全体・プロジェクト開発規約／SQLServer DB定義を入力にした。spec-evalは参照・変更していない。入力ハッシュ・セット再固定はrootの生成記録を正本とする。

4詳細文書を7.0→7.3に局所修正した。HTMLモック断片は変更していないためassetsのHTML/PNGは再生成していない。

| 文書 | 修正 | 一意な根拠 |
| --- | --- | --- |
| spec/詳細仕様書/CSharp_ASPNET/01_学生検索画面.md | 概要責務StudentApplicationService→StudentQueryService | 方式別共通のQuery/Command分離 |
| spec/詳細仕様書/CSharp_ASPNET/02_学生登録画面.md | 概要責務StudentApplicationService→StudentQueryService / StudentCommandService | 方式別共通と読込・保存責務 |
| spec/詳細仕様書/Vue_CSharpAPI/01_学生検索画面.md | 概要責務StudentCommandService→StudentQueryService | 方式別共通の検索責務 |
| spec/詳細仕様書/Vue_CSharpAPI/02_学生登録画面.md | 本人電話の再掲raw32→raw20 | 同書REG-011、共通09、項目長基準LEN-12 |

67親項目の長さ・必須・条件・初期値・未設定・範囲・正規化/チェックIDを共通09と比較し、DB ID範囲の具体化以外は一致。構造中断ブロッカーはこの担当範囲で確定しなかった。既存レポートの合格は今回の合格へ流用していない。

内部表示領域の旧10/50は業務値9/18より大きい領域として実装上保存上限を拡張しない。API表で省略されていた検索／clear／resumeのContextRevisionは、共通の旧Revision拒否契約に従い実装で必須化した。仕様意味の追加変更は行っていない。

## 出力

`srcs/CSharp_ASPNET/`と`srcs/Vue_CSharpAPI/`に2業務画面の実ソース・プロジェクト・設定例・ロックファイル・起動手順・仕様ID対応を生成。共通DB処理はrootの`srcs/Shared/StudentManagement.Core/`、DDL/seedは`srcs/Database/SQLServer/`を参照する。

Cookie信頼主体、CSRF、JSON未知/重複プロパティ・型・64KiB検査、管理列拒否、Context所有者/セッション/タブ・30分・Revision・排他、原スナップショット、入力保持、和暦4原入力、全19保存項目、確認理由、候補最大20件、定員参考、削除専用要求、303/JSON成功復帰を実装した。

Web側は直接DB DMLを発行せず共有IStudentServiceへ渡す。共有サービスは実SQLServer接続・ゲート・再検査・保存/監査/確認の確定処理を担当する。管理者マスタ保守は共有StudentMaintenance CLIへ案内し、追加業務画面は生成しない。実DB保守結合は未実施。

## 実施結果

| 検査 | 結果・検査範囲 |
| --- | --- |
| dotnet build CSharp_ASPNET | 成功、警告0／エラー0。net10.0、SDK10.0.401 |
| dotnet build Vue_CSharpAPI/backend | 成功、警告0／エラー0 |
| npm run build | Vue strict型検査・Vite production bundle成功 |
| npm audit | 0件。初期パッチの監査結果を受けVue3.5.43/Vite7.3.7へ固定し、未使用Vitest除去 |
| Node／npm | v24.16.0／11.13.0 |
| tests/WebContracts.csproj | 39件PASS。実HTTPS/Kestrel＋fake IStudentService。SQLServer結合を含まない |

39件では所有者・セッション・タブ・期限・旧Revision、64bit範囲/指数拒否、JSON未知/重複/管理列/型/64KiB、401JSON、評価Cookieセッション、CSRF欠落400JSON、検索API、ID文字列と和暦、一覧の追加個人情報列非公開、Staff削除403、no-store/CSP、Razor2画面描画、Unknown保存結果が成功文言にならず検索確認を案内することを確認。ローカルHTTPS開発証明書の許容はテストクライアント内だけ。

## 未実施・制約

SQL Serverへ未接続。DDL実行・実保存・独立2接続競合・最終席・マスタ停止競合・障害確定/結果不明・本番権限の試験は未実施。ブラウザーE2E、実認証基盤、負荷・受入も未実施。生成／ビルド／fake HTTP契約を実DB・実機・性能の合格とは扱わない。

QA-AUTHはDevelopment限定・サーバー秘密必須の評価セッションアダプターを採用。外部認証基盤、保護鍵、実クラス、保存/消去・バックアップ運用は未確定。Webは単一サーバーのメモリ状態ストア。複数サーバー化では共有ストアと保護鍵の配置設計が必要。
