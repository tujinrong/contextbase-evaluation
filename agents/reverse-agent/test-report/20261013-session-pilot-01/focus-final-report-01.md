# 学生検索・登録編集の改善反復 最終報告

2026年10月13日12:20:58（Asia/Tokyo）で新規作業を終了した。対象はtest-project1／CSharp_ASPNETの学生検索と学生登録・編集の2画面である。完了した独立意味採点の最高確認点は第5稿の289／316点。95%以上に必要な301点には未達である。第6稿は新規AI解析・AI本文執筆・構造検査・画像生成が完了したが、原281行の意味採点と登録・編集の原文・図の全量照合は未完了。旧稿の点数・承認を第6稿へ補完していない。

各稿の「確認点」は独立評価で根拠が一致した点の合計であり、保留を解消した正式得点ではない。保留を合格へ丸めず、全稿の正式得点・正式率・pass95はnullを維持した。第5稿の確認点換算は91.46%だが、正式率ではない。原仕様8.0、採点定義7.4の元281行・316点満点を維持し、検索120行／147点、登録・編集161行／169点を別々に評価した。

| 反復 | 検索確認点／147 | 登録編集確認点／169 | 全体確認点／316 | 不足点 | 非重大矛盾点 | 保留点 | 正式得点・率・95判定 |
|---|---:|---:|---:|---:|---:|---:|---|
| 基準稿 | 118 | 151 | 269 | 39 | 0 | 8 | null |
| 第1稿 | 117 | 157 | 274 | 35 | 0 | 7 | null |
| 第2稿 | 129 | 157 | 286 | 20 | 3 | 7 | null |
| 第3稿 | 126 | 140 | 266 | 40 | 3 | 7 | null |
| 第4稿 | 133 | 150 | 283 | 20 | 6 | 7 | null |
| 第5稿 | 140 | 149 | 289 | 20 | 0 | 7 | null |
| 第6稿 | 未採点 | 未採点 | null | 未判定 | 未判定 | 未判定 | null |

第5稿の行状態は一致255行、不足21行、保留5行。重大な生成矛盾は第1～5稿の完成評価で0件だが、それだけで合格にはしていない。第4稿から第5稿では矛盾6点を解消した一方、登録・編集の確認点は150から149へ下がった。全体の改善は単調ではない。第6稿の元281行はすべてUNSCORED／awardedPoints=nullで、部分点も付けていない。

| 反復 | 出力版 | 出力先（リポジトリ直下から） | 評価結果 | 根拠参照数／凍結pin数 |
|---|---|---|---|---|
| 基準稿 | 1.0 | test-project1/spec-analysis/CSharp_ASPNET/20261013-pilot-v2-r2 | evaluator-only/continuation-01/detail-evaluation.json | 2352／83 |
| 第1稿 | 1.0 | test-project1/spec-analysis/CSharp_ASPNET/20261013-focus-round-01 | evaluator-only/focus-round-01/detail-evaluation.json | 3348／95 |
| 第2稿 | 2.0 | test-project1/spec-analysis/CSharp_ASPNET/20261013-focus-round-02 | evaluator-only/focus-round-02/detail-evaluation-corrected-01.json | 4093／110 |
| 第3稿 | 3.0 | test-project1/spec-analysis/CSharp_ASPNET/20261013-focus-round-03 | evaluator-only/focus-round-03/detail-evaluation.json | 4179／128 |
| 第4稿 | 4.0 | test-project1/spec-analysis/CSharp_ASPNET/20261013-focus-round-04 | evaluator-only/focus-round-04/detail-evaluation.json | 4428／130 |
| 第5稿 | 5.0 | test-project1/spec-analysis/CSharp_ASPNET/20261013-focus-round-05 | evaluator-only/focus-round-05/detail-evaluation.json | 4673／128 |
| 第6稿 | 6.0 | test-project1/spec-analysis/CSharp_ASPNET/20261013-focus-round-06 | evaluator-only/focus-round-06/detail-evaluation-partial-01.json | 意味根拠未確定／128 |

