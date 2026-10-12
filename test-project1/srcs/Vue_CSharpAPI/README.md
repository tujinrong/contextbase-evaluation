# Vue3/TypeScript＋C# Web API 学生管理

生成版1.0／2026-10-12。仕様セット7.2＋担当詳細の局所修正版7.3。Vue3・Composition API・TypeScript strict、APIはnet10.0、SQL Server 2022。検索／登録2画面を実装した。

## ビルドと起動

```powershell
Set-Location frontend
npm ci --ignore-scripts
npm run build
Set-Location ../backend
dotnet restore --locked-mode
dotnet build --no-restore
$env:ConnectionStrings__StudentDb = 'Server=YOUR-SERVER;Database=YOUR-DB;Integrated Security=True;Encrypt=True;TrustServerCertificate=False'
dotnet run --launch-profile https
```

Node24系、Vue3.5.43、Vite7.3.7、TypeScript5.9.3をpackage-lock.jsonで固定。Node・npmの実行版は担当検査記録に記載。npm監査は0件。APIが同一オリジン`https://localhost:7242`でSPAのビルド成果物を配信する。APIの不存在はJSON404とし、index.htmlへ落とさない。開発時のViteプロキシはローカル開発証明書に限って検証を緩める。本番DBの暗号化・証明書検証は共有サービスで有効。

SQL Serverは`../Database/SQLServer`のDDL/seedを適用し、承認済みクラスを設定する。実DBは今回の検査で接続していない。認証には同一オリジンのSecure/HttpOnly Cookieと全POST/PUTのCSRF検証を使用する。QA-AUTH評価用セッションの有効化・制約は`../CSharp_ASPNET/README.md`参照。本番の認証基盤結合は未実施。

## 仕様と実装

| 仕様ID | 実装 |
| --- | --- |
| SCR-STU-001、EV-SRC-001～006 | frontend/src/pages/StudentSearchPage.vue、composables/useStudentSearch.ts |
| SCR-STU-002、EV-REG-001～007 | frontend/src/pages/StudentEditPage.vue、composables/useStudentEditor.ts |
| REG-002～024、UI-03～07 | components/StudentForm.vue、CodeSelect.vue、JapaneseBirthDateField.vue |
| UI-08／09／11 | StudentGrid.vue、Pager.vue、DuplicateDialog.vue、DeleteDialog.vue |
| UI-10／12／13 | useDirtyGuard.ts、originalSnapshot／form／dirty／busyの分離 |
| API契約、ID・版 | api/contracts.ts、studentApi.ts、apiClient.ts（ID/版は10進文字列） |
| API全ルート | backend/Controllers/StudentsApiController.cs |
| 共通01／02／12、S-14 | ASP.NET方式と同じInfrastructure/InputsをbackendプロジェクトのCompile Linkで共用 |
| 正規化・全業務検査・SQL/監査/重複確認 | ../Shared/StudentManagement.Core |

部品は親のpropsを直接更新せず更新イベントで新しいformを渡す。原スナップショットは別複製。候補応答は要求連番とAbortControllerで古い応答を破棄。未実行draftと実行済みcriteriaを分け、一覧・ページ操作はAPIの保持条件を使用する。学生値をv-html／localStorageへ保存する処理はない。

## 検査状況

`npm run build`でstrict型検査・production bundle成功、C#APIのビルドは警告0／エラー0。ASP方式の`tests/WebContracts.csproj`に同じAPIコントローラーを組み込み、39件のHTTPS/HTTP契約検査を実施した。

実SQL Server結合・同時更新／定員・ブラウザーE2E（watch／応答逆転／履歴移動／オフラインを含む）・外部認証基盤・負荷／受入は未実施。API／UIの生成とコンパイルを実機試験合格とは扱わない。

## 管理者マスタ保守

クラス／コード保守は共有CLI `../Shared/StudentMaintenance/` を使用する。業務画面は検索／登録の2画面に保つ。CLIの実行主体はDB側のstudent_admin権限で再検査され、承認済みJSON入力を受け取る。

```powershell
$env:STUDENT_DB_CONNECTION = 'Server=YOUR-SERVER;Database=YOUR-DB;Integrated Security=True;Encrypt=True;TrustServerCertificate=False'
dotnet run --project ../Shared/StudentMaintenance/StudentMaintenance.csproj -- class approved-class.json
dotnet run --project ../Shared/StudentMaintenance/StudentMaintenance.csproj -- code approved-code.json
```

入力契約は共有Coreの `ClassChange`／`CodeChange` とCLI手順を参照する。保護値・期間・定員・参照・期待版・理由・履歴・共通ゲートをDBトランザクションで検査する。実DBでの保守結合試験は今回未実施。
