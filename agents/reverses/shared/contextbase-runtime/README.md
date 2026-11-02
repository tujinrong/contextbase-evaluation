# ContextBase 共通ランタイム

文書版0.1.21／2026-11-02。文書版はpackage版と区別する。ソース全体の連続解析入口と、独立した [discovery-agent](../../discovery-agent/README.md)、[relationship-agent](../../relationship-agent/README.md)、[behavior-agent](../../behavior-agent/README.md)が利用するPythonライブラリー。reverse-agentは依存先に含めない。

`analyze`入口では、解析者が元要求の全義務を一つのCodex工具会話で調査し、別文脈の検証者が凍結候補全体を確認する。目録・関係・振舞いは成果の責務・依存を表し、3 Agentの固定起動を要求しない。従来の独立CLIも維持する。導入・実行は下記のnative手順、独立経路は [独立Agentガイド](../../reverse-agent/docs/ContextBase初期実装.md)を参照する。

## 実装の読み方

| Module | 責務 |
| --- | --- |
| [native_contracts.py](src/contextbase_runtime/native_contracts.py) | taskに固定した工具定義、役割ごとの許可、引数診断と契約説明。外部へ返す定義は副本とし、実行ごとの再構築を避ける |
| [native_tools.py](src/contextbase_runtime/native_tools.py) | Codex工具会話の状態、草稿、凍結提出、記録と順序付き回放。状態読取り・改訂・検証・草稿変更を名前付き処理へ分ける |
| [native_draft_patch.py](src/contextbase_runtime/native_draft_patch.py) | 既存草稿の差分を現在版に束縛した通常の草稿イベントへ展開し、既存reducerで検査する |
| [native_state.py](src/contextbase_runtime/native_state.py) | 保存済みrecordの機械集計、unit状態、既存unknownのIDと適用範囲。意味判断や未知の自動統合は行わない |
| [native_evidence.py](src/contextbase_runtime/native_evidence.py) | 原文・Factの取得、返信容量、批次と回放の完全性検査 |
| [native_amendment.py](src/contextbase_runtime/native_amendment.py) | 旧native候補を未信頼入力として検査し、fresh workへseed/specを固定する |
| [candidate_amendment.py](src/contextbase_runtime/candidate_amendment.py) | I/Oを持たないCAS差分検査、指摘別処置と完全候補の決定的合成。v1/v2で共用する |
| [amendment_runtime.py](src/contextbase_runtime/amendment_runtime.py) | task・seed・差分・由来・独立検証の束縛。native transcriptとincremental traceの読取りを分ける |

controllerは実行モードが消費する指示・schema・promptだけを準備する。nativeのcontextは各実行のsetupと内容hash付きtranscriptに保存し、task直下の副本と実行直下のtranscript副本は作らない。incrementalのtask contextはincremental.runが保存し、controllerから重複保存しない。完全なnative記録の取得先はtransportのnativeTranscriptSha256が示すnative-transcripts/<SHA>.jsonとする。草稿checkpoint、setup、個々の工具呼出しと回放検査は維持する。

