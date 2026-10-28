<!-- spec-meta: {"schema":"spec-md/1.0","documentId":"COBOL-COM-COBOL-WINDOWS","version":"1.1","path":"sample-project1/spec/COBOL/共通/方式別/02_Windows実行環境.md","sheets":[{"heading":"利用者指定と適用範囲","kind":"GRID","sheet":"01_利用者指定と適用範囲"},{"heading":"実行環境と責務","kind":"GRID","sheet":"02_実行環境と責務"},{"heading":"入力と描画","kind":"GRID","sheet":"03_入力と描画"},{"heading":"全文補助とキー","kind":"GRID","sheet":"04_全文補助とキー"},{"heading":"主体とセッション","kind":"GRID","sheet":"05_主体とセッション"},{"heading":"暗号化状態とDB","kind":"GRID","sheet":"06_暗号化状態とDB"},{"heading":"検証と残る事項","kind":"GRID","sheet":"07_検証と残る事項"}],"isolationProfile":"COBOL"} -->
# Windows実行環境・認証なしサンプル

版1.1／2026-10-25。ユーザー指定に基づく確定前提を次回の仕様生成へ継承する。設計契約と実装・検証状態を分け、各状態は対象版・ハッシュ付きの実行記録で判断する。

## 利用者指定と適用範囲

| 項目 | 契約 |
| --- | --- |
| 指定1 | Windowsで実行できる環境を想定する |
| 指定2 | サンプルのため、認証はしない |
| 選定 | Windows x64／GnuCOBOL 3.2／同bit C／Windows標準Console・Win32 Unicode W API／Windows ODBC Driver18 |
| 認証なし | 本サンプルはログイン/Windows token検証をしない。実行側が固定actor=sample-user、固定操作role=Administratorを設定し全サンプル操作を確認する。利用者別認証・認可適合、本番採用の承認を意味しない |
| 適用例外 | 共通01/02、CHK-023、一般の認証・権限表、認証主体/認証セッションという互換名は、本サンプルでは固定actor/roleと実行側発行接続sessionへ対応する。通常の本番規則自体は削除しない |
| 維持 | 検索4条件・8論理一覧項目、20/50/100取得頁と4件表示窓、編集REG全34項目、27×132の配置、raw/保存長、日付、19/18保存入力、DB物理表・制約・確定・監査を変更しない |

次回仕様生成で継承する確定前提：対象はsample-project1/COBOLのWindows認証なしサンプルである。Windows x64／GnuCOBOL 3.2／同bit C／Windows標準Console・Win32 Unicode W API／27行×132桁／Windows ODBC Driver18を既定とし、固定actor=sample-user・固定操作role=Administrator、ログインなしを継承する。利用者から変更指示がない限り未選定・認証元未定へ戻さず、他方式へ認証なしの前提を拡張しない。

DB接続権限・TLS・入力検査・期待版・同時保存・監査・確定境界は維持する。必要な処理系・Unicode/暗号等のランタイムは外部供給とし、採用版・必要DLL・配布条件を実行手順へ明記する。入力値の64スロットと、1値1032byte（int32実長・int16 NULL標識・2byte予約領域・raw1024byte）の既存ABI、65536byteの入力メッセージ上限を維持し、値の切捨てやNULLと空文字の同一化を行わない。

これらは設計上の前提であり、実装・ビルド・実DB・実glyph/手動IME・端末実操作・本番受入・正式採点の完了状態とは別に管理する。次回は対象版・ハッシュ付きの記録から実施範囲を判定し、未実施や過去のPASSを今回の合格へ読み替えない。入力・QA・正式試験コード・fixtureを保全し、仕様正本はspecRootへ、最終記録はsourceRoot/build/spec-generation/の固定先へ更新する。中間はsourceRoot/.tmp/で処理し、.tmp/はGitから除外する。過去結果を別名で累積せずGit履歴を使用する。

## 実行環境と責務

