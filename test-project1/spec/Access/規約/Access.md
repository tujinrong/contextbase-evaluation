<!-- spec-meta: {"schema":"spec-md/1.0","documentId":"ACCESS-DOC-5AA4A3B1E208","version":"8.4","path":"test-project1/spec/Access/規約/Access.md","sheets":[{"heading":"VBA型・NULL・Unicode","kind":"GRID","sheet":"01_VBA型・NULL・Unicode"},{"heading":"セキュリティ・配置・稼働条件","kind":"GRID","sheet":"02_セキュリティ・配置・稼働条件"},{"heading":"公式参照資料（2026-10-10確認（前版からの参照。今回全URLの再確認は未実施））","kind":"GRID","sheet":"03_公式参照資料（2026-10-10確認（前版からの参照。"},{"heading":"共通規約の具体化","kind":"GRID","sheet":"04_共通規約の具体化"}],"isolationProfile":"Access"} -->
# Access 開発規約

| 項目 | 内容 |
| --- | --- |
| 版数・改訂日 | 8.4／2026-10-25 |
| 対象方式 | Access |
| 適用 | 設計上の実装契約。製品コードの実装・コンパイルは未実施 |

開発入力：[学生検索詳細](../詳細仕様書/01_学生検索画面.md)／[学生登録詳細](../詳細仕様書/02_学生登録画面.md)／[共通実装](../共通/方式別/01_共通実装仕様.md)／[DB定義](../DB定義/Access/01_DB定義書.md)／[方式別開発規約](Access.md)／[共通開発規約](開発規約.md)。

## VBA型・NULL・Unicode

| 意味 | VBA／ACE表現 | 制約 |
| --- | --- | --- |
| 学生・クラス・履歴ID | AutoNumber(Counter)／VBA Long | 正の32bit、上限2,147,483,647。採番・版の上限到達はエラー、欠番可 |
| 外部キー・版・人数・表示位置 | Long | VBA Integerは16bitなので使用しない。Office64bitでもLongは拡張しない |
| 任意の数値・文字・日付 | VariantでNullまたは型付き値 | IsNullで判定。Nz(値,0)でNullの意味を失わせない |
| 生年月日・入学日・終了日 | TEXT(10)／ISO年月日String | 生年月日等は業務範囲1900年～業務日、コード日付は9999年まで。固定ISO文字列で日付と時点を分離する |
| 作成更新・実行・有効期限の時点 | Date/Time／VBA Date | UTCとして保存、表示で日本時間。信頼できる時計から取得 |
| 業務文字N文字 | UTF-16 String、物理領域は最大2Nコード単位 | サロゲートペアを1業務文字として数え、不正ペア拒否 |
| APIのポインター | LongPtr | PtrSafe宣言。文字数・戻りintはLongと区別 |
| 真偽 | Boolean／YESNO | True=-1、False=0。SQLはTrue/Falseを明示 |

modJapaneseDateは年・月・日を分割し、うるう年規則と月末日を検査して10文字へ組み立てる。DateSerialによる範囲外日の繰上げを受理しない。ISO日付の比較は固定10文字のバイナリー比較で可能。空の任意日はNull。日時と年月日を混同しない。

modUnicodeはWindows NormalizeStringのNFKCを呼び、前後空白、カナ対応、英字大文字、scalar数を処理する。StringのLenだけを業務文字数としない。StrConv/UCaseだけで共通正規化が満たせたとみなさず、英字大小対応をカルチャー非依存に固定して共通ベクトルで検証する。NormalizeStringはUTF-16ポインターとコード単位長を渡し、出力バッファ不足時の再確保と異常戻りを処理する。[A-04]

### 任意の複合参照

続柄未選択は分類とコードを共にVariant Nullで扱う。両列のRequired=False、AllowZeroLength=Falseと行内ValidationRule、参照整合付きRelationを同時に定義する。[Access DB定義](../DB定義/Access/01_DB定義書.md)の生成手順・最小再検証を稼働条件とする。DAO3201を握りつぶす、FKを解除する、緊急連絡先を必須化する方法では解決しない。

