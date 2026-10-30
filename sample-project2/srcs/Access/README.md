# Access 社員経歴管理

Windows 11 / Microsoft 365 Access・Excel 64bit / VBA7 / DAO・ACE の単一ACCDBです。5画面、6機能、5表48列を持ち、社員と全経歴を一つのトランザクションで明示保存します。社員削除はなく、経歴除去は全体保存で確定します。

今回のrunIdは `sp2-ui-regenerate-20261029`、採用詳細はDQA-UI08/09/10を含む現版です。配布候補は `build/CareerManagement.accdb`、正本ソースは `src/`、DB構造は `database/`、正式試験は `tests/`、検査記録は `build/test-results/` に置きます。日本語VBA正本 `src/modules/*.bas`・`src/classes/*.cls` はCP932（Windows版Shift-JIS、BOMなし）、native exportの `src/forms/*.txt` はBOM付きUTF-16、文書・Python・JSONはUTF-8です。読込みは種類ごとに明示し、一括変換しません。再構築定義 `src/forms/definitions.py` は原仕様/試験期待値を読みません。

## 現在の品質状態

候補は **UI_NOT_VERIFIED** として扱います。コンパイル、全VBAクラス初期化、業務API、データ保全、帳票API/PDF、source-only再構築の実施結果は対象ACCDB/コード/試験SHAに結び付けて記録します。構造/属性/APIのPASSを実画面/実キー/印刷/正式受入へ読み替えません。

Windowsロック中はnative入力を停止します。F03先頭可視社員IDの独立捕捉・復帰、TextBox原入力の末尾空白保持、未採用入力の標準補助面を実装しています。旧候補の実操作結果を現在のACCDBへ転記せず、現在版の実表示・複数Pending・候補選択・取消/キーは別に検査します。特に同値候補のマウス確定は未完で、Click/ListIndexだけで採用しません。IME/clipboard/他倍率、全状態の標準Dialog、実Excelプレビュー/実印刷も未検証です。必須UI gateの欠落/FAILを回避せず、正式outputs manifestは同gateが揃うまで未確定です。正式採点はnullです。

## 再構築とデータ保全

Python 3.11 x64・pywin32311・既存Office64bitと、VBAプロジェクトAutomationが許可された環境を使います。以下はこのsourceRootを作業ディレクトリーにした例です。途中/キャッシュは `.tmp/` に隔離し、Pythonは `-B` で起動します。

```powershell
python -B -m pip install --no-user --target .tmp/python-deps pywin32==311
python -B -X utf8 tools/build.py --preserve-existing build/CareerManagement.accdb
```

既存ACCDBはロックがないことと開始SHAを確認して所有stagingへコピーし、5表全列/全行を型・Null・ID・監査・版・資格情報込みのdigest/schema fingerprintで前後比較します。Forms/VBAだけを差し替え、seedや資格情報の初期化は行いません。元ファイル変更/未知Form在庫/データ差分は停止条件です。`tools/data_integrity.py` は所有 `.tmp` コピーだけを読取り、原文/資格情報をログへ出しません。

既存データを保った公開は、候補と検査範囲を明示した上で同じコマンドへ `--publish-candidate` を付けます。元最終ファイルのSHAが開始値と一致する場合だけ固定先へ移動します。UI未検証候補の公開はUI合格や正式manifest確定を意味しません。

新規・source-only隔離再構築は、既存ACCDBのない独立フォルダーで次を使います。fresh DEMO初期化から既存最終ACCDBを置き換えることは拒否します。

```powershell
python -B -X utf8 tools/build.py --demo-credentials --publish-candidate
```

新規だけSP2-DEMO-01 v1.1（基準業務日2026-10-27、3分類/9コード/2利用者/3社員/3経歴）を投入します。通常の公開DEMO認証は `admin / 123`（ADMIN）と `staff / 123`（STAFF）、パスワード3～128 Unicodeスカラー、salt付きPBKDF2-SHA256/600000反復です。既存データ保全では検証情報/失敗回数/ロックも変更しません。通常起動でseed/resetはしません。明示の対話初期設定はfresh staging専用で、CLI入力と実フォーム入力の検証を区別します。

コンパイルは `RunCommand(126)` / `Application.IsCompiled=True` →全 `src/classes/*.cls` 実初期化probe→probe除去→再コンパイル/Trueを必須にします。SysCmd603を成功判定にしません。所有Office PID/終了値とApplication Errorを記録し、利用者のOfficeを接収/終了しません。VBEへの非往復文字列はChrW化してUnicodeを保持します。

