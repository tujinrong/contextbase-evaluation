# Access の共有 SQL Server バックエンド適合調査

2026-10-12／projectId=test-project1／工程=共有構成への移行前・読取り調査／対象方式=Access。既存成果を変更する生成工程は実施していない。

Access は１個の accdb をフロントエンドにして、Windows 認証で共有 SQL Server を使用できる。現行成果は業務表を内包したローカル ACE 構成なので、そのまま接続先を差し替えるだけでは移行できない。既存の４フォームと VBA の画面処理を維持しつつ、DB アダプター、認可、排他制御、型、配備仕様を改訂する必要がある。Microsoft は Access VBA からの DAO/ODBC と ADO 接続、ADO Command によるパラメーター付き保存手続の呼出しを説明している。[Microsoft: Connect Access to SQL Server](https://support.microsoft.com/en-us/access/connect-access-to-sql-server)

最新の利用者指示を優先するため、「画面・物理業務表を全て単一 accdb 内へ格納」という旧構成を今回の移行先に強制しない。新構成の配布ファイルは１個の accdb フロントエンド、共有業務 DB は SQL Server と解釈する。この方針変更自体は旧仕様のバグや未承認の推測補完と区別する。共有 DB の採用に伴う業務契約の空欄は、生成担当が恣意的に埋めず、仕様担当による確定後に実装する。

## 調査範囲と証拠の性質

- 読取り対象：全体規則・build-agent 契約と、当方式内の README、spec、Build-Access.ps1、Classes、Modules、ACE database 資源。共通 SQL Server の確定 DDL/API は今回の Access 調査入力として提示されていないため、他方式の実装を正本に選んでいない。
- 公式資料：2026-10-12 に Microsoft Support / Learn を確認。資料の機能説明と、当プロジェクトに必要な設計判断を区別した。
- 既存 accdb を開いていない。今回取得した SHA-256 はバイト列の読取りだけ。内部テーブル件数、フォーム動作、DAO 実行結果について README の記述を今回の実測値へ置き換えていない。
- SQL 接続・クエリー・DDL/DML・DSN 作成・ドライバー導入・サーバー設定変更・実データ変更は０回。既存 accdb、仕様、コード、ZIP、過去報告は変更していない。本書だけを新規保存した。
- 過去の ACE 業務・FK・競合・フォーム試験の合格は、共有 SQL Server の結合合格として流用していない。AS400/RPG の調査・移植は対象外。

## 現行 Access の実装根拠

下記のパスは全て `test-project1/srcs/Access/` からの相対パス。行番号は今回読んだファイルの１始まり。

| 根拠 | 版・行 | 現行内容・移行への影響 |
| --- | --- | --- |
| spec/規約/Access.md | 8.1、17–24、39 | ID は Counter/VBA Long、正の32bitで上限2,147,483,647。日付は TEXT(10)、時点は VBA Date の UTC。StudentManagement.accdb に業務表・役割表を内包し、保存先は CurrentProject.FullName に限定する。 |
| spec/共通/方式別/Access/01_共通実装仕様.md | 8.1、40、57、75–87、111 | `StudentBackendPath=SELF`、`GetUserNameW` と内包 t_app_role。検索と全書込みが同一 t_write_guard を取得し、同一 DAO Workspace で処理する。 |
| spec/DB定義/Access/01_DB定義書.md | 8.2、14、18、35–47、56、60–62 | ID/版は LONG、制約は ACE 用物理型・ValidationRule・Relation。５業務表89列、技術 guard と評価用 role。続柄は両 NULL 可・片 NULL 不可。 |
| Build-Access.ps1 | 130–158 | SingleFile は StudentBackendPath を SELF に設定し、staging ACE 表を TransferDatabase で物理インポートする。DAO Relation と内包 t_app_role を作り、初期利用者役割を投入する。ODBC リンクや SQL Server 接続を生成しない。 |
| Classes/clsUnitOfWork.cls | 15–26 | `CreateWorkspace(...,dbUseJet)`、`OpenDatabase(backend)`、Workspace.BeginTrans、ACE SQL `lock_bit=Not lock_bit`、CommitTrans。SELF は現 accdb のパスへ置換する。 |
| Classes/clsStudentRepository.cls | 10–14、22–30、44–50、82–120、124–142 | ACE の `PARAMETERS ... LONG/TEXT` で QueryDef を作る。AddNew/Edit/Update による学生・監査の直接 DML、Long ID/版、版＋１。新規/更新 dynaset に dbSeeChanges は指定していない。 |
| Modules/modSecurity.bas | 10–15、21–44、64–72 | GetUserNameW の名前をローカル t_app_role へ照合し Reader/Staff/Admin を決める。SELF 以外の旧分離構成は roles.conf を読む。SQL Server のログイン/DB役割を判定する経路はない。 |
| Modules/modClock.bas | 17–24 | GetSystemTime から秒単位の VBA Date UTC を作り、＋９時間で業務日を求める。共有 SQL Server の時刻を取得しない。 |
| Classes/clsConfirmation.cls | 18–25 | 確認は VBA オブジェクト内に、主体・ローカル権限 stamp・入力 fingerprint・全候補 fingerprint・10分期限を保持し再照合する。現行ローカル方式は全候補変更を含むが、サーバー側確認契約はまだ実装していない。 |
| README.md | 3、7、9、21–33 | 配布は１accdb・４フォーム・初期５分類70コード・学生/クラス/監査０と記述。過去実機は Office64/Access 16.0.20430.20146、DAO16.0.20430.20032。今回再ビルド・実行はしていない。 |

## 接続方式の両立性

| 方式 | 技術的可能性 | 現実装に対して必要な対応 |
| --- | --- | --- |
| DAO＋ODBC リンク表 | Access が正式に対応。１accdb にリンク定義を持ち、Windows 認証で外部 SQL Server 表を読む構成は可能。 | 現物理表の置換、TableDef.Connect/SourceTableName、キーと型の対応、権限と全方式の共通ゲートが必要。ACE QueryDef SQL と pass-through T-SQL は別物。リリンクのみで業務保証が成立したとしない。 |
| ADO＋SQL Server 保存手続 | 非連結フォームからパラメーター付き Command を呼ぶ構成が可能。現４フォームの明示保存と合わせやすい。 | 保存処理を単一 ADODB.Connection 上へ集約し、サーバーの主体再認可・原入力検証・共通ゲート・確認・監査入口を利用するアダプターを方式内に実装する。DAO と ADO の別接続に業務 Tx を分割しない。 |
| ODBCDirect Workspace（dbUseODBC） | 現行 Access の直接外部接続への置換案には採用しない。 | Microsoft の DAO 文書は Access 2013 で ODBCDirect Workspace をサポートせず、ACE を経由しない外部接続には ADO を使用すると明記する。現 dbUseJet を定数だけ変える対処は不可。 |

DAO/ADO の選択と保存手続利用の説明は [Microsoft Support の接続説明](https://support.microsoft.com/en-us/access/connect-access-to-sql-server)、ODBCDirect の制約は [DBEngine.CreateWorkspace](https://learn.microsoft.com/en-us/office/client-developer/access/desktop-database-reference/dbengine-createworkspace-method-dao) に基づく。ここでの ADO 優先は、非連結フォームと共有サーバー側保存境界に合わせるための設計提案であり、公式が本業務システムの完成構成を保証したとの主張ではない。

## 共有化で確定が必要な構造契約

本表は「新しい共有構成に向けた未確定契約／現実装との不適合」を示す。旧 ACE 構成が壊れているとの判定ではない。今回は調査だけを行い、下記を推測補完する仕様修正・アプリ生成・実 DB 変更は開始しない。

| 問題ID | 分類・正確な根拠 | 影響・再開条件 |
| --- | --- | --- |
| SHARED-ACCESS-001 | 構成契約の改訂が必要。規約8.1:39 の「同じファイルへ内包し、外部リンク表・外部設定ファイルを必要としない」と、最新指示の共有 SQL Server バックエンドは配備責務が異なる。共通8.1:40、Build:130–158 も SELF 物理表構成。 | 単一 frontend accdb＋共有 SQL DB へ配置仕様・接続設定・ビルド資源を一緒に改訂する。最新指示が旧配置制約に優先することを改訂理由へ記録し、学生/クラス等のローカル複製を正本として二重運用しない。これは利用者による構成変更。 |
| SHARED-ACCESS-002 | 共通排他・保存境界が未確定。共通8.1:75–87 の local guard と clsUnitOfWork:15–26 は、別方式が別ゲートで共有 DB を更新すると協調しない。Repository:87/99/136 は直接 DML。 | 全学生書込み・論理削除・マスタ保守・整合した検索が同じサーバーのゲートを守る契約と、呼出元 Tx／手続内 Tx の所有者を確定する。guard 表ロックでもアプリロックでも選択できるが、全方式で同一資源・ロック期間を合わせる。監査と学生/マスタ変更を１サーバー Tx で原子的に扱い、直接 DML 権限を許すか EXEC-only にするか明記する。 |
| SHARED-ACCESS-003 | 認証・認可の正本が未確定。modSecurity:21–44 はローカル役割を信頼し、:64–72 の権限変更 stamp も同じローカル評価主体。 | Windows 認証の実 DB 接続主体、ドメインを含む主体の一意表現、Reader/Staff/Admin と DB 役割の対応、毎回のサーバー認可、監査 executed_by、確認後の権限剥奪時の拒否を決める。ローカル t_app_role や利用者が渡す役割を共有 DB の権限根拠にしない。ローカル画面の表示制御は補助として残せる。 |
| SHARED-ACCESS-004 | 型・保存表現の契約が未確定。DB8.2:14/60–62、規約8.1:17–24、Repository:82–120 は32bit Long ID/数値版、ISO TEXT(10)、YESNO、Date UTC。 | 共有 DDL の ID/版の範囲、bit、date、UTC時点、GUID、Unicode、NULL と型付きパラメーターを対照表で確定する。bigint採用なら2,147,483,648以上も正確に往復するアダプターが必要。サーバー上限を Access に合わせて独断で縮小しない。既存 row_version は手動加算数値版であり、SQL Server の rowversion 型へ名前だけで置換しない。 |
| SHARED-ACCESS-005 | 確認・正規化・時計・エラー契約が未確定。clsConfirmation:18–25 と modClock:17–24 は VBA の主体 stamp／時計／fingerprint を使用する。共有 DB を直接他方式も変更する場合の確定サーバー API は今回の調査入力にない。 | 原入力とサーバー側正規化、全候補集合の順序/版/hash、確認トークンの保存場所/消費/期限/権限変更、０候補への集合変更、期待版、業務日、定員、監査、戻り状態/エラーコード/項目名を定義する。候補一覧の利用者向け返却は学籍番号・氏名・和暦生年月日・クラス等の必要項目に限定する。API/API版・DDL hash を各方式内仕様へ独立して記載する。 |

共有 SQL Server DDL が int と ISO text 等を選ぶ場合、型変更量は減る。bigint/date/datetimeoffset を採用する場合、現 Long/String/Date を無変換で共用できない。この調査では未提示の共有 DDL の型を断定していない。

Access は SQL Server bigint を Large Number としてリンク／インポートできるが、明示設定と対応バージョンが必要であり、設定が既存 VBA の `As Long`、`CLng`、`PARAMETERS ... LONG` を自動的に変更するわけではない。ID の文字列／Decimal／64bit Office LongLong 等の採用は正確なパラメーター往復検証を伴うものとし、Double 経由で大きい整数を変換しない。[Microsoft: Large Number](https://support.microsoft.com/en-us/access/using-the-large-number-data-type)

SQL Server の rowversion は自動生成される8バイトの版スタンプで、業務で明示的に＋１する現在の数値 row_version と意味が異なる。必要なら別列として設計し、期待版・監査 before/after の型まで明記する。[Microsoft: rowversion](https://learn.microsoft.com/en-us/sql/t-sql/data-types/rowversion-transact-sql?view=sql-server-ver17)

DAO リンク表を選ぶ場合、SQL Server IDENTITY 表の dynaset に Microsoft が必要としている dbSeeChanges を追加し、busy cursor、更新後再取得、型変換、取消を実機検証する。現 Repository:87/99/136 に指定がないことは、ローカル Counter を扱う現 ACE 構成のバグではない。[Microsoft: Database.OpenRecordset](https://learn.microsoft.com/en-us/office/client-developer/access/desktop-database-reference/database-openrecordset-method-dao)

DAO BeginTrans は Workspace 範囲に作用し、外部レコードセットの Transactions 対応確認が必要で、ACE 経由 ODBC の Tx はネストできない。ローカル guard や別 ADO 接続の処理まで同一 SQL Server Tx とみなさず、選んだ構成で取消・監査原子性を再検証する。[Microsoft: Workspace.BeginTrans](https://learn.microsoft.com/en-us/office/client-developer/access/desktop-database-reference/workspace-begintrans-method-dao)

## 実装候補と配備条件

推奨候補は、４つの非連結フォームと方式内 VBA を１accdb に残し、業務読取りと保存を ADO の単一接続＋固定された型付きサーバー入口へ移す構成。共有 DB の契約が DAO direct-write を認める場合は DAO リンク案も選べるが、共通 gate と DB 権限境界の検証は省略しない。方式固有の資料・ソース・生成器・配備資源は Access 内へ持ち、他方式のソースを import／参照してアダプターを作らない。共有 DB への実行時接続は今回の利用者指示で許可された共有と区別する。

Windows 認証では利用者パスワードを accdb/設定へ保存しない。DAO/ODBC の設計例は `Driver={ODBC Driver 18 for SQL Server};Server=<承認済みサーバー>;Database=<共有DB>;Trusted_Connection=Yes;Encrypt=Yes;TrustServerCertificate=No;`。これは未実行の接続契約例で、接続先・証明書名を決めるものではない。ODBC 18 の Encrypt=Yes＋TrustServerCertificate=No は暗号化とサーバー証明書検査を行う。loopback 接続でも対象名・信頼・許可を実接続で確認する。[Microsoft: ODBC 接続属性](https://learn.microsoft.com/en-us/sql/connect/odbc/dsn-connection-string-attribute?view=sql-server-ver17)

ADO を選ぶ場合は Microsoft OLE DB Driver を別の前提として記録し、ODBC Driver の導入だけで MSOLEDBSQL19 の導入済みとは扱わない。最新の OLE DB 文書は MSOLEDBSQL19 を現行として示し、ADO 文書は Provider と DataTypeCompatibility=80 の対応を説明する。ADO の暗号化・証明書キーワードは選択 API に合う公式定義で固定し、ODBC文字列をそのまま ADO に渡さない。[Microsoft: OLE DB Driver](https://learn.microsoft.com/en-us/sql/connect/oledb/oledb-driver-for-sql-server?view=sql-server-ver17)、[Microsoft: ADO 対応](https://learn.microsoft.com/en-us/sql/connect/oledb/applications/using-ado-with-oledb-driver-for-sql-server?view=sql-server-ver17)

これらのドライバー／証明書／Office bitness／SQL Server 稼働確認は配備上の未実施であり、それだけを仕様の構造問題に分類しない。確定応答喪失は自動再送せず、未知状態として調査できる相関IDと手順を契約化する。

共有 DB の初期５分類70コードは配備管理者が１度だけ投入し、各 frontend のビルドは接続契約と初期内容を検証する。各方式のビルドが共有 DB を再作成したり独自に seed を上書きしたりしない。現在の staging ACE 物理表インポートは新 frontend ビルドへ持ち込まない。学生・クラス・監査０の配備初期状態と、CRUD／競合用の専用 fixture を別にする。既存 local accdb に実データがある場合の移行は別途承認された移行手順を作り、本調査から移行実行を開始しない。

## 再開条件と必要試験

1. 共有 DB の名前・エンドポイント・DDL/API版/hash・所有者・初期seed・Windows主体/DB役割・型/Unicode/NULL/日付/UTC表現・ゲート・Tx所有者・確認/監査/エラー契約を仕様担当が確定し、Access/spec の構成と関連詳細/DB/規約へ独立して反映する。共有契約のコピーは許可された配置へ置き、他方式への参照依存を残さない。
2. 新規実行IDで Access 入力版/hash/構造を固定し、１accdb frontend の接続アダプター、ビルドと配備手順を生成する。既存 main accdb と過去証拠は保持し、新しい成果名でビルドする。
3. 承認された SQL Server 専用 fixture で、Windows 認証/TLS、閲覧者・担当者・管理者、接続主体の監査、正規化の同一結果、ID/版境界、NULL/続柄FK、date/UTC往復、CRUD/マスタ保守、取消/監査失敗、期待版競合、確認集合の変更（全候補消滅も含む）・期限・権限剥奪を新しく試験する。
4. 異なる方式と Access が同時に同じ DB の最終１席／同一学生／マスタへ書く競合、全件検索件数・一覧の一致、10,000/10,001件、切断・commit応答喪失を検証する。ローカル ACE の２プロセス合格を流用しない。
5. Access64bitで再コンパイル・実フォーム・単一frontend配布・ZIP単独ビルドを再検証し、Office32bitを対象にする場合は別処理系でも確認する。テスト fixture と配備初期DBを区別し、新しい test-report に生ログ・終了値・入力hash・未実施範囲を保存する。

本調査の到達点は「Access から共有 SQL Server を使う製品機能は可能、現行実装の無改訂接続は不適合、共有契約確定後に生成再開」。接続／実DB／アプリ結合は未実施。共有化の仕様改訂やコード修正は本書で行っていない。

## 今回の入力ハッシュ

Access/spec の Markdown 41件。版分布 `{"8.0": 31, "8.1": 9, "8.2": 1}`。並べた `spec相対パス|SHA256\n` を UTF-8 で連結した集合 SHA-256：`7DC13F49FA1C1DBD37727F8F9FFEE0F9E5E1CBA6AD17A194E54A42573E7D1584`。これは今回の入力識別用で、構造検査や結合の合格証明ではない。

| 当方式内パス | SHA-256 |
| --- | --- |
| StudentManagement.accdb | `838F5FE63826FCE58FACE6C5102D363AF41C3EF433D6B2D7229C8D5DE0C93DE5` |
| README.md | `0EFFE485F0EBE9928F92ED5540E1EB61150B9659D206596008B5B355F55CE06E` |
| Build-Access.ps1 | `4FE1329ECF2092E50672BB6B1465387C9FFF4B471CFD00D84E6CE4CB7939769B` |
| spec/規約/Access.md | `B9F25FA562B9316FCB53B47D0BBE417F343793ABF47EE1FDA3AF9D0EE45D7563` |
| spec/共通/方式別/Access/01_共通実装仕様.md | `2DD8247CDD0DD41E43354CDC43D585CA281D6E3DF487B8A1361D7ADE136681D3` |
| spec/DB定義/Access/01_DB定義書.md | `F8D90E6DA1D526D066910DC7A669FBFE47A5788996121CC16CC98373A4F231C0` |
| database/schema.sql | `4DB63CD7D111024F1C6FFD2E7ABD4AE0E16F08AEB1A69447B0098D4D865EB885` |
| database/schema.json | `498325FE235FE5CDF623EBE1DE1D8940462033BA9ACB1F41B1796B8D297D9EB4` |
| Classes/clsUnitOfWork.cls | `EA5E1742EAA893CEAE8BAA4F943A25C8A77AC61E7012BFD3AC58986BF1BCF5C2` |
| Classes/clsStudentRepository.cls | `C1936F62D25C86A9BEF53D6D9C2EB3271B9679318DF839578993A88034792DB9` |
| Classes/clsConfirmation.cls | `046BCC5DFC1E1C5AF88D86F40AD18AE457E2C83FF0F9BC187F8751ECC4D5BD46` |
| Modules/modSecurity.bas | `52C4311BD5BEE6C45127956B16894AE89905B8E976741D4334FD93EE17E93574` |
| Modules/modClock.bas | `4AEC7DB30934E9FE81FD2C9B287970D93CF4253BCE78C8B9DBE732DFCA05778C` |

StudentManagement.accdb の調査前後 SHA-256 は同じ `838F5FE63826FCE58FACE6C5102D363AF41C3EF433D6B2D7229C8D5DE0C93DE5`。本書の保存時点で原本を変更していない。
