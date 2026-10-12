# reverse-agent 文書品質・AI実行経路の調査

実行ID：20261013-tuning-01／調査日：2026-10-13／工程：調査のみ。

現行generic出力は、見出し・表・画像と原文対応を備えている一方、読者が操作の目的、状態変化、分岐結果を理解する説明が不足している。特にreturn内の委譲、セッション属性の削除、三項演算子の成功・失敗分岐が文章で失われている。抽出結果の体裁だけを改善するより、根拠付き解析、原稿、独立レビューを保存し、それぞれを検証する工程が必要である。

## 対象と境界

- 調査対象は `agents/reverse-agent`。設定のproject IDは `jsbrms`、profileは `auto`、入力先設定は `input`。この調査では業務input原本自体を開いていない。生成MDに既に掲載された原文・根拠行と生成器・検査器を照合した。
- 代表対象はSCR-020職員番号入力、SCR-013ログイン、SCR-018新規・変更・削除の基本・詳細、計6文書。基本設計書13文書について定型句の出現を別途読み取り集計した。
- 全体docsの一般書式、Agent役割、reverse-agent/AGENTS.md、README、現行コード・テストを読んだ。test-project1原仕様、spec-eval、正解表は読んでいない。
- 書込みは本報告の新規作成だけ。生成文書、プログラム、設定、共通docs、他Agent、test-project1は変更していない。品質検査・ユニットテスト・再生成・業務inputの実行もしていない。
- `codex --version`、`codex exec --help`、管理されたruntimeのバージョン・モジュール存在確認はローカル操作のみ。モデル呼出し、APIリクエスト、外部送信、依存インストール、重み取得、fine-tune、API課金を実行していない。

## 具体的な品質欠陥

以下のL番号は調査時のファイル行。業務原本との完全一致を判定した結果ではなく、現行生成文書同士と生成コードから確認できる欠陥である。