表の評価結果は本報告と同じsession報告ディレクトリを基点とする。リポジトリはD:/開発/contextbase-evaluation。各出力先の対象本文はspec/detail/student-search.mdとspec/detail/student-editor.mdであり、全14本文の実際の版・documentId・path・SHA256を[最終出力一覧](D:/開発/contextbase-evaluation/agents/reverse-agent/test-report/20261013-session-pilot-01/final-output-inventory-01.json)へ保存した。基準稿の歴史的manifest全体394行／443点には対象外のテーブルが含まれ、この報告の採点範囲は2画面281行／316点のみである。基準稿の評価freezeには生成scope／resultのpinがなく、現在のfirst-detail-results.jsonのhashはmetadata観測にとどまる。基準稿の4回推論完了を厳密に実証したとは主張しない。第1稿のscope／resultsのhashも観測値として保持し、第6稿の実raw完了証拠と区別した。

構造、テキスト承認、画像生成、実画像と原ソースの照合、意味採点を別状態として扱った。

| 反復 | 構造・テキスト | 描画 | 実画像・原文レビュー | 意味採点 |
|---|---|---|---|---|
| 基準稿・第1稿 | 今回の最終稿検査として再承認しない | 歴史的結果を第6稿へ流用しない | 歴史的承認を第6稿へ流用しない | 各稿の独立完成評価を保持 |
| 第2稿 | 原稿に検索6・登録編集4の構造指摘、テキスト未承認 | 補正描画36図・5layout成功。原稿の不備を消した扱いにしない | 5layout・21図を実閲覧。検索major1、各minor1 | 286確認点、保留あり |
| 第3稿 | 構造PASS、両テキスト未承認 | 独立した描画runtime補正で35図・6layout成功 | 40画像の閲覧記録を保持。追加の原文照合で検索の待機取消枝、登録編集の409／400枝を指摘し、両追加レビューは未承認 | 266確認点、保留・矛盾あり |
| 第4稿 | 当時の構造PASS。新検査では登録編集にTABLE_CELL_OVERFLOW 1件。テキスト未承認 | 35図・6layout成功、本文不変 | 63PNG実閲覧。検索は限定範囲承認、登録編集はmajor2で未承認 | 283確認点、保留・矛盾あり |
| 第5稿 | 構造PASS、両テキスト承認 | 38図・5layout・25全文tile成功、本文不変 | 68PNG実閲覧、原文55範囲・12crosscheck。両source-only限定範囲承認 | 289確認点、保留あり |
| 第6稿 | 両構造PASS。検索テキスト承認。登録編集の独立テキストレビューはtimeoutで未成立 | 38図・6layout・25全文tile成功、本文不変 | 69PNGを期限前に実閲覧。検索source-only限定承認。登録編集の原文→手順→局所図→結果の全量照合は未完で承認null。全体承認null | 全281行未採点、null |

第6稿の原寸閲覧は検索30PNG（16図・3layout・11全文tile）、登録編集39PNG（22図・3layout・14全文tile）。最終閲覧記録は03:20:39Z、全69件を含むpartial保存は03:20:40.502192Zで期限内。全PNGを見たことだけでは意味一致を承認していない。検索は今回の原文32ファイルを再読した限定source-only承認であり、完全な参考設計適合、全モードの完成画面、狭幅表示、実アプリ操作、正式採点を含まない。登録編集の既観察範囲に新しい確定欠陥はないが、未照合範囲を「欠陥0／合格」へ補っていない。[期限前視覚証跡](D:/開発/contextbase-evaluation/agents/reverse-agent/test-report/20261013-session-pilot-01/focus-review-round-06/partial-manifest-03-before-deadline.json)のSHA256は14c2ad12b1469273012ce9ff3e22526595798c4e64821c251d59e4eda567e895。期限後の新規閲覧0、境界不明0、既存証跡・launch26／source32／capsule43＋11／raw・draft・公開MD・描画原稿コピー／全69PNGのhash変更0を確認した。[視覚証跡の最終保存](D:/開発/contextbase-evaluation/agents/reverse-agent/test-report/20261013-session-pilot-01/focus-review-round-06/final-deadline-persistence-manifest.json)のSHA256はe73f34ee8f9fa1d8ea43b77823f6376d4e4400cc7c9e370251f1766e13b80ca2。

