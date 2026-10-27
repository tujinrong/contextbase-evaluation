# discovery-agent 分類結果レビュー

**新分類基準による再抽出・人手レビュー待ち。** 機能数を先に決めず、主機能、子操作、共通能力、技術入口等を分けて記録した。

| 項目 | 今回の結果 |
| --- | --- |
| 対象 | test-project1 / CSharp_ASPNET |
| 処理 | discoveryのみ。relationship／behaviorは未実行 |
| 分類ポリシー | contextbase-catalog/1 |
| ソース事実索引 | contextbase-source-facts/1・1747 facts |
| 事実利用の作者記録 | 69 records |
| ホスト採用 | 新候補を採用済み |
| 主機能 | 7 |
| 子操作 | 8 |
| 共通能力 | 15 |
| 分類保留 | 0 |
| 全記録 | 69 |
| 原文 | 75 files / 353907 bytes |
| 元ソース | 封印時と全ファイル同一 |
| snapshot SHA-256 | `774b5bcbe15ec413f574dabb88b4b98d00cf97901bc5e4c9af0efc0018200964` |
| 候補 SHA-256 | `9610e1b66fc86642754471027111beb58198b7a4c8ed2796f1f5e9a10314e50f` |

[機械可読成果](contextbase.json)

[ソース事実・技術入口のレビュー](facts/facts-review.md) / [完全な事実索引](facts/source-facts.json) / [機械検査](facts/validation.json)

## 集計範囲と機能領域

選択したソースから概要、業務機能、テーブル／データ、共通処理を整理し、関係と動作を原文根拠付きで確認する。仕様書は生成しない。

取得したプロジェクト全体とWebだけの集計範囲を混同しない。CLIの業務マスタ保守も、分類された領域として別に確認する。主機能数には子操作・共通・入口を含めない。

| 主機能の機能領域（業務・システム） | 件数 |
| --- | --- |
| システム認証 | 2 |
| システム機能選択 | 1 |
| 学生管理 | 2 |
| マスタ保守 | 2 |

## システム概要

### 学生管理システムのソース概要

.NET 10のASP.NET Core MVC、Razor、SQL Server用Coreと独立マスタ保守CLIを含む。分類済み主機能は7件：システム認証2件、機能選択1件、学生管理2件、マスタ保守2件。操作・共通処理・技術入口・データ・補助資源は別記録とした。

