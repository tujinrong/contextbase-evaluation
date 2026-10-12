# WPF 検索初期表示修正 R3

実行ID `20261012-evidence-01-wpf-ui-fix-r3`。R2後の実画面で、年度以外の検索条件が「すべて」を表示せず空欄になった。独立仕様の詳細検索 SRC-004/005/006/009（L87–89/L92、版8.0）の初期値は「すべて」、未設定値はNULL相当であり、本体の表示バグとして修正した。仕様本文は変更していない。

コード候補に検索専用のNULL選択キーを追加し、クラスはNULL条件と一致する「すべて」候補をSelectedItemで選ぶ。候補再構成中は一時的な未選択をモデルへ戻さず、適合するクラスを保持する。条件に合わない既存クラスだけ解除する。学年「00」、登録画面の空文字raw ID、DBのlong?型は保持した。最終入力・変更前後SHA-256・実行ログは [ui-fix-r3-results.json](ui-fix-r3-results.json)。

| 今回の最終ソースでの新規実行 | 結果 |
|---|---|
| GUI fixture build | 0警告・0エラー |
| GUI self-test | 15 PASS |
| NativeSmoke | 7 PASS、SQL接続なし・Window Showなし |
| 実Application.Run / production Window起動 | search・new・editの3モード PASS、自動閉鎖 |
| 実検索ComboBox状態 | 初期、クラス選択と保持、クリア、未所属、不適合クラス解除の5状態 PASS |

実起動ではVisible/Loaded/HWND/resourcesとfixture値を検査した。検索の5状態は3起動モードのsearch内の追加観点であり、旧fixture12件や旧244件に加算していない。Core96・native境界102・actualFramework27はこの表示修正後には再実行していない。Core/CLRソースは変更していないが、過去のPASSを今回の再実行結果として扱わない。

NULLのSelectedValueだけではクラス候補再構成後の選択が消える中間失敗、誤ったSmokeプロジェクトパスの実行失敗も別ログに保持し、最終成功ログで区別した。R3は解除後の選択表示を検証した範囲であり、W-STU-107文言保持は後続の別修正・別検証で扱う。

手動操作・スクリーンショットはrootの別記録。fixture backendの起動・検索表示検査であり、共有SQLの配備・CRUD・認可結合は未実施。以前の入力・報告・初回launch failureは上書きしていない。