| ID | 観点 | 具体的根拠 | 読者への影響と改善 |
| --- | --- | --- | --- |
| RQ-001 | 責務・文章 | 基本SCR-020 L19、基本SCR-013 L19、基本SCR-018 L19がすべて「…の入力・表示・要求処理を行う」。開始契機も各L24「呼出元からの要求」。生成元 `src/contextbase/detail/core.py:L251`、`documents.py:L25-27` | ログイン、職員照合、予約保守の目的・利用者・開始操作を区別できない。イベントに到達する要求、実際に使う入力、正常結果を根拠付きで一段落にまとめる。不明な役割・業務目的を画面名から創作しない。 |
| RQ-002 | 処理順・委譲 | 基本SCR-020 L57/L79/L101は「処理結果を呼出元へ返す」だけ。詳細SCR-020 L16/L24/L32には `return new MenuViewAction().perform(request, response)`。`event_templates.py:L160-168`はreturnを先に処理し、内部呼出しを一般的な返却に置換する | メニュー表示処理への委譲が消え、クリア・照合・表示の違いも読めない。「メニュー表示処理を呼び、その結果を返す」と委譲を明記し、解決できた呼出先の副作用を別の根拠付き説明にする。原本から確認できない『職員番号を消す』等を名称だけで追加しない。 |
| RQ-003 | 状態 | 基本SCR-013 L56-60の「関連情報を取得・設定する」に対し、同文書L107-109と詳細SCR-013 L16-18には職員context/CSRF tokenの `removeAttribute`、その後 `super.perform`。`event_templates.py:L182-184`の一般fallback | 認証関連の既存状態を削除する順番が『取得・設定』という別の動作に見える。「職員contextをセッションから除去→CSRF tokenを除去→基底処理を呼ぶ」の順と対象を説明する。新token生成や認証成功は確認できた別根拠がない限り補わない。 |
| RQ-004 | 条件・結果 | 基本SCR-013 L62、L78-79は条件8/9/10だけ。L110-112に戻り先がLogin.jspか否かの原文がある。詳細SCR-013 L20-21は `return next` と `return new MenuViewAction().perform(...)`。`event_templates.py:L154-156` | 補足へ移動してソースを読むまで二つの戻り先を理解できない。「基底処理の戻り先がログイン画面ならその戻り先を返す。それ以外はメニュー表示処理へ委譲する」と記述できる。『認証成功/失敗』との同一視は基底処理の根拠確認後に行う。番号は本文の意味の代用にしない。 |
| RQ-005 | 成功・失敗、状態保持 | 基本SCR-018 L144-150は削除後に無条件で「削除対象が見つかりません。」を設定。詳細SCR-018 L38-40は `boolean deleted=...`、`deleted ? "削除終了！" : "削除対象が見つかりません。"`、`deleted ? repository.createEmpty(staff) : value`。`event_templates.py:L170-179`は日本語リテラルの最後だけを返す | 既に生成された詳細の成功分岐と基本説明が矛盾する。削除成功時は成功通知と空入力用データ、失敗時は対象なし通知と入力保持、という二経路を示す。三項演算子を条件・真値・偽値として解析し、単なる文字列拾いを使わない。優先修正対象。 |
| RQ-006 | データ・責務範囲 | 基本SCR-020 L25と基本SCR-013 L25は同じ16表を処理対象として列挙。詳細SCR-020 L38-86も同一表を複数回列挙し、根拠は `literal_sql`。`detail/core.py:L247-249`は依存ファイル全体のCRUDを関連データへ追加、L255で集合化する | 呼出しから到達した表と、同一依存ファイル中にあるだけの表を区別できない。ファイル依存とイベントから到達する操作を別に保存し、イベントID/呼出経路/操作IDで関連付ける。16表すべてが本機能では未使用と断定するには業務原本の再解析が必要だが、現行表示にはその区別がない。 |
| RQ-007 | DB設定・確定・例外 | 基本SCR-018 L177-180ほかは「対象データを読み取る」「当該SQL式の列指定・実行時引数」「呼出側または接続の設定に従う」等。具体WHEREはあるがバインド値と呼出側トランザクションが本文では閉じていない | 取得項目、各プレースホルダーの由来、確定主体、失敗時の取消・保持を読者が判断できない。直接解析済み部分と呼出側未解決部分を分け、未解決ならQA-IDと対象経路を明記する。全SQLに推定コミット/ロールバックを追加しない。 |
| RQ-008 | 項目の必須・候補 | 基本SCR-018 L47の店番は「任意（仮定）」だがL114-118では未設定を拒否。L55の性別候補は「固定候補：／」。必須区分とイベント条件を相互照合していない | 画面共通の入力可否と操作別の必須を区別できず、空候補を定義済みに見せる。操作条件付き必須を列記し、既知の拒否分岐と矛盾する仮定はレビューで戻す。候補値が未解決なら空区切りでなく未解決理由・QAを記す。 |
| RQ-009 | 詳細文書・検証文章 | 詳細SCR-020 L14-32はソース表の列挙、L93の検証シナリオは「各イベントの分岐条件を満たす入力」「分岐ごとの応答・状態変更を照合」。`documents.py:L102-114`はstepsをそのまま表にする | ソース対応は有用だが、入力・返却・状態・例外の契約や具体的な正常/異常ケースがない。根拠表を維持しつつ、各イベントの契約とケースを説明する。ソース実行なしの期待候補であることは維持し、実行合格へ読み替えない。 |

基本13文書の読取り集計：概要の定型句13/13、条件番号だけの表現7/13、取得・設定fallback6/13、少なくとも一つの返却だけのイベントを含む文書2/13。これらは文書単位の出現数であり、イベント総数や欠陥総数ではない。

## 既存quality.pyとテストの有効範囲・限界

現行ゲートを廃止する理由はない。`validation/quality.py`は生成器のparserをimportせず別走査を行い、画面の欠落、画像欠落/破損/微小/単色、DB文書・列欠落、日本語論理名、操作説明、項目DBバインドを確認する。原本義務をP1から消して隠せない設計も有用である。

