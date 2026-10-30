# Access source-only 再構築

このフォルダー内のソースだけからACCDBを構築します。Windows、Python 3.11 x64、pywin32 311、Microsoft 365 Access/Excel 64bit、VBAプロジェクトAutomationが許可された環境が必要です。原仕様・試験期待値・検査結果はsource-only ZIPに含みません。

空の隔離フォルダーへZIPを展開し、同フォルダーを作業ディレクトリーにします。

```powershell
python -B -m pip install --no-user --target .tmp/python-deps pywin32==311
python -B -X utf8 tools/build.py --demo-credentials --publish-candidate
```

新規DEMOだけadmin/123とstaff/123、基準業務日2026-10-27のSP2-DEMO-01 v1.1を初期化します。既存の最終ACCDBがある場合、fresh公開は停止します。既存利用者・社員・経歴・コードを保持する更新では明示的に次を使い、候補の検査後に同コマンドへ`--publish-candidate`を指定します。実行前に所有者へ利用を停止してもらい、ロックのない対象だけを指定します。

```powershell
python -B -X utf8 tools/build.py --preserve-existing build/CareerManagement.accdb
```

保全更新は元ファイルのSHAを固定し、所有stagingコピーのForms/VBAだけを置き換えます。業務5表の全列・全行をNull/型/ID/版/資格情報込みで前後比較し、seedや資格情報を初期化しません。元ファイル変更や差分があれば公開しません。中間ファイルは`.tmp/`、最終ACCDBとseed-manifestは`build/`です。

RunCommand(126)/IsCompiled、全11クラス初期化、probe除去後の再コンパイルを行います。所有Accessが正常終了したことまで確認します。利用者のOfficeプロセスは終了しません。

現在のリリース状態は**UI_NOT_VERIFIED**です。F03の先頭可視社員IDの独立捕捉・復帰と、6組の未採用入力補助面を実装しています。同値候補のマウス確定は未完で、現在版の実表示/実キーの合格は未確定です。実キー・IME・clipboard・表示倍率・Header/Tab/Footerの通常遷移・Dialog・実Excelプレビュー/紙印刷の受入は別途必要です。ビルド成功、属性照合、業務API、PDF、ZIP再現は実画面検査や正式受入を意味しません。正式採点はnullです。

日本語のVBAファイルはCP932です。ビルドはCP932を厳密に復号し、全非ASCIIリテラルを正確なUTF-16/ChrW式でVBEへ輸送します。日本語版OfficeでもWindows ACPが932とは限らないため、ホストの既定ANSIに依存しません。フォームのUTF-16 BOMと業務データのUnicodeは保持します。文字コードの検証結果と画面全体の合格は別です。タイトル/入力高の新規約はAgentへ反映済みですが、既存画面の再設計・再生成は別工程で実施します。
