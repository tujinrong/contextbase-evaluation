# Windows Text 実装記録

入力はCOBOL自身のWindows/no-auth仕様を含む凍結セット。`build/input-manifest.json` は方式内44文書、全体ルーティングを含む `build/generation/inputs.json` は60入力です。版・SHAはその記録を正とします。他方式の仕様/コードを入力にしていません。

## COBOLとCの境界

`STMAIN` が起動/終了、要求連番、画面、固定action集合、DB業務dispatchを管理します。`STAUTH` はサンプルsessionの有効性を確認し、固定actor/roleを取得します。認証処理ではありません。`STRENDER` は固定行桁/属性/値を渡し、`STEVENT` がraw同期・キーから業務操作への対応・候補/エラー/確認状態を管理、`STTEXTREQ` が名前・重複・許可集合・要求/期待版を検査します。HTML/HTTP入口は製品COBOLから除去しました。

`bridge/windows_terminal.c` は汎用Console/Unicode入力/表示/全文補助のみ。業務SQL・検索条件・候補集合・保存・権限/理由/確認目的を判断しません。全数値は原則int32参照、ST_VALUEはlength:int32/null:int16/pad2/data1024で1032byte。raw64slotは変更せず、画面/action/requestID/expectedRevision/window/sessionは別 `ST-TEXT.cpy` envelopeへ保持します。

`STTERMOPEN(cols,rows)`、`STTERMBEGIN(panelId,title)`、`STTERMADD(id,row,col,width,height,flags,maxScalars,value)`、`STTERMNEXT(key,focus)`、`STTERMGET(id,value,changed)`、`STTERMFULL(raw,title,flags,maxScalars)`、`STTERMCLOSE()`。座標1-based、P0/U1/R2/E4/保護focus8、NEXT focusはin/out、key下16bitVK・Shift0x10000/Ctrl0x20000/Alt0x40000。通常0成功/負失敗、FULLは1Apply/0Cancel。全GET同期後にBEGINし、未変更/保護rawを表示文字から再構成しません。

panelIdは画面モード・panel種別・確認目的・候補分類から作り、同一通常frameとmodal境界を区別します。FULL F2通常/コードポイント、F5raw反映のみ、F12完全取消、Enter補助内検査。通常元号M/T/S/H/Rはcanonical識別値と分離し、変更時だけ対応付けます。F8は元rawを直接扱います。

## 業務と状態

既存STNORM/STVALID/STRULES/STDUP/STSAVE/STDELT/STAUDITと固定SQL38コマンド、7物理表・5分類70コードを維持しました。STMLOOKは旧HTML option出力を6件の値/名称/選択可否モデルへ置換し、全候補走査・現在値保持・有効期間・年度/学年連動はCOBOLへ残しています。STREFは既存CLASS-EDITで人数/定員・クラス名称を取得します。

SearchContextに表示窓と選択IDを追加し、検索raw/pendingと実行済み条件を分離します。Editorの原入力/正規化snapshot、確認draft/pendingAction、Search/Editor CAS、10分確認、理由再訂正/取消と保存時の再検査を維持します。確認中のキーはCONFIRM/CANCEL、専用パネル内の補助操作だけへ制限します。MAINのMENUはDB接続失敗時でもローカル終了できます。

`STMAINT` もsample sessionを開始/終了し、固定actorを監査に使用します。DB側 `student_admin` 所属は別に確認し、no-authという指定でDB権限を緩めません。

## 証跡の限界

ビルドはWindows x64 GnuCOBOL→C変換＋同bit Cリンク、exeの配布hash付き、runtime DLLは外部準備。共通境界と新Text制御/Win32 synthetic testsを分けて記録します。旧HTTP decoder互換テストと旧HTML fixtureは今回端末受入を証明しません。実glyph/IME/キー、実SQL/crypto状態表・実時間期限/競合・本番受入・正式採点は未実施です。