一方、下記は人間向け文章の合格を保証しない。

| 箇所 | 現行判定 | 見逃す意味と必要な検証 |
| --- | --- | --- |
| `quality.py:L40-42` | 日本語を一文字以上含み、一部の未確認語を含まない | 「関連情報を取得・設定」のような日本語の埋草も通る。対象・動詞・値・成立条件・結果が解決済みfactへ対応するか確認する。 |
| `quality.py:L298-303` | 表/CRUD/パス/Javaメソッドscopeが一致、説明欄8文字以上＋日本語 | 処理説明の具体性、実際の設定値、成功と失敗、取消の範囲は照合しない。長い定型句を増やしても改善にならない。 |
| `quality.py:L324-340` | P2のバインド表示と一致、DDL列存在、evidenceパス/行番号が有効 | evidence行がその意味を本当に支持するかは確認しない。IDと位置に加え、原文範囲・hash・主張属性の対応を検証する。 |
| `quality.py:L341-362` | reviewed機能はイベント検査をskip、narrativeなしのlegacyもskip。概要/手順見出し、P2 stepsの非空、フロー/ER画像掲載 | 公開本文の手順内容・guard・副作用・結果をP2と照合していない。画像が対象イベントに対応することと、説明が正しいことを別に検査する。reviewedも意味検査から免除しない。 |
| `quality.py:L140-144` | 書込義務キーはパス/表/CRUD/Java scope | 同じメソッドの同表・同CRUD複数経路を一義務へ統合するため、各条件/値/取消範囲の省略は検出できない。操作のsource span＋呼出経路を義務IDに含める。 |
| `shared/schemas.py` | 文書block/featureの基本型と必須key | イベント内容・主張と根拠・状態遷移の完全性はschemaで要求していない。source hash/span付きfactとclaim参照の別schemaが必要。 |

`tests/test_independent_quality.py:L47-116`の正常・欠落・改変例は手書きで、生成結果丸写しではない。しかし主に欠落/英語名/画像/DB説明の不在を扱い、意味は誤っているが長い日本語になっている負例はない。正常fixtureの確定説明もL40「呼出側のトランザクション設定に従う」で合格する。`test_event_procedures.py`はif/else、same-line、早期return、loop、finally、guardの順序を検査しており有用だが、職員context削除、return内委譲、三項成功・失敗の人間向け説明は検査していない。`test_bind_templates.py:L177-180`は未知条件を原文として保持する安全性を確認するが、読者が条件番号だけで操作を理解できるという保証にはならない。

本調査で既存テストを実行していないため、過去PASSを今回の改訂検査として流用していない。

## 改善ワークフロー案

