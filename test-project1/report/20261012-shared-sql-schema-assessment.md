# 共有SQL Server DBの現行スキーマ・導入契約評価

2026-10-12／projectId=test-project1／工程=build・読取り比較。対象DB予定名：`contextbase_test_project1`。ユーザーの最新指示によりDBの共有は許可されたが、方式ごとの仕様・コードの独立は維持する。

## 結果と停止範囲

WPF、VB.NET WinForms、ASP.NET MVC、Vue API、COBOLの**基礎7表と初期データは共用可能**。5方式の`001_schema.sql`はコメント・空行を除いた実行内容が完全一致し、`002_seed.sql`はファイル単位で完全一致した。テーブル形状・列型・NULL・照合・キー・外部キー・CHECK・既定値・5分類70コードについて、相互矛盾は検出しなかった。

ただし、**現在の5方式の導入・権限・SQLCLR検証を無変更で一つのDBに重ねることはできない**。下記SHARED-SQL-ROLE-001とSHARED-SQL-ENTRY-002は、従来の専用DB配置を共有DBに変更した際に生じる導入契約の構造衝突である。共有時の権限主体・入口・正規化資源を確定するまで、対象導入SQLの実行と共有構成の推測生成を停止する。基礎スキーマの業務ルールを独断で変更しない。親AgentのSQL Serverインストールと空DB作成は、この比較では共有アプリケーション導入の合格扱いにしない。

基礎schemaと構造衝突の評価は読み取り比較で行った。発見したWeb検証の局所バグは追加許可を受け、MVC/Vueの004検証SQL各1値だけ修正し、非接続の新規試験記録を保存した。SQL接続・SQL実行・DB作成・アプリ起動・昇格・仕様変更・本体DDL変更・実行時コード変更は0件。`spec-eval`は読んでいない。Access／AS400_RPGのSQL Server利用可否は別担当の評価であり、本報告の合格範囲に含まない。

## 比較入力とハッシュ

次の相対パスはすべて`test-project1/srcs/`起点。各ファイルは現行方式配下の独立コピーを読み取った。

| 方式 | ファイル | SHA256 | byte |
| --- | --- | --- | ---: |
| CSharp_WPF | database/001_schema.sql | e6872d042fed6e1d795fde72e29adef5cecda6a0887348444ea905661de1178a | 17532 |
| VB.NET_WinForms | database/001_schema.sql | 3b02732aa725894df03c16bb2ee79bbb9e280c0d1fee3dc332967f26f8d07a6c | 17532 |
| CSharp_ASPNET | database/001_schema.sql | e6872d042fed6e1d795fde72e29adef5cecda6a0887348444ea905661de1178a | 17532 |
| Vue_CSharpAPI | database/001_schema.sql | e6872d042fed6e1d795fde72e29adef5cecda6a0887348444ea905661de1178a | 17532 |
| COBOL | database/001_schema.sql | 0fb8e5f3686243fbf9a26e5da10c75a7ab93ca86c70ddc169e9c91cc0a98c2cf | 17524 |
| 全5方式 | database/002_seed.sql（各方式の5ファイル） | b4b6745e5c6e7d1ed3a22b07b2bb4607b5a6bf173ad08ba5bf32f0e4bb2322ee | 5085 |

DDL比較の正規化は、行頭空白を除いて`--`で始まる行と空行を除外し、残りを各行Trim後LFで連結、末尾LFを付けずUTF-8化したもの。SQL本文の大文字小文字・値・式は変更しない。5方式すべて213行、SHA256=`7c546dcc1ab8ba75eda29c81bf4ab2a90fc0f7a229e470f73e3eb6650e90db25`。原ファイル比較ではWPF/MVC/Vueがbyte同一、VBの差は先頭コメント、COBOLの差は先頭・L217コメントと末尾改行だけだった。コメント差を版の実行適合の根拠には使わない。

各DDLのCREATE TABLEは同じ行番号にあり、物理列数は以下の通り。

| 表 | CREATE行 | 物理列数 |
| --- | ---: | ---: |
| dbo.m_student | 7 | 35 |
| dbo.m_class | 62 | 17 |
| dbo.m_code_category | 90 | 11 |
| dbo.m_code | 112 | 14 |
| dbo.t_operation_log | 137 | 12 |
| dbo.t_confirmation | 156 | 9 |
| dbo.t_runtime_state | 171 | 8 |
| 合計 | — | 106 |

