# 新AI経路の汎用ワークフロー独立レビュー

2026-10-13、読取り調査。capsule／workflow／prompts／schemas／batch／主AI CLIと、pilot-v2のAI計画を確認した。元ソース・参考設計本文・原仕様・評価criteria・spec-evalは本レビューでは読んでいない。実AI、業務コード、SQL、GUIも実行していない。計画に書かれた業務説明を正解として認定していない。

対象計画のSHA-256は `232C3F10288F4D6363AC6995DD7F6780BF703D07E35872CFB43EA0D5E4DF25BD`。27文書、unresolved14。5 basic-design、4 detailed-specification、4 common-contract、7 database-table、api-contract／database-index／logical-data-specification／operations／dependency各1、analysis-report2である。handoffはtraining-assisted／legacy-v1再検証／現在カプセルとの後付け照合だけのscopeを正しく記録している。

## 指摘と一般化した対応方針

| ID・優先度 | 現状と影響 | 一般化できる対応 |
| --- | --- | --- |
| GWF-001 P1 | AI CLIはdeadlineを受け付けるが、plan／document／review呼出へ渡していない。batchだけが渡す。直接CLI経路では13時間の上限を外せる。 | 全CLI入口へ同じdeadlineを渡し、workflowの各AI呼出前再計算を利用する。開始点だけのtimeout制限にしない。CLI mockで引渡しを検査する。 |
| GWF-002 P1 | 修復の制御が例外と意味不承認を分けきれていない。workflow.reviewはAIがapprovedでも構造不備があると例外を投げ、iteration.runは任意例外でFAILED／breakとなる。修復可能な構造不備が次AI改訂へ届かない経路がある。 | 元AI応答は保持し、ホストのacceptanceを別artifactにする。STRUCTURE_REPAIR_REQUIRED、SEMANTIC_REPAIR_REQUIRED、PROVIDER_FAILED、INPUT_CHANGED、TIME_LIMIT等を型付きで分け、前2者は新round、後者は安全停止とする。Pythonが本文を修正しない。 |
| GWF-003 P2 | v2には物理表7件の個別文書があるが、個別logical-table計画はない。logical-data-specification1件はDTOと移送の契約であり、論理表別のヘッダー／明細文書とは異なる。analysis-reportの責務には「参考設計の5表とDDL7表」とAIが記載しているが、原仕様未読のため5表の正解は本レビューで認定しない。 | AIに論理表／物理表／DTO／一時保持のentity inventoryを作らせ、各entityと文書のcoverage対応を検証する。表名や件数をPYへ固定せず、1表1文書という一般様式を計画の構造契約へ入れる。DTO本を論理表の代用にしない。 |
| GWF-004 P2 | analysis-report2件のpathがspec/reports配下。PLAN promptは報告を納品仕様と分けるが、schemaのkindは自由TEXT、batchは全chosenを同一outputへ書く。選択subsetを外すと報告が仕様へ混入する。 | artifact role=deliverable/report、subject kind、publication rootを型付きにし、役割別の出力先をhostが選ぶ。業務上の分割／表発見はAIが決める。kindから業務文を創作しない。 |
| GWF-005 P2 | full raw／indexed材料は失わず提供され、追跡閉包は開始sourcePathsで制限していない。一方ANALYSISのread path／factsは自己申告だけで、必須調査material、未読／不解決、関連源の追加取得を機械的に対照できない。 | 原文索引とplanのrequired material、AIのread receipt、observed／intended／unknownのclaim ledgerを別に記録する。容量上限では分割／不足を返し、属性や長文を切り捨てない。source-onlyとassistedの結果を同じ精度主張にしない。 |
| GWF-006 P2 | 未接続helperを公開APIとみなさない指示はQUALITYに追加済み。v2のHTTP共通責務とunresolvedにもStrictJson／JSON応答helperの未接続注意がある。これは改善だが、schemaは接続根拠／入口／実装登録／探索範囲を保持する属性を持たず、次writerが注意を落としても形式検査は検出できない。 | AI解析でentry／caller／registration／guards／evidenceを構造化し、reachability=confirmed／declaration-only／not-found-in-included-scope／unknownを分ける。除外資料がある状況で「絶対に未使用」と断定しない。これらは発見した対象へ適用し、固定helper名で分類しない。 |
| GWF-007 P2 | PLAN documentsのkind・subject・親子対応・依存・covered entitiesが自由な文章だけである。機能基本／詳細の粒度、表の分冊、文書間の更新範囲を再計画できる根拠が弱い。 | AI plan review→新AI plan repairを独立工程にする。元planを上書きせず、安定IDとsplit／merge／moveの対応、subject、responsibility、source／design根拠を保存する。修復後に計画pinを新hashで作り直す。 |
| GWF-008 P2 | batchのdefinition選択がtask内tryより前、future.resultの例外も集約されない。計画pinの不備等があるとbatch-resultを残さず終了し得る。またREVIEWEDはchosen subsetだけの状態で、planned全件の完了ではない。 | 入口検査と各futureの失敗をimmutable結果へ記録し、selected／planned／not-selectedをstatus scopeへ明示する。時間不足・未選択を合格文書に数えない。 |
| GWF-009 P2 | capsuleのauthorized reference directoryはresolveを先に使うため、参照ディレクトリのsymlink祖先を隠し得る。source root／reference root自体がspec-eval下の場合も入口で禁止していない。 | resolve前safe_pathで全祖先を検査し、source／authorized referenceのrootにも評価専用領域禁止を適用する。設計参照のユーザー許可と期待値の評価者専用を混同しない。既存liveカプセルは変更せず、今後の入口へ適用する。 |

