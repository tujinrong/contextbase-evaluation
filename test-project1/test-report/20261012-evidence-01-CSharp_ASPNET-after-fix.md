# MVC UI-OBS-MVC-001 修正後検証

初期検索・新規・編集画面の空エラー枠は、本体の共通Razor部分がエラー0件でも常時描画される実装不具合だった。`ModelState.ErrorCount > 0` のときだけエラー要約を描画する修正を行い、情報表示は維持した。

仕様 `共通/04_共通UI部品設計.md` のUI-02（13行）および入力エラー保持（53行）に沿う局所修正であり、仕様変更は不要。DB・共通サービス・他方式の本体は変更していない。

修正対象は `_MessagePanel.cshtml:2`、追加検証は `tests/Program.cs:44` 以降の11項目。初期・新規・既存編集で空パネル/空bulletなし、実際の全体エラー・モデルバインドエラー・サービス入力エラーは可視、通常情報も可視を実HTTP・本体Controller・実Razorで確認した。

修正前に追加回帰検証を実行して初期検索の空枠で期待どおり失敗した。修正後の同じ契約試験は **42/42 PASS**、撮影ホスト再ビルドは **警告0・エラー0**。偽サービスを使う描画契約検証であり、SQL実統合の合格ではない。

入力は方式内107ファイルを新しい `.inputs.json` に保存。原証跡からの差分は許可されたRazor1ファイルと契約試験1ファイルのみ。仕様42文書（8.0/8.1）はSHA不変。Vue方式の124入力は全件SHA不変。

|変更ファイル|修正前SHA256|修正後SHA256|
|---|---|---|
|test-project1/srcs/CSharp_ASPNET/tests/Program.cs|2f19adfdda64a9eccd350091e141c1bd8831de2c6a74a85ef50f6c10b599b1a3|a36fc05e88106f80c78c8de11a86d6ff6c4dfa47b68773658ee3768817eb9e5f|
|test-project1/srcs/CSharp_ASPNET/Views/Shared/_MessagePanel.cshtml|f48745679fb30670f34eeaa2f58c651f54c97ee4d718d6e2014c1c55d6cb3c62|cdeb2006d70da32d4e2589e3d80471c6118498fc04585df49a024fbc076b872f|

修正前の部分ソース、期待失敗生ログ、修正後試験生ログ、ビルド生ログ、停止生ログ、差分、新しい入力ロックを別名保存した。元のevidence-01結果・画面・ログは上書きしていない。詳細の出力DLL・ログSHAは同名JSON。

MVC 7441は修正後DLLで再起動済み。親Agentは `https://localhost:7441/__evidence/login?role=Staff` から新しいセッションを開始して最終撮影する。寿命60分、停止は `POST /__evidence/stop`。生ログ `20261012-evidence-01-CSharp_ASPNET-after-fix.host-runtime-r2.log` は稼働中なので可変。Vue7442は変更・再起動していない。

親Agentは修正後の実ブラウザーで空枠消失を確認し、`test-evidence/20261012-evidence-01/CSharp_MVC/08-after-fix-search.jpg`、`09-after-fix-new.jpg` を保存した。メタデータの画像SHAを実ファイルと照合済み。既存編集の空エラー非表示も本回42件の実Razor契約で確認済み。

このAgentのUI操作・画面撮影・SQL接続・SQL実行は0。共有SQLのroles/CLR構造衝突修正、実DB・本番認証/認可、保存/競合/監査ロールバックは未実施。元のCore/Vue検証を本修正の新実行結果として流用していない。

撮影補記訂正：元evidence-01の05 INVALID_CAPTURE記述は、親Agentの画像プレビューの見落としだった。保存済み05-edit-bottom.jpgを親がview_imageで再確認し、編集下部の正常画像としてCAPTUREDへ訂正した。アプリ不具合・撮影失敗には分類しない。04は03と同SHAのDUPLICATE_CAPTURE。元記録を保ち、本補記を最新の判断とする。