各DDLのL189–195は同じ7外部キー、L213–215は同じ3ロール。学生L30–31の続柄分類・値はともにNULL可で、L199の`ck_student_contact`が緊急4保存列の全NULL／全非NULLを検査する。過去の続柄partial-NULL問題は、現在の5SQL Server DDLの比較では再発していない。

seedのL9–13は5分類、L15–84は70コード（GENDER=4、ENROLLMENT_STATUS=4、PREFECTURE=47、RELATIONSHIP=8、GRADE=7）。クラス・学生のサンプルINSERTは含まない。L85–87で既存初期値の差異を拒否するため、共有時に方式間で異なる初期値を上書きする処理は不要である。

## SHARED-SQL-ROLE-001：同じロールにNativeのDML禁止とWeb/CGIのDML許可

種別：共有配置の構造衝突／書込み導入のブロッカー。基礎001/002のテーブル衝突ではない。

根拠A：`CSharp_WPF/database/native/010_student_api.sql` L178–180は`student_api.prepare_save`／`persist_student`等へのEXECUTEを許可する一方、L181–185は`m_student`、`m_class`、`m_code`、`m_code_category`、`t_operation_log`の直接INSERT/UPDATE/DELETEを`student_staff,student_admin,student_viewer`へDENYする。`VB.NET_WinForms/database/native/010_student_api.sql`の同じ行にも同じDENYがある。

根拠B：`CSharp_ASPNET/database/003_web_permissions.sql`と`Vue_CSharpAPI/database/003_web_permissions.sql`の各L12–13は`ALTER ROLE student_viewer ADD MEMBER student_staff`、`ALTER ROLE student_staff ADD MEMBER student_admin`。各L14–15はstaffへ学生INSERT/UPDATE・履歴INSERT、L18–19はadminへクラス・コードINSERT/UPDATEをGRANTする。`COBOL/database/windows-auth/003_permissions.sql`のL10・13も同じ包含関係、L11–12・14–15も同じDML許可である。

トリガと影響：共用DBで両境界の導入SQLを実行し、Web/CGIのDB利用者をそのstaff/adminロールに所属させる。Nativeがviewerへ与えた直接DMLのDENYが、Web/CGIで追加したロール包含を通じstaff/adminに継承される。staffへの後置GRANTだけではviewerのDENYを打ち消さない。Web/CGIの学生保存・監査・マスタ保守は、アプリ側検査に成功してもDBの直接DMLで拒否される。逆にNative利用者を直接DMLが許可される同じロール構成へ変更して回避すると、NativeのDB入口限定境界を維持できない。sysadmin接続で動いたことはこの衝突の解消・認可適合の証明にならない。

