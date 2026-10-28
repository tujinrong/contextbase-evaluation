# CSharp_ASPNET 仕様入力配置の移行

2026-10-25。projectId=test-project1、工程=spec-root-migration。入力コミットは4fbf60ed0f3a9e3e72ebf18240515281dc70a329。未コミット差分を含む実ファイルの版・SHA-256を入力として固定した。

仕様正本をtest-project1/srcs/CSharp_ASPNET/specからtest-project1/spec/CSharp_ASPNET/へ移動した。42文書のspec-meta.path/版/可視改訂日と必要な参照を更新し、旧フォルダを削除した。生成ソース・build/・.tmp/はtest-project1/srcs/CSharp_ASPNET/側を維持する。仕様参照は選択specRoot内で閉じる。

全体規則6種のコピー、Agent定義、生成ツール/configの入力解決を同期した。画面分類・検索/編集項目・イベント・DB項目/制約を保全し、配置/メタ/追加説明だけを逆変換した入力SHA検査と独立レビューで確認した。画面HTMLは入力と一致し、再描画は未実施。render.jsonの過去出典と今回のcanonical対応を区別した。

build-agent preflight --project test-project1 --profile CSharp_ASPNET --run-id spec-root-migration --inspect-only trueは入力58ファイル、指摘0で通過。読み込んだ仕様は本方式の新specRootだけであり、旧root/他方式/評価資料へのfallbackはない。通常preflight、アプリ生成、DB生成、ビルド、実機試験は今回実施していない。

入力/出力の全ファイル・版・SHAはmanifest.json、今回検査はvalidation.jsonへ保存した。業務実装・生成済みDB・accdb・既存配布ZIPと通常生成の記録は保持した。変更したプログラムはAgent/生成補助/パス検査のtoolingに限る。次の生成前には従来のinput lock/preflightを新入力で明示実行する。formalScore=null。

未実施: 実アプリの再生成・コンパイル・業務試験、DB実行・Access/5250実機・端末/認証アダプターの実行試験、画面再描画・Excel/PDF変換、正式採点・受入。
