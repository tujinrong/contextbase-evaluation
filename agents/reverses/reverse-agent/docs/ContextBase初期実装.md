# ContextBase 独立Agentの実装ガイド

版4.1／2026-10-27。独立3Agentの導入・操作・入力境界と現行規則を定める。[設計](ContextBase段階的抽出・検証フロー.md)・[実装計画](ContextBase実装計画.md)のD01～D12を維持する。試行明細を本文へ累積せず、末尾の「実行結果の確認」で確認先を定める。

## 1. 独立した実行単位

| プロジェクト | package／CLI | モジュール | 実行する層 |
| --- | --- | --- | --- |
| [discovery-agent](../../discovery-agent/README.md) | contextbase-discovery | contextbase_discovery | 取得・目録化だけ |
| [relationship-agent](../../relationship-agent/README.md) | contextbase-relationship | contextbase_relationship | 関係構築だけ |
| [behavior-agent](../../behavior-agent/README.md) | contextbase-behavior | contextbase_behavior | 動作深化だけ |

共通runtimeはagents/reverses/shared/contextbase-runtime。snapshot、SourceAccess、ID、store、アダプター、独立検証、host採用を共有する。各プロジェクトは自身のsource／request／workを持ち、reverse-agentのインストール・import・統括を必要としない。

後続層は前層を自動起動しない。前提がなければneeds-prerequisitesで返す。各層の抽出後は別task・文脈で独立検証し、そのローカルホストが採用する。独立検証を第4の抽出Agentにしない。

## 2. 独立導入

