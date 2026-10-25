# AS400_RPG 生成記録

実行ID: `20261025-regenerate`。状態: **REGENERATED（実ソース再生成）／nativeExecution=NOT_RUN**。完了範囲と未実施はregeneration.jsonにも保存します。

入力は `test-project1/spec/AS400_RPG/` の42ファイルと全体規則16ファイルを通常preflightで凍結しました（構造PASS58、意味/実行適合の合格ではない）。README8.5、登録詳細8.6、方式別共通8.4、共通・全詳細・Db2定義・業務コード・規約を確認しました。登録詳細の物理参照 `CNFRM.DELREAS1/EREAS2` だけが同文書のspan/REG-026/移送表と衝突し、後者のDELREAS2に一意に確定するため8.5→8.6へ局所修正。local-spec-fix.jsonへ前後hashと根拠を保存して再preflight58 PASSで再凍結しました。QA・正式fixtureは変更していません。

旧2パネルをEDSTUDENT通常1画面へ変更し、19保存入力とREG-001～034を維持しました。DDSは現在の方式内HTML行桁契約から再生成し、可視窓・プログラムバイト・SI/SO・前後属性セルを分離しています。原元号varucs2(20)、年月日、原年度/学年、備考3窓・理由2窓を原Unicode DSへ結線しました。新規入学日は空欄、既存の性別0/在籍01/当年度補助は維持します。

検索の4条件と7列、SQL20/50/100件、同じDBページ内の8学生×2行窓を維持し、F9ソート8選択・F11件数3選択のPICK、カーソルF4/F8、F9次エラー、正確なカーソル復帰へ更新しました。Enterの2/5選択は全行を先に検査し、ちょうど1有効行だけを処理。READC後に変更標識が消えても非空選択を保持し、複数/不正行で検索へ落ちません。

LONGTXTは通常/明示Unicodeモードと128バイト窓を用い、完全スカラー/完全エスケープで送ります。元LFと物理折返しを別に保持し、未変更原文や非表示末尾を切り捨てずspliceします。独立レビューで発見された狭いrawへのF10容量超過黙殺を修正し、製品C StTextLimitが対象DS容量とrawスカラー上限をF10前に検査します。超過はLMSGを出してdraft/TEXTを補助内に保持し、原入力は変えません。F12は元値へ戻します。DUP/DELETE/DISCARDは種別別の値を表示し、F10/F23だけを明示確定、Enterでは確定しません。保存・認可・版・全候補・10分期限・監査同一Txの既存契約は維持しています。

今回の生成コマンド（Pythonは-X utf8）は tools/generate_sources.py、generate_database.py、generate_messages.py、generate_dds.py、format_rpg.py。COPY/ABI/メッセージとDb2の6表89業務列・5分類70コードのDDL/seedを再生成し、DB適用はしていません。生成器が必要なStConfirm/StEndWork/Lookup各prototypeとStClassInfoの任意引数を保持するよう修正し、公開PIとの型一致を静的確認しました。

最終現ソースから tools/test_host.py --run-id 20261025-regenerate、test_state.py、test_compact.py、write_report.pyを実行。方式内の既存Zig0.14.1/ICU77.1を再利用し、製品C57/57（新Text窓/上限22件）、製品状態C42/42、参照/ABI静的94/94、Text/DDS静的46/46、状態/生成器静的25/25がPASSです。全記録の対象source hashを現ソースへ照合しました。コマンド/exit/stdout/stderrはbuild/test-resultsの固定名、失敗/試行・バイナリ・cache・隔離生成は.tmpに保存しています。旧PASSを流用していません。

IBM i SQLRPGLE/ILE C/DDS/CLのコンパイル・バインド、Db2、5250端末/IME/CCSID実機往復、保存/競合/確認/異常終了の統合、正式受入/逆生成採点はNOT_RUN。ソース生成とホストC/静的PASSをネイティブ動作成功へ読み替えません。COMMON V2 / SVC V3 / UNICODE V2を全体再構築し、新しい専用ジョブで配備検証する必要があります。主なDDS構文は公式IBM RTNCSRLOC/SFLCSRRRN資料を参照し、リンクはdocs/deployment.mdへ保存しました。formalScore=null。

source.zipと最終outputs manifestは親工程が作成します。
