# CSharp_WPF Native 保存境界・マスタ保守生成と検査

実施日2026-10-12。入力は CSharp_WPF/spec の独立版8.0、46ファイル。担当出力は同方式 database/native、Core/NativeStoredProcedureClient.cs、Core/NativeMessages.cs。SQLServerStudentService、MasterMaintenanceService、StudentGateway の接続変更は親担当です。入力・出力ハッシュと生ログは [証拠 JSON](20261012-build-08-wpf-native-evidence.json) に固定しました。旧ログは保存しています。

本番保存入口 prepare_save / persist_student / delete_student と、管理者入口 save_class / save_code を実装しました。サーバーが原入力を再正規化し、DB主体・役割、期待版、最新コード/クラス、期間、定員、全重複候補、確認期限・単一使用を再判定します。保守は固定分類・コード桁、保護、クラス参照・在籍人数、同名通知、監査を扱います。呼出元 READ COMMITTED トランザクションの中で学生/保守の共通ゲート、変更、監査、確認消費を実行し、内部 commit はしません。学生・マスタ・監査・確認表への通常役割の直接 DML を拒否し、必要な SELECT と公開 EXEC だけを許可します。

確認情報は主体・セッション・対象・期待版・正規化値・全候補ID/版集合へ結び付けます。表示の先頭20件と集合判定を区別し、候補が０件へ変わった場合も再確認します。ConfirmationRequired は呼出元が commit してゲートを解放してから UI で待機します。Saved は呼出元の commit 成功後に公開します。commit 不明は呼出元が Unknown として扱います。監査失敗を握りつぶしません。

原入力 XML は型付き nvarchar(max) パラメータで渡し、ユーザー値から SQL を組み立てません。19業務項目、生年月日の和暦４原入力、年度/学年ヒント、理由をサーバー側で Unicode scalar 数、NFKC、かな、連絡先、日付、在籍状態、任意続柄へ正規化します。未知・重複フィールド、DTD、外部実体、子要素、任意属性を拒否し、CR は文字参照で保ち原入力文字数を検査します。マスタも原入力から再検証します。NativeMessages は当方式のメッセージ仕様58件を生成し、項目名・サーバー実上限・照合IDを日本語で解決します。不正マスタXMLのクライアント例外も ValidationFailed へ対応させました。CancellationToken をすべての SQL 読取へ渡します。

| 検査 | 当回結果 | 実際に検査した範囲 |
|---|---|---|
| SQLCLR用 .NET Framework 4.7.2 DLL | 0 warnings / 0 errors | production DLL のコンパイル |
| NativeBoundary.Tests / .NET 10 | 88 / 88 PASS | 原入力wire、正規化、Unicode/かな/和暦/日付/NULL、マスタ、JPメッセージ、XML異常 |
| NativeFramework.Tests / CLR 4.0.30319.42000 | 17 / 17 PASS | 実 DLL と SqlFunction wrapper の呼出、Framework NFKC/かな/和暦/Unicode/NULL/マスタ |
| SQL ScriptDom 18 / TSql160Parser | 3 / 3 構文指摘0 | 000_sqlclr.sql / 010_student_api.sql / 020_master_api.sql の構文 |
| SQL Server実DB | 未実施 | CLRホストロード、手続意味解析・実行、権限、確認永続化、監査・競合・commit/rollback |

実DLL SHA512 は `E79A7E5EEAB1654E1C4DF67D28C0899EAFAA1FBD07BA7B45A11A2C2D723C1559B5879D82880C0B5F0D0B842EF164F7E81886C1AEDECE3874B4530F069D96DA83`。Framework 試験がロードしたDLLはこのハッシュと一致します。000_sqlclr.sql は同じバイト列・SHA512を内包します。Framework の通常ホストでの通過を SQL Server のCLRロード通過として扱いません。

最初の SQL 構文検査でマスタ手続の scalar/table 混在 DECLARE を検出しました。生成器を修正し、syntax-02、最終syntax-03で３ファイルすべて通過しました。最初の失敗ログも削除していません。既存規約や業務仕様の構造問題は新たに検出していません。

再生成・配備は [方式内 README](../srcs/CSharp_WPF/database/native/README.md)、呼出型と戻り列は [方式内契約](../srcs/CSharp_WPF/database/native/INTERFACE.md)。SQLCLRの厳密セキュリティを維持し、DB管理者が実DLL SHA512を承認して信頼済み登録する構成です。[Microsoft公式の信頼済みアセンブリ手順](https://learn.microsoft.com/en-us/sql/relational-databases/system-stored-procedures/sys-sp-add-trusted-assembly-transact-sql?view=sql-server-ver15) と [対応 Framework ライブラリ](https://learn.microsoft.com/en-us/sql/relational-databases/clr-integration/database-objects/supported-net-framework-libraries?view=sql-server-ver16) に照合しました。SQLServer実機への配備・業務結合が残り、当回のローカル合格から本番DB動作の合格を推定しません。