第6稿の新規解析は検索80facts／未解決9、登録編集79facts／未解決12。AIのdeclared read pathsは37／45であり、OS・全toolアクセスの完全監査を意味しない。独立評価担当が実rawを照合し、新規解析2回とAI執筆2回の完了、raw本文＝公開本文＝凍結本文を確認した。検索本文SHA256は4a0fe4056d701e3a51ab58e693212de094f1d781d38a6258bbc332d4e99d07cc、登録編集本文は0c10e37c99ede863745128b4a36977eff3436b3f323d635fcca0f4c36f9fc594。[4推論の実証](D:/開発/contextbase-evaluation/agents/reverse-agent/test-report/20261013-session-pilot-01/evaluator-only/focus-round-06/raw-provenance-final.json)のSHA256は0db33c92493d0b46ce483971c56969795326d9d5d5e86cb8b2b59ba67ae16d0f。[第6稿固定manifest](D:/開発/contextbase-evaluation/agents/reverse-agent/test-report/20261013-session-pilot-01/evaluator-only/focus-round-06/frozen-manifest.json)は128pins、SHA256 f52c21e001ac1515d11064b3b896d23dca35a4cbf4f5b9705a93aa3679579a5d。

第6稿の独立意味評価は検索本文1114／1114行を読了したが、元120評価行の最終文脈・理由・根拠の確定は0行。登録編集は1286行中407行（1–180、298–429、1085–1113、1221–1286）を読了し、元161評価行はすべて未採点。期限後に読解・採点を再開せず、既存観察を排他保存した。[未採点の部分結果](D:/開発/contextbase-evaluation/agents/reverse-agent/test-report/20261013-session-pilot-01/evaluator-only/focus-round-06/detail-evaluation-partial-01.json)のSHA256はd5f638b72225161682c44e76cd384036ca02a70489ad305deb1f6f774e36c55a。[読みやすい部分報告](D:/開発/contextbase-evaluation/agents/reverse-agent/test-report/20261013-session-pilot-01/evaluator-only/focus-round-06/detail-evaluation-partial-final-01.md)と[18成果物の完全byte保存記録](D:/開発/contextbase-evaluation/agents/reverse-agent/test-report/20261013-session-pilot-01/evaluator-only/focus-round-06/final-partial-artifact-manifest-02.json)を保存した。後者のSHA256はa28f9516bada7823d2b34cc67e0999ba48301cce31361b545ba28bd0f5afed84。既存128pinsのorigin／frozenを期限後にhashだけ再検証し、変更0（existing-pin-revalidation-after-deadline-01.json、SHA256 8875db6e4f54b48c69e3407bca5f869c791f2e77ce2285b670e7fe4b08ec4445）。

今回取り出して修正した作成方法の問題は、AI解析より先に本文を組み立て得る経路、前稿の限定承認の過大解釈、図の合流で返却値や条件が落ちること、入力値・NULL・例外の扱い不足、同じ対象の基本／詳細参考設計の読取り不足、HTML内の実送信先、描画されない表セル、工程のタイムアウトと履歴保存である。

