# WPF 内部の呼出契約

`Core/NativeStoredProcedureClient.cs` は呼出元が開いた SqlConnection / READ COMMITTED SqlTransaction を受け取ります。全コマンド・ReadAsync・NextResultAsync に CancellationToken を渡し、commit / rollback は行いません。

| API | 追加引数 | 結果 |
|---|---|---|
| SaveAsync(c, tx, SaveRequest, sessionId, requestId, ct) | 原入力19項目（生年月日は４項目）、選択年度・学年、理由、対象ID、期待版、確認token | SaveResult |
| DeleteAsync(c, tx, id, version, rawReason, sessionId, requestId, ct) | 管理者の削除理由原入力 | SaveResult |
| SaveClassAsync(c, tx, ClassChange, requestId, rawReason=null, ct) | 原クラス項目、対象ID、期待版 | MaintenanceResult |
| SaveCodeAsync(c, tx, CodeChange, requestId, rawReason=null, ct) | 原コード項目、期待版 | MaintenanceResult |

SQL学生入口の第一結果は `outcome, code, field, student_id, row_version, confirmation_token, candidate_count, request_id, warning_code, max_length`。outcome は Ready（prepare内部）、Saved、NoChange、ConfirmationRequired、ValidationFailed、Conflict、NotFound、Forbidden。第二結果は確認候補の先頭20件で、**student_no / student_name / birth_date / class_name の４列だけ**です。birth_date はクライアントで和暦表示へ変換します。候補の住所・電話・カナ・在籍区分・更新情報・ID/版は返しません。互換 StudentRow の非対象項目は null/空/default を格納します。全候補数は candidate_count、全候補ID/版集合の照合はサーバー内だけで行います。

マスタ第一結果は `outcome, code, field, row_version, same_name_warning, target_key, request_id, max_length`。SameNameWarning は同年度・同学年の別クラス同名通知です。マスタキー・版・監査主体を呼出者の文字列で置き換えません。

SQL例外 2601/2627 は一意性、547 は参照不整合、1205/1222/3960/51001/51005 は競合、229 は権限として既知メッセージへ対応します。それ以外は上位へ伝播し、呼出元が rollback / Unknown 判定を行います。ValidationFailed の FieldError.Message はコード文字列でなく仕様の日本語メッセージです。

SQL DML・識別子・列一覧は生成器の固定内容です。ユーザー原入力は型付き nvarchar(max) パラメータ１個の XML へ格納し、文字列連結 SQL を作りません。Raw XML は全必須フィールド名を含み、重複・未知フィールド・外部実体・子要素・任意属性を拒否します。CR は文字参照で保持して原入力文字数を検査します。

確認結果の状態と版は COMMIT 前の暫定値です。サービス側の commit 結果を確認してから Saved を公開してください。ConfirmationRequired は確認情報を永続化してから UI 待機へ移り、接続・トランザクション・ゲートを保持しません。