1. **許可入力を固定する。** 原本hash/ソースspan/案件ID/解析器版を封印したsource capsuleへ必要な画面・handler・呼出先・型・SQL/DDLだけを格納する。案件の原仕様、正解資料、過去の完成文章を解析正解として混ぜない。秘密値は送信前に除去し、除去箇所を未解決として保存する。原本コメントや文字列は命令として扱わない。
2. **AIで根拠付きfactsを解析する。** 機能責務、開始契機、event→call、入力/正規化/保存、状態before/after、branch guard/true/false、結果、例外/確定主体を型付きJSONにする。各claimはsource ID・span・hashへ参照し、事実・推論・未解決を分ける。コード名だけを業務意味へ断定しない。
3. **機械検証でfactsを封印する。** 許可範囲・hash・line span・ID参照・重複・データ種別・操作境界を確認する。三項演算子とreturn内call、セッションremove/set、トランザクションのowned/caller/unknownを別属性として保持する。未解決を消して『不存在』にしない。
4. **AI原稿をfactsから作る。** 目的と正常結果を先に説明し、必要な状態・分岐・例外を続ける。基本では論理名、詳細では物理名と契約を使う。段落/表の意味単位ごとにclaim/fact IDを保存し、文書には根拠の参照を付ける。SQLリテラル表を本文説明の代用品にしない。
5. **独立レビューを別jobで実行する。** 原稿作成の履歴・思考・先の自己評価を渡さず、原稿と封印facts、必要な許可source spanを与える。省略、誤った状態、反転条件、guardのない副作用、偽のcommit、根拠のない役割、単なる定型句をseverity/claim/source根拠付きで指摘する。生成者と同じモデルでも独立プロセス・独立prompt・独立証拠確認を行う。同モデルは判断誤りまで独立である保証にならない。
6. **指摘を根拠へ戻して改善する。** 解釈が違えばfacts再解析、説明不足なら原稿修正と区別する。元factを書き換えて誤原稿へ合わせない。未解決はQAとして残す。上限回数まで新しいreviewを行い、重大指摘が残る場合は未承認成果として保存し、検証済み公開をしない。
7. **P3/P4境界を維持して公開する。** AIによる業務解析・原稿・レビューはP2の追加工程で実行し、承認されたdoc planをresolvedへ封印する。P3はresolvedだけを読み、input/src-dynamic/P1の追加読取りや新しい推論をしない。既存構造/画像/DBゲートと新しい意味ゲートを通してからMD/HTML/PDF/Excelへ変換する。

保存候補：`facts.json`、`draft.json`、`review.json`、`revision.json`、`final-review.json`、各source/prompt/schema/結果のhash、CLI版、実行時間・終了値・timeout・usage。原稿と根拠、レビューを同じファイルで上書きしない。usageが実レスポンスにない場合はnull/not_reportedとし、呼出成功やトークン数を推測しない。

優先する意味の負例は、RQ-005の三項分岐反転、RQ-003の削除→取得への誤変換、RQ-002のreturn内call欠落、ログイン戻り先の二経路が同じ結果になる原稿、同一表の別分岐書込省略、guardを外した副作用、未確定transactionへの確定宣言、空候補を既知扱い、必須拒否と任意表示の矛盾である。合格基準は文章長・単語数・AIの自己採点ではなく、重要claim全件の根拠対応、重要分岐と状態のカバー、矛盾ゼロにする。読みやすさは別の人間レビュー項目として扱う。

## ローカルCLI・API・runtimeの実確認

openai-docsスキルを利用した。CLIについては実機のローカル版helpを根拠とした。OpenAI製品の現行サービス提供可否、料金、モデルアクセス権はこの調査で照会していない。

| 対象 | 確認結果 | 実行可能性の限界 |
| --- | --- | --- |
| Codex CLI | `C:\Users\tujin\AppData\Local\OpenAI\Codex\bin\2e5e00daee91c61d\codex.exe`、`codex-cli 0.162.0-alpha.17.2`。PATHにはnvmの`codex.cmd`/拡張子なしも存在 | --version/exec --helpのみ実行。モデルjobは未実行。wrapperとexeの版一致は未確認。 |
| CLI出力・隔離flag | exec helpで `--output-schema`、`--json`、`--output-last-message`、`--ephemeral`、`--sandbox read-only`、`--cd`、`--config key=value`、`--model`、`--ignore-user-config`を確認 | flagの実動作はモデルjobなしのため未試験。後続実装は利用中CLIのhelp/実終了値でunsupportedを扱い、fake成功や弱いsandboxへのfallbackをしない。 |
| ユーザー設定 | `C:\Users\tujin\.codex\config.toml`存在。root model設定あり、値は `gpt-6.1-sol`。root model_provider設定・model_providers節なし | 後続CLIはユーザー既定を継承し、モデル名を固定する必要はない。設定を変更しない。 |
| APIキー存在 | OPENAI_API_KEY、AZURE_OPENAI_API_KEY、ANTHROPIC_API_KEY、GEMINI_API_KEY、CODEX_API_KEYはprocess/user/machineすべてfalse。auth.jsonのAPIキー欄もfalse | 値は出力・保存していない。別の秘密管理場所まで調査しておらず、環境全体で永久に鍵不存在とは断定しない。 |
| Codexログイン | auth.json存在、tokens/access_token/refresh_tokenはいずれも存在trueのみ確認 | token値・account IDは出力・保存していない。期限、利用枠、モデルアクセス、外部呼出成功は未確認。ログイン存在を実行の自動承認にしない。 |
| Python | bundled `C:\Users\tujin\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe` は3.12.14 | `-B`と管理コードのみ実行。PILあり、openai/anthropic/requests/httpx/jsonschema/markdown_it/bs4はこのruntimeのfind_specでなし。プロジェクト全体の他venvまで不存在とは断定しない。 |
| その他runtime | node v24.16.0、dotnet 10.0.401。curlあり | バージョン確認だけ。HTTP/API/業務コードを実行していない。 |
| ローカルLLM | PATHのollama/llama-cliなし、11434/1234のListenなし | モデルserverへ接続していない。他PATH/他port/コンテナーのモデルまで調査していない。 |