| 境界 | 責務 |
| --- | --- |
| Consoleアダプター | 起動/終了、表示域検査、文字とキーの取得、行桁/属性/カーソル描画、汎用F8全文補助をCのWin32 W APIで実装する。SCREEN SECTIONや端末の既定キー動作へ推測委譲しない |
| COBOL | STMAINがaction/名前付き入力を検査し各業務へ振分ける。STRENDERはfieldID・行桁・表示幅・属性・raw/実長/NULLを渡す。F4候補・エラー一覧・確認目的・DB候補取得・保存はCOBOLが管理する |
| 技術ABI | 数値はint32相当の参照渡しを基本とし、ポインター・int64・COPY/C構造のsizeof/offsetを同bitで検証する。汎用値レコードはint32実バイト長（offset0）＋int16 NULL標識（offset4）＋2byte予約padding（offset6）＋UTF-8 raw1024byte（offset8）の総1032byte。NULL標識は-1/0を使用し、外側のint32参照渡し引数と混同しない。具体関数名・リンク引数は方式内実装記録へ固定する |
| Windows部品 | GetConsoleMode/GetConsoleScreenBufferInfo等で実表示域を確認し、ReadConsoleInputWでイベントを取得、WriteConsoleOutputW等で固定セルを描画する。API採用とglyph/IMEの実機適合を区別する |
| ビルド | Windows x64のGnuCOBOL 3.2・同bit C・Windows ODBC Driver Manager/Driver18を使用。Linux用PIC/unixODBC/pkg-configを必須にしない。Unicode/暗号の依存版とDLL配布条件を記録する |

## 入力と描画

| 対象 | 契約 |
| --- | --- |
| 配置 | 座標は1-based、通常27行×132桁。実表示域不足は起動/入力継続不可を通知し、縮小・欠落・自動折返しで代替しない |
| 属性 | P=保護、U=編集、R=保護見出し、E=エラー装飾。エラー装飾だけで編集可能にはしない。ラベル/見出しは非focus、保護されたデータ値は必要に応じTab/F8可・編集不可を明示する |
| 属性の受渡し | P=0、U=1、R=2、E=4。保護データ値のfocus/F8可は8。UとEの組合せは編集可、E単独や保護focus8は編集不可。role/編集可否を表示色だけで実装しない |
| Raw | UTF-8原文字列/実バイト長/NULLを別に渡す。NULL=-1かつ長さ0と、空文字=NULL0かつ長さ0を区別する。未変更/保護値を表示用文字列から再構成しない |
| 物理境界 | 値1024byte超、不正UTF-8、NUL、実長と領域の不整合を拒否し切り捨てない。メッセージ全体65536byteを維持。業務スカラー長は従来の各項目上限で別検査する |
| 名前付き要求 | 画面ID、action、要求ID、contextId/期待Revision等の制御情報と、名前付きraw/実長/NULLを分離する。actor/role/sessionを端末入力項目として受付けない。action毎の許可名を検査し、未知/廃止名は空/nullでも拒否、単一項目重複は拒否。SEARCHで反復可能なのはstatusCodeだけ |
| 安全な表示 | ESC等の制御列を端末命令として送出しない。原rawは保持し、安全な注記またはF8コードポイント表示へ渡す。保存禁止文字は従来の業務検査で拒否し、表示窓で代替保存しない |

## 全文補助とキー

| 操作 | 契約 |
| --- | --- |
| 通常パネル | Tab/Shift+Tabで編集欄とfocus可の保護データ値を移動。F4候補、F8全文、F1説明、F12取消。通常Enterは入力検査/候補操作だけで、登録/削除/確認の確定をしない。編集F5はCREATE/UPDATEに対応する |
| FULL開始 | 原項目raw/NULL、title、編集/保護属性、rawスカラー上限を渡し補助draftへ分離する。単なる表示幅で原値を切り捨てない。単行欄の隠れた末尾、補助/結合文字へ到達できることを適合検査する |
| F2 | 通常文字/コードポイント列を明示切替する。通常のU+0041等の文字列を勝手に解釈しない。切替は補助draftを保持し、不正なコードポイント列は同欄に保持して通知する |
| コードポイント | U+XXXX形式の空白区切り列。Unicode scalarだけを受け、10FFFF超・surrogate単体・不完全列を拒否する。LFはU+000Aで明示入力し、画面の折返しをLFとして保存しない |
| FULL Enter | 補助内の入力検査のみ。LFの自動挿入、原項目への反映、DB保存は行わない。備考/理由のLFはコードポイント入力で扱い、単行項目に含むLFは保存側の従来制約で拒否・raw保持する |
| FULL F5 | 編集可かつUTF-8/容量/rawスカラー上限を満たす場合だけ原項目へ反映し、DBへ保存しない。上限超過・不正値は補助draft/入力欄へ保持して通知し、無通知で捨てない |
| FULL F12 | 補助変更だけを取消し、原項目のbytes/実長/NULLを完全に保つ。未変更Applyも同bytesを保つ。保護参照は入力/Apply不可で、終了時に原値を変更しない。原パネルのfocus/カーソルへ戻す |
| 候補・確認 | F4は6件×2行、エラー/重複/削除/破棄は専用パネルを維持。候補/エラー選択はCOBOLへ返して検査する。確認はN/取消既定、明示Y+F5で保持済み目的だけ続行。背景の保存キーを通さない |

