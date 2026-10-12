# WPF Native 年度形式・重複候補の回帰修正

実施日2026-10-12。入力は当方式 CSharp_WPF/spec の最終独立仕様46ファイルです。文書ごとの版・ハッシュ、生成資源・DLL・クライアントのハッシュと生ログを [当回証拠](20261012-build-09-wpf-native-evidence.json) に記録します。旧08報告・JSON・失敗を含む生ログはそのまま残しています。

最終監査で、学生年度ヒントを汎用IDとして正規化して原入力最大19桁を許容することと、重複候補SQLが検索一覧の住所・電話・在籍区分・履歴等を返すことを検出しました。実装の不備で、仕様の構造問題ではありません。

年度はローカル REG-016 / CHK-034 に従い、専用 SchoolYear 検査へ変更しました。原入力は４文字上限、NFKCとtrim後はASCII数字ちょうど４桁、1900～9998です。`02026`、19桁のゼロ埋め、３桁、指数表記、範囲外、trim前５文字を E-DATE-003 で拒否します。４桁全角数字はNFKC後に受理、選択補助のNULLは保持します。クラス保守の年度も同じ専用規則へ揃えました。最大ID等の19桁規則は年度へ流用しません。

生成器の重複候補射影を `student_no / student_name / birth_date / class_name` の４列へ変更し、生成SQLを更新しました。全候補ID/版集合、件数、ハッシュ、先頭20件の抽出はサーバー内部で維持します。クライアントの ReadDuplicateCandidate は４列だけを読み、和暦は既存 BirthDateWareki に変換します。互換 StudentRow のカナ・年度・学年・コード・在籍区分・住所・電話・入学日・更新時刻・ID・版は null/空/default です。新しい４列だけの DataTableReader fixture で余分な列を要求しないこと、和暦表示、クラスNULL、他項目非返却を確認しました。SQL側にも候補射影の許可４列検査を追加しました。

| 当回検査 | 結果 | 生ログ/JSON |
|---|---|---|
| SQLCLR production DLL 再生成・net472 build | 0 warnings / 0 errors | 20261012-build-09-wpf-native-build-01.log |
| .NET 10 原入力・正規化・候補mapper境界 | 102 / 102 PASS | 20261012-build-09-wpf-native-boundary-01.log |
| 実 .NET Framework DLL / SQLFunction wrapper | 27 / 27 PASS | 20261012-build-09-wpf-native-framework-build-01.log / framework-run-01.log |
| SQL ScriptDom ３資源と候補射影 | 構文0件、許可４列 PASS | 20261012-build-09-wpf-native-syntax-01.json / .log |

新しいDLL SHA512 は `A5889EAA82A078761A59AD48F79472437671FB8AFAECFA2706948AC9DD95915A727F0717500CF01BA0DB4CF5F4EC32C5B5609F4F5D49D739616AE1D73E6D5468`。000_sqlclr.sql はこの実バイナリとハッシュへ更新しました。Framework fixture がロードするDLLと一致を確認します。旧08のDLLハッシュや試験数を、この改訂の結果として流用しません。

SQL Server 実機の CLR ホストロード、手続の意味解析・実行、権限、確認永続化、監査・競合・commit/rollback・確定応答喪失は未実施です。SQL構文、生成器射影、通常Framework実行の合格から、それらの成功を推定しません。今回の書込みは当WPFの Native 資源と当方所有の client だけで、Access や他方式・グローバル定義は変更していません。