後続provider実装案：CLIパスは明示指定を優先し、なければGet-Command相当で実在する一つの実行経路へ解決する。1jobを独立したephemeral processとし、source capsuleをcwd、read-only sandbox、`--config approval_policy=never`、schema指定、JSONLイベント、final出力を使う。今回確認したユーザー設定を保存・変更せず、モデル指定の省略でユーザー既定を継承する。処理時間制限、終了値、最終JSONのschema検証、timeout/error/not_run、実際に返されたusageを保存する。

`read-only`は書込み制限であり、禁止原仕様の読取りまで遮断する十分な境界ではない。cwdをcapsuleに変更するだけでも外部パスの読取りを保証しない。原仕様・spec-eval・他案件をプロセスから見えなくする実行環境/OS境界と、許可ソースだけのcapsuleを合わせる必要がある。stdin/promptには秘密値を含めず、入力原本をimport/起動しない。model jobの開始はこの調査後の明示された実行工程に限る。

## 調査入力のSHA-256

パスは `agents/reverse-agent/` を基準とする。元ファイルに独自版宣言がないものはこのhashで識別し、今回新しい合格や仕様版を付けていない。

| ファイル | SHA-256 |
| --- | --- |
| output/md/基本設計書/基本設計書_SCR-020_職員番号入力.md | 04F15D69C4ECA4582782B5A67CF9419A236B13A007881E7FAFC928501A5F67C3 |
| output/md/基本設計書/基本設計書_SCR-013_年金自動受取予約管理システム - ログイン.md | D0CEBB309E9F95B0E7BBD139DE5183397E86251EDBAF973DF40809CBDF6A6B86 |
| output/md/基本設計書/基本設計書_SCR-018_新規・変更・削除.md | 98FC46FE88DD8E68A77624AD2B23A7CB67ECB676FFB66C600873EE0E213D9CF1 |
| output/md/詳細仕様書/詳細仕様書_SCR-020_職員番号入力.md | 79B04D999547816F2C318AF9DC156F4D62074E364FF5C48E012139ADEFEB0B31 |
| output/md/詳細仕様書/詳細仕様書_SCR-013_年金自動受取予約管理システム - ログイン.md | 8640519796C271D96BB1F242ED20E50B13440D3B8F0F4ED1F8A6EF8B2AB49D45 |
| output/md/詳細仕様書/詳細仕様書_SCR-018_新規・変更・削除.md | 67B74AFBCE7AD65511615F80F4D30AB7B30F7E1B2F5C1478A6DD73D47AA288A1 |
| src/contextbase/validation/quality.py | AA9F4FF2CAE726AD996CFFCB931B1F4E013B1731A90B76A06A061CA8ACA1022B |
| src/contextbase/tests/test_independent_quality.py | 2BE7AE58C8385DBA2EDF0DF024BCA0E0C15E773D2D16092B2E9F44ED4F8605B0 |
| src/contextbase/tests/test_event_procedures.py | D0E019A2F5E3C2D7BFE49732713DFC7F6760E9D2992F260A784B2B1F47C1770B |