選んだagents/*-agentを作業ディレクトリとし、専用仮想環境へ共通runtimeとそのAgentの2つだけを導入する。

```powershell
python -m venv .venv
./.venv/Scripts/python.exe -m pip install -e '../shared/contextbase-runtime[analysis]' -e .
```

CLIはその環境のScriptsから起動する。例えばdiscovery-agentなら `./.venv/Scripts/contextbase-discovery.exe --help`。モジュール入口は `python -m contextbase_discovery`、他2つも表のモジュールを使う。reverse-agentの追加導入は不要。

C#／Javaの構文解析は共通runtimeが担当する。tree-sitter 0.25.2、tree-sitter-c-sharp 0.23.5、tree-sitter-java 0.23.5を使用し、0.26.0の [Point参照カウント不具合](https://github.com/tree-sitter/py-tree-sitter/issues/500)を避ける。型束縛・データフロー・framework／SQL専用解析は未実装。callは未解決候補であり、completeは構文抽出の終了だけを意味する。

## 3. 元目標とrequest

3つとも同じcontextbase-analysis/2 requestと全前提グラフを使い、各CLIは自層の義務だけを選択する。handoffのrequestは受信側と同一でなければ拒否する。別目標・別範囲への汎用P6再利用ではない。

```json
{
  "schema": "contextbase-analysis/2",
  "projectId": "selected-project",
  "goal": {
    "id": "selected-function",
    "question": "許可範囲の対象を段階的に理解する",
    "requirements": [
      {
        "id": "catalog",
        "question": "概要、業務機能、入口、データ、共通候補を整理する",
        "stage": "discovery",
        "scope": "selected-area",
        "requires": []
      },
      {
        "id": "relations",
        "question": "対象の入口、処理、データと共通の関係を追う",
        "stage": "relationship",
        "scope": "selected-area",
        "requires": ["catalog"]
      },
      {
        "id": "behavior",
        "question": "必要な条件、値、状態と異常時の結果を確認する",
        "stage": "behavior",
        "scope": "selected-area",
        "requires": ["relations"]
      }
    ]
  },
  "allowedPaths": ["src/Example.cs", "src/Rules.cs"],
  "excludedPaths": []
}
```

各義務はid／question／stage／scope／requiresを持つ。同scope内でrelationship→discovery、behavior→relationshipの前提を指定する。v1 request／sessionや旧 --role を推測変換しない。例示パスは許可された実在入力へ置き換える。

原仕様全体・spec-evalは権限層で禁止し、選択するソース根の外へ物理的に隔離する。CLI allowedPaths／excludedPathsはsource内相対パスだけで、../や兄弟の仕様を列挙しない。入力コード、SQL、DB、build、pluginは実行しない。

## 4. 各Agentの単独起動

SOURCE_D／SOURCE_R／SOURCE_Bは各Agentが自身で固定するソース入力、WORK_D／WORK_R／WORK_Bは独立した作業先。requestは同一内容を使う。

```text
contextbase-discovery init --source SOURCE_D --request REQUEST.json --work WORK_D
contextbase-discovery run --work WORK_D
contextbase-discovery export --work WORK_D --output DISCOVERY_HANDOFF.json
```

前層workを渡さず、portable JSONだけを渡す。

```text
contextbase-relationship init --source SOURCE_R --request REQUEST.json --work WORK_R --handoff DISCOVERY_HANDOFF.json
contextbase-relationship run --work WORK_R
contextbase-relationship export --work WORK_R --output RELATIONSHIP_HANDOFF.json
```

```text
contextbase-behavior init --source SOURCE_B --request REQUEST.json --work WORK_B --handoff RELATIONSHIP_HANDOFF.json
contextbase-behavior run --work WORK_B
contextbase-behavior export --work WORK_B --output BEHAVIOR_HANDOFF.json
```

各CLIはstatus／indexも --work で受ける。runのcompleteは当該Agentの今回対象が通過した意味で、元goal全体の完了とは区別する。runは --requirements ID...、--inline-sources、--timeout SECONDSを受ける。source-fact対応Dでは--compactを明示利用できる。前提なしなら前層を実行せずneeds-prerequisitesを返す。request／ソース不一致は受信を拒否し、再検証で未解決があれば未完了状態を保存して停止する。導入確認と合成経路の結果は末尾の検証範囲を参照し、個別の業務実行結果へ転用しない。

## 4.1 プロジェクト設定と成果配置

[正式設定](../../../../sample-project1/contextbase.toml)と[要求](../../../../sample-project1/contextbase-request.json)を使う。設定schemaはcontextbase-project/1、default_profileはcsharp_aspnet。相対パスはconfigファイルのディレクトリから解決する。

| csharp_aspnet | 値 |
| --- | --- |
| source | srcs/CSharp_ASPNET |
| request | contextbase-request.json |
| output | spec-reverse |
| work | .tmp/contextbase/csharp_aspnet |

各Agentのworkは設定work基点/Agent名、正式export先はoutput基点/Agent名/contextbase.jsonである。csharp_wpfの切替例はWPF専用のsource・work・outputを使うが、解析は個別の実行要求に従う。

```text
contextbase-discovery paths --config sample-project1/contextbase.toml
contextbase-discovery init --config sample-project1/contextbase.toml
contextbase-discovery run --config sample-project1/contextbase.toml --inline-sources --compact
contextbase-discovery status --config sample-project1/contextbase.toml
```

pathsは解決したsource／request／work／output／上流成果を表示するだけで、snapshot・モデルを作らない。--configはコマンド後に指定し、必要なら--profile NAMEを加える。明示--source／--request／--work／--handoff／--outputとは混在させない。init／run／status／index／query／validate-index／retry／repair／export／revise／cancel／resumeで設定を使える。

| Agent成果rootからの相対位置 | 役割 |
| --- | --- |
| README.md／review.md | 公開の入口・現在判定・人手レビュー材料。生成前のreviewは存在しない |
| target.json | 公開slotの所有保護。rootに保持 |
| contextbase.json | 当該規則で正式採用した後だけexportするportable成果 |
| result/ | 候補と独立検証。これ自体を後層の正式前提へ代用しない |
| facts/ | 構文索引・機械検査・fact利用レビュー |
| .tmp/diagnostics/ | 一時的な診断。公開READMEにも判定・制約を要約する |

正式exportはtarget.jsonのprofile名・source絶対パス・request digest・output root・Agentに対する所有束縛とロックで固定contextbase.jsonを原子的に更新する。同じ所有・内容は冪等、異なるprofile／source／goalは上書きを拒否する。targetは署名ではなくplainな所有情報である。正式履歴はGitを使い、run-id／attempt／archive別に固定出力を増やさない。最新状態は[プロジェクト成果案内](../../../../sample-project1/spec-reverse/discovery-agent/README.md)と本書末尾で確認する。

## 5. Portable handoffと受信側の独立再検証

exportは受入れ済み自層成果がある場合だけ可能。scope部分成果も出せる。手動 --output はsource／work外の未作成パスを使い上書きしない。設定経由の正式exportは第4.1節の所有束縛付き固定先更新として区別する。

exportは元request、ソースmanifest／内容への束縛、現時点の全有効記録、全unknown、未閉鎖followup（raw履歴は監査用）を保存する。同scopeの部分成果も未達と区別する。前層のworkパス・プロセス・reverse-agentの存在は受渡し条件にしない。premisesのexact SHAは成果内容の依存であり、前層のプロセスへの依存ではない。

受信側は自身の封印ソースを使い、同一requestとmanifest／内容を照合する。外部passは監査情報にとどめ、別task・文脈で前提を原文から再検証した後、ローカルで有効化する。ファイルhash一致だけで業務判断の正しさを保証しない。

前提が満たされてから自層を抽出・独立検証・host採用する。グラフ外質問、前層修訂、異なるscopeへの調査はホスト判断へ返し、前層起動や範囲追加を自動化しない。

## 5.1 retryと外部前提の修訂

```text
contextbase-relationship retry --work WORK_R --feedback CANDIDATE_SHA256
```

各独立CLIのretryは、自層の既知候補を材料に一度だけ原文再調査・独立検証・採用する。必要に応じ --requirements／--inline-sources／--timeoutを付ける。初稿が拒否された場合も使える。採用済みの自層義務をやり直すなら先にreviseする。runは同basisで既存pendingを返すため、暗黙の無限retryにはならない。

独立CLIのreviseも自身の義務だけを受ける。上流・外部前提はこのCLIで修訂せず、訂正済みの新handoffを新workで受け直す。故障でstoppedの場合は元requestでresumeした後にretryする。

可搬ソース束縛では絶対sourceRootを除き、それ以外のmanifest、相対パス、内容指紋、許可・除外材料を照合する。ソースの絶対配置が違っても、同一request・相対scope・材料の一致が必要である。

明示followupは安定ID followup:<digest> のunknownとして質問・対象義務・内容hashに束縛する。後続の独立検証はunknownChecksで各項目を判定し、原文根拠付きresolvedだけが閉鎖を意味する。acceptedやnon-blockingだけでは閉鎖しない。raw followupは監査履歴に残し、portableな活動中一覧には未閉鎖項目だけを含める。受信側の独立検証でresolvedを確認してから前提を有効化できる。引き継いだfollowupの対象義務が今回の採用予定集合へ入る場合、原文根拠付きresolvedを必須とする。この条件はローカルadoptと外部前提の有効化へ同じgateで適用し、最終behaviorも未閉鎖の本層質問を残したままcompleteにしない。未解決の有効上流と、現在候補が要求する有効上流への補査は採用を阻害する。

## 6. 依存・未知・信頼境界

recordには唯一のownerRequirementを持ち、作者のdependsOnをホストがdependencies key／versionへ固定する。上流の変更ではrequirementとrecord依存の下流を失効確認し、古い記録は現正本から外す。履歴と安定IDを保持する。

unknownのid／question／relatedRequirements／blocksRequirements／scopeReasonを保持する。record ownerの失効や作者の省略で消さず、影響する旧decisionを失効させる。独立検証はunknownChecksで全id／hashの影響を確認し、非阻害・解決済みにも根拠を要求する。有効な上流へのfollowupはsupported／passでも採用を阻害し、未採用の将来義務への質問はhandoffQuestionsとして渡す。

storeは信頼できるホストが管理し、hashは内容整合であって認証ではない。固定総時間・総token予算は置かず、単操作timeoutと未完了停止を区別する。即時子プロセスkill、一般的なcross-session増分再利用、自動補査修復、長期運用は未完了。

既定は封印workspaceの原文読取り。明示inlineでは改行保持sourceTextを全量提供し、本改訂のモデル投影では表示用numberedTextを重複送信しない。原文1MiB超は切り捨てず失敗する。LF基準の位置を使い、CRLF・末尾改行・Unicode区切り文字を保持する。ゼロバイト原文は空文字で読めるがevidenceには使わない。

sourceとworkは同一・親子にしない。方式sourceRoot/.tmp/内の準備済みsource-only入力と兄弟workなら両立する。候補・試行は.tmp/、最終成果・今回の検査はbuild/固定先へ更新し、履歴はGitで管理する。入力、QA、正式fixtureは削除しない。

## 7. reverse-agentの任意互換経路

独立Agentを実行するためにこの経路を使う必要はない。希望時だけreverse-agentに3packageを追加導入して使う。reverseの既定依存はruntimeだけであり、単独Agentの導入にはreverseを含めない。

reverse-agentディレクトリの互換環境へ3packageを追加する例：

```powershell
python -m pip install -e ../discovery-agent -e ../relationship-agent -e ../behavior-agent
```

```text
python -m contextbase analysis-pipeline --source SOURCE --request REQUEST.json --work PIPELINE_WORK
```

必要なら --inline-sources／--timeoutを明示する。PIPELINE_WORK/<scope-hash>/配下のdiscovery／relationship／behaviorをscopeごとに独立に作り、各公開Agentのrun／exportと受信再検証で連続実行する。一つのscopeの3層を先に進め、次のscopeへ移る。全倉discovery完了待ちにはせず、request全体も切り詰めない。これは利用者が明示した任意入口であり、独立Agentの親や必須runtimeではない。

旧 `python -m contextbase extract` のstep／verify／adopt／run／reviseは旧v2の互換経路として残る。そのrunの合格を新3独立Agentの導入・受渡しの実証にしない。過去の合成試験は監査情報だけとして保持する。検証範囲は第10節で区別する。旧engine fingerprintは移設で変わるため旧v2 sessionもそのまま再開できず、新workを作る。これは旧v1自動変換の拒否とは別の互換制約である。[旧仕様書経路](legacy/README.md)も明示選択時だけ使う。

## 8. 現行の目録・索引・伝送規則

主機能・子操作・共通を判定するときは[用語集](../../../GLOSSARY.md)と[分類境界](../../shared/contextbase-runtime/docs/機能分類境界.md)を読む。主機能は独立した利用者目的と結果で判断し、業務とシステム利用の双方を含む。完全なログイン交互作用は独立機能候補、認証サービス・Cookie・共有レイアウトは別の共通として関連付ける。

メニューは共有nav断片だけでなく汎用の共通メニュー画面も共通になり得る。顧客専用の完全画面や役割別選択に独立した目的があれば主機能候補となる。完全画面は十分条件ではなく、ブランド・URLだけでも決まらない。詳細・確認・popup・編集モードは親タスクへの帰属を確認する。API／CLIに画面は不要で、ログアウトの単独化・統合も一律に決めない。共通には技術処理だけでなく共有業務規則と集中責務を含む。

新Dはホスト固定catalogPolicy=contextbase-catalog/1とtyped classificationを使う。function／operation／common／unclassifiedが主・子・共通・保留に対応する。形式版が同じでも規則内容hashの変更は無視せず、fresh workで再検証する。意味参照の同scope・kind・存在、分類対象全recordのkey／版hash、元要求全scopeを確認し、件数・必要被覆に影響する保留があれば採用しない。

構文factの作成・検索・利用は[索引契約](../../shared/contextbase-runtime/docs/ソース事実索引.md)に従う。全inventoryとsymbol／call／entry／importをモデルへ渡し、sourceFactsSha256と各recordのfactUsageを束縛する。callは未解決の構文観測、entryは登録候補であって配備時到達性の証明ではない。.slnx／.mjsはテキストを取得し、parser未対応はunsupportedとする。静的consumer未観測・退役・コメント構成・実登録を原文逆参照と構成確認で区別する。0 callsやディレクトリ名だけで不足を除外せず、productionの実参照不足は阻害として残す。

```text
contextbase-discovery query --work WORK_D --kind call --callee NAME
contextbase-discovery query --work WORK_D --kind entry --route ROUTE
contextbase-discovery validate-index --work WORK_D
```

query／validate-indexはモデルを呼ばない。queryのlimitは明示した正整数だけを使い、truncatedを報告する。既存index出力は維持する。作者の全recordのfactUsageと、独立検証のfactUsageCheck=passを採用条件に加えるが、分類・scope・unknownのgateを置き換えない。

証拠の一括検査・--compact・repairは[短縮伝送契約](../../shared/contextbase-runtime/docs/短縮伝送と証拠一括検査.md)を読む。operation首尾の完全snapshot検査を保持し、バッチ内read／hashを共有する。compactはsource-fact対応Dだけで明示利用し、task専用aliasを厳密schema後にcanonicalへ展開する。raw／canonical・materializationを保存し、adopt時に展開を再生照合する。全原文を保持し、原文オンデマンド反復調査は未実装である。

拒否草稿のrepairはホストが明示したrecordだけをモデルが全置換する。fresh workで同一snapshot／request／indexの未信頼seedを照合し、key／kind／owner・他record・coverage・未知を保護する。追加削除・scope変更はunresolvedへ戻し、全体の機械検査・独立verify・採用再生を行う。利用できる拒否草稿が存在する場合だけ使い、削除済みの旧記録を前提にしない。ホストは業務内容や未知を推測補完しない。

## 9. 人手照合チェックリスト草稿

AI作成の汎用草稿であり、人手承認済み正解表ではない。

| 点検 | 確認すること |
| --- | --- |
| 入力・受渡し | request、封印材料、scope、受信側再検証が一致するか |
| 被覆 | 原文登録点・構成・未調査領域から漏れを確認したか |
| 目録 | 独立利用者目的、主子帰属、共通責務と入口を区別したか |
| データ | 物理定義、SQL参照、DTO、設定値を区別したか |
| 関係・動作 | 方向、条件、値、例外、呼出差と反例を確認したか |
| 未知 | 関連先と阻害先、非阻害理由を原文から独立確認したか |

原仕様・spec-evalを期待値として解析モデルへ渡さない。合成試験やチェックリスト自体を人手P0／P8の受入れへ読み替えない。後層・人手受入れ、汎用P6再利用、即時kill、長期運用・性能比較は未完了を維持する。

## 10. 正式テストの範囲と実施記録の扱い

正式試験コード・合成fixtureは実行ログと区別して保持する。共通runtimeではsource封印／証拠一括検査、adapter、FactIndex、wire、repair、catalog／unknown／host gateと公開CLIを検査する。legacy analysisと任意pipelineの互換、独立環境・受渡しも各対象スイートで確認する。過去の件数や合格を新規則・新modelの検査結果へ加算又は継承しない。

共有runtimeの回帰、legacy経路の互換試験、実モデル解析、人手受入れは別々に判定する。実施していない範囲を合格とせず、過去の合格や別の入力・実装版の結果を流用しない。単体試験や独立検証の成功だけで全システムの正確性を保証しない。

## 11. 実行結果の確認

実行要求に固定した入力・出力・契約の版、ファイル、hash、検査範囲と未実施を、今回の結果案内で確認する。実行ID、件数、hash、所要時間、provider応答及び試験ログを本書へ転記・累積しない。中間物・実行記録はwork、利用者向けの結果は選択したoutputに置く。

既定profileの人手確認入口はsample-project1/spec-reverse/discovery-agent/review.md。正式な可搬成果は同Agentのcontextbase.json、目録検証はresult/validation.json、構文事実の機械検証はfacts/validation.jsonで確認する。これらは種類の異なる検証であり、索引の機械検証だけで目録の意味や業務品質を承認しない。後続層と人手受入れは、その工程自身の今回の記録で判断する。

分類の内訳、原文根拠、未解決事項及び採用範囲は今回のreviewと正式成果を参照する。discoveryの完了を元goal全体の完了へ広げず、relationship／behaviorの実行や原アプリ・SQL・DBの動作確認へ読み替えない。

実装又は依存の変更でコード指紋が変わる場合、既存workの復元は現行の指紋検査に従う。純粋な構造整理を理由に旧workの自動移行や実モデルの再実行を行わず、必要な解析は新しいworkへ明示的に初期化する。既存の解析結果と人手記入情報は別途保持する。

許可外資料を誤って走査した等の調査境界上の問題があれば、その事実、破棄・再確認した範囲及びモデルに渡した入力を今回の報告へ記録する。封印済みソースだけをモデルへ渡したことと、調査全体が許可外資料へ一度も接触しなかったことを混同しない。