## 主体とセッション

| 項目 | 契約 |
| --- | --- |
| 固定主体 | actor=sample-user、操作role=Administrator。Windowsログイン/token、REMOTE_USER/ST_TRUSTED_ROLE、rawのactor/role/sessionを採用しない。監査のactorはサンプル主体であり実個人の認証証跡ではない |
| 接続 | 同一起動のConsole接続開始時にCSPRNG32byteを小文字64桁hexへ符号化したsessionを発行。接続・画面instance・要求IDを分離し、別接続/別プロセス/再起動へsessionを引き継がない |
| 検査 | 要求ごとに実行側の接続有効性、固定所有者、画面instance/目的、期限、要求ID、期待Revisionを照合する。期待Revision省略を最新値で補完しない。状態更新/消費はDBで条件付き・原子的に行う |
| idle | 実キー活動時だけTOUCHし、無入力のtimer/poll/再描画では期限を延長しない。最大1秒間隔で期限を確認し、無活動30分で接続を失効する。失効後は入力を受付けず旧sessionを復活させない |
| 終了/切断 | 接続を失効し、関連する検索/編集/確認状態を再利用不可にする。再接続/再起動は新session・未検索・未確認。同一起動内の同一接続での画面再作成だけ、owner/instance/期限/Revision照合後に復帰できる |

## 暗号化状態とDB

| 対象 | 契約 |
| --- | --- |
| 要求間状態 | t_runtime_stateとAES-GCMを維持し、検索30分・確認10分・成功Flash一回。DBの暗号化payloadを正本とし、WORKING-STORAGEだけへ状態を保持しない |
| サンプル鍵 | 起動ごとにCSPRNG256bit鍵を生成しプロセスメモリだけに保持する。秘密ファイル/OS環境設定を自動作成しない。終了時に破棄し、他プロセス/再起動からの復帰を許可しない |
| 旧payload | 終了/失効後のsession/keyで復元しない。到達不能な旧payloadは期限削除する。プロセス異常終了後も再起動時は新鍵/sessionとし、旧状態を成功状態へ読み替えない |
| DB接続 | 既存Windows64bit DSN、Microsoft ODBC Driver18、Encrypt=Yes、TrustServerCertificate=Noを使用する。接続権限・資格情報・証明書は実行環境で用意し、本サンプルがDB/DSN/OS権限を自動作成しない |
| 保存と監査 | DB接続権限、TLS、型付きSQL、必須/一意/FK/日付/期間/定員/全候補/版/理由、短い保存単位、同時保存・監査・確定後成功・結果不明時の検索確認は従来通り。固定AdministratorをDBのGRANTや権限付与の代用にしない |

## 検証と残る事項

| 項目 | 状態・判定条件 |
| --- | --- |
| QA-TEXT-COBOL | OS・Console/W API・27×132の設計は確定前提。実glyph/手動IME/キー/補助・結合文字の完全往復は対象版・ハッシュ付きの実行記録で実施状態を別記し、未実施を技術未選定にも合格にも読み替えない |
| QA-AUTH | 本サンプルのアプリ認証は対象外。Windows token/ログイン/人別role mappingを実装必須にしない。本番認証決定・認可適合を主張しない |
| 入力/ABI | 同bit COPY/C ABI、UTF-8/実長/NULL、1024/65536byte境界、重複/未知項目、保護値、制御列安全表示、F8 Apply/Cancel/原値保持を検査する |
| セッション | 複数接続/画面の分離、再起動/切断/idleで旧状態拒否、キーだけ延長/無入力poll非延長、期待Revision競合、期限・一回消費を検査する |
| 実機とDB | 実glyph/IME・採用Windows Consoleでの実操作、SQL Server接続/DDL/CRUD/競合/障害/監査、本番配備/受入は別検査。本書の技術選定だけで合格にしない |
| 正式判定 | 静的構造/ホスト境界/実機/実DB/本番受入/逆生成採点を分け、formalScoreは未実施ならnull |