現行engineで実行できない旧限定移行処理と専用テスト、未使用の役割包装関数・引数検査橋渡し・importを削除した。過去の監査・候補・正式結果は変更しない。[旧移行の扱いと再開条件](docs/分割調査・独立検証プロトコル.md#旧版の移行処理と現行の再開条件)を参照する。新規実行は別workを明示して初期化する。

整理時のengine `4b4b9a282e4251f27bed20ec1aac0bccbc4215da463535bfc0955c0bdb0eface`は[279件の回帰検査と4件・161工具呼出しの実記録回放](build/native-tools/refactor-validation.json)を通過した。工具定義、初期context、契約説明、代表的な引数診断は整理前と一致する。その整理だけでruntimeの実装を純減438行とした。当時は新しいモデル実行を行っておらず、下記99b04版の実案件採用・exportはその版の実績として保持する。

## Codexによる連続取証と役割設定

解析入力のsourceRoot（例：`sample-project1/srcs/CSharp_ASPNET`）へ解析ログ・I/O表示・ZIP・実行報告を追加しない。今回のローカル閲覧資料は`sample-project1/.tmp/contextbase/native-review/`へ置き、正式解析結果はprofileのoutput（`spec-reverse`）へ出力する。

新規recordは`draft_apply`で保存し、既存recordの本文フィールド又は`factUsage`だけを直すときは`draft_patch`を使う。patchは現在の`expected_revision`に束縛し、宿主が変更されない本文と正確なrecord版を補う。所属unit・record identity・調査終了状態を変更せず、元のモデルpatchを保存して回放時に再展開する。独立検証、原文交付、出典・最終採用検査は従来どおり必要である。

`analysis_state(collection=summary)`はrecord件数、unit状態とunknown一覧を返す。件数は指定された保存viewの統計であり、意味上の完全性を保証しない。同じ不確実性を別unitで扱う場合は、適用範囲と阻害責任を確認して既存の完全なunknown IDを参照する。問題文一致による自動統合は行わない。工具試行の経過時間はcanonical回放とは別の`timings/`に保存し、失敗も記録する。

草稿工具には`include_diagnostics=true`を指定する。変更対象recordのfactUsageについて、recordKey・問題コード・既存引用範囲を持つ非阻害の機械診断を返す。全問題は`analysis_state(collection=fact_usage_diagnostics)`の文字ページで取得する。古い指定なし呼出しの返信と回放は維持する。未完了草稿は保存できるが、終提出の既存の厳密な検査は緩和しない。範囲重複は意味上の支持ではなく、宿主がfactIdsを補充したり未取得Factの交付権を与えたりしない。

共有validatorの`completeReport`案内はnative工具会話向けである。legacy呼出しには`analysis_state`工具がないため、programmaticな全量診断は`FactIndex.usage_diagnostics`を利用する。検査条件自体は共通である。

engine `965b1ceacdf261f9832c8f4015303049c5273c3d81c20d25b3dbaf54b4b659d9`を固定して[321件の回帰検査](build/native-tools/protocol-validation.json)と[9件のfixture隔離・評価器検査](build/native-tools/semantic-fixture-validation.json)を通過した。[6会話・265成功呼出しの回放](build/native-tools/protocol-replay.json)は旧草稿の状態を変更しない。[実traceの比較](build/native-tools/protocol-trace-reduction.json)では、95記録を再送した3呼出しをpatchへ置き換え、同一canonical候補を生成した。引数は199,755から49,454 byteへ75.2%減った。これは保存済みtraceの通信量比較であり、モデル実時間の短縮率ではない。

同版の[全量試行失敗](build/native-tools/protocol-failed-run.json)は総1,828.83秒で作者が30分上限に達し、候補凍結・独立検証へ進めなかった。113草稿、3未知、5回のpatch、本文の丸ごと再送0回を記録した。空factUsageの終提出エラーがrecordKeyを示さず、一件修正後にも同じエラーを返して調査が長引いた。上記の機械診断はこの反復失敗への修正である。失敗時間を後続のfresh runから消去せず、旧checkpointを新engineへ移植しない。

診断修正版engine `d4a2a9972bda124d8b093b469138ca6e266645194fc09522590e6ce5a86ceee8`では[359件の凍結検査](build/native-tools/diagnostics-validation.json)が通過した。前述の6会話の回放に加え、[失敗草稿56呼出しの読取り回放](build/native-tools/diagnostics-failed-replay.json)で、残る`op.confirmDuplicate`の空関連と8候補の範囲重複を一度に診断した。旧草稿・状態は不変であり、新たな採用・モデル交付・意味判断は行っていない。

役割指示は、戻り値の消費・代入・副作用、複合条件・境界値・別表現、例外後の処理を追跡するよう更新した。[固定ソースによる指示比較](build/native-tools/semantic-role-comparison.json)は同じ新protocol、ソースbyte、要求、model／reasoningで旧指示と新指示を各1回実行した。3例の独立Agent原文確認は両方とも通過し、実時間は320.21秒から406.60秒へ増加した。正確性の改善や高速化はこの観測から示せない。隔離先sourceRootだけが異なるためsnapshot IDは異なる。期待判定はモデルへ渡しておらず、入力programの実行と人手受入れは未実施である。

診断修正版の[最新全量実行](../../../../sample-project1/.tmp/contextbase/native-review/contextbase-native-run.json)は同じ78ファイル・4,797行、同じ元要求と`gpt-6.1-sol/high`で総1,753.15秒（29分13秒、初期化17秒・作者18分・検証10分08秒）を要した。初期化後のrunは1,735.70秒。比較元の`ba2638a1f8810ea70d48e17ce0295acad80c054a0c2076e82db2fbdb2389c458`は1,690.10秒（28分10秒）であり、今回の総時間は3.7%増え、高速化は示していない。単役割上限は1,800秒から3,600秒へ延長した。各版1回、候補粒度は95から71記録へ変化し、protocolと役割指示を同時変更した観測である。profileは追加Skill・Web・Subagentを選択していない。

今回は71記録（目録42・関係9・振舞い20、主機能6）の全3義務を独立検証・採用し、正式exportを更新した。作者・検証者とも全78ファイル・4,797行を取得した。追加Agent原文抽査でも、principal変換の戻り値破棄と数値enum入力の旧誤判定が訂正されたことを確認した。404への変換経路をより直接記述できるという表現上の指摘は残る。候補の8未知項目は4質問の2重宣言で、full IDをlocal IDとして再宣言したために生じた。正式exportでは将来followup由来の1項目を加えて9項目を保持する。内容・範囲・理由は保持され、独立検証で各項目を非阻害と判断したが、未知の重複防止は未達である。人手受入れ・入力programやDBの実行は行っていない。

作者は5回のpatchを使い、早期診断の6件を2回のfactUsage patchで修正した。終提出は一度で通過した。本文の同一内容再送は112から0回、作者の成功呼出し引数は468,909から201,154 byteへ減った。ただし異なる粒度の実行であり、この57.1%を固定成果物や全tokenの削減率としない。宿主工具処理は計153.59秒、provider時間から工具処理を引いた1,534.41秒はモデル・サービス・通信・CLIなど未分離の時間で、純粋な推論時間ではない。前述の超時試行を含む2回の全量試行は計3,581.97秒（59分42秒）で、probe・検査・実装作業の時間を含まない。

[逐次I/O表示](../../../../sample-project1/.tmp/contextbase/native-review/contextbase-native-io/index.html)と[ZIP](../../../../sample-project1/.tmp/contextbase/native-review/contextbase-native-io.zip)は236原始ファイル・101イベントを収録し、99工具呼出し（失敗2）と97宿主回执を照合した。全文書とbyte hashを保持するが、内部モデルHTTP要求全体や隠れた推論の記録ではない。2失敗はstate field指定と既存unknownの改写拒否で、factUsage終提出の反復失敗は再発しなかった。engine・agent束縛・設定はこの実行中に不変だった。

nativeの未採用候補は、fresh workで`analyze amend-candidate --from-work <旧work/project-analysis> --candidate <SHA> --verification <SHA> --finding <ID> --replace-key <key>`を実行して限定改訂できる。先に新しいworkを指定したprofileで`analyze init`する。通常の`run`／`retry`と区別し、既存incremental Discoveryの`--bundle`契約も維持する。設計正本は[候補の部分改訂設計](../../reverse-agent/docs/ContextBase候補の部分改訂設計.md#12-native-joint候補の限定改訂v2)を参照する。

作者は`analysis_state(amendment)`で選択指摘・原記録・凍結view版を読み、`submit_amendment`で差分と全義務の新しいclosureを提出する。宿主は既存の純粋合成moduleで未変更記録・未知・followupを保持し、新候補全体を別の検証者へ渡す。旧engineの候補は静的検査した未信頼入力として取り込み、旧passや旧交付記録を今回の権限へ昇格しない。v2は原始native候補の指定既存keyの置換専用で、追加・削除・改訂候補からの連続改訂は未対応である。

保存済み取証の回放は操作の入口・出口で封印入力を検査し、その間は固定したsource textを共用する。取証権は元の呼出順でのみ付与し、ライブMCPの各批次検査と取消確認は維持する。旧実行の同一作者・検証記録を各1回比較したローカル測定では、合計143.63秒から28.05秒へ短縮した。モデル時間や新規全量解析の短縮率ではない。

固定engine `99b04cce9af566ccac7b56f4ce5526a823d93bd1b438fe1d772cab15dc2a1d92`の[144件の検査](build/native-tools/amendment-validation.json)が通過した。実例sample-project1／CSharp_ASPNETでは84記録のうち2記録だけを改訂し、他82記録・factUsage・未知ID・followupを保持した。新しい全量検証と採用・exportを15分09秒で完了（作者3分39秒、検証8分52秒、残り約2分39秒）。作者は22ファイル・470行、検証者は全78ファイル・4,797行を今回取得した。旧全量runの24分19秒とは異なる作業であり、新規解析の短縮率へ換算しない。版・指摘・設定・費用情報・限界は[固定実行報告](../../../../sample-project1/.tmp/contextbase/native-review/contextbase-native-run.json)に記録する。

新規の全体解析は`python -m contextbase_runtime analyze`を使う。各役割につき1回の`codex exec`を起動し、その内部でMCPのinventory／query／search／read、plan_update、draft_apply、submit_candidateを使う。検証者には読取りとreview_submitだけを渡す。宿主による取証往復・各単位のprovider再起動はnative経路で使わない。Codex内部の文脈管理を利用し、宿主は封印入力、構文・意味索引、証拠、草稿CAS、未知保持、凍結、回放、独立検証の束縛と原子的採用を保持する。

`evidence_batch`は既知の独立したread／query／searchを最大8件まとめる。完全な返信だけを順に返し、未交付の残りは`next_request_index`で明示する。各返信の`nextLine`／`nextOffset`は別途継続する。入力順の後続取得から先行する提出へ証拠権を与えず、未交付の要求を取得済みに数えない。単項取証は28,672 byte、批次と状態ページは32,768 byte以内の実際のMCP tools/call result UTF-8に制限する。内側JSONの転義とcontent包装を含み、外側JSON-RPC／HTTPは含まない。完全な1行・1項目が入らない場合は明示的な容量診断を返す。原文・意味束縛・診断は圧縮投影せず保持する。

`analysis_state`は最大32,768文字を要求できるが、byte上限に応じて実返却文字数を減らす。必ず`next_offset`で続きを取得する。nativeのglobal／各MCP工具の出力予算を262,144へ明示し、無turn探測で観測値を照合する。Code Modeでは1 cellにつき1返信を完全表示し、追加のexec出力予算も指示する。[実CLIのローカル境界検査](build/native-evidence/boundary-result.json)では、gpt-6.1-solのCode Modeでexec pragmaを省いても32,768 byteの単一返信がhash一致した。同じcellへ最大返信を2件結合すると截断した。host記録はモデル端の毎回の完全受信や注目を証明しない。

followup.requirementは関連分野のラベルではなく、未完了の義務を指定する。現在の割当先へ新規followupを保存するには`retain_blocking_followups=true`の明示確認が必要で、確認しても阻害は解消しない。現時点の調査はplan／remainingQuestions、解釈の不確実性はunknowns、現在の完了条件外の将来作業だけはrequirement=nullで表す。保存候補が既存の無条件拒否条件を満たす場合は独立検証を起動せず停止する。未知の意味判断や採用基準を簡略化しない。

リポジトリルートでruntimeを導入したPythonから実行する。初回導入は選択した仮想環境で`python -m pip install -e "agents/reverses/shared/contextbase-runtime[analysis]"`を使う。既存の`agents/reverses/discovery-agent/.tmp/oneclick-environment/Scripts/python.exe`でも下記入口を利用できる。例のprofileは既存incremental作業先と成果を分離している。

```powershell
python -m contextbase_runtime analyze init --config sample-project1/contextbase.toml --profile csharp_aspnet_native
python -m contextbase_runtime analyze run --config sample-project1/contextbase.toml --profile csharp_aspnet_native
python -m contextbase_runtime analyze export --config sample-project1/contextbase.toml --profile csharp_aspnet_native
```

profileの`context_mode = "native"`と`roles.analysis`／`roles.verification`で、`id`、`instructions`、`model`、`model_reasoning_effort`、`model_provider`を指定できる。`instructions`はconfig相対のUTF-8ファイル。未指定の指示は配布nativeテンプレート、モデル設定は利用者configの許可項目だけを採用し、初期化時に固定する。独自providerの接続定義は未対応であり、暗黙に別providerへ切り替えず拒否する。

役割ごとの`capabilities`で必要な拡張を選ぶ。`skills`はconfig相対の`SKILL.md`一覧、`web_search`は`disabled`／`cached`／`live`、`subagents`は真偽値とする。指定しない役割は従来の最小構成を維持する。Skillは本文と同梱文書のhashを固定して私有workspaceへ複製し、未選択Skillは読ませない。現在のSkill契約はUTF-8文書だけで、実行scriptを含むbundleは未対応。選択後に内容が変わった場合は再初期化が必要になる。

```toml
[profiles.csharp_aspnet_native.roles.analysis.capabilities]
skills = ["skills/source-survey/SKILL.md"] # 利用者が配置した実在ファイル
web_search = "disabled"
subagents = true

[profiles.csharp_aspnet_native.roles.verification.capabilities]
skills = []
web_search = "disabled"
subagents = false
```

Subagentは各役割内の任意の調査補助であり、3 Agent固定ではない。作者の子は独立検証の代替にしない。子の起動には親のrolloutが必要なため、この選択時だけ`--ephemeral`を外し、記録を私有homeの清掃対象に含める。Webは公開言語・framework資料の補助に限定し、原文根拠と混同しない。この制約は指示と観測済みeventの監査であり、通信内容全体を強制検査する機構ではない。Shell・Hooks・pluginの一般実行は別の実行権限契約を要するため、現在の本番role設定では受け付けない。fixtureでの能力検証と、実ソースへの適用可否を分けて記録する。

CLIの親event streamには拒否されたshell呼出しや子Agentの全活動が現れない場合がある。`disallowed_tool_events=[]`を全活動の許可確認と解釈しない。ContextBaseのMCP工具権限はbroker側で役割ごとに制限するが、子の他の工具使用については親event監査だけでは証明できない。

子Agentは親と同じMCP tokenと役割の工具集合を継承する。作者の子にも草稿変更・提出の工具権限があるため、読取り調査だけを委任して変更を親へ戻す規則は指示上の制約である。brokerは親子を識別した読取り専用権限をまだ発行しない。作者と独立検証者の工具集合・会話の分離は維持する。

[役割機能の実測記録](build/native-tools/capability-validation.json)は、設定照合・実際の能力使用・原文解析の比較を分けて保存する。CLI 0.162.1でSkill、Web検索、Hook、ローカルpluginの実行を確認し、shellは実行要求後にpolicyで拒否された。Hook/pluginは合成fixtureでの確認であり、本番解析への接続済みを意味しない。system SkillやAppsの混入を除いた比較では、sample-project2の`CurrentActorFilter.cs`（78行、5,090 byte）だけを解析し、基準26記録／331.88秒に対し、解析役のSkill選択時は34記録／390.37秒となった。双方が独立検証を通過したが、主な差は記録の細分化で、汎用Skillの速度・品質優位は確認できない。各1回、背景に回帰検査も動いた測定であり、統計的性能評価や全project再実行ではない。

同記録の回帰範囲は303項目。途中の`config.py`表示変更によるagent版束縛の不一致1件を初回失敗として保持し、凍結後の対象・隣接検査と拒否の再現を確認した。全項目を一括して再実行した結果ではない。4実会話・161工具呼出しの回放は通過した。原文比較の両armは同じ旧agent実装束縛を保存し、解析engineは現行と一致するが、現在のprofile表示を含むagent束縛は異なる。旧workの束縛を書き換えて現行へ昇格せず、新規initを必要とする。

役割は`model_instructions_file`で基礎指示として設定する。taskへ付ける分析責務と区別し、指示原文・SHA、モデル設定と取得元をsession／jobへ保存する。起動時はambient user configを除外し、封印資料を返す認証付きローカルMCPだけを明示構成する。設定済みの基礎指示と有効なtask契約が解析行動に影響するが、指示の効果や意味的品質を設定値だけで保証しない。実際に観測できないruntime注入はmetadataのunconfirmedに残す。

nativeでは解析試行ごとにリポジトリ外の私有一時`CODEX_HOME`とworkspaceを作り、作者と検証者が順次使う。既存のChatGPTファイル認証だけを複製し、元の認証・設定・親プロセスの環境は更新しない。API-key／endpoint環境上書き、keyringのみの認証は未対応として拒否する。各役割の推論前に実CLIを無turnで初期化し、有効Skillが選択集合と一致すること、`instructionSources=[]`、凍結モデル・推論強度・基礎指示・機能設定を照合する。plugin停止だけでは接続済みAppsを除外できないため`features.apps=false`も指定し、実際のMCP一覧が役割のContextBase工具集合だけであることを確認してから開始する。通常終了・例外・取消時に私有homeを削除し、`native-environments/`へ認証内容を含まない結果を保存する。これは完全なモデル入力やOS隔離の証明ではなく、プロセス強制終了時の清掃や認証更新によるrefresh-tokenの影響も保証しない。

保存済みnative取証の回放では、source返信を操作単位で一括検査する。検査済みの返信も元の呼出し順に交付し、後続のread／queryで先行する提出を許可しない。草稿CAS、役割・引数schema、提出時検査、回放終了後のsource／索引／意味索引の束縛検査は維持する。回復もproducerごとに検査し、過去会話での原文交付を新会話へ持ち越さない。前版の[組合せ検査](build/native-tools/batch-validation.json)は188件通過した。並行修正前のfixtureを読み込んだ2件は、productionの同一指紋下で修正版の3件を再検査し、初回診断も記録に保持した。

providerは現在識別できるCLI動作イベントも検査し、shell実行、ファイル変更、外部MCP、web検索、子Agent起動等の記録があれば成功結果を拒否する。この実行後検査はOS隔離ではなく、将来CLIで追加される未知のイベント型まで網羅する保証も持たない。CLI更新時は実際のイベントと起動設定を再確認する。ユーザー設定の継承対象はトップレベルのモデル・推論強度・providerの3項目であり、ユーザーの名前付きprofile全体の優先順位を再現しない。

元requestは`contextbase-analysis/2`のまま。`jointPolicy`と`executionScope`をhostが明示し、同一候補内の依存又は既採用の依存だけを認める。採用前に全体を独立検証し、同一候補の目録→関係→振舞いを一括採用する。部分範囲を選ぶ場合、未選択・未採用の前提は自動追加せずneeds-prerequisitesを返す。全義務が採用された場合だけ`contextbase-project-result/1`をexportする。旧handoffとは別契約であり、自動変換しない。

失敗時の草稿は同じsource／task／役割設定のbasisで回復する。回復後は引用原文を現在の会話で再取得する。旧採用・旧レビューを回復した承認として使わない。`resume`後に`run`すると凍結済み候補を再利用して検証を再開できる。指示・規則・sourceを変更した場合は別の新workを用いる。大小のprojectで同じ経路を使い、速度と解析品質は対象projectの実測で判断する。

native導入時の検査記録は[final-verification.json](build/native-tools/final-verification.json)、実Codex記録は[smoke.json](build/native-tools/smoke.json)。同記録の固定版では44件検査と、合成Predicate.csの作者1回・独立検証1回・3義務採用・7レコードexportを確認した。継承設定gpt-6.1-sol／highで約268秒を要しており、小projectの高速化は達成したと判断しない。実projectの実行状態は[現在のCSharp_ASPNET実測](../../../../sample-project1/.tmp/contextbase/native-review/contextbase-native-run.json)で区別する。この導入時点では旧経路との性能比較と基礎指示の精度比較は未実施だった。後続の限定的な指示比較は上記の固定ソース3例を参照する。

後続の[Skill読込み監査](build/native-tools/skill-context-audit.json)で、無効化pathをディレクトリにしていた不具合を確認し、`SKILL.md`ファイルへ修正した。同じインストール済みCLIのskills/listで、有効なSkill数は46から0へ変わった。修正版のprovider・基礎指示・役割の21件検査は通過した。上記268秒の測定はこの修正前であり、修正後のモデル実行速度や完全なモデル入力の計測とは区別する。

native実行の開始時は、taskと材料の完全なフィールドを最大12,000文字のbootstrapへ入れる。これはbootstrapだけの予算であり、指示全体やモデルのcontext window上限ではない。超限フィールドは長さと取得先を明示し、`analysis_state`の任意`field`で必要なトップレベル値だけを読み足せる。無指定の全量取得も保持する。起動時の`context.task`重複だけを省き、host保存の完全なtask／context、各義務、分類規則と成果schemaは変えない。bootstrapは原文・fact交付の証明にならず、再生時に束縛入力から再計算する。復帰時は検査済み草稿revisionを通知する。

この変更とSkill修正を含む固定版の[回帰検査](build/native-tools/context-validation.json)は49件通過。既存の草稿CAS・原文交付・独立検証・採用拒否を含めて確認した。

2026-11-01の先行全量実例はsample-project1／CSharp_ASPNETの78ファイル・4,797行を同じ全体要求、gpt-6.1-sol／highで解析した。engineは`977f46c67ebd040b8bb1f376658f3072f5dd2cfccae6a1d61b337a3354bea17f`。runは1,459.46秒（24分19秒）、作者838.65秒、検証者484.82秒、総時間とprovider合計の差は135.99秒だった。初期化・実装・回帰検査の時間はrunへ含めない。作者と検証者はそれぞれ78ファイルの全4,797行をhostから取得し、成功MCP呼出しは50＋44回、全94返信が32,768 byte以下だった。inventoryのlimitを文字数と取り違えた1回のエラーは通常診断で修正された。

候補は84記録（目録56・関係11・振舞い17）、未知9件、現在義務外の将来runtime確認followup 1件。目録・関係の独立検証はpassだが、振舞いはfailとなった。`behavior.class`の厳密なprofile文字列という過剰表現と、`behavior.forms`でmissing/deleted studentの404とexpired stateの409を混同した記述が指摘された。未知の判断はすべて非阻害だったが、hostは通常の検査に従って採用・exportを拒否した。CLIはneeds-investigation、候補・検証は保存済みで、正式成果は未出力である。両roleの探測で有効Skill 0・instructionSources空・全体と各MCPの出力予算262,144を確認し、私有認証cache変更なし・終了時清掃成功を記録した。

先行d013版の同一source run 2,021.46秒に対して今回の時間は27.8%短縮し、成功MCP呼出しは410から94へ減った。ただし候補粒度は117から84記録へ変わり、固定成果物の反復benchmarkではない。累積入力tokenは11,626,124から22,221,448（今回cache hit 21,518,592）へ増え、contextや費用の削減とは言えない。出力tokenは49,156から42,920。provider合計との差は53.99から135.99秒へ増えており、この差を回放CPU時間そのものとは扱わない。その後の回放変更と単独測定は上記native手順に記載する。

source snapshotとraw索引は先行版と同じ。意味索引はcompiler診断の並びだけが変わり、その並びだけを揃えると全payloadが一致した。[比較証跡](build/native-evidence/input-comparison.json)と[今回実行報告](../../../../sample-project1/.tmp/contextbase/native-review/contextbase-native-run.json)に版・時間・未採用理由・export拒否を保存した。nativeの通常retryは前候補を未信頼feedbackとして新規草稿を開始する。今回追加したv2の明示amendは上記の限定改訂入口を使い、旧レビューの流用や手動の採用変更は行わない。小projectの高速・安定完了を達成したとはまだ判断しない。

実project試行で、草稿更新に必要なレコード版の取得口が欠けていたことを確認した。通常の`draft_apply`による置換・削除では`analysis_state(collection="draft_versions", offset=0, limit=12000)`から正規化済み草稿の`{key, sha256}`と返信の`revision`を取得し、`expectedVersions`／削除指定と`expected_revision`へ使う。この入口では版を推測・自動補完しない。新しい`draft_patch`に限り、検査済みrevisionの下で宿主が正確なrecord版を補い、同じCAS検査へ渡す。旧版は更新せず新workを初期化する。[CAS回帰検査](build/native-tools/cas-validation.json)は51件通過し、取得した版による実際の置換・削除、過時版拒否、未知ID正規化、回放・回復を確認した。

[同一入力の実測](build/native-tools/context-performance.json)では、同じPredicate.cs原文・request・役割指示・gpt-6.1-sol／high・CLIバイナリを使い、総時間は268.03秒から162.99秒、MCP呼出しは37回から30回になった。作者96.46秒、独立検証64.52秒で3義務を採用し、6レコードと外部連携に関する非阻害の未知1件をexportした。旧7レコードとは粒度が異なり、同一JSONとは扱わない。49件検査と実測のengineはともに`5ecf9ca6d760282bb56ae63a9c0de5ec1a34f59448554b440fd1c4fdcc45f0f0`で固定された。各版1回の合成試行であり、約39%の短縮をSkill単独の効果や実projectの性能保証へ読み替えない。4行でも約163秒を要し、3回の引数・分類訂正も含むため、高速化は引き続き課題である。

| ファイル | 責務 |
| --- | --- |
| project_analysis.py | 元義務を保持した全体解析、同一候補依存、全義務採用後のproject-result出力 |
| roles.py／native_*_instructions.md | 役割別基礎指示・モデル設定の固定と変更検査 |
| native_tools.py／native_mcp.py | 認証付きMCP、単一役割会話、草稿保存・回復、凍結提出と回放 |
| native_evidence.py／native_readiness.py | canonical取証の字節予算と一括取得、既存の未完了義務判定と保存前確認 |
| native_environment.py | 試行専用の認証cache・子プロセス環境、無turn起動検査、終了時清掃 |
| agent.py | 単層Agentのライフサイクル、自層限定、実装版の束縛 |
| handoff.py | 可搬成果の整合検査、外部前提の独立再検証と有効化 |
| cli.py | 各Agentが渡す型を使ったコマンド処理。Agentの登録簿は持たない |
| controller.py／contracts.py／storage.py | 内容・版・依存に束縛した候補と検証、原子的な採用 |
| repair.py | 未信頼の失敗草稿とモデル作成patchの限定合成・全体再検査 |
| wire.py | task専用短縮参照と厳密なcanonical展開、採用時の再現検査 |
| facts.py | snapshot・抽出器版に束縛した構文事実、全inventory検査、query、モデル利用証跡 |
| semantic_project.py／dotnet_host.py／dotnet/／semantic_calls.py | C#の静的project範囲・metadata、Roslyn宣言束縛、raw位置接続、版付き派生索引と有界検索 |
| semantic_support.py | 通常D/Rの解析設定・派生索引の固定、子task能力、調査対象に沿った初期query選択 |
| sources.py／paths.py／adapters.py | source-only封印、原文位置、言語ごとの構文索引 |
| provider.py／analysis_instructions.md／verification_instructions.md | 解析と独立検証を別の基礎指示へ明示置換したephemeral推論呼出しと実行記録 |
| evidence.py／evidence_dialog.py | 明示モードのhost取証、型付き検索／原文取得、provider往復と採用前の回放検査 |
| investigation.py | 元義務内の調査plan・型付き草稿・CAS修訂・未知保持と決定的な完全候補組立 |
| review_set.py | 全record・未知・scope・義務を分配し、独立検証結果を保守的に集約する版付き契約 |
| incremental.py | 単位別の原文／材料取得、チェックポイント、継続、合成実行の由来と採用前再生 |
| material_window.py | 実交付された候補ページを原文から分離し、出所・版・文字範囲を保つ作業窓 |

handoffは同一の元requestとソース材料に限定する。可搬source束縛から絶対sourceRootを除き、相対パス、内容、許可・除外範囲と残りのmanifestを一致させる。外部の検証要約は監査用であり、受信先の採用権限を復元しない。hashを署名や完全性の意味的証明とは扱わない。

tests/の正式テストは合成入力と模擬providerを使う。実モデルの業務精度・性能、人手受入れは別工程である。実行ログ・仮想環境・生成metadataはGit管理せず、.tmp/で検査する。

独立3環境でruntimeと当該Agentだけの導入・実行、portable成果の受信側原文再検証、活動中followupの解決gateを構造・合成試験で確認した。確定件数と除外範囲は [実装ガイド](../../reverse-agent/docs/ContextBase初期実装.md)を参照する。実モデルの業務品質・人手受入れ・性能確認は含めない。

現行の利用者機能規則は独立ログインとメニュー責務を区別し、作者と独立検証へ同じ境界を適用する。実行・採用・試験の最新状態は実装ガイドへ集約し、過去の実行世代を本文へ累積しない。

## 解析用の基礎指示

3つの独立AgentのCodex呼出しは、taskのoperationに応じて次の基礎指示を`-c model_instructions_file=絶対パス`で指定する。これは通常のタスク文への追記ではなく、Codex内蔵の基礎指示の置換である。[公式設定例](https://learn.chatgpt.com/docs/config-file/config-sample)と[単発CLI上書き](https://learn.chatgpt.com/docs/config-file/config-advanced)に基づき、利用者のグローバルconfigは変更しない。モデルと推論強度は従来どおり利用者設定を継承する。

| taskのoperation | role | 基礎指示と責務 |
| --- | --- | --- |
| extract（抽出・局部改訂） | analysis | [解析者](src/contextbase_runtime/analysis_instructions.md)。根拠付き候補・解釈・未知を作成し、提出前に自分の成果を点検する |
| verify（自層検証・受領前提の再検証） | verification | [独立検証者](src/contextbase_runtime/verification_instructions.md)。候補の支持根拠・矛盾・欠落を調べ、checkと指摘を返す。作者の成果は改訂しない |

2つのファイルは利用者提供の`default.md`を底稿とし、計画・継続・工具使用・根本原因の判断を各責務へ調整した派生版である。進捗会話、personality、最終回答の文章・レイアウト規則は削除し、回答形式は現在のtask契約へ委ねる。工程固有の分類・応答schema・取証手順はtaskが定め、入力境界は既存のCOMMON_POLICYとホストが維持する。

controllerはfull／evidence／incrementalへ入る前にroleを固定する。検証の分輪全体と上流前提の再検証もverificationを使用し、retryと候補改訂の作者呼出しはanalysisを使用する。注入runnerの既存インターフェースは維持し、模擬providerの通過を実Codex設定の確認とは区別する。

各jobは選択した指示の実バイトを`model-instructions.md`へ保存し、`result.json`のmetadataに`model_instructions_policy`、`model_instructions_role`、`model_instructions_path`、`model_instructions_sha256`と起動argvを残す。jobは既存どおり.tmp内の実行記録である。不明なroleは拒否し、選択指示の欠落・空・不正UTF-8なら起動しない。実行中に選択テンプレート又は保存指示が変わった場合も成功にせず、別roleや内蔵指示へ自動代替しない。

基礎指示の内容はengine指紋と配布packageへ含める。旧workのengine値や旧指示下の成功は書き換えず、旧結果を新指示の実測として扱わない。指示置換の疎通確認と、実projectの業務品質・全体速度・人手受入れの評価は分ける。

## プロジェクトprofile設定

[sample-project1/contextbase.toml](../../../../sample-project1/contextbase.toml)はcontextbase-project/1の設定。各CLIはコマンド後の --configと任意 --profileでsource／request／work／outputを解決し、pathsは表示だけを行う。設定相対パスはconfigファイルの位置が基準である。

既定sourceはsample-project1/srcs/CSharp_ASPNET、正式結果はsample-project1/spec-reverse/CSharp_ASPNET/各Agent/contextbase.json。設定exportはtarget.jsonの所有束縛・ロック・原子的更新を使い、手動--outputはfresh-only。現在の実行・採用・未実施範囲は[実装ガイド](../../reverse-agent/docs/ContextBase初期実装.md)で確認し、設定・合成検査とモデル品質・人手受入れを区別する。

## 可搬前提の版と過時拒否

portable成果はcontextbase-handoff/2を使い、payload.premisesにstageから上流envelope SHAへの正確な依存を保存する。discoveryは空、relationshipは受信したdiscovery全成果のSHA、behaviorはそのdiscoveryを継承してrelationshipのSHAも持つ。audit集合や過去passを成果版の代用にせず、内容依存と原文の独立再検証を区別する。

設定モードの後続Agentのrun／retry／exportは、現在の直接前層の固定成果SHAとworkに封印したincoming SHAを照合する。behaviorでは現在のdiscovery固定成果が存在すればpremises.discoveryとも照合する。採用範囲や内容が変わればaudit集合が同じでも過時として拒否し、新handoff・新workで受け直す。

contextbase-handoff/1は推測・自動移行せず、v2成果を再生成して新workを使う。解析requestはcontextbase-analysis/2のままである。手動portable --workは受領時の固定入力に束縛し、生成元workや前層ファイルの継続的な存在・更新には依存しない。固定前層の最新版を追跡するgateは設定モードに限定する。

## 新discoveryの分類契約

[用語集](../../../GLOSSARY.md)と[機能分類境界](docs/機能分類境界.md)を定義の正本とする。ホスト固定catalogPolicy=contextbase-catalog/1に従い、function／operation／common／unclassifiedとtyped classification、主・子・共通・保留の全対象recordのclassificationChecks・元要求全scopeのscopeChecksを用いる。scopeChecksはentry／data／support／material／dependency等を含む全viewを確認する。件数・今回必要な被覆へ影響する保留はpass検査だけで採用しない。詳細な必須項目、参照、unknown、失効と採用条件は分類正本§8～9へ集約する。

裸Sessionの旧v2タスク互換は新分類の合格ではなく、旧レコードへclassification=nullを自動追加して内容hashを変更しない。実装と新規回帰・実モデルの確認結果は[実装ガイド](../../reverse-agent/docs/ContextBase初期実装.md)を参照する。構造・合成回帰の詳細は実装ガイドに記録し、前改訂の70レコードは独立検証を実施したが未解決事項により未採用で、relationship／behaviorの実行や人手受入れを実施済みとしない。

contextbase-handoff/2のcatalogPolicyは互換拡張だが、新独立Agentの受信は合法なcontextbase-catalog/1を必須とする。discoveryは0レコードでもpolicyをexportし、後層はincomingの明示値を継承する。flagの欠落・不正値や旧handoffの自動格上げを認めず、旧入力はDから再抽出する。旧v2 task互換は裸Sessionだけに限定する。

保留のunknownIdsは物化前に大域IDへ固定する。可搬policyと未知IDの詳細は分類正本§8～10へ集約する。

## 構文事実の利用と文脈投影

索引の作成・キャッシュ・query／validate-index・factUsageを扱うときは[ソース事実索引契約](docs/ソース事実索引.md)を読む。完全な構文事実表とinventory・原文を提供し、重複する投影だけを除く。利用妥当性・目録分類・host採用は個別に確認し、索引機械検査のpassだけで業務品質を承認しない。

C#の宣言呼出先は[静的解決契約](docs/CSharp呼出先の静的解決.md)に従い、別派生索引の`SemanticCallIndex.open(...)`／`query(...)`と各独立CLIの`semantic-calls`で取得する。設定の`semantic_project`／`semantic_configuration`を新workへ固定すると、通常D/Rのevidence／incremental取証へ接続する。各作者・独立検証へ少量の初期queryを自動交付し、以後の通常queryにも静的束縛・正規宣言fact・条件付きDI観測を添える。モデルは確認済み宣言を再探索せず、業務意味・条件・SQL・未解決部分の原文調査を担う。

.NET SDKとローカルmetadataを使い、対象のMSBuild・restore・アプリ・SQLは実行しない。interface宣言、実装候補、条件付きDI観測を分け、queryから原文読取り権を付与しない。旧raw索引と119件候補は保持し、新workだけで実行する。fullモードとbehaviorの通常task接続は本改訂の対象外である。実D→Rの実施・採用・計測状態は対象projectの今回の成果案内へ記録する。

## 証拠一括検査と明示compact

証拠検査・短縮伝送は[短縮伝送契約](docs/短縮伝送と証拠一括検査.md)に従い、operation首尾のsnapshot確認、task束縛alias、canonical展開、通常gate・採用時再現検査を維持する。全原文を扱うfull／compact経路と別途のhost取証を区別し、局所replayを全体性能へ換算しない。

明示repairは[短縮伝送契約](docs/短縮伝送と証拠一括検査.md)に従い、同source/request/indexの拒否草稿を未信頼seedとして限定置換する。元回答と失敗診断は現在のworkで保持し、旧承認を継承せず全体検査・独立verify・採用時再生を行う。新規抽出と差分回復の測定を区別する。

## 明示したホスト取証モード

新workのinit --evidence又はprofileのcontext_mode="evidence"で、[ホスト取証プロトコル](docs/ホスト取証プロトコル.md)を使う。3Agentがそれぞれ必要な事実・原文をhostへ要求し、全原文の反復送信とR／Bの前提複製を避ける。旧fullモードを既定として保持し、新モードは--inline-sources／--compact／repairと併用しない。

第1段階は取証の往復と完全viewでの検証・採用を接続した範囲である。台帳を意味上の合格にせず、受信側の独立原文確認、全unknown／followup、分類・fact利用の検査を維持する。選択前提有効化、局所レビュー合成、一般的な増分再利用と業務性能の確認は含めない。

旧evidenceモードの実D試行は、既取得材料の補読が続き、無進展保護で候補化前に停止した。有界原文窓と、以下の新しい構造化草稿経路を区別する。模擬provider回帰の通過を実モデルの可用性・高速化へ読み替えない。

## 明示した分割調査・独立検証モード

新workのinit --incremental又はprofileのcontext_mode="incremental"で[分割調査・独立検証プロトコル](docs/分割調査・独立検証プロトコル.md)を使う。plan→単位草稿→モデルによる義務判断→host完全候補→対象別／全体独立レビュー→host採用を実行する。全量候補・検証JSONを最後にモデルへ再出力させない。既定fullと旧evidenceは保持し、モードの混在・自動移行は拒否する。

草稿・原文・指摘はページで参照でき、別root taskから同basisの検査済み子実行を継続する。拒否回答は診断として保持し、可続用traceへは入れない。statusのinvestigationsは調査途中の表示であり採用receiptではない。新候補へ旧レビューを流用せず、source／規則変更後は新work又は所有範囲を確認した明示freshを使う。

実装と合成回帰は[実装ガイド§8.2](../../reverse-agent/docs/ContextBase初期実装.md)を参照する。領域子集の正式交接、一般的な増分再利用、R／Bの専用型拡張、実業務精度・人手受入れ・性能改善は未確認又は未実装である。