- AI-first経路で毎回新規解析を要求し、本文はAIの全文contentを直接保存する。再利用は同一ジョブ・hash一致の明示的な復旧に限定した。全計画ID／pathと実解析のcheckpointを照合し、driverのfreshフラグだけでは完了と認めない。
- 汎用プロンプトに、UI→DTO・型→正規化→DB型・NULL→SQL引数の追跡、raw／内部／保存／表示の区別、await後の再確認、catch優先順位、合流時のversion／NULL代入、各失敗枝の返却値を追加した。対象名や正解値をPythonの本文組立てへ埋め込まない。
- 参考設計の表示意図、業務I/O、共有契約の利用関係、実装・検証責務、値の往復を、観測実装との差としてAI本文に記述するよう修正した。未生成の関連文書へ責任を丸投げせず、設計意図を「未実装／未試験」だけで置き換えない。
- テキストレビューのunresolvedはその評価範囲内の重要な未確定事項として扱う。画像・実機・正式採点の未実施は別範囲へ記録し、重大指摘や実質的な未解決を残した承認は禁止した。限定source-only承認を全体合格へ流用しない。
- 静的HTMLは元のrouteを非実行data属性・注記へ保存し、type=button／文書内fragmentで表示を保つ。action／formaction等の実送信は検査で拒否する。DOM・外観・モードの証拠を保持する。
- GRID／LISTの余剰セルで条件や結果が描画から落ちる不備をTABLE_CELL_OVERFLOWで検出する。コード内のpipeはAIにescapeまたは記述変更させ、Pythonの本文差替えでは修復しない。
- 描画はcanonical document path、ローカルMermaidとChromiumを明示する。全文を高さ4000以下のtileに分け、寸法・decode・nonblank・hash・coverageを保存する。描画成功と原文一致は別判定である。
- Providerへ同じUTF-8 promptを保存済み通常ファイルstdinで渡し、Windowsの同期PIPE書込みがtimeout前に詰まる経路を改善した。中断時のraw／stderr／eventsを保存し、不完全answerを完成本文として採用しない。
- 試行は外部configで駆動し、開始時runner全文とruntime13ファイル、改訂入力を凍結する。AIが書いた批評JSONを直接保存し、Pythonはschema・根拠範囲・hash・保存のみを担当する。metadata-onlyの分類訂正は本文・業務文言を変えず、旧byte列とtransitionを残す。
- 評価結果はexclusive-createで保存し、訂正時に旧byte列・新版・対応記録を残す。元評価行のID・見出し・判定対象・隣接文脈を最終本文で確認し、別操作への根拠の誤結合を防ぐ。

第2稿で検索2操作行の理由・根拠が誤結合していたため、元結果を保持してcorrected-01へ訂正した。点数は変えていない。第4稿の初期暫定editor JSON／contextはsnapshot前に上書きされ、初期byte列を失った。残るhash・記録を保存したが、復元済みとは主張しない。第5稿は17最終artifactのexact-byte manifestを保存し、排他保存の改善を確認した。過去の失われた履歴を新しい保存機構が回復した扱いにしていない。

最新の汎用工程テストは[method-integration-11/results.json](D:/開発/contextbase-evaluation/agents/reverse-agent/test-report/20261013-session-pilot-01/method-integration-11/results.json)：301 PASS、failure／error／skip各0、code・test pinsの変更0。これは工程テスト301件であり、意味採点301／316点ではない。ProviderのUTF-8 child・非読取りchildのtimeout・通常ファイルstdin等を含む。最初のCRLF期待値fixtureの失敗記録を残し、os.linesepに合わせて修正した。deadline helper／wrapperの各13 synthetic PASSとlive no-stop dryrunは別試験であり、実強制停止の成功試験と合算しない。production修正の主なファイルはagents/reverse-agent/src/contextbase/ai配下の__main__.py、batch.py、iteration.py、workflow.py、prompts.py、provider.py、rendering.py、validation.py。保存機構・config runner・deadline制御・独立評価の補助は.tmp／test-reportへ分離した。

入力はユーザー許可のtraining-assistedで、capsuleに原ソース43ファイル・参考設計11ファイルを収録した。capsule manifest SHA256は3a722dc206dbf2ce850b594aa1bee65117e472a8144531adb731d354fb9a5a24、planは232c3f10288f4d6363ac6995dd7f6780bf703d07e35872cfb43ea0d5e4df25bd。legacy-v1のraw／indexed／metadataを再検証した未封印manifestであり、sealed-v2やblind source-only生成精度を主張しない。参考設計の要求と観測実装を区別した。期待評価行・配点は評価担当側に隔離し、生成入力へ渡していない。モデル指定はuser-configured default、実モデル名・reasoningの確定値は記録されていない。

