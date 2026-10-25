# CSharp_ASPNET 今回のソース再生成

実行ID: `20261025-regenerate`。2026-10-25。AG-BUILD 7.7。

入力正本は `test-project1/spec/CSharp_ASPNET/`、ソース正本は `test-project1/srcs/CSharp_ASPNET/`。索引8.5、検索詳細8.4、登録詳細8.5、方式別共通8.3、DB索引8.2、物理表8.1を使用しました。ファイルごとの版とSHA-256は `inputs.json` に固定しています。旧sourceRoot/spec、他方式、spec-evalを実装入力にしていません。

## 生成・照合

`database/generate.mjs` を実行し、物理7表（業務5表89列、技術補助2表）と5分類70コードのSQLソースを更新しました。生成器の固定旧版コメントを現在の入力指紋へ変更し、`database-inputs.json` に入力文書ID・版・ハッシュと生成SQLのハッシュを記録します。DDLを実DBへ適用していません。

検索4条件、7列、20/50/100件、schemaVersion 8.1、原入力と実行済み条件・Revisionの分離を `Web/Inputs/StudentSearchInput.cs`、`Infrastructure/SearchContextStore.cs`、`Web/Controllers/StudentsController.cs`、`Views/Students/Search.cshtml` と照合しました。氏名とカナを同セルへ置き、検索DTOへ住所・電話・更新日時を返さない既存実装を維持しました。

登録34項目、和暦4原入力、保存19入力・通常更新18入力、派生続柄分類、原子性・期待版・権限・確認・取消の既存C#/Razorを最新詳細と照合し、仕様に一致する実装を維持しました。上段基本情報と下段3列、確認ダイアログの分離、入力エラー時の原入力保持は今回のブラウザー操作で再確認しました。配置移動を理由に機能やDBを再設計していません。

## 今回の検査

- `python -X utf8 tools/build.py`: NuGet監査有効、Release build/publish、Core 114件・MVC HTTPS契約129件・ログイン47件 PASS。
- `dotnet build tests/EvidenceHost/EvidenceHost.csproj -c Release -p:RestoreLockedMode=true`: PASS。
- `python -X utf8 tests/Browser/verify_ui.py --base-url https://localhost:7443 --output build/test-results/browser`: 実Razor/JSと合成サービスで53件PASS。1366×650・1280×650、検索一覧内スクロール、入力・確認・取消・狭幅・参照権限を確認しました。
- `browser/editor-1280.png` を目視し、入力グループ・和暦4入力・主要操作の表示を確認しました。

最終配布は `build/publish/`、今回記録は `build/test-results/`、中間コンパイルと依存は `.tmp/`。入力・fixture・QAを保持しました。過去のPASSを今回へ流用していません。

SQL Server統合・配備・実認証製品・手動全画面受入・正式採点は未実施です。`formalScore=null`。
