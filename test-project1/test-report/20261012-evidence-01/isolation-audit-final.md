# 最終隔離・成果物監査

20261012-evidence-01 ／ test-project1。最終BUG修正後の現在ファイルを読み取りで再検査しました。

**ISOLATION_AND_ARTIFACT_AUDIT_PASSED。確定指摘0件。** 独立ソース・入力・凍結成果物の監査結果です。共有SQL上のアプリ受入合格を意味しません。

[詳細JSON](isolation-audit-final.json) · [共有SQL最終SELECT結果](sql-readonly-final.json) · [試験報告README](README.md) · [中間監査](isolation-audit.md)

| 検査対象 | 最終結果 |
| --- | --- |
| 固定入力 | 335件SHA一致、変更0。各方式spec入力320件を含む |
| DB資源 | SQL/JSON31ファイルSHA一致、変更0。DB仕様入力は固定入力の一部として照合 |
| 既存隔離checker | 855ファイル／1511参照、指摘0 |
| 補助隔離検査 | 全855ファイル、110プロジェクト項目、47fixtureファイル。相互参照・共有参照・相互hardlink0、未解決MSBuild式0 |
| 凍結source ZIP | build10の7個すべてSHA一致、再生成なし。今回BUG修正を含まない旧版とREADMEへ明記 |
| 最終SQL読取 | Windows統合認証＋Encrypt=Yes／TrustServerCertificate=No、13条件PASS。テーブル・業務オブジェクト・ユーザーassembly・アプリ役割各0 |

既存checkerは元スクリプトを変更せずメモリ上で起動点と新しい出力prefixだけを調整し、ファイル書込みを抑止しました。標準checkerが十分に扱わないcs/vb/bas/clsと試験fixtureも補助検査に含め、ワイルドカードCompile、Include/Update/Remove、ProjectReference、ローカルspecリンクの方式内閉鎖を確認しました。外部処理系や任意の動的経路全体の保証ではありません。

| 方式 | spec入力ファイル数 | 文書版 |
| --- | --- | --- |
| VB.NET_WinForms | 46 | 8.0 / 8.1 |
| CSharp_WPF | 46 | 8.0 / 8.1 |
| CSharp_ASPNET | 46 | 8.0 / 8.1 |
| Vue_CSharpAPI | 46 | 8.0 / 8.1 |
| COBOL | 46 | 8.0 / 8.1 |
| AS400_RPG | 45 | 8.0 / 8.1 |
| Access | 45 | 8.0 / 8.1 / 8.2 |

ユーザーが承認した今回の実装BUG修正を記録しました。sqlserver-12の既存986ファイルとの比較では18ファイルが変更され、新規activeファイルは48件でした。既存ファイル変更はAccess/VB/WPF/MVCの方式内に収まり、仕様入力とDB資源には変更がありません。新規試験ホスト・fixture・seed helperも各方式内に配置されています。詳細なfile・before/after SHA・追加fileはJSONに記録しています。

VBはTab順・Shown後フォーカスとスクロール、MVCは空validation枠、WPFは在籍選択・クラス選択補助・警告、AccessはACE FileFormat12・Yes/No値・候補一覧の全行参照・ACP936による中点文字の置換を修正した現在ソースです。別Agentによる8行のread-only照合でも、WPF R4/VB after-fix/MVC after-fixの現在SHAは最新報告と一致しました。WPF R3の変更後SHAの一部は後続R4が置換しています。

Access配布成果物は承認された新ACE成果物へ置換済みです。旧原本の不変を合格条件にせず、旧版バックアップのバイト一致と最終原本の検査証拠をそれぞれ確認しました。監査Agentはaccdbをアプリで開いていません。

| Access成果物 | 最終照合 |
| --- | --- |
| 旧版バックアップ | `838f5fe63826fce58face6c5102d363af41c3ef433d6b2d7229c8d5de0c93de5`（旧838F版とbyte exact一致） |
| 現配布原本 | `d1777167fd7423bf4399f05d006519fd5a8e005a6fef2e56b1a8f11aad73ec87`（指定D177版と一致、Standard ACE DBヘッダー） |
| 最終R6 | 58通知＋1ラベル＋13フォーム/DAO＋19配布＝91チェックPASS、Compile成功、FileFormat12 |
| clean初期状態 | 5分類／70コード、クラス0／学生0／監査0、外部リンク0、test moduleなし |
| 撮影用fixture | ローカルACEの新規fixture。最終UI close記録のSHAに一致、原本D177を維持 |

[Access R6詳細](Access-r6/README.md)・[clean配布試験](Access-r6/20261012-evidence-01-access-r6-deployment.json)・[最終artifact照合](Access-r6/final-artifact-check.json)・[撮影fixture終了](Access-ui-r6-screen/ui-closed.json)に対応する現在SHAを確認しました。生ログと個別JSONのSHAも監査JSONへ保存しました。R6の通知は `E-DATE-001: 生年月日の元号・年・月・日を確認してください。` と文字単位で一致しています。

R5の業務137・関係21・形式/Boolean10・全候補一覧21・二プロセス競合は、R6では全件を再実行していません。過去R5結果はその版の証拠として保持し、最終R6の再試験成功へ流用しません。

撮影metadataはnative26＋web17＝43件、MVC04の明示重複1件です。元画像のJPEG完全デコード・HTML埋込み一致はrootの独立検証の範囲です。R6の実画面は `Access/09-invalid-date-after-final-fix.jpg`。全ホスト終了は[終了状態](close-verification.json)を参照してください。各方式の画面証拠はSQL未接続fixture、COBOLは実CGI401/400エラー画面だけ、AccessはfreshローカルACE、IBM i/5250はNOT_RUNです。

共有SQLは4つの固定metadata SELECTだけで再検査しました。DBは `contextbase_test_project1` の1個、Express17.0.5005.3／ONLINE／compatibility160／Japanese_XJIS_140_CI_AS。テーブル0を完全なmetadata可視性で確認しています。共有契約の構造衝突が未解消のため業務テストデータは投入していません。DDL/DML・役割・サービス・サーバ設定変更0。検査主体はsysadminなのでアプリ用DB主体の認可を検証した結果ではありません。

共有SQLへのスキーマ移行・正常CRUD・実DB主体認可・競合/監査rollback、IBM i/5250、逆生成評価/採点は未実施です。中間isolation/SQL記録は変更せず、新しいfinalファイルだけを保存しました。

