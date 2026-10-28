# discovery-agent 収束・独立検証レビュー

**改名前test-project1の実行記録。** project移動後も証拠内のprojectId・絶対パス・hashは原値を保持する。新sample-project1は未解析で、現在の既定成果先は`spec-reverse/CSharp_ASPNET/`。ここに保持する旧成果・targetを新projectへ転用しない。ソースリンクは移動後の参照位置を示し、当時の根拠は記録されたsnapshotとhashで識別する。

**7組の保存済み草稿から収束と独立検証を完了した。123記録・33分類の逐項検査は合格したが、全体目録は範囲境界の根拠不足により不合格・未採用。**

2026-10-28。test-project1 / csharp_aspnet、discoveryのみ。最終launcherは終了コード2、結果は`needs-investigation`、`published=false`。sessionはversion 0・acceptedRequirements空のままで、完了receiptを発行していない。再抽出、fresh初期化、relationship／behavior Agent、入力アプリ・ビルド・スクリプト・SQL・DBの実行は行っていない。

## 今回の判定

| 検査 | 結果 | 意味 |
| --- | --- | --- |
| 作者による収束 | supported、4 round | 保存済み草稿の原義務被覆を作者が声明した。独立合格ではない |
| 独立review集合 | 23／23分片完了 | 21組の記録、2待問の1組、全体検査1組 |
| recordChecks | 123／123 pass | 既存候補の各記述を原文で確認 |
| classificationChecks | 33／33 pass | 主機能6・子操作7・共通20の候補内分類を確認 |
| factUsageCheck | pass | 構文事実の利用を原文と照合。実行成功の検査ではない |
| 既存2待問 | reviewerはresolvedと判断 | 静的な質問への回答。全体未採用のため正式ContextBaseの未知解除ではない |
| 全体catalog | fail | 範囲境界に新たな阻害unknownがある |
| selected-system scope | unknown | 許可外領域の本番コンパイル所属と目録への影響を確定できない |
| 採用・正式公開 | なし | 旧機械成果を保持した |

## 阻害事項：除外領域とコンパイル範囲の境界

独立検証は`global-0022-omitted-compile-boundary`をblocking、新規unknownを1件提出した。