## セキュリティ・配置・稼働条件

本案は信頼された職員グループ向けの評価構成。ACCDBでは利用者別DBセキュリティを前提にできず、ファイル書込み権限を持つ利用者の直接改変をVBAの役割判定で防げると説明しない。ACCDE化、起動時フォーム固定、ナビゲーション非表示、Shiftバイパス無効は配布・操作制限であり完全な権限境界ではない。[A-05]

強い閲覧者／担当者／管理者分離が必要な本番では、AccessをフロントとしてサーバーDBまたはAPIへ変更し、サーバー側で権限・検証を強制する追加設計を承認する。本案のACE構成をそのまま強い認証分離要件に適合済みとしない。

利用者の最新版指示により、ローカル単体評価の配布成果は StudentManagement.accdb の１ファイルとする。画面・VBA・業務表・制御表・初期５分類70コード・評価用役割表を同じファイルへ内包し、外部リンク表・外部設定ファイルを必要としない。認証アダプターは GetUserNameW で取得した Windows 主体と内包 t_app_role をパラメーター付き DAO 読取りで照合する。秘密情報は格納せず、環境変数を主体証明にしない。保存 Workspace は CurrentProject.FullName のみを開き、利用者入力で接続先を変更しない。役割表を直接編集できる利用者への強い境界ではない。

32/64bitの各Office用にVBA API宣言を検証し、該当環境でコンパイル・ACCDB生成を行う。参照設定の欠落、DAO対応、NormalizeString、GUID生成、UTC時計を確認する。バックアップ・最適化修復・単体ファイル差替えは運用手順で調整し、通常の保存中に実施しない。TEMP空き容量・成果ファイル容量を監視する。実装・実機試験未実施のため、性能と競合耐性は共通試験を実行して確認する。

## 公式参照資料（2026-10-10確認（前版からの参照。今回全URLの再確認は未実施））

| ID | 資料 |
| --- | --- |
| A-01 | Microsoft ListBox.RowSourceType：ユーザー定義の供給関数 https://learn.microsoft.com/en-us/office/vba/api/access.listbox.rowsourcetype |
| A-02 | Microsoft DAO Workspace.BeginTrans：Workspace範囲の確定・取消 https://learn.microsoft.com/en-us/office/client-developer/access/desktop-database-reference/workspace-begintrans-method-dao |
| A-03 | Microsoft DAO Recordset.LastModified：同じRecordsetで追加・変更した行のbookmark https://learn.microsoft.com/en-us/office/client-developer/access/desktop-database-reference/recordset-lastmodified-property-dao |
| A-04 | Microsoft Win32 NormalizeString：UTF-16の正規化 https://learn.microsoft.com/en-us/windows/win32/api/winnls/nf-winnls-normalizestring |
| A-05 | Microsoft Access file format：ACCDBの権限制約 https://support.microsoft.com/en-us/access/which-access-file-format-should-i-use |

上記は製品機能の確認資料。非連結フォーム、ゲート方式、物理型、検索時のメモリーソート、セキュリティ適用条件は本設計の選択であり、Microsoftの推奨完成構成として引用しない。

## 共通規約の具体化

本方式では[共通開発規約](開発規約.md)を適用し、業務ルールや項目長は[詳細仕様](../詳細仕様書/02_学生登録画面.md)と[DB定義](../DB定義/Access/01_DB定義書.md)に一致させる。長さの計測単位はUnicodeスカラー値。処理系のバイト／コード単位の領域は余裕を確保し、業務最大長を拡大しない。

機能固有のイベントは機能別詳細、複数機能で使う接続・トランザクション・正規化・和暦・認可・確認・UI部品は方式別共通へ置く。コピーした定義の修正は同じ仕様IDを持つ文書へ同時に反映する。デザイナー生成物、業務ロジック、テスト資源を分ける。

ビルド設定・ライブラリ版・DB設定・文字コード・暦定義版を方式プロファイルに記録する。現行の採用版は仮定を維持し、勝手な最新版への変更は行わない。API署名や型を変更する際は両画面、共通、DB、試験条件を同一改訂で直す。
