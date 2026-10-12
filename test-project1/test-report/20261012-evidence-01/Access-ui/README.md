# Access 新規画面撮影用テストデータ

実行ID `20261012-evidence-01-ui`、2026-10-12、project `test-project1`、AG-BUILD7.5。**新規SingleFile ACCDBの作成・VBAコンパイル・production処理での架空データ登録・実DAO読返しが成功した。** GUIはまだ表示しておらず、rootへ撮影を引き継ぐ。過去の試験PASSを転記していない。

## 実行範囲

Build-Access.ps1に明示Frontend/Backend、CreateBackend/SingleFile/Compile/IncludeTests/NoStartupを渡した。COMのVisibleはfalse。テスト専用modEvidenceUiSeedだけを新規ファイルへAddFromStringし、再コンパイルした。テスト用TestDraftを利用するが、学籍番号・氏名/カナ・生年月日・住所・電話・メールなどを架空検証値へ置換した。

| 今回の結果 | 実測 |
| --- | --- |
| production MaintainClass | 1件Saved。class_id=1、TEST-UI、架空撮影A組、定員30 |
| production clsStudentService.SaveStudent | 3件Saved。student_id=1..3、row_version=1 |
| DAO学生/クラス | 3件/1件 |
| DAO CREATE監査 | 4件。m_class1件、m_student3件、before_version NULL、after_version1 |
| 独立DB | StudentBackendPath=SELF、外部リンク0 |
| 任意続柄4項目 | 3学生ともNULL。DAO JSONの再照合も保存 |
| 画面/共有SQL | 未表示/未接続 |
| 終了 | Access.CloseCurrentDatabase/Quit、MSACCESSプロセス0を確認 |

Access COM Version16.0で実行した。新PowerShell helperのPS5.1.26100.9549 ParseFileもerror0。PS5の検査はParseのみでseedを再実行していない。

## 保護した原本と入力版

既存 `srcs/Access/StudentManagement.accdb` は一度も開いていない。作成前後SHA-256は両方 `838F5FE63826FCE58FACE6C5102D363AF41C3EF433D6B2D7229C8D5DE0C93DE5`。原本spec/runtime/Build-Access.ps1/業務DDLを変更していない。

`results.json` に方式内spec45ファイル（版8.0/8.1/8.2）、Modules/Classes/database/Build-Access.ps1の入力hashを保存し、終了時の一致を確認した。他方式コード・DB・仕様への参照を追加していない。

## 新規fixtureとrootの入口

新規ファイル:

`D:\開発\contextbase-evaluation\test-project1\srcs\Access\build\20261012-evidence-01-ui\20261012-build-04-access-single-evidence-01-ui.accdb`

COMを閉じた時点のfixture SHA-256は `0A6A65D90A67DD070BA1F9F6E798DED879AADD2694936043E470E8C171031DAB`。以後のGUI起動でAccessの内部メタデータが変わり得るため、撮影後のhashは撮影担当が別に記録する。`initial-staging.accdb` は生成材料であり、この完成fixtureに外部リンクはない。

rootの撮影はこの新規fixtureだけを開き、frmStudentSearchを通常表示する。NoStartupなので自動起動フォームは設定していない。検索は在学/休学で2行、卒業を追加して3行。新規登録/一覧の学生を開く通常操作を使用できる。直接frmStudentEditを開くときのOpenArgsは新規 `|evidence`、編集 `1|evidence`。登録画面下部のスクロール位置も実画面として記録する。

架空データはTEST-ACE-001..003、仮名太郎/花子/次郎（空白込み氏名5字で上限8字以内）、架空試験町1、電話0000000000、fixture1..3@example.invalid。在籍区分は01/02/03。今回業務日は2026-10-12。`synthetic-data.json` と方式内tests/Evidence/ui-data.jsonに実DAO読返しを保存した。

## 証拠と未実施

- `create.log`: Build-Access生成・コンパイル記録
- `seed.raw.log`: MaintainClass/SaveStudentの今回Saved結果
- `results.json`: 全入力hash、DAO学生/クラス/監査、原本hash、独立性、状態
- `synthetic-data.json`: 架空データのDAO読返し
- `dao-json-postcheck.json`: 続柄4項目NULLなどの記録ファイル再照合
- `ps5-parser.raw.json`: 新helperのPS5構文検査
- 上位フォルダー `access-ui-launch.log`: 作成・seed実行の生出力

この実行は新規ACE/DAO fixture内の登録・読返しであり、共有SQL結合試験ではない。共有SQL接続/配備/移行、非管理Windows主体、office32bit、GUI目視・操作・スクリーンショットは **NOT_RUN**。既存production ACCDBの再検査や改変としても扱わない。
