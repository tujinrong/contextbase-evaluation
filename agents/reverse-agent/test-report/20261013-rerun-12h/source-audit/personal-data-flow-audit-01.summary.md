# 個人データ source-only 追加監査

対象は封印snapshotの41 raw sourceと、SHA固定済み検索基本05・詳細04。固定checklist.v1と25 sourceのSHA、前回独立監査の41 source SHAを再照合した。原仕様・評価期待値・採点・training-assisted・新基本06/詳細05は未読。原稿と原ソースは変更していない。

検索氏名・カナ・電話はPOSTフォーム/DTOから検索用引数へ渡り、成功後はAppliedの入力コピーとLastResultをサーバー辞書に保持する。一覧は氏名・カナ・和暦生年月日・所属・都道府県名＋住所1・本人電話を含む。住所2、メール、緊急連絡先、備考を検索表示へ出さず、登録読込では明細から編集inputへ渡す。生成された往復URLには状態ID/版や学生IDを載せ、氏名・電話・住所をシリアライズしない。状態IDは乱数32バイトの16進値である。検索専用cookie書込みは見つからず、認証cookieへのSignInAsyncは別の利用者claimsを受けるため、全cookieの個人識別情報がないとは保証しない。

原ビューの動的値は通常のRazor @式とasp-for/validation Tag Helper記法。明示Raw/Html.Raw/IHtmlContent/HtmlString/WriteLiteralは対象application source内で0件。手組の外側エラーHTMLはHtmlEncodeを使用する。実HTML・DOM・framework出力は未実行。

HTTP原設定はno-store/nosniff/no-referrerとselfを中心とするCSP、frame-ancestors none、HTTPS redirect、Secure/HttpOnly/SameSiteStrict cookie、認証30分・sliding expiration。実配備の挙動は未確認。

通常障害のapp固有ILogger/Log*/Console呼出しは未観測で、appsettingsはDefault/ASP.NET Warning。これは運用ログのPII不在を保証しない。実監査はAuditメソッドで、変更列名JSON、対象ID、前後版、実施者、時刻、相関ID、理由、重複確認値を保存する。氏名/住所/電話のbefore/after値を監査引数へ渡さない。一方、自由入力の理由は長さ・制御文字・改行・trimの検査後にoperation_reasonへ本文保存され、削除理由は学生表delete_reasonにも保存される。伏字処理はなく、理由内容次第で個人情報を含み得る。AuditBuilderという型名は見つからない。

既存2稿に新たな重要矛盾・重要業務誤りは発見しなかった。DTO・表示・メモリ・暗号化DDLの未接続境界は説明されている。検索データ/URL/cookieの区分、Razor/手組HTMLの出力境界、監査引数と自由理由・通常ログの限界は補足が不足する。詳細の監査はINSERT記述のみで、基本は変更列JSON・理由等を既に記述する。HTTP不足は既存DC07の継続として扱い、新規重複計数しない。source-pilotへ根拠行・実quote付きで共有済み。

本監査はコードの観測であり、アプリ・DB・SQL・ブラウザ・運用ログ・配備を検証していない。仕様書得点、個人情報保護の合格、視覚合格は作成していない。40 source引用範囲、12 flow、6稿比較、負の文字列検索、各SHAをJSONへ保存した。
