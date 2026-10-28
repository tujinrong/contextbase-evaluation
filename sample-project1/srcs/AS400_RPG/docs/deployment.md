# 配備・実機確認

本方式のソースは凍結したcanonical仕様42ファイル（README8.5、方式別共通8.4）によります。Windows試験の成功はIBM iの配備承認ではありません。ILE C/SQLRPGLE/DDS/CL/バインドとDb2/5250の実機検証は未実施です。

1. 空の評価用STUDAPPを用意し、schema.sqlをSQLツールで適用する。初期5分類70値とguard1行を照合する。既存データへseedを再投入しない。
2. JOURNAL.clleをコンパイルし、M_STUDENT/M_CLASS/MCAT/M_CODE/T_OPLOG/STGUARDの全6表を同じSTUJRNでジャーナルする。受信先と保存方針を環境管理者が設定する。
3. BUILD.clleを実行してコンパイルスプールとバインド一覧を保存する。Cの標準インクルードは/QIBM/include、ICUのbinding directoryはQICU/QXICUAPIBD。採用ICUの版を保存する。
4. STUADMIN/STUSTAFF/STUVIEWのグループ所属を承認設定として用意する。最小権限のSTUOWNERを作り、任意コマンドや対話サインオンを許可しない。SECURITY.clleがサービス/入口の所有者採用と6表の限定権限を設定する。表の直接変更権限やサービスの直接起動権限を一般利用者へ付与しない。STUOWNERに必要なライブラリー/ジャーナル/認証サービスの参照権限を確認する。
5. /stuapp/sourceは配備者だけが更新し、/stuapp/approvedは承認者だけが内容を発行できるACLにする。STUMNTはASCIIの`.txt`葉ファイルだけを受け、親参照・サブパス・制御文字・コマンド文字を拒否する。一般利用者が承認済みファイルや親ディレクトリーを更新できないこと、シンボリックリンクを用いないことを確認する。
6. START.clleから専用ジョブを起動する。CCSID1399、27×132、STUDAG、ジョブ共通コミットメント、15秒の待ち上限を確認する。既存のコミットメント定義があるジョブでの起動は拒否する。
7. UTF16の補助文字/結合文字、CCSIDに存在しない文字、未変更原文保持、全長のF8編集、SFL8学生×2物理行とSQL20/50/100件、READCのID対応、停止候補保持、原文と保持条件、30分期限、Viewer/Staff/Admin、保存・削除・監査・0行競合・全候補確認を実際に操作して試験記録を保存する。
8. 2ジョブで定員競合、番号競合、候補変更、同一学生版競合、監査失敗、COMMIT結果不明、ジョブ異常終了を試験する。失敗時ROLLBACK、ゲート解放、成功通知の抑止、検索確認を確認する。これらは今回NOT_RUNである。

STUMNTへの入力はUTF8（BOMなし）の `key=value`、`TYPE=CLASS/CODE`、最後に `END` です。全項目を明示し、任意の空値も`key=`と記します。値は承認入力のエスケープモードであり、普通の文字と `\u{HEX}`、`\\` を厳密に復号します。型・上限・マスタ規則・履歴は業務サービスが再検査します。ClassはclassId/期待版0で作成、Codeは期待版0で作成し、更新時は対象キーと取得済み版を指定します。入力内容から権限や実行者を指定できません。configの例を承認者が見直し、実DBの版と合わせてください。失敗ブロックを越えて投入せず、各完了ブロックの受付番号/結果/版をジョブログへ残します。

主な処理系根拠はIBMの [CRTSQLRPGI](https://www.ibm.com/docs/en/i/7.4.0?topic=c-create-sql-ile-rpg-object)、[CRTSRVPGM](https://www.ibm.com/docs/ssw_ibm_i_74/cl/crtsrvpgm.htm?lang=en)、[ICU option39](https://www.ibm.com/docs/en/i/7.5.0?topic=category-international-components-unicode-apis)、[CFnn](https://www.ibm.com/docs/ja/i/7.5.0?topic=c-cfnn)、[LIKEDSの構造](https://www.ibm.com/docs/en/i/7.4.0?topic=statement-free-form-data-structure-definition) です。これらの確認だけでは実機コンパイル成功を示しません。

2026-10-25実行20261025-regenerateの検索状態契約はCriteriaFormatVersion=2、正64bit Revision。STUCOMMON V2 / STUSVC V3 / STUNICODE V2、原元号/補助DSとText窓C関数を含め全プログラムを一括再構築し、既存ジョブを終了して新しい専用ジョブで開始する。旧DSレイアウトを持つバイナリーや実行中activation groupとの混在配備は対象外。ジョブ内レジストリー64件について同一Revisionの旧要求拒否、owner/job/window不一致、形式欠落／旧版、30分期限、expired slot再利用後の復帰、F5/F12解放、満杯時の明示拒否をIBM iで再検査する。Windowsで実行したのは同じC gate/key/blockと既存Unicode/入力Cだけであり、RPGレジストリーの実行証拠ではない。

最新のEDSTUDENT/PICK/LONGTXT/CNFRMは今回ソース再生成したがネイティブ未検証です。RTNCSRLOC/CSRLOCとSFLCSRRRN、出力名称、8候補窓、F9次エラー、F23削除、通常/Unicode切替、空/不正raw、LFと物理折返し、補助文字とSI/SOを実機で検査してください。公式DDS構文根拠は [RTNCSRLOC](https://www.ibm.com/docs/en/i/7.4.0?topic=r-rtncsrloc) と [SFLCSRRRN](https://www.ibm.com/docs/en/i/7.6.0?topic=s-sflcsrrrn) です。これらの参照・静的行桁検査は実機合格を意味しません。
