<!-- spec-meta: {"schema":"spec-md/1.0","documentId":"COBOL-DOC-AE86D9630E09","version":"8.3","path":"test-project1/spec/COBOL/規約/COBOL.md","sheets":[{"heading":"データ表現・ABI","kind":"GRID","sheet":"01_データ表現・ABI"},{"heading":"ビルド・配備・試験","kind":"GRID","sheet":"02_ビルド・配備・試験"},{"heading":"共通規約の具体化","kind":"GRID","sheet":"03_共通規約の具体化"}],"isolationProfile":"COBOL"} -->
# COBOL 開発規約

| 項目 | 内容 |
| --- | --- |
| 版数・改訂日 | 8.3／2026-10-25 |
| 対象方式 | COBOL |
| 適用 | 設計上の実装契約。製品コードの実装・コンパイルは未実施 |

開発入力：[学生検索詳細](../詳細仕様書/01_学生検索画面.md)／[学生登録詳細](../詳細仕様書/02_学生登録画面.md)／[共通実装](../共通/方式別/01_共通実装仕様.md)／[DB定義](../DB定義/SQLServer/01_DB定義書.md)／[方式別開発規約](COBOL.md)／[共通開発規約](開発規約.md)。

## データ表現・ABI

| 意味 | COBOL表現 | 規則 |
| --- | --- | --- |
| DB ID・版 | PIC S9(18) COMP-5 | ネイティブ符号付き64bitをビルド環境で静的検証。入力は19桁rawから0超～9223372036854775807を厳密検査 |
| 人数・戻りコード | PIC S9(9) COMP-5 | C int32_tとサイズ検証 |
| NULL標識 | PIC S9(4) COMP-5 | -1=NULL、0=値あり。空白と混同しない |
| 日付 | PIC X(10) | yyyy-MM-dd。NULL標識併用 |
| 時点 | PIC X(32)＋長さ | ISO 8601 UTC。DBにdatetimeoffset(7)で渡す |
| Unicode文字N字 | PIC X(4*N)＋実バイト長 | UTF-8最大バイト領域。業務長はコードポイントで別検査 |
| ASCIIコード・番号 | 正規化後PIC X(N)＋長さ | raw入力は4*Nで受け全角入力を正規化できるようにする |
| 接続・結果 | USAGE POINTER | INTEGERや文字列に詰め替えない |

例：氏名X(32)・住所各X(180)・備考X(480)・name_key X(640)、原カナ36文字はX(144)、保存カナ18文字はX(72)。LENGTHだけで日本語文字数を数えない。固定長領域の末尾空白を無条件に削除せず、実長を用いてDBへ渡す。

```cobol
01 DB-HANDLE USAGE POINTER.
01 WS-RETURN PIC S9(9) COMP-5.
COPY "ST-DB-REQUEST.cpy".
COPY "ST-DB-RESULT.cpy".
CALL "STDBOP" USING BY VALUE DB-HANDLE
    BY REFERENCE ST-DB-REQUEST ST-DB-RESULT
    RETURNING WS-RETURN
END-CALL.
```

C ABIは`int32_t STDBOP(void *connection, const ST_DB_REQUEST *request, ST_DB_RESULT *result)`。要求レコードはcommand_id固定12byte、parameter_count int32、最大40個のパラメーター構造（type_id、null_flag、byte_length、data_pointer）。結果はsqlstate[5]、native_error_code int32、affected_rows int64、cursor_handle pointer、error_class int32。COPYとCヘッダーを同じスキーマから生成し、sizeof/offsetの結合試験を行う。最大40は1SQL分、全候補数の上限ではない。

## ビルド・配備・試験

cobcはfree形式、COPYパス固定。CブリッジをPICでビルドしODBC・Unicode・暗号の依存版を固定してリンクする。実際のリンカー引数は配備Linuxのpkg-config結果とCIに固定。`cobc -x -free`による主プログラムと呼出プログラムのリンク構成をCIで確認する。例をそのまま完成コマンドとしない。

端末入口はText系の行/桁/属性と操作を実装する。GnuCOBOL/LinuxとODBC/C境界の設計基準を維持し、端末製品/ランタイム/IME/認証アダプターはQA-TEXT-COBOLで選定する。学生画面を旧CGI HTMLとして配備することを本改訂の達成としない。実行主体は非特権・接続先限定・タイムアウト管理とする。DB初期化・承認クラス投入後、コピー句とC構造のABI、UTF-8境界、プロセス終了を跨ぐ状態、2接続競合、監査失敗、確定後応答喪失を試験する。実装コード・実機試験の完成を本書は意味しない。

## 共通規約の具体化

本方式では[共通開発規約](開発規約.md)を適用し、業務ルールや項目長は[詳細仕様](../詳細仕様書/02_学生登録画面.md)と[DB定義](../DB定義/SQLServer/01_DB定義書.md)に一致させる。長さの計測単位はUnicodeスカラー値。処理系のバイト／コード単位の領域は余裕を確保し、業務最大長を拡大しない。

機能固有のイベントは機能別詳細、複数機能で使う接続・トランザクション・正規化・和暦・認可・確認・UI部品は方式別共通へ置く。コピーした定義の修正は同じ仕様IDを持つ文書へ同時に反映する。デザイナー生成物、業務ロジック、テスト資源を分ける。

ビルド設定・ライブラリ版・DB設定・文字コード・暦定義版を方式プロファイルに記録する。現行の採用版は仮定を維持し、勝手な最新版への変更は行わない。API署名や型を変更する際は両画面、共通、DB、試験条件を同一改訂で直す。

### Text系の画面・入力アダプター規則

通常画面は27行×132桁、左上(1,1)、半角1/全角2の設計値。P保護/U入力/R見出し/Eエラー属性、項目ID、実バイト長、表示開始位置を端末アダプターへ渡す。実機がこの格子を確保できない場合は適合エラーを示し、入力や主要操作を黙って削らない。全文のUnicodeを単純なセル数へ切捨てず、結合文字/補助文字はコードポイント編集の完全往復を検証する。

F4候補/F8全文/F1説明/Tab移動/F12取消と機能別操作キーを共通割当とする。端末エミュレーターがキーを奪う場合の代替キーはQA-TEXT-COBOLで決め、画面へ表示する。Enterだけで登録/削除/別人続行を確定させない。確認は既定N、明示Y+F5でサーバー保持の確認目的だけを続行する。HTML資料のpre/spanと製品の端末制御を区別し、PNGや別HTMLを正本へ置かない。旧CGI実装の改修・新端末実装・ビルド・実DB・端末試験は今回未実施。
