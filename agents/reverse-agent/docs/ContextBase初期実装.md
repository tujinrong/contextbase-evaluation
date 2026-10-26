# ContextBase v2 実装ガイド

版2.0／2026-10-26。[共通契約](../AGENT.md)、[設計 v0.8](ContextBase分轮提取与验证流程.md)、[実装計画 v0.6](ContextBase実装計画.md)に対応する。3抽出層と独立検証を実装した現CLIを説明する。実モデルの業務品質、人手受入れ、P0～P8全体の完了を示すものではない。

## 1. 実装範囲

- 抽出層はdiscovery（取得・目録化）、relationship（関係構築）、behavior（動作深化）。execute／stepで抽出し、verifyが別task・文脈で検証する。独立検証は第4の抽出層ではない。
- 同じscopeの検証済み目録が関係義務の、検証済み関係が動作義務の前提になる。ホストだけが候補を採用する。
- runは要求グラフ内のready義務を決定的に選び、extract→verify→adoptを進める。既に検証された局所範囲を上層へ進め、全目録の完了障壁を作らない。
- 阻害、目標グラフ外の補査、未解決は保存して停止する。同じ入力・前提での重複runは既存pendingを返し、新しいモデル呼出しを繰り返さない。
- reviseは採用済み義務と依存下流を明示撤回する。step --feedbackは以前の候補を根拠に原文を再調査する。

任意の補査配車・無制限の自動修復、新ソース範囲や別セッションへのP6増分再利用、長期P7運用、即時子プロセスkillは未完了。固定総時間・総token予算は設けないが、個別操作timeoutは持つ。

## 2. 開発環境と入力保護

agents/reverse-agentを作業ディレクトリとし、Python 3.11以降の専用環境へ導入する。

```powershell
python -m venv .venv
./.venv/Scripts/python.exe -m pip install -e '.[analysis]'
./.venv/Scripts/python.exe -m contextbase extract --help
```

