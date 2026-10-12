# Access 形式・Boolean修正 R4

実行ID `20261012-evidence-01-access-r4`。拡張子accdbでも内部を旧MDBで生成していた実装バグと、検索初期の卒業・退学・未所属チェックがNULLになっていた実装バグを修正した。NewCurrentDatabaseの形式値を10から12へ変更した。12はACCDB、10はAccess 2002–2003 MDBである。[Microsoft公式定義](https://learn.microsoft.com/en-us/office/vba/api/access.acnewdatabaseformat)

独立仕様45ファイルは不変。業務版8.0、単体配置版8.1、DB索引版8.2を実行時SHA-256で固定した。生成器とmodStudentFormsだけが今回のproduction変更である。入力・差分・実行範囲は [results.json](results.json)。

| 新規実行 | 結果 |
|---|---|
| SingleFile生成・VBA compile | 成功 |
| 通常31・拡張77・実フォーム29 | 137 PASS |
| 任意続柄NULL・複合FK | 21 PASS |
| 同一バイトのclean成果コピー | 配布19 PASS |
| FileFormat12・Standard ACE DB・初期Boolean | 10 PASS、cleanコピーでも10 PASS |
| 異なるAccessプロセスの最終1席 | 保存1件、E-STU-102拒否1件、占有1件・CREATE監査1件 PASS |

試験用Access.Runの引数をPS5のbyref呼出しへ修正し、新しいfixture・RunIdで競合を再実行した。最初のPS5文字コード失敗、フォームCOM取得失敗、競合テスト呼出し失敗は元ログを保存した。最終PS5Parserは対象4スクリプト0件。

旧配布成果は `Access/build/20261012-evidence-01-backup/StudentManagement.pre-format-fix.accdb` にSHA-256 `838F5FE63826FCE58FACE6C5102D363AF41C3EF433D6B2D7229C8D5DE0C93DE5` のまま退避した。clean成果のバイトコピーで原本を置換し、R4成果SHA-256は `090DB949398017D0583B24EA16D79EAC0C055577F82051B75A57146C0906C896`。StartupFormあり、試験モジュールなし、学生・クラス・監査0件、5分類70コード、SELF・外部リンクなし。[replacement.json](replacement.json)

架空3学生・1クラスのR4撮影用DBは別のbuildフォルダーだけに保存し、production入口で登録・DAO読返しを行った。[Access-ui-r4の結果](../Access-ui-r4/results.json)。原本はCOMで開かず、学生fixtureを混入させていない。

R4実画面で後から発見した検索4条件の「すべて」空表示は未修正範囲として記録し、R5へ続ける。このR4結果は完全仕様適合を主張しない。共有SQL移行・配備・認可・CRUD、Office 32-bit、10,000／10,001件性能、確定応答喪失は未実施。手動撮影はrootの別記録。
