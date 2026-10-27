# discovery-agent 分類結果レビュー

**ホスト採用済み・人手レビュー待ち。**

| 項目 | 結果 |
| --- | --- |
| 対象 | test\-project1 / CSharp\_ASPNET |
| 処理 | discoveryのみ。後続層と人手受入れの完了ではない |
| 採用した要求 | catalog |
| 分類ポリシー | contextbase\-catalog/1 |
| 事実索引ポリシー | contextbase\-source\-facts/1 |
| 正式成果 SHA-256 | `0334b43f85a4ca2383f8e636cff903fe34f21616582093745e9cab82ad43e659` |
| snapshot SHA-256 | `29dc9ab9b9317d33661eb3aaf4e6de1686f8833faeac1c37856ce2819653e20f` |
| 索引 SHA-256 | `330d4bb3d1b3ece48b4d9b738ed4dda2526b03883739556552e5888772150c4d` |
| 原文 | 75 files |
| 全記録 | 63 |

[正式成果](contextbase.json) / [独立検証](result/validation.json) / [ソース事実レビュー](facts/facts-review.md)

## 集計範囲

選択したソースから概要、業務機能、テーブル／データ、共通処理を整理し、関係と動作を原文根拠付きで確認する。仕様書は生成しない。

| 分類 | 件数 |
| --- | ---: |
| システム概要 | 2 |
| 主機能 | 6 |
| 子操作 | 8 |
| 共通能力 | 14 |
| データ対象 | 10 |
| 技術入口 | 14 |
| 運用・開発支援 | 7 |
| 資料 | 1 |
| 外部依存 | 1 |
| 分類保留 | 0 |

## システム概要

### 機能分類と集計

- ID: `SYSTEM\-0c61963351cba1c2`
- 担当要求: catalog

contextbase\-catalog/1による主機能は6件：学生管理2件、マスタ管理2件、認証2件。別枠は操作8件、共通責任14件、技術入口14件、物理表7件、DTO等のデータ群3件、支援7件、依存資源群1件、説明資料群1件、概要・集計2件。分類保留候補は0件。メニューは共通ナビゲーション、配備・検査は支援とした。relationshipsとbehaviorは本割当では未検証のまま残る。