今回の出力は本調査報告のみ。AI解析・原稿生成・レビューの実行、provider実装、品質ゲート改訂、既存テスト実行、派生文書再生成、顧客承認、原仕様との逆生成採点は未実施。

## 後続工程の追加記録：provider実装・専用回帰

上記は最初の調査工程の記録である。その後、親Agentからprovider実装の指示と、ユーザーによる基本/詳細設計の分析材料利用の明示許可が届いた。既存の調査結果を新実行結果へ読み替えず、以下を別工程として記録する。

- 変更は `src/contextbase/ai/provider.py` と専用 `src/contextbase/tests/test_ai_provider.py` の新規追加。root所有のcapsule/prompts/schemas/workflow、既存生成器・品質検査、業務プログラム、原仕様は編集していない。
- providerは指定workspace、新規排他的job、ユーザー既定model、ephemeral/read-only、approval_policy=never、project_doc_max_bytes=0、UTF-8 stdin、JSONLイベント、最終応答ファイルで動作する。CLI回答の原バイトと原schemaを保持し、JSON修理・fence除去・値補完・fallback成功は行わない。実際に返されたusageだけを記録する。
- 参考設計はcapsule manifestの `mode=training-assisted`、`trainingReferenceAuthorizedByUser=true`、`referenceSpecificationIncluded=true` と `referenceFiles` の `reference-designs/` 配下への明示供給が揃う場合だけ許可する。旗なし/falseはsource-only。意図と観測動作を区別し、参考設計を実行証拠にしない。spec-eval・期待採点表・領域外は引き続き禁止する。providerは許可フラグとパスだけを読み、参考設計本文自体を開いていない。
- 専用回帰42件をPython3.11.9で実行しPASS、終了値0。全model subprocessをfixtureへ置き換えた。timeout/非0/回答欠落/不正UTF-8/JSON/schema/イベントerror、usage欠落・複数、原回答保持、重複key/NaN、job上書き拒否、CLI解決、原schema不変、reference境界を確認した。外部schema参照はネットワークを防ぐため拒否し、未解決の局所参照も失敗として記録する。
- 依存はrootが方式内 `.tmp/pydeps` に用意したものをPYTHONPATHで使用し、user/global Python環境を変更していない。実行は `python -B -m unittest contextbase.tests.test_ai_provider -v`。生ログは `.tmp/provider-unit-03.raw.log`、SHA-256 `777CEC635C75844D109474AA2C5A0470181CA3899F2CEA35486BF8EEF9A92A7A`。途中31件/36件のログは別名で保持し、最終42件と区別した。
- 最終provider SHA-256 `9FC4FE95CF7FD000EBD1EA7C350489F50F9244A49DF2205BD9DCBB5683F96BDD`。専用tests SHA-256 `9A8F0462F900E822AC2EAE3790F9CF32EA793F436CB3FE9B92D84CAAECBA00E7`。この版を親Agentへ凍結・結合可能として通知した。
- 実Codex接続のroot smokeは別記録 `provider-smoke/answer.txt` の `REVERSE_AI_READY` と同JSONLのturn.completed usageを読み取り確認した。これは親Agentの接続確認であり、この担当の42回帰は実LLMを呼んでいない。構造化AI原稿の意味品質・本providerの実LLM schema負例・顧客承認・逆生成採点の合格として扱わない。
- この担当はモデル重みのtraining/fine-tune、外部送信、業務input実行を行っていない。read-only/cwdとプロンプトだけで領域外読取り・model tool動作まで強制隔離済みとは報告しない。`model_tool_actions_audited=false` を記録し、source capsuleとOS境界はcallerの責任とする。
