<!-- spec-meta: {"schema":"spec-md/1.0","documentId":"DOC-E461E85A4485","version":"7.0","path":"test-project1/docs/開発規約/AS400_RPG.md","sheets":[{"heading":"RPG型・データ構造","kind":"GRID","sheet":"01_RPG型・データ構造"},{"heading":"ビルド・配備・エラー","kind":"GRID","sheet":"02_ビルド・配備・エラー"},{"heading":"共通規約の具体化","kind":"GRID","sheet":"03_共通規約の具体化"}]} -->
# AS400／RPG 開発規約

| 項目 | 内容 |
| --- | --- |
| 版数・改訂日 | 7.0／2026-10-11 |
| 対象方式 | AS400／RPG |
| 適用 | 設計上の実装契約。製品コードの実装・コンパイルは未実施 |

開発入力：[学生検索詳細](../../spec/詳細仕様書/AS400_RPG/01_学生検索画面.md)／[学生登録詳細](../../spec/詳細仕様書/AS400_RPG/02_学生登録画面.md)／[共通実装](../../spec/共通/方式別/AS400_RPG/01_共通実装仕様.md)／[DB定義](../../spec/DB定義/Db2_for_i/01_DB定義書.md)／[方式別開発規約](AS400_RPG.md)／[共通開発規約](../開発規約.md)。

## RPG型・データ構造

| 意味 | RPG型・表現 |
| --- | --- |
| ID・版 | int(20)の符号付き64bit。DDS非表示転送は19桁文字から検査して変換 |
| 人数・ページ | int(10)、定員NULL標識を別保持 |
| NULL標識 | int(5)、-1=NULL／0=値あり。SQLホスト変数へ併記 |
| 日付 | date、内部ISO日付char(10)と変換。生年月日の画面入力は和暦の分割項目 |
| 時点 | timestamp、UTCとして運用し表示時に日本時間へ変換 |
| 業務Unicode文字N | vargraphic(2*N) CCSID1200相当のUTF-16領域。scalar数Nを別検査 |
| ASCIIコード | varchar(N)、数字・大文字英字等を検証 |
| SQL真偽 | smallint 0/1、RPG側はindへ明示変換 |

`StudentWork`はqualified DS。物理列snake_caseをcamelCaseへ対応付けたサブフィールドを持つ。SQL NULL可の各項目について同名＋Indのint(5)を持ち、空文字・0・最小日付をNULLの代替にしない。API署名はStSaveStudent(work const、hints const、expectedVersion、confirmation const、result)とし、resultはResultKind、MessageId、FieldErrors、StudentId、RowVersionを持つ。

## ビルド・配備・エラー

DDSをCRTDSPF、SQLRPGLEをCRTSQLRPGI／モジュール→サービスプログラムとしてビルドし、COPYとバインダーシグネチャーを固定する。STUDAPP/STUDPGMのライブラリーリスト、実行activation group、SQL命名・日付形式・照合順・CCSIDを配置資料で固定。ジャーナルレシーバー・ジャーナル作成、全5表＋制御表へのジャーナル開始を検証してからコミットメント制御を開始する。

SQLSTATE23505は番号／マスタ重複、23503は参照、02000は呼出目的に応じ行なし、ROW_COUNT=0は版または不在、40xxx・ロック待ちは再確認、その他は受付番号付き共通エラー。SQLCOD<0で後続更新を続けない。

STUNICODEは製品標準で存在するという仮定ではなく、実装が必要な補助サービス。変換不能文字の保持・Unicodeエスケープ補助・全長編集・C ABIを稼働条件として試験する。実機未検証のためコンパイル済み・文字往復確認済みとは記載しない。

## 共通規約の具体化

本方式では[共通開発規約](../開発規約.md)を適用し、業務ルールや項目長は[詳細仕様](../../spec/詳細仕様書/AS400_RPG/02_学生登録画面.md)と[DB定義](../../spec/DB定義/Db2_for_i/01_DB定義書.md)に一致させる。長さの計測単位はUnicodeスカラー値。処理系のバイト／コード単位の領域は余裕を確保し、業務最大長を拡大しない。

機能固有のイベントは機能別詳細、複数機能で使う接続・トランザクション・正規化・和暦・認可・確認・UI部品は方式別共通へ置く。コピーした定義の修正は同じ仕様IDを持つ文書へ同時に反映する。デザイナー生成物、業務ロジック、テスト資源を分ける。

ビルド設定・ライブラリ版・DB設定・文字コード・暦定義版を方式プロファイルに記録する。現行の採用版は仮定を維持し、勝手な最新版への変更は行わない。API署名や型を変更する際は両画面、共通、DB、試験条件を同一改訂で直す。
