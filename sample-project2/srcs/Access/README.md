# Access 社員経歴管理

Windows 11 / Microsoft 365 Access・Excel 64bit / VBA7 / DAO・ACE の単一 ACCDB です。5画面、6機能、5表48列を実装します。社員削除はなく、経歴の除去は社員全体の保存時にだけ反映します。

最終候補は `build/CareerManagement.accdb`、実ソースは `src/`、構造定義は `database/`、正式試験は `tests/` です。`src/forms/*.txt` は Access native export（UTF-16）、その他のソースは UTF-8 です。フォームの再構築定義は `src/forms/definitions.py`、コードは各 VBA module/class にあります。ソースだけで再構築でき、原仕様をソース内へ複写しません。

## 再構築

Python 3.11 x64 と pywin32 311 が必要です。Office は既存の製品を使います。Python の実行入口は `-B` で起動し、builder も private source の import 前に `sys.dont_write_bytecode=True` を設定します。生成キャッシュは正本へ保存しません。

```powershell
python -B -m pip install --no-user --target .tmp/python-deps pywin32==311
python -B -X utf8 tools/build.py --test-secrets --publish-candidate
python -B -X utf8 tests/run.py --cycle 1
python -B -X utf8 tests/run.py --cycle 2
python -B -X utf8 tests/concurrency.py
python -B -X utf8 tests/run.py --cycle 3
```

ビルドは新しい `.tmp/build/CareerManagement.accdb` だけを初期化し、全 Compile・投入検査を終えてから固定候補へ確定します。既存最終候補が manifest の SHA と違う場合は上書きせず停止します。既存利用者 ACCDB を引数にして再初期化する機能はありません。Windows ANSI codepage が日本語以外でも、VBE へ渡す非往復の文字列 literal を `ChrW` に変換して Unicode を保持します。

Compile は `RunCommand(126)` 後の `Application.IsCompiled=True`、staging だけの全クラス実初期化 probe、probe 除去後の再 Compile・IsCompiled、投入後の最終 IsCompiled を必須にします。SysCmd(603) は当環境の Automation 呼出しで引数数エラーとなったため、成功判定に使いません。結果は `build/seed-manifest.json` の `compileGate` へ記録します。

上の検査コマンドと `open-verification.py` はリポジトリ完全版の入口です。source-only ZIP は生成に必要な production helper だけを含み、正式 tests/検査用 helper は含みません。source-only 再構築では先頭2コマンドを使います。

`--test-secrets` は実行時に秘密をメモリ生成し、検査用の取得口を同一 Windows 利用者の DPAPI で `.tmp/test-secrets.dpapi` へ保護します。秘密・検証情報を Git、通常ログ、manifest へ出しません。この候補は実機検証用で、利用者資格情報で初期設定した配布版とは区別します。VBA の秘密メモリ完全消去は保証しません。

## 初期設定と操作

SP2-DEMO-01 v1.0（基準業務日2026-10-27）の完全架空データです。分類3、コード9、利用者2、社員3、経歴3を単一確定します。ログインIDは `demoadmin`（ADMIN）と `demostaff`（STAFF）です。秘密は別の初期設定で与えます。通常起動で投入やリセットをしません。

利用者用の配布前初期設定では、新規 staging の `SP2_Staging=True`、業務5表が空のときだけ既存 frmLogin を初期設定モードで開きます。ログインIDを固定表示し、ADMIN の秘密→同じ秘密、STAFF の秘密→同じ秘密の順に伏字で入力します。成功した staging を検査して `SP2_Staging=False` にした版だけを配布対象にします。CLI の `--interactive-initialize` は別の検査用入口で、伏字 Form の実入力検証を代用しません。今回の candidate はこの利用者用実入力を未実施です。

投入済みファイルは `python -B -X utf8 tools/verify-seed.py --database build/CareerManagement.accdb --manifest build/seed-manifest.json` で確認します。同一なら挿入せず SKIP、編集済み・所有不明なら無変更で STOP です。Access を開いたことによる物理ファイル変更も再投入を許す根拠にしません。

STAFF でログインし、社員検索の初期条件「在職」で000001/000002の2件を確認します。000001を選択→編集→2経歴→取消→経歴書Excelを出力します。未使用000004で社員と経歴を新規保存し、再検索します。ADMIN はコードマスタで部署04を追加・停止できます。在籍3値は編集できません。退職を含め000003を検索すると、経歴0件の出力は拒否します。

Excel は専用 instance で2シート `.xlsx` を生成し、保存先を利用者が選びます。保存先取消は正常取消です。原文を文字列として保存・再読込し、最後に現在認可を再確認して完成名へ確定します。既存の利用者 Excel を接収・終了しません。

## 検査と境界

検査は `.tmp` の専用コピーだけで実施します。`build/test-results/quality-cycles.json` は3回の検査・指摘・修正・回帰、各 cycle JSON は対象 artifact/入力/source SHA と独自 API 検査、`pilot-coverage.json` は原41条件の実施状態です。独自検査の PASS を原 Pilot 全体の PASS と扱いません。

処理中は入力・一覧・タブを物理的に保護し、Esc 以外のキーを消費します。Esc の取消は既存の社員検索・帳票要求の範囲に限ります。サービス終了後に元の保護状態を復元してから、保存済みコードのキー読取専用、新規経歴の入力可能等の業務状態を適用します。専用コピーの `tests/busy.py` は成功・失敗・取消と状態遷移を確認します。

`python -B -X utf8 tools/open-verification.py menu` は専用 UI コピーを開き、標準フォームを COM の値・イベントで準備します。stdin に login/menu/search/editor-new/editor-edit/careers/code/quit を入力します。これはキー入力・貼付・IME の合格証拠にはなりません。

実キー・7桁貼付拒否・6桁訂正・通常保存再読込・編集番号保護と、5画面の目視は、root の `build/test-results/native-ui.json` が対象候補 SHA ごとに記録します。帳票の後続修正を含む新 ACCDB へ過去の実入力結果を自動転用しません。IME変換そのもの、DPI125/150%、利用者秘密による初期設定は当該記録の未実施を確認してください。

印刷の技術差分 PH07：Excel の Fit To は手動改ページを無視するため、詳細の Zoom=False 指定に対する Access 内の回避策として、A4 実幅から明示 Zoom を算出します。列幅を紙幅内へ置き、Zoom は100%以上、本文10.5pt以上、縦は章・案件の続きへ展開します。実 HPageBreaks と計画ページ境界が一致・安定しなければ出力を拒否します。採用根拠と元詳細のSHAは `build/generation/implementation-deviations.json` に記録し、業務仕様の承認と区別します。

ACCDB を直接編集できる信頼された DEMO 利用者向けです。ログインで強いファイルアクセス分離はできません。共有先障害・電源断、利用者受入・正式採点は未実施です。実印刷は今回の帳票 SHA とroot記録に従います。正式得点は null です。