[Program.cs:2\-8](../../srcs/CSharp_ASPNET/Program.cs#L2)<br>[Infrastructure/WebHostSetup.cs:13\-24](../../srcs/CSharp_ASPNET/Infrastructure/WebHostSetup.cs#L13)<br>[StudentManagement.Web.csproj:1\-7](../../srcs/CSharp_ASPNET/StudentManagement.Web.csproj#L1)<br>[StudentManagement.slnx:1\-8](../../srcs/CSharp_ASPNET/StudentManagement.slnx#L1)<br>[maintenance/Program.cs:4\-17](../../srcs/CSharp_ASPNET/maintenance/Program.cs#L4)

### 取得範囲・解析限界・保留義務

C\# Factは構文観測であり意味束縛・実行到達性を保証しない。他形式は原文を確認した。Webの除外規則、Core参照、CLI、テスト設定、出力除外を確認した範囲で目録の分類保留候補はない。Native入口はコメント上の言及で、現行WebはSqlServerStudentServiceを登録する。relationshipsとbehaviorは後続確認のまま保持する。

[Core/SqlServerStudentService.cs:11\-13](../../srcs/CSharp_ASPNET/Core/SqlServerStudentService.cs#L11)<br>[Infrastructure/WebHostSetup.cs:23\-23](../../srcs/CSharp_ASPNET/Infrastructure/WebHostSetup.cs#L23)<br>[StudentManagement.Web.csproj:1\-7](../../srcs/CSharp_ASPNET/StudentManagement.Web.csproj#L1)<br>[Core/StudentManagement.Core.csproj:1\-12](../../srcs/CSharp_ASPNET/Core/StudentManagement.Core.csproj#L1)<br>[Directory.Build.props:3\-14](../../srcs/CSharp_ASPNET/Directory.Build.props#L3)<br>[StudentManagement.slnx:1\-8](../../srcs/CSharp_ASPNET/StudentManagement.slnx#L1)<br>[tools/build\_config.json:1\-19](../../srcs/CSharp_ASPNET/tools/build_config.json#L1)<br>[database/generate.mjs:6\-22](../../srcs/CSharp_ASPNET/database/generate.mjs#L6)

## 主機能と子操作

### ログイン (`FUNCTION-51c140f72a1525d6`)

- 機能領域: システム認証
- 主体: 利用者
- 業務対象: 認証セッション
- 目的: 利用者本人としてシステム利用を開始する
- 開始契機: ログイン画面で資格情報を送信する
- 完了成果: 認証済みセッションで学生検索へ進む、又は失敗通知を確認する
- 分類理由: 資格情報入力、送信、成功・失敗の帰結を持つ専用画面で独立した利用目的がある。
- 別の分け方・反例: 認証実装は共通化できるが、それだけでは専用画面の利用者タスクを表せない。
- 技術入口: ログイン画面・送信入口 (`ENTRY-8f8cf94cdd6cefb1`)
- 原文根拠: [Views/Account/Login.cshtml:1\-13](../../srcs/CSharp_ASPNET/Views/Account/Login.cshtml#L1)<br>[Web/Controllers/AccountController.cs:10\-34](../../srcs/CSharp_ASPNET/Web/Controllers/AccountController.cs#L10)<br>[appsettings.json:1\-1](../../srcs/CSharp_ASPNET/appsettings.json#L1)

| 子操作 | 利用文脈・目的 | 成果・帰属理由 | 根拠 |
| --- | --- | --- | --- |
| — | 子操作記録なし | 主機能の分類根拠・被覆を確認する | — |

### ログアウト (`FUNCTION-50628fec93066521`)

- 機能領域: システム認証
- 主体: 認証済み利用者
- 業務対象: 認証セッション
- 目的: 現在の利用セッションを終了する
- 開始契機: 認証済み画面のログアウトボタンを押す
- 完了成果: サインアウト後にログイン画面へ戻る
- 分類理由: 各業務画面から独立してセッション終了を完了でき、ログインの途中手順ではない。
- 別の分け方・反例: ログインと合わせて認証セッション管理という一主機能にまとめる分割も可能。
- 技術入口: ログアウト送信入口 (`ENTRY-9c769e24277ce710`)
- 原文根拠: [Views/Shared/\_Layout.cshtml:2\-4](../../srcs/CSharp_ASPNET/Views/Shared/_Layout.cshtml#L2)<br>[Web/Controllers/AccountController.cs:36\-41](../../srcs/CSharp_ASPNET/Web/Controllers/AccountController.cs#L36)

| 子操作 | 利用文脈・目的 | 成果・帰属理由 | 根拠 |
| --- | --- | --- | --- |
| — | 子操作記録なし | 主機能の分類根拠・被覆を確認する | — |

### 学生管理の操作選択 (`FUNCTION-12af019b26e0f2c3`)

- 機能領域: システム機能選択
- 主体: 認証済み利用者
- 業務対象: 学生管理の操作選択
- 目的: 役割に応じて開始する学生管理作業を選ぶ
- 開始契機: 学生管理メニューを開き操作を選択する
- 完了成果: 選択した検索又は新規登録の入口へ進む
- 分類理由: 共通レイアウトとは別のController・専用画面が役割別の機能選択を担い、検索画面からの復帰先にもなる。
- 別の分け方・反例: 選択責務を共通ナビゲーションだけと捉える場合はcommonにまとめられるが、専用の役割別選択画面を重視した。
- 技術入口: メニュー画面入口 (`ENTRY-e6d17ea2174934c2`)
- 原文根拠: [Web/Controllers/MenuController.cs:6\-10](../../srcs/CSharp_ASPNET/Web/Controllers/MenuController.cs#L6)<br>[Views/Menu/Index.cshtml:1\-7](../../srcs/CSharp_ASPNET/Views/Menu/Index.cshtml#L1)<br>[Views/Students/Search.cshtml:15\-18](../../srcs/CSharp_ASPNET/Views/Students/Search.cshtml#L15)<br>[Views/Shared/\_Layout.cshtml:1\-5](../../srcs/CSharp_ASPNET/Views/Shared/_Layout.cshtml#L1)

| 子操作 | 利用文脈・目的 | 成果・帰属理由 | 根拠 |
| --- | --- | --- | --- |
| — | 子操作記録なし | 主機能の分類根拠・被覆を確認する | — |

### 学生情報の検索・照会 (`FUNCTION-99e6712465221e10`)

- 機能領域: 学生管理
- 主体: Viewer、Staff、Administrator
- 業務対象: 学生情報
- 目的: 条件に合う学生とその登録情報を確認する
- 開始契機: 検索条件を指定し検索する
- 完了成果: 該当一覧、該当なし又は絞込要求を確認し、必要な学生を参照する
- 分類理由: Viewerにも認められ、保存を前提とせず完了できる照会タスクがある。
- 別の分け方・反例: 学生管理全体に統合することも可能だが、書込権限のない利用者にも独立した完了結果がある。
- 技術入口: 学生検索MVC入口群 (`ENTRY-569831b8ae99baac`)<br>既存学生の参照・更新MVC入口 (`ENTRY-b2d24681ff7c4259`)
- 原文根拠: [Views/Students/Search.cshtml:14\-77](../../srcs/CSharp_ASPNET/Views/Students/Search.cshtml#L14)<br>[Web/Controllers/StudentsController.cs:8\-22](../../srcs/CSharp_ASPNET/Web/Controllers/StudentsController.cs#L8)<br>[Infrastructure/WebStudentCoordinator.cs:7\-15](../../srcs/CSharp_ASPNET/Infrastructure/WebStudentCoordinator.cs#L7)<br>[Views/Students/Edit.cshtml:34\-43](../../srcs/CSharp_ASPNET/Views/Students/Edit.cshtml#L34)

| 子操作 | 利用文脈・目的 | 成果・帰属理由 | 根拠 |
| --- | --- | --- | --- |
| 検索結果の表示調整・条件クリア<br>`OPERATION-5e462890c5faa4eb` | 学生検索結果を閲覧しているとき<br>照会一覧を見やすくし条件を指定し直す | 調整後一覧又は未検索の条件画面になる<br>照会を進めるための補助操作で独立した対象業務を持たない。<br>別案: 条件クリアを別操作に分けても主機能数は変わらない。 | [Web/Controllers/StudentsController.cs:5\-5](../../srcs/CSharp_ASPNET/Web/Controllers/StudentsController.cs#L5)<br>[Web/Controllers/StudentsController.cs:23\-26](../../srcs/CSharp_ASPNET/Web/Controllers/StudentsController.cs#L23)<br>[Views/Students/Search.cshtml:45\-71](../../srcs/CSharp_ASPNET/Views/Students/Search.cshtml#L45) |
| 選択学生の詳細参照<br>`OPERATION-960593ec19e9aead` | 照会結果から参照又は編集リンクを開くときの照会目的<br>一覧で選んだ学生の詳細を確認する | 選択学生の登録内容を確認する<br>一覧からの詳細確認であり、同じ技術入口を編集準備とも共有する。<br>別案: 単独の詳細照会目的が別途確認されれば主機能に分離できる。 | [Views/Students/Search.cshtml:64\-67](../../srcs/CSharp_ASPNET/Views/Students/Search.cshtml#L64)<br>[Web/Controllers/StudentsController.cs:5\-5](../../srcs/CSharp_ASPNET/Web/Controllers/StudentsController.cs#L5)<br>[Web/Controllers/StudentsController.cs:30\-31](../../srcs/CSharp_ASPNET/Web/Controllers/StudentsController.cs#L30)<br>[Infrastructure/WebStudentCoordinator.cs:22\-22](../../srcs/CSharp_ASPNET/Infrastructure/WebStudentCoordinator.cs#L22)<br>[Views/Students/Edit.cshtml:34\-43](../../srcs/CSharp_ASPNET/Views/Students/Edit.cshtml#L34) |

### 学生情報の登録・保守 (`FUNCTION-4521f3923459be27`)

- 機能領域: 学生管理
- 主体: Staff、Administrator
- 業務対象: 学生台帳情報
- 目的: 学生の登録内容を整備する
- 開始契機: 新規登録又は既存学生の編集を開始する
- 完了成果: 保存又は論理削除の結果を確認して検索へ戻る
- 分類理由: 新規・編集・削除は同じ学生情報保守の画面と対象文脈を共有し、確認ダイアログは補助手順である。
- 別の分け方・反例: 新規登録と既存保守を別主機能にする分割は可能だが、独立した承認・廃棄業務を示す入口はない。
- 技術入口: 学生新規MVC入口 (`ENTRY-d72e4150a83d85b0`)<br>既存学生の参照・更新MVC入口 (`ENTRY-b2d24681ff7c4259`)<br>学生入力取消MVC入口 (`ENTRY-cb5b1e1281efcab0`)<br>学生論理削除MVC入口 (`ENTRY-0f3a182eb209a2b5`)
- 原文根拠: [Views/Students/Edit.cshtml:34\-176](../../srcs/CSharp_ASPNET/Views/Students/Edit.cshtml#L34)<br>[Web/Controllers/StudentsController.cs:29\-44](../../srcs/CSharp_ASPNET/Web/Controllers/StudentsController.cs#L29)<br>[Web/Models/StudentEditPageModel.cs:3\-15](../../srcs/CSharp_ASPNET/Web/Models/StudentEditPageModel.cs#L3)

| 子操作 | 利用文脈・目的 | 成果・帰属理由 | 根拠 |
| --- | --- | --- | --- |
| 保守対象学生の検索・選択<br>`OPERATION-06de96cd8788f0bb` | 既存学生を更新又は論理削除する前<br>変更する学生を特定する | 対象学生の保守画面を開く<br>独立照会と同じ検索入口を使うが、この文脈では保守の準備段階である。<br>別案: 検索画面をすべて独立照会だけに帰属させると保守時の利用文脈が失われる。 | [Views/Students/Search.cshtml:14\-20](../../srcs/CSharp_ASPNET/Views/Students/Search.cshtml#L14)<br>[Views/Students/Search.cshtml:64\-67](../../srcs/CSharp_ASPNET/Views/Students/Search.cshtml#L64)<br>[Web/Controllers/StudentsController.cs:5\-22](../../srcs/CSharp_ASPNET/Web/Controllers/StudentsController.cs#L5)<br>[Web/Controllers/StudentsController.cs:30\-31](../../srcs/CSharp_ASPNET/Web/Controllers/StudentsController.cs#L30) |
| 学生の新規入力・保存<br>`OPERATION-9447c1fc00d37108` | 新規登録を選択した保守作業<br>新しい学生情報を登録する | 登録結果を確認する<br>共用学生保守の新規モードとしてまとまっている。<br>別案: 新規受付に固有の独立工程が確認できれば別主機能にできる。 | [Web/Controllers/StudentsController.cs:5\-5](../../srcs/CSharp_ASPNET/Web/Controllers/StudentsController.cs#L5)<br>[Web/Controllers/StudentsController.cs:29\-39](../../srcs/CSharp_ASPNET/Web/Controllers/StudentsController.cs#L29)<br>[Infrastructure/WebStudentCoordinator.cs:23\-23](../../srcs/CSharp_ASPNET/Infrastructure/WebStudentCoordinator.cs#L23)<br>[Views/Students/Edit.cshtml:34\-56](../../srcs/CSharp_ASPNET/Views/Students/Edit.cshtml#L34)<br>[Views/Students/Edit.cshtml:144\-152](../../srcs/CSharp_ASPNET/Views/Students/Edit.cshtml#L144) |
| 既存学生の編集・保存<br>`OPERATION-8e540ae31cc8cc69` | 選択済み学生の情報を保守するとき<br>既存学生の登録内容を修正する | 更新結果を確認する<br>新規と共有する保守画面の既存モードであり、詳細参照とは同じ入口の別文脈。<br>別案: 訂正承認など独立した完了責任があれば主機能への分離が考えられる。 | [Web/Controllers/StudentsController.cs:5\-5](../../srcs/CSharp_ASPNET/Web/Controllers/StudentsController.cs#L5)<br>[Web/Controllers/StudentsController.cs:30\-40](../../srcs/CSharp_ASPNET/Web/Controllers/StudentsController.cs#L30)<br>[Views/Students/Edit.cshtml:34\-56](../../srcs/CSharp_ASPNET/Views/Students/Edit.cshtml#L34)<br>[Views/Students/Edit.cshtml:144\-152](../../srcs/CSharp_ASPNET/Views/Students/Edit.cshtml#L144) |
| 重複候補の確認・続行<br>`OPERATION-0975fa417893b0ad` | 学生保存が重複確認を要求したとき<br>候補を確認して保存継続を判断する | 保存要求を続行又は取消する<br>保存結果に応じて開く補助ダイアログで、独立した重複審査入口はない。<br>別案: 独立した審査担当・承認入口があれば別主機能にできる。 | [Views/Students/Edit.cshtml:153\-162](../../srcs/CSharp_ASPNET/Views/Students/Edit.cshtml#L153)<br>[Core/SqlServerStudentService.cs:278\-282](../../srcs/CSharp_ASPNET/Core/SqlServerStudentService.cs#L278)<br>[wwwroot/js/site.js:106\-116](../../srcs/CSharp_ASPNET/wwwroot/js/site.js#L106) |
| 学生情報の論理削除<br>`OPERATION-95721013980c31ff` | 既存学生の保守中に管理者が削除を選択したとき<br>選択学生を通常の管理対象から除く | 論理削除結果を確認して検索へ戻る<br>同一対象の保守画面から起動する確認付き操作で、独立した法的廃棄工程は観測されない。<br>別案: 別の承認・保管期限・廃棄責任を持つ工程なら主機能に分ける。 | [Views/Students/Edit.cshtml:150\-173](../../srcs/CSharp_ASPNET/Views/Students/Edit.cshtml#L150)<br>[Web/Controllers/StudentsController.cs:5\-5](../../srcs/CSharp_ASPNET/Web/Controllers/StudentsController.cs#L5)<br>[Web/Controllers/StudentsController.cs:43\-44](../../srcs/CSharp_ASPNET/Web/Controllers/StudentsController.cs#L43)<br>[Infrastructure/WebStudentCoordinator.cs:24\-24](../../srcs/CSharp_ASPNET/Infrastructure/WebStudentCoordinator.cs#L24) |
| 入力取消・再読込・検索復帰<br>`OPERATION-b9b99887830e9e95` | 学生情報を編集中又は参照中<br>編集中の入力を取り消し作業を再開又は終了する | 読込時の値、最新情報又は検索画面に戻る<br>保守作業内の補助操作で独立した業務対象を持たない。<br>別案: 取消・再読込・復帰を個別操作として分けても主機能数は変わらない。 | [Web/Controllers/StudentsController.cs:5\-5](../../srcs/CSharp_ASPNET/Web/Controllers/StudentsController.cs#L5)<br>[Web/Controllers/StudentsController.cs:41\-41](../../srcs/CSharp_ASPNET/Web/Controllers/StudentsController.cs#L41)<br>[Views/Students/Edit.cshtml:144\-152](../../srcs/CSharp_ASPNET/Views/Students/Edit.cshtml#L144)<br>[Views/Students/Edit.cshtml:175\-175](../../srcs/CSharp_ASPNET/Views/Students/Edit.cshtml#L175)<br>[wwwroot/js/site.js:117\-147](../../srcs/CSharp_ASPNET/wwwroot/js/site.js#L117) |

### クラスマスタ保守 (`FUNCTION-2afdcc2b1793e98c`)

- 機能領域: マスタ保守
- 主体: student\_adminに属するDB接続主体
- 業務対象: 年度別クラス
- 目的: 学生の所属先となるクラス情報を整備する
- 開始契機: CLIでclassと変更JSONを指定する
- 完了成果: クラス保存結果又は修正を要する通知を受け取る
- 分類理由: 独立実行可能なCLIに、学生編集と別の対象・入力・完了結果がある。
- 別の分け方・反例: コード保守と一つのマスタ保守機能にまとめることも可能だが、選択対象と変更要求型が異なる。
- 技術入口: StudentMaintenance CLI入口 (`ENTRY-dc043b22af9afce4`)
- 原文根拠: [maintenance/Program.cs:4\-17](../../srcs/CSharp_ASPNET/maintenance/Program.cs#L4)<br>[Core/MasterMaintenanceService.cs:17\-78](../../srcs/CSharp_ASPNET/Core/MasterMaintenanceService.cs#L17)<br>[maintenance/StudentMaintenance.csproj:1\-4](../../srcs/CSharp_ASPNET/maintenance/StudentMaintenance.csproj#L1)

| 子操作 | 利用文脈・目的 | 成果・帰属理由 | 根拠 |
| --- | --- | --- | --- |
| — | 子操作記録なし | 主機能の分類根拠・被覆を確認する | — |

### 業務コード保守 (`FUNCTION-1b8a3fb7f1cba96d`)

- 機能領域: マスタ保守
- 主体: student\_adminに属するDB接続主体
- 業務対象: 分類別業務コード
- 目的: 学生管理で使う選択値を整備する
- 開始契機: CLIでcodeと変更JSONを指定する
- 完了成果: コード保存結果又は修正を要する通知を受け取る
- 分類理由: 分類別コードを対象とする独立した管理者タスクで、クラス保守とは要求型と対象が異なる。
- 別の分け方・反例: クラス保守と統合したマスタ保守の操作として扱う分割も可能。
- 技術入口: StudentMaintenance CLI入口 (`ENTRY-dc043b22af9afce4`)
- 原文根拠: [maintenance/Program.cs:4\-17](../../srcs/CSharp_ASPNET/maintenance/Program.cs#L4)<br>[Core/MasterMaintenanceService.cs:17\-29](../../srcs/CSharp_ASPNET/Core/MasterMaintenanceService.cs#L17)<br>[Core/MasterMaintenanceService.cs:79\-122](../../srcs/CSharp_ASPNET/Core/MasterMaintenanceService.cs#L79)

| 子操作 | 利用文脈・目的 | 成果・帰属理由 | 根拠 |
| --- | --- | --- | --- |
| — | 子操作記録なし | 主機能の分類根拠・被覆を確認する | — |

## 共通能力

| 名称 | 共有・集中する責務 | 利用先 | 分類理由・反例 | 根拠 |
| --- | --- | --- | --- | --- |
| ローカル認証・Cookieセッション<br>`COMMON-44bbb5fbe07b7437` | 認証検証とセッション維持・終了の共通実装 | ログイン画面・送信入口 (`ENTRY-8f8cf94cdd6cefb1`)<br>ログアウト送信入口 (`ENTRY-9c769e24277ce710`)<br>Web登録・要求保護・共通例外処理 (`COMMON-ab23bcef940d1fc4`) | ホスト及びアカウント入口が利用する中央責務で、専用ログイン機能とは別の実装層。<br>別案: ログイン画面の主機能だけに含めるとホストのCookie受入責務を表しにくい。 | [Infrastructure/LocalLogin.cs:13\-90](../../srcs/CSharp_ASPNET/Infrastructure/LocalLogin.cs#L13)<br>[Infrastructure/WebHostSetup.cs:15\-18](../../srcs/CSharp_ASPNET/Infrastructure/WebHostSetup.cs#L15)<br>[Web/Controllers/AccountController.cs:18\-41](../../srcs/CSharp_ASPNET/Web/Controllers/AccountController.cs#L18) |
| 要求主体・役割別認可<br>`COMMON-f5a6919b3b06925e` | Web要求からの利用者識別と権限確認 | 学生Web処理の調整 (`COMMON-dc62b6377e02c341`) | 検索・保存・削除にまたがる中央の要求認可責務。<br>別案: 各入口へ埋め込む分割も可能だが、実装は独立サービスとして登録される。 | [Infrastructure/RequestIdentity.cs:4\-18](../../srcs/CSharp_ASPNET/Infrastructure/RequestIdentity.cs#L4)<br>[Infrastructure/WebHostSetup.cs:17\-17](../../srcs/CSharp_ASPNET/Infrastructure/WebHostSetup.cs#L17)<br>[Infrastructure/WebStudentCoordinator.cs:7\-24](../../srcs/CSharp_ASPNET/Infrastructure/WebStudentCoordinator.cs#L7) |
| 学生照会・保存のCoreサービス<br>`COMMON-3084969d4225f395` | 学生情報の永続化と照会・保守に共通する業務規則 | 学生Web処理の調整 (`COMMON-dc62b6377e02c341`)<br>学生検索MVC入口群 (`ENTRY-569831b8ae99baac`)<br>既存学生の参照・更新MVC入口 (`ENTRY-b2d24681ff7c4259`) | 登録されたCoreサービスとして複数の利用者タスクを支える。<br>別案: 照会・保存サービスを分割できるが、原文は一つの契約と実装にまとめている。 | [Core/SqlServerStudentService.cs:115\-209](../../srcs/CSharp_ASPNET/Core/SqlServerStudentService.cs#L115)<br>[Core/SqlServerStudentService.cs:219\-409](../../srcs/CSharp_ASPNET/Core/SqlServerStudentService.cs#L219)<br>[Infrastructure/WebHostSetup.cs:23\-23](../../srcs/CSharp_ASPNET/Infrastructure/WebHostSetup.cs#L23)<br>[Infrastructure/WebStudentCoordinator.cs:7\-24](../../srcs/CSharp_ASPNET/Infrastructure/WebStudentCoordinator.cs#L7) |
| マスタ保守のCoreサービス<br>`COMMON-f0f9501d20c56062` | クラス及びコード保守の共通実装 | クラスマスタ保守 (`FUNCTION-2afdcc2b1793e98c`)<br>業務コード保守 (`FUNCTION-1b8a3fb7f1cba96d`)<br>StudentMaintenance CLI入口 (`ENTRY-dc043b22af9afce4`) | 独立した二つのCLIタスクを同一サービスが支える。<br>別案: クラス用とコード用に実装を分けても利用者機能の分割とは別問題。 | [Core/MasterMaintenanceService.cs:15\-137](../../srcs/CSharp_ASPNET/Core/MasterMaintenanceService.cs#L15)<br>[maintenance/Program.cs:11\-13](../../srcs/CSharp_ASPNET/maintenance/Program.cs#L11) |
| 入力正規化・学生共通検証<br>`COMMON-80447ecdad329c88` | 保存・検索・マスタ入力で共用する正規化及び業務入力規則 | 学生照会・保存のCoreサービス (`COMMON-3084969d4225f395`)<br>マスタ保守のCoreサービス (`COMMON-f0f9501d20c56062`) | 複数のCore処理が参照する中央規則で、単なる文字列ユーティリティに限らない。<br>別案: 個別保存処理へ含められるが、検索・マスタでも利用される責務が失われる。 | [Core/StudentNormalizer.cs:19\-169](../../srcs/CSharp_ASPNET/Core/StudentNormalizer.cs#L19)<br>[Core/SqlServerStudentService.cs:225\-229](../../srcs/CSharp_ASPNET/Core/SqlServerStudentService.cs#L225)<br>[Core/MasterMaintenanceService.cs:33\-36](../../srcs/CSharp_ASPNET/Core/MasterMaintenanceService.cs#L33)<br>[Core/MasterMaintenanceService.cs:82\-85](../../srcs/CSharp_ASPNET/Core/MasterMaintenanceService.cs#L82) |
| 和暦・西暦日付変換<br>`COMMON-e5eba6cf1b258ce7` | 学生・マスタで使う日付の共通表現と検証 | 入力正規化・学生共通検証 (`COMMON-80447ecdad329c88`)<br>マスタ保守のCoreサービス (`COMMON-f0f9501d20c56062`)<br>学生照会・保存のCoreサービス (`COMMON-3084969d4225f395`) | 入力正規化、マスタ期間、学生読込から実際の参照がある。<br>別案: 画面別の日付処理に分けることも可能だが、原文の共通元号定義と整合しにくい。 | [Core/JapaneseDateService.cs:7\-62](../../srcs/CSharp_ASPNET/Core/JapaneseDateService.cs#L7)<br>[Core/StudentNormalizer.cs:127\-137](../../srcs/CSharp_ASPNET/Core/StudentNormalizer.cs#L127)<br>[Core/MasterMaintenanceService.cs:36\-36](../../srcs/CSharp_ASPNET/Core/MasterMaintenanceService.cs#L36)<br>[Core/SqlServerStudentService.cs:175\-187](../../srcs/CSharp_ASPNET/Core/SqlServerStudentService.cs#L175) |
| SQL補助・共通書込ゲート<br>`COMMON-4990109eb50e3f01` | SQL要求組立、パラメーター設定、書込排他とロールバックの共有 | 学生照会・保存のCoreサービス (`COMMON-3084969d4225f395`)<br>マスタ保守のCoreサービス (`COMMON-f0f9501d20c56062`) | 別サービスのマスタ保守からも利用する明示的な共通責務。<br>別案: 独立したDB補助クラスへ移せるが、現状の宣言位置だけで学生専用とは判断しない。 | [Core/SqlServerStudentService.cs:65\-73](../../srcs/CSharp_ASPNET/Core/SqlServerStudentService.cs#L65)<br>[Core/SqlServerStudentService.cs:92\-102](../../srcs/CSharp_ASPNET/Core/SqlServerStudentService.cs#L92)<br>[Core/SqlServerStudentService.cs:233\-236](../../srcs/CSharp_ASPNET/Core/SqlServerStudentService.cs#L233)<br>[Core/SqlServerStudentService.cs:321\-321](../../srcs/CSharp_ASPNET/Core/SqlServerStudentService.cs#L321)<br>[Core/MasterMaintenanceService.cs:38\-42](../../srcs/CSharp_ASPNET/Core/MasterMaintenanceService.cs#L38)<br>[Core/MasterMaintenanceService.cs:74\-77](../../srcs/CSharp_ASPNET/Core/MasterMaintenanceService.cs#L74) |
| マスタ監査操作の分類<br>`COMMON-18a1da87ea7d820f` | マスタ変更の監査上の操作種別を統一する | マスタ保守のCoreサービス (`COMMON-f0f9501d20c56062`) | クラスとコードの二つの保存文脈から参照される共有業務規則。<br>別案: マスタサービスの内部処理として一括記録することも可能。 | [Core/AuditOperation.cs:4\-8](../../srcs/CSharp_ASPNET/Core/AuditOperation.cs#L4)<br>[Core/MasterMaintenanceService.cs:75\-75](../../srcs/CSharp_ASPNET/Core/MasterMaintenanceService.cs#L75)<br>[Core/MasterMaintenanceService.cs:119\-119](../../srcs/CSharp_ASPNET/Core/MasterMaintenanceService.cs#L119) |
| 検索状態と共通識別子の保持<br>`COMMON-1402f405c79093a3` | 検索文脈の中央保持と状態識別子生成 | 学生Web処理の調整 (`COMMON-dc62b6377e02c341`)<br>学生検索MVC入口群 (`ENTRY-569831b8ae99baac`)<br>ローカル認証・Cookieセッション (`COMMON-44bbb5fbe07b7437`)<br>編集スナップショット管理 (`COMMON-486b008b89e07bf9`) | 検索Controller・調整処理、認証、編集スナップショットに静的な利用箇所がある。<br>別案: 識別子生成を別commonへ分けることも可能だが、ここでは原文の責務単位を維持する。 | [Infrastructure/SearchContextStore.cs:7\-18](../../srcs/CSharp_ASPNET/Infrastructure/SearchContextStore.cs#L7)<br>[Infrastructure/WebHostSetup.cs:17\-17](../../srcs/CSharp_ASPNET/Infrastructure/WebHostSetup.cs#L17)<br>[Infrastructure/WebStudentCoordinator.cs:5\-20](../../srcs/CSharp_ASPNET/Infrastructure/WebStudentCoordinator.cs#L5)<br>[Web/Controllers/StudentsController.cs:8\-11](../../srcs/CSharp_ASPNET/Web/Controllers/StudentsController.cs#L8)<br>[Infrastructure/LocalLogin.cs:77\-77](../../srcs/CSharp_ASPNET/Infrastructure/LocalLogin.cs#L77)<br>[Infrastructure/EditorSnapshotStore.cs:9\-9](../../srcs/CSharp_ASPNET/Infrastructure/EditorSnapshotStore.cs#L9) |
| 編集スナップショット管理<br>`COMMON-486b008b89e07bf9` | 編集の読込状態と所有者を中央管理する | 学生新規MVC入口 (`ENTRY-d72e4150a83d85b0`)<br>既存学生の参照・更新MVC入口 (`ENTRY-b2d24681ff7c4259`)<br>学生入力取消MVC入口 (`ENTRY-cb5b1e1281efcab0`)<br>学生論理削除MVC入口 (`ENTRY-0f3a182eb209a2b5`) | 新規・既存・取消の複数文脈から共用される登録済み状態サービス。<br>別案: 画面モデルだけに含めるとサーバー保持の所有者確認責務を表せない。 | [Infrastructure/EditorSnapshotStore.cs:5\-12](../../srcs/CSharp_ASPNET/Infrastructure/EditorSnapshotStore.cs#L5)<br>[Infrastructure/WebHostSetup.cs:17\-17](../../srcs/CSharp_ASPNET/Infrastructure/WebHostSetup.cs#L17)<br>[Web/Controllers/StudentsController.cs:31\-41](../../srcs/CSharp_ASPNET/Web/Controllers/StudentsController.cs#L31) |
| 復帰先メッセージ保持<br>`COMMON-fb7fdb3c43b55398` | 画面遷移をまたぐ一時通知の受渡し | 学生検索MVC入口群 (`ENTRY-569831b8ae99baac`)<br>学生新規MVC入口 (`ENTRY-d72e4150a83d85b0`)<br>既存学生の参照・更新MVC入口 (`ENTRY-b2d24681ff7c4259`)<br>学生論理削除MVC入口 (`ENTRY-0f3a182eb209a2b5`) | 保存側と検索側が共有する中央保持責務。<br>別案: Controller固有の補助処理としてまとめることも可能。 | [Infrastructure/FlashMessageStore.cs:4\-10](../../srcs/CSharp_ASPNET/Infrastructure/FlashMessageStore.cs#L4)<br>[Infrastructure/WebHostSetup.cs:17\-17](../../srcs/CSharp_ASPNET/Infrastructure/WebHostSetup.cs#L17)<br>[Web/Controllers/StudentsController.cs:11\-11](../../srcs/CSharp_ASPNET/Web/Controllers/StudentsController.cs#L11)<br>[Web/Controllers/StudentsController.cs:44\-44](../../srcs/CSharp_ASPNET/Web/Controllers/StudentsController.cs#L44) |
| 学生Web処理の調整<br>`COMMON-dc62b6377e02c341` | MVC入口とCoreの間の学生処理調整 | 学生検索MVC入口群 (`ENTRY-569831b8ae99baac`)<br>学生新規MVC入口 (`ENTRY-d72e4150a83d85b0`)<br>既存学生の参照・更新MVC入口 (`ENTRY-b2d24681ff7c4259`)<br>学生論理削除MVC入口 (`ENTRY-0f3a182eb209a2b5`) | 複数のMVC入口が使う登録済みサービスで、メソッド単位の独立機能ではない。<br>別案: Controller内に統合できるが、利用者タスクと調整実装は分けて記録する。 | [Infrastructure/WebStudentCoordinator.cs:3\-28](../../srcs/CSharp_ASPNET/Infrastructure/WebStudentCoordinator.cs#L3)<br>[Infrastructure/WebHostSetup.cs:17\-17](../../srcs/CSharp_ASPNET/Infrastructure/WebHostSetup.cs#L17)<br>[Web/Controllers/StudentsController.cs:13\-43](../../srcs/CSharp_ASPNET/Web/Controllers/StudentsController.cs#L13) |
| 日時・結果・エラーの表示変換<br>`COMMON-f015d0673752f073` | Web層の表示値・通知・応答表現の統一 | 学生Web処理の調整 (`COMMON-dc62b6377e02c341`)<br>既存学生の参照・更新MVC入口 (`ENTRY-b2d24681ff7c4259`)<br>Web登録・要求保護・共通例外処理 (`COMMON-ab23bcef940d1fc4`) | 調整処理、Controller、共通例外処理から静的な使用がある。<br>別案: JSON向け宣言全体を現行APIと解釈してはならず、入口のない宣言は補助資源として別記する。 | [Infrastructure/WebPresentation.cs:3\-31](../../srcs/CSharp_ASPNET/Infrastructure/WebPresentation.cs#L3)<br>[Infrastructure/WebStudentCoordinator.cs:26\-27](../../srcs/CSharp_ASPNET/Infrastructure/WebStudentCoordinator.cs#L26)<br>[Web/Controllers/StudentsController.cs:38\-45](../../srcs/CSharp_ASPNET/Web/Controllers/StudentsController.cs#L38)<br>[Infrastructure/WebHostSetup.cs:27\-27](../../srcs/CSharp_ASPNET/Infrastructure/WebHostSetup.cs#L27) |
| Web登録・要求保護・共通例外処理<br>`COMMON-ab23bcef940d1fc4` | Webアプリ全体の起動登録と要求横断処理 | Web起動・ルート転送 (`ENTRY-02508968d096bfde`) | Programから呼ばれる中央設定であり、個別の利用者主機能ではない。<br>別案: 起動支援としてsupportにまとめる余地はあるが、要求時に適用される共通責務を含む。 | [Infrastructure/WebHostSetup.cs:11\-34](../../srcs/CSharp_ASPNET/Infrastructure/WebHostSetup.cs#L11)<br>[Infrastructure/AntiforgeryResultFilter.cs:5\-10](../../srcs/CSharp_ASPNET/Infrastructure/AntiforgeryResultFilter.cs#L5)<br>[Program.cs:3\-5](../../srcs/CSharp_ASPNET/Program.cs#L3) |
| 共通レイアウト・通知・画面操作支援<br>`COMMON-b0eb6b85dc082fc4` | 画面横断の表示枠とブラウザー操作支援 | ログイン (`FUNCTION-51c140f72a1525d6`)<br>ログアウト (`FUNCTION-50628fec93066521`)<br>学生管理の操作選択 (`FUNCTION-12af019b26e0f2c3`)<br>学生情報の検索・照会 (`FUNCTION-99e6712465221e10`)<br>学生情報の登録・保守 (`FUNCTION-4521f3923459be27`) | ViewStartによる共通適用、Layoutの資源読込、部分View利用が原文にある。<br>別案: 学生専用CSS・JavaScriptを別commonに細分化できるが、それ自体を利用者機能とは数えない。 | [Views/Shared/\_Layout.cshtml:1\-5](../../srcs/CSharp_ASPNET/Views/Shared/_Layout.cshtml#L1)<br>[Views/Shared/\_MessagePanel.cshtml:1\-3](../../srcs/CSharp_ASPNET/Views/Shared/_MessagePanel.cshtml#L1)<br>[Views/\_ViewImports.cshtml:1\-3](../../srcs/CSharp_ASPNET/Views/_ViewImports.cshtml#L1)<br>[Views/\_ViewStart.cshtml:1\-1](../../srcs/CSharp_ASPNET/Views/_ViewStart.cshtml#L1)<br>[wwwroot/css/site.css:1\-2](../../srcs/CSharp_ASPNET/wwwroot/css/site.css#L1)<br>[wwwroot/css/students.css:1\-117](../../srcs/CSharp_ASPNET/wwwroot/css/students.css#L1)<br>[wwwroot/js/site.js:1\-231](../../srcs/CSharp_ASPNET/wwwroot/js/site.js#L1)<br>[Views/Students/Search.cshtml:19\-19](../../srcs/CSharp_ASPNET/Views/Students/Search.cshtml#L19) |

## データ対象（主機能数には含めない）

| 名称 | 内容 | 根拠 |
| --- | --- | --- |
| 物理表 dbo.m\_student<br>`DATA-deef86a72d368260` | 学生識別、基本情報、住所・連絡先、在籍・所属、緊急連絡先、論理削除及び更新管理を持つCREATE TABLE定義。 | [database/001\_schema.sql:7\-60](../../srcs/CSharp_ASPNET/database/001_schema.sql#L7) |
| 物理表 dbo.m\_class<br>`DATA-3f3f53564617db53` | 年度、学年、クラスコード・名称、利用期間、定員、有効状態及び更新管理を持つCREATE TABLE定義。 | [database/001\_schema.sql:62\-88](../../srcs/CSharp_ASPNET/database/001_schema.sql#L62) |
| 物理表 dbo.m\_code\_category<br>`DATA-737bd2f6a3900da0` | 分類識別、名称、コード長、追加可否、有効状態及び更新管理を持つCREATE TABLE定義。 | [database/001\_schema.sql:90\-110](../../srcs/CSharp_ASPNET/database/001_schema.sql#L90) |
| 物理表 dbo.m\_codeと初期業務コード<br>`DATA-10f80affb2d3f89e` | 分類とコード値の複合主キー、名称、表示順、有効期間、保護区分を持つ物理表。seedには性別・在籍区分・都道府県・続柄・学年の5分類70コードを記述する。 | [database/001\_schema.sql:112\-135](../../srcs/CSharp_ASPNET/database/001_schema.sql#L112)<br>[database/002\_seed.sql:8\-91](../../srcs/CSharp_ASPNET/database/002_seed.sql#L8) |
| 物理表 dbo.t\_operation\_log<br>`DATA-6dd334c1de11e661` | 対象表・キー、操作種別、変更前後の版、変更列、実行主体・日時、相関ID、理由等を持つ監査履歴の物理定義。 | [database/001\_schema.sql:137\-154](../../srcs/CSharp_ASPNET/database/001_schema.sql#L137) |
| 物理表 dbo.t\_confirmation<br>`DATA-464a851789c34899` | 重複確認情報の物理定義と非Webトークン経路のSQL参照がある。現行Web登録はwebTokens:trueを指定するため、表宣言を現行Webの保持先と同一視しない。 | [database/001\_schema.sql:156\-169](../../srcs/CSharp_ASPNET/database/001_schema.sql#L156)<br>[Core/SqlServerStudentService.cs:269\-275](../../srcs/CSharp_ASPNET/Core/SqlServerStudentService.cs#L269)<br>[Core/SqlServerStudentService.cs:322\-335](../../srcs/CSharp_ASPNET/Core/SqlServerStudentService.cs#L322)<br>[Infrastructure/WebHostSetup.cs:23\-23](../../srcs/CSharp_ASPNET/Infrastructure/WebHostSetup.cs#L23) |
| 物理表 dbo.t\_runtime\_state<br>`DATA-b366067737eda551` | 所有者、ログインセッション、状態種別、暗号化ペイロード、期限、版等を持つ物理定義。取得した現行Web実装にこの表へのDML利用は観測されず、権限SQLもメモリー保持を説明する。 | [database/001\_schema.sql:171\-184](../../srcs/CSharp_ASPNET/database/001_schema.sql#L171)<br>[database/003\_web\_permissions.sql:23\-24](../../srcs/CSharp_ASPNET/database/003_web_permissions.sql#L23) |
| Azure配備向けDDL・seed派生入力<br>`DATA-fdf88a4c61dbddfe` | Initialize\-AzureDatabase.pyは元DDLの5参照コード列をvarchar\(10\)に変換して元幅のCHECKを加え、seed表変数の照合順序を補う。別の表群ではなく、同じ7表の配備時定義変種として保持する。 | [deployment/Initialize\-AzureDatabase.py:11\-30](../../srcs/CSharp_ASPNET/deployment/Initialize-AzureDatabase.py#L11)<br>[deployment/Initialize\-AzureDatabase.py:93\-131](../../srcs/CSharp_ASPNET/deployment/Initialize-AzureDatabase.py#L93) |
| Coreの契約・DTO<br>`DATA-bb2153271f2e42dd` | CurrentUser、StudentDraft、SearchCriteria、StudentListItem、StudentRow、StudentDetail、LookupSet、SaveRequest/Result、エラー・結果列挙とIStudentServiceを宣言する。サービス用DTO・投影型であり、物理表定義やORM Entity登録ではない。 | [Core/Contracts.cs:4\-94](../../srcs/CSharp_ASPNET/Core/Contracts.cs#L4) |
| マスタ保守の変更DTO<br>`DATA-f949734b7e465aaf` | ClassChange、CodeChange、MaintenanceResultがCLIの変更要求と処理結果を表す。 | [Core/MasterMaintenanceService.cs:9\-11](../../srcs/CSharp_ASPNET/Core/MasterMaintenanceService.cs#L9) |
| Web入力・要求候補・画面モデル<br>`DATA-74694962c01f89ec` | 学生検索・保存・削除入力、文脈・ページ要求、OptionsRequestとログイン・検索・編集ページモデルを宣言する。OptionsRequestの存在だけでは現行公開APIを証明しない。 | [Web/Inputs/StudentDeleteInput.cs:3\-4](../../srcs/CSharp_ASPNET/Web/Inputs/StudentDeleteInput.cs#L3)<br>[Web/Inputs/StudentSaveInput.cs:6\-56](../../srcs/CSharp_ASPNET/Web/Inputs/StudentSaveInput.cs#L6)<br>[Web/Inputs/StudentSearchInput.cs:4\-21](../../srcs/CSharp_ASPNET/Web/Inputs/StudentSearchInput.cs#L4)<br>[Web/Models/LoginPageModel.cs:3\-7](../../srcs/CSharp_ASPNET/Web/Models/LoginPageModel.cs#L3)<br>[Web/Models/StudentEditPageModel.cs:3\-15](../../srcs/CSharp_ASPNET/Web/Models/StudentEditPageModel.cs#L3)<br>[Web/Models/StudentSearchPageModel.cs:4\-16](../../srcs/CSharp_ASPNET/Web/Models/StudentSearchPageModel.cs#L4) |
| プロセス内の検索・編集・確認・通知状態<br>`DATA-f4e324f578eaf525` | 検索Entry、編集Snapshot、重複Confirmation、FlashMessageを辞書で保持する宣言がある。物理表t\_runtime\_stateやt\_confirmationとは別の保持対象。 | [Infrastructure/SearchContextStore.cs:10\-11](../../srcs/CSharp_ASPNET/Infrastructure/SearchContextStore.cs#L10)<br>[Infrastructure/EditorSnapshotStore.cs:7\-8](../../srcs/CSharp_ASPNET/Infrastructure/EditorSnapshotStore.cs#L7)<br>[Infrastructure/FlashMessageStore.cs:4\-9](../../srcs/CSharp_ASPNET/Infrastructure/FlashMessageStore.cs#L4)<br>[Core/SqlServerStudentService.cs:19\-29](../../srcs/CSharp_ASPNET/Core/SqlServerStudentService.cs#L19)<br>[Infrastructure/WebHostSetup.cs:23\-23](../../srcs/CSharp_ASPNET/Infrastructure/WebHostSetup.cs#L23) |

## 技術入口（主機能数には含めない）

| 名称 | 内容 | 根拠 |
| --- | --- | --- |
| Web起動・ルート転送<br>`ENTRY-02508968d096bfde` | ProgramのトップレベルでWebHostSetup、Controllerを登録し、GET /を/studentsへ転送する。 | [Program.cs:2\-8](../../srcs/CSharp_ASPNET/Program.cs#L2) |
| ログイン画面・送信入口<br>`ENTRY-8f8cf94cdd6cefb1` | AccountControllerに匿名許可のGET /login及びPOST /loginを宣言する。 | [Web/Controllers/AccountController.cs:10\-34](../../srcs/CSharp_ASPNET/Web/Controllers/AccountController.cs#L10) |
| ログアウト送信入口<br>`ENTRY-9c769e24277ce710` | AccountControllerに認証要求のPOST /logoutを宣言する。 | [Web/Controllers/AccountController.cs:36\-41](../../srcs/CSharp_ASPNET/Web/Controllers/AccountController.cs#L36) |
| メニュー画面入口<br>`ENTRY-e6d17ea2174934c2` | 認証要求のMenuControllerにGET /menuを宣言する。 | [Web/Controllers/MenuController.cs:6\-10](../../srcs/CSharp_ASPNET/Web/Controllers/MenuController.cs#L6) |
| 学生検索MVC入口群<br>`ENTRY-569831b8ae99baac` | 認証要求のstudentsルートにGET /students、POST /students/search、/students/page、/students/clearを宣言する。 | [Web/Controllers/StudentsController.cs:5\-26](../../srcs/CSharp_ASPNET/Web/Controllers/StudentsController.cs#L5) |
| 学生新規MVC入口<br>`ENTRY-d72e4150a83d85b0` | GET /students/newとPOST /students/createを宣言する。 | [Web/Controllers/StudentsController.cs:5\-5](../../srcs/CSharp_ASPNET/Web/Controllers/StudentsController.cs#L5)<br>[Web/Controllers/StudentsController.cs:29\-29](../../srcs/CSharp_ASPNET/Web/Controllers/StudentsController.cs#L29)<br>[Web/Controllers/StudentsController.cs:32\-32](../../srcs/CSharp_ASPNET/Web/Controllers/StudentsController.cs#L32) |
| 既存学生の参照・更新MVC入口<br>`ENTRY-b2d24681ff7c4259` | GET /students/\{id:long\}とPOST /students/\{id:long\}/updateを宣言し、参照と編集で表示入口を共有する。 | [Web/Controllers/StudentsController.cs:5\-5](../../srcs/CSharp_ASPNET/Web/Controllers/StudentsController.cs#L5)<br>[Web/Controllers/StudentsController.cs:30\-33](../../srcs/CSharp_ASPNET/Web/Controllers/StudentsController.cs#L30)<br>[Web/Models/StudentEditPageModel.cs:14\-14](../../srcs/CSharp_ASPNET/Web/Models/StudentEditPageModel.cs#L14) |
| 学生入力取消MVC入口<br>`ENTRY-cb5b1e1281efcab0` | POST /students/resetを宣言する。 | [Web/Controllers/StudentsController.cs:5\-5](../../srcs/CSharp_ASPNET/Web/Controllers/StudentsController.cs#L5)<br>[Web/Controllers/StudentsController.cs:41\-41](../../srcs/CSharp_ASPNET/Web/Controllers/StudentsController.cs#L41) |
| 学生論理削除MVC入口<br>`ENTRY-0f3a182eb209a2b5` | POST /students/\{id:long\}/deleteを宣言する。 | [Web/Controllers/StudentsController.cs:5\-5](../../srcs/CSharp_ASPNET/Web/Controllers/StudentsController.cs#L5)<br>[Web/Controllers/StudentsController.cs:43\-43](../../srcs/CSharp_ASPNET/Web/Controllers/StudentsController.cs#L43) |
| 廃止候補更新URLの残存宣言<br>`ENTRY-2c3bfac7003453be` | POST /students/optionsは宣言が残るが、アクション本文はNotFoundを返す。現行候補取得機能として数えない。 | [Web/Controllers/StudentsController.cs:5\-5](../../srcs/CSharp_ASPNET/Web/Controllers/StudentsController.cs#L5)<br>[Web/Controllers/StudentsController.cs:27\-28](../../srcs/CSharp_ASPNET/Web/Controllers/StudentsController.cs#L27) |
| 評価用セッションAPI入口<br>`ENTRY-318ca0e1cc94683a` | POST /\_evaluation/sessionを明示登録する評価支援入口。Development及びサーバー設定に制約され、利用者向けログイン画面とは別である。 | [Infrastructure/WebHostSetup.cs:30\-31](../../srcs/CSharp_ASPNET/Infrastructure/WebHostSetup.cs#L30) |
| 生存確認入口<br>`ENTRY-ac29297370f00e36` | GET /healthを登録し、running及びdatabase=not\-testedを応答する宣言がある。DB検証の成功証拠ではない。 | [Infrastructure/WebHostSetup.cs:32\-32](../../srcs/CSharp_ASPNET/Infrastructure/WebHostSetup.cs#L32) |
| StudentMaintenance CLI入口<br>`ENTRY-dc043b22af9afce4` | 独立Exeプロジェクトのトップレベルでclass又はcodeとJSONファイルを受け付ける。CLI選択の意味は原文から確認した。 | [maintenance/Program.cs:4\-17](../../srcs/CSharp_ASPNET/maintenance/Program.cs#L4)<br>[maintenance/StudentMaintenance.csproj:1\-4](../../srcs/CSharp_ASPNET/maintenance/StudentMaintenance.csproj#L1) |
| DatabaseSmokeコンソール入口<br>`ENTRY-e06d9eb9d4764688` | 独立した配備検証Exeに学生サービスの候補取得・検索を呼ぶトップレベル入口がある。 | [deployment/DatabaseSmoke/Program.cs:3\-9](../../srcs/CSharp_ASPNET/deployment/DatabaseSmoke/Program.cs#L3)<br>[deployment/DatabaseSmoke/DatabaseSmoke.csproj:1\-4](../../srcs/CSharp_ASPNET/deployment/DatabaseSmoke/DatabaseSmoke.csproj#L1) |
| LoginPasswordHashコンソール入口<br>`ENTRY-e8fd78d7771d26f5` | 独立した配備補助Exeにパスワードハッシュを指定出力先へ作るトップレベル入口がある。 | [deployment/LoginPasswordHash/Program.cs:4\-9](../../srcs/CSharp_ASPNET/deployment/LoginPasswordHash/Program.cs#L4)<br>[deployment/LoginPasswordHash/LoginPasswordHash.csproj:1\-4](../../srcs/CSharp_ASPNET/deployment/LoginPasswordHash/LoginPasswordHash.csproj#L1) |

## 運用・開発支援（主機能数には含めない）

| 名称 | 内容 | 根拠 |
| --- | --- | --- |
| 静的消費者を観測しないStrictJson宣言<br>`SUPPORT-d7d0b488fc141a97` | StrictJsonには厳格JSON読取の実装があるが、取得済みソース全体と登録箇所にReadの静的呼出元を観測しない。既知の補助宣言として保持し、利用中commonや公開APIとは断定しない。 | [Infrastructure/StrictJson.cs:4\-15](../../srcs/CSharp_ASPNET/Infrastructure/StrictJson.cs#L4)<br>[Infrastructure/WebHostSetup.cs:13\-33](../../srcs/CSharp_ASPNET/Infrastructure/WebHostSetup.cs#L13)<br>[Web/Controllers/StudentsController.cs:5\-47](../../srcs/CSharp_ASPNET/Web/Controllers/StudentsController.cs#L5) |
| 公開呼出元を観測しない候補取得宣言<br>`SUPPORT-31604301e909da85` | WebStudentCoordinator.OptionsとWebPresentation.Lookupsに候補取得・整形の宣言がある。取得済み入口・呼出箇所にはOptionsの静的消費者を観測せず、残存する/students/optionsは404応答である。 | [Infrastructure/WebStudentCoordinator.cs:21\-21](../../srcs/CSharp_ASPNET/Infrastructure/WebStudentCoordinator.cs#L21)<br>[Infrastructure/WebPresentation.cs:8\-19](../../srcs/CSharp_ASPNET/Infrastructure/WebPresentation.cs#L8)<br>[Web/Inputs/StudentSearchInput.cs:20\-21](../../srcs/CSharp_ASPNET/Web/Inputs/StudentSearchInput.cs#L20)<br>[Web/Controllers/StudentsController.cs:27\-28](../../srcs/CSharp_ASPNET/Web/Controllers/StudentsController.cs#L27)<br>[Program.cs:5\-7](../../srcs/CSharp_ASPNET/Program.cs#L5) |
| プロジェクト構成・ビルド・出力管理<br>`SUPPORT-527a749133fd82c3` | Web、Core、maintenanceとテストのプロジェクト区分、WebのCompile/Content除外、Coreのテスト向け内部公開、出力先制御、ビルド・パス検証資源を確認した。tests/database/testsは明示テスト参照、bin/obj/build等は出力規則で説明できる。除外領域の内容や過去結果は取得していない。 | [StudentManagement.Web.csproj:1\-7](../../srcs/CSharp_ASPNET/StudentManagement.Web.csproj#L1)<br>[Core/StudentManagement.Core.csproj:1\-12](../../srcs/CSharp_ASPNET/Core/StudentManagement.Core.csproj#L1)<br>[maintenance/StudentMaintenance.csproj:1\-4](../../srcs/CSharp_ASPNET/maintenance/StudentMaintenance.csproj#L1)<br>[StudentManagement.slnx:1\-8](../../srcs/CSharp_ASPNET/StudentManagement.slnx#L1)<br>[Directory.Build.props:1\-15](../../srcs/CSharp_ASPNET/Directory.Build.props#L1)<br>[Core/Properties/AssemblyInfo.cs:1\-2](../../srcs/CSharp_ASPNET/Core/Properties/AssemblyInfo.cs#L1)<br>[build\_paths.py:1\-110](../../srcs/CSharp_ASPNET/build_paths.py#L1)<br>[tools/build.py:1\-101](../../srcs/CSharp_ASPNET/tools/build.py#L1)<br>[tools/build\_config.json:1\-19](../../srcs/CSharp_ASPNET/tools/build_config.json#L1)<br>[tools/test\_output\_paths.py:1\-153](../../srcs/CSharp_ASPNET/tools/test_output_paths.py#L1) |
| DB生成・導入・権限・照合資源<br>`SUPPORT-94abfa22e18090ff` | SQL生成器、導入PowerShell、権限SQL、配備照合SQLを含む。生成器は取得外の仕様入力を読むが、取得済み通常ビルドからの生成実行参照はなく、現存DDLを目録根拠とした。生成一致・SQL実行成功は未確認。 | [database/generate.mjs:1\-110](../../srcs/CSharp_ASPNET/database/generate.mjs#L1)<br>[database/Deploy\-Database.ps1:1\-165](../../srcs/CSharp_ASPNET/database/Deploy-Database.ps1#L1)<br>[database/003\_web\_permissions.sql:1\-26](../../srcs/CSharp_ASPNET/database/003_web_permissions.sql#L1)<br>[database/004\_verify\_deployment.sql:1\-135](../../srcs/CSharp_ASPNET/database/004_verify_deployment.sql#L1)<br>[tools/build.py:70\-88](../../srcs/CSharp_ASPNET/tools/build.py#L70) |
| Azure構築・設定・公開・資格情報補助<br>`SUPPORT-3a8bb29932244152` | Azure資源構築、DB初期化・設定、Webログイン設定、公開及びローカル資格情報取得のスクリプトを含む。これらは配備支援であり、学生管理の主機能には数えない。参照される資格情報ファイル・環境値は取得していない。 | [deployment/Provision\-FreeAzure.ps1:1\-49](../../srcs/CSharp_ASPNET/deployment/Provision-FreeAzure.ps1#L1)<br>[deployment/Configure\-AzureDatabase.ps1:1\-42](../../srcs/CSharp_ASPNET/deployment/Configure-AzureDatabase.ps1#L1)<br>[deployment/Configure\-AzureWebLogin.ps1:1\-30](../../srcs/CSharp_ASPNET/deployment/Configure-AzureWebLogin.ps1#L1)<br>[deployment/Initialize\-AzureDatabase.py:1\-145](../../srcs/CSharp_ASPNET/deployment/Initialize-AzureDatabase.py#L1)<br>[deployment/Publish\-FreeAzure.ps1:1\-44](../../srcs/CSharp_ASPNET/deployment/Publish-FreeAzure.ps1#L1)<br>[deployment/Get\-AzureDatabaseLogin.ps1:1\-6](../../srcs/CSharp_ASPNET/deployment/Get-AzureDatabaseLogin.ps1#L1)<br>[deployment/Get\-AzureWebLogin.ps1:1\-7](../../srcs/CSharp_ASPNET/deployment/Get-AzureWebLogin.ps1#L1) |
| DB・ブラウザー配備検証プログラム<br>`SUPPORT-ad619033c622fcf3` | DatabaseSmoke、リモートDB検証、Azureログインのブラウザー検証を含む。実行はしていない。ログイン検証は現行検索Viewにない\#SRC\-009を参照しており、スクリプトや文書のPASS記述を現行動作の検証済み結果として採用しない。 | [deployment/DatabaseSmoke/Program.cs:3\-9](../../srcs/CSharp_ASPNET/deployment/DatabaseSmoke/Program.cs#L3)<br>[deployment/DatabaseSmoke/DatabaseSmoke.csproj:1\-4](../../srcs/CSharp_ASPNET/deployment/DatabaseSmoke/DatabaseSmoke.csproj#L1)<br>[deployment/Verify\-AzureRemoteDatabase.py:1\-35](../../srcs/CSharp_ASPNET/deployment/Verify-AzureRemoteDatabase.py#L1)<br>[deployment/Verify\-AzureWebLogin.py:45\-88](../../srcs/CSharp_ASPNET/deployment/Verify-AzureWebLogin.py#L45)<br>[Views/Students/Search.cshtml:24\-44](../../srcs/CSharp_ASPNET/Views/Students/Search.cshtml#L24) |
| 配備用ログインハッシュ生成<br>`SUPPORT-392f1aa5f846cf6c` | LoginPasswordHashプロジェクトはWebログイン設定用ハッシュを準備する補助Exeで、Configure\-AzureWebLoginから参照される。 | [deployment/LoginPasswordHash/Program.cs:4\-9](../../srcs/CSharp_ASPNET/deployment/LoginPasswordHash/Program.cs#L4)<br>[deployment/LoginPasswordHash/LoginPasswordHash.csproj:1\-4](../../srcs/CSharp_ASPNET/deployment/LoginPasswordHash/LoginPasswordHash.csproj#L1)<br>[deployment/Configure\-AzureWebLogin.ps1:14\-23](../../srcs/CSharp_ASPNET/deployment/Configure-AzureWebLogin.ps1#L14) |

## 資料（主機能数には含めない）

| 名称 | 内容 | 根拠 |
| --- | --- | --- |
| 取得済みREADME・導入説明文書<br>`MATERIAL-c82c47d447a38aff` | アプリ、DB、Express導入、Azure配備、CLIの説明文書を含む。記載された仕様リンクは追跡せず、過去試験・配備・承認の記述は実行証拠や利用者承認として扱わない。 | [README.md:1\-58](../../srcs/CSharp_ASPNET/README.md#L1)<br>[database/README.md:1\-14](../../srcs/CSharp_ASPNET/database/README.md#L1)<br>[database/EXPRESS17.md:1\-51](../../srcs/CSharp_ASPNET/database/EXPRESS17.md#L1)<br>[deployment/README.md:1\-51](../../srcs/CSharp_ASPNET/deployment/README.md#L1)<br>[maintenance/README.md:1\-11](../../srcs/CSharp_ASPNET/maintenance/README.md#L1) |

## 外部依存（主機能数には含めない）

| 名称 | 内容 | 根拠 |
| --- | --- | --- |
| .NET・ASP.NET Core及びNuGet依存<br>`DEPENDENCY-13fcd24101c76a1f` | net10.0、ASP.NET Core Web SDK/共有フレームワーク、Microsoft.Data.SqlClient 6.1.3、System.Security.Cryptography.Pkcs 9.0.21とlock内の推移依存を宣言する。依存名だけで外部認証等の接続機能を認定しない。 | [Core/StudentManagement.Core.csproj:1\-12](../../srcs/CSharp_ASPNET/Core/StudentManagement.Core.csproj#L1)<br>[StudentManagement.Web.csproj:1\-3](../../srcs/CSharp_ASPNET/StudentManagement.Web.csproj#L1)<br>[deployment/LoginPasswordHash/LoginPasswordHash.csproj:1\-4](../../srcs/CSharp_ASPNET/deployment/LoginPasswordHash/LoginPasswordHash.csproj#L1)<br>[packages.lock.json:1\-201](../../srcs/CSharp_ASPNET/packages.lock.json#L1) |
| 生成・配備・検証の外部ツール依存<br>`DEPENDENCY-ce41ced8e6227548` | 補助資源にはdotnet、Python、Node.js、PowerShell、sqlcmd、Azure CLI、pyodbc/ODBC Driver及びPlaywrightの参照がある。ホストでの導入状況・稼働は確認していない。 | [tools/build.py:66\-88](../../srcs/CSharp_ASPNET/tools/build.py#L66)<br>[database/generate.mjs:1\-5](../../srcs/CSharp_ASPNET/database/generate.mjs#L1)<br>[database/Deploy\-Database.ps1:26\-80](../../srcs/CSharp_ASPNET/database/Deploy-Database.ps1#L26)<br>[deployment/Initialize\-AzureDatabase.py:2\-42](../../srcs/CSharp_ASPNET/deployment/Initialize-AzureDatabase.py#L2)<br>[deployment/Configure\-AzureDatabase.ps1:4\-7](../../srcs/CSharp_ASPNET/deployment/Configure-AzureDatabase.ps1#L4)<br>[deployment/Verify\-AzureWebLogin.py:1\-7](../../srcs/CSharp_ASPNET/deployment/Verify-AzureWebLogin.py#L1) |

## 分類保留

分類保留レコードはない。下記の不確実性・後続調査がなくなった意味ではない。

## 未確認・追加調査の管理項目（解決済みを含む）

合計10件。解決済み4、非阻害4、阻害2、未解決0、未判定0。

### 構文上の呼出候補について、DI登録、引数型、インターフェース及び各入口の原文を照合した確定関係はどうなるか。

- ID: `cb8e661bb820444aab68ff4e0b14cb5f:U001-semantic-connections`
- 関連義務: relationships、behavior
- 範囲理由: 今回の目録は宣言・登録・利用目的を確認した段階であり、AST呼出を意味束縛済みの関係へ昇格していない。元の関係・動作義務は保留。
- 独立判定: blocking / 入口・登録・受入型の主要な静的接続は照合できるが、元目標の関係目録全体は未完了である。catalogの分類は成立し、構文Factだけによる意味束縛・実行の認定は行わない。
- 阻害する義務: relationships
- 判定根拠: [Infrastructure/WebHostSetup.cs:17\-23](../../srcs/CSharp_ASPNET/Infrastructure/WebHostSetup.cs#L17)<br>[Infrastructure/WebStudentCoordinator.cs:3\-24](../../srcs/CSharp_ASPNET/Infrastructure/WebStudentCoordinator.cs#L3)<br>[Core/Contracts.cs:86\-94](../../srcs/CSharp_ASPNET/Core/Contracts.cs#L86)<br>[maintenance/Program.cs:11\-13](../../srcs/CSharp_ASPNET/maintenance/Program.cs#L11)

### StrictJson.Read及びWebStudentCoordinator.Optionsに動的利用や未観測の接続があるか。

- ID: `cb8e661bb820444aab68ff4e0b14cb5f:U002-unobserved-consumers`
- 関連義務: catalog、relationships
- 範囲理由: 取得済み全ソースと入口・登録を逆確認して静的消費者を観測しないが、実行不能とは断定しない。宣言の同一性とsupport分類は確認でき、現行の主機能数はこれらに依存しない。
- 独立判定: non\-blocking / 全原文・登録・逆参照にStrictJson.ReadとCoordinator.Optionsの静的消費者を認めず、残存URLはNotFoundを返す。既知の補助宣言として保持できるため主機能数を阻害しないが、動的利用の不存在は解決していない。
- 阻害する義務: なし
- 判定根拠: [Infrastructure/StrictJson.cs:4\-15](../../srcs/CSharp_ASPNET/Infrastructure/StrictJson.cs#L4)<br>[Infrastructure/WebStudentCoordinator.cs:21\-21](../../srcs/CSharp_ASPNET/Infrastructure/WebStudentCoordinator.cs#L21)<br>[Web/Controllers/StudentsController.cs:27\-28](../../srcs/CSharp_ASPNET/Web/Controllers/StudentsController.cs#L27)<br>[Program.cs:3\-7](../../srcs/CSharp_ASPNET/Program.cs#L3)

### 実配置は元DDLとAzure向け変換DDLのどちらを採用し、現在のDB構造はどちらに一致するか。

- ID: `cb8e661bb820444aab68ff4e0b14cb5f:U003-database-variant`
- 関連義務: relationships、behavior
- 範囲理由: 双方のソース定義は識別できるが実DBは取得・実行対象外。表の目録は成立する一方、配置依存の動作を一方へ断定できない。
- 独立判定: blocking / 同じ7表の元DDLとAzure向け変換は識別でき、catalogには双方が保持されている。実配置の一致先は原文から確定できず、配置を特定した動作判断には未解決として残す。
- 阻害する義務: behavior
- 判定根拠: [database/001\_schema.sql:7\-184](../../srcs/CSharp_ASPNET/database/001_schema.sql#L7)<br>[deployment/Initialize\-AzureDatabase.py:12\-30](../../srcs/CSharp_ASPNET/deployment/Initialize-AzureDatabase.py#L12)<br>[deployment/Initialize\-AzureDatabase.py:93\-131](../../srcs/CSharp_ASPNET/deployment/Initialize-AzureDatabase.py#L93)

### コメントにある別Native production EXEC\-only入口及びstudent\_apiの実装・適用範囲は何か。

- ID: `cb8e661bb820444aab68ff4e0b14cb5f:U004-native-comment`
- 関連義務: catalog、relationships、behavior
- 範囲理由: 当該実装・profileは取得されていない。取得済みWeb登録、CLI、プロジェクト参照にはそれを要求する接続を観測せず、現行ソースの主機能を増減する根拠にはしない。別構成の存在・適用は未確認として残す。
- 独立判定: non\-blocking / 別Native構成へのコメントに対し、選択実装のWeb登録とWeb/Core/CLIのプロジェクト参照に当該入口への現行接続はない。選択ソース目録の欠落を示す根拠はなく、別実装の存在・適用範囲は未確認のまま保持する。
- 阻害する義務: なし
- 判定根拠: [Core/SqlServerStudentService.cs:11\-13](../../srcs/CSharp_ASPNET/Core/SqlServerStudentService.cs#L11)<br>[Infrastructure/WebHostSetup.cs:23\-23](../../srcs/CSharp_ASPNET/Infrastructure/WebHostSetup.cs#L23)<br>[StudentManagement.Web.csproj:1\-7](../../srcs/CSharp_ASPNET/StudentManagement.Web.csproj#L1)<br>[Core/StudentManagement.Core.csproj:1\-12](../../srcs/CSharp_ASPNET/Core/StudentManagement.Core.csproj#L1)<br>[maintenance/StudentMaintenance.csproj:1\-4](../../srcs/CSharp_ASPNET/maintenance/StudentMaintenance.csproj#L1)<br>[database/001\_schema.sql:216\-217](../../srcs/CSharp_ASPNET/database/001_schema.sql#L216)

### 実運用でLocalLoginや評価用入口が有効か、どのDB接続・認証構成が選ばれるか。

- ID: `cb8e661bb820444aab68ff4e0b14cb5f:U005-runtime-configuration`
- 関連義務: behavior
- 範囲理由: 取得設定はLocalLogin無効・接続未設定を示し、配備スクリプトは上書き経路を持つ。秘密値や実環境を取得せず、設定可能な機能の目録と実配置の有効状態を区別する。
- 独立判定: non\-blocking / 元目標は選択ソースの整理であり、設定可能な実装と実運用の有効状態を分ければ目録は成立する。既定設定、読取箇所、配備上書き経路を確認したが、実環境の選択は未確認として残す。
- 阻害する義務: なし
- 判定根拠: [appsettings.json:1\-1](../../srcs/CSharp_ASPNET/appsettings.json#L1)<br>[Infrastructure/LocalLogin.cs:23\-36](../../srcs/CSharp_ASPNET/Infrastructure/LocalLogin.cs#L23)<br>[Infrastructure/WebHostSetup.cs:23\-31](../../srcs/CSharp_ASPNET/Infrastructure/WebHostSetup.cs#L23)<br>[deployment/Configure\-AzureWebLogin.ps1:17\-23](../../srcs/CSharp_ASPNET/deployment/Configure-AzureWebLogin.ps1#L17)<br>[deployment/Configure\-AzureDatabase.ps1:29\-36](../../srcs/CSharp_ASPNET/deployment/Configure-AzureDatabase.ps1#L29)

### 現行検索Viewに存在しない\#SRC\-009を参照するAzureログイン検証は、どのソース版を対象にしたものか。

- ID: `cb8e661bb820444aab68ff4e0b14cb5f:U006-verification-version`
- 関連義務: behavior
- 範囲理由: 検証資源の対象版と記載結果は未検証。支援プログラムとしての分類には影響しないが、現行画面の成功証拠には採用できない。
- 独立判定: non\-blocking / 検証スクリプトの対象版を確定する履歴は供給原文にない。現行画面との対象差を保持し、実行証拠へ採用しないためcatalogは阻害しないが、対象版の質問自体は未解決である。
- 阻害する義務: なし
- 判定根拠: [deployment/Verify\-AzureWebLogin.py:48\-58](../../srcs/CSharp_ASPNET/deployment/Verify-AzureWebLogin.py#L48)<br>[Views/Students/Search.cshtml:24\-44](../../srcs/CSharp_ASPNET/Views/Students/Search.cshtml#L24)<br>[deployment/README.md:49\-49](../../srcs/CSharp_ASPNET/deployment/README.md#L49)

### U001に沿って、MVC入口、WebStudentCoordinator、IStudentService登録、Core及びCLIの確定接続を原文で照合し、構文呼出候補と区別する。

- ID: `followup:08d3fbf196ede900ddac98d3c5b32caccfe5a49ad3da0f68293968f40b9a5308`
- 関連義務: relationships
- 範囲理由: An explicit relationship investigation request remains open until a local independent reviewer resolves it from original source.
- 独立判定: resolved / 限定された接続照合は回答済み。Programの登録、Controllerの受入型、Coordinatorの契約利用、IStudentServiceの具体登録、CLIの直接構築・選択が原文で整合する。実行やコンパイラによる意味束縛は認定せず、関係目録全体の義務はU001に残す。
- 阻害する義務: なし
- 判定根拠: [Program.cs:2\-6](../../srcs/CSharp_ASPNET/Program.cs#L2)<br>[Web/Controllers/StudentsController.cs:5\-6](../../srcs/CSharp_ASPNET/Web/Controllers/StudentsController.cs#L5)<br>[Infrastructure/WebStudentCoordinator.cs:3\-24](../../srcs/CSharp_ASPNET/Infrastructure/WebStudentCoordinator.cs#L3)<br>[Infrastructure/WebHostSetup.cs:17\-23](../../srcs/CSharp_ASPNET/Infrastructure/WebHostSetup.cs#L17)<br>[Core/SqlServerStudentService.cs:13\-13](../../srcs/CSharp_ASPNET/Core/SqlServerStudentService.cs#L13)<br>[Core/Contracts.cs:86\-94](../../srcs/CSharp_ASPNET/Core/Contracts.cs#L86)<br>[maintenance/Program.cs:11\-13](../../srcs/CSharp_ASPNET/maintenance/Program.cs#L11)

### U003・U005について、元DDL、Azure変換、Webトークン選択及び設定による動作差をソース上で確認し、実配置の選択は未確認のまま保持する。

- ID: `followup:326a51b0abc40653ead92c927974d6cc44657a22fd5c27e341b30e738c305ccf`
- 関連義務: behavior
- 範囲理由: An explicit behavior investigation request remains open until a local independent reviewer resolves it from original source.
- 独立判定: resolved / ソース上の差は確認済み。Azure入力は5参照列の幅とseed照合順序を変換し、Web登録はメモリー確認方式を選ぶ。認証の設定読取・上書き経路も確認した。実配置の選択はU003・U005に残す。
- 阻害する義務: なし
- 判定根拠: [deployment/Initialize\-AzureDatabase.py:12\-30](../../srcs/CSharp_ASPNET/deployment/Initialize-AzureDatabase.py#L12)<br>[Infrastructure/WebHostSetup.cs:23\-23](../../srcs/CSharp_ASPNET/Infrastructure/WebHostSetup.cs#L23)<br>[Core/SqlServerStudentService.cs:269\-275](../../srcs/CSharp_ASPNET/Core/SqlServerStudentService.cs#L269)<br>[Core/SqlServerStudentService.cs:322\-335](../../srcs/CSharp_ASPNET/Core/SqlServerStudentService.cs#L322)<br>[Infrastructure/LocalLogin.cs:23\-36](../../srcs/CSharp_ASPNET/Infrastructure/LocalLogin.cs#L23)<br>[deployment/Configure\-AzureWebLogin.ps1:17\-23](../../srcs/CSharp_ASPNET/deployment/Configure-AzureWebLogin.ps1#L17)

### U006の検証スクリプトと現行画面の対象差を確認し、文書上の試験主張を実行証拠から分離したまま扱う。

- ID: `followup:98b841b7c959c42f6b24b8777408e381c14870508e8c592fb766e00012760a94`
- 関連義務: behavior
- 範囲理由: An explicit behavior investigation request remains open until a local independent reviewer resolves it from original source.
- 独立判定: resolved / 対象差の調査は回答済み。検証は都道府県選択\#SRC\-009を要求するが、現行検索Viewは4検索条件を定義する。文書の検証記述は報告上の主張であり実行証拠ではない。正確な対象版はU006に残す。
- 阻害する義務: なし
- 判定根拠: [deployment/Verify\-AzureWebLogin.py:48\-58](../../srcs/CSharp_ASPNET/deployment/Verify-AzureWebLogin.py#L48)<br>[Views/Students/Search.cshtml:24\-44](../../srcs/CSharp_ASPNET/Views/Students/Search.cshtml#L24)<br>[README.md:13\-15](../../srcs/CSharp_ASPNET/README.md#L13)<br>[deployment/README.md:39\-41](../../srcs/CSharp_ASPNET/deployment/README.md#L39)

### U002の宣言について観測済み静的消費者なしを維持し、廃止URL、宣言内部の呼出候補、動的利用の未確認を分けて関係目録へ引き継ぐ。

- ID: `followup:a5b42346bb2523705dd38192e5455cae1b668570858c4347fda28cbf3fedd277`
- 関連義務: relationships
- 範囲理由: An explicit relationship investigation request remains open until a local independent reviewer resolves it from original source.
- 独立判定: resolved / 全索引・原文の逆確認で静的消費者なしを維持できる。Options内部の候補取得・整形、NotFoundを返す旧URL、未接続のStrictJson宣言を区別した。動的利用の未確認はU002として引き継ぐ。
- 阻害する義務: なし
- 判定根拠: [Infrastructure/StrictJson.cs:4\-15](../../srcs/CSharp_ASPNET/Infrastructure/StrictJson.cs#L4)<br>[Infrastructure/WebStudentCoordinator.cs:21\-21](../../srcs/CSharp_ASPNET/Infrastructure/WebStudentCoordinator.cs#L21)<br>[Infrastructure/WebPresentation.cs:8\-19](../../srcs/CSharp_ASPNET/Infrastructure/WebPresentation.cs#L8)<br>[Web/Controllers/StudentsController.cs:27\-28](../../srcs/CSharp_ASPNET/Web/Controllers/StudentsController.cs#L27)<br>[Infrastructure/WebHostSetup.cs:13\-33](../../srcs/CSharp_ASPNET/Infrastructure/WebHostSetup.cs#L13)

## 独立分類検証

### ソース事実の利用に対する独立判定

- 判定: pass
- 理由: 全Fact索引と75原文を照合し、選択Fact外の入口・CLI・未対応形式・補助資源も点検した。引用Factは対応する宣言・呼出構文を支持し、業務目的は画面・呼出文脈で補完されている。構文を意味束縛・実行証拠へ昇格する流用、又は重要な目録欠落を認めない。
- 原文根拠: [Program.cs:2\-8](../../srcs/CSharp_ASPNET/Program.cs#L2)<br>[Infrastructure/WebHostSetup.cs:17\-23](../../srcs/CSharp_ASPNET/Infrastructure/WebHostSetup.cs#L17)<br>[Web/Controllers/StudentsController.cs:5\-46](../../srcs/CSharp_ASPNET/Web/Controllers/StudentsController.cs#L5)<br>[Infrastructure/WebStudentCoordinator.cs:3\-28](../../srcs/CSharp_ASPNET/Infrastructure/WebStudentCoordinator.cs#L3)<br>[maintenance/Program.cs:4\-17](../../srcs/CSharp_ASPNET/maintenance/Program.cs#L4)<br>[Views/Students/Search.cshtml:14\-77](../../srcs/CSharp_ASPNET/Views/Students/Search.cshtml#L14)<br>[Views/Students/Edit.cshtml:34\-176](../../srcs/CSharp_ASPNET/Views/Students/Edit.cshtml#L34)<br>[database/001\_schema.sql:7\-184](../../srcs/CSharp_ASPNET/database/001_schema.sql#L7)<br>[deployment/Initialize\-AzureDatabase.py:12\-30](../../srcs/CSharp_ASPNET/deployment/Initialize-AzureDatabase.py#L12)<br>[StudentManagement.Web.csproj:3\-6](../../srcs/CSharp_ASPNET/StudentManagement.Web.csproj#L3)<br>[database/generate.mjs:6\-22](../../srcs/CSharp_ASPNET/database/generate.mjs#L6)<br>[deployment/Verify\-AzureWebLogin.py:48\-58](../../srcs/CSharp_ASPNET/deployment/Verify-AzureWebLogin.py#L48)

事実のIDが実在することと、その事実が業務の主張を裏付けることを分けて確認した。

### 範囲・過分割・過統合・除外の検査

| scope | 判定 | 理由 | 根拠 |
| --- | --- | --- | --- |
| selected\-system | pass | 選択範囲全体の入口・プロジェクト所属・逆利用・除外・生成参照を確認した。専用ログイン・メニュー、独立照会と学生保守、CLIのクラス・コード保守を含む7主機能の分割を支持する。評価入口・生存確認・配備検証・ハッシュ生成は技術又は配備目的であり、旧URLと未消費宣言も保持されている。目録の対象・件数を変える未解決接続は認めず、後続の関係・動作義務は保留のままである。 | [Views/Account/Login.cshtml:1\-13](../../srcs/CSharp_ASPNET/Views/Account/Login.cshtml#L1)<br>[Views/Menu/Index.cshtml:1\-7](../../srcs/CSharp_ASPNET/Views/Menu/Index.cshtml#L1)<br>[Web/Controllers/AccountController.cs:10\-41](../../srcs/CSharp_ASPNET/Web/Controllers/AccountController.cs#L10)<br>[Web/Controllers/StudentsController.cs:5\-46](../../srcs/CSharp_ASPNET/Web/Controllers/StudentsController.cs#L5)<br>[maintenance/Program.cs:4\-17](../../srcs/CSharp_ASPNET/maintenance/Program.cs#L4)<br>[StudentManagement.slnx:1\-8](../../srcs/CSharp_ASPNET/StudentManagement.slnx#L1)<br>[StudentManagement.Web.csproj:3\-6](../../srcs/CSharp_ASPNET/StudentManagement.Web.csproj#L3)<br>[Infrastructure/WebHostSetup.cs:30\-32](../../srcs/CSharp_ASPNET/Infrastructure/WebHostSetup.cs#L30)<br>[deployment/DatabaseSmoke/Program.cs:3\-9](../../srcs/CSharp_ASPNET/deployment/DatabaseSmoke/Program.cs#L3)<br>[deployment/LoginPasswordHash/Program.cs:4\-9](../../srcs/CSharp_ASPNET/deployment/LoginPasswordHash/Program.cs#L4)<br>[database/generate.mjs:6\-22](../../srcs/CSharp_ASPNET/database/generate.mjs#L6)<br>[tools/build.py:66\-88](../../srcs/CSharp_ASPNET/tools/build.py#L66) |

### 個別の分類検査

| 対象 | 判定 | 理由 | 根拠 |
| --- | --- | --- | --- |
| ログイン | pass | 利用者が専用フォームから利用開始を要求し、認証セッション又は失敗通知を得る独立したシステム目的がある。認証commonへの統合ではこのタスクを表せない。 | [Views/Account/Login.cshtml:1\-13](../../srcs/CSharp_ASPNET/Views/Account/Login.cshtml#L1)<br>[Web/Controllers/AccountController.cs:10\-34](../../srcs/CSharp_ASPNET/Web/Controllers/AccountController.cs#L10) |
| ログアウト | pass | 認証済み利用者が業務作業と独立してセッション終了を完了できる。認証管理への統合案も可能だが、開始と終了の別目的による分割は支持される。 | [Views/Shared/\_Layout.cshtml:2\-4](../../srcs/CSharp_ASPNET/Views/Shared/_Layout.cshtml#L2)<br>[Web/Controllers/AccountController.cs:36\-41](../../srcs/CSharp_ASPNET/Web/Controllers/AccountController.cs#L36) |
| 学生管理の操作選択 | pass | 認証済み利用者が専用メニューで学生管理作業を選択し、目的入口へ進むタスクを持つ。共通Layoutとは別の本文・入口・復帰リンクがあり、commonへの一括分類は適切でない。 | [Web/Controllers/MenuController.cs:6\-10](../../srcs/CSharp_ASPNET/Web/Controllers/MenuController.cs#L6)<br>[Views/Menu/Index.cshtml:1\-7](../../srcs/CSharp_ASPNET/Views/Menu/Index.cshtml#L1)<br>[Views/Students/Search.cshtml:15\-18](../../srcs/CSharp_ASPNET/Views/Students/Search.cshtml#L15) |
| 学生情報の検索・照会 | pass | Viewerを含む利用者が学生を探して登録情報を確認する完結した照会目的を持つ。書込みを伴う保守との分離、一覧・詳細を同じ照会にまとめる粒度が支持される。 | [Views/Students/Search.cshtml:24\-71](../../srcs/CSharp_ASPNET/Views/Students/Search.cshtml#L24)<br>[Views/Students/Edit.cshtml:34\-43](../../srcs/CSharp_ASPNET/Views/Students/Edit.cshtml#L34)<br>[Web/Models/StudentEditPageModel.cs:8\-14](../../srcs/CSharp_ASPNET/Web/Models/StudentEditPageModel.cs#L8) |
| 学生情報の登録・保守 | pass | 担当者・管理者が学生台帳を整備し、保存・論理削除結果を受け取る目的がある。同じ対象と共用保守画面に属する各モード・確認を操作としてまとめる説明は妥当である。 | [Views/Students/Edit.cshtml:54\-173](../../srcs/CSharp_ASPNET/Views/Students/Edit.cshtml#L54)<br>[Web/Controllers/StudentsController.cs:29\-44](../../srcs/CSharp_ASPNET/Web/Controllers/StudentsController.cs#L29) |
| クラスマスタ保守 | pass | DB管理主体が年度別クラスを整備して保存結果を得る独立タスクである。CLIは独立Exeとして所属し、コード保守と統合する案より対象・目的の区別が明確である。 | [maintenance/Program.cs:4\-13](../../srcs/CSharp_ASPNET/maintenance/Program.cs#L4)<br>[Core/MasterMaintenanceService.cs:17\-30](../../srcs/CSharp_ASPNET/Core/MasterMaintenanceService.cs#L17)<br>[Core/MasterMaintenanceService.cs:65\-76](../../srcs/CSharp_ASPNET/Core/MasterMaintenanceService.cs#L65)<br>[maintenance/StudentMaintenance.csproj:1\-4](../../srcs/CSharp_ASPNET/maintenance/StudentMaintenance.csproj#L1) |
| 業務コード保守 | pass | DB管理主体が分類別業務コードを整備して結果を得るタスクであり、学生保守の実装補助に隠せない。クラスとは異なる管理対象による主機能分割が支持される。 | [maintenance/Program.cs:4\-13](../../srcs/CSharp_ASPNET/maintenance/Program.cs#L4)<br>[Core/MasterMaintenanceService.cs:79\-120](../../srcs/CSharp_ASPNET/Core/MasterMaintenanceService.cs#L79) |
| 検索結果の表示調整・条件クリア | pass | 表示調整・条件クリアは学生照会を進める操作である。個別操作への細分化は可能だが、独立した主機能目的は示されない。 | [Views/Students/Search.cshtml:45\-71](../../srcs/CSharp_ASPNET/Views/Students/Search.cshtml#L45)<br>[Web/Controllers/StudentsController.cs:23\-26](../../srcs/CSharp_ASPNET/Web/Controllers/StudentsController.cs#L23) |
| 選択学生の詳細参照 | pass | 一覧から選んだ学生の確認は照会の子タスクであり、編集と共用する詳細画面だけを別主機能に昇格させる根拠はない。 | [Views/Students/Search.cshtml:64\-67](../../srcs/CSharp_ASPNET/Views/Students/Search.cshtml#L64)<br>[Web/Controllers/StudentsController.cs:30\-31](../../srcs/CSharp_ASPNET/Web/Controllers/StudentsController.cs#L30)<br>[Views/Students/Edit.cshtml:34\-43](../../srcs/CSharp_ASPNET/Views/Students/Edit.cshtml#L34) |
| 保守対象学生の検索・選択 | pass | 既存学生の保守では検索・編集リンクが対象選択の準備になる。独立照会との共用を目的別に記録しており、技術入口の重複を主機能の重複にしていない。 | [Views/Students/Search.cshtml:64\-67](../../srcs/CSharp_ASPNET/Views/Students/Search.cshtml#L64)<br>[Web/Controllers/StudentsController.cs:30\-31](../../srcs/CSharp_ASPNET/Web/Controllers/StudentsController.cs#L30) |
| 学生の新規入力・保存 | pass | 新規入力・登録は学生保守の新規モードとして共用画面・保存処理に属する。別受付工程を示す根拠はなく、操作分類が支持される。 | [Web/Controllers/StudentsController.cs:29\-39](../../srcs/CSharp_ASPNET/Web/Controllers/StudentsController.cs#L29)<br>[Views/Students/Edit.cshtml:54\-56](../../srcs/CSharp_ASPNET/Views/Students/Edit.cshtml#L54)<br>[Views/Students/Edit.cshtml:145\-147](../../srcs/CSharp_ASPNET/Views/Students/Edit.cshtml#L145) |
| 既存学生の編集・保存 | pass | 既存学生の修正・保存は学生保守の操作である。参照と共有する入口を利用目的で分け、画面・モードごとの過剰な主機能分割を避けている。 | [Web/Controllers/StudentsController.cs:30\-39](../../srcs/CSharp_ASPNET/Web/Controllers/StudentsController.cs#L30)<br>[Views/Students/Edit.cshtml:54\-56](../../srcs/CSharp_ASPNET/Views/Students/Edit.cshtml#L54)<br>[Views/Students/Edit.cshtml:145\-147](../../srcs/CSharp_ASPNET/Views/Students/Edit.cshtml#L145) |
| 重複候補の確認・続行 | pass | 重複候補確認は学生保存に従属する続行判断であり、独立した審査タスクの入口はない。ダイアログを保守操作に置く分類が適切である。 | [Views/Students/Edit.cshtml:153\-162](../../srcs/CSharp_ASPNET/Views/Students/Edit.cshtml#L153)<br>[Core/SqlServerStudentService.cs:278\-282](../../srcs/CSharp_ASPNET/Core/SqlServerStudentService.cs#L278) |
| 学生情報の論理削除 | pass | 選択学生を論理削除する管理者操作は同じ保守画面と対象に属する。役割差だけで独立主機能に分ける必要はない。 | [Views/Students/Edit.cshtml:150\-173](../../srcs/CSharp_ASPNET/Views/Students/Edit.cshtml#L150)<br>[Infrastructure/WebStudentCoordinator.cs:24\-24](../../srcs/CSharp_ASPNET/Infrastructure/WebStudentCoordinator.cs#L24) |
| 入力取消・再読込・検索復帰 | pass | 取消・再読込・検索復帰は学生保守を再開又は終了する補助操作である。個別操作への分割は可能だが主機能数には影響しない。 | [Views/Students/Edit.cshtml:148\-152](../../srcs/CSharp_ASPNET/Views/Students/Edit.cshtml#L148)<br>[Web/Controllers/StudentsController.cs:41\-41](../../srcs/CSharp_ASPNET/Web/Controllers/StudentsController.cs#L41)<br>[wwwroot/js/site.js:117\-147](../../srcs/CSharp_ASPNET/wwwroot/js/site.js#L117) |
| ローカル認証・Cookieセッション | pass | 認証検証とCookie受入を中央実装が担い、Account入口とホストが利用する。独立ログイン機能を保持したうえで共通実装を別記している。 | [Infrastructure/LocalLogin.cs:53\-89](../../srcs/CSharp_ASPNET/Infrastructure/LocalLogin.cs#L53)<br>[Infrastructure/WebHostSetup.cs:15\-18](../../srcs/CSharp_ASPNET/Infrastructure/WebHostSetup.cs#L15)<br>[Web/Controllers/AccountController.cs:18\-41](../../srcs/CSharp_ASPNET/Web/Controllers/AccountController.cs#L18) |
| 要求主体・役割別認可 | pass | 要求主体と権限確認を中央化し、照会・保存・削除から利用される。各入口へまとめる案より共有責務を明示できる。 | [Infrastructure/RequestIdentity.cs:4\-16](../../srcs/CSharp_ASPNET/Infrastructure/RequestIdentity.cs#L4)<br>[Infrastructure/WebStudentCoordinator.cs:7\-24](../../srcs/CSharp_ASPNET/Infrastructure/WebStudentCoordinator.cs#L7) |
| 学生照会・保存のCoreサービス | pass | 登録済みCore実装が照会・保守を横断する永続化と業務規則を担う。主機能を別に保持しており、サービス名への業務機能の埋没はない。 | [Infrastructure/WebHostSetup.cs:23\-23](../../srcs/CSharp_ASPNET/Infrastructure/WebHostSetup.cs#L23)<br>[Infrastructure/WebStudentCoordinator.cs:14\-24](../../srcs/CSharp_ASPNET/Infrastructure/WebStudentCoordinator.cs#L14)<br>[Core/SqlServerStudentService.cs:115\-209](../../srcs/CSharp_ASPNET/Core/SqlServerStudentService.cs#L115)<br>[Core/SqlServerStudentService.cs:219\-409](../../srcs/CSharp_ASPNET/Core/SqlServerStudentService.cs#L219) |
| マスタ保守のCoreサービス | pass | クラス・コードの二管理タスクが同じ中央サービスを利用する。利用者機能の分割と実装の集約を区別したcommon分類が妥当である。 | [Core/MasterMaintenanceService.cs:15\-30](../../srcs/CSharp_ASPNET/Core/MasterMaintenanceService.cs#L15)<br>[Core/MasterMaintenanceService.cs:79\-79](../../srcs/CSharp_ASPNET/Core/MasterMaintenanceService.cs#L79)<br>[maintenance/Program.cs:11\-13](../../srcs/CSharp_ASPNET/maintenance/Program.cs#L11) |
| 入力正規化・学生共通検証 | pass | 学生・検索・マスタ入力が使う中央正規化責務がある。個別保存処理への統合では共有する規則の所在が失われる。 | [Core/StudentNormalizer.cs:19\-169](../../srcs/CSharp_ASPNET/Core/StudentNormalizer.cs#L19)<br>[Core/SqlServerStudentService.cs:225\-229](../../srcs/CSharp_ASPNET/Core/SqlServerStudentService.cs#L225)<br>[Core/MasterMaintenanceService.cs:33\-36](../../srcs/CSharp_ASPNET/Core/MasterMaintenanceService.cs#L33)<br>[Core/Contracts.cs:48\-56](../../srcs/CSharp_ASPNET/Core/Contracts.cs#L48) |
| 和暦・西暦日付変換 | pass | 日付表現・検証を中央化し、学生入力・読込とマスタ保守が利用する。画面ごとの分割より原文の共有責務に合う。 | [Core/JapaneseDateService.cs:7\-62](../../srcs/CSharp_ASPNET/Core/JapaneseDateService.cs#L7)<br>[Core/StudentNormalizer.cs:127\-137](../../srcs/CSharp_ASPNET/Core/StudentNormalizer.cs#L127)<br>[Core/MasterMaintenanceService.cs:36\-36](../../srcs/CSharp_ASPNET/Core/MasterMaintenanceService.cs#L36)<br>[Core/SqlServerStudentService.cs:175\-187](../../srcs/CSharp_ASPNET/Core/SqlServerStudentService.cs#L175) |
| SQL補助・共通書込ゲート | pass | 学生実装内に置かれたSQL補助・書込ゲートをマスタ実装も明示利用する。宣言位置だけで学生専用に限定しない分類が支持される。 | [Core/SqlServerStudentService.cs:65\-73](../../srcs/CSharp_ASPNET/Core/SqlServerStudentService.cs#L65)<br>[Core/SqlServerStudentService.cs:92\-102](../../srcs/CSharp_ASPNET/Core/SqlServerStudentService.cs#L92)<br>[Core/SqlServerStudentService.cs:321\-321](../../srcs/CSharp_ASPNET/Core/SqlServerStudentService.cs#L321)<br>[Core/MasterMaintenanceService.cs:5\-5](../../srcs/CSharp_ASPNET/Core/MasterMaintenanceService.cs#L5)<br>[Core/MasterMaintenanceService.cs:74\-77](../../srcs/CSharp_ASPNET/Core/MasterMaintenanceService.cs#L74) |
| マスタ監査操作の分類 | pass | 監査操作名を統一する小さな中央規則で、クラス・コード保存の双方が利用する。マスタサービスへの一括記録も可能だが、この分離に実際の共有責務がある。 | [Core/AuditOperation.cs:4\-8](../../srcs/CSharp_ASPNET/Core/AuditOperation.cs#L4)<br>[Core/MasterMaintenanceService.cs:75\-75](../../srcs/CSharp_ASPNET/Core/MasterMaintenanceService.cs#L75)<br>[Core/MasterMaintenanceService.cs:119\-119](../../srcs/CSharp_ASPNET/Core/MasterMaintenanceService.cs#L119) |
| 検索状態と共通識別子の保持 | pass | 検索文脈の中央保持に加え、認証・編集でも使う識別子生成を提供する。別部品への分割案は可能だが、現行の責務と消費者が原文で支持される。 | [Infrastructure/SearchContextStore.cs:7\-18](../../srcs/CSharp_ASPNET/Infrastructure/SearchContextStore.cs#L7)<br>[Infrastructure/WebStudentCoordinator.cs:5\-20](../../srcs/CSharp_ASPNET/Infrastructure/WebStudentCoordinator.cs#L5)<br>[Infrastructure/LocalLogin.cs:77\-77](../../srcs/CSharp_ASPNET/Infrastructure/LocalLogin.cs#L77)<br>[Infrastructure/EditorSnapshotStore.cs:9\-9](../../srcs/CSharp_ASPNET/Infrastructure/EditorSnapshotStore.cs#L9) |
| 編集スナップショット管理 | pass | 新規・既存・保存・取消で共有するサーバー保持責務がある。画面モデルだけへの統合では保持と所有者確認の所在を表せない。 | [Infrastructure/EditorSnapshotStore.cs:5\-12](../../srcs/CSharp_ASPNET/Infrastructure/EditorSnapshotStore.cs#L5)<br>[Infrastructure/WebHostSetup.cs:17\-17](../../srcs/CSharp_ASPNET/Infrastructure/WebHostSetup.cs#L17)<br>[Web/Controllers/StudentsController.cs:31\-43](../../srcs/CSharp_ASPNET/Web/Controllers/StudentsController.cs#L31) |
| 復帰先メッセージ保持 | pass | 保存側と検索表示側が一時通知を受け渡す中央サービスである。Controller補助への統合案もあるが、共有保持としてのcommon分類を支持する。 | [Infrastructure/FlashMessageStore.cs:4\-10](../../srcs/CSharp_ASPNET/Infrastructure/FlashMessageStore.cs#L4)<br>[Web/Controllers/StudentsController.cs:11\-11](../../srcs/CSharp_ASPNET/Web/Controllers/StudentsController.cs#L11)<br>[Web/Controllers/StudentsController.cs:44\-44](../../srcs/CSharp_ASPNET/Web/Controllers/StudentsController.cs#L44) |
| 学生Web処理の調整 | pass | 複数MVC入口が要求・状態・認可・Core利用の調整を共有する。利用者タスクを別記したうえで調整実装をcommonに置く粒度は適切である。 | [Infrastructure/WebStudentCoordinator.cs:3\-28](../../srcs/CSharp_ASPNET/Infrastructure/WebStudentCoordinator.cs#L3)<br>[Infrastructure/WebHostSetup.cs:17\-17](../../srcs/CSharp_ASPNET/Infrastructure/WebHostSetup.cs#L17)<br>[Web/Controllers/StudentsController.cs:18\-18](../../srcs/CSharp_ASPNET/Web/Controllers/StudentsController.cs#L18)<br>[Web/Controllers/StudentsController.cs:31\-43](../../srcs/CSharp_ASPNET/Web/Controllers/StudentsController.cs#L31) |
| 日時・結果・エラーの表示変換 | pass | 日時・一覧・状態・エラー表現を調整処理、Controller、ホストが共有する。未消費の候補整形宣言を現行公開APIと同一視しない説明も原文に合う。 | [Infrastructure/WebPresentation.cs:3\-31](../../srcs/CSharp_ASPNET/Infrastructure/WebPresentation.cs#L3)<br>[Infrastructure/WebStudentCoordinator.cs:26\-27](../../srcs/CSharp_ASPNET/Infrastructure/WebStudentCoordinator.cs#L26)<br>[Web/Controllers/StudentsController.cs:38\-45](../../srcs/CSharp_ASPNET/Web/Controllers/StudentsController.cs#L38)<br>[Infrastructure/WebHostSetup.cs:27\-27](../../srcs/CSharp_ASPNET/Infrastructure/WebHostSetup.cs#L27) |
| Web登録・要求保護・共通例外処理 | pass | Programから使う中央登録と要求横断処理を担う。起動支援への一括分類も可能だが、各要求に適用される共通責務を含むためcommonは妥当である。 | [Program.cs:3\-5](../../srcs/CSharp_ASPNET/Program.cs#L3)<br>[Infrastructure/WebHostSetup.cs:13\-29](../../srcs/CSharp_ASPNET/Infrastructure/WebHostSetup.cs#L13)<br>[Infrastructure/AntiforgeryResultFilter.cs:5\-10](../../srcs/CSharp_ASPNET/Infrastructure/AntiforgeryResultFilter.cs#L5) |
| 共通レイアウト・通知・画面操作支援 | pass | View共通設定、Layout、部分Viewと読込資源が画面横断の表示・操作支援を担う。学生専用資源の細分化は可能だが、専用メニュー本文やログイン目的をここへ隠していない。 | [Views/\_ViewStart.cshtml:1\-1](../../srcs/CSharp_ASPNET/Views/_ViewStart.cshtml#L1)<br>[Views/Shared/\_Layout.cshtml:1\-5](../../srcs/CSharp_ASPNET/Views/Shared/_Layout.cshtml#L1)<br>[Views/Shared/\_MessagePanel.cshtml:1\-3](../../srcs/CSharp_ASPNET/Views/Shared/_MessagePanel.cshtml#L1)<br>[Views/Students/Search.cshtml:19\-19](../../srcs/CSharp_ASPNET/Views/Students/Search.cshtml#L19)<br>[wwwroot/js/site.js:1\-231](../../srcs/CSharp_ASPNET/wwwroot/js/site.js#L1) |

[独立検証JSON](result/validation.json)

## 取得時に除外された材料

| パス | 理由 |
| --- | --- |
| .gitignore | unsupported\-text\-material |
| Core/bin | excluded\-directory |
| Core/obj | excluded\-directory |
| bin | excluded\-directory |
| build | excluded\-directory |
| database/tests | excluded\-directory |
| deployment/DatabaseSmoke/bin | excluded\-directory |
| deployment/DatabaseSmoke/obj | excluded\-directory |
| deployment/LoginPasswordHash/bin | excluded\-directory |
| deployment/LoginPasswordHash/obj | excluded\-directory |
| deployment/\_\_pycache\_\_ | excluded\-directory |
| obj | excluded\-directory |
| spec\-eval | excluded\-directory |
| tests | excluded\-directory |

## 人手で確認すること

- 主機能の利用目的と完了成果に、独立性と同じ粒度があるか。
- 子操作の親・利用文脈と、共通能力の利用先が妥当か。
- 取得範囲と集計範囲を混同せず、管理業務を入口形態で落としていないか。
- 保留、範囲外、不確実性の判断に納得できるか。

入力プログラム・SQL・DBは実行していない。新しい分類の人手承認と後続2層は未実施。
