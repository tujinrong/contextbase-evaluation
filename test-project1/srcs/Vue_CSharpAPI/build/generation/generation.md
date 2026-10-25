# Vue_CSharpAPI 今回のソース再生成

実行ID: `20261025-regenerate`。2026-10-25。AG-BUILD 7.7。

入力正本は `test-project1/spec/Vue_CSharpAPI/`、ソース正本は `test-project1/srcs/Vue_CSharpAPI/`。索引・検索詳細・登録詳細8.4、方式別共通8.3、DB索引8.2、物理表8.1を使用しました。ファイルごとの版とSHA-256は `inputs.json` に固定しています。旧sourceRoot/spec、他方式、spec-evalを実装入力にしていません。

## 生成・照合

`database/generate.mjs` で物理7表（業務5表89列、技術補助2表）と5分類70コードを再生成し、`database-inputs.json` に入力ID・版・ハッシュとSQLハッシュを保存しました。DDLを実DBへ適用していません。

`frontend/build.py` でTypeScript型検査と本番JS/CSS生成を行い、C# APIと合わせて `build/publish/` を更新しました。生成済み旧 `backend/wwwroot` は `.tmp/legacy-work/` へ移動し、fixtureホストも現在の配布ファイルを使うように修正しました。従来のソース用静的アセットmanifestを今回の配布検査へ混入させません。

検索4条件・7列、search-compact-1、contextRevision、原入力/実行済み条件の分離、旧形式の警告初期化、未知条件の拒否を、当方式のAPI・composable・検索画面・一覧部品と照合しました。登録34項目、和暦4原入力、上段基本情報＋下段3列、単一確認状態、保存・権限・版・CSRF・64bit ID文字列の既存契約は維持しました。仕様に一致するCore・API・Vue部品を作為的に変更していません。

## 今回の検査

- 通常 `python -X utf8 tools/build.py`: NU1902/NU1903でrestore失敗。固定依存System.Security.Cryptography.Pkcs 9.0.4に対する監査の失敗であり、未解決です。
- `python -X utf8 tools/build.py --no-audit`: この呼出し限定で監査を省略し、Release build/publish、Core105件・HTTPS API111件PASS。依存版・監査の恒久設定は変更していません。
- `python -X utf8 frontend/build.py browser`: 実Vue/Edgeと合成APIで33件PASS。標準サイズ・狭幅・確認取消・原入力・非同期順序・参照権限を確認しました。
- 現在の `build/publish/wwwroot` と実Controllerを配信する不変fixtureに対し、`python -X utf8 tests/fullstack_browser.py --url https://localhost:7444 --output build/test-results/fullstack`: 15件PASS。今回のbundle、API接続、64bitID、DTO縮小、失敗時入力保持を再確認しました。
- `fullstack/built-search.png` を目視し、4条件・7列・一覧領域・ページ操作の表示を確認しました。

最終配布は `build/publish/`、今回記録は `build/test-results/`、中間コンパイル・Vite・依存は `.tmp/`。入力・fixture・QAを保持し、旧PASSは流用していません。

SQL Server統合・配備・実認証製品・手動全画面受入・正式採点は未実施です。`formalScore=null`。
