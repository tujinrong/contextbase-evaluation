<!-- spec-meta: {"schema":"spec-md/1.0","documentId":"AG-REVERSE","version":"8.5","path":"agents/reverse-agent/AGENT.md","sheets":[{"heading":"役割と対象","kind":"GRID","sheet":"01_役割と対象"},{"heading":"内部Agentと共通制御","kind":"GRID","sheet":"02_内部Agent"},{"heading":"共通request","kind":"GRID","sheet":"03_request"},{"heading":"候補と受入","kind":"GRID","sheet":"04_候補と受入"},{"heading":"互換性と完了","kind":"GRID","sheet":"05_互換性と完了"}]} -->
# reverse-agent の役割

版8.5／2026-10-26。内部3子Agentを取得・目録化、関係構築、動作深化へ分ける設計契約。独立検証は共通の実行能力とし、第4の抽出層にはしない。v2は三層の抽出、共通の独立検証、ホスト採用、ready queueと明示修訂を実装する。実モデルの業務品質とP0／P8の人手受入れは未完了。

## 役割と対象

選択したprojectIdの許可ソースから、システム概要、業務機能、テーブル／データ、共通処理と、それらの関係・動作をContextBaseへ整理する。成果は根拠付き候補、未解決、検証・受入記録まで。仕様書の構成・執筆・描画・変換・公開は下流の責務である。

[運用規則](AGENTS.md)、[実行指示](PROMPT.md)、指定された層の契約を読む。[設計 v0.8](docs/ContextBase分轮提取与验证流程.md)は原則、[実装計画 v0.6](docs/ContextBase実装計画.md)は移行と残工程、[初期実装ガイド](docs/ContextBase初期実装.md)は現v2 CLIを示す。

## 内部Agentと共通制御

| 子Agent | 主責務 | 契約 |
| --- | --- | --- |
| discovery | 取得・目録化。概要、機能、入口、データ、共通候補と被覆を整理する | [取得・目録化](roles/discovery/AGENT.md) |
| relationship | 関係構築。対象間の接続、方向、条件、候補と未解決を整理する | [関係構築](roles/relationship/AGENT.md) |
| behavior | 動作深化。条件、値、状態、順序、例外、副作用、呼出差を調べる | [動作深化](roles/behavior/AGENT.md) |

三つは主責務であり読取り禁止線ではない。relationshipも関係を判断するために条件や引数を読み、behaviorも不明な関係を追加調査へ戻せる。後続の層もアダプターと原文を利用できる。

snapshot、SourceAccess、安定ID、store、アダプター、機械検査、独立原文検証を共通基盤に集約する。独立検証は抽出作業とは異なるtask・文脈で実行し、その候補の作者による自己判定で代替しない。対象目録以外の原文・登録点・未調査領域からも漏れを探す。ホストが版、競合、依存、検証を確認し、採用と範囲受入れを管理する。基盤や検証者を各層へ複製せず、単なる中継・待機のたびにモデルを呼ばない。

## 共通request

物理requestはschema=contextbase-analysis/2、projectId、goal、allowedPaths、excludedPathsを必須とする。各goal.requirementsはid／question／stage／scope／requiresを持つ。実行ID、snapshot、基準版、task、候補・検証情報はホストが生成・束縛する。下表の論理項目すべてをrequestへ重複追加しない。

| 項目 | 内容 |
| --- | --- |
| 実行・案件識別 | runId、projectId、作業IDと元目標の関係 |
| 実行種別と抽出層 | 抽出か独立検証かを区別する。抽出stageはdiscovery／relationship／behavior。task.operationはextract／verifyで、独立検証は対象候補・層・義務をホストが指定する |
| 封印入力と基準版 | sourceSnapshot、manifest、原文hash・位置、ContextBase基準版。初回未作成を明示する |
| 目標と範囲 | 元のgoal、id／question／stage／scope／requiresを持つ必要義務、対象・対象外、検証済み前提 |
| 読取り権限 | 許可原文と除外範囲。実行権限と入力根内パスを区別する |
| 出力先 | 候補・指摘は対象方式の.tmp/、最終検査記録はbuild/の固定先。入力・snapshot・正本と分離する |
| 検証条件 | 必須検査、独立原文確認、人手基準の参照、未確認範囲、受入義務。期待回答は評価側で隔離する |

relationshipは同じscopeのdiscovery義務、behaviorは同じscopeのrelationship義務をrequiresで指定し、独立検証・採用済みを前提とする。前提不足は上流へ質問と根拠を返す。全リポジトリの同期完了を待たず、目標に必要な前提だけを確認する。目録や関係で要求を満たせばそこで止め、有効な成果がある場合は適用性を確認して必要な層から始める。