analysis extraはtree-sitter 0.25.2、tree-sitter-c-sharp 0.23.5、tree-sitter-java 0.23.5を使う。0.26.0の [Point参照カウント不具合](https://github.com/tree-sitter/py-tree-sitter/issues/500)を避ける。構文workerは子プロセスに隔離し、バイト位置からLF基準の原文行を計算する。異常・上限を正常な空結果にしない。型束縛・データフロー・framework／SQL専用解析は未実装。呼出点は未解決の構文候補である。ゼロバイト原文の全量読取りは空文字列を返せるが、空ファイルを根拠範囲として引用することはできない。

入力・仕様隔離、パス権限、QA保護、build／.tmp規則は [共通契約](../AGENT.md)に従う。project/spec全体とspec-evalは権限層で禁止してソース根の外へ隔離し、CLIのallowedPaths／excludedPathsには --source 内の相対パスだけを書く。入力コード、SQL、DB、ビルド、pluginは実行しない。

sourceとworkは同一・親子にしない。方式sourceRoot/.tmp/内に準備済みsource-only入力がある場合は、その兄弟をworkに指定できる。今回の説明自体は複製・解析の実行指示ではない。

## 3. v2 request

schema=contextbase-analysis/2を必須にする。各義務はid、question、stage、scope、requiresを持つ。以下は汎用形式例であり、パス・目標を実際の許可範囲へ置き換える。

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

discoveryのrequiresは空、relationshipは同scopeのdiscovery義務、behaviorは同scopeのrelationship義務を一つ以上指定する。別領域の合格で代用しない。目録だけなら後続義務は不要。roleやreviewを義務のstageへ入れない。

v1 request／sessionと旧 --role は自動変換しない。旧investigationを新しい二層へ推測分割せず、明示したv2 requestで新セッションを作る。

## 4. 自動進行と手動の単独操作

SOURCE、REQUEST.json、WORKは実際の対象へ置換する。WORKは新しい専用作業先。

```text
python -m contextbase extract init --source SOURCE --request REQUEST.json --work WORK
python -m contextbase extract index --work WORK
python -m contextbase extract run --work WORK
python -m contextbase extract status --work WORK
```

run --requirements behavior のように限定した場合も必要前提を含めて進める。要求済みの範囲を受入れたscope-complete、または元目標を受入れたcompleteは終了コード0。needs-investigation、stopped、cancelled等の未完了は非0（2）、例外は1、Ctrl-Cは130で返す。JSONが返ったことだけで成功としない。

単独操作は次の形で行う。

```text
python -m contextbase extract step --stage discovery --requirements catalog --work WORK
python -m contextbase extract verify --candidate CANDIDATE_SHA256 --work WORK
python -m contextbase extract adopt --candidate CANDIDATE_SHA256 --work WORK
python -m contextbase extract step --stage relationship --requirements relations --work WORK
python -m contextbase extract verify --candidate RELATION_CANDIDATE_SHA256 --work WORK
python -m contextbase extract adopt --candidate RELATION_CANDIDATE_SHA256 --work WORK
python -m contextbase extract step --stage behavior --requirements behavior --work WORK
```

候補hashは実際のstep返却idを使う。behaviorの候補もverifyとadoptが必要。検証は候補と、保持する未失効の既採用記録を統合したviewSha256を確認し、旧版の合格を新版へ無条件に引き継がない。

runは既定グラフを進めるだけで、発見した質問を勝手に義務へ追加したり許可scopeを広げたりしない。阻害時はpending、findings、followupsを確認して、次の原文調査や要求の扱いをホストが判断する。

## 5. 依存、未知、修訂

recordは唯一のownerRequirementを持ち、coverageに所有義務のkeyを含める。作者が返すdependsOnは記録keyで、ホストがdependenciesのkey／versionへ固定する。上流変更時はrequirement依存と版固定のrecord依存を推移的に確認し、古い下流記録・受入れを現正本から外す。履歴と安定IDは保持する。

unknownはid、question、relatedRequirements、blocksRequirements、scopeReasonを持つ。関連する話題と完了を阻害する義務を分ける。verifyはunknownChecksで対象id／hashごとに影響を判定する。非阻害・解決済み判定にも原文根拠が必要であり、作者の自己判定や空の阻害配列だけで放行しない。coverage／checksは今回の義務を正確に一度ずつ含める。

未知のライフサイクルはrecordのowner失効と分離する。上流候補の置換や明示reviseでも既存unknownのid・内容・hashを保持し、作者が省略しても消さない。影響を受けた旧検証decisionは失効させ、後続verifyが各未知を独立に再判定する。

followupが採用予定viewで有効な上流義務を指す場合、当候補のcoverageがsupportedでverifyがpassでもadoptを阻止する。runも補査要求を保存して停止し、明示reviseと再調査を待つ。現在候補のrequirementsだけを調べて上流への補査を見逃さない。まだ採用していない将来義務への質問はhandoffQuestionsとして後続層のcontextへ渡し、現在の前層採用を一律には妨げない。

採用済み成果を再調査する場合はホストが明示する。

```text
python -m contextbase extract revise --requirements relations --reason REASON --work WORK
python -m contextbase extract step --stage relationship --requirements relations --feedback OLD_CANDIDATE_SHA256 --work WORK
```

reviseは依存下流も撤回し、completeだったセッションも再開できる。新しい抽出候補は再度verify／adoptする。未採用の候補に対する指摘処置にもstep --feedbackを使える。フィードバック参照はソースに代わる事実ではなく、原文再調査の材料である。

## 6. 手動引継ぎ、原文受渡し、取消

```text
python -m contextbase extract step --stage discovery --prepare-only --work WORK
python -m contextbase extract verify --candidate CANDIDATE_SHA256 --prepare-only --work WORK
python -m contextbase extract submit --task TASK_ID --answer ANSWER.json --work WORK
```

手動・injected結果は保存できても採用不可。ホスト実行と、抽出と別task・文脈の独立検証を確認できるものだけを受け入れる。

既定は封印workspace読取り。原文読取り環境が使えない場合はstep／verify／runへ --inline-sources を明示できる。改行保持sourceTextと表示用numberedTextを全量提供し、原文1MiB超は切り捨てず失敗する。LF基準の位置、CRLF、末尾改行、Unicode区切り文字の内容を保持する。

```text
python -m contextbase extract cancel --reason user-cancelled --work WORK
python -m contextbase extract resume --request REQUEST.json --work WORK
```

cancelは旧作業の返却を失効させるが即時killは保証しない。resumeは元要求、入力、抽出規則、依存版を照合する。新ソース範囲や別セッションへの自動移行ではない。単操作のtimeout（モデル既定1800秒等）は総予算と区別する。storeはホスト管理前提で、hashは認証ではない。

## 7. 検証範囲と残作業

合成ソースとsynthetic providerを用いて三層の抽出・独立検証・採用、前提拒否、旧CLI拒否、版依存、未知の影響判定、修訂を確認する。新5スイート116件実行・失敗なし・2件skip、旧AI関連392件実行・失敗なし・7件skip（renderingはChromium／lxml環境制約で対象外）。実モデルの業務品質、人手P0／P8受入れ、cross-session P6再利用、自動補査修復、長期P7運用は未完了である。

2026-10-26に利用者指定の2プロジェクト試行用複製・設定・結果を清掃した。Windowsごみ箱へ移動し、元工程・汎用実装・合成テストは保持する。旧workspaceはresume不可。再試行は新scope／request／workspaceを定め、旧結果を再使用しない。[旧仕様書経路](legacy/README.md)は明示依頼時だけ使う。

## 8. 人手照合チェックリストの草稿

AI作成の汎用草稿であり人手承認済み正解表ではない。新しい対象と封印版を定め、人が原文から確認者・行・判断・未知を記録する。

| 点検 | 確認すること | 状態 |
| --- | --- | --- |
| 入口・被覆 | 原文の登録や呼出元から漏れを探し、未調査を不存在にしない | 未承認 |
| 機能・入口 | 業務タスクと技術的入口を区別する | 未承認 |
| データ | SQL参照、物理定義、DTO等の根拠を区別する | 未承認 |
| 共通 | 名前だけでなく共有責務・実装・呼出元を確認する | 未承認 |
| 関係 | 方向・条件・引渡し、候補と解決済みの区別を確認する | 未承認 |
| 動作 | 条件、値、状態、異常、呼出差と反例を確認する | 未承認 |
| 範囲・未知 | 非阻害理由も原文と元義務に照らし独立確認する | 未承認 |

原仕様・spec-evalの期待値は渡さない。この表や合成試験の通過をP0／P8全体の完了へ読み替えない。
