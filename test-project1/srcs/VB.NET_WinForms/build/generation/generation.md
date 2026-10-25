# VB.NET_WinForms 再生成記録

2026-10-25 / build-agent 7.7 / AGENTS 7.2 / run-id `20261025-regenerate`。AIが最新の自方式仕様・埋込みHTML・ネイティブ制約と現在ソースを照合し、以下の差を実装した。単なる旧ビルドの再実行ではない。

入力は `test-project1/spec/VB.NET_WinForms/` と固定全体規則・Agent入力。通常preflightは59ファイル、問題0件。各文書ID・版・SHA-256は inputs.json。詳細検索・登録、方式別共通、共通01～11、論理/物理テーブル、規約と最適化記録を照合した。自方式の最新版は8.1/8.2/8.3/8.4、最適化記録1.3。spec-eval、他方式の仕様・実装、旧source内specを入力にしていない。VB原仕様の編集はない。終端で59入力のbyte SHA-256一致を再確認した。

| 現仕様の差・保持理由 | 実ソース反映 |
| --- | --- |
| 全一致一括取得、ページ指定廃止 | SearchCriteriaは4条件だけ。SearchAsyncは別sort/directionと取消Token。TOP10001件数とOP-LISTを同じSNAPSHOTで実行しOFFSET/FETCHを除去。成功件数はItems.Count、10001はTotalCount相当なし・空一覧 |
| 原入力と適用済み条件、位置 | SearchDraftを追加。last applied normalized条件で並び替え/復帰しpending rawは保持。選択はhidden StudentId、位置はFirstDisplayedScrollingRowIndex。スクロールはDB要求を起こさない |
| scroll-2と状態保護 | owner/session/window/stateIDと現在の権威Revisionを照合。画面が受領した期待Revisionを明示引数で渡し、省略・最新補完しない。旧compact/形式欠落/未知版・期限切れは初期4条件、未検索、既定sort、選択なし・先頭へ。現行形式の未知・廃止キーはnullでも拒否 |
| 検索のネイティブHTML配置 | Client1180×610、条件GroupBox、Panel内4CheckBox、7列1146px、header24/row42、sortと日時。ページ部品を除去 |
| 編集のネイティブHTML配置 | Web風3等分・34pxを置換。基本GroupBox、中央756/gap8/400のTableLayout、下部緊急・備考・理由、更新情報と保存列、右端削除。単行23/24・ボタン27、Segoe UI9。住所だけ余幅を拡大し、エラーと狭幅はAutoScroll |
| 長文・日付・参照・確認 | 備考/理由はMultiline/Vertical/AcceptsReturn、参照TextBoxはReadOnlyでカーソル到達可。日付4原入力と不正値を保持し、01/02の不正終了日を無言消去しない。非同期終了後は破棄Formへ反映しない。確認にownerを指定、取消を既定 |
| コード/所属候補 | 有効な新規選択と既存停止値を区別。編集既存コードを名称付きで保持。所属は新規現在所属/期間が重なる最終所属/既存保持を分け、年度・学年・区分/日付変更時に再評価 |
| DB・保存を維持 | 自方式DB定義「検索射影の改訂」が物理表・列・制約・索引・保存手順を変更しないと明記。19/18入力、確認10分、任意続柄分類、更新版、同時保存、確定後成功を維持。DDL/seed/native保存SQL/main PackageReferenceのGit内容一致をCRLF正規化で確認。共有DBの推測移行はない |

今回実行した検査は Release build/publish、Core138、非表示fixture39、実フォーム245、実.NET Framework SQLCLR23、path guard21。実フォームは新規/編集/参照×1180/1280×610、エラー押下げ、長文、初期focus、実10000行、スクロール無DB、pendingと適用条件、hidden ID/位置の復帰、10001の非部分結果、stale command/foreign state拒否と旧compact初期化を検査する。入力/DDL型・NULL/SQL形/維持ファイルの177チェックは source-review.json。仕様ID対応は metadata/spec-mapping.json。test fixture JSON自体を変更せず、ハーネスを現契約へ更新した。

通常restore/監査を先に実行し、今回の最終統合実行も監査有効のまま完了。Pkcs9.0.4のNU1902/NU1903警告を記録した。既存PackageReferenceは変更せず、--locked-modeを指定したが永続packages.lock.jsonは存在しないため、全推移依存のlock完備という意味にはしない。

最新正本は build/test-results/results.json と今回の固定ログ/画像。旧audit/database-plan/sql-syntax/source-package/legacy-placement等9ファイルは方式内.tmp/legacy-workへ移し、今回の検査へ読み替えていない。native-artifact/protected-inputsは今回の値で作り直した。中間成果は.tmp、最終app/test-results/generationはbuild固定先。

未実施: SQL Serverへ接続するDDL/seed/CRUD/競合/障害/SQLCLR hosting、実個人主体・製品認証/配備、DPI拡大・IME・支援技術の網羅、性能評価・正式受入・逆生成採点。実フォームは方式内fixture利用で、実DB・手動受入とは区別する。正式点はnull。ZIPとoutputs manifestは親の最終包装工程で作成する。
