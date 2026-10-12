# Native 実装記録

最終状態: **STR-ACCESS-001 により全方式の生成を中断**。下記は中断前に実施した検査記録であり、完成・配備可能の判定ではない。rootがこの検査後に、クラス候補でDBの学年/表示順を維持する変更と停止値の表示補助を保存したが、中断のため最終Nativeソースの再ビルド・smokeは未実施。下記0警告/0エラー・12件通過をその最終変更の合格として扱わない。[全体報告](build-report.md)を参照。

実施日: 2026-10-12。対象: `test-project1`、build 工程。読み取りは docs/agents と test-project1 の仕様・開発規約・生成共有 Core に限定し、spec-eval 本文は未読。出力は srcs/VB.NET_WinForms、srcs/CSharp_WPF、担当仕様の局所訂正、および本報告。

入力: VB.NET_WinForms / CSharp_WPF 検索詳細 7.3、登録詳細 7.0、方式別共通実装 7.0、方式別開発規約 7.3、共通仕様・SQL Server 正本は build 実行時の入力一覧に従う。過去のレビュー合格を今回の検査として流用していない。

局所訂正: 両検索詳細のクラスコード10→9、クラス名50→18。WPF 番号 prefix20→15。両方式規約の確認 hash を binary(32) に一致。WPF 規約の主体 nvarchar(128)、SQL Server 保存手続、固定 DB エラーコードへの表現を統一。文書版は7.3。共通05/10や共有基本設計の訂正は root が担当。

構造検査: 担当詳細の見出し・LIST 列・空欄・参照、原入力契約、DB 正本の型・長さ、保存単位を検査し、構造的な停止条件は確定しなかった。確認待ちの業務 Tx を終了後、短い確定単位で確認情報を発行し、再保存時にゲート下で再検査・消費する構成は既存の確認契約から確定できる実装補完とした。

実装: 両方式の2画面、19業務入力、和暦4原入力、12検索条件、11一覧表示、独立した ID/期待版/確認/スナップショット、raw 値の保持、NULL、読取り権限モード、版競合・不存在・重複候補・削除理由・変更なし・保存不明の結果分岐。VB はフォーム/Designer/Presenter、WPF は XAML/MVVM/Command。共通業務は root 生成の StudentManagement.Core を利用。DB 主体と role は DB から取得する。

検査結果:

| 検査 | 結果 |
| --- | --- |
| .NET SDK | 10.0.401 / Windows |
| VB `dotnet build ...StudentManagement.WinForms.vbproj` | 成功、0警告/0エラー |
| WPF `dotnet build ...StudentManagement.Wpf.csproj` | 成功、0警告/0エラー |
| `dotnet run --project ...VB.NET_WinForms/Tests/NativeSmoke.csproj` | 12 checks passed。フォーム/XAMLの生成、不正日付と和暦原入力保持、検索適用済み条件、未所属補助解除、64bit ID、クリアを確認。画面非表示、DB未接続 |

未実施: 実DBのDDL・seed実行、CRUD/監査の往復、2主体競合と最終席、履歴失敗のrollback、DB配備権限、確認期限/候補変更、保存結果不明、IME/画面描画/DPI/読み上げ/性能。コンパイルと smoke 成功は仕様全件適合を意味しない。

制約: Native は仕様で許容された信頼するアプリケーション内サービスによる評価構成。本番 EXEC-only DB 更新入口と DB 側の正規化再生成は未実装。本番の強いセキュリティ境界として配備しない。共有マスタ保守 CLI の実装・試験と共有 Core の検査は root の報告範囲。