- 原文根拠: [Web/Controllers/AccountController.cs:10\-41](../../srcs/CSharp_ASPNET/Web/Controllers/AccountController.cs#L10)<br>[Web/Controllers/StudentsController.cs:5\-43](../../srcs/CSharp_ASPNET/Web/Controllers/StudentsController.cs#L5)<br>[maintenance/Program.cs:4\-17](../../srcs/CSharp_ASPNET/maintenance/Program.cs#L4)<br>[Views/Menu/Index.cshtml:1\-7](../../srcs/CSharp_ASPNET/Views/Menu/Index.cshtml#L1)

### 学生管理システムのソース構成

- ID: `SYSTEM\-ea2e0e568d6f735a`
- 担当要求: catalog

.NET 10のASP.NET Core MVC/Razor Web、SQL Server向けCore、管理者マスタ保守CLIで構成される。WebはIStudentServiceにSqlServerStudentServiceを登録する。配備・生成・検査資源も取得範囲に含む。構文Factは意味束縛・実行を証明せず、非C\#資源は原文読解による。本解析で入力の実行・ビルド・試験は行っていない。

- 原文根拠: [Program.cs:1\-9](../../srcs/CSharp_ASPNET/Program.cs#L1)<br>[Infrastructure/WebHostSetup.cs:13\-34](../../srcs/CSharp_ASPNET/Infrastructure/WebHostSetup.cs#L13)<br>[StudentManagement.Web.csproj:1\-7](../../srcs/CSharp_ASPNET/StudentManagement.Web.csproj#L1)<br>[StudentManagement.slnx:1\-8](../../srcs/CSharp_ASPNET/StudentManagement.slnx#L1)<br>[Core/StudentManagement.Core.csproj:1\-12](../../srcs/CSharp_ASPNET/Core/StudentManagement.Core.csproj#L1)<br>[maintenance/Program.cs:4\-17](../../srcs/CSharp_ASPNET/maintenance/Program.cs#L4)<br>[maintenance/StudentMaintenance.csproj:1\-4](../../srcs/CSharp_ASPNET/maintenance/StudentMaintenance.csproj#L1)


## 主機能

### クラスマスタ保守

- ID: `FUNCTION\-91d28046181a5fb5`
- 担当要求: catalog

DB管理者がCLIのclass選択とJSON入力によりクラスを登録・変更し、保守結果を受け取る。

- 主体: student\_adminに属するDB接続主体
- 別案・反例: コード保守と単一のマスタ保守機能にまとめることもできるが、入力対象と整合性責任が異なるため分離した。
- 機能領域: マスタ管理
- 業務対象: クラスマスタ
- 技術入口: StudentMaintenance CLI (`ENTRY-aa841ff3444b5ee5`)
- 完了成果: クラス保存または変更なし等の結果をJSON・終了コードで得る。
- 利用目的: 年度・学年・期間・定員等を持つクラスを整備する。
- 分類理由: 画面はないが、運用者が独立して入力し、クラス保存という業務結果を得る完全なCLI作業。
- 集計範囲: selected\-system
- 開始契機: 管理者がclassと入力JSONを指定して保守CLIを起動する。
- 原文根拠: [maintenance/Program.cs:4\-17](../../srcs/CSharp_ASPNET/maintenance/Program.cs#L4)<br>[Core/MasterMaintenanceService.cs:17\-78](../../srcs/CSharp_ASPNET/Core/MasterMaintenanceService.cs#L17)<br>[maintenance/StudentMaintenance.csproj:1\-4](../../srcs/CSharp_ASPNET/maintenance/StudentMaintenance.csproj#L1)

### 業務コードマスタ保守

- ID: `FUNCTION\-22591896d39dca6b`
- 担当要求: catalog

DB管理者がCLIのcode選択とJSON入力により業務コードを登録・変更し、保守結果を受け取る。

- 主体: student\_adminに属するDB接続主体
- 別案・反例: クラス保守と共通CLI単位で統合する分け方もあるが、CLIの共用は業務対象の同一性を意味しない。
- 機能領域: マスタ管理
- 業務対象: 分類別業務コード
- 技術入口: StudentMaintenance CLI (`ENTRY-aa841ff3444b5ee5`)
- 完了成果: コード保存または変更なし等の結果をJSON・終了コードで得る。
- 利用目的: コード名称・表示順・有効性・利用期間を整備する。
- 分類理由: 分類別コードの維持という独立目的、専用入力契約、保存結果が確認できる。
- 集計範囲: selected\-system
- 開始契機: 管理者がcodeと入力JSONを指定して保守CLIを起動する。
- 原文根拠: [maintenance/Program.cs:4\-17](../../srcs/CSharp_ASPNET/maintenance/Program.cs#L4)<br>[Core/MasterMaintenanceService.cs:17\-29](../../srcs/CSharp_ASPNET/Core/MasterMaintenanceService.cs#L17)<br>[Core/MasterMaintenanceService.cs:79\-122](../../srcs/CSharp_ASPNET/Core/MasterMaintenanceService.cs#L79)

### ログイン

- ID: `FUNCTION\-3a8a1be5f76f61aa`
- 担当要求: catalog

明示的に有効化されたローカル認証で、利用者名とパスワードを受け付け、認証成功時にWebセッションを開始し、失敗時に画面へ通知する。

- 主体: 設定されたローカル利用者
- 別案・反例: 認証処理は共通実装にも分類するが、それだけでは画面からの独立した利用目的を表せない。
- 機能領域: 認証
- 業務対象: Web認証セッション
- 技術入口: ログイン画面・送信入口 (`ENTRY-66c5a6efefe481b6`)
- 完了成果: 認証セッション開始と学生検索への遷移、または認証失敗通知。
- 利用目的: 利用者が認証して学生管理を利用できる状態にする。
- 分類理由: 専用入力画面、送信、認証成否、完了結果が揃う独立したシステム利用目的。
- 集計範囲: selected\-system
- 開始契機: ログイン画面で資格情報を入力し送信する。
- 原文根拠: [Views/Account/Login.cshtml:1\-13](../../srcs/CSharp_ASPNET/Views/Account/Login.cshtml#L1)<br>[Web/Controllers/AccountController.cs:10\-34](../../srcs/CSharp_ASPNET/Web/Controllers/AccountController.cs#L10)

### ログアウト

- ID: `FUNCTION\-02c59fd1943df269`
- 担当要求: catalog

認証済み利用者が共通ヘッダーの操作から現在のWeb認証を終了し、ログイン画面へ戻る。

- 主体: 認証済み利用者
- 別案・反例: 小規模な認証ライフサイクル機能に統合する分け方もあるが、ログインの入力工程ではなく全認証済み画面からの退出目的として分離した。
- 機能領域: 認証
- 業務対象: Web認証セッション
- 技術入口: ログアウト送信入口 (`ENTRY-490e1e603efd7cff`)
- 完了成果: サインアウト後にログイン画面へ転送される。
- 利用目的: 現在の利用セッションを明示的に終了する。
- 分類理由: 業務画面から独立して起動でき、セッション終了という完了結果を持つ。
- 集計範囲: selected\-system
- 開始契機: 認証済み画面のログアウトボタンを押す。
- 原文根拠: [Views/Shared/\_Layout.cshtml:2\-4](../../srcs/CSharp_ASPNET/Views/Shared/_Layout.cshtml#L2)<br>[Web/Controllers/AccountController.cs:36\-41](../../srcs/CSharp_ASPNET/Web/Controllers/AccountController.cs#L36)

### 学生情報登録・保守

- ID: `FUNCTION\-fa89f6d82503c20f`
- 担当要求: catalog

学生情報の新規登録、既存情報の更新、確認付き論理削除を、登録・編集画面の作業として提供する。

- 主体: Staff、Administrator
- 別案・反例: 新規登録と更新を別主機能に分けることも可能だが、共通の入力・検証・保存作業のモードとして扱った。独立した承認・法的廃棄工程があれば削除の主機能化を再検討する。
- 機能領域: 学生管理
- 業務対象: 学生台帳の学生情報
- 技術入口: 学生検索画面と結果操作入口 (`ENTRY-0685f475cf01843c`)、学生新規画面・登録入口 (`ENTRY-04f7cce92fae19d2`)、学生詳細・更新・入力復元入口 (`ENTRY-2775c8d43391475a`)、学生論理削除入口 (`ENTRY-bb761d73375a1900`)
- 完了成果: 保存完了、変更なし、論理削除完了、または未完了理由の通知。
- 利用目的: 学生の基本・連絡先・在籍・所属情報を登録し維持する。
- 分類理由: 同じ学生情報・編集フォーム・保存結果を中心とする一連の保守作業としてまとめた。
- 集計範囲: selected\-system
- 開始契機: 新規登録を選ぶ、または検索結果から既存学生を編集する。
- 原文根拠: [Views/Students/Edit.cshtml:37\-176](../../srcs/CSharp_ASPNET/Views/Students/Edit.cshtml#L37)<br>[Web/Controllers/StudentsController.cs:5\-6](../../srcs/CSharp_ASPNET/Web/Controllers/StudentsController.cs#L5)<br>[Web/Controllers/StudentsController.cs:29\-44](../../srcs/CSharp_ASPNET/Web/Controllers/StudentsController.cs#L29)

### 学生検索・照会

- ID: `FUNCTION\-95e69c5434befaad`
- 担当要求: catalog

学生を学籍番号・氏名・クラス・在籍区分で検索し、結果一覧と必要な学生詳細を確認する。

- 主体: Viewer、Staff、Administrator
- 別案・反例: 更新対象の選択だけなら学生保守の操作にできるが、本画面は参照利用者にも結果を提供するため独立照会を残す。
- 機能領域: 学生管理
- 業務対象: 学生情報
- 技術入口: 学生検索画面と結果操作入口 (`ENTRY-0685f475cf01843c`)、学生詳細・更新・入力復元入口 (`ENTRY-2775c8d43391475a`)
- 完了成果: 条件に対応する一覧、件数、該当なし等の照会結果を得る。
- 利用目的: 対象学生と在籍・所属情報を調べる。
- 分類理由: 参照権限の利用者も完了できる独立した照会目的と結果表示がある。
- 集計範囲: selected\-system
- 開始契機: 学生検索画面で条件を指定して検索する。
- 原文根拠: [Views/Students/Search.cshtml:14\-77](../../srcs/CSharp_ASPNET/Views/Students/Search.cshtml#L14)<br>[Web/Controllers/StudentsController.cs:5\-22](../../srcs/CSharp_ASPNET/Web/Controllers/StudentsController.cs#L5)<br>[Infrastructure/WebStudentCoordinator.cs:7\-15](../../srcs/CSharp_ASPNET/Infrastructure/WebStudentCoordinator.cs#L7)


## 子操作

### 重複候補の確認・続行

- ID: `OPERATION\-78354a05df977f3d`
- 担当要求: catalog

保存時に提示された同一人物候補を確認し、理由を入力して同じ保存入口へ続行する。

- 別案・反例: 独立した重複統合・審査機能なら主機能になり得るが、本実装は保存続行の確認に限る。
- 技術入口: 学生新規画面・登録入口 (`ENTRY-04f7cce92fae19d2`)、学生詳細・更新・入力復元入口 (`ENTRY-2775c8d43391475a`)
- 完了成果: 確認を取り消す、または理由を付けて保存を続ける。
- 主帰属: 学生情報登録・保守 (`FUNCTION-fa89f6d82503c20f`)
- 利用目的: 同一人物候補を確認して保存意思を明確にする。
- 分類理由: 独立した対象整理ではなく、進行中の保存に従属するダイアログ。
- 集計範囲: selected\-system
- 利用文脈: 新規登録・更新の保存途中に必要となる確認。
- 原文根拠: [Views/Students/Edit.cshtml:151\-159](../../srcs/CSharp_ASPNET/Views/Students/Edit.cshtml#L151)<br>[Web/Controllers/StudentsController.cs:34\-40](../../srcs/CSharp_ASPNET/Web/Controllers/StudentsController.cs#L34)<br>[Core/SqlServerStudentService.cs:260\-282](../../srcs/CSharp_ASPNET/Core/SqlServerStudentService.cs#L260)

### 保守対象の検索・選択

- ID: `OPERATION\-fe8ffc62b1bb2dc5`
- 担当要求: catalog

独立照会にも使う学生検索入口を、既存学生の編集対象選択に利用する。

- 別案・反例: 全検索利用を照会だけにまとめる分け方もあるが、編集準備という利用文脈を別操作として残した。
- 技術入口: 学生検索画面と結果操作入口 (`ENTRY-0685f475cf01843c`)
- 完了成果: 選択学生の編集画面へ進む。
- 主帰属: 学生情報登録・保守 (`FUNCTION-fa89f6d82503c20f`)
- 利用目的: 保守する既存学生を特定する。
- 分類理由: 同じ技術入口でも、保守作業内では対象選択の工程になる。
- 集計範囲: selected\-system
- 利用文脈: 学生更新・論理削除の準備としての検索結果選択。
- 原文根拠: [Views/Students/Search.cshtml:14\-20](../../srcs/CSharp_ASPNET/Views/Students/Search.cshtml#L14)<br>[Views/Students/Search.cshtml:63\-66](../../srcs/CSharp_ASPNET/Views/Students/Search.cshtml#L63)<br>[Web/Controllers/StudentsController.cs:5\-22](../../srcs/CSharp_ASPNET/Web/Controllers/StudentsController.cs#L5)

### 入力復元・再読込・変更破棄

- ID: `OPERATION\-cf27427be305dab3`
- 担当要求: catalog

編集作業中に入力を読込時へ戻す、最新情報を読み直す、または変更破棄を確認して検索へ戻る。

- 別案・反例: 各ボタンを別操作に分割できるが、ここでは入力作業の取消・復帰という共通目的でまとめた。
- 技術入口: 学生新規画面・登録入口 (`ENTRY-04f7cce92fae19d2`)、学生詳細・更新・入力復元入口 (`ENTRY-2775c8d43391475a`)
- 完了成果: 読込時値・最新値の表示、または変更を破棄した画面復帰。
- 主帰属: 学生情報登録・保守 (`FUNCTION-fa89f6d82503c20f`)
- 利用目的: 編集中の入力を整理し、安全に作業をやり直し・終了する。
- 分類理由: 学生保守の作業制御であり、独立した業務対象を完了させない。
- 集計範囲: selected\-system
- 利用文脈: 学生入力・編集途中の取消と再読込。
- 原文根拠: [Web/Controllers/StudentsController.cs:5\-6](../../srcs/CSharp_ASPNET/Web/Controllers/StudentsController.cs#L5)<br>[Web/Controllers/StudentsController.cs:41\-41](../../srcs/CSharp_ASPNET/Web/Controllers/StudentsController.cs#L41)<br>[Views/Students/Edit.cshtml:143\-150](../../srcs/CSharp_ASPNET/Views/Students/Edit.cshtml#L143)<br>[Views/Students/Edit.cshtml:175\-175](../../srcs/CSharp_ASPNET/Views/Students/Edit.cshtml#L175)<br>[wwwroot/js/site.js:42\-53](../../srcs/CSharp_ASPNET/wwwroot/js/site.js#L42)<br>[wwwroot/js/site.js:139\-150](../../srcs/CSharp_ASPNET/wwwroot/js/site.js#L139)

### 学生詳細参照

- ID: `OPERATION\-05a23e427d16ab97`
- 担当要求: catalog

検索一覧から選んだ学生について、編集画面と同じ入口・フォームを参照モードで利用する。

- 別案・反例: 独立した詳細照会目的として分離することもできるが、ここでは一覧からの選択と共用フォームの参照モードにまとめた。
- 技術入口: 学生詳細・更新・入力復元入口 (`ENTRY-2775c8d43391475a`)
- 完了成果: 対象学生の詳細を読取表示する。
- 主帰属: 学生検索・照会 (`FUNCTION-95e69c5434befaad`)
- 利用目的: 選択した学生の詳細情報を確認する。
- 分類理由: 一覧で特定した対象を深く見る照会の補助工程。
- 集計範囲: selected\-system
- 利用文脈: 照会結果からの詳細確認。Viewerでは参照モードとなる。
- 原文根拠: [Views/Students/Search.cshtml:63\-66](../../srcs/CSharp_ASPNET/Views/Students/Search.cshtml#L63)<br>[Views/Students/Edit.cshtml:37\-44](../../srcs/CSharp_ASPNET/Views/Students/Edit.cshtml#L37)<br>[Web/Controllers/StudentsController.cs:5\-6](../../srcs/CSharp_ASPNET/Web/Controllers/StudentsController.cs#L5)<br>[Web/Controllers/StudentsController.cs:30\-31](../../srcs/CSharp_ASPNET/Web/Controllers/StudentsController.cs#L30)<br>[Infrastructure/WebStudentCoordinator.cs:22\-22](../../srcs/CSharp_ASPNET/Infrastructure/WebStudentCoordinator.cs#L22)<br>[Web/Models/StudentEditPageModel.cs:3\-15](../../srcs/CSharp_ASPNET/Web/Models/StudentEditPageModel.cs#L3)

### 検索結果の表示操作・条件クリア

- ID: `OPERATION\-ae1e266eec14c5f8`
- 担当要求: catalog

検索結果のページ、表示件数、並び順を変更し、または検索条件・結果をクリアする。

- 別案・反例: 大量データの独立分析機能なら主機能にもなるが、この実装は検索一覧内の補助操作。
- 技術入口: 学生検索画面と結果操作入口 (`ENTRY-0685f475cf01843c`)
- 完了成果: 指定表示の一覧、または未検索状態。
- 主帰属: 学生検索・照会 (`FUNCTION-95e69c5434befaad`)
- 利用目的: 照会結果を見やすくし、条件を再指定できるようにする。
- 分類理由: 既に開始した照会の表示・再指定工程である。
- 集計範囲: selected\-system
- 利用文脈: 学生検索・照会中の結果閲覧と条件再設定。
- 原文根拠: [Web/Controllers/StudentsController.cs:5\-6](../../srcs/CSharp_ASPNET/Web/Controllers/StudentsController.cs#L5)<br>[Web/Controllers/StudentsController.cs:23\-26](../../srcs/CSharp_ASPNET/Web/Controllers/StudentsController.cs#L23)<br>[Views/Students/Search.cshtml:45\-71](../../srcs/CSharp_ASPNET/Views/Students/Search.cshtml#L45)

### 学生新規入力・登録

- ID: `OPERATION\-4100b273ea61d3aa`
- 担当要求: catalog

新規学生の入力フォームを開き、学生情報を入力して登録する。

- 別案・反例: 新規登録専用の独立主機能に分けることも可能だが、現行ソースは既存編集と同じ画面・保存実装を中心にする。
- 技術入口: 学生新規画面・登録入口 (`ENTRY-04f7cce92fae19d2`)
- 完了成果: 新規学生の保存結果を得る。
- 主帰属: 学生情報登録・保守 (`FUNCTION-fa89f6d82503c20f`)
- 利用目的: 学生台帳に新しい学生を加える。
- 分類理由: 共通の学生入力・保存作業の新規モードとして分類した。
- 集計範囲: selected\-system
- 利用文脈: 学生保守の新規モード。
- 原文根拠: [Web/Controllers/StudentsController.cs:5\-6](../../srcs/CSharp_ASPNET/Web/Controllers/StudentsController.cs#L5)<br>[Web/Controllers/StudentsController.cs:29\-32](../../srcs/CSharp_ASPNET/Web/Controllers/StudentsController.cs#L29)<br>[Views/Students/Edit.cshtml:37\-62](../../srcs/CSharp_ASPNET/Views/Students/Edit.cshtml#L37)<br>[Views/Students/Edit.cshtml:143\-150](../../srcs/CSharp_ASPNET/Views/Students/Edit.cshtml#L143)

### 学生の理由付き論理削除

- ID: `OPERATION\-469473adb2ab805e`
- 担当要求: catalog

管理者が編集画面で対象と理由を確認し、学生を論理削除する。

- 別案・反例: 法的廃棄・承認・保存期限管理の独立工程があれば主機能化できるが、その目的は取得ソースから確認できない。
- 技術入口: 学生論理削除入口 (`ENTRY-bb761d73375a1900`)
- 完了成果: 論理削除完了、または未完了理由の通知。
- 主帰属: 学生情報登録・保守 (`FUNCTION-fa89f6d82503c20f`)
- 利用目的: 保守対象の学生を通常検索対象から除く。
- 分類理由: 編集対象の保守操作として配置され、確認ダイアログと理由入力を持つ。
- 集計範囲: selected\-system
- 利用文脈: 既存学生編集画面からの管理者補助操作。
- 原文根拠: [Views/Students/Edit.cshtml:143\-176](../../srcs/CSharp_ASPNET/Views/Students/Edit.cshtml#L143)<br>[Web/Controllers/StudentsController.cs:5\-6](../../srcs/CSharp_ASPNET/Web/Controllers/StudentsController.cs#L5)<br>[Web/Controllers/StudentsController.cs:43\-44](../../srcs/CSharp_ASPNET/Web/Controllers/StudentsController.cs#L43)<br>[Infrastructure/WebStudentCoordinator.cs:24\-24](../../srcs/CSharp_ASPNET/Infrastructure/WebStudentCoordinator.cs#L24)

### 学生既存情報の編集・更新

- ID: `OPERATION\-2b805dc211d38474`
- 担当要求: catalog

既存学生を読み込み、変更を入力して更新する。

- 別案・反例: 登録と更新を別主機能に数える分け方もあるが、独立承認等の別作業は取得ソースに現れていない。
- 技術入口: 学生詳細・更新・入力復元入口 (`ENTRY-2775c8d43391475a`)
- 完了成果: 更新完了、変更なし、または更新未完了の通知。
- 主帰属: 学生情報登録・保守 (`FUNCTION-fa89f6d82503c20f`)
- 利用目的: 登録済み学生情報を維持する。
- 分類理由: 新規登録と共用する学生保守作業の既存対象モード。
- 集計範囲: selected\-system
- 利用文脈: 学生保守の既存編集モード。
- 原文根拠: [Web/Controllers/StudentsController.cs:5\-6](../../srcs/CSharp_ASPNET/Web/Controllers/StudentsController.cs#L5)<br>[Web/Controllers/StudentsController.cs:30\-40](../../srcs/CSharp_ASPNET/Web/Controllers/StudentsController.cs#L30)<br>[Views/Students/Edit.cshtml:37\-62](../../srcs/CSharp_ASPNET/Views/Students/Edit.cshtml#L37)<br>[Views/Students/Edit.cshtml:143\-150](../../srcs/CSharp_ASPNET/Views/Students/Edit.cshtml#L143)


## 共通能力

### ローカル認証・Cookieセッション

- ID: `COMMON\-d0315425c7b13a6b`
- 担当要求: catalog

LocalLoginが設定された利用者の認証・失敗抑制・Cookie受入判定を所有し、AccountControllerとホスト設定がセッション開始・終了・検査に利用する。

- 別案・反例: 各画面へ内包する分け方もあるが、ホストのCookie検査にも利用される中央責任として分離した。
- 利用先: ログイン (`FUNCTION-3a8a1be5f76f61aa`)、ログアウト (`FUNCTION-02c59fd1943df269`)、Webホスト・要求保護・例外応答 (`COMMON-5e74be0106d52822`)
- 分類理由: 独立したログイン・ログアウト機能の下で使われる認証実装を別に保持する。
- 共有・集中する責務: 認証判定とWeb認証セッションの中央管理。
- 集計範囲: selected\-system
- 原文根拠: [Infrastructure/LocalLogin.cs:13\-90](../../srcs/CSharp_ASPNET/Infrastructure/LocalLogin.cs#L13)<br>[Web/Controllers/AccountController.cs:18\-41](../../srcs/CSharp_ASPNET/Web/Controllers/AccountController.cs#L18)<br>[Infrastructure/WebHostSetup.cs:15\-18](../../srcs/CSharp_ASPNET/Infrastructure/WebHostSetup.cs#L15)

### 要求主体・役割・権限検査

- ID: `COMMON\-59b6d97bf7d6ea45`
- 担当要求: catalog

RequestIdentityが認証情報からCurrentUserを作り、読取・保存・管理者操作の権限確認を提供する。

- 別案・反例: 個別アクションの検査として分散できるが、原文ではRequestIdentityに集約される。
- 利用先: 学生Web操作の調停 (`COMMON-7739e9983ee40d19`)、学生検索・照会 (`FUNCTION-95e69c5434befaad`)、学生情報登録・保守 (`FUNCTION-fa89f6d82503c20f`)
- 分類理由: 複数の学生操作から利用される中央の認可責任。
- 共有・集中する責務: Web要求における主体・セッション・役割の解釈と認可。
- 集計範囲: selected\-system
- 原文根拠: [Infrastructure/RequestIdentity.cs:4\-18](../../srcs/CSharp_ASPNET/Infrastructure/RequestIdentity.cs#L4)<br>[Infrastructure/WebStudentCoordinator.cs:7\-24](../../srcs/CSharp_ASPNET/Infrastructure/WebStudentCoordinator.cs#L7)

### Web入力・識別番号・Core契約変換

- ID: `COMMON\-05007c9fc45349dd`
- 担当要求: catalog

StudentSaveInput、StudentSearchInputの変換メソッドとIdParserがWeb入力をCore要求へ変換し、既存値からフォームを構成する。

- 別案・反例: DTO宣言だけのデータ資源とするには変換・検査責任があるため、データ契約とは別に共通処理を保持した。
- 利用先: 学生Web操作の調停 (`COMMON-7739e9983ee40d19`)、学生詳細・更新・入力復元入口 (`ENTRY-2775c8d43391475a`)
- 分類理由: 検索、編集初期表示、保存、削除で実利用される変換責任。
- 共有・集中する責務: Web転送形式とCoreの入力契約・識別子表現を接続する。
- 集計範囲: selected\-system
- 原文根拠: [Web/Inputs/StudentSaveInput.cs:34\-61](../../srcs/CSharp_ASPNET/Web/Inputs/StudentSaveInput.cs#L34)<br>[Web/Inputs/StudentSearchInput.cs:11\-12](../../srcs/CSharp_ASPNET/Web/Inputs/StudentSearchInput.cs#L11)<br>[Infrastructure/WebStudentCoordinator.cs:7\-14](../../srcs/CSharp_ASPNET/Infrastructure/WebStudentCoordinator.cs#L7)<br>[Infrastructure/WebStudentCoordinator.cs:22\-24](../../srcs/CSharp_ASPNET/Infrastructure/WebStudentCoordinator.cs#L22)

### 和暦・西暦・年度処理

- ID: `COMMON\-b89d8de2b7f2c5d8`
- 担当要求: catalog

JapaneseDateServiceが明示的な元号境界による日付解釈、和暦表示、ISO日付と年度処理を提供する。

- 別案・反例: 画面部品として扱うとマスタ入力やCore変換での利用を捉えられない。
- 利用先: 入力正規化・共通検証 (`COMMON-ac4e2446c323b378`)、マスタ保守ルール・DB管理者確認 (`COMMON-d07c5cf8dcb72c73`)、学生業務ルール・SQLサービス (`COMMON-3fcb61c6b12956ad`)、Web入力・識別番号・Core契約変換 (`COMMON-05007c9fc45349dd`)
- 分類理由: 学生・マスタ・Web変換で共有される中央の日付責任。
- 共有・集中する責務: 入力・保存・表示で使う日付解釈と和暦表現。
- 集計範囲: selected\-system
- 原文根拠: [Core/JapaneseDateService.cs:7\-62](../../srcs/CSharp_ASPNET/Core/JapaneseDateService.cs#L7)<br>[Core/MasterMaintenanceService.cs:30\-36](../../srcs/CSharp_ASPNET/Core/MasterMaintenanceService.cs#L30)<br>[Core/StudentNormalizer.cs:119\-137](../../srcs/CSharp_ASPNET/Core/StudentNormalizer.cs#L119)<br>[Core/SqlServerStudentService.cs:175\-187](../../srcs/CSharp_ASPNET/Core/SqlServerStudentService.cs#L175)<br>[Web/Inputs/StudentSaveInput.cs:44\-55](../../srcs/CSharp_ASPNET/Web/Inputs/StudentSaveInput.cs#L44)

### マスタ保守ルール・DB管理者確認

- ID: `COMMON\-d07c5cf8dcb72c73`
- 担当要求: catalog

MasterMaintenanceServiceがDB接続主体の管理者確認とクラス・コードの保守ルール、保存を所有する。

- 別案・反例: 両主機能へ実装を重複記載できるが、中央責任として分離し機能数を増やさない。
- 利用先: クラスマスタ保守 (`FUNCTION-91d28046181a5fb5`)、業務コードマスタ保守 (`FUNCTION-22591896d39dca6b`)、StudentMaintenance CLI (`ENTRY-aa841ff3444b5ee5`)
- 分類理由: 独立したクラス保守・コード保守を支える共用サービス。
- 共有・集中する責務: マスタ保守における管理者確認・整合性・永続化。
- 集計範囲: selected\-system
- 原文根拠: [Core/MasterMaintenanceService.cs:15\-137](../../srcs/CSharp_ASPNET/Core/MasterMaintenanceService.cs#L15)<br>[maintenance/Program.cs:11\-13](../../srcs/CSharp_ASPNET/maintenance/Program.cs#L11)

### 学生管理メニューのナビゲーション

- ID: `COMMON\-a72f42829f3452d1`
- 担当要求: catalog

専用メニュー画面は学生検索と権限に応じた新規登録への移動を提供する。集約照会や作業完了結果は持たない。

- 別案・反例: 状態集約や独立照会結果を表示するワークベンチなら主機能にできるが、この原文は移動先選択だけ。
- 利用先: 学生管理メニュー入口 (`ENTRY-c904cd076b366295`)、学生検索画面と結果操作入口 (`ENTRY-0685f475cf01843c`)
- 分類理由: リンクと役割別表示が責任であり、移動先の業務結果をメニュー自身へ帰属させない。
- 共有・集中する責務: 学生業務の移動先を提示する共通ナビゲーション。
- 集計範囲: selected\-system
- 原文根拠: [Web/Controllers/MenuController.cs:6\-10](../../srcs/CSharp_ASPNET/Web/Controllers/MenuController.cs#L6)<br>[Views/Menu/Index.cshtml:1\-7](../../srcs/CSharp_ASPNET/Views/Menu/Index.cshtml#L1)<br>[Views/Students/Search.cshtml:14\-18](../../srcs/CSharp_ASPNET/Views/Students/Search.cshtml#L14)

### 入力正規化・共通検証

- ID: `COMMON\-ac4e2446c323b378`
- 担当要求: catalog

StudentNormalizerが文字列、識別子、氏名照合値、カナ、連絡先、コード、学生入力の正規化・検証を提供する。

- 別案・反例: 学生登録専用の内部処理とする分け方では、検索・マスタ側の利用を表せない。
- 利用先: 学生業務ルール・SQLサービス (`COMMON-3fcb61c6b12956ad`)、マスタ保守ルール・DB管理者確認 (`COMMON-d07c5cf8dcb72c73`)、Web入力・識別番号・Core契約変換 (`COMMON-05007c9fc45349dd`)
- 分類理由: 学生保存に加え検索条件・マスタ入力からも使う共有業務ルール。
- 共有・集中する責務: 入力値の共通表現と検証エラーを統一する。
- 集計範囲: selected\-system
- 原文根拠: [Core/StudentNormalizer.cs:19\-169](../../srcs/CSharp_ASPNET/Core/StudentNormalizer.cs#L19)<br>[Core/Contracts.cs:42\-58](../../srcs/CSharp_ASPNET/Core/Contracts.cs#L42)<br>[Core/MasterMaintenanceService.cs:30\-36](../../srcs/CSharp_ASPNET/Core/MasterMaintenanceService.cs#L30)<br>[Core/SqlServerStudentService.cs:219\-231](../../srcs/CSharp_ASPNET/Core/SqlServerStudentService.cs#L219)

### Web結果・時刻・エラー整形

- ID: `COMMON\-a09fb8ca183e4bd5`
- 担当要求: catalog

WebPresentationが業務日時、一覧値、項目エラー、HTTP状態等の表示用表現を提供する。未接続のJSON候補処理は別支援記録に保持する。

- 別案・反例: 画面ごとの整形に含められるが、共通クラスの実利用があるため分離した。
- 利用先: 学生Web操作の調停 (`COMMON-7739e9983ee40d19`)、学生新規画面・登録入口 (`ENTRY-04f7cce92fae19d2`)、学生詳細・更新・入力復元入口 (`ENTRY-2775c8d43391475a`)、学生論理削除入口 (`ENTRY-bb761d73375a1900`)、Webホスト・要求保護・例外応答 (`COMMON-5e74be0106d52822`)
- 分類理由: 調停、MVC、共通例外応答で使う表示責任。
- 共有・集中する責務: サービス結果とエラーのWeb向け表現を統一する。
- 集計範囲: selected\-system
- 原文根拠: [Infrastructure/WebPresentation.cs:3\-7](../../srcs/CSharp_ASPNET/Infrastructure/WebPresentation.cs#L3)<br>[Infrastructure/WebPresentation.cs:20\-23](../../srcs/CSharp_ASPNET/Infrastructure/WebPresentation.cs#L20)<br>[Infrastructure/WebStudentCoordinator.cs:26\-27](../../srcs/CSharp_ASPNET/Infrastructure/WebStudentCoordinator.cs#L26)<br>[Web/Controllers/StudentsController.cs:38\-38](../../srcs/CSharp_ASPNET/Web/Controllers/StudentsController.cs#L38)<br>[Infrastructure/WebHostSetup.cs:27\-27](../../srcs/CSharp_ASPNET/Infrastructure/WebHostSetup.cs#L27)

### SQL書込基盤・排他・監査

- ID: `COMMON\-f89bacb97f5450d5`
- 担当要求: catalog

両CoreサービスがSQLコマンド・パラメーター・書込ゲート等を共用し、保存時の監査情報を記録する。AuditOperationはマスタ変更の監査種別を決める。

- 別案・反例: SQLヘルパー・排他・監査を細分化できるが、目録では共通の書込基盤としてまとめた。
- 利用先: 学生業務ルール・SQLサービス (`COMMON-3fcb61c6b12956ad`)、マスタ保守ルール・DB管理者確認 (`COMMON-d07c5cf8dcb72c73`)
- 分類理由: 学生・マスタ双方の実利用が確認できる書込基盤責任。
- 共有・集中する責務: Core書込処理のSQL実行補助、排他、監査情報を統一する。
- 集計範囲: selected\-system
- 原文根拠: [Core/AuditOperation.cs:4\-8](../../srcs/CSharp_ASPNET/Core/AuditOperation.cs#L4)<br>[Core/SqlServerStudentService.cs:65\-102](../../srcs/CSharp_ASPNET/Core/SqlServerStudentService.cs#L65)<br>[Core/SqlServerStudentService.cs:234\-236](../../srcs/CSharp_ASPNET/Core/SqlServerStudentService.cs#L234)<br>[Core/SqlServerStudentService.cs:298\-299](../../srcs/CSharp_ASPNET/Core/SqlServerStudentService.cs#L298)<br>[Core/SqlServerStudentService.cs:377\-383](../../srcs/CSharp_ASPNET/Core/SqlServerStudentService.cs#L377)<br>[Core/SqlServerStudentService.cs:395\-405](../../srcs/CSharp_ASPNET/Core/SqlServerStudentService.cs#L395)<br>[Core/MasterMaintenanceService.cs:5\-5](../../srcs/CSharp_ASPNET/Core/MasterMaintenanceService.cs#L5)<br>[Core/MasterMaintenanceService.cs:38\-42](../../srcs/CSharp_ASPNET/Core/MasterMaintenanceService.cs#L38)<br>[Core/MasterMaintenanceService.cs:74\-75](../../srcs/CSharp_ASPNET/Core/MasterMaintenanceService.cs#L74)<br>[Core/MasterMaintenanceService.cs:119\-136](../../srcs/CSharp_ASPNET/Core/MasterMaintenanceService.cs#L119)

### 学生業務ルール・SQLサービス

- ID: `COMMON\-3fcb61c6b12956ad`
- 担当要求: catalog

SqlServerStudentServiceが学生検索、詳細取得、候補取得、保存、論理削除と業務整合性確認を所有する。Web登録はwebTokens=trueを指定する。

- 別案・反例: 各公開メソッドを機能として数えると技術粒度になるため、業務機能とは分離した。
- 利用先: 学生検索・照会 (`FUNCTION-95e69c5434befaad`)、学生情報登録・保守 (`FUNCTION-fa89f6d82503c20f`)、学生Web操作の調停 (`COMMON-7739e9983ee40d19`)、配備DB読取検査プログラム (`ENTRY-fd80a6fc9f66497c`)
- 分類理由: 利用者向け機能を消さず、その下で共有される業務責任を表す。
- 共有・集中する責務: 学生情報の照会・整合性・保存とSQLアクセスの中央実装。
- 集計範囲: selected\-system
- 原文根拠: [Core/SqlServerStudentService.cs:115\-209](../../srcs/CSharp_ASPNET/Core/SqlServerStudentService.cs#L115)<br>[Core/SqlServerStudentService.cs:219\-409](../../srcs/CSharp_ASPNET/Core/SqlServerStudentService.cs#L219)<br>[Infrastructure/WebHostSetup.cs:23\-23](../../srcs/CSharp_ASPNET/Infrastructure/WebHostSetup.cs#L23)<br>[Infrastructure/WebStudentCoordinator.cs:7\-24](../../srcs/CSharp_ASPNET/Infrastructure/WebStudentCoordinator.cs#L7)<br>[deployment/DatabaseSmoke/Program.cs:4\-7](../../srcs/CSharp_ASPNET/deployment/DatabaseSmoke/Program.cs#L4)

### 学生Web操作の調停

- ID: `COMMON\-7739e9983ee40d19`
- 担当要求: catalog

WebStudentCoordinatorが要求主体、検索状態、入力変換、Coreサービス、表示用結果を学生Web操作として調停する。

- 別案・反例: コントローラーごとの処理へ吸収することもできるが、原文では独立クラスへ集約されている。
- 利用先: 学生検索画面と結果操作入口 (`ENTRY-0685f475cf01843c`)、学生新規画面・登録入口 (`ENTRY-04f7cce92fae19d2`)、学生詳細・更新・入力復元入口 (`ENTRY-2775c8d43391475a`)、学生論理削除入口 (`ENTRY-bb761d73375a1900`)
- 分類理由: 画面の独立目的とは別に、検索・編集・保存・削除の実装を中央調停する。
- 共有・集中する責務: 学生Web操作を共通の主体・状態・サービス契約へ接続する。
- 集計範囲: selected\-system
- 原文根拠: [Infrastructure/WebStudentCoordinator.cs:3\-28](../../srcs/CSharp_ASPNET/Infrastructure/WebStudentCoordinator.cs#L3)<br>[Web/Controllers/StudentsController.cs:13\-18](../../srcs/CSharp_ASPNET/Web/Controllers/StudentsController.cs#L13)<br>[Web/Controllers/StudentsController.cs:29\-43](../../srcs/CSharp_ASPNET/Web/Controllers/StudentsController.cs#L29)

### Webホスト・要求保護・例外応答

- ID: `COMMON\-5e74be0106d52822`
- 担当要求: catalog

WebHostSetupがDI、MVC、Cookie、CSRF、要求制限、ヘッダー、例外応答を中央設定し、AntiforgeryResultFilterを登録する。API向け応答分岐の存在だけから業務APIの稼働は推定しない。

- 別案・反例: 設定を支援資源とする分け方もあるが、ここでは要求処理時の保護・例外応答も実装するため共通処理とした。
- 利用先: ログイン画面・送信入口 (`ENTRY-66c5a6efefe481b6`)、ログアウト送信入口 (`ENTRY-490e1e603efd7cff`)、学生管理メニュー入口 (`ENTRY-c904cd076b366295`)、学生検索画面と結果操作入口 (`ENTRY-0685f475cf01843c`)、学生新規画面・登録入口 (`ENTRY-04f7cce92fae19d2`)、学生詳細・更新・入力復元入口 (`ENTRY-2775c8d43391475a`)、学生論理削除入口 (`ENTRY-bb761d73375a1900`)、旧検索候補入口 (`ENTRY-e7c9bfab9c3816a4`)
- 分類理由: 起動点から一括適用される中央責任である。
- 共有・集中する責務: Web全体の登録、要求保護、共通失敗応答。
- 集計範囲: selected\-system
- 原文根拠: [Infrastructure/WebHostSetup.cs:13\-29](../../srcs/CSharp_ASPNET/Infrastructure/WebHostSetup.cs#L13)<br>[Infrastructure/AntiforgeryResultFilter.cs:5\-10](../../srcs/CSharp_ASPNET/Infrastructure/AntiforgeryResultFilter.cs#L5)<br>[Program.cs:2\-6](../../srcs/CSharp_ASPNET/Program.cs#L2)

### Webの一時状態・編集スナップショット・通知

- ID: `COMMON\-4485a90fc273e866`
- 担当要求: catalog

SearchContextStore、EditorSnapshotStore、FlashMessageStoreが検索状態、読込時入力、完了通知をプロセス内で保持する。トークン生成は認証でも利用される。

- 別案・反例: 各ストアを別共通部品に分けることもできるが、ここではWeb作業状態という責任群でまとめた。
- 利用先: 学生Web操作の調停 (`COMMON-7739e9983ee40d19`)、学生検索画面と結果操作入口 (`ENTRY-0685f475cf01843c`)、学生新規画面・登録入口 (`ENTRY-04f7cce92fae19d2`)、学生詳細・更新・入力復元入口 (`ENTRY-2775c8d43391475a`)、学生論理削除入口 (`ENTRY-bb761d73375a1900`)、ローカル認証・Cookieセッション (`COMMON-d0315425c7b13a6b`)
- 分類理由: 検索・編集・保存後復帰に利用される中央ストア群であり、物理状態表と混同しない。
- 共有・集中する責務: 主体・セッション等に結び付く一時的Web作業状態の保持。
- 集計範囲: selected\-system
- 原文根拠: [Infrastructure/SearchContextStore.cs:7\-18](../../srcs/CSharp_ASPNET/Infrastructure/SearchContextStore.cs#L7)<br>[Infrastructure/EditorSnapshotStore.cs:5\-12](../../srcs/CSharp_ASPNET/Infrastructure/EditorSnapshotStore.cs#L5)<br>[Infrastructure/FlashMessageStore.cs:4\-10](../../srcs/CSharp_ASPNET/Infrastructure/FlashMessageStore.cs#L4)<br>[Infrastructure/WebStudentCoordinator.cs:7\-20](../../srcs/CSharp_ASPNET/Infrastructure/WebStudentCoordinator.cs#L7)<br>[Web/Controllers/StudentsController.cs:31\-31](../../srcs/CSharp_ASPNET/Web/Controllers/StudentsController.cs#L31)<br>[Web/Controllers/StudentsController.cs:44\-44](../../srcs/CSharp_ASPNET/Web/Controllers/StudentsController.cs#L44)<br>[Infrastructure/LocalLogin.cs:77\-77](../../srcs/CSharp_ASPNET/Infrastructure/LocalLogin.cs#L77)

### 共通レイアウト・表示資源・画面操作

- ID: `COMMON\-6cb65166b395fdd5`
- 担当要求: catalog

共通レイアウト、メッセージpartial、CSS、site.jsが各画面の枠組みとフォーム送信・ダイアログ・変更破棄等の操作を提供する。共有断片を独立画面として数えない。

- 別案・反例: CSS・JS・partialを個別部品に細分化できるが、主機能数とは分けて共通UI責任群として保持する。
- 利用先: ログイン画面・送信入口 (`ENTRY-66c5a6efefe481b6`)、学生管理メニュー入口 (`ENTRY-c904cd076b366295`)、学生検索画面と結果操作入口 (`ENTRY-0685f475cf01843c`)、学生新規画面・登録入口 (`ENTRY-04f7cce92fae19d2`)、学生詳細・更新・入力復元入口 (`ENTRY-2775c8d43391475a`)、学生論理削除入口 (`ENTRY-bb761d73375a1900`)
- 分類理由: ViewStartとレイアウト資源参照、partial使用から実際の画面消費を確認できる。
- 共有・集中する責務: 複数Web画面の枠組み、表示、共通フォーム操作を支える。
- 集計範囲: selected\-system
- 原文根拠: [Views/Shared/\_Layout.cshtml:1\-5](../../srcs/CSharp_ASPNET/Views/Shared/_Layout.cshtml#L1)<br>[Views/Shared/\_MessagePanel.cshtml:1\-3](../../srcs/CSharp_ASPNET/Views/Shared/_MessagePanel.cshtml#L1)<br>[Views/\_ViewImports.cshtml:1\-3](../../srcs/CSharp_ASPNET/Views/_ViewImports.cshtml#L1)<br>[Views/\_ViewStart.cshtml:1\-1](../../srcs/CSharp_ASPNET/Views/_ViewStart.cshtml#L1)<br>[Views/Students/Search.cshtml:19\-20](../../srcs/CSharp_ASPNET/Views/Students/Search.cshtml#L19)<br>[wwwroot/css/site.css:1\-2](../../srcs/CSharp_ASPNET/wwwroot/css/site.css#L1)<br>[wwwroot/css/students.css:1\-117](../../srcs/CSharp_ASPNET/wwwroot/css/students.css#L1)<br>[wwwroot/js/site.js:1\-231](../../srcs/CSharp_ASPNET/wwwroot/js/site.js#L1)


## データ対象

### dbo.m\_class

- ID: `DATA\-ace7a698d1adb33e`
- 担当要求: catalog

CREATE TABLEで定義されるクラス物理表。年度・学年・コード・名称・利用期間・定員・有効性と更新管理情報を持つ。

- 原文根拠: [database/001\_schema.sql:61\-88](../../srcs/CSharp_ASPNET/database/001_schema.sql#L61)<br>[database/001\_schema.sql:186\-204](../../srcs/CSharp_ASPNET/database/001_schema.sql#L186)

### dbo.m\_code

- ID: `DATA\-67f51fb05888a625`
- 担当要求: catalog

分類IDとコード値を複合主キーとする業務コード物理表。名称・表示順・期間・保護状態等を持ち、seed原文は70コードを列挙する。実DBへの投入済みを意味しない。

- 原文根拠: [database/001\_schema.sql:111\-135](../../srcs/CSharp_ASPNET/database/001_schema.sql#L111)<br>[database/002\_seed.sql:14\-93](../../srcs/CSharp_ASPNET/database/002_seed.sql#L14)

### dbo.m\_code\_category

- ID: `DATA\-5dc73e10013223aa`
- 担当要求: catalog

分類IDを主キーとするコード分類の物理表。コード長・追加可否等を定義する。seedは性別・在籍区分・都道府県・続柄・学年の5分類を記述する。

- 原文根拠: [database/001\_schema.sql:89\-110](../../srcs/CSharp_ASPNET/database/001_schema.sql#L89)<br>[database/002\_seed.sql:8\-13](../../srcs/CSharp_ASPNET/database/002_seed.sql#L8)

### dbo.t\_confirmation

- ID: `DATA\-deaaa1ddf00766b3`
- 担当要求: catalog

重複確認の主体・対象・版・照合値・期限等を持つ物理表。Coreには非Webトークン分岐からのSQL参照があるが、取得Web登録はメモリー型トークンを選ぶ。

- 原文根拠: [database/001\_schema.sql:155\-169](../../srcs/CSharp_ASPNET/database/001_schema.sql#L155)<br>[Core/SqlServerStudentService.cs:322\-335](../../srcs/CSharp_ASPNET/Core/SqlServerStudentService.cs#L322)<br>[Infrastructure/WebHostSetup.cs:23\-23](../../srcs/CSharp_ASPNET/Infrastructure/WebHostSetup.cs#L23)<br>[database/003\_web\_permissions.sql:23\-24](../../srcs/CSharp_ASPNET/database/003_web_permissions.sql#L23)

### Coreサービス契約・DTO・正規化値

- ID: `DATA\-82ab1e80c677079f`
- 担当要求: catalog

Role、Outcome、CurrentUser、FieldError、BirthDateInput、StudentDraft、SearchCriteria、一覧・詳細・候補・保存要求結果、IStudentServiceとNormalizedStudentを定義する。これらはサービス／転送上の型であり、物理表定義やORM Entityとは扱わない。

- 原文根拠: [Core/Contracts.cs:4\-94](../../srcs/CSharp_ASPNET/Core/Contracts.cs#L4)<br>[Core/StudentNormalizer.cs:7\-16](../../srcs/CSharp_ASPNET/Core/StudentNormalizer.cs#L7)

### マスタ保守CLIの入出力契約

- ID: `DATA\-a24863ea42bd4d2a`
- 担当要求: catalog

ClassChange、CodeChange、MaintenanceResultが保守CLIのJSON入力・結果契約を構成する。物理マスタ表とは別に保持する。

- 原文根拠: [Core/MasterMaintenanceService.cs:9\-11](../../srcs/CSharp_ASPNET/Core/MasterMaintenanceService.cs#L9)<br>[maintenance/Program.cs:8\-13](../../srcs/CSharp_ASPNET/maintenance/Program.cs#L8)

### dbo.t\_operation\_log

- ID: `DATA\-07c1ad9593609c3c`
- 担当要求: catalog

操作対象・監査種別・変更列・実行主体・日時・理由等を持つ操作履歴の物理表。利用者向け履歴照会入口の存在は確認していない。

- 原文根拠: [database/001\_schema.sql:136\-154](../../srcs/CSharp_ASPNET/database/001_schema.sql#L136)<br>[database/001\_schema.sql:203\-211](../../srcs/CSharp_ASPNET/database/001_schema.sql#L203)

### dbo.t\_runtime\_state

- ID: `DATA\-5da744d01ee06b77`
- 担当要求: catalog

所有者・セッション・状態種別・暗号化ペイロード・期限・版等を持つ物理表。取得アプリの検索・編集状態ストアはメモリー実装で、当表のアプリDML利用は観測していない。

- 原文根拠: [database/001\_schema.sql:170\-184](../../srcs/CSharp_ASPNET/database/001_schema.sql#L170)<br>[database/003\_web\_permissions.sql:23\-24](../../srcs/CSharp_ASPNET/database/003_web_permissions.sql#L23)

### dbo.m\_student

- ID: `DATA\-9d5d3195fff34959`
- 担当要求: catalog

CREATE TABLEで定義される学生物理表。学生識別、基本・連絡先・在籍・所属、論理削除、更新管理情報を持つ。DTO宣言とは別のデータ対象。

- 原文根拠: [database/001\_schema.sql:7\-60](../../srcs/CSharp_ASPNET/database/001_schema.sql#L7)<br>[database/001\_schema.sql:186\-204](../../srcs/CSharp_ASPNET/database/001_schema.sql#L186)

### Web入力DTO・要求・画面モデル

- ID: `DATA\-3c301828eb1ebb13`
- 担当要求: catalog

学生保存・削除・検索入力、検索状態／ページ／候補要求、ログイン・学生編集・検索画面モデルを定義する。OptionsRequestの宣言だけから公開APIを推定しない。

- 原文根拠: [Web/Inputs/StudentDeleteInput.cs:3\-4](../../srcs/CSharp_ASPNET/Web/Inputs/StudentDeleteInput.cs#L3)<br>[Web/Inputs/StudentSaveInput.cs:6\-33](../../srcs/CSharp_ASPNET/Web/Inputs/StudentSaveInput.cs#L6)<br>[Web/Inputs/StudentSearchInput.cs:4\-21](../../srcs/CSharp_ASPNET/Web/Inputs/StudentSearchInput.cs#L4)<br>[Web/Models/LoginPageModel.cs:3\-7](../../srcs/CSharp_ASPNET/Web/Models/LoginPageModel.cs#L3)<br>[Web/Models/StudentEditPageModel.cs:3\-15](../../srcs/CSharp_ASPNET/Web/Models/StudentEditPageModel.cs#L3)<br>[Web/Models/StudentSearchPageModel.cs:4\-16](../../srcs/CSharp_ASPNET/Web/Models/StudentSearchPageModel.cs#L4)


## 技術入口

### 配備DB読取検査プログラム

- ID: `ENTRY\-fd80a6fc9f66497c`
- 担当要求: catalog

DatabaseSmokeは実サービスの候補取得と検索を呼び出す検査用コンソール入口。ソース内のPASS出力は検査結果として採用しない。

- 原文根拠: [deployment/DatabaseSmoke/Program.cs:3\-9](../../srcs/CSharp_ASPNET/deployment/DatabaseSmoke/Program.cs#L3)<br>[deployment/DatabaseSmoke/DatabaseSmoke.csproj:1\-4](../../srcs/CSharp_ASPNET/deployment/DatabaseSmoke/DatabaseSmoke.csproj#L1)

### 評価用セッション作成入口

- ID: `ENTRY\-801781942a7dc5ea`
- 担当要求: catalog

POST /\_evaluation/sessionの登録がある。Development環境とサーバー設定に依存する評価用入口であり、通常ログイン画面とは別に保持する。

- 原文根拠: [Infrastructure/WebHostSetup.cs:30\-31](../../srcs/CSharp_ASPNET/Infrastructure/WebHostSetup.cs#L30)<br>[appsettings.json:1\-1](../../srcs/CSharp_ASPNET/appsettings.json#L1)

### 存活応答入口

- ID: `ENTRY\-52ca446bbea6e0f4`
- 担当要求: catalog

GET /healthはrunningとdatabase=not\-testedを返す登録。DB接続確認や利用者向け独立業務の証拠ではない。

- 原文根拠: [Infrastructure/WebHostSetup.cs:32\-32](../../srcs/CSharp_ASPNET/Infrastructure/WebHostSetup.cs#L32)

### ログイン画面・送信入口

- ID: `ENTRY\-66c5a6efefe481b6`
- 担当要求: catalog

GET /login と POST /login。LocalLogin設定が有効な場合のMVC画面入口である。

- 原文根拠: [Web/Controllers/AccountController.cs:10\-34](../../srcs/CSharp_ASPNET/Web/Controllers/AccountController.cs#L10)<br>[Views/Account/Login.cshtml:1\-13](../../srcs/CSharp_ASPNET/Views/Account/Login.cshtml#L1)

### 配備ログインハッシュ生成入口

- ID: `ENTRY\-c6f2f9dceff05846`
- 担当要求: catalog

LoginPasswordHashは配備時のハッシュ生成補助コンソールであり、業務利用者のログイン画面とは別の支援入口。

- 原文根拠: [deployment/LoginPasswordHash/Program.cs:4\-9](../../srcs/CSharp_ASPNET/deployment/LoginPasswordHash/Program.cs#L4)<br>[deployment/LoginPasswordHash/LoginPasswordHash.csproj:1\-4](../../srcs/CSharp_ASPNET/deployment/LoginPasswordHash/LoginPasswordHash.csproj#L1)

### ログアウト送信入口

- ID: `ENTRY\-490e1e603efd7cff`
- 担当要求: catalog

認証付きPOST /logout。共通ヘッダーのフォームから送信する。

- 原文根拠: [Web/Controllers/AccountController.cs:36\-41](../../srcs/CSharp_ASPNET/Web/Controllers/AccountController.cs#L36)<br>[Views/Shared/\_Layout.cshtml:2\-4](../../srcs/CSharp_ASPNET/Views/Shared/_Layout.cshtml#L2)

### StudentMaintenance CLI

- ID: `ENTRY\-aa841ff3444b5ee5`
- 担当要求: catalog

class\|codeと入力JSONファイルを引数に取る実行プロジェクト。接続設定を受け取り、選択したマスタ保守結果を出力する。

- 原文根拠: [maintenance/Program.cs:4\-17](../../srcs/CSharp_ASPNET/maintenance/Program.cs#L4)<br>[maintenance/StudentMaintenance.csproj:1\-4](../../srcs/CSharp_ASPNET/maintenance/StudentMaintenance.csproj#L1)

### 学生管理メニュー入口

- ID: `ENTRY\-c904cd076b366295`
- 担当要求: catalog

認証付きGET /menuがメニューViewを表示する。

- 原文根拠: [Web/Controllers/MenuController.cs:6\-10](../../srcs/CSharp_ASPNET/Web/Controllers/MenuController.cs#L6)<br>[Views/Menu/Index.cshtml:1\-7](../../srcs/CSharp_ASPNET/Views/Menu/Index.cshtml#L1)

### 旧検索候補入口

- ID: `ENTRY\-e7c9bfab9c3816a4`
- 担当要求: catalog

POST /students/optionsの宣言は残るが、現行本体はNotFoundを返す。候補取得機能の稼働入口として数えない。

- 原文根拠: [Web/Controllers/StudentsController.cs:5\-6](../../srcs/CSharp_ASPNET/Web/Controllers/StudentsController.cs#L5)<br>[Web/Controllers/StudentsController.cs:27\-28](../../srcs/CSharp_ASPNET/Web/Controllers/StudentsController.cs#L27)

### 学生検索画面と結果操作入口

- ID: `ENTRY\-0685f475cf01843c`
- 担当要求: catalog

認証付きGET /students、POST /students/search、/students/page、/students/clear。検索・結果操作と保守対象選択で共有するMVC入口。

- 原文根拠: [Web/Controllers/StudentsController.cs:5\-26](../../srcs/CSharp_ASPNET/Web/Controllers/StudentsController.cs#L5)<br>[Views/Students/Search.cshtml:14\-77](../../srcs/CSharp_ASPNET/Views/Students/Search.cshtml#L14)

### 学生論理削除入口

- ID: `ENTRY\-bb761d73375a1900`
- 担当要求: catalog

認証付きPOST /students/\{id:long\}/delete。対象版・理由・確認情報・編集状態を受け付ける。

- 原文根拠: [Web/Controllers/StudentsController.cs:5\-6](../../srcs/CSharp_ASPNET/Web/Controllers/StudentsController.cs#L5)<br>[Web/Controllers/StudentsController.cs:43\-43](../../srcs/CSharp_ASPNET/Web/Controllers/StudentsController.cs#L43)<br>[Web/Inputs/StudentDeleteInput.cs:3\-4](../../srcs/CSharp_ASPNET/Web/Inputs/StudentDeleteInput.cs#L3)

### 学生詳細・更新・入力復元入口

- ID: `ENTRY\-2775c8d43391475a`
- 担当要求: catalog

認証付きGET /students/\{id:long\}、POST /students/\{id:long\}/update、POST /students/reset。詳細照会と編集の文脈で共有する。

- 原文根拠: [Web/Controllers/StudentsController.cs:5\-6](../../srcs/CSharp_ASPNET/Web/Controllers/StudentsController.cs#L5)<br>[Web/Controllers/StudentsController.cs:30\-31](../../srcs/CSharp_ASPNET/Web/Controllers/StudentsController.cs#L30)<br>[Web/Controllers/StudentsController.cs:33\-41](../../srcs/CSharp_ASPNET/Web/Controllers/StudentsController.cs#L33)

### 学生新規画面・登録入口

- ID: `ENTRY\-04f7cce92fae19d2`
- 担当要求: catalog

認証付きGET /students/new と POST /students/create。新規入力と保存を受け付ける。

- 原文根拠: [Web/Controllers/StudentsController.cs:5\-6](../../srcs/CSharp_ASPNET/Web/Controllers/StudentsController.cs#L5)<br>[Web/Controllers/StudentsController.cs:29\-32](../../srcs/CSharp_ASPNET/Web/Controllers/StudentsController.cs#L29)<br>[Views/Students/Edit.cshtml:54\-62](../../srcs/CSharp_ASPNET/Views/Students/Edit.cshtml#L54)

### Web起動とルート転送

- ID: `ENTRY\-4301bebb19454b0d`
- 担当要求: catalog

Program.csがWebホスト設定を呼び出し、MVCコントローラーを公開する。GET / は /students へ転送する。

- 原文根拠: [Program.cs:1\-9](../../srcs/CSharp_ASPNET/Program.cs#L1)<br>[Properties/launchSettings.json:1\-1](../../srcs/CSharp_ASPNET/Properties/launchSettings.json#L1)<br>[appsettings.json:1\-1](../../srcs/CSharp_ASPNET/appsettings.json#L1)


## 運用・開発支援

### Azure配備・DB適応・認証設定支援

- ID: `SUPPORT\-b57fe43da2e3c329`
- 担当要求: catalog

Azure資源準備、公開、DB初期化・DDL適応、Web認証設定、資格情報取得補助を記述する。Initialize\-AzureDatabase.pyは基礎DDLの一部コード列幅とseed照合順序を適応する。これらはWeb本体から除外された配備資源。資格情報実体や外部配備状態は取得していない。

- 原文根拠: [deployment/Configure\-AzureDatabase.ps1:1\-42](../../srcs/CSharp_ASPNET/deployment/Configure-AzureDatabase.ps1#L1)<br>[deployment/Configure\-AzureWebLogin.ps1:1\-30](../../srcs/CSharp_ASPNET/deployment/Configure-AzureWebLogin.ps1#L1)<br>[deployment/Get\-AzureDatabaseLogin.ps1:1\-6](../../srcs/CSharp_ASPNET/deployment/Get-AzureDatabaseLogin.ps1#L1)<br>[deployment/Get\-AzureWebLogin.ps1:1\-7](../../srcs/CSharp_ASPNET/deployment/Get-AzureWebLogin.ps1#L1)<br>[deployment/Initialize\-AzureDatabase.py:1\-145](../../srcs/CSharp_ASPNET/deployment/Initialize-AzureDatabase.py#L1)<br>[deployment/LoginPasswordHash/LoginPasswordHash.csproj:1\-4](../../srcs/CSharp_ASPNET/deployment/LoginPasswordHash/LoginPasswordHash.csproj#L1)<br>[deployment/LoginPasswordHash/Program.cs:4\-9](../../srcs/CSharp_ASPNET/deployment/LoginPasswordHash/Program.cs#L4)<br>[deployment/Provision\-FreeAzure.ps1:1\-49](../../srcs/CSharp_ASPNET/deployment/Provision-FreeAzure.ps1#L1)<br>[deployment/Publish\-FreeAzure.ps1:1\-44](../../srcs/CSharp_ASPNET/deployment/Publish-FreeAzure.ps1#L1)<br>[StudentManagement.Web.csproj:4\-4](../../srcs/CSharp_ASPNET/StudentManagement.Web.csproj#L4)

### 配備DB・ログイン検証ソース

- ID: `SUPPORT\-5b71f5e0a4042846`
- 担当要求: catalog

DatabaseSmoke、Verify\-AzureRemoteDatabase.py、Verify\-AzureWebLogin.pyはDB読取と配備Web認証の検査資源。後者には現行検索画面に存在しないSRC\-009への検査参照もあり、試験コードや説明資料の成功記載を現行動作の証明にしない。

- 原文根拠: [deployment/DatabaseSmoke/DatabaseSmoke.csproj:1\-4](../../srcs/CSharp_ASPNET/deployment/DatabaseSmoke/DatabaseSmoke.csproj#L1)<br>[deployment/DatabaseSmoke/Program.cs:3\-9](../../srcs/CSharp_ASPNET/deployment/DatabaseSmoke/Program.cs#L3)<br>[deployment/Verify\-AzureRemoteDatabase.py:1\-35](../../srcs/CSharp_ASPNET/deployment/Verify-AzureRemoteDatabase.py#L1)<br>[deployment/Verify\-AzureWebLogin.py:1\-88](../../srcs/CSharp_ASPNET/deployment/Verify-AzureWebLogin.py#L1)<br>[Views/Students/Search.cshtml:25\-44](../../srcs/CSharp_ASPNET/Views/Students/Search.cshtml#L25)

### プロジェクト構成・ビルド出力・試験支援

- ID: `SUPPORT\-4eb23465d0e61571`
- 担当要求: catalog

Web/Core/CLIのプロジェクト参照、出力配置、除外規則、ビルド・出力パス検査を定義する。WebはCoreを参照し、deployment・maintenance・tests等を自身のコンパイルから除外する。solutionとbuild\_configは省略された試験プロジェクトを明示する。.tmp、build、bin、obj等は出力・既定項目除外として裏付けられ、取得原文に欠落先を要求する独自の本番生成Compile/Importは確認しない。省略物の内容・試験結果は未確認。

- 原文根拠: [Core/Properties/AssemblyInfo.cs:1\-2](../../srcs/CSharp_ASPNET/Core/Properties/AssemblyInfo.cs#L1)<br>[Core/StudentManagement.Core.csproj:1\-12](../../srcs/CSharp_ASPNET/Core/StudentManagement.Core.csproj#L1)<br>[Directory.Build.props:1\-15](../../srcs/CSharp_ASPNET/Directory.Build.props#L1)<br>[StudentManagement.Web.csproj:1\-7](../../srcs/CSharp_ASPNET/StudentManagement.Web.csproj#L1)<br>[StudentManagement.slnx:1\-8](../../srcs/CSharp_ASPNET/StudentManagement.slnx#L1)<br>[maintenance/StudentMaintenance.csproj:1\-4](../../srcs/CSharp_ASPNET/maintenance/StudentMaintenance.csproj#L1)<br>[build\_paths.py:1\-110](../../srcs/CSharp_ASPNET/build_paths.py#L1)<br>[tools/build.py:1\-101](../../srcs/CSharp_ASPNET/tools/build.py#L1)<br>[tools/build\_config.json:1\-19](../../srcs/CSharp_ASPNET/tools/build_config.json#L1)<br>[tools/test\_output\_paths.py:1\-153](../../srcs/CSharp_ASPNET/tools/test_output_paths.py#L1)

### DDL・seed生成器

- ID: `SUPPORT\-4b345e7a8685459f`
- 担当要求: catalog

database/generate.mjsは別パスの仕様資料からDDLとseedを生成する著作済み支援スクリプト。現存DDLは直接取得され、プロジェクト・build.pyに生成器の実行登録は見られない。参照仕様は本解析で取得せず、生成・整合性の成功も推定しない。

- 原文根拠: [database/generate.mjs:1\-110](../../srcs/CSharp_ASPNET/database/generate.mjs#L1)<br>[StudentManagement.Web.csproj:1\-7](../../srcs/CSharp_ASPNET/StudentManagement.Web.csproj#L1)<br>[tools/build.py:66\-88](../../srcs/CSharp_ASPNET/tools/build.py#L66)

### DB初期値・権限・導入検証支援

- ID: `SUPPORT\-0c685af40a8dfa8b`
- 担当要求: catalog

002\_seed、003\_web\_permissions、004\_verify\_deploymentとDeploy\-Database.ps1が初期コード、DB役割権限、導入・読取検証を記述する。これは配備支援であり、実DBの作成・権限・検証成功の証拠ではない。DDL末尾の別Native用EXEC入口への言及も現行登録とは区別する。

- 原文根拠: [database/002\_seed.sql:1\-93](../../srcs/CSharp_ASPNET/database/002_seed.sql#L1)<br>[database/003\_web\_permissions.sql:1\-26](../../srcs/CSharp_ASPNET/database/003_web_permissions.sql#L1)<br>[database/004\_verify\_deployment.sql:1\-135](../../srcs/CSharp_ASPNET/database/004_verify_deployment.sql#L1)<br>[database/Deploy\-Database.ps1:1\-165](../../srcs/CSharp_ASPNET/database/Deploy-Database.ps1#L1)<br>[database/001\_schema.sql:212\-218](../../srcs/CSharp_ASPNET/database/001_schema.sql#L212)

### 静的利用を観測しないStrictJson宣言

- ID: `SUPPORT\-48dbec518cb6c37c`
- 担当要求: catalog

StrictJsonはJSON本文の読取・構造確認を実装する。取得全ソース、呼出Fact、ホスト登録とコントローラーを逆照合した範囲ではReadへの外部静的利用を観測しない。動的利用の不存在や実行不能までは断定せず、共通消費者を作らず支援宣言として保持する。

- 原文根拠: [Infrastructure/StrictJson.cs:4\-15](../../srcs/CSharp_ASPNET/Infrastructure/StrictJson.cs#L4)<br>[Infrastructure/WebHostSetup.cs:13\-34](../../srcs/CSharp_ASPNET/Infrastructure/WebHostSetup.cs#L13)<br>[StudentManagement.Web.csproj:1\-7](../../srcs/CSharp_ASPNET/StudentManagement.Web.csproj#L1)

### 公開接続を観測しない候補・JSON整形宣言

- ID: `SUPPORT\-b5da89b9e6965423`
- 担当要求: catalog

WebStudentCoordinator.Options、OptionsRequest、WebPresentation.Lookups/Save等の宣言が残る。取得全ソース・呼出・登録ではOptionsを公開する現行入口やSave整形の静的消費者を観測せず、旧/students/optionsはNotFoundである。これらから稼働業務APIや新しい主機能を作らない。

- 原文根拠: [Infrastructure/WebStudentCoordinator.cs:21\-21](../../srcs/CSharp_ASPNET/Infrastructure/WebStudentCoordinator.cs#L21)<br>[Infrastructure/WebPresentation.cs:8\-19](../../srcs/CSharp_ASPNET/Infrastructure/WebPresentation.cs#L8)<br>[Infrastructure/WebPresentation.cs:30\-30](../../srcs/CSharp_ASPNET/Infrastructure/WebPresentation.cs#L30)<br>[Web/Inputs/StudentSearchInput.cs:20\-21](../../srcs/CSharp_ASPNET/Web/Inputs/StudentSearchInput.cs#L20)<br>[Web/Controllers/StudentsController.cs:5\-6](../../srcs/CSharp_ASPNET/Web/Controllers/StudentsController.cs#L5)<br>[Web/Controllers/StudentsController.cs:27\-28](../../srcs/CSharp_ASPNET/Web/Controllers/StudentsController.cs#L27)<br>[Program.cs:2\-8](../../srcs/CSharp_ASPNET/Program.cs#L2)<br>[Infrastructure/WebHostSetup.cs:25\-34](../../srcs/CSharp_ASPNET/Infrastructure/WebHostSetup.cs#L25)


## 資料

### 取得済み説明・運用資料

- ID: `MATERIAL\-c3c21708595fbdbc`
- 担当要求: catalog

README群はシステム利用、DB導入、Azure配備、保守CLIを説明する資料。外部仕様へのリンクは辿らず、記載された試験件数・配備成功・過去の利用者指示は未検証の説明として扱い、本解析の実行証拠・承認にはしない。

- 原文根拠: [README.md:1\-58](../../srcs/CSharp_ASPNET/README.md#L1)<br>[database/EXPRESS17.md:1\-51](../../srcs/CSharp_ASPNET/database/EXPRESS17.md#L1)<br>[database/README.md:1\-14](../../srcs/CSharp_ASPNET/database/README.md#L1)<br>[deployment/README.md:1\-51](../../srcs/CSharp_ASPNET/deployment/README.md#L1)<br>[maintenance/README.md:1\-11](../../srcs/CSharp_ASPNET/maintenance/README.md#L1)


## 外部依存

### .NET・ASP.NET Core・SQLクライアント等

- ID: `DEPENDENCY\-efa67ec550e3ac32`
- 担当要求: catalog

プロジェクトはnet10.0を対象とし、CoreはMicrosoft.Data.SqlClient 6.1.3とSystem.Security.Cryptography.Pkcs 9.0.21を参照する。ASP.NET Core Identity/Cookie機構を利用し、packages.lock.jsonは推移依存も記録する。パッケージ復元・導入状態は未確認。

- 原文根拠: [Core/StudentManagement.Core.csproj:1\-12](../../srcs/CSharp_ASPNET/Core/StudentManagement.Core.csproj#L1)<br>[StudentManagement.Web.csproj:1\-3](../../srcs/CSharp_ASPNET/StudentManagement.Web.csproj#L1)<br>[deployment/LoginPasswordHash/LoginPasswordHash.csproj:1\-4](../../srcs/CSharp_ASPNET/deployment/LoginPasswordHash/LoginPasswordHash.csproj#L1)<br>[packages.lock.json:1\-201](../../srcs/CSharp_ASPNET/packages.lock.json#L1)<br>[Core/SqlServerStudentService.cs:7\-7](../../srcs/CSharp_ASPNET/Core/SqlServerStudentService.cs#L7)<br>[Infrastructure/LocalLogin.cs:5\-7](../../srcs/CSharp_ASPNET/Infrastructure/LocalLogin.cs#L5)


## 分類保留


## 未確認・追加調査

### 実際の起動環境でLocalLoginとDB接続がどう設定され、各条件付き入口が到達可能になるかは未確認。

- ID: `0f9f112700bf4d02b31ee146974ba652:U\-CATALOG\-CONFIG\-001`
- 関連要求: catalog、relationships、behavior
- 範囲理由: 取得設定ではローカル認証は無効、DB接続は未設定であり、配備スクリプトは設定方法を示すだけ。条件付き機能のソース上の存在・分類は支持されるため目録を阻害しない。
- 独立判定: non\-blocking / 実環境設定と到達可能性は未確認のまま保持する。原目標は選択ソースの静的確認であり、既定設定、条件付きログイン・評価入口、DB登録は原文で区別できるため、実設定の取得は目録や静的解析の前提ではない。
- 阻害する要求: —
- 判定根拠: [appsettings.json:1\-1](../../srcs/CSharp_ASPNET/appsettings.json#L1)<br>[Web/Controllers/AccountController.cs:10\-34](../../srcs/CSharp_ASPNET/Web/Controllers/AccountController.cs#L10)<br>[Infrastructure/WebHostSetup.cs:23\-31](../../srcs/CSharp_ASPNET/Infrastructure/WebHostSetup.cs#L23)

### 実環境に適用された物理定義は基礎DDLか、Initialize\-AzureDatabase.pyの列幅・照合順序適応後の定義か。また各検証ソースは現行画面・DBに対して成立するか。

- ID: `0f9f112700bf4d02b31ee146974ba652:U\-DEPLOYED\-SCHEMA\-001`
- 関連要求: relationships、behavior
- 範囲理由: 両定義経路と検証コードの差は原文で観測できるが、実環境・実行結果は取得していない。表の同一性と目録分類は変わらないが、実際の物理制約・配備動作について一方を確定するには不足する。
- 独立判定: non\-blocking / 実適用定義と検証実行の成否は未解決である。基礎DDL、配備時適応、古い画面検査参照を別々に保持しており、表の同一性や主機能数は変わらない。原目標はソースの関係・動作確認なので、後続で両経路を解析する義務は残すが、実環境の一方を確定することを静的解析の阻害条件とはしない。
- 阻害する要求: —
- 判定根拠: [database/001\_schema.sql:15\-31](../../srcs/CSharp_ASPNET/database/001_schema.sql#L15)<br>[deployment/Initialize\-AzureDatabase.py:12\-30](../../srcs/CSharp_ASPNET/deployment/Initialize-AzureDatabase.py#L12)<br>[deployment/Initialize\-AzureDatabase.py:117\-135](../../srcs/CSharp_ASPNET/deployment/Initialize-AzureDatabase.py#L117)<br>[deployment/Verify\-AzureWebLogin.py:51\-58](../../srcs/CSharp_ASPNET/deployment/Verify-AzureWebLogin.py#L51)<br>[Views/Students/Search.cshtml:25\-44](../../srcs/CSharp_ASPNET/Views/Students/Search.cshtml#L25)

### t\_runtime\_stateを利用する実装、非Web確認表分岐の起動主体、コメントにある別Native用student\_api入口の適用関係は何か。

- ID: `0f9f112700bf4d02b31ee146974ba652:U\-STATE\-PROFILE\-001`
- 関連要求: relationships、behavior
- 範囲理由: 物理表と非Web分岐は取得原文にある一方、Web・配備検査はwebTokens=trueを明示し、取得プロジェクトと登録に別Native入口はない。コメントだけで入口を追加せず、対象表と宣言を保持したまま未確認とする。
- 独立判定: non\-blocking / 別Native実装と非Web分岐の起動主体は未確認として残す。取得プロジェクト・登録ではWebと検査がメモリー確認方式を選び、状態ストアもメモリー実装である。表と非Web分岐を保持した静的目録に、別方式へのコメントだけから追加機能を要求する根拠はない。
- 阻害する要求: —
- 判定根拠: [StudentManagement.slnx:1\-8](../../srcs/CSharp_ASPNET/StudentManagement.slnx#L1)<br>[Infrastructure/WebHostSetup.cs:17\-23](../../srcs/CSharp_ASPNET/Infrastructure/WebHostSetup.cs#L17)<br>[deployment/DatabaseSmoke/Program.cs:4\-7](../../srcs/CSharp_ASPNET/deployment/DatabaseSmoke/Program.cs#L4)<br>[Infrastructure/SearchContextStore.cs:7\-17](../../srcs/CSharp_ASPNET/Infrastructure/SearchContextStore.cs#L7)<br>[Core/SqlServerStudentService.cs:322\-335](../../srcs/CSharp_ASPNET/Core/SqlServerStudentService.cs#L322)<br>[database/001\_schema.sql:170\-184](../../srcs/CSharp_ASPNET/database/001_schema.sql#L170)<br>[database/001\_schema.sql:212\-217](../../srcs/CSharp_ASPNET/database/001_schema.sql#L212)

### StrictJson.Read、WebStudentCoordinator.Options、WebPresentation.Save等に、取得原文から見えない動的な利用があるか。

- ID: `0f9f112700bf4d02b31ee146974ba652:U\-STATIC\-CONSUMERS\-001`
- 関連要求: relationships、behavior
- 範囲理由: 取得全ソース・呼出表・登録点の逆照合では外部静的利用を観測しない。既知宣言を支援資源として保持しており、現在の目録対象や主機能数はこの実行時不確実性に依存しない。
- 独立判定: non\-blocking / 動的利用の有無は解決していない。全原文の逆参照と登録では対象宣言への公開接続を観測せず、旧候補入口はNotFoundである。原目標の静的範囲では宣言を保持して接続を未確認とする判断が可能で、機能数を左右する現行登録の欠落は認めない。
- 阻害する要求: —
- 判定根拠: [Infrastructure/StrictJson.cs:4\-15](../../srcs/CSharp_ASPNET/Infrastructure/StrictJson.cs#L4)<br>[Infrastructure/WebStudentCoordinator.cs:21\-24](../../srcs/CSharp_ASPNET/Infrastructure/WebStudentCoordinator.cs#L21)<br>[Infrastructure/WebPresentation.cs:24\-30](../../srcs/CSharp_ASPNET/Infrastructure/WebPresentation.cs#L24)<br>[Web/Controllers/StudentsController.cs:27\-46](../../srcs/CSharp_ASPNET/Web/Controllers/StudentsController.cs#L27)<br>[Program.cs:3\-7](../../srcs/CSharp_ASPNET/Program.cs#L3)

## 独立検証

### 要求

| 対象 | 判定 | 理由・原文根拠 |
| --- | --- | --- |
| catalog | pass | 提示原文全体を登録、画面、呼出元、プロジェクト構成、生成参照と照合した。概要、主機能6件、操作、入口、7物理表、データ契約、共通責任、支援資源の分類・集計を支持する。relationshipsとbehaviorは未検証の義務として残り、実行結果や受入を認定しない。<br>[Program.cs:2\-8](../../srcs/CSharp_ASPNET/Program.cs#L2)<br>[Infrastructure/WebHostSetup.cs:13\-33](../../srcs/CSharp_ASPNET/Infrastructure/WebHostSetup.cs#L13)<br>[Web/Controllers/AccountController.cs:10\-41](../../srcs/CSharp_ASPNET/Web/Controllers/AccountController.cs#L10)<br>[Web/Controllers/StudentsController.cs:5\-46](../../srcs/CSharp_ASPNET/Web/Controllers/StudentsController.cs#L5)<br>[maintenance/Program.cs:4\-17](../../srcs/CSharp_ASPNET/maintenance/Program.cs#L4)<br>[database/001\_schema.sql:7\-184](../../srcs/CSharp_ASPNET/database/001_schema.sql#L7)<br>[StudentManagement.Web.csproj:1\-7](../../srcs/CSharp_ASPNET/StudentManagement.Web.csproj#L1)<br>[database/generate.mjs:6\-21](../../srcs/CSharp_ASPNET/database/generate.mjs#L6) |

### 範囲

| 対象 | 判定 | 理由・原文根拠 |
| --- | --- | --- |
| selected\-system | pass | 全75資源を登録点・逆利用・プロジェクト所属・除外・生成参照から確認した。独立ログインとCLIマスタ業務は主機能に残り、リンクだけのメニュー、存活応答、配備・検査は適切に別保持される。省略先は試験または出力資源として裏付けられ、欠落した現行本番include/importは観測しない。未確認事項は静的範囲の対象・主機能数を変更する保留ではない。<br>[Program.cs:2\-8](../../srcs/CSharp_ASPNET/Program.cs#L2)<br>[Infrastructure/WebHostSetup.cs:13\-33](../../srcs/CSharp_ASPNET/Infrastructure/WebHostSetup.cs#L13)<br>[Web/Controllers/AccountController.cs:10\-41](../../srcs/CSharp_ASPNET/Web/Controllers/AccountController.cs#L10)<br>[Views/Menu/Index.cshtml:1\-7](../../srcs/CSharp_ASPNET/Views/Menu/Index.cshtml#L1)<br>[Web/Controllers/StudentsController.cs:5\-46](../../srcs/CSharp_ASPNET/Web/Controllers/StudentsController.cs#L5)<br>[maintenance/Program.cs:4\-17](../../srcs/CSharp_ASPNET/maintenance/Program.cs#L4)<br>[StudentManagement.Web.csproj:3\-6](../../srcs/CSharp_ASPNET/StudentManagement.Web.csproj#L3)<br>[StudentManagement.slnx:2\-7](../../srcs/CSharp_ASPNET/StudentManagement.slnx#L2)<br>[Directory.Build.props:4\-13](../../srcs/CSharp_ASPNET/Directory.Build.props#L4)<br>[database/generate.mjs:6\-21](../../srcs/CSharp_ASPNET/database/generate.mjs#L6)<br>[tools/build.py:66\-88](../../srcs/CSharp_ASPNET/tools/build.py#L66)<br>[tools/build\_config.json:1\-19](../../srcs/CSharp_ASPNET/tools/build_config.json#L1) |

### 分類

| 対象 | 判定 | 理由・原文根拠 |
| --- | --- | --- |
| ログイン (`FUNCTION-3a8a1be5f76f61aa`) | pass | 設定利用者が専用フォームから認証し、セッション開始または失敗通知を得る独立目的がある。認証共通実装だけへ吸収せず主機能として保持する分類を支持する。<br>[Views/Account/Login.cshtml:2\-12](../../srcs/CSharp_ASPNET/Views/Account/Login.cshtml#L2)<br>[Web/Controllers/AccountController.cs:10\-34](../../srcs/CSharp_ASPNET/Web/Controllers/AccountController.cs#L10) |
| ログアウト (`FUNCTION-02c59fd1943df269`) | pass | 認証済み利用者が各画面からセッション終了を要求し、サインアウト結果を得る。ログインへの統合も可能だが、独立した退出目的による分離は過分割に当たらない。<br>[Views/Shared/\_Layout.cshtml:2\-4](../../srcs/CSharp_ASPNET/Views/Shared/_Layout.cshtml#L2)<br>[Web/Controllers/AccountController.cs:36\-41](../../srcs/CSharp_ASPNET/Web/Controllers/AccountController.cs#L36) |
| 学生検索・照会 (`FUNCTION-95e69c5434befaad`) | pass | 参照利用者を含む利用者が学生情報を調べ、一覧・件数・詳細を得る独立照会である。保守対象選択への全面的な統合は参照目的を失うため、主機能として妥当。<br>[Views/Students/Search.cshtml:25\-76](../../srcs/CSharp_ASPNET/Views/Students/Search.cshtml#L25)<br>[Infrastructure/WebStudentCoordinator.cs:7\-14](../../srcs/CSharp_ASPNET/Infrastructure/WebStudentCoordinator.cs#L7)<br>[Web/Models/StudentEditPageModel.cs:8\-14](../../srcs/CSharp_ASPNET/Web/Models/StudentEditPageModel.cs#L8) |
| 学生情報登録・保守 (`FUNCTION-fa89f6d82503c20f`) | pass | 職員・管理者が学生台帳を登録・維持し、保存・論理削除等の結果を得る。新規・更新・削除は同じ対象と編集作業に置かれ、別主機能への細分化を必須とする独立工程は原文にない。<br>[Views/Students/Edit.cshtml:37\-62](../../srcs/CSharp_ASPNET/Views/Students/Edit.cshtml#L37)<br>[Views/Students/Edit.cshtml:143\-176](../../srcs/CSharp_ASPNET/Views/Students/Edit.cshtml#L143)<br>[Web/Controllers/StudentsController.cs:29\-44](../../srcs/CSharp_ASPNET/Web/Controllers/StudentsController.cs#L29)<br>[Infrastructure/WebStudentCoordinator.cs:23\-24](../../srcs/CSharp_ASPNET/Infrastructure/WebStudentCoordinator.cs#L23) |
| クラスマスタ保守 (`FUNCTION-91d28046181a5fb5`) | pass | DB管理者がclass入力で年度・所属・定員を持つクラスを整備し、保存結果を得る完全なCLI作業である。コード保守との入口共用だけで統合せず、独立した業務対象による主機能分類を支持する。<br>[maintenance/Program.cs:4\-16](../../srcs/CSharp_ASPNET/maintenance/Program.cs#L4)<br>[Core/MasterMaintenanceService.cs:17\-37](../../srcs/CSharp_ASPNET/Core/MasterMaintenanceService.cs#L17)<br>[Core/MasterMaintenanceService.cs:65\-76](../../srcs/CSharp_ASPNET/Core/MasterMaintenanceService.cs#L65)<br>[maintenance/StudentMaintenance.csproj:1\-4](../../srcs/CSharp_ASPNET/maintenance/StudentMaintenance.csproj#L1) |
| 業務コードマスタ保守 (`FUNCTION-22591896d39dca6b`) | pass | DB管理者がcode入力で分類別コードを維持し、保存結果を得る。クラスとは入力契約・対象・整合性責任が異なり、共通CLI単位にまとめるより別主機能として説明できる。<br>[maintenance/Program.cs:10\-16](../../srcs/CSharp_ASPNET/maintenance/Program.cs#L10)<br>[Core/MasterMaintenanceService.cs:17\-29](../../srcs/CSharp_ASPNET/Core/MasterMaintenanceService.cs#L17)<br>[Core/MasterMaintenanceService.cs:79\-120](../../srcs/CSharp_ASPNET/Core/MasterMaintenanceService.cs#L79) |
| 検索結果の表示操作・条件クリア (`OPERATION-ae1e266eec14c5f8`) | pass | ページ・表示順変更と条件クリアはfunction.student\-query内の閲覧・再指定作業であり、独立分析機能へ昇格させない親子関係が妥当。<br>[Views/Students/Search.cshtml:45\-71](../../srcs/CSharp_ASPNET/Views/Students/Search.cshtml#L45)<br>[Web/Controllers/StudentsController.cs:23\-26](../../srcs/CSharp_ASPNET/Web/Controllers/StudentsController.cs#L23) |
| 学生詳細参照 (`OPERATION-05a23e427d16ab97`) | pass | 一覧で選択した学生を共用フォームの参照モードで確認するfunction.student\-queryの工程である。詳細ページだけを別主機能に数えない分類を支持する。<br>[Views/Students/Search.cshtml:63\-66](../../srcs/CSharp_ASPNET/Views/Students/Search.cshtml#L63)<br>[Views/Students/Edit.cshtml:37\-44](../../srcs/CSharp_ASPNET/Views/Students/Edit.cshtml#L37)<br>[Infrastructure/WebStudentCoordinator.cs:22\-22](../../srcs/CSharp_ASPNET/Infrastructure/WebStudentCoordinator.cs#L22) |
| 保守対象の検索・選択 (`OPERATION-fe8ffc62b1bb2dc5`) | pass | 職員等が検索結果から編集対象を選ぶ用途はfunction.student\-maintainの準備工程である。独立照会と共有する入口を重複した主機能にせず、利用文脈として保持している。<br>[Views/Students/Search.cshtml:63\-66](../../srcs/CSharp_ASPNET/Views/Students/Search.cshtml#L63)<br>[Web/Controllers/StudentsController.cs:30\-31](../../srcs/CSharp_ASPNET/Web/Controllers/StudentsController.cs#L30) |
| 学生新規入力・登録 (`OPERATION-4100b273ea61d3aa`) | pass | 新規入力と登録はfunction.student\-maintainの新規モードであり、既存編集と共用するフォーム・保存作業を踏まえた操作分類が妥当。<br>[Views/Students/Edit.cshtml:54\-62](../../srcs/CSharp_ASPNET/Views/Students/Edit.cshtml#L54)<br>[Views/Students/Edit.cshtml:143\-145](../../srcs/CSharp_ASPNET/Views/Students/Edit.cshtml#L143)<br>[Web/Controllers/StudentsController.cs:29\-36](../../srcs/CSharp_ASPNET/Web/Controllers/StudentsController.cs#L29) |
| 学生既存情報の編集・更新 (`OPERATION-2b805dc211d38474`) | pass | 既存学生を読み込み変更保存する作業はfunction.student\-maintainの既存対象モードである。新規と別の独立工程を示す根拠がなく、操作としての統合を支持する。<br>[Web/Controllers/StudentsController.cs:30\-40](../../srcs/CSharp_ASPNET/Web/Controllers/StudentsController.cs#L30)<br>[Views/Students/Edit.cshtml:54\-62](../../srcs/CSharp_ASPNET/Views/Students/Edit.cshtml#L54)<br>[Views/Students/Edit.cshtml:143\-145](../../srcs/CSharp_ASPNET/Views/Students/Edit.cshtml#L143) |
| 重複候補の確認・続行 (`OPERATION-78354a05df977f3d`) | pass | 候補確認と理由付き続行は進行中の学生保存に従属し、function.student\-maintainを親とする。独立した重複統合・審査機能として分割する根拠はない。<br>[Views/Students/Edit.cshtml:151\-159](../../srcs/CSharp_ASPNET/Views/Students/Edit.cshtml#L151)<br>[Web/Controllers/StudentsController.cs:34\-39](../../srcs/CSharp_ASPNET/Web/Controllers/StudentsController.cs#L34)<br>[wwwroot/js/site.js:107\-114](../../srcs/CSharp_ASPNET/wwwroot/js/site.js#L107) |
| 学生の理由付き論理削除 (`OPERATION-469473adb2ab805e`) | pass | 管理者が編集対象を理由付きで論理削除する作業はfunction.student\-maintain内に置かれる。権限差や確認画面だけで独立廃棄業務へ分割せず、保守操作とする判断を支持する。<br>[Views/Students/Edit.cshtml:148\-173](../../srcs/CSharp_ASPNET/Views/Students/Edit.cshtml#L148)<br>[Infrastructure/WebStudentCoordinator.cs:24\-24](../../srcs/CSharp_ASPNET/Infrastructure/WebStudentCoordinator.cs#L24)<br>[Core/SqlServerStudentService.cs:384\-406](../../srcs/CSharp_ASPNET/Core/SqlServerStudentService.cs#L384) |
| 入力復元・再読込・変更破棄 (`OPERATION-cf27427be305dab3`) | pass | 入力復元、再読込、変更破棄はfunction.student\-maintainの作業制御である。取消・復帰という共通目的でまとめても独立した業務成果を隠していない。<br>[Views/Students/Edit.cshtml:145\-150](../../srcs/CSharp_ASPNET/Views/Students/Edit.cshtml#L145)<br>[Views/Students/Edit.cshtml:175\-175](../../srcs/CSharp_ASPNET/Views/Students/Edit.cshtml#L175)<br>[Web/Controllers/StudentsController.cs:41\-41](../../srcs/CSharp_ASPNET/Web/Controllers/StudentsController.cs#L41)<br>[wwwroot/js/site.js:139\-150](../../srcs/CSharp_ASPNET/wwwroot/js/site.js#L139) |
| 学生管理メニューのナビゲーション (`COMMON-a72f42829f3452d1`) | pass | メニューと検索画面のリンクは移動先選択を担う。メニュー自身の照会・集約結果はなく、主機能への昇格を避けて入口と共通ナビゲーションを残す分類が妥当。<br>[Views/Menu/Index.cshtml:1\-7](../../srcs/CSharp_ASPNET/Views/Menu/Index.cshtml#L1)<br>[Web/Controllers/MenuController.cs:6\-10](../../srcs/CSharp_ASPNET/Web/Controllers/MenuController.cs#L6)<br>[Views/Students/Search.cshtml:14\-18](../../srcs/CSharp_ASPNET/Views/Students/Search.cshtml#L14) |
| ローカル認証・Cookieセッション (`COMMON-d0315425c7b13a6b`) | pass | LocalLoginの認証・Cookie受入責任はAccountControllerとホストから消費される。独立ログイン・ログアウトを保持した上で中央実装を共通化しており、機能の埋没はない。<br>[Infrastructure/LocalLogin.cs:53\-89](../../srcs/CSharp_ASPNET/Infrastructure/LocalLogin.cs#L53)<br>[Web/Controllers/AccountController.cs:24\-40](../../srcs/CSharp_ASPNET/Web/Controllers/AccountController.cs#L24)<br>[Infrastructure/WebHostSetup.cs:15\-18](../../srcs/CSharp_ASPNET/Infrastructure/WebHostSetup.cs#L15) |
| 要求主体・役割・権限検査 (`COMMON-59b6d97bf7d6ea45`) | pass | 主体解釈・認可はRequestIdentityへ集中し、検索・保存・削除が利用する。個別処理への分散より中央責任としての共通分類が原文に合う。<br>[Infrastructure/RequestIdentity.cs:4\-16](../../srcs/CSharp_ASPNET/Infrastructure/RequestIdentity.cs#L4)<br>[Infrastructure/WebStudentCoordinator.cs:7\-24](../../srcs/CSharp_ASPNET/Infrastructure/WebStudentCoordinator.cs#L7) |
| Webホスト・要求保護・例外応答 (`COMMON-5e74be0106d52822`) | pass | 起動点が呼ぶ登録・ミドルウェア・CSRFフィルターは複数Web入口を一括保護する中央責任である。単なる配備資料への分類より共通処理として妥当。<br>[Program.cs:2\-6](../../srcs/CSharp_ASPNET/Program.cs#L2)<br>[Infrastructure/WebHostSetup.cs:13\-29](../../srcs/CSharp_ASPNET/Infrastructure/WebHostSetup.cs#L13)<br>[Infrastructure/AntiforgeryResultFilter.cs:5\-9](../../srcs/CSharp_ASPNET/Infrastructure/AntiforgeryResultFilter.cs#L5) |
| 学生Web操作の調停 (`COMMON-7739e9983ee40d19`) | pass | 検索・編集・保存・削除の入口が同じ調停クラスを消費する。業務主機能を残しながら主体・状態・サービス接続を共通責任として分離する判断を支持する。<br>[Infrastructure/WebStudentCoordinator.cs:3\-24](../../srcs/CSharp_ASPNET/Infrastructure/WebStudentCoordinator.cs#L3)<br>[Web/Controllers/StudentsController.cs:18\-18](../../srcs/CSharp_ASPNET/Web/Controllers/StudentsController.cs#L18)<br>[Web/Controllers/StudentsController.cs:29\-43](../../srcs/CSharp_ASPNET/Web/Controllers/StudentsController.cs#L29) |
| 学生業務ルール・SQLサービス (`COMMON-3fcb61c6b12956ad`) | pass | 学生照会・保守を支えるSQLサービスはWeb登録、調停、配備検査から利用される中央実装である。各メソッドを主機能へ分割せず、利用者目的との二層を保つ分類が妥当。<br>[Infrastructure/WebHostSetup.cs:23\-23](../../srcs/CSharp_ASPNET/Infrastructure/WebHostSetup.cs#L23)<br>[Infrastructure/WebStudentCoordinator.cs:14\-24](../../srcs/CSharp_ASPNET/Infrastructure/WebStudentCoordinator.cs#L14)<br>[deployment/DatabaseSmoke/Program.cs:4\-7](../../srcs/CSharp_ASPNET/deployment/DatabaseSmoke/Program.cs#L4)<br>[Core/SqlServerStudentService.cs:384\-406](../../srcs/CSharp_ASPNET/Core/SqlServerStudentService.cs#L384) |
| マスタ保守ルール・DB管理者確認 (`COMMON-d07c5cf8dcb72c73`) | pass | クラス・コード保守の双方が管理者確認と保存を担うサービスを利用する。両業務を主機能に残した共通実装の分類であり、管理業務を支援へ隠していない。<br>[maintenance/Program.cs:11\-13](../../srcs/CSharp_ASPNET/maintenance/Program.cs#L11)<br>[Core/MasterMaintenanceService.cs:17\-30](../../srcs/CSharp_ASPNET/Core/MasterMaintenanceService.cs#L17)<br>[Core/MasterMaintenanceService.cs:79\-90](../../srcs/CSharp_ASPNET/Core/MasterMaintenanceService.cs#L79) |
| 入力正規化・共通検証 (`COMMON-ac4e2446c323b378`) | pass | 入力表現・検証の責任は検索条件、学生保存、マスタ保守から共有される。学生登録だけの内部処理へまとめない共通分類を支持する。<br>[Core/StudentNormalizer.cs:47\-118](../../srcs/CSharp_ASPNET/Core/StudentNormalizer.cs#L47)<br>[Core/Contracts.cs:48\-56](../../srcs/CSharp_ASPNET/Core/Contracts.cs#L48)<br>[Core/MasterMaintenanceService.cs:33\-35](../../srcs/CSharp_ASPNET/Core/MasterMaintenanceService.cs#L33)<br>[Core/SqlServerStudentService.cs:225\-229](../../srcs/CSharp_ASPNET/Core/SqlServerStudentService.cs#L225) |
| 和暦・西暦・年度処理 (`COMMON-b89d8de2b7f2c5d8`) | pass | 日付解釈・和暦表現は学生正規化、マスタ入力、詳細変換、Web入力変換が共有する。画面専用部品へ限定せず共通日付責任とする分類が妥当。<br>[Core/JapaneseDateService.cs:17\-61](../../srcs/CSharp_ASPNET/Core/JapaneseDateService.cs#L17)<br>[Core/MasterMaintenanceService.cs:36\-36](../../srcs/CSharp_ASPNET/Core/MasterMaintenanceService.cs#L36)<br>[Core/StudentNormalizer.cs:127\-137](../../srcs/CSharp_ASPNET/Core/StudentNormalizer.cs#L127)<br>[Web/Inputs/StudentSaveInput.cs:44\-54](../../srcs/CSharp_ASPNET/Web/Inputs/StudentSaveInput.cs#L44) |
| SQL書込基盤・排他・監査 (`COMMON-f89bacb97f5450d5`) | pass | 両CoreサービスはSQL補助・書込ゲートを共用し、各保存で監査を記録する。補助・排他・監査への細分化も可能だが、目録上の書込基盤責任群としての統合は妥当。<br>[Core/SqlServerStudentService.cs:65\-102](../../srcs/CSharp_ASPNET/Core/SqlServerStudentService.cs#L65)<br>[Core/MasterMaintenanceService.cs:5\-5](../../srcs/CSharp_ASPNET/Core/MasterMaintenanceService.cs#L5)<br>[Core/MasterMaintenanceService.cs:74\-75](../../srcs/CSharp_ASPNET/Core/MasterMaintenanceService.cs#L74)<br>[Core/MasterMaintenanceService.cs:119\-135](../../srcs/CSharp_ASPNET/Core/MasterMaintenanceService.cs#L119)<br>[Core/SqlServerStudentService.cs:298\-299](../../srcs/CSharp_ASPNET/Core/SqlServerStudentService.cs#L298)<br>[Core/AuditOperation.cs:4\-7](../../srcs/CSharp_ASPNET/Core/AuditOperation.cs#L4) |
| Webの一時状態・編集スナップショット・通知 (`COMMON-4485a90fc273e866`) | pass | 検索、編集、保存後復帰が一時状態ストア群を消費し、認証もトークン生成を利用する。ストア別分割も可能だが、物理表と区別したWeb作業状態責任としての統合を支持する。<br>[Infrastructure/SearchContextStore.cs:7\-17](../../srcs/CSharp_ASPNET/Infrastructure/SearchContextStore.cs#L7)<br>[Infrastructure/EditorSnapshotStore.cs:5\-11](../../srcs/CSharp_ASPNET/Infrastructure/EditorSnapshotStore.cs#L5)<br>[Infrastructure/FlashMessageStore.cs:4\-9](../../srcs/CSharp_ASPNET/Infrastructure/FlashMessageStore.cs#L4)<br>[Web/Controllers/StudentsController.cs:31\-44](../../srcs/CSharp_ASPNET/Web/Controllers/StudentsController.cs#L31)<br>[Infrastructure/LocalLogin.cs:73\-79](../../srcs/CSharp_ASPNET/Infrastructure/LocalLogin.cs#L73) |
| Web結果・時刻・エラー整形 (`COMMON-a09fb8ca183e4bd5`) | pass | 時刻・一覧・エラー・HTTP状態の整形は調停、MVC、共通失敗応答から利用される。未接続の整形宣言を別保持した上で、実利用のある中央表示責任を共通化している。<br>[Infrastructure/WebPresentation.cs:3\-23](../../srcs/CSharp_ASPNET/Infrastructure/WebPresentation.cs#L3)<br>[Infrastructure/WebStudentCoordinator.cs:26\-27](../../srcs/CSharp_ASPNET/Infrastructure/WebStudentCoordinator.cs#L26)<br>[Web/Controllers/StudentsController.cs:38\-38](../../srcs/CSharp_ASPNET/Web/Controllers/StudentsController.cs#L38)<br>[Infrastructure/WebHostSetup.cs:27\-27](../../srcs/CSharp_ASPNET/Infrastructure/WebHostSetup.cs#L27) |
| 共通レイアウト・表示資源・画面操作 (`COMMON-6cb65166b395fdd5`) | pass | ViewStart、共通レイアウト、partial、CSS・JSの参照と画面属性が消費関係を示す。個別資源への細分化は可能だが、共通UI責任群へまとめても独立画面・業務成果を隠さない。<br>[Views/\_ViewStart.cshtml:1\-1](../../srcs/CSharp_ASPNET/Views/_ViewStart.cshtml#L1)<br>[Views/Shared/\_Layout.cshtml:1\-5](../../srcs/CSharp_ASPNET/Views/Shared/_Layout.cshtml#L1)<br>[Views/Students/Search.cshtml:19\-20](../../srcs/CSharp_ASPNET/Views/Students/Search.cshtml#L19)<br>[Views/Students/Edit.cshtml:143\-175](../../srcs/CSharp_ASPNET/Views/Students/Edit.cshtml#L143)<br>[wwwroot/js/site.js:2\-10](../../srcs/CSharp_ASPNET/wwwroot/js/site.js#L2)<br>[wwwroot/js/site.js:103\-150](../../srcs/CSharp_ASPNET/wwwroot/js/site.js#L103) |
| Web入力・識別番号・Core契約変換 (`COMMON-05007c9fc45349dd`) | pass | 検索・編集・保存・削除はWeb入力変換と識別番号解釈を利用する。型宣言だけでは表せない処理責任があり、データ契約と別の共通処理として保持する分類を支持する。<br>[Web/Inputs/StudentSaveInput.cs:34\-61](../../srcs/CSharp_ASPNET/Web/Inputs/StudentSaveInput.cs#L34)<br>[Web/Inputs/StudentSearchInput.cs:11\-12](../../srcs/CSharp_ASPNET/Web/Inputs/StudentSearchInput.cs#L11)<br>[Infrastructure/WebStudentCoordinator.cs:11\-11](../../srcs/CSharp_ASPNET/Infrastructure/WebStudentCoordinator.cs#L11)<br>[Infrastructure/WebStudentCoordinator.cs:22\-24](../../srcs/CSharp_ASPNET/Infrastructure/WebStudentCoordinator.cs#L22) |

### 事実利用

pass: 全Fact索引と原文・inventoryを照合し、候補の選択外も含め入口22件、CLI選択、未接続宣言、非対応言語資源を検討した。使用Factは対応する構文観測を支持し、業務境界・消費者・所属判断はフォーム、処理本体、登録、プロジェクト原文で補われる。ASTを意味束縛・実行証拠とする誤用や、目録を変えるFactの見落としは認めない。

[Program.cs:2\-8](../../srcs/CSharp_ASPNET/Program.cs#L2)<br>[Infrastructure/WebHostSetup.cs:17\-32](../../srcs/CSharp_ASPNET/Infrastructure/WebHostSetup.cs#L17)<br>[Web/Controllers/AccountController.cs:10\-41](../../srcs/CSharp_ASPNET/Web/Controllers/AccountController.cs#L10)<br>[Web/Controllers/StudentsController.cs:5\-46](../../srcs/CSharp_ASPNET/Web/Controllers/StudentsController.cs#L5)<br>[maintenance/Program.cs:4\-17](../../srcs/CSharp_ASPNET/maintenance/Program.cs#L4)<br>[Views/Students/Search.cshtml:45\-76](../../srcs/CSharp_ASPNET/Views/Students/Search.cshtml#L45)<br>[Views/Students/Edit.cshtml:143\-176](../../srcs/CSharp_ASPNET/Views/Students/Edit.cshtml#L143)<br>[Infrastructure/StrictJson.cs:4\-15](../../srcs/CSharp_ASPNET/Infrastructure/StrictJson.cs#L4)<br>[StudentManagement.Web.csproj:1\-7](../../srcs/CSharp_ASPNET/StudentManagement.Web.csproj#L1)<br>[database/001\_schema.sql:7\-184](../../srcs/CSharp_ASPNET/database/001_schema.sql#L7)<br>[deployment/Initialize\-AzureDatabase.py:12\-30](../../srcs/CSharp_ASPNET/deployment/Initialize-AzureDatabase.py#L12)<br>[database/generate.mjs:6\-21](../../srcs/CSharp_ASPNET/database/generate.mjs#L6)<br>[deployment/DatabaseSmoke/Program.cs:3\-9](../../srcs/CSharp_ASPNET/deployment/DatabaseSmoke/Program.cs#L3)<br>[deployment/LoginPasswordHash/Program.cs:4\-9](../../srcs/CSharp_ASPNET/deployment/LoginPasswordHash/Program.cs#L4)

### 検証指摘

指摘なし。
## 限界

構文事実は意味上の呼出先・実行時到達性・業務機能の正解を証明しない。
入力プログラム・SQL・DBを実行した結果ではない。主・子・共通の粒度と未解決事項を人手で確認する。
