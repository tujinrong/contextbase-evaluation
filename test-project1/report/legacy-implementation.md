# Legacy 実装事前検査・中断報告

projectId: `test-project1`／工程: `build`／作成日: 2026-10-12／状態: **構造適合問題を報告して中断**。

ユーザーの「仕様書構造的な問題があれば、test-project1\report で報告書、中断」に従い、Access の正当な未入力ケースを標準の参照整合付き複合外部キーで保存できないことを実機で再現した時点で実装を停止した。親 Agent も全方式の生成を中断した。制約を独断で無効化せず、構造仕様を変更していない。生成済みソース・試験用 ACCDB は途中成果であり、完成・合格・配備可能とは扱わない。

## S-ACE-001: 続柄の部分 NULL と参照整合付き複合 FK の未解決な適合問題

分類: **構造適合問題／実装中断理由**。通常の ACE/DAO 外部キー構成では、正当な業務入力と指定された DB 制約を同時に満たせない。単一の数値・表記誤りとして修正する問題ではない。

| 根拠ファイル | 入力版・行 | 原文の要点 |
| --- | --- | --- |
| `spec/共通/09_項目制約定義.md` | 7.0、66–68行、REG-020～022 | 緊急氏名・続柄・電話は「いずれか入力時は全3項目必須」。全3項目の未入力は「NULL相当」 |
| `spec/DB定義/Access/テーブル/01_m_student.md` | 7.2、46行、No.23 | `relationship_category` は NOT NULL。「続柄の値が空でも分類情報を保持。固定値RELATIONSHIP」 |
| 同上 | 7.2、47行、No.24 | `relationship_code` は NULL可。「FK:(relationship_category,relationship_code)→m_code(category_id,code_value)」 |
| `spec/DB定義/Access/01_DB定義書.md` | 7.2、38行、C-006 | 「分類列＋値列→m_code、RESTRICT。続柄値NULL可」 |
| 同上 | 7.2、73行、製品別外部キー | 「DAO.Relationで…学生4組の分類＋値…を参照整合付きで定義」 |

緊急連絡先なしの学生は、`relationship_category='RELATIONSHIP'`、`relationship_code=NULL` となる。他の必須情報と本人電話を正しく指定しても、標準 ACE 複合 FK はこの部分 NULL の組を参照先と照合して拒否した。学生保存は `SystemError/E-COM-004` に分類され、DAO エラー番号は **3201** だった。

本報告は「Access のすべての構成・製品版で絶対に実現不能」と断定しない。`Index.IgnoreNulls`、`Index.Required`、外国キー用索引の作成順序などの代替設定を網羅していない。別 Agent が現仕様を満たす構成を設計・実機再検証するか、業務 NULL 契約・固定分類列・FK 制約の仕様を整合させる判断が必要である。

## 実行環境と保存した証拠

| 項目 | 実測値 |
| --- | --- |
| Office / MSACCESS.EXE | FileVersion / ProductVersion `16.0.20430.20146` |
| DAO/ACE COM | `DAO.DBEngine.120` |
| ACEDAO.DLL | FileVersion / ProductVersion `16.0.20430.20032`、Office16 の `ProgramFilesCommonX64` 配下 |
| 形式 | ACCDB、Access 2007以降形式、ACE ローカル試験バックエンド |
| 最終再現 frontend | `srcs/Access/build/StudentFrontend-23.accdb` |
| 最終再現 backend | `srcs/Access/build/StudentBackend-23.accdb` |
| backend SHA-256 | `926EC5ED41EFF36770024EF7690C683F79CA44EA68A82DB4AABA69F6E4A41AAC` |
| 証拠ファイル | `report/legacy-evidence.json`、`report/legacy-fixtures.json` |

試験は番号付きの専用 fixture に対して実施した。**配備用初期 backend は最終生成していない**。fixture の `roles.conf` は、試験プロセスの OS 身元だけを Admin とする試験用設定であり、正式配備の認証設定ではない。

最終 backend を読み取り確認した件数は、コード分類5、コード70、クラス1、学生0、操作履歴1、ガード1、追加の空の `z_dao_fk_probe` 0件。クラス1件と履歴1件はセルフテストのクラス保守が確定した試験データであり、初期投入データではない。学生 CREATE の失敗後に学生・学生監査は確定していない。37個の ACCDB は生成試行・失敗・再現 fixture として保存し、いずれも正式アプリ成果の合格証跡には用いない。

## 実際のエラー出力

最終セルフテストの返値:

```text
FAILED after 11 checks: -2147221314 create student returned SystemError E-COM-004 error=3201 テーブル 'm_code' にリレーションシップが設定されたレコードが必要なので、レコードの追加や変更を行うことはできません。
```