第6稿起動configは5b4d300859ec77e777101358bb6cb4edd73a5872ec1566e9ef65c3171b24b823、保存runnerはc63aca7300a44fa17c542d82a98dc0523c3853206fb8b8a6d3ebe0fc62a9f591。generic promptsは8135a2157fc127565baf5ec9d62c7c6616b0a12112385c61f5f30e09b467228e、Providerは9e5a10ab196cf30127a4596ba77538bb9c9e772f783aea240c25baa25bccf26d、AGENT.mdは7.2。今回のactive AI経路はPythonによる業務本文組立てを使用していないが、互換用legacy pipelineの全廃までは行っていない。read restrictionsは記録されたpolicyであり、全tool／OS I/Oの強制隔離を証明していない。

期限watchdogは最新focus-continuation-handoff-12.jsonを03:20:58Zに取得した。所有証拠のある第6稿generator PID49380、renderer PID313200のみを照合し、03:21:03Zの確認では既にNOT_RUNNING、03:21:09Zに両identityのABSENTを確認した。生成は登録編集の独立テキストレビューtimeout（231.294711秒、answer=null）をFAILEDとして記録して終了したが、完成したAI本文は保持した。両rootが既に終了していたため、強制停止成功とは報告しない。停止前後で各901ファイルのコピーを保存し、captureErrorsは0。準備コピー／CIMに時間を要したため、期限時刻ちょうどの停止は主張しない。未捕捉の新しい子processやremote処理の不在を完全証明した扱いにもしていない。

rootは03:21:08Zの時計観測後、実行中だったこの依頼の意味評価child、集約評価、独立視覚レビューAgentを中断した。個別の精密な中断時刻は未記録。後続のAgent作業は既存観察の証跡保存だけに限定し、新規読解・画像閲覧・解析・執筆・採点を許可していない。[停止と捕捉の記録](D:/開発/contextbase-evaluation/agents/reverse-agent/test-report/20261013-session-pilot-01/focus-deadline-01/finished.json)、[Agent制御記録](D:/開発/contextbase-evaluation/agents/reverse-agent/test-report/20261013-session-pilot-01/deadline-agent-control-01.json)を保持した。最終報告の保存後に継続用heartbeat「検索・登録仕様の改善ループ」（id=automation）をPAUSEDへ変更した。実際のautomation.tomlを読み直してPAUSEDを確認し、name・prompt・rrule・target・id・kindは元の設定と一致した。[停止設定の実確認](D:/開発/contextbase-evaluation/agents/reverse-agent/test-report/20261013-session-pilot-01/automation-stop-verification-01.json)を保存した。停止確認追記前の本報告byte列も.tmpへ保持している。

最終原本検査はセッション開始時の原ソース・原仕様・spec-evalを含む179ファイルのhash比較で、179 unchanged／missing0／changed0。[原本検査](D:/開発/contextbase-evaluation/agents/reverse-agent/test-report/20261013-session-pilot-01/focus-protected-final-01.json)のSHA256は5eec546437da69583e180b0cb2a85c010212ade7f11b9b03e0c7f809369a164f。全repoの全ファイル不変を意味しない。第6稿の凍結runtime13＋config＋保存runnerの15pins、改訂入力8pinsも変更0である。[runtime確認](D:/開発/contextbase-evaluation/agents/reverse-agent/test-report/20261013-session-pilot-01/final-runtime-pins-01.json)と[改訂入力確認](D:/開発/contextbase-evaluation/agents/reverse-agent/test-report/20261013-session-pilot-01/final-revision-input-pins-01.json)を保存した。

残件は第5稿の不足20点・保留7点、第6稿全281行の独立意味確定、登録編集の全量原文・図・本文照合、timeoutした独立テキストレビューである。参考設計の完全意味適合、全モードを組み合わせた画面、狭幅、実HTTP binding、アプリ／DB／SQLの実行、ビルド、実機・並行・取消・配信試験、全1408行評価、PDF／Excel export、他projectへの一般化は未実施。実ソースのtargetはnet10.0であり、別の.NET10調査は生成capsuleの実行証拠ではない。原ソース・原仕様・spec-evalは編集せず、アプリ実装・DB操作・commit・push・deployは行っていない。

本文はAIが執筆し、Pythonは検査・保存・描画・工程制御を担当した。指摘の解消や画像成功をもって95%達成や自己学習の効果を断定しない。期限までに得られた成果物・工程改修・独立判定・未確定をそのまま保持した。