判定の技術根拠：[Microsoft Learn: Determine effective Database Engine permissions](https://learn.microsoft.com/en-us/sql/relational-databases/security/authentication-access/determining-effective-database-engine-permissions?view=sql-server-ver17)。本報告は実DB試験ではなく、現行ロール包含と権限評価規則からの静的判断。

再開条件：共有DB上のNativeクライアント主体とWeb/CGIサービス主体のロール割当・直接DML可否を確定し、方式内の導入/検証がその境界を同時に満たす設計へ修正されること。ロール名変更、統一DB入口、サービス用権限の分離のいずれを採用するかは本Agentが推測して実装しない。少なくとも非sysadmin・非dboの実利用主体で、Native直接DML拒否、許可されたWeb/CGI業務更新、閲覧者業務更新拒否を検証できることが必要。

## SHARED-SQL-ENTRY-002：WPF/VBの同名SQLCLR入口と異なる厳密binary要求

種別：共有配置の資源・検証契約の構造衝突／両Native導入のブロッカー。

根拠A：`CSharp_WPF/database/native/000_sqlclr.sql` L10と`VB.NET_WinForms/database/native/000_sqlclr.sql` L10は、ともに`CREATE ASSEMBLY StudentNativeNormalization FROM 0x... WITH PERMISSION_SET=SAFE`。両方L12・15・18・21で同名の`student_api.normalize_raw/reason/class/code`をCREATEする。前者L5–6のbinary SHA512は`A5889EAA82A078761A59AD48F79472437671FB8AFAECFA2706948AC9DD95915A727F0717500CF01BA0DB4CF5F4EC32C5B5609F4F5D49D739616AE1D73E6D5468`、後者は`80CB01ECF43DADE7644B55FE9583C74ED9F3B369997846401BC1E148A48CC9B780A62D356ECEF8E4B12167494F6BEACB34D868BAF10BE50250810ADED806F433`で異なる。

根拠B：`CSharp_WPF/database/Install-ProjectDatabase2025.ps1` L170、`VB.NET_WinForms/database/Install-ProjectDatabase2025.ps1` L169は、同じDB assembly名のbinary SHA512が各方式の`$assemblyHash`と一致することを必須とし、不一致を51138で拒否する。

トリガと影響：同じDBで両000を順に適用すると、二つ目は同名assembly/functionの再CREATEとなる。一方だけ適用しても、もう一方の現行binary厳密検証条件を同時には満たせない。binary差が業務処理の差であるとは判断していない。同一機能でも、独立ビルド資源の異なるbyteを同じDB資源名の唯一の現物として同時に要求することが衝突である。

再開条件：共有DBへ配置するNative正規化入口とbinaryの所有/版/実体を確定し、両方式の呼出・導入・厳密検証条件がその構成に一致すること。あるいは方式ごとの入口名・assembly名を分離し、それぞれのローカル依存を維持すること。どちらの構成も現在の業務規則を未知の値で補完する必要はないが、ここでは選択・変更・SQLCLR登録を行わない。

## SHARED-SQL-DEPLOY-003：従来の専用DB名・単一Project markerは共有配置に未対応

種別：ユーザーの新しい共有指示に対応する設定/導入上の未改訂。未知の業務仕様の欠落ではなく、共有schemaの形状を否定する根拠にしない。

根拠A：MVC/Vueの`database/Deploy-Database.ps1`各L16–17は`contextbase_test_project1_mvc`／`contextbase_test_project1_vue`と別々の`test-project1/<方式>`marker。L108で同じ単一DB拡張property`Contextbase.Project`を書き、L118–123で方式専用marker・原ファイルschema/seed/permission SHAを必須照合する。各003 L5も専用DB名を要求する。

根拠B：WPF/VBの`database/Install-ProjectDatabase2025.ps1` L19／L18は`contextbase_test_project1_wpf`／`contextbase_test_project1_vb`。COBOLの`database/windows-auth/Common.ps1` L4と`003_permissions.sql` L3は`contextbase_test_project1_cobol`。予定共有DB名は最新指示による`contextbase_test_project1`。WPFの導入器には親AgentがすでにL16で共有指示を理由とする実行停止ガードを置いている。

影響：旧導入器をそのまま使うと共有DBに導入せず別DBへ向かうか、DB名・marker/hash条件で拒否する。同じCREATE TABLE/ROLEを5回適用することもできない。raw schema SHAのコメント差を、共有DBの実スキーマ不一致と誤判定してはならない。

再開条件：共有DB導入の担当・適用一回の基礎DDL/seed・共有DB名・方式ごとの配置記録・検証の意味を更新すること。生成コード/仕様の独立を維持したまま、同じDBの使用を各方式の設定に明示すること。既存DBの無断DROPや型/制約の回避を行わない。

## LOCAL-VERIFY-004：Web導入検証の学生物理列数が33になっている

種別：導入検証スクリプトの確定局所バグ（追加許可により修正済み）。仕様の業務定義欠落や5方式のDDL衝突ではない。

根拠A：修正前の`CSharp_ASPNET/database/004_verify_deployment.sql` L8と`Vue_CSharpAPI/database/004_verify_deployment.sql` L8はともに`INSERT @tables VALUES (N'm_student',33)`、各L16は`sys.columns`の実列数がこの期待数と違えば検証を拒否する。現在のL8は許可を受け35へ修正した。

根拠B：各方式の`database/001_schema.sql` L8–42には35列が定義されている。`name_key`／`kana_key`を含めた実物理列数であり、業務入力数ではない。DDLのCREATE TABLEブロックを抽出し、列名行を数え直した結果は学生35、クラス17、分類11、コード14、履歴12、確認9、実行状態8、合計106。最初の集計で学生33・全104とした値は誤りであり、本報告と親Agent通知で訂正した。

トリガと影響：正しい001を新規DBに適用して004を実行しても、学生列数の比較だけで誤って不適合になる。この問題は専用DBでも再現する論理不備であり、共有DB化に伴う権限衝突とは別である。過去のR1/R2は未接続のParse/Plan検査で、004の実SQL判定を実機合格とはしていない。

対応：親Agentから「両ファイルのみ修正」と追加許可を受け、学生期待値だけ35へ修正。`test-project1/test-report/20261012-web-deployment-column-validation-r3-final.{json,md,raw.log}`へ現行入力hashと全7表のDDL由来列数照合を保存し20/20 PASS。学生期待33への戻し、name_key列欠落、表名変更の負例も検出。逆変換SHAが修正前SHAと一致するため、004のその他byte不変更も確認した。001/002のSHAは不変。旧R1/R2・初回R3の証拠を保持し、試験装置のWindows PowerShell UTF-8 BOM解決前のparser失敗も`r3-preflight-01.raw.log`へ保存した。その他の期待列数は現行DDLと一致する。この局所バグの対応条件は満たしたが、共有role/CLRの構造衝突による導入停止は継続する。

| 004ファイルの方式 | 修正前SHA256 | 修正後SHA256 |
| --- | --- | --- |
| CSharp_ASPNET | 80d9a7c01f809f749acaade923c507878cc74b03595e88a09adab6a4d21ec4a4 | b6d20d90bdad0e300d9f56260a4676c54efb7aeef01931d59646addfae017e75 |
| Vue_CSharpAPI | 95074bc573d27408cde841fd45a725d16b139f45acad7472b44e0ba98729cb3e | 2b9d1bcfae6eba2ed2579495dfaa6c3dd7eb552972a33c4848b6edc647b4fff0 |

## 共有時に維持できる契約と未実施

001 L5の`ALLOW_SNAPSHOT_ISOLATION ON`、各方式の保存ゲート`test-project1:student-write`（seed L5、MVC/Vue Core/SqlServerStudentService.cs L97、WPF native/010 L52・161、COBOL bridge/student_bridge.c L73）が同じであり、共有DBの読取り整合性と同時保存制御の基礎契約は一致する。ただし実サーバーでの同時実行・失敗時取消は未試験である。

共有構成では学生ID・学籍番号の一意性・定員・参照・監査は同じ行集合に作用する。各方式を別データ集合として試験する従来fixtureや初期空データ前提の試験を、そのまま共有実DBへ実行してはならない。今回は試験fixtureを適用していない。

未実施：Express17.xへのDDL/seed適用、SQLCLRホスト設定と信頼登録、共有権限の実効検証、5方式接続・読取り/更新/削除・同時実行、Access/RPG変換。過去の独立host/static試験合格をこれらの共有DB試験へ流用しない。

追加根拠ファイルのSHA256（本評価時点）：

| 独立方式内ファイル | SHA256 |
| --- | --- |
| CSharp_WPF/database/native/010_student_api.sql | efaaf2654effc629cbbf50bc36db66d7f0a63148536c4cb7a6d6fe3bee1d810d |
| VB.NET_WinForms/database/native/010_student_api.sql | 6b5d0c625b5edd5b6cb3f55d78224a643d184037f3fd5ef6dbe6636c90347356 |
| CSharp_WPF/database/native/000_sqlclr.sql | eca914b5d589b7a57fd095b44b2d30cb4209f58e3abad92febbc02312df6101f |
| VB.NET_WinForms/database/native/000_sqlclr.sql | 6dbb9a16e4222472b1efa60c5d9d5126bedb692d089d10767a6b289b1f2a63d8 |
| CSharp_ASPNET/database/003_web_permissions.sql | 782df16a150e377da3d087264f6ba649d7c587f97af058530340a0eff89fc0b7 |
| Vue_CSharpAPI/database/003_web_permissions.sql | 8cf6357e2ebb945189fa168aae85e224747f25340a2313699c03c9eaa4184dd2 |
| COBOL/database/windows-auth/003_permissions.sql | fed4d743746fda564611f5aa2f0d6540ac1d61e89a59315be648af2189c67e6b |

本報告は既存レポートを上書きせず新規作成した。問題の根拠と再開条件を親Agentへ送信し、共有導入の未確定部分の作成/実行を停止する。
