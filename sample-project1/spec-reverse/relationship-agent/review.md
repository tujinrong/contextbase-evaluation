# Relationship 関係候補のレビュー

**改名前test-project1の実行記録。** project移動後も証拠内のprojectId・絶対パス・hashは原値を保持する。新sample-project1は未解析で、現在の既定成果先は`spec-reverse/CSharp_ASPNET/`。ここに保持する旧成果・targetを新projectへ転用しない。ソースリンクは移動後の参照位置を示し、当時の根拠は記録されたsnapshotとhashで識別する。

**未採用・独立原文検証が未完了。正式ContextBaseではない。**

2026-10-28。現在の78ファイルから作成した候補を表示する。旧76ファイル版の未採用判定を現在版の検証結果へ流用しない。

## 入力と検証状態

- 追加入力: `database/shared-access/001-schema.sql` と `provenance.json`。変換工程のリポジトリ内DDLを同一bytesで参照複製し、元パス・SHA・生成補助と利用設定の対応を固定した。
- 元の76入力ファイルは変更していない。Native用DDLをSharedAccessへ適用していない。SQL実行・実DB調査は行っていない。
- Discoveryは新入力で抽出・独立検証・採用・公開済み。Relationshipは受領目録のローカル再検証と関係候補の機械検査まで完了。
- 関係の独立原文検証: 未完了。候補を後続Agentの正式前提として渡さない。
- 上流SHA: `9c1f24b11ba15a7adc80a2497b19d2f989212eab1a613eafb7dbcb53ae0e627d`
- 候補SHA: `5c3ea3ca057d6e2ad68a2fe75f773474fc3d5ab7492becbef361829763a2377b`
- Snapshot: `24746f8d3f11ba3cfce6d2f0d6e0fafc811a9ad27c3076923bfd672c7c220ae0`

## 今回の停止理由

1. 全量原文を含む検証入力は1,050,781文字で、CLI上限1,048,576文字を超過した。モデルは検証を開始できなかった。
2. 同じ候補を原文ファイル読取り方式で検証したが、読取りコマンドが2回とも `helper_unknown_error: setup refresh had errors` で起動できなかった。
3. その応答は未知の影響要求が欠落し、`A blocking/unresolved unknown must identify impacted obligations` でホストが拒否した。正常な独立検証レコードは作成されていない。

入力長対策は構文解析の品質を保証しない。読取り失敗や未受理応答を、DDL不足・関係誤り・検証合格の証拠として扱わない。

## 関係候補

以下は作者の観測・提案であり、意味上の正しさは未承認。

### Web起動からサービス登録への接続

- ID: `r-host-composition`
- 根拠種別: `observed-source`
- 参照目録: `e-host`, `c-web-pipeline`, `c-auth`, `c-training-identity`, `c-identity`, `c-web-state`, `c-coordinator`, `c-student-service`

ProgramはWebHostSetup.Add、Build、WebHostSetup.Use、MapControllersを呼ぶ。AddはRequestIdentityとWebStudentCoordinatorをScoped、認証アダプタと検索・編集・通知ストアをSingletonとして登録する。IStudentServiceの生成式はStudentDb設定とRequestIdentity.CurrentUserをSqlServerStudentServiceへ渡し、webTokens:trueと選択DBプロファイルを指定する。これは登録原文の関係であり、起動・実行の証明ではない。