入力はsource-only。実行権限・入力選択ではproject/spec/全体とproject/spec-eval/を禁止し、選択ソース根の外へ物理的に隔離する。sourceRoot=project/srcs/方式ID/または隔離したsource-only入力を選び、project根へ拡張しない。現CLIのallowedPaths／excludedPathsは --source 内の相対パスだけを指定し、兄弟のspecや ../ を使わない。入力プログラム、SQL、DB、ビルドtask、pluginを実行せず、過去の訓練許可も自動継承しない。

現CLIは --source と --work の同一・親子配置を拒否する。方式sourceRoot/.tmp/内の準備済みsource-only展開先と兄弟の作業先で分離できる。最終正本はホスト採用後に更新し、過去生成世代はGit履歴で管理する。人手QA、identities、正式fixtureを中間物として削除しない。

## 候補と受入

各子Agentは根拠付き候補差分、被覆、未知、依存、上流への追加調査要求を作業領域へ提出する。recordは唯一のownerRequirementを持ち、作者のdependsOnキーをホストがdependenciesのkey／versionへ固定する。原文観測、推定、候補集合、未知・矛盾を分け、構文callを解決済み関係と扱わない。固定ツールは位置・構造・整合を、AIは業務解釈を担当する。

共通検証は候補版と原文に結び付いた指摘、確認範囲、未検査、判定理由を返す。作者は指摘を処置し、変更後の候補・根拠版を再検証する。ホスト以外は正本・受入状態を変更しない。manual／injected結果の保存を採用可能な独立実行の証明にしない。

上流で新対象・誤関係を発見した場合は目録または関係構築へ戻す。変更による依存成果・検証の失効を確認し、影響不明なら再確認を広げる。全対象を毎回3層へ投入しない。部分成果には達成範囲と未達義務を付け、元目標を勝手に縮めて完了しない。

未知はid／question／relatedRequirements／blocksRequirements／scopeReasonを持ち、関連先と阻害先を分離する。verifyはunknownChecksで全unknownのidとhashを正確に束縛し、影響を判定する。非阻害・解決済みには根拠を求め、作者の自己評価で放行しない。検証viewは候補と保持する未失効の既採用記録を含み、viewSha256の一致を採用時にも確認する。

未知のライフサイクルはrecordのowner失効と分離する。上流候補の置換や明示reviseでも既存unknownのid・内容・hashを保持し、作者が省略しても消さない。影響を受けた旧検証decisionは失効させ、後続verifyが各未知を独立に再判定する。

followupが採用予定viewで有効な上流義務を指す場合、当候補のcoverageがsupportedでverifyがpassでもadoptを阻止する。runも補査要求を保存して停止し、明示reviseと再調査を待つ。現在候補のrequirementsだけを調べて上流への補査を見逃さない。まだ採用していない将来義務への質問はhandoffQuestionsとして後続層のcontextへ渡し、現在の前層採用を一律には妨げない。

## 互換性と完了

現CLIはstep --stage、verify、run、reviseを提供する。v1 request／sessionと旧 --role は明示エラーとし、自動変換しない。旧investigationの意味を推測せず、v2 requestで新しいセッションを作る。

runは元要求の依存グラフからready義務を選び、局所の検証済み範囲を上層へ優先して進める。阻害・グラフ外補査は保存して停止し、scopeや義務を勝手に拡大しない。同basisの重複runは既存pendingを返し、新モデル呼出しを増やさない。

reviseは採用済み義務とrequirement／版固定record依存の推移的な下流を撤回し、completeを再開できる。過時記録は現正本から外し、履歴・安定IDを保持する。step --feedbackは旧候補を材料に原文を再調査し、再検証・採用する。

D01～D12は維持する。有効性を確認した成果の再利用を目指すが、P6の依存照合・失効・互換試験前に自動再利用済みと扱わない。既定の総時間・総token予算は設けず、実質的進展に基づく継続を目指す。定義済み目標グラフのready queueと同basis無進捗停止は実装済み。任意の補査配車・自動修復、長期継続制御、新入力範囲やcross-sessionのP6増分再利用は未完了。現cancelは旧返却を失効させるが、モデル子プロセスの即時killは保証しない。

現CLIは封印workspace読取りを既定とし、明示inlineでは改行保持sourceTextと表示用numberedTextを全量提供する。1MiB超は切り捨てず失敗。型束縛、データフロー、framework／SQL専用解析は未実装である。storeはホスト管理前提で、hashは内容整合・版束縛の検査であり認証ではない。

旧仕様書経路を明示選択した場合だけ [旧契約](docs/legacy/README.md)を参照する。2026-10-26に指定された2プロジェクトの試行用複製・設定・結果は清掃済みで、元工程と汎用実装・合成テストは保持する。旧作業領域はresume不可。再試行はscope・request・workspaceを新たに決める。

報告は入力・出力・契約の版、ファイル、実施した検査、受入範囲、未達・未実施を明記する。文書改訂をコード実装・解析・実アプリ試験・性能確認・正式受入れへ読み替えない。