GWF-001のCLI配線とGWF-009の今後のcapsule入口は親から別途実装担当を受領した。本レビュー自体は確認時点の記録であり、修正後のPASSは別runへ保存する。現在正規scopeで進行するpilotを、これらの一般入口候補だけで停止する必要はない。

## AI意味承認と構造検査

現workflowは本文をrewriteせず、draftの構造結果と意味未評価を別に保存する。reviewにもFORMATと構造指摘を渡し、AI承認が構造ERRORを上書きすることを拒否する。この方向は妥当である。正しい文書形式、原本pinと引用位置の正当性、AIの意味レビュー、原期待表による正式評価はそれぞれ別の証拠である。

126件PASSは親から共有された構造等の試験結果で、本担当が再実行したものではない。見出し・表の存在を、処理意味の正しさや全27文書の完成へ換算しない。現reviewのunresolvedは単なる文字列列挙で、critical未解決と静的観測対象外の環境前提を分類できない。scope内のcritical未解決を不承認としつつ、明記したscope外制約を隠したり「不存在」へ変換したりしない結果契約が必要である。

## 汎用修復ループのインターフェース案

計画と文書のループを分ける。いずれもsnapshotSHA、mode、styleVersion、promptVersion、model設定、artifactSHA、前round ID、deadlineを固定する。AI出力は上書きせず、採択された版へのselection artifactだけを更新する。

| artifact | 必要な共通情報 |
| --- | --- |
| PlanAssessment | planSHA、entity inventory、document coverage、subject／role／親子、split／merge／move／add／remove提案、根拠、重要度、未確定。PYは案件名・件数を供給しない。 |
| PlanRepairRequest | 前AI計画、plan assessment、一般様式、許可材料、snapshot pin、deadline。返すものはAIが作った新planと旧新ID対応。 |
| DocumentAssessment | 対象MD SHA、structural findings、独立AI semantic findings、evidence validity、blocking unresolved、scope limitationsを別欄で保存。 |
| DocumentRevisionRequest | 同一snapshot／plan pin、前MD全文とSHA、原本位置付き批評、一般形式の指摘、調査不足、deadline。正解業務値をhostが足さない。 |
| SelectionResult | evidence-valid／structure-valid／AI-semantic-approved各状態、採択MD SHA、限定scope、未実施、round数、終了理由。正式期待表評価は別担当のartifact IDだけ。 |

現iteration.pyは新round、新出力、新jobを作り、前MDと批評を次AIへ渡す基本形を備えている。構造承認競合のrecoverable扱いと計画修復はこれからの改善範囲である。文書単独の改善だけで、欠けた論理表文書や誤った分割を直せたと判定しない。全体のcoverage／依存に変化があればAIへ計画レビューを戻す。

## 検査範囲

本報告は現在コードとAI計画の読取りレビューで、業務事実の確認、実行同等性、参考設計の採点は行っていない。13時間の制約は各モデル呼出境界と上位run deadlineの両方で扱い、残時間により打ち切った文書は未実施として残す。試行は.tmp、仕様出力は承認されたspec-analysis、報告はtest-reportへ分ける。旧input、元AI応答、過去の生成物を勝手に削除しない。