学生サービスとは別の最小表で同じ条件を試した出力:

```text
ACE partly-null composite foreign key rejected: テーブル 'm_code' にリレーションシップが設定されたレコードが必要なので、レコードの追加や変更を行うことはできません。
DAO.Relation rejects partly-null key: テーブル 'm_code' にリレーションシップが設定されたレコードが必要なので、レコードの追加や変更を行うことはできません。
```

FK 用の既存 `m_code` には初期続柄値が存在する。学生サービスを通さず、以下の最小 DDL/INSERT でも拒否を再現した。SQL 試験の `z_fk_probe` は試験後に除去した。

```sql
CREATE TABLE z_fk_probe (cat TEXT(48) NOT NULL, val TEXT(20));
ALTER TABLE z_fk_probe ADD CONSTRAINT fk_probe
  FOREIGN KEY (cat,val) REFERENCES m_code(category_id,code_value);
INSERT INTO z_fk_probe(cat,val) VALUES('RELATIONSHIP',NULL);
```

SQL 外部キー生成だけの問題を区別するため、別の2列表で、仕様が指定した DAO.Relation の通常構成でも検査した。

```powershell
# db は試験 backend を開いた DAO.Database。m_code は初期70値を持つ。
$db.Execute('CREATE TABLE z_dao_fk_probe (cat TEXT(48) NOT NULL, val TEXT(20))',128)
$relation = $db.CreateRelation('dao_fk_probe','m_code','z_dao_fk_probe',0)
$field = $relation.CreateField('category_id')
$field.ForeignName = 'cat'
$relation.Fields.Append($field)
$field = $relation.CreateField('code_value')
$field.ForeignName = 'val'
$relation.Fields.Append($field)
$db.Relations.Append($relation)
$db.Execute("INSERT INTO z_dao_fk_probe(cat,val) VALUES('RELATIONSHIP',NULL)",128)
```

この DAO 試験も同じ FK エラーを返した。その後の既存 `IGNORE NULL` 索引を前置する探索は、削除済み Relation オブジェクトの再 Append が「オブジェクトが正しくないか、現在設定されていません」で失敗したため、**代替設定の解決可否を示す証拠として採用しない**。残った空の `z_dao_fk_probe` と索引は試験用 backend の一部であり、正式スキーマではない。

