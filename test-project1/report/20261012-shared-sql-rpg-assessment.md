# AS400_RPG の共有 SQL Server 接続評価

評価 ID: `20261012-shared-sql-rpg-assessment`。記録日: 2026-10-12。対象: `test-project1`、工程: 共有 DB への構成変更の事前調査。入力は方式内の現行仕様と実ソース、および IBM/Microsoft の一次公式資料。`spec-eval` は読んでいない。

ユーザーの最新指示「SQLSERVER DBを共有します。できればAS400,AccessもこのDBを使用します」を優先する。DB の独立制約は変更されたが、方式ごとのコード・仕様・ビルドの独立は維持する。この報告は RPG の調査だけであり、Access の可否を判定しない。

現状判定は **条件付きで接続経路があるが、現 RPG プログラムを設定変更だけで SQL Server へ切り替えることはできない**。接続アダプター、認証主体、共有 DB の型、保存入口、トランザクションと排他の仕様変更が必要。IBM i 実機・接続情報・ドメイン/Kerberos 情報が未提供のため、実行可能性と Windows 認証の成立は未検証。Db2 用の既存ソース・仕様・DDLは変更していない。

## 現仕様と実装の根拠

主要な方式仕様は版 8.0。以下の行は本調査で読んだファイルの行番号であり、調査入力の SHA-256 は末尾に記録する。

| ファイル・行 | 現行記載または実装 | 共有 SQL Server への影響 |
| --- | --- | --- |
| `srcs/AS400_RPG/spec/DB定義/Db2_for_i/01_DB定義書.md:58`、版8.0 | 「DBスキーマSTUDAPP」「FOR SYSTEM NAMEを明示」 | SQL Server の DB/schema と Db2 のライブラリー/システム名は同じ契約ではない。接続先だけを変えて同一の DDL を投入できない。 |
| 同 `:60`、版8.0 | `BIGINT GENERATED ALWAYS AS IDENTITY`、`TIMESTAMP(6)`、`VARGRAPHIC(2*N) CCSID 1200` | SQL Server 用の ID、Unicode 領域、UTC時点、論理版・真偽値の対応を定義する必要がある。 |
| `srcs/AS400_RPG/spec/共通/方式別/AS400_RPG/01_共通実装仕様.md:44`、版8.0 | 「検索の件数・一覧と全書込みが同じ行を更新」する `STUDAPP.T_WRITE_GUARD` | RPG だけのゲートでは、同じ DB に書く他方式との定員・重複・候補版の競合を防げない。全更新入口が同じサーバ排他契約に参加する必要がある。 |
| 同 `:57-61`、版8.0 | `IDENTITY_VAL_LOCAL`、`GET DIAGNOSTICS`、成功COMMIT/検索ROLLBACK、全DML対象のジャーナル、`COMMIT(*CS)` | SQL Server の接続上の Tx、生成ID取得、行数、例外/競合、確定不明、ロック解放へ明示的に対応する必要がある。IBM i ローカルの ROLLBACK が別 JDBC 接続の Tx を終了したと扱えない。 |
| 同 `:69-71`、版8.0 | 確認DSはジョブ・利用者・画面識別別、認証は「IBM iの実行ユーザープロファイルと承認済み認可設定」 | SQL 側の Windows 主体との対応、監査主体、確認トークンの発行/保管/照合責務を定義する必要がある。 |
| `srcs/AS400_RPG/spec/規約/AS400_RPG.md:29-31`、版8.0 | `CRTSQLRPGI`、ジャーナル開始、Db2 の `SQLSTATE`/`SQLCOD` | Db2 の異常判定を SQL Server/JDBC のエラーと同一視できない。期限・競合・権限拒否・未知結果のマッピングが必要。 |
| `srcs/AS400_RPG/src/STUCOMMON.sqlrpgle:29-40` | `VALUES SESSION_USER` と `QSYS2.GROUP_PROFILE_ENTRIES`、`STUADMIN/STUSTAFF/STUVIEW` | SQL Server にはこの IBM i 認可照会がない。実行ユーザーの文字列を渡すだけで Windows DB 認証が成立したことにはならない。 |
| 同 `:91-102` | `QSYS2.OBJECT_STATISTICS` の6ファイルのジャーナル確認と `STUDAPP.T_WRITE_GUARD` 確認 | 現起動検査はローカル Db2 前提。共有 SQL Server の接続・schema・API版・必要権限・TLS確認へ置換する仕様が必要。 |
| `srcs/AS400_RPG/src/STUSVC.sqlrpgle:5,82,597,1211-1218` | 埋込SQL設定、ゲートUPDATE、`IDENTITY_VAL_LOCAL`、埋込COMMIT/ROLLBACK | 現処理は SQL Server の JDBC/ODBC 接続を保持しておらず、その接続上の保存・監査確定を実行できない。 |
| `srcs/AS400_RPG/database/schema.sql:3-9,149-154` | `CREATE SCHEMA STUDAPP`、`SET CURRENT SCHEMA`、`FOR SYSTEM NAME`、CCSID、`t_write_guard` | Db2 専用DDL。現在の SQL Server に適用する手順ではない。 |
| `srcs/AS400_RPG/cl/BUILD.clle`、`cl/SECURITY.clle`、`cl/START.clle` | IBM i SQLプリコンパイル、STUOWNER所有者採用、IBM iオブジェクト権限、ジョブ共通コミットメント | SQL Server の個別 Windows LOGIN/USER/role、接続資格、ネットワーク、SSL trust store の配備契約は生成されていない。 |