## UIと保存

標準未連結Form/Control、灰色背景・黒字・白入力・矩形のクラシック外観、全アプリ管理文字Yu Gothic UI11ptを採用します。タイトル/領域見出し/主操作は太字、Fontを持たないCheckBox記号とOS管理Dialog子文字は理由付き別範囲です。付属Label/列見出し/Tab/Pageの字体を省きません。

F04はHeader2400twipにタイトル/親社員識別/高さ900の標準Tabと空Page2つを置き、入力群はDetail7920の実親/論理Page所属を分けます。Footerの保存/取消は全体操作です。経歴一覧6300twipと詳細11580twip、氏名3900/カナ4950/日付2250twipを維持し、Header/Detail/Footer各原点を使います。実clientと1366×768静的モックを同一視しません。

F03全文補足は初期330twip/非表示、選択後1980/Detail9450へ展開し、readonlyでもTab/全文/コピーへ到達できる設計です。文字を縮めず、明細や全文は内部/Detailスクロールを使います。F03条件のraw表示/accepted code/Pending、適用済条件/結果/選択/focusを別保持し、取消は検索0、保存成功だけraw再検査/再検索です。

未採用Combo入力は、部署/在籍/役割/分類に固定対応する6個の標準TextBoxと6個の付属Labelで表示・編集します。元Comboの採用コード・候補集合・BoundColumn/LimitToListを維持し、補助欄の編集だけでコードを採用しません。通常は補助面を隠し、各Pendingと可視Pageの条件が成立した面を同時表示します。候補操作・同値マウス選択の完成/実測は検査記録の範囲で判断します。

番号/年月/人数等はString rawを保持し、Password以外のInputMask/Formatを空にします。検索/反映/保存で中央検査し、不正入力から取消へ届くようにします。ComboはNotInListでNewDataを別保持し、Undoは当該Control表示だけに限定します。未反映/予約を全体保存で黙って落とさず、変更破棄は対象/範囲を表示して確認します。busyのfocus所有Controlを先に無効化せず、成功/失敗後の属性とfocusを復元します。

## Excel帳票

保存済み1社員の一貫Snapshotから専用Excelで2シートを生成し、保存先選択後に再認可/再確認して完成名へ移動します。取消/失敗で不完全物を完成と表示せず、旧ファイルを先に削除しません。全件全文/元LF/型/式/外部リンクを保存再Openで検査します。

A4縦、余白15mm/ヘッダー・フッター7mm、Zoom100/FitTo無効、24列の実幅20～21pt（総480～504pt）、各頁行高720pt以内と手動改ページ/継続見出しを採用します。本文セルメイリオ10.5pt/見出し11pt/表題18pt、Footerだけ整数11ptです。小数Footerコードの印字崩れと数字先頭名のサイズ誤解釈を限定probeで確認し、サイズの後へFontコードを置いて氏名と区切ります。氏名40字は先頭1行、残り情報は次行です。小試験PDFやAPI設定を製品帳票/実印刷PH07の合格にしません。

## 検査入口

リポジトリー完全版では、所有コピーだけで業務APIと境界値を検査します。

```powershell
python -B -X utf8 tests/run.py --cycle 1
python -B -X utf8 tests/run.py --cycle 2
python -B -X utf8 tests/run.py --cycle 3
```

`--artifact` / `--manifest` / `--output-root` で未公開stagingを明示して検査できます。Value代入/Application.Runは業務API/状態設定であり、物理キー・貼付・IMEの証拠ではありません。native操作はrootのcomputer-useと `tests/native-cua-session.mjs`、範囲は `tests/native-ui-checklist.md` の現SHAへ対応させます。ロック画面越しの操作や独自の入力注入は行いません。

`tests/ui-contract.json` は最終仕様のID/版/SHAから独立固定した期待値で、170部品/139Control/140字体/658rule・16surfaceの9カテゴリと個別状態を持ちます。実測値を期待値へ転記しません。新改訂/新ACCDB/測定コード変更で旧結果を失効させ、未観測・未実装をPASSへ集約しません。source-only ZIPは原仕様・正式tests/期待値・検査結果を含まず、明示した4production helperだけでfresh再構築します。配布再現と仕様に対する正式受入は別です。
