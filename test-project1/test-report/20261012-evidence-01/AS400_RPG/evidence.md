# AS400_RPG 新規試験・撮影可否

20261012-evidence-01／2026-10-12／Windows x64。方式内の C 補助を新規コンパイルし実行した。SQLRPGLE/DDS/CLのコンパイル、Db2/SQL接続・初期値・実データ・共有構成への移植は行っていない。spec、runtimeコード、database、metadataは変更していない。

| 検査 | 今回結果 | 根拠 |
| --- | --- | --- |
| production STUNICODE.c/STUINPUT.c を使うC補助試験 | 35/35 PASS、コンパイル/実行exit0 | 20261012-evidence-01-rpg-results.json、-c-compile.log、-c-run.log |
| 新規仮名・学籍番号・カナの実C正規化／不正番号拒否 | 9/9 PASS、コンパイルexit0 | input-fixture-results.json / .raw.log |
| COPY参照、source幅、binder export、DDS format/座標/キー、CL資源、message/DB/独立性の静的検査 | 89/89 PASS | 20261012-evidence-01-rpg-static.log |
| SQLRPGLE／ILE C／DDS／CL／bind／Db2／5250実行 | NOT_RUN | IBM i環境・処理系・端末なし |

既存 tools/test_host.py はmetadata/spec-inputs.jsonとtest-status.jsonを更新するため、その読取済みコードをtests配下 run_host.py で実行する際、書込み先を新規reportへだけリダイレクトし、exeも build/20261012-evidence-01 へ分離した。適用した３置換と元tester hashは harness-adaptation.json。元tester自体は変更していない。元結果内の metadata/spec-inputs.json や originPreIsolationManifest は元testerの固定ラベルで、当回実入力は rpg-input-manifest.json に保存した全版/hashを用いる。evidence.json では正しい新規入力パスを明記した。

新規fixtureは方式内 tests/20261012-evidence-01/input-fixtures.json の架空３組。追加の input-probe.c はUTF8 stdinをUTF16へ変換して未変更の production StUnicodeNormalize を呼ぶ試験装置。業務や画面を模倣したRPG代替実装ではない。正常学籍番号の全角正規化・仮名保持・カナ変換・不正記号拒否を実Cで確認した。氏名・学籍番号のDB投入は０件。Cの成功はRPG業務検証・IBM i稼働・CCSID1399実端末描画の合格を意味しない。

処理系はZig0.14.1、方式内取得済みICU77.1。現在の実zig version/hash、Python/Windows情報は toolchain-current.json、コンパイルcommandは各生ログに保存した。specの全ファイル版/hashは rpg-input-manifest.json（版8.0/8.1）。protected-source-check.json の89対象ファイルは前後同hash。

## 未実施・撮影

IBM i SQLRPGLE/ILE C/DDS/CLコンパイル・bind、Db2 DDL/seed/CRUD/監査/rollback、２job競合、確定不明、承認IFS正常読取、5250画面は全て NOT_RUN。共有SQLServer接続も未実施。構造契約未確定の共有DBへは配備していない。

5250端末もIBM iもないため、RPGの実画面スクリーンショットを撮ることはできない。DDSテキストの描画、静的HTML、架空5250画像で代替しない。rootへ撮影不可を報告した。この担当はブラウザー/GUIを操作していない。