原文根拠:
- [Program.cs:2](../../srcs/CSharp_ASPNET/Program.cs#L2)（2–8行、SHA `f55ce879e78e94b9144c1a9ed68fc6cfea01d45e91efc5dbbdf025d906fc1f85`）
- [Infrastructure/WebHostSetup.cs:13](../../srcs/CSharp_ASPNET/Infrastructure/WebHostSetup.cs#L13)（13–25行、SHA `319d64cab66a244193ab3d33c01e55b2638928469db4f6548183e818f1d3ee10`）
- [Infrastructure/WebStudentCoordinator.cs:3](../../srcs/CSharp_ASPNET/Infrastructure/WebStudentCoordinator.cs#L3)（3–6行、SHA `f57e213dc22534b74e357aa066e31e25e58bac5b4de1b3f5458502e06e049385`）

### 各実行プロジェクトからCoreへの参照

- ID: `r-project-boundaries`
- 根拠種別: `observed-source`
- 参照目録: `sys-outline`, `s-build`, `dep-platform-tools`, `e-host`, `e-maint`, `e-smoke`, `e-hash`

Web、StudentMaintenance、DatabaseSmokeはそれぞれCoreプロジェクトを参照する。WebはCore・maintenance・deployment等のC\#を自身のCompile対象から除外する。LoginPasswordHashはASP.NET CoreのFrameworkReferenceを持つ別実行プロジェクトで、Core参照は宣言しない。CoreはSqlClientとPkcsのPackageReferenceを宣言する。

原文根拠:
- [StudentManagement.Web.csproj:1](../../srcs/CSharp_ASPNET/StudentManagement.Web.csproj#L1)（1–7行、SHA `a82e58b4b27e6c808f2bdb24397cf679f429b2c7e8234dfef252eb5f3165badf`）
- [maintenance/StudentMaintenance.csproj:1](../../srcs/CSharp_ASPNET/maintenance/StudentMaintenance.csproj#L1)（1–4行、SHA `31bfeef4bd4bec25c23b24f91b752484a5b07de5d6b8dc7cd73aab7d8a4b9151`）
- [deployment/DatabaseSmoke/DatabaseSmoke.csproj:1](../../srcs/CSharp_ASPNET/deployment/DatabaseSmoke/DatabaseSmoke.csproj#L1)（1–4行、SHA `7e4a4b8f12c494d82275bb3518fdb4fb8fddd573575318dcd28fbd7704058600`）
- [deployment/LoginPasswordHash/LoginPasswordHash.csproj:1](../../srcs/CSharp_ASPNET/deployment/LoginPasswordHash/LoginPasswordHash.csproj#L1)（1–4行、SHA `21eaca2ae8287016e834a9522edd57d2d8ab4cfb7c1a4581e823ed378758be3b`）
- [Core/StudentManagement.Core.csproj:8](../../srcs/CSharp_ASPNET/Core/StudentManagement.Core.csproj#L8)（8–12行、SHA `445e22609b5fde4310bd7d57f04b4fc0efba7ca096526018dc6e80d9c1f833aa`）

### ルート・メニュー・学生画面間の導線

- ID: `r-navigation`
- 根拠種別: `observed-source`
- 参照目録: `e-root`, `e-menu`, `e-search`, `e-new`, `e-student`, `c-navigation`, `f-query`, `f-maintain`, `o-find-for-edit`, `o-query-detail`

GET /の登録は/studentsへリダイレクトする。認証付きMenuController.IndexはメニューViewを返し、そのViewは検索とViewer以外向けの新規登録リンクを持つ。検索Viewは/menu、新規登録、学生ID別参照・編集へのリンクを持ち、学生画面へのリンクには復帰用contextIdを渡す。

原文根拠:
- [Program.cs:6](../../srcs/CSharp_ASPNET/Program.cs#L6)（6–7行、SHA `f55ce879e78e94b9144c1a9ed68fc6cfea01d45e91efc5dbbdf025d906fc1f85`）
- [Web/Controllers/MenuController.cs:6](../../srcs/CSharp_ASPNET/Web/Controllers/MenuController.cs#L6)（6–10行、SHA `ba3fe274371fafa9464cb23dac72425bfa30450c5a673b19e44c0bfe0330aa2e`）
- [Views/Menu/Index.cshtml:1](../../srcs/CSharp_ASPNET/Views/Menu/Index.cshtml#L1)（1–7行、SHA `0f56d5d6c4e3aa8ebf7b04724db174cdcfae52a976eec9b6f1c8fbce4958e078`）
- [Views/Students/Search.cshtml:14](../../srcs/CSharp_ASPNET/Views/Students/Search.cshtml#L14)（14–18行、SHA `11b3aa90f38759dfcaf7df2f3bc0448537ce0ac1ba1828d259bd07709a0842a9`）
- [Views/Students/Search.cshtml:62](../../srcs/CSharp_ASPNET/Views/Students/Search.cshtml#L62)（62–65行、SHA `11b3aa90f38759dfcaf7df2f3bc0448537ce0ac1ba1828d259bd07709a0842a9`）

### ログイン入力・認証判定・Cookie・要求主体

- ID: `r-local-auth`
- 根拠種別: `observed-source`
- 参照目録: `f-login`, `f-logout`, `e-login`, `e-logout`, `c-auth`, `c-identity`, `d-core-contracts`, `d-web-contracts`, `r-host-composition`

Login ViewのPOST /loginは利用者名・パスワードとCSRF情報を送る。AccountControllerはLocalLogin.ReadSettingsとAuthenticateを呼び、返されたClaimsPrincipalをCookie方式のSignInAsyncへ渡す。LocalLoginは構成値を参照して認証Claimとlogin\_sessionを生成する。RequestIdentityはHttpContext.Userの識別子・セッション・役割ClaimからCurrentUserを構成する。POST /logoutは同じCookie方式のSignOutAsyncを呼ぶ。

原文根拠:
- [Views/Account/Login.cshtml:7](../../srcs/CSharp_ASPNET/Views/Account/Login.cshtml#L7)（7–12行、SHA `7083b1858924c29a25c78126c0f440e91242a7b1afb16d590c9c47aee962cd7c`）
- [Web/Controllers/AccountController.cs:10](../../srcs/CSharp_ASPNET/Web/Controllers/AccountController.cs#L10)（10–41行、SHA `eb3317ec00f640a4ea7e6c7ff4538a7a0a716030f84cc3c31220df236ce8c394`）
- [Infrastructure/LocalLogin.cs:23](../../srcs/CSharp_ASPNET/Infrastructure/LocalLogin.cs#L23)（23–35行、SHA `1ee0e2968ae2eb3e5ee078076e65be375f3e46cd4125939e3476b5ff9232e52b`）
- [Infrastructure/LocalLogin.cs:53](../../srcs/CSharp_ASPNET/Infrastructure/LocalLogin.cs#L53)（53–89行、SHA `1ee0e2968ae2eb3e5ee078076e65be375f3e46cd4125939e3476b5ff9232e52b`）
- [Infrastructure/RequestIdentity.cs:4](../../srcs/CSharp_ASPNET/Infrastructure/RequestIdentity.cs#L4)（4–16行、SHA `5b9e55700123f6465667170ef2f12eb5096f01027f3ad67b84956abea01715da`）

### 共有DB確認構成からDB役割・Web主体への接続

- ID: `r-shared-identity`
- 根拠種別: `observed-source`
- 参照目録: `c-training-identity`, `c-auth`, `c-identity`, `d-app-role`, `d-core-contracts`, `e-host`, `r-host-composition`

ホストは認証ミドルウェアの後、認可の前にSharedDatabaseTraining.ApplyAsyncを呼ぶ。Enabled、専用環境、SharedAccess、LocalLogin無効等の設定条件を満たす構成では、設定されたPrincipalを引数にt\_app\_roleをSELECTし、Reader／Staff／AdminをCoreの役割へ対応付けてCookieとHttpContext.Userを構成する。launchSettingsの共有用2プロファイルがこの構成を宣言する。実際の起動選択やDB内容は未確認である。

原文根拠:
- [Infrastructure/WebHostSetup.cs:31](../../srcs/CSharp_ASPNET/Infrastructure/WebHostSetup.cs#L31)（31–33行、SHA `319d64cab66a244193ab3d33c01e55b2638928469db4f6548183e818f1d3ee10`）
- [Infrastructure/SharedDatabaseTraining.cs:22](../../srcs/CSharp_ASPNET/Infrastructure/SharedDatabaseTraining.cs#L22)（22–41行、SHA `b6509225a3a4bb4a78a6bbfbaa79a4654067d7cdbd0564737def599400d03e43`）
- [Infrastructure/SharedDatabaseTraining.cs:48](../../srcs/CSharp_ASPNET/Infrastructure/SharedDatabaseTraining.cs#L48)（48–93行、SHA `b6509225a3a4bb4a78a6bbfbaa79a4654067d7cdbd0564737def599400d03e43`）
- [Properties/launchSettings.json:3](../../srcs/CSharp_ASPNET/Properties/launchSettings.json#L3)（3–30行、SHA `72d1f4a434b06a83dcc5537605403d3d681b971e46cc40c329e84e0c8fcddefa`）

### MVC入口から共通要求保護・失敗応答への接続

- ID: `r-request-protection`
- 根拠種別: `observed-source`
- 参照目録: `c-web-pipeline`, `c-auth`, `c-training-identity`, `c-presentation`, `e-login`, `e-logout`, `e-search`, `e-results`, `e-new`, `e-student`, `e-reset`, `e-delete`

WebHostSetupはCookie認証、CSRF、MVCの自動CSRF検証とAntiforgeryResultFilter、フォーム・本文制限を登録する。Cookie検証はLocalLoginとSharedDatabaseTrainingのAcceptsCookieへ接続する。共通ミドルウェアはWebFault等をHTMLまたは/api条件のJSONへ変換し、JSON側はWebPresentation.Errorを使用する。StudentsControllerのフォーム入口は独自FormGuardも呼ぶ。/api分岐自体は業務API登録の根拠にしない。

原文根拠:
- [Infrastructure/WebHostSetup.cs:20](../../srcs/CSharp_ASPNET/Infrastructure/WebHostSetup.cs#L20)（20–33行、SHA `319d64cab66a244193ab3d33c01e55b2638928469db4f6548183e818f1d3ee10`）
- [Infrastructure/AntiforgeryResultFilter.cs:5](../../srcs/CSharp_ASPNET/Infrastructure/AntiforgeryResultFilter.cs#L5)（5–9行、SHA `3f26dafa231f9a3bda5a1cce9e3ae2cfe76a831346c2f077c10b222f7378c2ac`）
- [Web/Controllers/StudentsController.cs:46](../../srcs/CSharp_ASPNET/Web/Controllers/StudentsController.cs#L46)（46–46行、SHA `c927cdab41e0b5d2ce38eb0f88b3680b98ea1bfd1a42634637679cd8b23037b1`）
- [Infrastructure/WebPresentation.cs:21](../../srcs/CSharp_ASPNET/Infrastructure/WebPresentation.cs#L21)（21–23行、SHA `23800e7f88e643c952a8617f5382e43c5c0d4ffa543c0c1f24e333312ea213f3`）

### 検索フォームから正規化済み検索要求への接続

- ID: `r-search-input`
- 根拠種別: `observed-source`
- 参照目録: `f-query`, `o-find-for-edit`, `e-search`, `c-coordinator`, `c-input-mapping`, `c-rules`, `c-identity`, `c-web-state`, `c-student-service`, `d-web-contracts`, `d-core-contracts`

検索ViewはCriteriaの4条件と検索状態ID・版・タブ・表示設定をPOST /students/searchへ送る。StudentsController.SearchはStudentSearchInputをSearchRequestへ組み込みCoordinator.Searchへ渡す。CoordinatorはRequestIdentity.ReadとSearchContextStore.Useを経由し、StudentSearchInput.ToCriteria→IdParser.Optional／SearchCriteria.FromRaw→StudentNormalizerの変換結果をIStudentService.SearchAsyncへ渡す。

原文根拠:
- [Views/Students/Search.cshtml:20](../../srcs/CSharp_ASPNET/Views/Students/Search.cshtml#L20)（20–46行、SHA `11b3aa90f38759dfcaf7df2f3bc0448537ce0ac1ba1828d259bd07709a0842a9`）
- [Web/Controllers/StudentsController.cs:13](../../srcs/CSharp_ASPNET/Web/Controllers/StudentsController.cs#L13)（13–22行、SHA `c927cdab41e0b5d2ce38eb0f88b3680b98ea1bfd1a42634637679cd8b23037b1`）
- [Infrastructure/WebStudentCoordinator.cs:7](../../srcs/CSharp_ASPNET/Infrastructure/WebStudentCoordinator.cs#L7)（7–15行、SHA `f57e213dc22534b74e357aa066e31e25e58bac5b4de1b3f5458502e06e049385`）
- [Web/Inputs/StudentSearchInput.cs:5](../../srcs/CSharp_ASPNET/Web/Inputs/StudentSearchInput.cs#L5)（5–17行、SHA `a3fd854dafe0e42fe77a9a86c789b435ad16c1239025c734455e25fc1f831164`）
- [Core/Contracts.cs:45](../../srcs/CSharp_ASPNET/Core/Contracts.cs#L45)（45–61行、SHA `2071c2d7824c4aacfeb8d87f1eb3905e6bb4eeca01de4f865a6f50440b226df4`）

### 検索・ページ・復帰・クリアと検索状態ストア

- ID: `r-search-state`
- 根拠種別: `observed-source`
- 参照目録: `f-query`, `o-query-results`, `e-search`, `e-results`, `c-coordinator`, `c-web-state`, `c-identity`, `d-web-contracts`, `d-core-contracts`, `r-search-input`

GET /studentsは新規検索状態を作成するか既存状態を取得し、復帰時はCoordinator.Resumeへ接続する。POST pageはCoordinator.Page、POST clearはCoordinator.Clearへ接続する。Search／Page／ResumeはSearchAsyncの結果をEntryのApplied・LastResult等へ保持し、ClearはEntryを初期化する。Entryの所有者・セッション・タブ・版の照合はSearchContextStore.Get／Useが担当する。ストアの保存先はConcurrentDictionaryである。

原文根拠:
- [Web/Controllers/StudentsController.cs:8](../../srcs/CSharp_ASPNET/Web/Controllers/StudentsController.cs#L8)（8–26行、SHA `c927cdab41e0b5d2ce38eb0f88b3680b98ea1bfd1a42634637679cd8b23037b1`）
- [Infrastructure/WebStudentCoordinator.cs:5](../../srcs/CSharp_ASPNET/Infrastructure/WebStudentCoordinator.cs#L5)（5–20行、SHA `f57e213dc22534b74e357aa066e31e25e58bac5b4de1b3f5458502e06e049385`）
- [Infrastructure/SearchContextStore.cs:10](../../srcs/CSharp_ASPNET/Infrastructure/SearchContextStore.cs#L10)（10–17行、SHA `2418cabe8c3878cd7528e2280aa689642d55dd4685fef017e78046cf4ae5e04a`）

### 学生検索サービスから読取対象・一覧契約への接続

- ID: `r-search-data`
- 根拠種別: `observed-source`
- 参照目録: `f-query`, `c-student-service`, `c-rules`, `c-db-boundary`, `d-student`, `d-class`, `d-code`, `d-core-contracts`, `r-search-input`

SqlServerStudentService.SearchAsyncはSearchCriteriaを受け、在籍コードをm\_code、指定クラスをm\_classで照合する。件数SQLはm\_student、一覧SQLはm\_studentからm\_classと学年・在籍名称のm\_codeへのLEFT JOINを使用する。条件値はParamへ渡し、学籍番号・氏名のLIKE値にはEscapeLikeを使用する。ReaderをListItemでStudentListItemへ変換し、SearchResultとして呼出元へ返す。

原文根拠:
- [Core/SqlServerStudentService.cs:116](../../srcs/CSharp_ASPNET/Core/SqlServerStudentService.cs#L116)（116–176行、SHA `6a0004747afd6ed0a6fbc83cb7b936c4322d99ab5502e5ca0006efd887bac47a`）
- [Core/SqlServerStudentService.cs:223](../../srcs/CSharp_ASPNET/Core/SqlServerStudentService.cs#L223)（223–228行、SHA `6a0004747afd6ed0a6fbc83cb7b936c4322d99ab5502e5ca0006efd887bac47a`）
- [Core/Contracts.cs:63](../../srcs/CSharp_ASPNET/Core/Contracts.cs#L63)（63–76行、SHA `2071c2d7824c4aacfeb8d87f1eb3905e6bb4eeca01de4f865a6f50440b226df4`）

### 検索結果から画面モデル・Razor表示への接続

- ID: `r-search-output`
- 根拠種別: `observed-source`
- 参照目録: `f-query`, `c-coordinator`, `c-presentation`, `c-rules`, `d-core-contracts`, `d-web-contracts`, `r-search-state`, `r-search-data`

Coordinator.PresentはSearchResultとEntryから表示結果を構成し、一覧行はWebPresentation.Row、検索時刻はWebPresentation.Timeへ渡す。StudentsController.SearchModelはこれをStudentSearchPageModel.JsonでJsonElementにし、LookupSet・原入力・状態とともにSearch Viewへ渡す。Viewはitems、件数、ページ、検索日時を読み、実行条件にはEntry.AppliedとDraftを使用する。生年月日の和暦表示はStudentListItemからJapaneseDateServiceへ接続する。

原文根拠:
- [Infrastructure/WebStudentCoordinator.cs:26](../../srcs/CSharp_ASPNET/Infrastructure/WebStudentCoordinator.cs#L26)（26–27行、SHA `f57e213dc22534b74e357aa066e31e25e58bac5b4de1b3f5458502e06e049385`）
- [Infrastructure/WebPresentation.cs:5](../../srcs/CSharp_ASPNET/Infrastructure/WebPresentation.cs#L5)（5–7行、SHA `23800e7f88e643c952a8617f5382e43c5c0d4ffa543c0c1f24e333312ea213f3`）
- [Infrastructure/WebPresentation.cs:20](../../srcs/CSharp_ASPNET/Infrastructure/WebPresentation.cs#L20)（20–20行、SHA `23800e7f88e643c952a8617f5382e43c5c0d4ffa543c0c1f24e333312ea213f3`）
- [Web/Controllers/StudentsController.cs:45](../../srcs/CSharp_ASPNET/Web/Controllers/StudentsController.cs#L45)（45–45行、SHA `c927cdab41e0b5d2ce38eb0f88b3680b98ea1bfd1a42634637679cd8b23037b1`）
- [Web/Models/StudentSearchPageModel.cs:4](../../srcs/CSharp_ASPNET/Web/Models/StudentSearchPageModel.cs#L4)（4–15行、SHA `52fd3f4d09f9e2c8dfcc4ee8106577ebf0d06ae0fc1d9641654183ac465e1cb6`）
- [Views/Students/Search.cshtml:48](../../srcs/CSharp_ASPNET/Views/Students/Search.cshtml#L48)（48–75行、SHA `11b3aa90f38759dfcaf7df2f3bc0448537ce0ac1ba1828d259bd07709a0842a9`）
- [Core/Contracts.cs:63](../../srcs/CSharp_ASPNET/Core/Contracts.cs#L63)（63–67行、SHA `2071c2d7824c4aacfeb8d87f1eb3905e6bb4eeca01de4f865a6f50440b226df4`）

### 候補取得の呼出元・SQL対象・画面利用

- ID: `r-lookups`
- 根拠種別: `observed-source`
- 参照目録: `c-student-service`, `c-coordinator`, `d-code`, `d-category`, `d-class`, `d-student`, `d-core-contracts`, `e-search`, `e-new`, `e-student`, `e-reset`

検索画面モデルはLookupAsync\(false,ct\)、編集読込・保存再表示・Resetは既定LookupAsync\(ct\)を呼ぶ。実装の既定 overloadはincludeOccupancy:trueへ委譲する。候補SQLはm\_codeとm\_code\_category、m\_classと学年m\_codeを読み、人数を含める指定ではm\_studentを集計し、CodeEntry／SchoolClassからLookupSetを返す。Search／Edit ViewはこのLookupSetを直接候補表示に使う。

原文根拠:
- [Web/Controllers/StudentsController.cs:39](../../srcs/CSharp_ASPNET/Web/Controllers/StudentsController.cs#L39)（39–45行、SHA `c927cdab41e0b5d2ce38eb0f88b3680b98ea1bfd1a42634637679cd8b23037b1`）
- [Infrastructure/WebStudentCoordinator.cs:22](../../srcs/CSharp_ASPNET/Infrastructure/WebStudentCoordinator.cs#L22)（22–22行、SHA `f57e213dc22534b74e357aa066e31e25e58bac5b4de1b3f5458502e06e049385`）
- [Core/SqlServerStudentService.cs:201](../../srcs/CSharp_ASPNET/Core/SqlServerStudentService.cs#L201)（201–222行、SHA `6a0004747afd6ed0a6fbc83cb7b936c4322d99ab5502e5ca0006efd887bac47a`）
- [Views/Students/Search.cshtml:28](../../srcs/CSharp_ASPNET/Views/Students/Search.cshtml#L28)（28–44行、SHA `11b3aa90f38759dfcaf7df2f3bc0448537ce0ac1ba1828d259bd07709a0842a9`）
- [Views/Students/Edit.cshtml:114](../../srcs/CSharp_ASPNET/Views/Students/Edit.cshtml#L114)（114–122行、SHA `83fef1494f78591fafe423ec577a12d129df46095bf7cd97959d5aca4dc2854f`）

### 新規・既存学生入口から編集モデルとスナップショット

- ID: `r-edit-load`
- 根拠種別: `observed-source`
- 参照目録: `f-maintain`, `o-create`, `o-update`, `o-query-detail`, `e-new`, `e-student`, `c-coordinator`, `c-input-mapping`, `c-web-state`, `c-student-service`, `d-student`, `d-core-contracts`, `d-web-contracts`, `r-lookups`

New／Editは共通Loadを呼び、Load→Coordinator.Editへ学生IDと復帰先を渡す。既存IDではGetAsyncがm\_studentを読みStudentDetailを返し、新規ではdetailを持たず候補を取得する。StudentSaveInput.FromはDetailとLookupSetからフォーム値を構成する。Loadはフォーム・詳細・復帰版をEditorSnapshotStore.Createへ保存し、その識別子とStudentEditPageModelをEdit Viewへ渡す。

原文根拠:
- [Web/Controllers/StudentsController.cs:29](../../srcs/CSharp_ASPNET/Web/Controllers/StudentsController.cs#L29)（29–31行、SHA `c927cdab41e0b5d2ce38eb0f88b3680b98ea1bfd1a42634637679cd8b23037b1`）
- [Infrastructure/WebStudentCoordinator.cs:22](../../srcs/CSharp_ASPNET/Infrastructure/WebStudentCoordinator.cs#L22)（22–22行、SHA `f57e213dc22534b74e357aa066e31e25e58bac5b4de1b3f5458502e06e049385`）
- [Core/SqlServerStudentService.cs:177](../../srcs/CSharp_ASPNET/Core/SqlServerStudentService.cs#L177)（177–200行、SHA `6a0004747afd6ed0a6fbc83cb7b936c4322d99ab5502e5ca0006efd887bac47a`）
- [Web/Inputs/StudentSaveInput.cs:44](../../srcs/CSharp_ASPNET/Web/Inputs/StudentSaveInput.cs#L44)（44–55行、SHA `586305468bf66346dfbb0f8ce0d9aedc76cde99169d51b673d8f41f9b61d1f38`）
- [Infrastructure/EditorSnapshotStore.cs:7](../../srcs/CSharp_ASPNET/Infrastructure/EditorSnapshotStore.cs#L7)（7–11行、SHA `26fe339679b0190a9e4da0cbf62a82decc28777b59d0b59f26a2119f42fa86ba`）
- [Web/Models/StudentEditPageModel.cs:3](../../srcs/CSharp_ASPNET/Web/Models/StudentEditPageModel.cs#L3)（3–14行、SHA `f8a5fdbed669dc69850395502d0992411733e6c17a7b0f36878d9dd39c96c1d2`）

### 作成・更新フォームからCore保存要求への接続

- ID: `r-save-input`
- 根拠種別: `observed-source`
- 参照目録: `f-maintain`, `o-create`, `o-update`, `e-new`, `e-student`, `c-input-mapping`, `c-identity`, `c-web-state`, `c-coordinator`, `c-student-service`, `d-web-contracts`, `d-core-contracts`, `r-edit-load`

Edit Viewの保存フォームは新規時create、既存時ID別updateを宛先とし、InputとSnapshotIdを送る。ControllerのCreate／Updateは共通Saveへ委譲する。SaveはFormGuard、権限、スナップショットと復帰先の照合を経てCoordinator.Saveを呼ぶ。CoordinatorはStudentSaveInput.ToRequestにIDを渡し、文字列表現のクラスID・期待版をIdParserで解析したSaveRequestをSaveAsyncへ渡す。

原文根拠:
- [Views/Students/Edit.cshtml:55](../../srcs/CSharp_ASPNET/Views/Students/Edit.cshtml#L55)（55–61行、SHA `83fef1494f78591fafe423ec577a12d129df46095bf7cd97959d5aca4dc2854f`）
- [Web/Controllers/StudentsController.cs:32](../../srcs/CSharp_ASPNET/Web/Controllers/StudentsController.cs#L32)（32–36行、SHA `c927cdab41e0b5d2ce38eb0f88b3680b98ea1bfd1a42634637679cd8b23037b1`）
- [Infrastructure/WebStudentCoordinator.cs:23](../../srcs/CSharp_ASPNET/Infrastructure/WebStudentCoordinator.cs#L23)（23–23行、SHA `f57e213dc22534b74e357aa066e31e25e58bac5b4de1b3f5458502e06e049385`）
- [Web/Inputs/StudentSaveInput.cs:34](../../srcs/CSharp_ASPNET/Web/Inputs/StudentSaveInput.cs#L34)（34–61行、SHA `586305468bf66346dfbb0f8ce0d9aedc76cde99169d51b673d8f41f9b61d1f38`）
- [Core/Contracts.cs:84](../../srcs/CSharp_ASPNET/Core/Contracts.cs#L84)（84–88行、SHA `2071c2d7824c4aacfeb8d87f1eb3905e6bb4eeca01de4f865a6f50440b226df4`）

### 保存要求から入力共通規則・学生書込・履歴への接続

- ID: `r-student-write`
- 根拠種別: `observed-source`
- 参照目録: `f-maintain`, `o-create`, `o-update`, `c-student-service`, `c-rules`, `c-db-boundary`, `d-student`, `d-code`, `d-category`, `d-class`, `d-audit`, `d-core-contracts`, `r-save-input`

SaveAsyncはCurrentUserと業務日を使いStudentNormalizer.NormalizeへStudentDraftを渡す。NormalizeはJapaneseDateServiceと各項目正規化を使いSQL列名をキーとするNormalizedStudentを返す。保存処理は既存m\_student、コード・分類・クラスと所属人数を読み、CheckRulesへ接続する。書込SQLはm\_studentのINSERTまたは期待版付きUPDATEで、同じconnection／transactionをAuditへ渡してt\_operation\_logを追加する。

原文根拠:
- [Core/StudentNormalizer.cs:119](../../srcs/CSharp_ASPNET/Core/StudentNormalizer.cs#L119)（119–160行、SHA `6064479d6b76a6a5e64f71f956f181b2a12adb4bb765868a27e3da2f887835cd`）
- [Core/SqlServerStudentService.cs:232](../../srcs/CSharp_ASPNET/Core/SqlServerStudentService.cs#L232)（232–278行、SHA `6a0004747afd6ed0a6fbc83cb7b936c4322d99ab5502e5ca0006efd887bac47a`）
- [Core/SqlServerStudentService.cs:298](../../srcs/CSharp_ASPNET/Core/SqlServerStudentService.cs#L298)（298–321行、SHA `6a0004747afd6ed0a6fbc83cb7b936c4322d99ab5502e5ca0006efd887bac47a`）
- [Core/SqlServerStudentService.cs:350](../../srcs/CSharp_ASPNET/Core/SqlServerStudentService.cs#L350)（350–397行、SHA `6a0004747afd6ed0a6fbc83cb7b936c4322d99ab5502e5ca0006efd887bac47a`）

### 重複候補読取・確認情報・再送フォームの接続

- ID: `r-duplicate-confirmation`
- 根拠種別: `observed-source`
- 参照目録: `o-duplicate`, `f-maintain`, `c-student-service`, `c-ui`, `d-student`, `d-class`, `d-code`, `d-confirmation`, `d-core-contracts`, `d-web-contracts`, `r-host-composition`, `r-save-input`

SaveAsyncの重複候補SQLはm\_studentを生年月日とname\_key／kana\_keyで検索し、RowSelectでクラス・学年・在籍・都道府県名称を結合する。候補のID・版と正規化入力からハッシュを作り、確認情報へ対応付ける。webTokens:trueではWebConfirmationsを使用し、falseのNative経路ではt\_confirmationを読取・追加・消費更新する。ControllerはSaveResultの確認情報をInput.DuplicateTokenへ戻し、Edit Viewの候補ダイアログから同じ保存フォームを再送する。

原文根拠:
- [Core/SqlServerStudentService.cs:90](../../srcs/CSharp_ASPNET/Core/SqlServerStudentService.cs#L90)（90–99行、SHA `6a0004747afd6ed0a6fbc83cb7b936c4322d99ab5502e5ca0006efd887bac47a`）
- [Core/SqlServerStudentService.cs:229](../../srcs/CSharp_ASPNET/Core/SqlServerStudentService.cs#L229)（229–230行、SHA `6a0004747afd6ed0a6fbc83cb7b936c4322d99ab5502e5ca0006efd887bac47a`）
- [Core/SqlServerStudentService.cs:274](../../srcs/CSharp_ASPNET/Core/SqlServerStudentService.cs#L274)（274–296行、SHA `6a0004747afd6ed0a6fbc83cb7b936c4322d99ab5502e5ca0006efd887bac47a`）
- [Core/SqlServerStudentService.cs:314](../../srcs/CSharp_ASPNET/Core/SqlServerStudentService.cs#L314)（314–348行、SHA `6a0004747afd6ed0a6fbc83cb7b936c4322d99ab5502e5ca0006efd887bac47a`）
- [Web/Controllers/StudentsController.cs:38](../../srcs/CSharp_ASPNET/Web/Controllers/StudentsController.cs#L38)（38–39行、SHA `c927cdab41e0b5d2ce38eb0f88b3680b98ea1bfd1a42634637679cd8b23037b1`）
- [Views/Students/Edit.cshtml:147](../../srcs/CSharp_ASPNET/Views/Students/Edit.cshtml#L147)（147–156行、SHA `83fef1494f78591fafe423ec577a12d129df46095bf7cd97959d5aca4dc2854f`）

### 保存結果から再表示・一時通知・検索復帰への接続

- ID: `r-save-output`
- 根拠種別: `observed-source`
- 参照目録: `f-maintain`, `e-search`, `c-web-state`, `c-coordinator`, `c-presentation`, `d-core-contracts`, `d-web-contracts`, `s-retained-helpers`, `r-student-write`, `r-duplicate-confirmation`, `r-search-state`

Controller.SaveはSaveResult.ErrorsをModelStateへ渡し、再表示では入力・読込時Detail・候補・結果をStudentEditPageModelへ組み込む。SavedではReturnAfterSaveへ渡し、FlashMessageStore.Putと303 Locationで/studentsへ接続する。GET /studentsはFlashMessageStore.Takeで通知を取り出す。復帰先がある場合の検索再取得はCoordinator.Resumeへ接続する。WebPresentation.SaveによるJSON化はこのMVC保存経路では呼ばれない。

原文根拠:
- [Web/Controllers/StudentsController.cs:8](../../srcs/CSharp_ASPNET/Web/Controllers/StudentsController.cs#L8)（8–11行、SHA `c927cdab41e0b5d2ce38eb0f88b3680b98ea1bfd1a42634637679cd8b23037b1`）
- [Web/Controllers/StudentsController.cs:34](../../srcs/CSharp_ASPNET/Web/Controllers/StudentsController.cs#L34)（34–44行、SHA `c927cdab41e0b5d2ce38eb0f88b3680b98ea1bfd1a42634637679cd8b23037b1`）
- [Infrastructure/FlashMessageStore.cs:4](../../srcs/CSharp_ASPNET/Infrastructure/FlashMessageStore.cs#L4)（4–9行、SHA `34ebbaf013e5d2fe9a1fd248ceb1bc2c738bad667bc8a9d571766c042a08b355`）
- [Infrastructure/WebStudentCoordinator.cs:19](../../srcs/CSharp_ASPNET/Infrastructure/WebStudentCoordinator.cs#L19)（19–19行、SHA `f57e213dc22534b74e357aa066e31e25e58bac5b4de1b3f5458502e06e049385`）

### 論理削除フォームから学生更新・監査への接続

- ID: `r-delete`
- 根拠種別: `observed-source`
- 参照目録: `f-maintain`, `o-delete`, `e-delete`, `c-identity`, `c-input-mapping`, `c-web-state`, `c-coordinator`, `c-student-service`, `d-student`, `d-audit`, `d-web-contracts`, `d-core-contracts`, `r-save-output`

Edit Viewの削除フォームは対象ID別deleteへ期待版・理由・確認値・復帰先・SnapshotIdを送る。Controllerはスナップショットを照合してCoordinator.Deleteへ渡す。Coordinatorは管理者判定と確認値を検査し、IdParserで版を解析してDeleteAsyncを呼ぶ。Coreはm\_studentの版を読み、削除属性をUPDATEしてAuditへ接続する。物理DELETEのSQLではなく、結果はSaveResultでControllerへ戻る。

原文根拠:
- [Views/Students/Edit.cshtml:158](../../srcs/CSharp_ASPNET/Views/Students/Edit.cshtml#L158)（158–171行、SHA `83fef1494f78591fafe423ec577a12d129df46095bf7cd97959d5aca4dc2854f`）
- [Web/Controllers/StudentsController.cs:43](../../srcs/CSharp_ASPNET/Web/Controllers/StudentsController.cs#L43)（43–44行、SHA `c927cdab41e0b5d2ce38eb0f88b3680b98ea1bfd1a42634637679cd8b23037b1`）
- [Infrastructure/WebStudentCoordinator.cs:24](../../srcs/CSharp_ASPNET/Infrastructure/WebStudentCoordinator.cs#L24)（24–24行、SHA `f57e213dc22534b74e357aa066e31e25e58bac5b4de1b3f5458502e06e049385`）
- [Core/SqlServerStudentService.cs:398](../../srcs/CSharp_ASPNET/Core/SqlServerStudentService.cs#L398)（398–423行、SHA `6a0004747afd6ed0a6fbc83cb7b936c4322d99ab5502e5ca0006efd887bac47a`）

### 編集取消・再読込・検索復帰の接続差

- ID: `r-reset`
- 根拠種別: `observed-source`
- 参照目録: `o-reset`, `e-reset`, `e-new`, `e-student`, `e-search`, `c-web-state`, `c-ui`, `c-student-service`, `r-edit-load`, `r-search-state`

POST /students/resetはEditorSnapshotStore.GetのOriginalをCopyしてEdit Viewへ戻し、候補だけをLookupAsyncで再取得する。最新情報再読込リンクはnewまたはID別GETへ接続し、Loadから詳細を再取得する。検索へ戻るリンクはcontextIdとReturnRevisionをGET /studentsへ渡す。site.jsはこれらのフォーム・リンクに変更破棄ダイアログを接続する。

原文根拠:
- [Web/Controllers/StudentsController.cs:29](../../srcs/CSharp_ASPNET/Web/Controllers/StudentsController.cs#L29)（29–31行、SHA `c927cdab41e0b5d2ce38eb0f88b3680b98ea1bfd1a42634637679cd8b23037b1`）
- [Web/Controllers/StudentsController.cs:41](../../srcs/CSharp_ASPNET/Web/Controllers/StudentsController.cs#L41)（41–41行、SHA `c927cdab41e0b5d2ce38eb0f88b3680b98ea1bfd1a42634637679cd8b23037b1`）
- [Views/Students/Edit.cshtml:139](../../srcs/CSharp_ASPNET/Views/Students/Edit.cshtml#L139)（139–146行、SHA `83fef1494f78591fafe423ec577a12d129df46095bf7cd97959d5aca4dc2854f`）
- [wwwroot/js/site.js:113](../../srcs/CSharp_ASPNET/wwwroot/js/site.js#L113)（113–152行、SHA `0a5a77d068907e383ae7000adcdf03fe613cf7be987eed5d872a6aa03bd931a1`）

### 共通LayoutとRazor属性からブラウザー補助への接続

- ID: `r-browser-ui`
- 根拠種別: `observed-source`
- 参照目録: `c-ui`, `c-navigation`, `f-login`, `f-query`, `f-maintain`, `o-duplicate`, `o-delete`, `o-reset`, `d-web-contracts`

\_ViewStartは\_Layoutを指定し、LayoutはCSS2資産とsite.jsを読み込む。Search Viewは\_MessagePanelと検索状態のdata属性、Edit Viewは原入力・業務日・候補属性と確認ダイアログを提供する。site.jsはこれらをDOMセレクタで読み、フォーム送信、重複理由のフォーム項目への転記、候補のローカル絞込み、人数表示、検索条件変更通知へ接続する。取得済みsite.jsに候補取得のHTTP呼出はない。

原文根拠:
- [Views/\_ViewStart.cshtml:1](../../srcs/CSharp_ASPNET/Views/_ViewStart.cshtml#L1)（1–1行、SHA `4aa2ee81e05f0966fa762ae93e5c22be6092d1c4d1de683e20a2c41cd749910f`）
- [Views/Shared/\_Layout.cshtml:1](../../srcs/CSharp_ASPNET/Views/Shared/_Layout.cshtml#L1)（1–5行、SHA `50d7c26a2d07903ecf0be1b131af2cb6bd2a02fa731380c69fd0cdd401a1f337`）
- [Views/Students/Search.cshtml:19](../../srcs/CSharp_ASPNET/Views/Students/Search.cshtml#L19)（19–23行、SHA `11b3aa90f38759dfcaf7df2f3bc0448537ce0ac1ba1828d259bd07709a0842a9`）
- [Views/Students/Edit.cshtml:55](../../srcs/CSharp_ASPNET/Views/Students/Edit.cshtml#L55)（55–61行、SHA `83fef1494f78591fafe423ec577a12d129df46095bf7cd97959d5aca4dc2854f`）
- [wwwroot/js/site.js:1](../../srcs/CSharp_ASPNET/wwwroot/js/site.js#L1)（1–231行、SHA `0a5a77d068907e383ae7000adcdf03fe613cf7be987eed5d872a6aa03bd931a1`）

### 学生・マスタ処理からDBプロファイル変換への接続

- ID: `r-db-profile-boundary`
- 根拠種別: `observed-source`
- 参照目録: `c-db-boundary`, `c-student-service`, `c-master-service`, `d-core-contracts`, `d-student`, `d-class`, `d-code`, `d-audit`, `r-host-composition`

学生サービスのconstructorとマスタサービスのOpenはSharedAccessSchema.ConnectionStringを使い、接続をプロファイル付きでRegisterする。両サービスのSQLパラメータは共通Param→ConvertParameterへ接続する。SharedAccessではBigInt、Date、DateTimeOffset、UniqueIdentifier、VarCharの送信表現を変換し、読取側はReadDate／ReadTimestamp／ReadValueでCore表現へ戻す。マスタサービスはusing staticで学生サービスのSQL補助を参照する。

原文根拠:
- [Core/SqlServerStudentService.cs:42](../../srcs/CSharp_ASPNET/Core/SqlServerStudentService.cs#L42)（42–89行、SHA `6a0004747afd6ed0a6fbc83cb7b936c4322d99ab5502e5ca0006efd887bac47a`）
- [Core/SqlServerStudentService.cs:429](../../srcs/CSharp_ASPNET/Core/SqlServerStudentService.cs#L429)（429–489行、SHA `6a0004747afd6ed0a6fbc83cb7b936c4322d99ab5502e5ca0006efd887bac47a`）
- [Core/MasterMaintenanceService.cs:5](../../srcs/CSharp_ASPNET/Core/MasterMaintenanceService.cs#L5)（5–5行、SHA `752f17d77f8d7dae4af203676a40f402e1aaaed2024a4e2360396502c010cfb8`）
- [Core/MasterMaintenanceService.cs:19](../../srcs/CSharp_ASPNET/Core/MasterMaintenanceService.cs#L19)（19–35行、SHA `752f17d77f8d7dae4af203676a40f402e1aaaed2024a4e2360396502c010cfb8`）

### 学生・マスタ書込から共通ゲートへの逆利用照合

- ID: `r-write-gate`
- 根拠種別: `observed-source`
- 参照目録: `c-db-boundary`, `c-student-service`, `c-master-service`, `d-write-guard`, `d-code`, `s-db-deploy`, `r-db-profile-boundary`

学生SaveAsync／DeleteAsyncとマスタSaveClassAsync／SaveCodeAsyncはいずれも書込トランザクションから共通Gateを呼ぶ。GateはSharedAccess接続ではt\_write\_guardのguard\_id=1をUPDATEし、Nativeではsys.sp\_getapplockを呼ぶ。Native seedも同じリソース名のapplockを使用する。共有DDLはt\_write\_guardを定義するが、その原文中に必要行のINSERTはなく、初期行の実在は確認できない。

原文根拠:
- [Core/SqlServerStudentService.cs:100](../../srcs/CSharp_ASPNET/Core/SqlServerStudentService.cs#L100)（100–115行、SHA `6a0004747afd6ed0a6fbc83cb7b936c4322d99ab5502e5ca0006efd887bac47a`）
- [Core/SqlServerStudentService.cs:247](../../srcs/CSharp_ASPNET/Core/SqlServerStudentService.cs#L247)（247–250行、SHA `6a0004747afd6ed0a6fbc83cb7b936c4322d99ab5502e5ca0006efd887bac47a`）
- [Core/SqlServerStudentService.cs:405](../../srcs/CSharp_ASPNET/Core/SqlServerStudentService.cs#L405)（405–409行、SHA `6a0004747afd6ed0a6fbc83cb7b936c4322d99ab5502e5ca0006efd887bac47a`）
- [Core/MasterMaintenanceService.cs:44](../../srcs/CSharp_ASPNET/Core/MasterMaintenanceService.cs#L44)（44–48行、SHA `752f17d77f8d7dae4af203676a40f402e1aaaed2024a4e2360396502c010cfb8`）
- [Core/MasterMaintenanceService.cs:93](../../srcs/CSharp_ASPNET/Core/MasterMaintenanceService.cs#L93)（93–96行、SHA `752f17d77f8d7dae4af203676a40f402e1aaaed2024a4e2360396502c010cfb8`）
- [database/002\_seed.sql:2](../../srcs/CSharp_ASPNET/database/002_seed.sql#L2)（2–6行、SHA `b40e408a8c98b66b045adc05dca5eb15cc53faea5d700afc30e7e741d234c431`）
- [database/shared\-access/001\-schema.sql:306](../../srcs/CSharp_ASPNET/database/shared-access/001-schema.sql#L306)（306–328行、SHA `d33c729896e7bd0dc16f94421de296af0099d7660d58f596b91b372bd383229f`）

### 保守CLI入力からクラス・コード保守への接続

- ID: `r-maintenance-cli`
- 根拠種別: `observed-source`
- 参照目録: `e-maint`, `f-class`, `f-code`, `c-master-service`, `d-maint-contracts`, `d-core-contracts`

StudentMaintenanceはclass／codeセレクタ、JSONファイル、接続・プロファイルの環境設定を入力として参照する。JSONをClassChangeまたはCodeChangeへ逆直列化し、MasterMaintenanceService.SaveClassAsyncまたはSaveCodeAsyncへ渡す。返却MaintenanceResultはJSONで標準出力へ、検証・権限等の例外は標準エラーと終了コードへ対応付ける。入力名のapprovedは承認取得の証拠ではない。

原文根拠:
- [maintenance/Program.cs:4](../../srcs/CSharp_ASPNET/maintenance/Program.cs#L4)（4–19行、SHA `77c9abf66a53783f1dfdb5f25842be627a1d3ae46b7f03d1f7879ca1c1474588`）
- [Core/MasterMaintenanceService.cs:9](../../srcs/CSharp_ASPNET/Core/MasterMaintenanceService.cs#L9)（9–15行、SHA `752f17d77f8d7dae4af203676a40f402e1aaaed2024a4e2360396502c010cfb8`）

### マスタ保守からDB接続主体・役割への接続

- ID: `r-master-authorization`
- 根拠種別: `observed-source`
- 参照目録: `f-class`, `f-code`, `c-master-service`, `c-rules`, `d-app-role`, `s-db-deploy`, `r-maintenance-cli`

マスタ両保存メソッドはOpenを呼ぶ。OpenはNativeではORIGINAL\_LOGINとstudent\_admin所属、SharedAccessではsysadmin／db\_ownerまたはORIGINAL\_LOGINに一致するt\_app\_roleのAdminをSQLで照合する。SQLから得る主体をStudentNormalizer.Textで整え、保存・監査のactorへ渡す。WebのCurrentUser生成とは別の接続主体由来の経路である。

原文根拠:
- [Core/MasterMaintenanceService.cs:19](../../srcs/CSharp_ASPNET/Core/MasterMaintenanceService.cs#L19)（19–35行、SHA `752f17d77f8d7dae4af203676a40f402e1aaaed2024a4e2360396502c010cfb8`）
- [Core/MasterMaintenanceService.cs:44](../../srcs/CSharp_ASPNET/Core/MasterMaintenanceService.cs#L44)（44–46行、SHA `752f17d77f8d7dae4af203676a40f402e1aaaed2024a4e2360396502c010cfb8`）
- [Core/MasterMaintenanceService.cs:93](../../srcs/CSharp_ASPNET/Core/MasterMaintenanceService.cs#L93)（93–94行、SHA `752f17d77f8d7dae4af203676a40f402e1aaaed2024a4e2360396502c010cfb8`）

### クラス保守から参照照合・保存・監査への接続

- ID: `r-class-maintenance`
- 根拠種別: `observed-source`
- 参照目録: `f-class`, `c-master-service`, `c-rules`, `c-db-boundary`, `d-maint-contracts`, `d-class`, `d-student`, `d-code`, `d-category`, `d-audit`, `r-maintenance-cli`, `r-master-authorization`

SaveClassAsyncはClassChangeを正規化・日付変換し、m\_classの既存値・版、m\_studentの参照と所属人数、GRADEのm\_codeとm\_code\_category、同名m\_classを読む。保存補助Saveへm\_class／class\_idと値・型辞書を渡してINSERTまたはUPDATEし、Logへ対象キー・変更列・版・actorを渡す。操作種別はAuditOperation.ForMasterの返値を使用する。

原文根拠:
- [Core/MasterMaintenanceService.cs:36](../../srcs/CSharp_ASPNET/Core/MasterMaintenanceService.cs#L36)（36–84行、SHA `752f17d77f8d7dae4af203676a40f402e1aaaed2024a4e2360396502c010cfb8`）
- [Core/MasterMaintenanceService.cs:130](../../srcs/CSharp_ASPNET/Core/MasterMaintenanceService.cs#L130)（130–142行、SHA `752f17d77f8d7dae4af203676a40f402e1aaaed2024a4e2360396502c010cfb8`）
- [Core/AuditOperation.cs:4](../../srcs/CSharp_ASPNET/Core/AuditOperation.cs#L4)（4–8行、SHA `ad154004378612be2f2f80036edf63a2fb2fbfc4cf71858348044649dc2bb5e8`）

### コード保守から分類照合・保存・監査への接続

- ID: `r-code-maintenance`
- 根拠種別: `observed-source`
- 参照目録: `f-code`, `c-master-service`, `c-rules`, `c-db-boundary`, `d-maint-contracts`, `d-category`, `d-code`, `d-audit`, `r-maintenance-cli`, `r-master-authorization`

SaveCodeAsyncはCodeChangeを受け、m\_code\_categoryからcode\_lengthとallow\_addを読み、その長さをStudentNormalizer.Codeへ渡す。分類とコード値でm\_codeの既存値・版・保護情報を読み、m\_codeへINSERTまたは期待版付きUPDATEを組み立てる。Logは分類:コード値を対象キーとしてt\_operation\_logへ追加し、AuditOperation.ForMasterが操作種別を供給する。分類表への書込呼出はこの経路にない。

原文根拠:
- [Core/MasterMaintenanceService.cs:85](../../srcs/CSharp_ASPNET/Core/MasterMaintenanceService.cs#L85)（85–128行、SHA `752f17d77f8d7dae4af203676a40f402e1aaaed2024a4e2360396502c010cfb8`）
- [Core/MasterMaintenanceService.cs:138](../../srcs/CSharp_ASPNET/Core/MasterMaintenanceService.cs#L138)（138–142行、SHA `752f17d77f8d7dae4af203676a40f402e1aaaed2024a4e2360396502c010cfb8`）
- [Core/AuditOperation.cs:6](../../srcs/CSharp_ASPNET/Core/AuditOperation.cs#L6)（6–7行、SHA `ad154004378612be2f2f80036edf63a2fb2fbfc4cf71858348044649dc2bb5e8`）

### 両DDLの外部キーと履歴対象の区別

- ID: `r-data-references`
- 根拠種別: `observed-source`
- 参照目録: `d-student`, `d-class`, `d-code`, `d-category`, `d-audit`, `r-student-write`, `r-class-maintenance`, `r-code-maintenance`

Native／SharedAccessの双方のDDLは、m\_code.category\_id→m\_code\_category、m\_classの学年分類・値→m\_code、m\_student.class\_id→m\_class、学生の性別・都道府県・在籍・続柄の分類・値→m\_codeという7外部キーを宣言する。t\_operation\_logの対象表・キーは学生Audit／マスタLogが値として書く関係であり、このDDL群では対象業務表への外部キーではない。

原文根拠:
- [database/001\_schema.sql:137](../../srcs/CSharp_ASPNET/database/001_schema.sql#L137)（137–154行、SHA `32e87af4b5804c73ba9b0efa705a2050388b5105b3d64cceecd8c7e585fc1dc9`）
- [database/001\_schema.sql:187](../../srcs/CSharp_ASPNET/database/001_schema.sql#L187)（187–196行、SHA `32e87af4b5804c73ba9b0efa705a2050388b5105b3d64cceecd8c7e585fc1dc9`）
- [database/shared\-access/001\-schema.sql:314](../../srcs/CSharp_ASPNET/database/shared-access/001-schema.sql#L314)（314–328行、SHA `d33c729896e7bd0dc16f94421de296af0099d7660d58f596b91b372bd383229f`）
- [Core/SqlServerStudentService.cs:391](../../srcs/CSharp_ASPNET/Core/SqlServerStudentService.cs#L391)（391–397行、SHA `6a0004747afd6ed0a6fbc83cb7b936c4322d99ab5502e5ca0006efd887bac47a`）
- [Core/MasterMaintenanceService.cs:138](../../srcs/CSharp_ASPNET/Core/MasterMaintenanceService.cs#L138)（138–142行、SHA `752f17d77f8d7dae4af203676a40f402e1aaaed2024a4e2360396502c010cfb8`）

### Webメモリー状態とNative状態表の接続境界

- ID: `r-state-storage-separation`
- 根拠種別: `observed-source`
- 参照目録: `c-web-state`, `c-student-service`, `d-runtime-state`, `d-confirmation`, `s-db-deploy`, `r-host-composition`, `r-duplicate-confirmation`

SearchContextStore、EditorSnapshotStore、FlashMessageStoreは自身のConcurrentDictionaryを保存先に持つ。Web登録のwebTokens:trueもCoreのWebConfirmationsを選ぶ。取得済みストア実装からt\_runtime\_stateへのSQL接続はなく、t\_confirmationはCoreの非Web確認経路に存在する。003権限SQLも両状態表へのDMLを宣言していない。表の存在を現行Webストアの永続化関係へ置き換えない。

原文根拠:
- [Infrastructure/SearchContextStore.cs:10](../../srcs/CSharp_ASPNET/Infrastructure/SearchContextStore.cs#L10)（10–15行、SHA `2418cabe8c3878cd7528e2280aa689642d55dd4685fef017e78046cf4ae5e04a`）
- [Infrastructure/EditorSnapshotStore.cs:7](../../srcs/CSharp_ASPNET/Infrastructure/EditorSnapshotStore.cs#L7)（7–11行、SHA `26fe339679b0190a9e4da0cbf62a82decc28777b59d0b59f26a2119f42fa86ba`）
- [Infrastructure/FlashMessageStore.cs:6](../../srcs/CSharp_ASPNET/Infrastructure/FlashMessageStore.cs#L6)（6–9行、SHA `34ebbaf013e5d2fe9a1fd248ceb1bc2c738bad667bc8a9d571766c042a08b355`）
- [Infrastructure/WebHostSetup.cs:25](../../srcs/CSharp_ASPNET/Infrastructure/WebHostSetup.cs#L25)（25–25行、SHA `319d64cab66a244193ab3d33c01e55b2638928469db4f6548183e818f1d3ee10`）
- [Core/SqlServerStudentService.cs:336](../../srcs/CSharp_ASPNET/Core/SqlServerStudentService.cs#L336)（336–348行、SHA `6a0004747afd6ed0a6fbc83cb7b936c4322d99ab5502e5ca0006efd887bac47a`）
- [database/003\_web\_permissions.sql:8](../../srcs/CSharp_ASPNET/database/003_web_permissions.sql#L8)（8–24行、SHA `78d487c3ed3cf6aa5af35687bf98f42c00ff0c71397d9986b2bc77ed49957f5e`）

### Native直接DML登録と別EXEC専用入口注記

- ID: `r-native-permissions-and-unresolved-entrance`
- 根拠種別: `observed-source`
- 参照目録: `c-student-service`, `s-db-deploy`, `s-build`, `d-student`, `d-audit`, `r-host-composition`, `r-student-write`

現行Web登録はSqlServerStudentServiceを直接生成し、その本文は業務表へのSELECT／INSERT／UPDATEを組み立てる。003はstudent\_viewer→student\_staff→student\_adminの継承と、そのDMLに対応する権限を宣言する。一方、Core冒頭とDDL末尾の別EXEC専用入口／student\_apiは注記であり、取得済み登録やProjectReferenceからその実装への接続を確認できない。U\-REL\-001を未解決として保持する。

原文根拠:
- [Infrastructure/WebHostSetup.cs:25](../../srcs/CSharp_ASPNET/Infrastructure/WebHostSetup.cs#L25)（25–25行、SHA `319d64cab66a244193ab3d33c01e55b2638928469db4f6548183e818f1d3ee10`）
- [Core/SqlServerStudentService.cs:12](../../srcs/CSharp_ASPNET/Core/SqlServerStudentService.cs#L12)（12–14行、SHA `6a0004747afd6ed0a6fbc83cb7b936c4322d99ab5502e5ca0006efd887bac47a`）
- [Core/SqlServerStudentService.cs:300](../../srcs/CSharp_ASPNET/Core/SqlServerStudentService.cs#L300)（300–308行、SHA `6a0004747afd6ed0a6fbc83cb7b936c4322d99ab5502e5ca0006efd887bac47a`）
- [database/003\_web\_permissions.sql:8](../../srcs/CSharp_ASPNET/database/003_web_permissions.sql#L8)（8–24行、SHA `78d487c3ed3cf6aa5af35687bf98f42c00ff0c71397d9986b2bc77ed49957f5e`）
- [database/001\_schema.sql:213](../../srcs/CSharp_ASPNET/database/001_schema.sql#L213)（213–218行、SHA `32e87af4b5804c73ba9b0efa705a2050388b5105b3d64cceecd8c7e585fc1dc9`）
- [StudentManagement.Web.csproj:1](../../srcs/CSharp_ASPNET/StudentManagement.Web.csproj#L1)（1–7行、SHA `a82e58b4b27e6c808f2bdb24397cf679f429b2c7e8234dfef252eb5f3165badf`）

### 残存候補・JSON補助の内部接続と未確認呼出元

- ID: `r-retained-helpers`
- 根拠種別: `observed-source`
- 参照目録: `s-retained-helpers`, `e-retired`, `c-coordinator`, `c-presentation`, `c-student-service`, `d-web-contracts`, `r-lookups`, `r-save-output`

取得済み全原文の呼出・登録を逆照合した範囲でStrictJson.Read、Coordinator.Options、WebPresentation.Saveへの外部静的呼出は確認できない。Options内部にはGetAsync／LookupAsync→WebPresentation.Lookupsの連鎖、Save内部にはSaveMessage／Errorsの連鎖がある。登録済みPOST /students/optionsの定義先はRetiredSearchOptionsで、本文はNotFoundのみである。未確認の動的・外部利用を非到達と断定しない。

原文根拠:
- [Infrastructure/StrictJson.cs:4](../../srcs/CSharp_ASPNET/Infrastructure/StrictJson.cs#L4)（4–15行、SHA `2ece5d35b140cdded0ad30804e5f3ee431e7fb16f2e066df56fc968abb22a825`）
- [Infrastructure/WebStudentCoordinator.cs:21](../../srcs/CSharp_ASPNET/Infrastructure/WebStudentCoordinator.cs#L21)（21–21行、SHA `f57e213dc22534b74e357aa066e31e25e58bac5b4de1b3f5458502e06e049385`）
- [Infrastructure/WebPresentation.cs:8](../../srcs/CSharp_ASPNET/Infrastructure/WebPresentation.cs#L8)（8–30行、SHA `23800e7f88e643c952a8617f5382e43c5c0d4ffa543c0c1f24e333312ea213f3`）
- [Web/Controllers/StudentsController.cs:5](../../srcs/CSharp_ASPNET/Web/Controllers/StudentsController.cs#L5)（5–46行、SHA `c927cdab41e0b5d2ce38eb0f88b3680b98ea1bfd1a42634637679cd8b23037b1`）
- [Program.cs:3](../../srcs/CSharp_ASPNET/Program.cs#L3)（3–7行、SHA `f55ce879e78e94b9144c1a9ed68fc6cfea01d45e91efc5dbbdf025d906fc1f85`）

### 評価用セッションと生存確認入口の出力

- ID: `r-support-http-entries`
- 根拠種別: `observed-source`
- 参照目録: `e-evaluation`, `e-health`, `c-auth`, `c-web-pipeline`, `d-core-contracts`, `r-host-composition`

WebHostSetup.UseはPOST /\_evaluation/sessionとGET /healthを登録する。評価入口はDevelopmentおよびサーバー設定による照合条件を持ち、設定主体・役割からClaimを作ってCookie SignInAsyncへ接続する。healthは固定のrunning／database=not\-testedを返し、IStudentServiceやSQL接続を呼ばない。これらは学生業務の検索・保存入口とは別の支援経路である。

原文根拠:
- [Infrastructure/WebHostSetup.cs:34](../../srcs/CSharp_ASPNET/Infrastructure/WebHostSetup.cs#L34)（34–36行、SHA `319d64cab66a244193ab3d33c01e55b2638928469db4f6548183e818f1d3ee10`）
- [appsettings.json:8](../../srcs/CSharp_ASPNET/appsettings.json#L8)（8–12行、SHA `9a6c516728adc9a5b452a5d6a00296a3b897e6e93e0ff8870efa700edf5cdf25`）

### 配置検査入口から学生サービスへの追加呼出元

- ID: `r-smoke-reverse-use`
- 根拠種別: `observed-source`
- 参照目録: `e-smoke`, `s-verification`, `c-student-service`, `d-core-contracts`, `r-lookups`, `r-search-data`

DatabaseSmokeは明示環境設定を入力にSqlServerStudentServiceを直接生成する。指定はwebTokens:true、DBプロファイルは省略によるNativeであり、WebのDIを経由しない。既定LookupAsyncと既定SearchCriteriaによるSearchAsyncを呼び、コード・クラス・学生件数等を条件照合して標準出力または例外へ接続する。ソースのPASS文字列は実行結果ではない。

原文根拠:
- [deployment/DatabaseSmoke/Program.cs:3](../../srcs/CSharp_ASPNET/deployment/DatabaseSmoke/Program.cs#L3)（3–9行、SHA `74c6da0ca7493102bcae82bdefa5001162d02d684aea0e031ebf3902e666e537`）
- [Core/SqlServerStudentService.cs:42](../../srcs/CSharp_ASPNET/Core/SqlServerStudentService.cs#L42)（42–48行、SHA `6a0004747afd6ed0a6fbc83cb7b936c4322d99ab5502e5ca0006efd887bac47a`）

### Native導入スクリプトからDDL・seed・権限・検査への接続

- ID: `r-native-deployment`
- 根拠種別: `observed-source`
- 参照目録: `s-db-deploy`, `dep-platform-tools`, `d-student`, `d-class`, `d-code`, `d-category`, `d-audit`, `d-confirmation`, `d-runtime-state`

Deploy\-Database.ps1はInstall／Verify／BindPrincipalの入口を持ち、Invoke\-LocalSqlからsqlcmdへSQLファイルまたはSQL文字列を渡す。Installの宣言経路は001→002→003と入力ハッシュ記録で、その後004を参照する。002はm\_code\_category／m\_codeへ初期値を追加し、004は構造・キー・初期値・権限をSELECTする。BindPrincipalは選択されたアプリ役割をDB役割へ対応付ける。配備や検査の実行は認定しない。

原文根拠:
- [database/Deploy\-Database.ps1:1](../../srcs/CSharp_ASPNET/database/Deploy-Database.ps1#L1)（1–25行、SHA `61b5501f39d1a7013c79b0b5c8b703dcdb15753e8cfa5a92b2d2194654c2a2c7`）
- [database/Deploy\-Database.ps1:67](../../srcs/CSharp_ASPNET/database/Deploy-Database.ps1#L67)（67–150行、SHA `61b5501f39d1a7013c79b0b5c8b703dcdb15753e8cfa5a92b2d2194654c2a2c7`）
- [database/002\_seed.sql:85](../../srcs/CSharp_ASPNET/database/002_seed.sql#L85)（85–93行、SHA `b40e408a8c98b66b045adc05dca5eb15cc53faea5d700afc30e7e741d234c431`）
- [database/004\_verify\_deployment.sql:1](../../srcs/CSharp_ASPNET/database/004_verify_deployment.sql#L1)（1–25行、SHA `dfbe2d7ea7fadf9fc635e38349b649efbdab826df0cc2488e698e886fa0d0b36`）

### Azure配置支援のスクリプト間・設定先の接続

- ID: `r-azure-support`
- 根拠種別: `observed-source`
- 参照目録: `s-azure-deploy`, `s-verification`, `e-hash`, `e-smoke`, `c-auth`, `s-db-deploy`, `dep-platform-tools`, `r-smoke-reverse-use`, `r-local-auth`

Configure\-AzureDatabaseはInitialize\-AzureDatabase.pyとDatabaseSmokeを呼ぶコードを持ち、StudentDbアプリ設定へ接続設定を渡す。初期化Pythonは取得済み001／002を読み、コード参照列幅・seed照合順序を適配したSQLと003を処理対象にする。Configure\-AzureWebLoginはLoginPasswordHashを呼び、その出力をLocalLogin設定へ対応付ける。PublishはWebプロジェクトをpublishしAzure配置へ渡す。参照先の私有状態・資格情報内容は取得していない。

原文根拠:
- [deployment/Configure\-AzureDatabase.ps1:24](../../srcs/CSharp_ASPNET/deployment/Configure-AzureDatabase.ps1#L24)（24–40行、SHA `681f8c7dbab943ae8af5b3c554cf4c6ccb84e3bbac5dd711eb4962283e78f406`）
- [deployment/Initialize\-AzureDatabase.py:12](../../srcs/CSharp_ASPNET/deployment/Initialize-AzureDatabase.py#L12)（12–30行、SHA `630596b7c0d590fffaebeea5be55e4993b40bd2fe149bc4aae233eb5ecbd93e5`）
- [deployment/Initialize\-AzureDatabase.py:127](../../srcs/CSharp_ASPNET/deployment/Initialize-AzureDatabase.py#L127)（127–145行、SHA `630596b7c0d590fffaebeea5be55e4993b40bd2fe149bc4aae233eb5ecbd93e5`）
- [deployment/Configure\-AzureWebLogin.ps1:16](../../srcs/CSharp_ASPNET/deployment/Configure-AzureWebLogin.ps1#L16)（16–28行、SHA `591014c052acb3fe31c765ce69df2fbcb0be0c2301ab091693cd7260aaca1740`）
- [deployment/LoginPasswordHash/Program.cs:4](../../srcs/CSharp_ASPNET/deployment/LoginPasswordHash/Program.cs#L4)（4–9行、SHA `2e17ea8038733fba3c18cfc982d0a249472e862942f40bd8bfc071e6d16d8556`）
- [deployment/Publish\-FreeAzure.ps1:27](../../srcs/CSharp_ASPNET/deployment/Publish-FreeAzure.ps1#L27)（27–40行、SHA `3fe6e01a9e1939d04fe517bbdb0641ef9d4553457d139bb66f7e329efa587d47`）

### ビルド設定・出力管理・生成器の宣言接続

- ID: `r-build-and-generator`
- 根拠種別: `observed-source`
- 参照目録: `s-build`, `s-generator`, `s-db-deploy`, `dep-platform-tools`, `d-code`, `d-category`, `r-project-boundaries`

tools/build.pyはbuild\_config.jsonとbuild\_paths.OutputPathsを参照し、設定されたsolution・main・testsから外部コマンドを構成する。Directory.Build.propsは中間・出力先と除外を宣言する。database/generate.mjsは外部仕様パスを入力名として参照し、001\_schema.sql・002\_seed.sqlと生成記録を出力するコードを持つ。取得済みbuild.pyの通常経路に生成器呼出はない。外部仕様と省略テストの本文は取得せず、これらの参照だけから実行や成功を推定しない。

原文根拠:
- [tools/build.py:1](../../srcs/CSharp_ASPNET/tools/build.py#L1)（1–14行、SHA `f6c229827cfaa877194f542571560ea84852f26b56b3ae93d0f9919f8a539123`）
- [tools/build.py:65](../../srcs/CSharp_ASPNET/tools/build.py#L65)（65–86行、SHA `f6c229827cfaa877194f542571560ea84852f26b56b3ae93d0f9919f8a539123`）
- [tools/build\_config.json:1](../../srcs/CSharp_ASPNET/tools/build_config.json#L1)（1–19行、SHA `71d33ef84a65fc89f2cb321b4d464289aeaada46534ebb634a11a20d5eda8008`）
- [Directory.Build.props:3](../../srcs/CSharp_ASPNET/Directory.Build.props#L3)（3–13行、SHA `d81943ab416bf06d4af3b83700b8dff2cd26863506e242679b7c4908b57d23f9`）
- [database/generate.mjs:6](../../srcs/CSharp_ASPNET/database/generate.mjs#L6)（6–23行、SHA `e72bb17e1d9c772d802726048f3a75543b92008dacafc5546cb28ba3f9b49167`）
- [database/generate.mjs:81](../../srcs/CSharp_ASPNET/database/generate.mjs#L81)（81–110行、SHA `e72bb17e1d9c772d802726048f3a75543b92008dacafc5546cb28ba3f9b49167`）

### 配置検証ソースの呼出対象と現行Viewの接続不一致

- ID: `r-verification-targets`
- 根拠種別: `observed-source`
- 参照目録: `s-verification`, `s-azure-deploy`, `e-login`, `e-search`, `e-logout`, `e-evaluation`, `c-ui`, `r-search-input`

Verify\-AzureRemoteDatabaseはAzure worker上で設定接続を参照する読取SQLを構成する。Verify\-AzureWebLoginは/login、/students、検索POST、/logout、評価入口を対象にする一方、学生検索画面で\#SRC\-009 optionを要求する。現行Search Viewの条件領域にSRC\-009定義はなく、このセレクタを現行画面へ結び付けられない。実配置版が取得版と一致するかは未確認で、検証ソースのassertやPASS出力を結果として採用しない。

原文根拠:
- [deployment/Verify\-AzureRemoteDatabase.py:10](../../srcs/CSharp_ASPNET/deployment/Verify-AzureRemoteDatabase.py#L10)（10–35行、SHA `7654bd1b540f1df22476ebaa46f6d945b0437a1696c2504aa1a81e4ac39383d6`）
- [deployment/Verify\-AzureWebLogin.py:48](../../srcs/CSharp_ASPNET/deployment/Verify-AzureWebLogin.py#L48)（48–77行、SHA `f5eafc6a628504172020e74c7ffe1470c570c2fad252235f3e8b451f31cfa09b`）
- [Views/Students/Search.cshtml:20](../../srcs/CSharp_ASPNET/Views/Students/Search.cshtml#L20)（20–46行、SHA `11b3aa90f38759dfcaf7df2f3bc0448537ce0ac1ba1828d259bd07709a0842a9`）

## 候補に記録された未知

作者の原記録を保持する。後続工程の完了や独立検証による解決を示さない。

```json
[
  {
    "blocksRequirements": [],
    "id": "U-REL-001",
    "question": "Nativeの「別EXEC専用DB入口」注記に対応するstudent_api実装は、現行登録とは別に存在・利用されるのか。",
    "relatedRequirements": [
      "catalog",
      "relationships",
      "behavior"
    ],
    "scopeReason": "現行登録から直接DMLサービスへの接続は原文で抽出した。別入口は注記を超える実装・登録を確認できず、その存在を創作しない。現行静的関係を整理できるため既存の非阻止扱いを保持するが、追加入口の実在・利用は解決していない。"
  },
  {
    "blocksRequirements": [],
    "id": "U-REL-002",
    "question": "StrictJson.Read、WebStudentCoordinator.Options、WebPresentation.Saveには取得済み静的呼出以外の動的・外部利用があるか。",
    "relatedRequirements": [
      "relationships",
      "behavior"
    ],
    "scopeReason": "呼出元・ルート・登録・View・ブラウザー処理を逆照合し、残存補助の内部連鎖と現行options入口のNotFoundを区別した。静的呼出が見つからないことは実行時非到達の証明ではなく、動的・外部利用は未確認のまま保持する。"
  },
  {
    "blocksRequirements": [],
    "id": "U-BEH-001",
    "question": "実際の起動・配備で選択されるDB／認証プロファイル、配備スキーマと宣言DDLの一致、および検査の実行結果はどうなっているか。",
    "relatedRequirements": [
      "relationships",
      "behavior"
    ],
    "scopeReason": "設定と条件付き接続をソースから区別したが、実配備・実DB・省略されたbuild／tests・私有配備状態は確認していない。共有DDLの由来記録や文書の過去結果は今回の実行証拠ではない。元の静的解析を妨げないという既存判断を保持し、実行成功を推定しない。"
  },
  {
    "blocksRequirements": [
      "relationships"
    ],
    "id": "followup:392c5fcdc4c50bc6caf3e635e02298a48e882d71960704b52ceae80b92455292",
    "question": "検証済み目録を基に、Web／CLI入口、登録されたサービス、状態ストア、SQL対象の接続を原文で確認し、U-REL-001とU-REL-002の観測限界を保持する。",
    "relatedRequirements": [
      "relationships"
    ],
    "scopeReason": "今回、relationships所有の候補関係と原文根拠を抽出した。既存事項は独立レビューによる解決まで阻止とされており、本抽出担当はその決定の解除・レコード採用を行わない。ホスト側の独立確認が未完了のため既存ブロッカーを保持する。"
  },
  {
    "blocksRequirements": [
      "behavior"
    ],
    "id": "followup:e9209317f2d48633799d8225642ac11fe750b1316f04c8e2a4041c7561ffa9be",
    "question": "関係確認後、認証・検索状態・保存確認・論理削除・マスタ保守の条件、状態、異常とトランザクションを必要範囲で調べ、U-BEH-001の実行未確認を成功扱いせず保持する。",
    "relatedRequirements": [
      "behavior"
    ],
    "scopeReason": "behaviorは元の目標義務として未完了である。今回の関係抽出では呼出の適用条件と入出力を確認したが、behavior所有の条件・状態・順序・異常・トランザクション検証を実施または完了扱いにしていない。担当外であることを理由に元のブロッカーを消去しない。"
  },
  {
    "blocksRequirements": [],
    "id": "U-REL-003",
    "question": "Verify-AzureWebLogin.pyが要求する#SRC-009はどの配置版の画面を対象とし、現行Search.cshtmlとの不一致はどのように扱われているか。",
    "relatedRequirements": [
      "relationships",
      "behavior"
    ],
    "scopeReason": "取得済み検証ソースのセレクタと現行Viewの接続不一致を観測した。実配置版の内容やこの検証の実行結果は未確認である。不一致を明示して静的関係を記録できるため全体の追加ブロッカーとはしないが、現行画面への検証適合や成功は認定しない。"
  }
]
```

## 候補の補査要求とcoverage

```json
{
  "followups": [
    {
      "paths": [
        "Core/SqlServerStudentService.cs",
        "Infrastructure/WebHostSetup.cs",
        "StudentManagement.Web.csproj",
        "database/001_schema.sql",
        "database/003_web_permissions.sql"
      ],
      "question": "U-REL-001について、注記にあるstudent_api／別EXEC専用DB入口に対応する取得可能な実装ソースがある場合、別目録候補として追加する必要があるかを確認してください。注記だけから実装済みオブジェクトを追加せず、参考仕様の取得で代替しないでください。",
      "requirement": "catalog",
      "stage": "discovery"
    },
    {
      "paths": [
        "Program.cs",
        "Infrastructure/WebHostSetup.cs",
        "Web/Controllers/AccountController.cs",
        "Web/Controllers/StudentsController.cs",
        "Infrastructure/WebStudentCoordinator.cs",
        "Infrastructure/SearchContextStore.cs",
        "Infrastructure/EditorSnapshotStore.cs",
        "Infrastructure/FlashMessageStore.cs",
        "Core/Contracts.cs",
        "Core/SqlServerStudentService.cs",
        "Core/MasterMaintenanceService.cs",
        "maintenance/Program.cs"
      ],
      "question": "抽出関係を独立確認し、既存followup:392c5fcdc4c50bc6caf3e635e02298a48e882d71960704b52ceae80b92455292の解除可否をホスト側で判定してください。入口から定義、サービス生成引数、状態ストア、SQL対象、逆呼出元を照合し、U-REL-001／002を未解決のまま保持してください。",
      "requirement": "relationships",
      "stage": "relationship"
    },
    {
      "paths": [
        "deployment/Verify-AzureWebLogin.py",
        "Views/Students/Search.cshtml"
      ],
      "question": "U-REL-003の検証対象接続を確認してください。Verify-AzureWebLogin.pyの#SRC-009要求に対応する定義は現行Search.cshtmlに見つからないため、取得版の対応関係を明示し、実配置や検証成功を推定しないでください。",
      "requirement": "relationships",
      "stage": "relationship"
    }
  ],
  "coverage": [
    {
      "evidence": [
        {
          "endLine": 25,
          "path": "Infrastructure/WebHostSetup.cs",
          "sha256": "319d64cab66a244193ab3d33c01e55b2638928469db4f6548183e818f1d3ee10",
          "startLine": 19
        },
        {
          "endLine": 46,
          "path": "Web/Controllers/StudentsController.cs",
          "sha256": "c927cdab41e0b5d2ce38eb0f88b3680b98ea1bfd1a42634637679cd8b23037b1",
          "startLine": 5
        },
        {
          "endLine": 28,
          "path": "Infrastructure/WebStudentCoordinator.cs",
          "sha256": "f57e213dc22534b74e357aa066e31e25e58bac5b4de1b3f5458502e06e049385",
          "startLine": 3
        },
        {
          "endLine": 15,
          "path": "maintenance/Program.cs",
          "sha256": "77c9abf66a53783f1dfdb5f25842be627a1d3ae46b7f03d1f7879ca1c1474588",
          "startLine": 11
        }
      ],
      "recordKeys": [
        "r-host-composition",
        "r-project-boundaries",
        "r-navigation",
        "r-local-auth",
        "r-shared-identity",
        "r-request-protection",
        "r-search-input",
        "r-search-state",
        "r-search-data",
        "r-search-output",
        "r-lookups",
        "r-edit-load",
        "r-save-input",
        "r-student-write",
        "r-duplicate-confirmation",
        "r-save-output",
        "r-delete",
        "r-reset",
        "r-browser-ui",
        "r-db-profile-boundary",
        "r-write-gate",
        "r-maintenance-cli",
        "r-master-authorization",
        "r-class-maintenance",
        "r-code-maintenance",
        "r-data-references",
        "r-state-storage-separation",
        "r-native-permissions-and-unresolved-entrance",
        "r-retained-helpers",
        "r-support-http-entries",
        "r-smoke-reverse-use",
        "r-native-deployment",
        "r-azure-support",
        "r-build-and-generator",
        "r-verification-targets"
      ],
      "requirement": "relationships",
      "status": "unresolved"
    }
  ]
}
```

## 未実施

関係の採用・正式export、behavior、実DBスキーマ照合、原アプリ実行、人手受入れ。
