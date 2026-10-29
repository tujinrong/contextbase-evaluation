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

本サンプルの通常生成は利用者指定の固定DEMO認証情報 `admin / 123`（ADMIN）、`staff / 123`（STAFF）を使用します。パスワードの下限は本方式内で3 Unicodeスカラー、上限128です。salt付きPBKDF2-SHA256・600000反復を維持し、DBに平文パスワードを保存しません。`--demo-credentials` で明示でき、旧 `--test-secrets` も同じ固定DEMOの互換入口です。検査helper用には同じ値をDPAPI保護して `.tmp/test-secrets.dpapi` へ保存します。`--interactive-initialize` は別の運用値を非表示入力する入口です。

## 初期設定と操作

新規生成はSP2-DEMO-01 v1.1（基準業務日2026-10-27）の完全架空データです。分類3、コード9、利用者2、社員3、経歴3を単一確定します。ログインIDは `admin`（ADMIN）と `staff`（STAFF）です。初期パスワードは両方とも `123` です。通常起動で投入やリセットをしません。既存v1.0の利用中DBは全量seedをせず、2DEMOアカウントだけの認証情報移行を別記録し、業務行・監査・PK参照を保持します。

利用者用の配布前初期設定では、新規 staging の `SP2_Staging=True`、業務5表が空のときだけ既存 frmLogin を初期設定モードで開きます。ログインIDを固定表示し、ADMIN の秘密→同じ秘密、STAFF の秘密→同じ秘密の順に伏字で入力します。成功した staging を検査して `SP2_Staging=False` にした版だけを配布対象にします。CLI の `--interactive-initialize` は別の検査用入口で、伏字 Form の実入力検証を代用しません。今回の candidate はこの利用者用実入力を未実施です。

投入済みファイルは `python -B -X utf8 tools/verify-seed.py --database build/CareerManagement.accdb --manifest build/seed-manifest.json` で確認します。同一なら挿入せず SKIP、編集済み・所有不明なら無変更で STOP です。Access を開いたことによる物理ファイル変更も再投入を許す根拠にしません。

STAFF でログインし、社員検索の初期条件「在職」で000001/000002の2件を確認します。000001を選択→編集→2経歴→取消→経歴書Excelを出力します。未使用000004で社員と経歴を新規保存し、再検索します。ADMIN はコードマスタで部署04を追加・停止できます。在籍3値は編集できません。退職を含め000003を検索すると、経歴0件の出力は拒否します。

Excel は専用 instance で2シート `.xlsx` を生成し、保存先を利用者が選びます。保存先取消は正常取消です。原文を文字列として保存・再読込し、最後に現在認可を再確認して完成名へ確定します。既存の利用者 Excel を接収・終了しません。

## 検査と境界

検査は `.tmp` の専用コピーだけで実施します。今回の最終候補の再検査は `build/test-results/current-runtime.json`、業務・境界値は `cycle3.json`、描画と実キーの確認は `native-ui.json`、属性と共通判定は `ui-observations.json` / `ui-conformance.json` に記録します。入力・候補・試験ソースのSHAと実施範囲を照合し、過去候補のPASSを引き継ぎません。独自検査のPASSは原41Pilotの全条件や正式受入の合格を意味しません。

処理中は入力・一覧・タブを物理的に保護し、Esc 以外のキーを消費します。Esc の取消は既存の社員検索・帳票要求の範囲に限ります。サービス終了後に元の保護状態を復元してから、保存済みコードのキー読取専用、新規経歴の入力可能等の業務状態を適用します。専用コピーの `tests/busy.py` は成功・失敗・取消と状態遷移を確認します。

`python -B -X utf8 tools/open-verification.py menu` は専用 UI コピーを開き、標準フォームを COM の値・イベントで準備します。stdin に login/menu/search/editor-new/editor-edit/careers/code/quit を入力します。これはキー入力・貼付・IME の合格証拠にはなりません。

UIは標準未連結フォームを使い、本文の灰色・黒文字・白入力、四角い標準ボタン、テーマとグラデーションを使わない設定を明示します。本文・付属ラベル・一覧見出し・ボタン・タブは Yu Gothic UI 11pt です。CheckBox 本体はフォントを持たず、付属ラベルが文字を表示します。項目別の Twips を維持し、リサイズ時にも字体を縮小せず、標準スクロールで全操作へ到達します。Windows/Access のタイトルバー・Ribbon・標準メッセージボックスはOS管理の外枠として別に記録します。

`tests/ui-contract.json` は仕様の部品表と確定条件から実測前に固定する独立期待値です。`python -B -X utf8 tests/ui_observe.py --run-id <runId>` は最終 `build/CareerManagement.accdb` を `.tmp` へ複写し、全5画面・両ページ・付属ラベルの実部品を列挙して属性と画面画像を採取します。96DPI基準の論理寸法と、実DPIでの物理pixel画像を区別します。属性一致だけでは描画や実キーを合格にせず、別のrender-reviewとkeyboard-operation証拠が揃うまで共通UI gateはFAILになります。

`python -B -X utf8 tests/ui_state.py` は、Form_Load中の認可・読込busy処理後の初期フォーカス、TabIndex、新規キー入力可／既存キー読取専用、7桁raw保持拒否、5回の再遷移を実Accessの専用コピーで回帰検査します。値代入・イベント呼出しの検査なので、実キーボード・Clipboardはrootの独立試験で確認します。ビルド時は過去の `build/test-results` を失効させ、今回候補の証拠だけを固定パスへ更新します。

初期化中は論理busyだけを保持し、まだ最初の描画が完了していないフォームでフッターボタンへフォーカスを移しません。通常処理では入力の物理保護を維持し、標準 `Form.GoToPage` で処理前のviewportを戻してから元のフォーカスへ復帰します。新規／既存の基本タブ、経歴選択、途中までスクロールした入力欄、検索一覧選択、初期化失敗後の再表示を検査します。独立契約1.1は初期原点・基本タブ・タブ見出しの可視位置を必須化し、別コピーで旧不具合を注入した負例が拒否されることも確認します。測定器が撮影直前にスクロールを強制補正して合格を作ることはありません。

`python -B -X utf8 tests/verify_current.py --run-id <runId>` は最終候補コピーの回帰を一括実行します。所有Accessの終了journalはPIDと起動UUIDで区別し、工程ごとの必要instance数・正常終了を確認します。PID再利用やjournal欠落を合格として見逃しません。

実キーによる入力・訂正・通常保存再読込・編集番号保護と、5画面の目視は、root の `build/test-results/native-ui.json` が実施した項目だけを対象候補SHA付きで記録します。Clipboard・IME変換・別DPI・利用者秘密による初期設定などの未実施を同記録で区別します。帳票の後続修正を含む新ACCDBへ過去の実入力結果を自動転用しません。

印刷の技術差分 PH07：Excel の Fit To は手動改ページを無視するため、詳細の Zoom=False 指定に対する Access 内の回避策として、A4 実幅から明示 Zoom を算出します。列幅を紙幅内へ置き、Zoom は100%以上、本文10.5pt以上、縦は章・案件の続きへ展開します。実 HPageBreaks と計画ページ境界が一致・安定しなければ出力を拒否します。採用根拠と元詳細のSHAは `build/generation/implementation-deviations.json` に記録し、業務仕様の承認と区別します。

ACCDB を直接編集できる信頼された DEMO 利用者向けです。ログインで強いファイルアクセス分離はできません。共有先障害・電源断、利用者受入・正式採点は未実施です。実印刷は今回の帳票 SHA とroot記録に従います。正式得点は null です。