`src/`、`copy/`、`cl/`、C補助を読取り検索した範囲で、SQL Server 用 `CONNECT`/RDBディレクトリー設定、JDBC/ODBC/FreeTDS クライアント、HTTP DBアダプターは実装されていない。Unicode C補助が存在することは DB接続補助の存在を意味しない。

## 公式資料が示す接続候補

IBM は IBM i から SQL Server データへ到達する方式として DRDA を介するサービス、InfoSphere Federation Server、Java Type 4 JDBC、PASE の FreeTDS を紹介している。紹介は第三者製品の提供者サポートを前提とし、本題材のソースがそのまま適合するという保証ではない。[IBM: Accessing Data on Microsoft SQL Server From IBM i](https://www.ibm.com/support/pages/accessing-data-microsoft-sql-server-ibm-i)（Modified: 2026-01-26、閲覧: 2026-10-12）。

| 候補 | 技術上の位置づけ | 本題材で必要な条件と留保 |
| --- | --- | --- |
| RPG → 方式内 Java補助 → Microsoft Type 4 JDBC → 共有SQL | IBMの紹介する直接接続候補。JavaKerberos を選べる。 | RPGの画面・入力構造を維持し、Java補助の呼出契約、型/Unicode変換、接続/Tx所有、API入出力を新たに定義する。現在のSQLRPGLE埋込SQLを自動的にJDBCへ転送するものではない。JDK/JAR/IBM i/PTF の実機採用版は未確定。 |
| SQLRPGLE → DRDA → Microsoft Service for DRDA → SQL | SQLパッケージ、SQL構文/型、認証の変換を担う外部サービス。 | 接続先は SQL Server のTDSポートへ単にRDB登録する構成ではなく、別DRDAサービスが必要。Host Integration Server の配備・利用条件、Windows主体マッピング、SQL2025対応、Unicode/SQL/Tx変換を評価する。サービスは本環境に提供されていない。 |
| SQLRPGLE → Federation/独自ARD → SQL | 別製品または独自 Application Requester Driver を挟む方式。 | 追加基盤・ドライバー・バインド/SQL変換と全Tx契約が必要。無料Expressを導入しただけでこの基盤が揃うという判定はできない。 |
| RPG → PASE補助 → FreeTDS → SQL | IBM資料は利用できる可能性を紹介している。 | IBM i/PASE向けのビルド、Unicode、TLS、Windows/Kerberos認証の組合せを別途確認する。Microsoft ODBC DriverのWindows/Linux/macOS用バイナリーをIBM i用として使用できるとは判断しない。現在採用・配備・試験されていない。 |

DRDA Service の公式資料は、Db2パッケージから SQL Server 手続を生成し、SQL/型等を変換すること、ESSO資格マッピングとWindows SSPIを組み合わせる認証を説明している。これは追加の構成要素であり、現行RPGの認証を自動的に引き継ぐ設定ではない。[Microsoft: Service for DRDA (Operations)](https://learn.microsoft.com/en-us/host-integration-server/core/service-for-drda-operations)。IBMのARD定義も独自プログラムを用意する契約である。[IBM: ADDRDBDIRE, ARDPGM](https://www.ibm.com/docs/en/i/7.4.0?topic=ssw_ibm_i_74%2Fcl%2Faddrdbdire.html)。

JDBCはJVMを備えるOS上で動く設計だが、Microsoftの公式OS実検査一覧にIBM iは列挙されていない。IBM JVM向けKerberos設定の説明は存在するので、候補から除外する根拠にはならない一方、採用IBM i上の合格証拠にもならない。[Microsoft: JDBC system requirements](https://learn.microsoft.com/en-us/sql/connect/jdbc/system-requirements-for-the-jdbc-driver?view=sql-server-ver17)、[Microsoft: JDBC Kerberos integrated authentication](https://learn.microsoft.com/en-us/sql/connect/jdbc/using-kerberos-integrated-authentication-to-connect-to-sql-server?view=sql-server-ver17)。

## Windows 認証と接続環境

Windows認証を維持する候補は `integratedSecurity=true;authenticationScheme=JavaKerberos` の JDBC である。MicrosoftはIBM JVMの `useDefaultCcache` を明記し、realm/KDC、TGT、SQLサービスのSPNを必要条件として説明している。SQL接続を IBM iの実行プロファイルや画面文字列だけで Windows ログインとして認証する機能ではない。[Microsoft: JDBC Kerberos integrated authentication](https://learn.microsoft.com/en-us/sql/connect/jdbc/using-kerberos-integrated-authentication-to-connect-to-sql-server?view=sql-server-ver17)。

本環境で提供されているのは管理配備に用いる Windows ローカル主体 `DELL_DISKTOP1\tujin` であり、IBM iから利用するAD/Kerberos realm、KDC、ドメイン主体、TGT/keytab、SQL SPN、ユーザー委譲設定は提供されていない。従って **現在の Windows ローカルSSPIトークンで IBM i の直接統合認証が成立するとは判定できない**。JDBCのJavaKerberosを選ぶなら、その認証基盤と実際の接続主体を先に確定する。SQL認証への自動変更や資格情報のソース埋込みは行わない。

Microsoft ODBCの非Windows統合認証例もKerberosを前提とし、Linux/macOSでKerberos失敗時のNTLM代替を行わないことを説明している。この資料はIBM i/PASE上のFreeTDSまたは別ドライバーが同じ認証を実装済みだとする根拠には使用しない。[Microsoft: ODBC integrated authentication](https://learn.microsoft.com/en-us/sql/connect/odbc/linux-mac/using-integrated-authentication?view=sql-server-ver17)。

現ローカル導入wrapper `agents/build-agent/scripts/Setup-LocalSqlExpressAndDatabases.ps1:10,20` は `tcp:localhost,1433` と loopback/localhost のTLS証明書を指定している。IBM i上のlocalhostはIBM i自身なので、この設定はリモート接続先にならない。リモート用の到達可能なDNS名/固定ポート、承認済みネットワーク範囲、証明書の名前と信頼チェーン、IBM i側JVMのtrust storeが必要。共有DBのリモート公開は今回実行していない。JDBCでは暗号化と証明書検証を有効にし、証明書名不一致を `trustServerCertificate=true` で回避する設計にはしない。[Microsoft: Connecting with encryption](https://learn.microsoft.com/en-us/sql/connect/jdbc/connecting-with-ssl-encryption?view=sql-server-ver17)。

Windows側にRPG専用の中継サービスを置いて統合認証する別案も設計上はあり得る。ただし、それはIBM i利用者の認証、個人別認可/監査と中継資格を新たに設計する案である。他方式のアプリ/ライブラリーを共有しないという制約を維持し、単一の管理者DB資格へ利用者をまとめて既存の個別主体要件を満たしたと扱わない。本調査では実装案として採用していない。

## 構造変更の範囲と再開条件

判定 ID `AS400-SHARED-SQL-001` は、ユーザーの明示した新構成に必要な**方式設計変更**である。版8.0のDb2構成が内部的に破綻しているという旧仕様バグの判定ではない。処理系未導入だけを構造問題にして全方式を中断する扱いにもしていない。共有SQL向けRPG生成は、以下の契約が仕様に確定するまで着手しない。原仕様の誤字を一意に直す局所修正で補完できる範囲を超える。

1. 共有DB名、schema、物理型・固定制約・版・UTC・Unicode・照合キーの正本と、既存DBを保存する移行/初期化手順を定義する。方式のローカルspec内に必要な契約を展開し、他方式specをRPG実装の参照入力にしない。
2. JDBC/DRDA/ARD/PASE/中継のどの経路を採用するかを決める。RPGの関数と補助ABI、19入力と日付/理由原文、戻り値、候補/検索ページ、nullable/Int64/Unicode変換、エラーを定義する。DDS5250 UIを他方式のUIで置換しない。
3. IBM i利用者と実際のSQL接続Windows主体の対応、資格の発行/期限、個人別認可、DB role、監査主体、非sysadmin・非dbo・非db_ownerでの直接DML制限を定義する。ローカルグループ名をSQL role判定にそのまま流用しない。
4. 学生/マスタ/監査を同じSQL接続Txで確定する境界、既知失敗のRollbackと確定不明、キャンセル/タイムアウト/ジョブ終了、確認待ちTx終了と再確定の照合責務を定義する。IBM iコミットメントと別接続のTxを同一視しない。
5. すべての共有DB更新入口が守る同じ排他/容量/候補再検査契約を定義する。現RPGのguard行とSQL Server側の別applockが独立に存在する構成では、全方式の保存競合を保証できない。
6. 共有DBに配備する手続/正規化実装/SQLCLRアセンブリーの正本と版/hashを一つに確定する。現WPF/VBの独立DDLは同じ `StudentNativeNormalization` 名/`student_api` 名を使うので、共有DBへ方式別DDLを順番に再投入する手順にはできない。クライアントコードの独立とサーバAPI契約の共通化は別に扱う。
7. IBM i実機の版/PTF/JDK、承認接続先、TLS信頼材料、個人別主体の実接続情報を受け、読取、CRUD認可拒否、Unicode/和暦、競合、候補変更、監査失敗、確定不明を新しい入力hashで実試験する。

共有SQLへ到達するだけを目的とする評価なら、IBM i/JDKとKerberos環境が確認できた場合のType4 JDBC補助を最初の候補とするのが本調査の提案である。これは資料からの設計判断であり、ドライバー採用・Windows認証成功・IBM iコンパイル成功の実績ではない。環境が揃わない場合は現Db2版を保存したままRPGの共有SQL対応を未実装として報告する。

## 今回の検査状態

| 検査 | 状態 |
| --- | --- |
| 方式内spec/SQLRPGLE/COPY/CL/DDLの読取り照合 | REVIEWED（上記根拠範囲） |
| IBM/Microsoft公式接続/認証/TLS資料 | REVIEWED（2026-10-12閲覧） |
| RPG → SQL Serverのアダプター実装 | NOT_IMPLEMENTED |
| IBM i / SQLRPGLE / DDS / CL / JDBC補助の実機ビルド | NOT_RUN（実機・処理系なし） |
| IBM iから共有DBへの到達、TLS、Windows認証 | NOT_RUN（接続情報なし） |
| SQL実行・DB作成/更新・サーバ設定・昇格 | NOT_RUN（今回実行なし） |
| Viewer/Staff/Admin認可・CRUD・同時実行・COMMIT失敗 | NOT_RUN |
| 既存C補助の今回再コンパイル・再試験 | NOT_RUN（今回の調査範囲外） |

過去のC補助試験や静的参照閉鎖の合格を、共有SQL対応の合格として流用していない。今回の変更出力はこの新規報告書のみ。

## 調査入力 SHA-256

以下は本報告作成時の読取り入力を記録したものであり、構造検査全体のロックや実機試験結果を意味しない。

| 入力 | 仕様版 | SHA-256 |
| --- | --- | --- |
| `test-project1/srcs/AS400_RPG/spec/規約/AS400_RPG.md` | 8.0 | `C97425E605FF93BEE6929FF61B4B3DFCFCD44B1A392D6220F33621E28D7E3E85` |
| `test-project1/srcs/AS400_RPG/spec/共通/方式別/AS400_RPG/01_共通実装仕様.md` | 8.0 | `82F934714DA160AD3A90D85385ECDD9E0BB3D1EB6D223DC752899D598F029ABF` |
| `test-project1/srcs/AS400_RPG/spec/DB定義/Db2_for_i/01_DB定義書.md` | 8.0 | `150343DDD619B9358E46487104D68C3E4C0CB299F71E0A889D4D8CA567C80517` |
| `test-project1/srcs/AS400_RPG/src/STUCOMMON.sqlrpgle` | - | `A33786FF76582ACF987F66E72DCEBAF5D6556E877CFD1275E232FD19FAF68994` |
| `test-project1/srcs/AS400_RPG/src/STUSVC.sqlrpgle` | - | `80359FCAD97491C3E7B0CB981506E3541BE57F6DCCF9B034EE5495D756AE098E` |
| `test-project1/srcs/AS400_RPG/copy/STUINSERT.rpgleinc` | - | `5F7A3F3F0072C348DB2D064EB9841ED974DBC231D3C71074510D85A180D696F2` |
| `test-project1/srcs/AS400_RPG/cl/BUILD.clle` | - | `A81B7524CC9B5B507B1EBAE3F633D3D6A8D0725D2CDA22DD376CABFE1DB3A767` |
| `test-project1/srcs/AS400_RPG/cl/SECURITY.clle` | - | `3932321CC7732B8EFFAE8D779C7FE37EAF3EFEC1F1869EC20DB732A8996E6120` |
| `test-project1/srcs/AS400_RPG/cl/START.clle` | - | `D972AE4FBFD6E2F325B69BE1D769144FED6F4B413A07BB20D794B4DF38152991` |
| `test-project1/srcs/AS400_RPG/database/schema.sql` | - | `EFBE37AE01E1A119BCC7B35965310D6400FA82D64A5AC4DA1333AC64FD7D651A` |
| `test-project1/srcs/AS400_RPG/tools/generate_database.py` | - | `9CDD252361D9BC67E194A22612F3B2CBB91624B4A1551FF9515EC6F767BF1092` |
| `test-project1/srcs/AS400_RPG/README.md` | - | `022CD518691CA892FDD0335A465F21D64EE79E75615521DD8507E7E58A6E25CE` |
| `test-project1/srcs/AS400_RPG/docs/deployment.md` | - | `ED5B8ECBE19D211F1EC57EEFEDD4665BBB518A2C4955BD43B6D2E0B0F5681F4C` |
| `agents/build-agent/scripts/Setup-LocalSqlExpressAndDatabases.ps1` | - | `2B3E101F210FE0487364B5611634B879B0020D182E17CF07D698C9E676EF1692` |
| `test-project1/srcs/CSharp_WPF/database/native/000_sqlclr.sql` | - | `ECA914B5D589B7A57FD095B44B2D30CB4209F58E3ABAD92FEBBC02312DF6101F` |
| `test-project1/srcs/CSharp_WPF/database/native/010_student_api.sql` | - | `EFAAF2654EFFC629CBBF50BC36DB66D7F0A63148536C4CB7A6D6FE3BEE1D810D` |
| `test-project1/srcs/VB.NET_WinForms/database/native/000_sqlclr.sql` | - | `6DBB9A16E4222472B1EFA60C5D9D5126BEDB692D089D10767A6B289B1F2A63D8` |
