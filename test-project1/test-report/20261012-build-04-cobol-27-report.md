# COBOL 独立生成・ホスト試験報告

2026-10-12／runId 20261012-build-04。現行入力はCOBOL/spec版8.0、46ファイル。入力SHA256は `fbc6b41cdffd6a97756087a7f693865fc5707ac11caac8e0539b983f2574f5f8`。旧版の合格を現行検査として流用していません。

生成済みは25 production PROGRAM-ID、11 COPY、38固定SQL、2業務画面、保守CLI、SQLServer業務5表89列＋技術2表、5分類70初期値、Makefile、依存記録、配備・ABI資料です。方式内のspec/source/database/tools/toolchainで完結します。生成は実業務分岐を持つCOBOL/Cで、未解決CALL/COPY/command参照・未生成参照先は0です。

| 検査 | 結果 | 新規証拠 |
| --- | --- | --- |
| 入力・CALL/COPY/SQL・ABI・状態・隔離静的検査 | 12/12 PASS | [20261012-build-04-cobol-26-static.json](20261012-build-04-cobol-26-static.json) / [生ログ](20261012-build-04-cobol-26-static.raw.log) |
| GnuCOBOL3.2.0構文/C変換＋Zig0.14.1リンク | production25＋probe3、警告0/エラー0 | [20261012-build-04-cobol-24-host-build.json](20261012-build-04-cobol-24-host-build.json) / [生ログ](20261012-build-04-cobol-24-host-build.raw.log) |
| 実バイナリーの境界・入力検証 | 86/86 PASS | [20261012-build-04-cobol-25-host-tests.json](20261012-build-04-cobol-25-host-tests.json) / [生ログ](20261012-build-04-cobol-25-host-tests.raw.log) |

実行対象はWindows x64ホストです。ICU78.3-4/OpenSSL3.6.5-1を含むMSYS2配布物の版・取得先・SHA256とローカルZigを固定しています。手書きCはWall/Wextra/Werror、GnuCOBOL生成Cだけ旧形式プロトタイプ警告を抑制しています。ABI1、暦26、整数6、Unicode12、LIKE2、hex3、HTTP11、CGI400/401の2、登録検証23件を実行しました。COPY本体を用いたAPP整列・pointer/int32/int64/NULL、raw上限と正規化後上限、4バイト文字、全角hint、必須・状態・終了日・連絡先を含みます。

ビルド時の全コンパイル入力とexeハッシュを記録し、試験前に現在のソース・バイナリーと一致することを検査します。18番のビルド失敗と19番の旧バイナリー試験は保存しましたが、現行合格根拠から除外しました。最終証拠は24/25/26番だけです。

19raw（生年月日は元号/年/月/日4入力）、12検索条件、11一覧項目を実装し、一覧の技術ID・複合列を分けるためSQL取得は13物理列です。仕様ID/ファイル対応は方式内IMPLEMENTATION.mdです。EV-SRC-001～006、EV-REG-001～007、共通01～17、SQLServer定義の対応を記録しています。

入力中条件と実行済み条件を分離し、検索/ページ/クリア/復帰/保存/確認/削除等でContext revisionを検査します。登録後は再取得、候補検索では人数集計を実行せず登録候補のみ参考人数を取得します。続柄分類と値のNULLを揃え、定員・候補・版をゲート取得後に再判定し、全候補ID/版をハッシュ・20件だけ表示します。理由未入力は確認情報を保持し、取消では消費します。保守監査はCREATE/UPDATE/DISABLE/ENABLE、学生削除はDELETEです。描画時のDB失敗をヘッダーへ反映できるよう、描画完了までHTTPヘッダーを送信しません。

未生成の参照先や業務TODO骨組みはありません。ただしLinux版依存物の正確なパッケージlock、Linuxコンパイル/リンク/CGI、実SQLServerのDDL/seed/CRUD/保守/有効権限、プロセス再起動状態復帰、2接続競合/定員、監査失敗、COMMIT後応答喪失、ブラウザー画面は未実施です。共通認証済みWebサーバー、DBサービス主体、秘密管理は配備前提で、実稼働設定はまだありません。この報告は実DB/配備の合格を意味しません。

構造的な仕様矛盾は今回の担当範囲で確定していません。旧中断報告は保存し、今回の報告で上書きしていません。入力/生成物ハッシュの全一覧は [20261012-build-04-cobol-27-report.json](20261012-build-04-cobol-27-report.json) です。