[Microsoft の Relation object 文書](https://learn.microsoft.com/en-us/office/client-developer/access/desktop-database-reference/relation-object-dao)は参照整合と外国キー用索引の自動生成を説明する。[Index.IgnoreNulls 文書](https://learn.microsoft.com/en-us/office/client-developer/access/desktop-database-reference/index-ignorenulls-property-dao)は NULL の索引エントリを扱うが、それだけで本件の複合 FK を満たす構成は確認できていない。

## 実施した検査と中断地点

現行仕様から生成したデータ構造は、ACE/Db2 とも業務5表89列＋技術ガード1表2列、合計6表91列。初期データは5分類70値。Db2 の DDL/seed は生成・仕様対照のみで、Db2 実行は未実施。

Access の frontend/backend 生成、12標準モジュール・6クラスのインポート、4非連結フォームの保存は実施した。COM 追加モジュールに既定 `Option Compare Database` が残る問題、型別 DAO プロパティ設定、2個目の `CreateForm` の `RPC_E_SERVERFAULT` は実装側で修正・回避し、4フォームの生成まで到達した。`acCmdCompileAndSaveAllModules` (126) は戻り、実 VBA 入口から下記11検査を通過した。ただし、コマンド126の戻りだけを全機能の適合証明とは扱わない。

1. 補助平面文字の Unicode スカラー数。
2. 全角英数字の NFKC。
3. ひらがな→カタカナと空白正規化。
4. 電話番号のハイフン除去。
5. Gregorian うるう日。
6. 昭和の最終日。
7. 平成元年の初日。
8. 令和元年の初日。
9. 試験 backend が学生0件であること。
10. 管理者のクラス保守が監査とともに確定すること。
11. 学籍番号の正規化。

次の「緊急連絡先なし学生の新規保存」で DAO3201 となり中断。予定していた学生再表示・NoChange・更新・旧版・別人確認・定員・一覧の個人情報最小化・論理削除・監査件数の検査は**未実施／未達**。DAO 実行を通していない通常更新・削除・検索全件・10001件上限・複数職員による最終席競合・監査障害・確定応答喪失・Reader/Staff 権限往復・フォーム操作の視覚検査を合格と記載しない。

## 途中成果と仕様対応

| ソース・資源 | 実装範囲 | 状態 |
| --- | --- | --- |
| `srcs/Access/Modules/modUnicode.bas` | UTF-16のスカラー数、NFKC、名称キー、カナ、電話・郵便、制御文字/原入力長 | 該当する初期検査は実行。全境界は未実施 |
| `modJapaneseDate.bas` / `modClock.bas` | 厳密ISO、元号境界、UTC・日本業務日、GUID | 上記日付例は実行。全DATE-Tは未実施 |
| `modSecurity.bas` | OS身元＋管理者配置roles、Reader/Staff/Admin、認証状態印 | 試験Admin入口のみ実行。ACE直接編集を強い権限境界と扱わない |
| `modStudentRules.bas` | 19保存入力、19→21照合値、形式・日付・緊急一式・接触先・席 | 正規化の一部を実行。CREATEは阻害され未達 |
| `clsUnitOfWork.cls` / `clsStudentRepository.cls` | 専用Workspace、共有ガード、パラメーターQueryDef、Recordset書込/採番、監査 | クラス経路で実行。学生保存は3201で失敗 |
| `clsStudentService.cls` / `clsStudentDraft.cls` | 保存/削除、最新版・一意・マスタ・状態・定員、NoChange、全重複集合、監査一括 | ソース作成。学生の成功往復は未達 |
| `clsConfirmation.cls` | 身元/認証印/フォーム/対象版/全正規化値/全候補ID版、10分、単回消費 | ソース作成。集合0への変更も再確認対象。実往復未実施 |
| `clsSearchContext.cls` / `modStudentSearch.bas` | 条件分離、30分、全照合後10001判定、全件ソート、20/50/100ページ、不要個人項目をDTOへ渡さない | ソース作成。実検索は中断により未実施 |
| `modCandidates.bas` / `modStudentForms.bas` | クラス補助条件連動、既存停止値、一覧コールバック、二重操作抑止、保存後旧条件再検索、未保存変更 | ソース作成。操作試験・画面検査は未実施 |
| `modConfirmationForms.bas` | 最大20件・必要4項目の候補確認、既定取消、独立削除理由 | ソース作成。対話往復は未実施 |
| `modMasterMaintenance.bas` | クラス/コード管理入口、保護・参照学年・定員/停止、版、同値無変更、監査 | 新規クラスのみ実行。初期値の再投入入口・保守全枝は未完 |
| `modMessages.bas` | 現行共通05から58文言、種別分類 | ソース生成。項目別パラメーター全追跡は未完 |
| `modSelfTests.bas` | fresh fixture限定の実DAO往復入口 | 11検査通過後、CREATEで中断 |
| `Build-Access.ps1` | DDL・DAOプロパティ・seed・リンク・VBA・非連結4フォームの生成 | 番号付きfixture生成成功。正式最終buildは中断 |
| `database/schema.sql / schema.json / seed.json` | ACE6表と5分類70値 | fixtureに生成。NULL複合FK適合は未解決 |
| `srcs/AS400_RPG/database/schema.sql / seed.sql / schema.json / seed.json` | Db2 for i6表と5分類70値 | 生成のみ。実Db2/Journaling/SQLRPGLE試験は未実施 |
| `srcs/_tools/generate_legacy_schema.py` | 方式別物理MDと現行共通10から再生成 | 実行済み。spec-evalは入力にしていない |

主な入力は各方式の詳細2機能、方式別共通実装7.0、開発規約7.0、共通01～11、Access/Db2物理テーブル7.2。検索仕様の局所修正により Access/COBOL/AS400_RPG の検索分冊は7.3。入力・出力の最終一覧とハッシュ固定は親 Agent の中断報告・manifestを正本とする。

## 中断前に修正した局所バグ

許可された3方式の検索分冊だけで、内部 `ClassCode` の旧上限10→9、`ClassName` の旧上限50→18、Access補足の `StudentNoPrefix` 20→15を確定済み正本へ合わせ、文書版を7.3へ更新した。共通05/10などの修正は親 Agent が担当した。DBの構造問題は修正していない。

## 再開条件

別 Agent が、全緊急項目NULL・固定続柄分類・参照整合付き分類＋値FKの関係について、ACEで正当入力を保存でき、非NULLの不正コードを拒否し、参照中のコード削除を拒否する設計を確定する。代替索引設定が現行契約を満たすなら、その再現可能な DAO 設定と実機証跡を仕様に補う。契約変更が必要なら、該当共通・Access物理定義・方式別共通・詳細の版と記述を整合させる。

その修正版入力を固定してから、新しい空の fixture と配備初期backendを区別して再生成し、停止地点から先を含む業務往復・FK不正入力・競合・監査取消・確認集合変更・権限・画面を検査する。今回の11通過や過去レポートを新改訂の合格へ流用しない。
