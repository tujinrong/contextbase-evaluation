# .NET 共通処理とマスタ保守

`StudentManagement.Core` はVB.NET、WPF、MVC、Vue APIが使う.NET10ライブラリーです。和暦の厳密変換、Unicode scalar数とraw上限、正規化、入力検査、SQLの型付きパラメーター、同一SNAPSHOT検索、排他保存・版競合・重複確認・論理削除・同一トランザクション監査を実装しています。

検索候補は学生人数を集計しません。登録用候補取得と保存時は所属人数を検査します。確認トークンは認証主体/セッション/対象/読込版/正規化19値/全候補IDと版/10分期限へ結合します。理由は別途検査します。成功時に消費し、取消が確認できた失敗では占有を解放します。確定結果が不明な場合は再保存前の照会を要求します。

```powershell
dotnet build test-project1/srcs/Shared/StudentManagement.Core/StudentManagement.Core.csproj -c Release
dotnet run --project test-project1/srcs/Shared/StudentManagement.Core.Tests/StudentManagement.Core.Tests.csproj -c Release
dotnet build test-project1/srcs/Shared/StudentMaintenance/StudentMaintenance.csproj -c Release
```

境界値検査はDB・UIへ接続しません。SQL Server実機の動作をこの検査から証明しません。

`StudentMaintenance` は管理者向け保守CLIです。学生画面へマスタ編集欄を混ぜず、承認済みの完全なJSON入力を管理者自身が実行します。個別DBログインの `student_admin` 所属を要求ごとに検査します。

```powershell
$env:STUDENT_DB_CONNECTION = '<証明書検証付きの評価用接続文字列>'
dotnet run --project test-project1/srcs/Shared/StudentMaintenance -- class approved-class.json
dotnet run --project test-project1/srcs/Shared/StudentMaintenance -- code approved-code.json
```

クラスJSONの項目は `classId`、`expectedVersion`、`schoolYear`、`gradeCode`、`classCode`、`className`、`validFrom`、`validTo`、`capacity`、`displayOrder`、`isActive`、`remarks`。新規はID/版をnull、更新は実際に照会した値にします。クラス年度内の期間、同一年度コード一意、参照済み学年の不変性、定員・期間・所属状況を検査します。同年度同学年同名は警告です。

コードJSONの項目は `categoryId`、`codeValue`、`expectedVersion`、`codeName`、`displayOrder`、`isActive`、`validFrom`、`validTo`、`remarks`。分類は既存5分類です。通常追加許可、桁数、保護値の停止/期間短縮禁止、版を検査します。保護解除やキー変更は提供しません。

保守の変更なしは版・履歴を増やしません。変更と監査は同じ排他トランザクションです。実DBへの保守実行は本生成作業では未実施です。詳細な不足・未試験は [生成報告](../../report/build-report.md) を参照してください。