[StudentManagement.Web.csproj:4](../../srcs/CSharp_ASPNET/StudentManagement.Web.csproj#L4)は`spec-eval`をContent／Noneから除いている一方、Compileの除外には含めていない。[Directory.Build.props:10-11](../../srcs/CSharp_ASPNET/Directory.Build.props#L10)にも、その領域を明示的に対象外とする設定はない。取得manifestでは`spec-eval`を除外ディレクトリの名前としてだけ保持し、内容は取得していない。

このため、**現在の許可済み根拠だけでは、除外領域がコンパイル所属や目録被覆へ影響しないことを確認できない**、という検証者の判定になった。実際に未取得の業務機能が存在する、当該領域が確実にコンパイルされる、又は禁止資料を読む必要があると証明したものではない。禁止範囲への読取りを拡張せず、入力・凍結候補も変更していない。

作者の収束声明と局所検査の成功だけで、全体検査のfail／unknownを上書きしない。判定にはこの範囲前提の人手確認が残る。

## 軽微な補足と後続層

- `records-0002-layout-consumers`（minor）：共通レイアウトのconsumersに学生情報照会・学生情報登録／保守も補足できる。[Views/_ViewStart.cshtml:1](../../srcs/CSharp_ASPNET/Views/_ViewStart.cshtml#L1)と[StudentsController.cs:8-30](../../srcs/CSharp_ASPNET/Web/Controllers/StudentsController.cs#L8)が根拠。共通分類や主機能候補数を変更する指摘ではない。候補本文は修正していない。
- 元のrelationship／behavior向けfollowupは、独立検証者が原文の型・DI・SQL・保存／削除処理を読み、具体的な2質問にresolvedを返した。新しいrelationship／behavior記録、当該層の義務合格、正式な未知解除を意味しない。元候補の2 followupと全体未採用の状態を保持する。
- relationship-agentとbehavior-agentは起動していない。既存の後続成果を今回の結果として使っていない。

## 入力・候補・保持成果の版

| 対象 | 今回の識別情報 |
| --- | --- |
| source | test-project1/srcs/CSharp_ASPNET、78取得ファイル |
| snapshot | `55541f2412dae92232d1c3b56cad016766704637985151b31be1f738ac981dcf` |
| 構文事実 | 1,883件、C#31ファイル解析済み・47ファイルは構文解析未対応。未対応資料も許可内なら原文取得可能 |
| source-facts SHA | `09e5160f9c4d2f1b9847ed14faaa963c2bfd668990aa054e5246a675e43e3b4d` |
| 未採用の凍結候補 | `0e3ec3755be086e0cada0126aa00e144dbc6bd3f4a87ddf35f7ba21681372ee6` |
| 今回の独立検証 | `48b27f0de2f0cbade6d226b333f95eec3a1b8bed5dc4a312dd0d1c8c8ed3db9f` |
| 現行engine | `5b4157a97836890407be9214ba6eb5a069b48fe030fa5493649bd0d3c4026931` |
| 検証版移行audit | `8005d8666ab334e382ba13c13d23af7fbe3425b03514b761698160f9a9b6416d` |
| 保持する前回正式成果 | `9c1f24b11ba15a7adc80a2497b19d2f989212eab1a613eafb7dbcb53ae0e627d` |

今回の候補123件は原7草稿の記録と完全一致する。原作者9呼出し・52roundのcontext、prompt、wire schemaは一致再生し、原回答・候補を変更していない。最終確認で入力sourceの全manifestとsnapshotも一致した。作者履歴・候補・snapshot・索引の1,084ファイルが不変である。

`contextbase.json`、`result/validation.json`、`facts/*`、`target.json`は前回正式成果のままである。それらの旧合格を今回の合格として扱わない。今回の未採用候補・検証・原応答・試験ログはprojectの`.tmp`に保存し、正式rootへ追加しない。

## 修復と実測

収束には原義務、単位と原回答、階層目録、根拠、全unknown／followup、factUsage宣言数と取得境界を束縛した包を渡す。作者の逐項再審査を独立reviewへ分け、原草稿を再抽出しなかった。検証では材料全体のhashと記録版を明示的に分け、返答schemaのIDと期待版を成対constで束縛した。hostによる判定・Hashの補正は行っていない。

限定移行は隔離コピーで先に確認し、前auditと凍結候補を明示して原workへ適用した。旧9作者呼出し全体をモデルなしで再生し、1,204の歴史ファイルを保持した。実行中のtaskや成功review断片を移行対象にせず、通常のengine不一致拒否も維持する。移行auditから一時プロセスロックを除外し、プロセスが変わっても同じ証明になることを確認した。

| 今回のlauncher試行 | 壁時計 | 結果 |
| --- | ---: | --- |
| 修正前の収束続行 | 21分54.5秒 | 36 round後、既取得本文の再要求が続き無進展保護で停止 |
| 収束包修正後 | 9分8.7秒 | 原草稿を再利用して収束完了。最初の独立reviewが材料Hashと記録版を混同し拒否 |
| 検証の再試行 | 5分2.6秒 | 凍結候補を保持。版束縛修正のためhostが取消し |
| 版束縛修正後の検証続行 | 65分21.0秒 | reviewのみ23組・102 provider応答。全体阻害により未採用・未公開 |

launcher合計は101分26.7秒。修正・回帰・隔離検査・互換移行は別である。最後のverify操作は55分11.9秒で、モデル対話とhost処理を含み、純粋な推論時間ではない。最後のlauncherとの差10分9.1秒には起動・索引確認・保存作者の再生・採用前回放等を含む。失敗判定でも採用前に履歴を回放するための追加時間があり、処理速度が十分になったとは判定しない。

最後の続行で新しいplan／draft／closure呼出しは0、reviewは23。新provider応答102件に故障返答はなく、報告用量はinput 8,211,942、output 113,325。以前の失敗・取消し応答をこの用量へ混ぜていない。関連102件の合成回帰が成功したが、実モデルの全体合格や人手受入れとは区別する。

## 許可範囲の候補内訳

| 区分 | 件数 | 扱い |
| --- | ---: | --- |
| system | 3 | 概要・profile・分類集計 |
| function | 6 | 主機能候補 |
| operation | 7 | 主機能内の子操作候補 |
| common | 20 | 共通責務。主機能数へ加算しない |
| data | 41 | 物理定義14、契約／DTO等26、SQL参照分析1 |
| entry | 20 | 技術入口 |
| support | 17 | 支援資源 |
| material | 5 | 取得資料 |
| dependency | 4 | 宣言・参照依存 |

物理14はNative 7定義とSharedAccess 7定義であり、同名の別profile定義を同じ実配備表とみなさない。123は機能数ではない。以下は逐項検証された凍結候補の記述であり、全体完全性や正式採用を表さない。元statementを人手編集して判定に合わせてはいない。

## 主機能の候補（6件）

### ログイン

ID：`function:login`。領域：system.authentication。

LocalLoginが有効な構成で、利用者名とパスワードを送信し、成功時は認証Cookieを発行して学生検索へ遷移し、失敗時はログイン画面にエラーを表示する。

- 目的：設定された利用者が資格情報を提示して認証セッションを開始する。
- 完了結果：認証成功によるセッション開始、または失敗理由を示す画面への復帰。
- 分割理由：専用の入力画面、送信操作、認証処理、成功と失敗の結果が揃った独立したシステム利用目的である。
- 代替案：認証開始と終了をセッション管理機能に統合する分割も可能だが、開始には独自の資格情報入力と失敗結果があるため本目録では分ける。
- 入口：entry:login-get, entry:login-post
- 原文：[Web/Controllers/AccountController.cs:10-34](../../srcs/CSharp_ASPNET/Web/Controllers/AccountController.cs#L10)、[Views/Account/Login.cshtml:1-13](../../srcs/CSharp_ASPNET/Views/Account/Login.cshtml#L1)

### ログアウト

ID：`function:logout`。領域：system.authentication。

認証済み利用者が共通ヘッダーからログアウトを送信すると、Cookie認証をサインアウトしてログインURLへ遷移する。共有DB確認モードではヘッダーの操作を表示しない。

- 目的：利用者自身の操作で現在の認証セッションを終了する。
- 完了結果：Cookie認証のサインアウトとログインURLへの遷移。
- 分割理由：ログイン画面内の補助操作ではなく、認証済みの各画面から起動され、セッション終了という独立した結果を持つ。
- 代替案：セッション管理という主機能の終了操作にまとめる構成も可能。本ソースでは開始画面とは別の利用文脈と完了結果があるため独立機能とする。
- 入口：entry:logout-post
- 原文：[Web/Controllers/AccountController.cs:36-41](../../srcs/CSharp_ASPNET/Web/Controllers/AccountController.cs#L36)、[Views/Shared/_Layout.cshtml:2-4](../../srcs/CSharp_ASPNET/Views/Shared/_Layout.cshtml#L2)

### 学生情報照会

ID：`function:student-inquiry`。領域：業務・学生情報管理。

認証済み利用者が条件を指定して学生を検索し、件数・一覧・詳細を確認する。条件変更、ページ操作、編集画面からの検索再開を含む。

- 目的：条件に該当する学生とその情報を確認する。
- 完了結果：検索結果、該当なし、件数超過等の結果と学生一覧を確認できる。
- 分割理由：条件入力と独立した照会結果があり、編集権限を持たないViewerにも参照目的が成立する。
- 代替案：学生保守の対象選択へ統合する分割も考えられるが、Viewerの照会と検索結果自体の完了価値を隠すため、独立した主機能とする。
- 入口：entry:students-index, entry:students-search, entry:students-page, entry:students-clear
- 原文：[Views/Students/Search.cshtml:14-77](../../srcs/CSharp_ASPNET/Views/Students/Search.cshtml#L14)、[Web/Controllers/StudentsController.cs:5-26](../../srcs/CSharp_ASPNET/Web/Controllers/StudentsController.cs#L5)、[Infrastructure/WebStudentCoordinator.cs:7-20](../../srcs/CSharp_ASPNET/Infrastructure/WebStudentCoordinator.cs#L7)

### 学生情報登録・保守

ID：`function:student-maintenance`。領域：業務・学生情報管理。

StaffまたはAdministratorが学生情報を登録・変更し、Administratorが既存学生を論理削除する。共通の編集画面から結果通知または修正・確認へ進む。

- 目的：学生情報を登録し、登録後の内容と有効な管理対象を保守する。
- 完了結果：保存・論理削除の成功通知、変更なし、入力エラー、競合、確認要求等を得る。
- 分割理由：新規と既存更新は同じ入力画面・保存契約を使い、削除もその画面の対象確認から実行する学生保守の文脈にある。
- 代替案：登録・変更・削除を別主機能に分けることも可能だが、取得ソースには独立した申請・承認・法的廃棄等の別工程がなく、ここでは一つの保守目的と各操作に分ける。
- 入口：entry:students-new, entry:students-detail, entry:students-create, entry:students-update, entry:students-delete
- 原文：[Views/Students/Edit.cshtml:35-59](../../srcs/CSharp_ASPNET/Views/Students/Edit.cshtml#L35)、[Views/Students/Edit.cshtml:141-175](../../srcs/CSharp_ASPNET/Views/Students/Edit.cshtml#L141)、[Web/Controllers/StudentsController.cs:29-44](../../srcs/CSharp_ASPNET/Web/Controllers/StudentsController.cs#L29)、[Infrastructure/WebStudentCoordinator.cs:22-24](../../srcs/CSharp_ASPNET/Infrastructure/WebStudentCoordinator.cs#L22)

### クラスマスタ保守

ID：`function:class-maintenance`。領域：業務・マスタ管理。

DB管理権限を持つ利用者がCLIのclassコマンドへJSONを渡し、クラスを追加・変更して保存結果を取得する。サービスは接続主体の管理権限を検査し、年度・期間・定員・参照状況・期待版などを確認して保存する。

- 目的：クラスの年度別属性と利用条件を登録・保守する。
- 完了結果：保存または変更なしの結果、あるいは競合・入力不正・権限不足等の結果を取得する。
- 分割理由：入力、管理権限検査、クラス固有の整合性確認、保存結果までが実装された独立タスク。追加と変更は同じクラス保守目的のモードとしてまとめる。
- 代替案：管理者マスタ保守を一つの主機能とし、class/codeを操作にまとめる分割も可能。ただし対象と入力契約、整合性条件、保存完了結果がそれぞれ独立しているため、本目録では分ける。
- 入口：entry:maintenance-cli
- 原文：[maintenance/Program.cs:4-19](../../srcs/CSharp_ASPNET/maintenance/Program.cs#L4)、[Core/MasterMaintenanceService.cs:19-84](../../srcs/CSharp_ASPNET/Core/MasterMaintenanceService.cs#L19)

### コードマスタ保守

ID：`function:code-maintenance`。領域：業務・マスタ管理。

DB管理権限を持つ利用者がCLIのcodeコマンドへJSONを渡し、対応する分類のコードを追加・変更して保存結果を取得する。サービスは分類の追加可否、保護値、期間、期待版などを確認して保存する。

- 目的：対応するコード分類の名称・表示順・有効状態・期間等を登録・保守する。
- 完了結果：保存または変更なしの結果、あるいは競合・入力不正・権限不足等の結果を取得する。
- 分割理由：コード固有の入力契約と保護規則を持ち、単独のCLI実行で保存結果まで到達する。分類ごとのメソッドや機能には分割しない。
- 代替案：クラス保守と統合して管理者マスタ保守の操作とする構成も可能。共通CLIの使用だけでは同一タスクとはせず、独立した対象と完了結果を根拠に分ける。
- 入口：entry:maintenance-cli
- 原文：[maintenance/Program.cs:4-19](../../srcs/CSharp_ASPNET/maintenance/Program.cs#L4)、[Core/MasterMaintenanceService.cs:19-35](../../srcs/CSharp_ASPNET/Core/MasterMaintenanceService.cs#L19)、[Core/MasterMaintenanceService.cs:85-128](../../srcs/CSharp_ASPNET/Core/MasterMaintenanceService.cs#L85)

## 概要の候補

以下は保存済み提出内容。独立検証・採用は未実施。

### 学生管理システムの構成と対象範囲

ID：`system:selected-system`。

対象は.NET 10のASP.NET Core MVC Web、共通Core、クラス／コード保守CLIを含む。WebはControllerを登録し、IStudentServiceにSqlServerStudentServiceを登録する。保守CLIはclass/code指定からMasterMaintenanceServiceを呼び、結果をJSON出力する。機能の意味分類は各担当単位で行い、Webだけへ対象を限定しない。

原文：[StudentManagement.slnx:1-9](../../srcs/CSharp_ASPNET/StudentManagement.slnx#L1)、[Core/StudentManagement.Core.csproj:1-12](../../srcs/CSharp_ASPNET/Core/StudentManagement.Core.csproj#L1)、[Program.cs:2-8](../../srcs/CSharp_ASPNET/Program.cs#L2)、[Infrastructure/WebHostSetup.cs:25-25](../../srcs/CSharp_ASPNET/Infrastructure/WebHostSetup.cs#L25)、[maintenance/Program.cs:4-19](../../srcs/CSharp_ASPNET/maintenance/Program.cs#L4)

### 条件付き認証とデータベースプロファイル

ID：`system:configuration-profiles`。

基本設定はNativeで、LocalLoginとSharedDatabaseTrainingは無効。SharedTrainingSql／https起動設定はSharedAccessとSharedDatabaseTrainingを選ぶ。登録処理は両認証設定を検証し、Cookie認証・認可・CSRFを構成する。共有DB確認モードは明示環境、ローカルHTTPS、DB上の役割取得を条件とする。設定宣言は実際の配備設定や実行成功の証拠ではない。

原文：[appsettings.json:1-27](../../srcs/CSharp_ASPNET/appsettings.json#L1)、[Properties/launchSettings.json:1-41](../../srcs/CSharp_ASPNET/Properties/launchSettings.json#L1)、[Infrastructure/WebHostSetup.cs:14-25](../../srcs/CSharp_ASPNET/Infrastructure/WebHostSetup.cs#L14)、[Infrastructure/SharedDatabaseTraining.cs:22-92](../../srcs/CSharp_ASPNET/Infrastructure/SharedDatabaseTraining.cs#L22)

## 子操作の候補

以下は保存済み提出内容。独立検証・採用は未実施。

### 保守対象学生の検索・選択

ID：`operation:student-select-for-maintenance`。

照会と同じ検索入口を用い、既存学生を選んで編集へ進む。

親機能：`function:student-maintenance`。

原文：[Views/Students/Search.cshtml:20-70](../../srcs/CSharp_ASPNET/Views/Students/Search.cshtml#L20)、[Web/Controllers/StudentsController.cs:5-25](../../srcs/CSharp_ASPNET/Web/Controllers/StudentsController.cs#L5)

### 学生詳細参照

ID：`operation:student-detail-view`。

検索結果から既存学生を開き、登録済みの詳細情報を確認する。Viewerでは編集不可の参照モードとなる。

親機能：`function:student-inquiry`。

原文：[Views/Students/Search.cshtml:64-67](../../srcs/CSharp_ASPNET/Views/Students/Search.cshtml#L64)、[Views/Students/Edit.cshtml:35-43](../../srcs/CSharp_ASPNET/Views/Students/Edit.cshtml#L35)、[Web/Models/StudentEditPageModel.cs:3-15](../../srcs/CSharp_ASPNET/Web/Models/StudentEditPageModel.cs#L3)、[Web/Controllers/StudentsController.cs:30-31](../../srcs/CSharp_ASPNET/Web/Controllers/StudentsController.cs#L30)、[Infrastructure/WebStudentCoordinator.cs:22-22](../../srcs/CSharp_ASPNET/Infrastructure/WebStudentCoordinator.cs#L22)

### 学生新規登録

ID：`operation:student-create`。

新規モードで学生情報を入力し、登録要求を送信する。

親機能：`function:student-maintenance`。

原文：[Views/Students/Edit.cshtml:35-59](../../srcs/CSharp_ASPNET/Views/Students/Edit.cshtml#L35)、[Views/Students/Edit.cshtml:143-149](../../srcs/CSharp_ASPNET/Views/Students/Edit.cshtml#L143)、[Web/Controllers/StudentsController.cs:29-40](../../srcs/CSharp_ASPNET/Web/Controllers/StudentsController.cs#L29)、[Infrastructure/WebStudentCoordinator.cs:22-23](../../srcs/CSharp_ASPNET/Infrastructure/WebStudentCoordinator.cs#L22)

### 学生情報変更

ID：`operation:student-update`。

既存学生の詳細を読み込み、変更内容と期待版等を送信する。画面上で既存の学籍番号は変更不可となる。

親機能：`function:student-maintenance`。

原文：[Views/Students/Edit.cshtml:35-66](../../srcs/CSharp_ASPNET/Views/Students/Edit.cshtml#L35)、[Web/Controllers/StudentsController.cs:30-40](../../srcs/CSharp_ASPNET/Web/Controllers/StudentsController.cs#L30)、[Infrastructure/WebStudentCoordinator.cs:22-23](../../srcs/CSharp_ASPNET/Infrastructure/WebStudentCoordinator.cs#L22)

### 学生情報の論理削除

ID：`operation:student-logical-delete`。

Administratorが編集画面の対象を確認し、削除理由を入力して論理削除要求を送る。

親機能：`function:student-maintenance`。

原文：[Views/Students/Edit.cshtml:149-172](../../srcs/CSharp_ASPNET/Views/Students/Edit.cshtml#L149)、[Web/Controllers/StudentsController.cs:43-44](../../srcs/CSharp_ASPNET/Web/Controllers/StudentsController.cs#L43)、[Infrastructure/WebStudentCoordinator.cs:24-24](../../srcs/CSharp_ASPNET/Infrastructure/WebStudentCoordinator.cs#L24)

### 重複候補確認・保存続行

ID：`operation:student-duplicate-confirmation`。

保存結果が確認要求の場合、候補を表示し、別人である確認理由を入力して同じ保存入口へ再送する。

親機能：`function:student-maintenance`。

原文：[Views/Students/Edit.cshtml:152-161](../../srcs/CSharp_ASPNET/Views/Students/Edit.cshtml#L152)、[Web/Controllers/StudentsController.cs:32-40](../../srcs/CSharp_ASPNET/Web/Controllers/StudentsController.cs#L32)、[wwwroot/js/site.js:106-116](../../srcs/CSharp_ASPNET/wwwroot/js/site.js#L106)

### 学生編集の取消・再読込

ID：`operation:student-editor-reset-reload`。

入力クリアまたは編集取消で読込時の値へ戻し、再読込では未保存変更の破棄確認を経て画面を取得し直す。

親機能：`function:student-maintenance`。

原文：[Views/Students/Edit.cshtml:143-151](../../srcs/CSharp_ASPNET/Views/Students/Edit.cshtml#L143)、[Views/Students/Edit.cshtml:174-175](../../srcs/CSharp_ASPNET/Views/Students/Edit.cshtml#L174)、[Web/Controllers/StudentsController.cs:29-31](../../srcs/CSharp_ASPNET/Web/Controllers/StudentsController.cs#L29)、[Web/Controllers/StudentsController.cs:41-41](../../srcs/CSharp_ASPNET/Web/Controllers/StudentsController.cs#L41)

## 共通責務の候補

以下は保存済み提出内容。独立検証・採用は未実施。

### 学生管理メニュー

ID：`common:menu-navigation`。

学生検索・新規登録への遷移先を提示するナビゲーション画面。役割によるリンク表示の違いはあるが、集約照会や独立した業務結果は観測されない。

記載された利用先：entry:menu-get。

原文：[Web/Controllers/MenuController.cs:6-10](../../srcs/CSharp_ASPNET/Web/Controllers/MenuController.cs#L6)、[Views/Menu/Index.cshtml:1-7](../../srcs/CSharp_ASPNET/Views/Menu/Index.cshtml#L1)

### 共通画面レイアウト

ID：`common:web-layout`。

ViewStartで共通適用され、ヘッダー、利用者・業務日、ログアウト操作、共有DB確認通知、共通CSS・JavaScript参照と画面本文の挿入を担う。

記載された利用先：function:login、common:menu-navigation、function:logout。

原文：[Views/_ViewStart.cshtml:1-1](../../srcs/CSharp_ASPNET/Views/_ViewStart.cshtml#L1)、[Views/Shared/_Layout.cshtml:1-5](../../srcs/CSharp_ASPNET/Views/Shared/_Layout.cshtml#L1)、[Views/Account/Login.cshtml:1-13](../../srcs/CSharp_ASPNET/Views/Account/Login.cshtml#L1)、[Views/Menu/Index.cshtml:1-7](../../srcs/CSharp_ASPNET/Views/Menu/Index.cshtml#L1)

### ローカル資格情報認証

ID：`common:local-authentication`。

明示設定された単一利用者の資格情報検証、共通の失敗回数制限、認証Claims生成と設定変更に伴うCookie受入判定を集中管理する。ログイン操作自体とは分離する。

記載された利用先：function:login、common:cookie-session、entry:web-program。

原文：[Infrastructure/LocalLogin.cs:13-90](../../srcs/CSharp_ASPNET/Infrastructure/LocalLogin.cs#L13)、[Web/Controllers/AccountController.cs:21-29](../../srcs/CSharp_ASPNET/Web/Controllers/AccountController.cs#L21)、[Infrastructure/WebHostSetup.cs:15-20](../../srcs/CSharp_ASPNET/Infrastructure/WebHostSetup.cs#L15)

### Cookie認証セッション基盤

ID：`common:cookie-session`。

Cookie認証の有効期間・更新、Cookie属性、認証主体の受入検証、未認証・権限不足応答を共通設定し、ログイン・ログアウトおよび条件付き主体発行で利用される。

記載された利用先：function:login、function:logout、common:shared-database-training-identity、entry:evaluation-session。

原文：[Infrastructure/WebHostSetup.cs:20-21](../../srcs/CSharp_ASPNET/Infrastructure/WebHostSetup.cs#L20)、[Infrastructure/WebHostSetup.cs:31-35](../../srcs/CSharp_ASPNET/Infrastructure/WebHostSetup.cs#L31)、[Web/Controllers/AccountController.cs:27-40](../../srcs/CSharp_ASPNET/Web/Controllers/AccountController.cs#L27)、[Infrastructure/SharedDatabaseTraining.cs:79-91](../../srcs/CSharp_ASPNET/Infrastructure/SharedDatabaseTraining.cs#L79)

### 共有DB確認用の主体適用

ID：`common:shared-database-training-identity`。

明示した共有DB確認環境で、ローカルHTTPS要求に対して設定利用者のDB役割を取得・対応付けし、確認用ClaimsとCookieを適用する。資格情報入力を持つ独立ログイン画面ではない。

記載された利用先：entry:web-program、common:cookie-session。

原文：[Infrastructure/SharedDatabaseTraining.cs:22-93](../../srcs/CSharp_ASPNET/Infrastructure/SharedDatabaseTraining.cs#L22)、[Infrastructure/WebHostSetup.cs:16-20](../../srcs/CSharp_ASPNET/Infrastructure/WebHostSetup.cs#L16)、[Infrastructure/WebHostSetup.cs:31-33](../../srcs/CSharp_ASPNET/Infrastructure/WebHostSetup.cs#L31)、[Program.cs:3-5](../../srcs/CSharp_ASPNET/Program.cs#L3)

### 要求利用者・セッション・権限の取得

ID：`common:request-identity`。

HTTP Claimsから利用者・セッション・役割を取得して検査し、タブ識別と権限判定を提供する。ホストの学生サービス生成ではCurrentUserを取得するラムダが渡される。

記載された利用先：entry:web-program。

原文：[Infrastructure/RequestIdentity.cs:4-17](../../srcs/CSharp_ASPNET/Infrastructure/RequestIdentity.cs#L4)、[Infrastructure/WebHostSetup.cs:19-25](../../srcs/CSharp_ASPNET/Infrastructure/WebHostSetup.cs#L19)、[Program.cs:3-5](../../srcs/CSharp_ASPNET/Program.cs#L3)

### Web学生処理の調整

ID：`common:web-student-coordinator`。

MVC入口から利用者権限、検索文脈、Coreサービス呼出、入力変換、検索結果整形を調整する。独立したユーザー機能とは分ける。

記載された利用先：entry:students-index、entry:students-search、entry:students-page、entry:students-clear、entry:students-new、entry:students-detail、entry:students-create、entry:students-update、entry:students-delete。

原文：[Infrastructure/WebStudentCoordinator.cs:3-28](../../srcs/CSharp_ASPNET/Infrastructure/WebStudentCoordinator.cs#L3)、[Web/Controllers/StudentsController.cs:6-26](../../srcs/CSharp_ASPNET/Web/Controllers/StudentsController.cs#L6)、[Web/Controllers/StudentsController.cs:31-44](../../srcs/CSharp_ASPNET/Web/Controllers/StudentsController.cs#L31)、[Infrastructure/WebHostSetup.cs:19-25](../../srcs/CSharp_ASPNET/Infrastructure/WebHostSetup.cs#L19)

### 管理者マスタ保守サービス

ID：`common:master-maintenance`。

MasterMaintenanceServiceがクラス・コード保守の権限検査、入力整合性、期待版確認、保存と監査記録を担当する。両CLI分岐が同じサービスを生成・使用する。主機能とは別の実装責任として保持し、SQL参照を物理DDL定義と同一視しない。

記載された利用先：function:class-maintenance、function:code-maintenance。

原文：[Core/MasterMaintenanceService.cs:15-143](../../srcs/CSharp_ASPNET/Core/MasterMaintenanceService.cs#L15)、[maintenance/Program.cs:13-14](../../srcs/CSharp_ASPNET/maintenance/Program.cs#L13)

### 学生・マスタ入力の正規化と検証

ID：`common:student-normalization`。

文字数、識別子、照合キー、カナ、連絡先、コード、学生項目間整合性と項目別エラーを中央で処理する。

記載された利用先：common:sql-student-service、common:master-maintenance。

原文：[Core/StudentNormalizer.cs:18-169](../../srcs/CSharp_ASPNET/Core/StudentNormalizer.cs#L18)、[Core/SqlServerStudentService.cs:138-154](../../srcs/CSharp_ASPNET/Core/SqlServerStudentService.cs#L138)、[Core/SqlServerStudentService.cs:232-245](../../srcs/CSharp_ASPNET/Core/SqlServerStudentService.cs#L232)、[Core/MasterMaintenanceService.cs:39-42](../../srcs/CSharp_ASPNET/Core/MasterMaintenanceService.cs#L39)、[Core/MasterMaintenanceService.cs:88-102](../../srcs/CSharp_ASPNET/Core/MasterMaintenanceService.cs#L88)

### 和暦・西暦日付の変換と検証

ID：`common:japanese-date`。

明示的な元号境界による生年月日検証、和暦入力・表示変換、西暦日付検証と年度算出を提供する。

記載された利用先：common:student-normalization、common:sql-student-service、common:master-maintenance。

原文：[Core/JapaneseDateService.cs:7-62](../../srcs/CSharp_ASPNET/Core/JapaneseDateService.cs#L7)、[Core/StudentNormalizer.cs:127-137](../../srcs/CSharp_ASPNET/Core/StudentNormalizer.cs#L127)、[Core/SqlServerStudentService.cs:189-200](../../srcs/CSharp_ASPNET/Core/SqlServerStudentService.cs#L189)、[Core/MasterMaintenanceService.cs:42-43](../../srcs/CSharp_ASPNET/Core/MasterMaintenanceService.cs#L42)、[Core/MasterMaintenanceService.cs:90-92](../../srcs/CSharp_ASPNET/Core/MasterMaintenanceService.cs#L90)

### マスタ監査操作区分の判定

ID：`common:master-audit-operation`。

マスタの作成と有効状態の変化からCREATE、UPDATE、ENABLE、DISABLEを判定する。

記載された利用先：common:master-maintenance。

原文：[Core/AuditOperation.cs:4-8](../../srcs/CSharp_ASPNET/Core/AuditOperation.cs#L4)、[Core/MasterMaintenanceService.cs:80-82](../../srcs/CSharp_ASPNET/Core/MasterMaintenanceService.cs#L80)、[Core/MasterMaintenanceService.cs:125-126](../../srcs/CSharp_ASPNET/Core/MasterMaintenanceService.cs#L125)

### 学生データ処理サービス

ID：`common:sql-student-service`。

学生検索・詳細・候補取得・保存・論理削除と、保存時の整合性、重複確認、版管理、監査を中央で実装する。

記載された利用先：common:web-student-coordinator、entry:students-index、entry:students-search、entry:students-page、entry:students-new、entry:students-detail、entry:students-create、entry:students-update、entry:students-reset。

原文：[Core/SqlServerStudentService.cs:128-221](../../srcs/CSharp_ASPNET/Core/SqlServerStudentService.cs#L128)、[Core/SqlServerStudentService.cs:232-425](../../srcs/CSharp_ASPNET/Core/SqlServerStudentService.cs#L232)、[Infrastructure/WebStudentCoordinator.cs:3-24](../../srcs/CSharp_ASPNET/Infrastructure/WebStudentCoordinator.cs#L3)、[Infrastructure/WebHostSetup.cs:25-25](../../srcs/CSharp_ASPNET/Infrastructure/WebHostSetup.cs#L25)、[Web/Controllers/StudentsController.cs:45-45](../../srcs/CSharp_ASPNET/Web/Controllers/StudentsController.cs#L45)

### SQL接続・型変換・書込制御

ID：`common:sql-persistence-boundary`。

SQLコマンドとパラメータ、プロファイル別型変換、暗号化接続設定、書込直列化とロールバック補助を共有する。

記載された利用先：common:sql-student-service、common:master-maintenance。

原文：[Core/SqlServerStudentService.cs:42-115](../../srcs/CSharp_ASPNET/Core/SqlServerStudentService.cs#L42)、[Core/SqlServerStudentService.cs:329-333](../../srcs/CSharp_ASPNET/Core/SqlServerStudentService.cs#L329)、[Core/SqlServerStudentService.cs:429-489](../../srcs/CSharp_ASPNET/Core/SqlServerStudentService.cs#L429)、[Core/MasterMaintenanceService.cs:5-5](../../srcs/CSharp_ASPNET/Core/MasterMaintenanceService.cs#L5)、[Core/MasterMaintenanceService.cs:19-29](../../srcs/CSharp_ASPNET/Core/MasterMaintenanceService.cs#L19)、[Core/MasterMaintenanceService.cs:48-48](../../srcs/CSharp_ASPNET/Core/MasterMaintenanceService.cs#L48)、[Core/MasterMaintenanceService.cs:96-96](../../srcs/CSharp_ASPNET/Core/MasterMaintenanceService.cs#L96)、[Core/MasterMaintenanceService.cs:127-143](../../srcs/CSharp_ASPNET/Core/MasterMaintenanceService.cs#L127)

### サーバー保持の検索文脈管理

ID：`common:search-context`。

利用者・セッション・画面に結び付く検索条件と結果を保持し、期限、スキーマ版、更新版、排他を管理する。

記載された利用先：common:web-student-coordinator、entry:students-index、entry:students-search、entry:students-page、entry:students-clear、entry:students-new、entry:students-detail。

原文：[Infrastructure/SearchContextStore.cs:7-18](../../srcs/CSharp_ASPNET/Infrastructure/SearchContextStore.cs#L7)、[Infrastructure/WebStudentCoordinator.cs:5-20](../../srcs/CSharp_ASPNET/Infrastructure/WebStudentCoordinator.cs#L5)、[Web/Controllers/StudentsController.cs:8-25](../../srcs/CSharp_ASPNET/Web/Controllers/StudentsController.cs#L8)、[Infrastructure/WebHostSetup.cs:19-19](../../srcs/CSharp_ASPNET/Infrastructure/WebHostSetup.cs#L19)

### 編集読込時スナップショット管理

ID：`common:editor-snapshot`。

編集開始時の入力と詳細、復帰版を期限付きで保持し、利用者・セッション・対象学生を照合する。

記載された利用先：entry:students-new、entry:students-detail、entry:students-create、entry:students-update、entry:students-reset、entry:students-delete。

原文：[Infrastructure/EditorSnapshotStore.cs:5-12](../../srcs/CSharp_ASPNET/Infrastructure/EditorSnapshotStore.cs#L5)、[Web/Controllers/StudentsController.cs:31-43](../../srcs/CSharp_ASPNET/Web/Controllers/StudentsController.cs#L31)、[Infrastructure/WebHostSetup.cs:19-19](../../srcs/CSharp_ASPNET/Infrastructure/WebHostSetup.cs#L19)

### 画面遷移後の一回通知

ID：`common:flash-message`。

利用者・セッション・検索文脈に対応する短期メッセージを保存し、検索画面で一度だけ取り出す。

記載された利用先：entry:students-index、entry:students-create、entry:students-update、entry:students-delete。

原文：[Infrastructure/FlashMessageStore.cs:4-10](../../srcs/CSharp_ASPNET/Infrastructure/FlashMessageStore.cs#L4)、[Web/Controllers/StudentsController.cs:8-11](../../srcs/CSharp_ASPNET/Web/Controllers/StudentsController.cs#L8)、[Web/Controllers/StudentsController.cs:37-44](../../srcs/CSharp_ASPNET/Web/Controllers/StudentsController.cs#L37)、[Infrastructure/WebHostSetup.cs:19-19](../../srcs/CSharp_ASPNET/Infrastructure/WebHostSetup.cs#L19)

### Web結果・日時・エラーの表示整形

ID：`common:web-presentation`。

業務日と日時表示、検索行、結果区分のHTTP状態、項目エラーとJSON応答の整形を提供する。個別整形メソッドの全てが現行入口から使われるとは断定しない。

記載された利用先：common:web-student-coordinator、common:cookie-session、common:antiforgery-processing、common:web-layout、entry:students-create、entry:students-update、entry:students-delete。

原文：[Infrastructure/WebPresentation.cs:3-31](../../srcs/CSharp_ASPNET/Infrastructure/WebPresentation.cs#L3)、[Infrastructure/WebStudentCoordinator.cs:26-27](../../srcs/CSharp_ASPNET/Infrastructure/WebStudentCoordinator.cs#L26)、[Web/Controllers/StudentsController.cs:38-43](../../srcs/CSharp_ASPNET/Web/Controllers/StudentsController.cs#L38)、[Infrastructure/WebHostSetup.cs:20-20](../../srcs/CSharp_ASPNET/Infrastructure/WebHostSetup.cs#L20)、[Infrastructure/WebHostSetup.cs:28-30](../../srcs/CSharp_ASPNET/Infrastructure/WebHostSetup.cs#L28)、[Infrastructure/AntiforgeryResultFilter.cs:7-9](../../srcs/CSharp_ASPNET/Infrastructure/AntiforgeryResultFilter.cs#L7)、[Views/Shared/_Layout.cshtml:3-3](../../srcs/CSharp_ASPNET/Views/Shared/_Layout.cshtml#L3)

### MVC要求のCSRF検証と失敗応答

ID：`common:antiforgery-processing`。

MVC全体に自動CSRF検証を登録し、/apiでCSRF検証が失敗した場合のJSON応答を整形する。現行API入口の存在をこの条件分岐だけから推定しない。

記載された利用先：entry:students-search、entry:students-create、entry:students-update、entry:students-reset、entry:students-delete。

原文：[Infrastructure/AntiforgeryResultFilter.cs:5-10](../../srcs/CSharp_ASPNET/Infrastructure/AntiforgeryResultFilter.cs#L5)、[Infrastructure/WebHostSetup.cs:21-24](../../srcs/CSharp_ASPNET/Infrastructure/WebHostSetup.cs#L21)、[Web/Controllers/StudentsController.cs:5-6](../../srcs/CSharp_ASPNET/Web/Controllers/StudentsController.cs#L5)、[Web/Controllers/StudentsController.cs:13-13](../../srcs/CSharp_ASPNET/Web/Controllers/StudentsController.cs#L13)、[Web/Controllers/StudentsController.cs:32-43](../../srcs/CSharp_ASPNET/Web/Controllers/StudentsController.cs#L32)

### 検証・通知メッセージ表示断片

ID：`common:message-panel`。

ModelStateの検証エラーと文字列通知をaria-live付き共通断片として表示し、学生検索ビューから利用される。

記載された利用先：entry:students-index。

原文：[Views/Shared/_MessagePanel.cshtml:1-3](../../srcs/CSharp_ASPNET/Views/Shared/_MessagePanel.cshtml#L1)、[Views/Students/Search.cshtml:19-19](../../srcs/CSharp_ASPNET/Views/Students/Search.cshtml#L19)、[Web/Controllers/StudentsController.cs:8-11](../../srcs/CSharp_ASPNET/Web/Controllers/StudentsController.cs#L8)

### 共通CSSと画面操作JavaScript

ID：`common:web-ui-assets`。

共通レイアウトが読み込むCSSとJavaScript。画面表示、学生画面の再配置、ダイアログ、未保存変更確認、送信中制御とクラス候補の表示制御を担う。

記載された利用先：common:web-layout。

原文：[Views/Shared/_Layout.cshtml:1-5](../../srcs/CSharp_ASPNET/Views/Shared/_Layout.cshtml#L1)、[wwwroot/css/site.css:1-4](../../srcs/CSharp_ASPNET/wwwroot/css/site.css#L1)、[wwwroot/css/students.css:1-117](../../srcs/CSharp_ASPNET/wwwroot/css/students.css#L1)、[wwwroot/js/site.js:1-231](../../srcs/CSharp_ASPNET/wwwroot/js/site.js#L1)

## データの候補

以下は保存済み提出内容。独立検証・採用は未実施。

### LoginPageModel

ID：`data:login-page-model`。

ログイン画面の利用者名とエラー表示を保持する画面モデル。パスワードは別のフォーム引数で受け取り、物理テーブルや永続Entityの定義ではない。

原文：[Web/Models/LoginPageModel.cs:3-7](../../srcs/CSharp_ASPNET/Web/Models/LoginPageModel.cs#L3)、[Web/Controllers/AccountController.cs:15-19](../../srcs/CSharp_ASPNET/Web/Controllers/AccountController.cs#L15)、[Web/Controllers/AccountController.cs:31-33](../../srcs/CSharp_ASPNET/Web/Controllers/AccountController.cs#L31)、[Views/Account/Login.cshtml:1-10](../../srcs/CSharp_ASPNET/Views/Account/Login.cshtml#L1)

### StudentSearchInput

ID：`data:student-search-input`。

学籍番号、氏名、クラスID文字列、在籍区分配列を持つWeb検索入力DTO。ToCriteriaでCoreのSearchCriteriaへ変換する。物理テーブルや永続Entityの定義ではない。

原文：[Web/Inputs/StudentSearchInput.cs:4-13](../../srcs/CSharp_ASPNET/Web/Inputs/StudentSearchInput.cs#L4)、[Web/Controllers/StudentsController.cs:13-18](../../srcs/CSharp_ASPNET/Web/Controllers/StudentsController.cs#L13)

### 検索文脈・検索・ページ要求DTO

ID：`data:student-search-context-requests`。

ContextRequestは文脈IDと版、SearchRequestは条件と表示設定、PageRequestはページと表示設定を持つ転送型。型宣言だけでJSON公開APIの存在を意味しない。

原文：[Web/Inputs/StudentSearchInput.cs:14-19](../../srcs/CSharp_ASPNET/Web/Inputs/StudentSearchInput.cs#L14)、[Web/Controllers/StudentsController.cs:18-26](../../srcs/CSharp_ASPNET/Web/Controllers/StudentsController.cs#L18)

### OptionsRequest

ID：`data:student-options-request`。

候補用途、年度、学年、対象学生、在籍区分、入学日・終了日を持つ要求DTO。WebStudentCoordinator.Optionsの引数として残るが、取得したMVC入口は候補要求を結合せず404を返す。

原文：[Web/Inputs/StudentSearchInput.cs:20-21](../../srcs/CSharp_ASPNET/Web/Inputs/StudentSearchInput.cs#L20)、[Infrastructure/WebStudentCoordinator.cs:21-21](../../srcs/CSharp_ASPNET/Infrastructure/WebStudentCoordinator.cs#L21)、[Web/Controllers/StudentsController.cs:27-28](../../srcs/CSharp_ASPNET/Web/Controllers/StudentsController.cs#L27)

### StudentSaveInput

ID：`data:student-save-input`。

学生入力値、年度・学年、期待版、重複確認トークン、理由、検索復帰先を持つWeb保存DTO。StudentDraftとSaveRequestへの変換、詳細からの入力値作成を含む。物理テーブル定義ではない。

原文：[Web/Inputs/StudentSaveInput.cs:6-56](../../srcs/CSharp_ASPNET/Web/Inputs/StudentSaveInput.cs#L6)、[Infrastructure/WebStudentCoordinator.cs:22-23](../../srcs/CSharp_ASPNET/Infrastructure/WebStudentCoordinator.cs#L22)

### StudentDeleteInput

ID：`data:student-delete-input`。

期待版、削除理由、確認済みフラグ、検索復帰先を持つWeb削除要求DTO。学生の永続Entityではない。

原文：[Web/Inputs/StudentDeleteInput.cs:1-4](../../srcs/CSharp_ASPNET/Web/Inputs/StudentDeleteInput.cs#L1)、[Infrastructure/WebStudentCoordinator.cs:24-24](../../srcs/CSharp_ASPNET/Infrastructure/WebStudentCoordinator.cs#L24)

### StudentSearchPageModel

ID：`data:student-search-page-model`。

検索入力、候補集合、検索文脈、利用者、結果のJsonElement、通知、表示設定を束ねるSearchビュー用モデル。結果をJSON形状に保持することはJSONエンドポイントの証拠ではない。

原文：[Web/Models/StudentSearchPageModel.cs:1-16](../../srcs/CSharp_ASPNET/Web/Models/StudentSearchPageModel.cs#L1)、[Web/Controllers/StudentsController.cs:45-45](../../srcs/CSharp_ASPNET/Web/Controllers/StudentsController.cs#L45)

### StudentEditPageModel

ID：`data:student-edit-page-model`。

学生ID、保存入力、候補集合、利用者、詳細、保存結果、通知、編集スナップショットID、検索復帰版を束ねるEditビュー用モデル。CanEditはViewer以外を許可する表示判定。

原文：[Web/Models/StudentEditPageModel.cs:1-15](../../srcs/CSharp_ASPNET/Web/Models/StudentEditPageModel.cs#L1)、[Web/Controllers/StudentsController.cs:31-40](../../srcs/CSharp_ASPNET/Web/Controllers/StudentsController.cs#L31)

### ClassChange

ID：`data:class-change`。

クラス保守の入力DTO。識別子・期待版、年度、学年・クラスコード、名称、期間、定員、表示順、有効状態、備考を持ち、CLIのclass分岐がJSONから逆シリアライズする。物理テーブルや永続化Entityの定義ではない。

原文：[Core/MasterMaintenanceService.cs:9-9](../../srcs/CSharp_ASPNET/Core/MasterMaintenanceService.cs#L9)、[maintenance/Program.cs:14-14](../../srcs/CSharp_ASPNET/maintenance/Program.cs#L14)

### CodeChange

ID：`data:code-change`。

コード保守の入力DTO。分類・コード値・期待版、名称、表示順、有効状態、期間、備考を持ち、CLIのcode分岐がJSONから逆シリアライズする。物理テーブルや永続化Entityの定義ではない。

原文：[Core/MasterMaintenanceService.cs:10-10](../../srcs/CSharp_ASPNET/Core/MasterMaintenanceService.cs#L10)、[maintenance/Program.cs:14-14](../../srcs/CSharp_ASPNET/maintenance/Program.cs#L14)

### MaintenanceResult

ID：`data:maintenance-result`。

両マスタ保守の結果DTO。Outcome、版、メッセージ、同名警告フラグを持つ。CLIは結果をJSONへシリアライズし、SavedまたはNoChangeを正常終了として扱う。

原文：[Core/MasterMaintenanceService.cs:11-11](../../srcs/CSharp_ASPNET/Core/MasterMaintenanceService.cs#L11)、[maintenance/Program.cs:14-15](../../srcs/CSharp_ASPNET/maintenance/Program.cs#L14)

### Native dbo.m_student

ID：`data:native-m-student`。

Native用物理テーブル定義。学生情報、検索キー、所属、論理削除情報、監査属性と更新版を保持する。student_idはbigint IDENTITY。DDLの存在を示し、実DBへの適用は示さない。

原文：[database/001_schema.sql:7-61](../../srcs/CSharp_ASPNET/database/001_schema.sql#L7)

### Native dbo.m_class

ID：`data:native-m-class`。

Native用クラスマスタの物理定義。年度、学年コード、クラスコード・名称、利用期間、定員、有効状態と更新版を持ち、class_idはbigint IDENTITY。

原文：[database/001_schema.sql:62-89](../../srcs/CSharp_ASPNET/database/001_schema.sql#L62)

### Native dbo.m_code_category

ID：`data:native-m-code-category`。

Native用コード分類マスタの物理定義。category_idを主キーとし、分類名、コード長、追加可否、有効状態、監査属性と更新版を持つ。

原文：[database/001_schema.sql:90-111](../../srcs/CSharp_ASPNET/database/001_schema.sql#L90)

### Native dbo.m_code

ID：`data:native-m-code`。

Native用コードマスタの物理定義。category_id/code_valueの複合主キー、名称、表示順、有効期間、保護区分、監査属性と更新版を持つ。

原文：[database/001_schema.sql:112-136](../../srcs/CSharp_ASPNET/database/001_schema.sql#L112)

### Native dbo.t_operation_log

ID：`data:native-t-operation-log`。

Native用操作監査ログの物理定義。対象表・キー、操作種別、前後版、変更列、実行主体・時刻、相関ID、理由、重複確認区分を持つ。log_idはbigint IDENTITY。

原文：[database/001_schema.sql:137-155](../../srcs/CSharp_ASPNET/database/001_schema.sql#L137)

### Native dbo.t_confirmation

ID：`data:native-t-confirmation`。

Native用確認情報の物理定義。トークン、主体、セッション、対象・期待版、入力と候補のハッシュ、有効期限、消費状態を持つ。定義の存在とWeb経路での利用を同一視しない。

原文：[database/001_schema.sql:156-170](../../srcs/CSharp_ASPNET/database/001_schema.sql#L156)

### Native dbo.t_runtime_state

ID：`data:native-t-runtime-state`。

Native用状態保存表の物理定義。所有主体、ログインセッション、状態種別、暗号化ペイロード、期限、改訂と消費状態を持つ。全取得ソースの同名検索ではDDL・生成・配備確認資料の参照を観測し、アプリケーションDMLの静的参照は観測しなかった。動的利用や実行不能を断定しない。

原文：[database/001_schema.sql:171-185](../../srcs/CSharp_ASPNET/database/001_schema.sql#L171)、[database/003_web_permissions.sql:23-23](../../srcs/CSharp_ASPNET/database/003_web_permissions.sql#L23)

### SharedAccess dbo.m_student

ID：`data:shared-access-m-student`。

SharedAccess用として収録された学生表の物理定義。student_idとrow_versionはint、業務日付はnvarchar(10)、監査時刻はdatetime2(3)。Nativeの同名表とは別のプロファイル定義として保持し、同一実DBオブジェクトとは断定しない。

原文：[database/shared-access/001-schema.sql:127-164](../../srcs/CSharp_ASPNET/database/shared-access/001-schema.sql#L127)

### SharedAccess dbo.m_class

ID：`data:shared-access-m-class`。

SharedAccess用クラス表の物理定義。class_id・年度・更新版はint、利用日はnvarchar(10)、監査時刻はdatetime2(3)。Native定義と型を区別する。

原文：[database/shared-access/001-schema.sql:9-28](../../srcs/CSharp_ASPNET/database/shared-access/001-schema.sql#L9)

### SharedAccess dbo.m_code_category

ID：`data:shared-access-m-code-category`。

SharedAccess用コード分類表の物理定義。category_idを主キーとし、分類名、コード長、追加可否、有効状態と監査属性を持つ。文字列は明示BIN2照合、更新版はint。

原文：[database/shared-access/001-schema.sql:98-111](../../srcs/CSharp_ASPNET/database/shared-access/001-schema.sql#L98)

### SharedAccess dbo.m_code

ID：`data:shared-access-m-code`。

SharedAccess用コード表の物理定義。category_id/code_valueの複合主キーを持ち、有効期間は文字列、監査時刻はdatetime2(3)、更新版はintとして宣言される。

原文：[database/shared-access/001-schema.sql:58-74](../../srcs/CSharp_ASPNET/database/shared-access/001-schema.sql#L58)

### SharedAccess dbo.t_operation_log

ID：`data:shared-access-t-operation-log`。

SharedAccess用操作監査ログの物理定義。対象・操作・変更列・実行主体等を持ち、IDと前後版はint、時刻はdatetime2(3)、相関IDはnvarchar(36)。Native定義との型差を保持する。

原文：[database/shared-access/001-schema.sql:270-284](../../srcs/CSharp_ASPNET/database/shared-access/001-schema.sql#L270)

### SharedAccess dbo.t_app_role

ID：`data:shared-access-t-app-role`。

SharedAccess用利用者ロール表の物理定義。user_idを主キーとし、role_nameをReader/Staff/Adminに制限する。認証資格情報の表とみなす根拠はない。

原文：[database/shared-access/001-schema.sql:258-269](../../srcs/CSharp_ASPNET/database/shared-access/001-schema.sql#L258)

### SharedAccess dbo.t_write_guard

ID：`data:shared-access-t-write-guard`。

SharedAccess用書込ガード表の物理定義。guard_idを主キーとし1に制限し、lock_bitを持つ。Native用DDLにはこの表の定義がなく、プロファイル固有の対象として保持する。

原文：[database/shared-access/001-schema.sql:306-313](../../srcs/CSharp_ASPNET/database/shared-access/001-schema.sql#L306)

### SQL参照先とプロファイル別の適用範囲

ID：`data:sql-target-references`。

学生サービスのSQLはm_student/m_class/m_code/m_code_category/t_operation_logを参照し、SharedAccess書込ガードはt_write_guard、共有DB主体適用はt_app_roleを参照する。t_confirmationのSQLは非Webトークン分岐に残るが、Web登録はwebTokens:trueであり、SharedAccessもWeb所有トークンを要求する。これはソース上の参照候補で、実接続先の配備・スキーマ一致を証明しない。

原文：[Core/SqlServerStudentService.cs:42-47](../../srcs/CSharp_ASPNET/Core/SqlServerStudentService.cs#L42)、[Core/SqlServerStudentService.cs:93-116](../../srcs/CSharp_ASPNET/Core/SqlServerStudentService.cs#L93)、[Core/SqlServerStudentService.cs:201-223](../../srcs/CSharp_ASPNET/Core/SqlServerStudentService.cs#L201)、[Core/SqlServerStudentService.cs:253-315](../../srcs/CSharp_ASPNET/Core/SqlServerStudentService.cs#L253)、[Core/SqlServerStudentService.cs:390-395](../../srcs/CSharp_ASPNET/Core/SqlServerStudentService.cs#L390)、[Infrastructure/SharedDatabaseTraining.cs:71-76](../../srcs/CSharp_ASPNET/Infrastructure/SharedDatabaseTraining.cs#L71)、[Infrastructure/WebHostSetup.cs:25-25](../../srcs/CSharp_ASPNET/Infrastructure/WebHostSetup.cs#L25)

### CurrentUser

ID：`data:current-user`。

主体名、セッションID、Roleを渡すCore契約レコード。物理利用者表やORM Entityの定義ではない。

原文：[Core/Contracts.cs:9-9](../../srcs/CSharp_ASPNET/Core/Contracts.cs#L9)

### FieldError

ID：`data:field-error`。

項目名、コード、メッセージを持つエラー通知契約。物理テーブルではない。

原文：[Core/Contracts.cs:10-10](../../srcs/CSharp_ASPNET/Core/Contracts.cs#L10)

### BirthDateInput

ID：`data:birth-date-input`。

元号・年・月・日の文字列を保持する生年月日入力契約。SQLの日付列定義と分離する。

原文：[Core/Contracts.cs:11-11](../../srcs/CSharp_ASPNET/Core/Contracts.cs#L11)

### StudentDraft

ID：`data:student-draft`。

学生番号、氏名、生年月日入力、連絡先、在籍・所属等を保持する可変入力契約クラス。DB表へのマッピング宣言はなく、学生表そのものや独立機能として数えない。

原文：[Core/Contracts.cs:12-33](../../srcs/CSharp_ASPNET/Core/Contracts.cs#L12)

### SearchCriteria

ID：`data:search-criteria`。

正規化済み学生検索条件とページ・並び順を持つ契約クラス。FromRawによる入力検証・正規化を含むが、検索という利用者タスクとは分離する。

原文：[Core/Contracts.cs:34-62](../../srcs/CSharp_ASPNET/Core/Contracts.cs#L34)

### StudentListItem

ID：`data:student-list-item`。

学生検索一覧の投影契約。学生識別・氏名・生年月日・所属・在籍名称と和暦表示属性を持つ。物理表の全列を表すEntityではない。

原文：[Core/Contracts.cs:63-67](../../srcs/CSharp_ASPNET/Core/Contracts.cs#L63)

### StudentRow

ID：`data:student-row`。

学生候補の投影契約。氏名・所属等に住所、電話、入学日、更新日時と版を含み、SaveResultの重複候補にも用いる型として宣言される。物理テーブルではない。

原文：[Core/Contracts.cs:68-74](../../srcs/CSharp_ASPNET/Core/Contracts.cs#L68)、[Core/Contracts.cs:86-88](../../srcs/CSharp_ASPNET/Core/Contracts.cs#L86)

### SearchResult

ID：`data:search-result`。

結果区分、件数、StudentListItem一覧、検索時刻、上限超過と項目エラーを返す検索結果契約。

原文：[Core/Contracts.cs:75-76](../../srcs/CSharp_ASPNET/Core/Contracts.cs#L75)

### StudentDetail

ID：`data:student-detail`。

学生ID・版、StudentDraft、生年月日、更新日時・主体を持つ詳細取得契約。物理表定義と分離する。

原文：[Core/Contracts.cs:77-78](../../srcs/CSharp_ASPNET/Core/Contracts.cs#L77)

### CodeEntry

ID：`data:code-entry`。

分類・値・名称・表示順・有効期間・保護区分を持つコード取得契約。m_codeの物理定義や更新入力契約とは区別する。

原文：[Core/Contracts.cs:79-80](../../srcs/CSharp_ASPNET/Core/Contracts.cs#L79)

### SchoolClass

ID：`data:school-class`。

クラス識別・年度・学年・名称・期間・定員・在籍人数・有効状態・表示順を持つ取得契約。在籍人数を含む投影であり、物理クラス表そのものではない。

原文：[Core/Contracts.cs:81-82](../../srcs/CSharp_ASPNET/Core/Contracts.cs#L81)

### LookupSet

ID：`data:lookup-set`。

CodeEntryとSchoolClassの一覧をまとめる参照候補取得契約。物理テーブルではない。

原文：[Core/Contracts.cs:83-83](../../srcs/CSharp_ASPNET/Core/Contracts.cs#L83)

### SaveRequest

ID：`data:save-request`。

StudentDraftと任意の学生ID・期待版・年度・学年・確認トークン・理由を渡すCore保存要求契約。Web入力DTOおよび物理表と分離する。

原文：[Core/Contracts.cs:84-85](../../srcs/CSharp_ASPNET/Core/Contracts.cs#L84)

### SaveResult

ID：`data:save-result`。

結果区分、学生ID・版、エラー、確認トークン、重複候補件数・一覧と受付番号を返すCore保存結果契約。

原文：[Core/Contracts.cs:86-88](../../srcs/CSharp_ASPNET/Core/Contracts.cs#L86)

### Core契約の権限・DBプロファイル・結果区分

ID：`data:core-contract-enums`。

Role、StudentDatabaseProfile、Outcomeはアプリケーション内の列挙型。DBのコードマスタや物理利用者ロール表とは別の契約上の値集合である。

原文：[Core/Contracts.cs:4-8](../../srcs/CSharp_ASPNET/Core/Contracts.cs#L4)

## 技術入口の候補

以下は保存済み提出内容。独立検証・採用は未実施。

### Web起動入口

ID：`entry:web-program`。

トップレベルProgramがWebApplicationを構築し、WebHostSetup.Add/Use、MapControllers、ルート転送を設定してRunする。起動・登録の技術入口であり、独立した利用者機能としては数えない。

原文：[Program.cs:2-8](../../srcs/CSharp_ASPNET/Program.cs#L2)

### GET /

ID：`entry:web-root`。

ルート要求を/studentsへ転送する登録。転送先機能の結果をこの入口の独立した完了結果とは扱わない。

原文：[Program.cs:7-7](../../srcs/CSharp_ASPNET/Program.cs#L7)

### GET /health

ID：`entry:health`。

status=running、database=not-testedを返す診断入口。DB接続の検証結果を示すものではない。

原文：[Infrastructure/WebHostSetup.cs:36-36](../../srcs/CSharp_ASPNET/Infrastructure/WebHostSetup.cs#L36)

### POST /_evaluation/session

ID：`entry:evaluation-session`。

Development環境かつサーバー側秘密設定が存在する場合に、要求ヘッダーを検証し、設定された主体・役割で認証Cookieを発行する評価用入口。条件不成立時は404等を返す。通常ログイン画面とは別の技術入口として保持し、有効な配備や実行成功は推定しない。

原文：[Infrastructure/WebHostSetup.cs:34-35](../../srcs/CSharp_ASPNET/Infrastructure/WebHostSetup.cs#L34)

### GET /login

ID：`entry:login-get`。

匿名アクセスを許可するMVC入口。LocalLogin無効時は404、認証済みなら学生検索へ遷移し、それ以外はログイン画面を返す。

原文：[Web/Controllers/AccountController.cs:10-16](../../srcs/CSharp_ASPNET/Web/Controllers/AccountController.cs#L10)

### POST /login

ID：`entry:login-post`。

匿名アクセスを許可する資格情報送信のMVC入口。認証結果に応じてCookie発行・遷移、または401とエラー付きログイン画面を返す。

原文：[Web/Controllers/AccountController.cs:18-34](../../srcs/CSharp_ASPNET/Web/Controllers/AccountController.cs#L18)

### POST /logout

ID：`entry:logout-post`。

認証を要求するMVC入口。Cookie認証をサインアウトして/loginへ遷移する。

原文：[Web/Controllers/AccountController.cs:36-41](../../srcs/CSharp_ASPNET/Web/Controllers/AccountController.cs#L36)

### GET /menu

ID：`entry:menu-get`。

認証を要求し、メニュービューを返すMVC入口。ビューは学生検索と、Viewer以外への新規登録リンクを表示する。

原文：[Web/Controllers/MenuController.cs:6-11](../../srcs/CSharp_ASPNET/Web/Controllers/MenuController.cs#L6)、[Views/Menu/Index.cshtml:1-7](../../srcs/CSharp_ASPNET/Views/Menu/Index.cshtml#L1)

### GET /students

ID：`entry:students-index`。

認証を要求する学生検索画面入口。検索文脈を新規作成するか既存文脈を再開し、Searchビューを返す。

原文：[Web/Controllers/StudentsController.cs:5-12](../../srcs/CSharp_ASPNET/Web/Controllers/StudentsController.cs#L5)

### POST /students/search

ID：`entry:students-search`。

検索条件と文脈情報をフォーム入力として受け、検索結果またはエラーをSearchビューへ返す。

原文：[Web/Controllers/StudentsController.cs:5-5](../../srcs/CSharp_ASPNET/Web/Controllers/StudentsController.cs#L5)、[Web/Controllers/StudentsController.cs:13-22](../../srcs/CSharp_ASPNET/Web/Controllers/StudentsController.cs#L13)

### POST /students/page

ID：`entry:students-page`。

既存検索文脈のページ、表示件数、並び順を指定し、Searchビューを返す。

原文：[Web/Controllers/StudentsController.cs:5-5](../../srcs/CSharp_ASPNET/Web/Controllers/StudentsController.cs#L5)、[Web/Controllers/StudentsController.cs:23-25](../../srcs/CSharp_ASPNET/Web/Controllers/StudentsController.cs#L23)

### POST /students/clear

ID：`entry:students-clear`。

検索文脈の条件・適用結果をクリアし、未検索状態のSearchビューを返す。

原文：[Web/Controllers/StudentsController.cs:5-5](../../srcs/CSharp_ASPNET/Web/Controllers/StudentsController.cs#L5)、[Web/Controllers/StudentsController.cs:26-26](../../srcs/CSharp_ASPNET/Web/Controllers/StudentsController.cs#L26)、[Infrastructure/WebStudentCoordinator.cs:20-20](../../srcs/CSharp_ASPNET/Infrastructure/WebStudentCoordinator.cs#L20)

### POST /students/options（退役応答）

ID：`entry:students-retired-options`。

属性で宣言された入口はRetiredSearchOptionsからNotFoundを返す。候補取得機能の稼働入口とは分類しない。構文FactのhandlerShapeはexpression-not-foundであり、応答は原文で確認した。

原文：[Web/Controllers/StudentsController.cs:5-5](../../srcs/CSharp_ASPNET/Web/Controllers/StudentsController.cs#L5)、[Web/Controllers/StudentsController.cs:27-28](../../srcs/CSharp_ASPNET/Web/Controllers/StudentsController.cs#L27)

### GET /students/new

ID：`entry:students-new`。

IDなしの共通Load処理から新規学生のEditビューを返す。

原文：[Web/Controllers/StudentsController.cs:5-5](../../srcs/CSharp_ASPNET/Web/Controllers/StudentsController.cs#L5)、[Web/Controllers/StudentsController.cs:29-31](../../srcs/CSharp_ASPNET/Web/Controllers/StudentsController.cs#L29)

### GET /students/{id:long}

ID：`entry:students-detail`。

選択学生の情報と編集スナップショットを準備し、参照・編集共用のEditビューを返す。

原文：[Web/Controllers/StudentsController.cs:5-5](../../srcs/CSharp_ASPNET/Web/Controllers/StudentsController.cs#L5)、[Web/Controllers/StudentsController.cs:30-31](../../srcs/CSharp_ASPNET/Web/Controllers/StudentsController.cs#L30)

### POST /students/create

ID：`entry:students-create`。

Input接頭辞のStudentSaveInputを受け、IDなしの共通保存処理へ渡すHTMLフォーム入口。

原文：[Web/Controllers/StudentsController.cs:5-5](../../srcs/CSharp_ASPNET/Web/Controllers/StudentsController.cs#L5)、[Web/Controllers/StudentsController.cs:32-40](../../srcs/CSharp_ASPNET/Web/Controllers/StudentsController.cs#L32)

### POST /students/{id:long}/update

ID：`entry:students-update`。

対象IDとStudentSaveInputを共通保存処理へ渡し、成功時の検索復帰またはEditビューの結果表示を行う。

原文：[Web/Controllers/StudentsController.cs:5-5](../../srcs/CSharp_ASPNET/Web/Controllers/StudentsController.cs#L5)、[Web/Controllers/StudentsController.cs:33-40](../../srcs/CSharp_ASPNET/Web/Controllers/StudentsController.cs#L33)

### POST /students/reset

ID：`entry:students-reset`。

利用者と対象IDに対応するスナップショットから元の入力値を復元し、Editビューを返す。

原文：[Web/Controllers/StudentsController.cs:5-5](../../srcs/CSharp_ASPNET/Web/Controllers/StudentsController.cs#L5)、[Web/Controllers/StudentsController.cs:41-41](../../srcs/CSharp_ASPNET/Web/Controllers/StudentsController.cs#L41)

### POST /students/{id:long}/delete

ID：`entry:students-delete`。

スナップショットと復帰先を確認して削除調整処理を呼び、成功時は303で検索画面へ戻す。

原文：[Web/Controllers/StudentsController.cs:5-5](../../srcs/CSharp_ASPNET/Web/Controllers/StudentsController.cs#L5)、[Web/Controllers/StudentsController.cs:43-44](../../srcs/CSharp_ASPNET/Web/Controllers/StudentsController.cs#L43)

### StudentMaintenance class|code 入り口

ID：`entry:maintenance-cli`。

ソリューション所属のnet10.0実行プロジェクトのトップレベル入口。class/codeとJSONファイルを受け取り、接続設定とNative/SharedAccessの選択を読み、対応サービスへ渡す。結果JSONと終了コード、例外時の標準エラー出力を定義する。CLIという入口形式は主機能の意味分類とは分離する。

原文：[maintenance/Program.cs:1-19](../../srcs/CSharp_ASPNET/maintenance/Program.cs#L1)、[maintenance/StudentMaintenance.csproj:1-4](../../srcs/CSharp_ASPNET/maintenance/StudentMaintenance.csproj#L1)、[StudentManagement.slnx:1-4](../../srcs/CSharp_ASPNET/StudentManagement.slnx#L1)

## 支援資源の候補

以下は保存済み提出内容。独立検証・採用は未実施。

### プロジェクト所属・除外・生成物の調査境界

ID：`support:catalog-source-boundary`。

WebはCoreをProjectReferenceし、保守CLIもCoreを参照する。WebのCompile/Content規則はtests、deployment、maintenance、database等を分離し、Directory.Build.propsはbuild/.tmp等を既定項目から除外する。省略testsにはsolutionとbuild設定上の試験プロジェクト参照がある。DB生成器は外部仕様を入力に取得済みSQLとbuild/generation記録を生成するが、現行プロジェクトにその仕様をコンパイルする規則は見られない。省略試験・出力の内容や実績は未検証。XML、JSON、Python、JavaScript、SQLは構文アダプター非対応のため原文として確認した。

原文：[StudentManagement.Web.csproj:1-7](../../srcs/CSharp_ASPNET/StudentManagement.Web.csproj#L1)、[maintenance/StudentMaintenance.csproj:1-4](../../srcs/CSharp_ASPNET/maintenance/StudentMaintenance.csproj#L1)、[StudentManagement.slnx:1-9](../../srcs/CSharp_ASPNET/StudentManagement.slnx#L1)、[Directory.Build.props:1-15](../../srcs/CSharp_ASPNET/Directory.Build.props#L1)、[tools/build_config.json:1-19](../../srcs/CSharp_ASPNET/tools/build_config.json#L1)、[tools/build.py:70-101](../../srcs/CSharp_ASPNET/tools/build.py#L70)、[database/generate.mjs:6-23](../../srcs/CSharp_ASPNET/database/generate.mjs#L6)、[database/generate.mjs:78-110](../../srcs/CSharp_ASPNET/database/generate.mjs#L78)

### Native EXEC専用入口への注意書き

ID：`support:native-production-entrance-note`。

SQLサービスとDDLには別途Native本番用EXEC専用入口が必要との注意書きがある。一方、取得した現行Web登録はSqlServerStudentServiceを直接構築し、Web権限SQLもテーブルへのSELECT/INSERT/UPDATEを設定する。この注意書きだけからstudent_apiを現行技術入口や欠落した登録先として追加しない。別配備方式の実装・本番適合性は確認できず、現行ソースの実行成功も主張しない。

原文：[Core/SqlServerStudentService.cs:12-14](../../srcs/CSharp_ASPNET/Core/SqlServerStudentService.cs#L12)、[Infrastructure/WebHostSetup.cs:25-25](../../srcs/CSharp_ASPNET/Infrastructure/WebHostSetup.cs#L25)、[database/001_schema.sql:213-218](../../srcs/CSharp_ASPNET/database/001_schema.sql#L213)、[database/003_web_permissions.sql:1-26](../../srcs/CSharp_ASPNET/database/003_web_permissions.sql#L1)

### 残存する候補取得調整宣言

ID：`support:student-options-declaration`。

WebStudentCoordinator.Optionsは要求型を受け、学生・候補の取得と表示変換を行う宣言として残る。全取得ソース対象のOptions(検索では宣言と退役応答等だけが返り、取得した入口一覧にも対応する稼働候補APIはない。静的な公開導線は観測されないが、動的到達不能までは断定しない。

原文：[Infrastructure/WebStudentCoordinator.cs:21-21](../../srcs/CSharp_ASPNET/Infrastructure/WebStudentCoordinator.cs#L21)、[Web/Controllers/StudentsController.cs:27-28](../../srcs/CSharp_ASPNET/Web/Controllers/StudentsController.cs#L27)、[Program.cs:3-8](../../srcs/CSharp_ASPNET/Program.cs#L3)、[StudentManagement.Web.csproj:1-7](../../srcs/CSharp_ASPNET/StudentManagement.Web.csproj#L1)

### Native DDL・初期コード生成器

ID：`support:database-source-generator`。

database/generate.mjsは外部の仕様Markdownを読み、001_schema.sql、002_seed.sqlとbuild/generation/database-inputs.jsonを書き出す著作済み生成器。生成対象はSQL・生成記録であり、実行時C#ソースを生成する宣言ではない。参照仕様は許可範囲外のため未読で、生成器も未実行。

原文：[database/generate.mjs:1-26](../../srcs/CSharp_ASPNET/database/generate.mjs#L1)、[database/generate.mjs:77-110](../../srcs/CSharp_ASPNET/database/generate.mjs#L77)

### Native初期コード投入SQL

ID：`support:database-seed`。

002_seed.sqlは5分類70コードを宣言し、既存値との差異を検査して不足分を追加する導入支援SQL。学生・クラスの初期行は作成しない。投入成功や実DB件数を示す実行証跡ではない。

原文：[database/002_seed.sql:1-20](../../srcs/CSharp_ASPNET/database/002_seed.sql#L1)、[database/002_seed.sql:77-93](../../srcs/CSharp_ASPNET/database/002_seed.sql#L77)

### Native Web用DB権限設定SQL

ID：`support:database-web-permissions`。

003_web_permissions.sqlはstudent_viewer/staff/adminの表権限と継承を設定する配備支援資料。Webの状態・確認情報はメモリー保持と記し、t_confirmation/t_runtime_stateのDML権限を要求しない。利用者向け機能ではない。

原文：[database/003_web_permissions.sql:1-26](../../srcs/CSharp_ASPNET/database/003_web_permissions.sql#L1)

### Native DB配備確認SQL

ID：`support:database-deployment-verification`。

004_verify_deployment.sqlは製品版・表構成・制約・初期コード・宣言権限を検査する読取確認プログラム。PASS文字列は成功時の出力コードであり、この解析でのテスト成功を示さない。実Windowsログインの有効権限確認は別途必要と本文に記す。

原文：[database/004_verify_deployment.sql:1-28](../../srcs/CSharp_ASPNET/database/004_verify_deployment.sql#L1)、[database/004_verify_deployment.sql:117-135](../../srcs/CSharp_ASPNET/database/004_verify_deployment.sql#L117)

### 厳格JSON読込の残存宣言

ID：`support:strict-json-declaration`。

JSONの型・未知項目・重複項目・深さ・本文サイズを検証するStrictJson宣言。取得済み逆参照調査では外部の静的消費者を観測しておらず、共通消費者や公開APIを補完しない。動的利用や実行時到達不能を断定する材料ではない。

原文：[Infrastructure/StrictJson.cs:1-15](../../srcs/CSharp_ASPNET/Infrastructure/StrictJson.cs#L1)

## 資料の候補

以下は保存済み提出内容。独立検証・採用は未実施。

### SharedAccess DDLの収録来歴

ID：`material:shared-access-schema-provenance`。

provenance.jsonは収録DDLのコピー元・ハッシュと共有DB起動プロファイルを記録する資料。埋め込まれた別プロジェクトの生成元情報は来歴の主張として扱い、別プロジェクトを取得・解析した証拠にはしない。SQL実行、実スキーマ検査、互換性承認はいずれもfalseと明記する。

原文：[database/shared-access/provenance.json:1-19](../../srcs/CSharp_ASPNET/database/shared-access/provenance.json#L1)、[database/shared-access/provenance.json:91-121](../../srcs/CSharp_ASPNET/database/shared-access/provenance.json#L91)

### DB導入・プロファイル区分の説明

ID：`material:database-profile-guidance`。

database/README.mdはSharedTrainingSqlが共有DBを使い、Native用DDL・seed・空DB専用試験を共有DBへ適用しないと説明する。外部仕様へのリンクは追跡せず、本文は導入説明として保持する。

原文：[database/README.md:1-16](../../srcs/CSharp_ASPNET/database/README.md#L1)

## 後続調査として保存されたメモ

- relationship：学生MVC入口から調整処理、登録されたIStudentService実装、契約DTO、SQLデータ対象までの関係を確認する。構文callの名称一致だけで解決済みの辺にしない。
- behavior：学生保存・論理削除について、入力検証、重複確認、期待版、権限、結果不明時の扱い、DB更新とトランザクションを必要範囲で確認する。本目録の画面結果を実行成功の証拠にはしない。

これらは今回実行した後続工程や解決済み事項ではない。生ログ・中間応答・実行記録はGit管理外の.tmpへ保存し、このレビューを新しい正式ContextBaseとして後続Agentへ渡さない。


## 今回追加された未検証草稿（17件）

以下も作者の保存済み提出内容で、候補や採用成果へ手作業で変換していない。

### ビルド・検査・発行の実行支援

ID：`support:build-orchestration`。kind：`support`。

tools/build.pyは設定されたsolution、production project、試験projectを使い、restore・build・検査・publishと結果記録を制御する。Directory.Build.propsは中間出力とパッケージ保存先を.tmpへ配置する。これは開発支援のソースであり、記載されたPASS生成処理を今回の実行結果とは扱わない。

原文：[tools/build.py:1-101](../../srcs/CSharp_ASPNET/tools/build.py#L1)、[tools/build_config.json:1-19](../../srcs/CSharp_ASPNET/tools/build_config.json#L1)、[Directory.Build.props:1-15](../../srcs/CSharp_ASPNET/Directory.Build.props#L1)

### 開発出力パスの検査と検査用ソース

ID：`support:output-path-guard`。kind：`support`。

build_paths.pyのOutputPathsはbuild/.tmp配下の出力と既存パスのredirectを検査し、build helperが使用する。tools/test_output_paths.pyには一時fixtureとjunction等を使う検査手順がある。業務アプリの共通処理には数えず、検査コードの存在と検査成功を区別する。

原文：[build_paths.py:1-110](../../srcs/CSharp_ASPNET/build_paths.py#L1)、[tools/build.py:5-15](../../srcs/CSharp_ASPNET/tools/build.py#L5)、[tools/test_output_paths.py:1-153](../../srcs/CSharp_ASPNET/tools/test_output_paths.py#L1)

### Native専用DBの導入・確認・主体関連付け

ID：`support:express-database-deployment`。kind：`support`。

Deploy-Database.ps1には固定した専用DBに対するInstall、Verify、BindPrincipalとPlanOnlyがある。ローカルExpress major17、Windows認証等を検査し、取得済み001～004 SQLを使用する配備支援である。現行業務機能とは分離し、導入済みであるとは主張しない。

原文：[database/Deploy-Database.ps1:1-26](../../srcs/CSharp_ASPNET/database/Deploy-Database.ps1#L1)、[database/Deploy-Database.ps1:65-165](../../srcs/CSharp_ASPNET/database/Deploy-Database.ps1#L65)

### Azure資源準備とWeb発行支援

ID：`support:azure-provision-publish`。kind：`support`。

Provision-FreeAzure.ps1は固定資源の計画表示と明示実行を分け、F1プランとSQL無料枠設定を検査する。Publish-FreeAzure.ps1はWeb projectをwin-x86で発行し、除外対象を確認してZIP配備する。単独発行時には検査未実施を記録する実装であり、今回の配備・費用・検査実績は未確認。

原文：[deployment/Provision-FreeAzure.ps1:1-49](../../srcs/CSharp_ASPNET/deployment/Provision-FreeAzure.ps1#L1)、[deployment/Publish-FreeAzure.ps1:1-44](../../srcs/CSharp_ASPNET/deployment/Publish-FreeAzure.ps1#L1)、[StudentManagement.Web.csproj:4-6](../../srcs/CSharp_ASPNET/StudentManagement.Web.csproj#L4)

### Azure SQL初期化・接続設定支援

ID：`support:azure-database-configuration`。kind：`support`。

Configure-AzureDatabase.ps1は初期化用Python、サービス確認用projectと接続設定を組み合わせる。Initialize-AzureDatabase.pyはNative DDLのコード参照列幅とseed表変数の照合を配備入力上で適合させ、既知の空状態を検査して初期化・権限設定を行う。原DDLの定義、配備時変換、実DB状態を同一視しない。

原文：[deployment/Configure-AzureDatabase.ps1:16-42](../../srcs/CSharp_ASPNET/deployment/Configure-AzureDatabase.ps1#L16)、[deployment/Initialize-AzureDatabase.py:10-30](../../srcs/CSharp_ASPNET/deployment/Initialize-AzureDatabase.py#L10)、[deployment/Initialize-AzureDatabase.py:81-145](../../srcs/CSharp_ASPNET/deployment/Initialize-AzureDatabase.py#L81)

### 配備用ログイン設定とパスワードハッシュ生成

ID：`support:azure-web-login-configuration`。kind：`support`。

Configure-AzureWebLogin.ps1は配備用資格情報の準備、ハッシュ生成projectの呼出、LocalLogin設定の反映を行う。LoginPasswordHashは環境変数から受け取る値をPasswordHasherでハッシュ化して指定ファイルへ保存する配備支援である。利用者のログイン主機能と認証共通サービスは別記録に保持する。資格情報ファイルや実際の値は取得していない。

原文：[deployment/Configure-AzureWebLogin.ps1:1-30](../../srcs/CSharp_ASPNET/deployment/Configure-AzureWebLogin.ps1#L1)、[deployment/LoginPasswordHash/Program.cs:4-9](../../srcs/CSharp_ASPNET/deployment/LoginPasswordHash/Program.cs#L4)、[deployment/LoginPasswordHash/LoginPasswordHash.csproj:1-4](../../srcs/CSharp_ASPNET/deployment/LoginPasswordHash/LoginPasswordHash.csproj#L1)

### Azure DBのサービス・worker確認用ソース

ID：`support:azure-database-verification`。kind：`support`。

DatabaseSmokeはCoreを参照し、SqlServerStudentServiceの候補取得と検索結果を検査する独立した配備確認プログラムである。Verify-AzureRemoteDatabase.pyには認証済みSCM経由でworkerのDB接続・初期件数・役割を確認する処理がある。出力文字列やassertは検査手順の証拠であり、成功した実行の証拠ではない。

原文：[deployment/DatabaseSmoke/DatabaseSmoke.csproj:1-4](../../srcs/CSharp_ASPNET/deployment/DatabaseSmoke/DatabaseSmoke.csproj#L1)、[deployment/DatabaseSmoke/Program.cs:3-9](../../srcs/CSharp_ASPNET/deployment/DatabaseSmoke/Program.cs#L3)、[deployment/Verify-AzureRemoteDatabase.py:1-35](../../srcs/CSharp_ASPNET/deployment/Verify-AzureRemoteDatabase.py#L1)、[deployment/Configure-AzureDatabase.ps1:27-32](../../srcs/CSharp_ASPNET/deployment/Configure-AzureDatabase.ps1#L27)

### 配備先ログインのブラウザー確認用ソース

ID：`support:azure-web-login-verification`。kind：`support`。

Verify-AzureWebLogin.pyにはPlaywright/Chromiumで匿名アクセス、ログインフォーム、CSRF、認証失敗・成功、検索、ログアウト等を確認し、画像とJSONを保存する処理がある。現在の画面との一致や検査成功は未確認で、過去の結果や受入承認として扱わない。

原文：[deployment/Verify-AzureWebLogin.py:1-88](../../srcs/CSharp_ASPNET/deployment/Verify-AzureWebLogin.py#L1)

### 配備資格情報のローカル参照支援

ID：`support:deployment-credential-access`。kind：`support`。

Get-AzureDatabaseLogin.ps1とGet-AzureWebLogin.ps1は配備状態とWindows暗号化資格情報ファイルを読む補助スクリプトで、明示switchによる表示・コピー処理を持つ。Web利用者向けのアカウント管理機能には数えない。参照される私有ファイルや秘密値は取得していない。

原文：[deployment/Get-AzureDatabaseLogin.ps1:1-6](../../srcs/CSharp_ASPNET/deployment/Get-AzureDatabaseLogin.ps1#L1)、[deployment/Get-AzureWebLogin.ps1:1-7](../../srcs/CSharp_ASPNET/deployment/Get-AzureWebLogin.ps1#L1)

### アプリ構成・起動・検査の説明文書

ID：`material:application-source-guidance`。kind：`material`。

README.mdは起動プロファイル、共有DBとNativeの区分、出力配置、認証、画面、保守CLI、検査手順を説明する。外部仕様や省略された結果へのリンクは追跡していない。文書内のPASS・実機確認・再生成の記述は著者の報告であり、今回取得した実行証拠ではない。

原文：[README.md:1-72](../../srcs/CSharp_ASPNET/README.md#L1)

### Azure配備・DB適合・ログイン設定の説明文書

ID：`material:azure-deployment-guidance`。kind：`material`。

deployment/README.mdは配備対象、必要ツール、資格情報管理、DDL/seedの配備時適合、検査範囲、単一所有者ログイン設定を説明する。実配備・DB検査等の記述は文書上の報告として保持し、現在の状態、実行結果、利用者受入を証明するものとはしない。

原文：[deployment/README.md:1-51](../../srcs/CSharp_ASPNET/deployment/README.md#L1)

### 管理者マスタ保守CLIの説明文書

ID：`material:maintenance-cli-guidance`。kind：`material`。

maintenance/README.mdはclass/codeへのJSON入力、DB接続主体による権限検査とNative/SharedAccessの区分を説明する。保守機能そのものはCLIとサービスの原文で確認し、文書内の無変更保存確認を今回の検査結果や承認とは扱わない。

原文：[maintenance/README.md:1-13](../../srcs/CSharp_ASPNET/maintenance/README.md#L1)

### Microsoft.Data.SqlClient 6.1.3

ID：`dependency:microsoft-data-sqlclient`。kind：`dependency`。

Core projectがMicrosoft.Data.SqlClient 6.1.3をPackageReferenceする。WebはCoreをProjectReferenceし、Webのlockファイルにも同版と推移依存が記載される。第三者ライブラリとして保持し、業務機能・自作共通部品には数えない。復元・導入状況は未確認。

原文：[Core/StudentManagement.Core.csproj:8-11](../../srcs/CSharp_ASPNET/Core/StudentManagement.Core.csproj#L8)、[StudentManagement.Web.csproj:2-3](../../srcs/CSharp_ASPNET/StudentManagement.Web.csproj#L2)、[packages.lock.json:35-58](../../srcs/CSharp_ASPNET/packages.lock.json#L35)

### System.Security.Cryptography.Pkcs 9.0.21

ID：`dependency:system-security-cryptography-pkcs`。kind：`dependency`。

Core projectがSystem.Security.Cryptography.Pkcs 9.0.21を明示参照し、Web lockファイルにも同版が記載される。パッケージ参照の観測であり、この宣言だけから業務上の用途、実行時使用、脆弱性評価を補わない。

原文：[Core/StudentManagement.Core.csproj:8-11](../../srcs/CSharp_ASPNET/Core/StudentManagement.Core.csproj#L8)、[packages.lock.json:150-173](../../srcs/CSharp_ASPNET/packages.lock.json#L150)

### Webの固定NuGet推移依存定義

ID：`dependency:nuget-lock-closure`。kind：`dependency`。

packages.lock.jsonはnet10.0とnet10.0/win-x86について、SqlClient、Azure.Identity、IdentityModel等の版・依存関係を記録する。Web projectはlockファイル作成を設定し、build helperはlocked-modeで復元するソースを持つ。lock記載を実行時ロードや現在の監査合格とは解釈しない。

原文：[packages.lock.json:1-201](../../srcs/CSharp_ASPNET/packages.lock.json#L1)、[StudentManagement.Web.csproj:1-3](../../srcs/CSharp_ASPNET/StudentManagement.Web.csproj#L1)、[tools/build.py:70-73](../../srcs/CSharp_ASPNET/tools/build.py#L70)

### 配備・確認用の外部ツール依存

ID：`dependency:deployment-verification-toolchain`。kind：`dependency`。

配備・確認ソースはAzure CLI、.NET SDK、Python/pyodbc、Playwright/Chromium、sqlcmd等を使用する。必要環境の説明と呼出・importの原文を依存根拠とし、導入済みであるとは判断しない。業務ユーザー機能や自作共通処理とは別の支援環境依存である。

原文：[deployment/README.md:14-28](../../srcs/CSharp_ASPNET/deployment/README.md#L14)、[deployment/Initialize-AzureDatabase.py:1-8](../../srcs/CSharp_ASPNET/deployment/Initialize-AzureDatabase.py#L1)、[deployment/Verify-AzureWebLogin.py:1-7](../../srcs/CSharp_ASPNET/deployment/Verify-AzureWebLogin.py#L1)、[database/Deploy-Database.ps1:27-65](../../srcs/CSharp_ASPNET/database/Deploy-Database.ps1#L27)

### selected-systemの機能分割と支援資源の区分

ID：`system:catalog-function-partition`。kind：`system`。

contextbase-catalog/1による主機能の分割は、業務・学生情報管理2件（学生情報照会、学生情報登録・保守）、業務・マスタ管理2件（CLIのクラス保守、コード保守）、system.authentication 2件（ログイン、ログアウト）の計6件。照会は一覧結果、保守は保存結果、認証開始・終了は各セッション結果を根拠とする。登録・変更・論理削除・詳細参照・確認・取消・保守対象選択は既存のoperation記録、共有実装とUI責任はcommon、URLとCLI入口はentryに分離する。メニューは遷移選択のみで主機能に含めない。ビルド・配備・検査・ハッシュ生成はsupport、文書はmaterial、第三者資源はdependency、物理DDLとDTO等はdataとして別記録に保持する。件数はこの分割の推論結果であり、実行・受入を表さない。

原文：[Web/Controllers/AccountController.cs:10-41](../../srcs/CSharp_ASPNET/Web/Controllers/AccountController.cs#L10)、[Views/Account/Login.cshtml:1-13](../../srcs/CSharp_ASPNET/Views/Account/Login.cshtml#L1)、[Views/Shared/_Layout.cshtml:2-4](../../srcs/CSharp_ASPNET/Views/Shared/_Layout.cshtml#L2)、[Views/Menu/Index.cshtml:1-7](../../srcs/CSharp_ASPNET/Views/Menu/Index.cshtml#L1)、[Views/Students/Search.cshtml:14-77](../../srcs/CSharp_ASPNET/Views/Students/Search.cshtml#L14)、[Views/Students/Edit.cshtml:141-176](../../srcs/CSharp_ASPNET/Views/Students/Edit.cshtml#L141)、[Web/Controllers/StudentsController.cs:5-46](../../srcs/CSharp_ASPNET/Web/Controllers/StudentsController.cs#L5)、[maintenance/Program.cs:4-19](../../srcs/CSharp_ASPNET/maintenance/Program.cs#L4)、[Core/MasterMaintenanceService.cs:19-128](../../srcs/CSharp_ASPNET/Core/MasterMaintenanceService.cs#L19)、[StudentManagement.Web.csproj:1-7](../../srcs/CSharp_ASPNET/StudentManagement.Web.csproj#L1)、[tools/build_config.json:1-19](../../srcs/CSharp_ASPNET/tools/build_config.json#L1)
