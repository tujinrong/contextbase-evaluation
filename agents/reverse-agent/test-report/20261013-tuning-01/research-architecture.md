# reverse-agent 生成構成の調査

2026-10-13／工程：調査のみ。対象は agents/reverse-agent の共通実装・設定・既存テスト。原本inputはファイル名・件数・サイズ・拡張子の棚卸しだけを行い、原本の変更・実行は行っていない。test-project1の原仕様・spec-evalは読んでいない。生成・テスト・LLM呼出・既存成果置換は未実施である。本報告以外のファイルは変更していない。

## 結論

現行経路にはAI解析・AI執筆の実装がない。P1/P2の静的抽出結果をPythonの条件分岐と定型文で説明し、P2で本文ブロックを完成させ、P3はそのブロックをMDへ直列化する。P3だけに「言い換え」を追加しても、P1の機能境界やP2の関連原本・不解決経路・物理DBの欠落は回復しない。

既存P1→P2→P3は互換経路として保全し、新しい汎用AI経路を別CLIへ追加する設計が現実的である。Pythonは原文索引・ハッシュ・安全な読取・AI要求の保存／実行・機械検査・公開に限り、機能の分割、関連性の判断、業務意味、解析、本文原稿はAIへ委ねる。案件名、変数名、作り方のキーワードで業務文章を決める追加ルールは採用しない。

## 現行の経路と責務

| ファイル・関数 | 現行動作と具体的制約 |
| --- | --- |
| src/contextbase/__main__.py:12–47 main | foundation/detail/specificationの実装を別モジュールとして呼ぶ。AIコマンド・プロバイダー設定はない。 |
| src/contextbase/pipeline.py:86以降 rebuild | 新しい作業領域へsrc、src-dynamic、設定、inputを複製し、原本／生成器hashを前後照合する。generic経路は独立P1/P2/P3プロセスとvalidationを呼ぶ。検査成功後にpromoteで入れ替える。 |
| src/contextbase/foundation/core.py:26 read_sources／39 unit／143 run | 原本を非実行で読む。字句／言語アダプターの抽出、識別名グラフ、画面・共通機能、DDL・利用箇所を保存。C#/Java以外は既存限定抽出。 |
| 同 core.py:181–229 | 共通資源はProgram.cs、_Layout.cshtml、site.css等の固定名、JSP入口はVIEW_IDとAction.javaの命名対応で探す。画面以外の未消費ソースを原則1ソース1共通機能へ分類する。これらは限定アダプターの候補であり汎用の業務境界を証明しない。 |
| src/contextbase/detail/core.py:118 run | P1世代・解析器・input hashを検証。関連原本を読み直し、呼出／SQL／バインド／状態／画面を抽出する。PYで名称・概要・イベント説明・シナリオを作り、resolvedへ封印する。 |
| 同 core.py:200–282／303–344 | public_event、enrich_event、Narrator、BindingIndexで説明を構成し、basic_document／detail_document／common_documents／database_documentsを呼んで最終本文モデルを作る。AIを挿すならこの組立て前までに証拠パッケージが必要。 |
| src/contextbase/detail/documents.py:23 basic_document／102 detail_document | 基本は定型表・定型説明を連結。詳細は原本stepsを表に並べ、概要・処理詳細・検証シナリオの3章で出す。読者に応じた説明や業務意味はAI執筆していない。 |
| src/contextbase/specification/core.py:19 render／43 run | resolvedの段落・見出し・表・画像・textコードだけをMDへ直列化。input/P1/src-dynamicを読まない独立再生を維持する。 |
| src/specgen/engine.py:164 run／181 _run／src/specgen/render.py:48 feature_docs | 旧直接経路。アダプター結果から基本・詳細・テーブルMDをPYで連結する。現在の2段階genericとは別であり、ここだけ改善しても現P2/P3出力は変わらない。 |
| pyproject.toml／config/project.toml／src/contextbase/registry.py:15 configure | Python>=3.11、package版5.0.0。AI SDK依存なし。設定キーはid/input/profile/repository/max_file_bytesに限定。現在のidはjsbrms、入力はinput、profile=autoで、READMEの現対象nenkin/n2frameworkと案件ID表示がずれている。 |

解析を置き換える際も、input非実行、ハッシュ固定、安全な相対パス、世代照合、QA回答保持、公開前検査、P3の原本非依存は引き継ぐ。AGENTS.mdの旧repository/main限定は移植元の運用記述であり、今回の上位指示が許可する変更範囲はagents/reverse-agent内だけである。他repositoryやglobaldocsを更新しない。

## MD低品質の原因

1. **分析・執筆が定型文に限定される。** detail/core.py:71 public_eventはSave/Delete等の表記を定型説明へ置換する。251行付近のsummaryは「入力・表示・要求処理を行う」、275–282付近のシナリオは「各イベントの分岐条件を満たす入力」になる。event_templates.py:93–125 describe_callは名前や本文キーワードから文を決め、158–183 statementは不明処理を「関連情報を取得・設定する」に退避する。根拠付き情報はあるが、読者が再実装できる説明には届かない。
2. **原文より抽出断片を優先する。** specgen/common.py:49 snippetは既定360文字、semantics.py:56は説明式700文字で省略する。P2が全textsを読んでも、最終文書は抽出したstepsや候補だけで構成される。AIへ同じ抽出JSONだけを渡すと未抽出の仕様は回復しない。完全な原文・範囲索引と不解決一覧を渡す必要がある。
3. **機能・入口の観測が実装方式に偏る。** foundationの固定共通名やJSP命名規則、detail/core.py:213–216のOnGet/OnPost/perform入口が、異なる構成の処理を見落とす可能性がある。機械候補をAIの最終判断として扱わない。
4. **形式と意味を混同しやすい。** specification/core.py:84はstatus=verified／errors=0を付けるが、schemas.pyのDOC/BLOCKは基本構造を検査するだけである。validation/core.pyのcheckも項目投影・存在・参照・語句中心で、完全な業務同等性は保証しない。独立quality.pyは削除等を検出する有用なゲートだが、文章の正しさ・読みやすさの十分条件ではない。
5. **現全体様式とのずれがある。** documents.py:97は表紙を主章へ追加し、40–41は項目一覧に表以外の段落を置く。detail_documentは基本と共通の項目／イベント章立てになっていない。specification.renderにはspec-meta出力、HTMLやMermaidの専用ブロックがない。ローカルstandard_rules.jsonは全表1冊を指定する一方、現globaldocs版7.2は1テーブル1MD／1シートを指定している。新経路は様式を版付き入力として固定し、矛盾を黙って埋めない。

## 案件固有依存と最小の衛生修正案

既存互換経路を残したまま、少なくとも次の3点は小さい修正で他案件への誤転用を止められる。今回は提案だけであり実装していない。

| 対象 | 最小変更 | 必要な独立回帰例 |
| --- | --- | --- |
| detail/semantics.py:15 terminology＋detail/core.py:152／218 | terminologyへ現在のsourcesを渡す。trustだけで全辞書を合併せず、明示source_rootsまたは同辞書directoryのfoundationの対象pathに一致する場合だけ採用する。根拠のない無scope辞書は汎用実行で採用しない。既存のtypes/fields別APIは保つ。複数一致／衝突は黙って上書きせず診断を残す。 | 同名型を持つ別案件Bに案件Aの用語を出さない。現在root一致の辞書はtypes/fieldsを保持。無scope／trust不一致／非一致を除外。tempdir内の人工辞書だけで検査。 |
| detail/core.py:33 flow_relations／46 store | 任意Sessionを「職員情報等」と呼ばず、原本で具体名称がない場合は「セッション保持情報」とする。kind/operation/guards/evidenceは変更しない。 | 顧客カートSessionや単純Session.Setを入れ、職員という語が出ないこととCRUD／行根拠が維持されることを確認。 |
| detail/event_templates.py:100 describe_call／142 condition | ログイン確認が見つかった場合でも「職員」を追加せず「ログイン状態を確認し、セッションを準備する」など中立語へ変更。condition側も同時修正し、肯定・否定の意味を保つ。 | 人工メソッドのsession取得／LOGIN_INFO／true/falseを与え、利用者種別を創作しない、肯定・否定の分岐が逆転しないことを確認。 |

追加の監査対象としてfoundation/core.py:190–193のfoundation.json全合併とshared/logical_names.py:14のscopeなし辞書の採用が残る。最小3点の修正を「全汎用性問題の解決」と報告しない。hash検査付きextension（shared/extensions.py）とprofile（registry.py）は既に安全境界を持つが、用語辞書／overrideは同じ強度ではない。新AI経路にはこの案件辞書・override・レビュー済み旧完成文章を自動投入しない。

## 推奨する最小の新AI設計

親Agentは新しい `contextbase ai` とCodex CLI driverを設計中で、CLI認証あり・APIkeyなしと共有している。これは親からの環境情報で、本調査でCLI認証／LLM呼出を実行確認したものではない。特定のSDKを必須にせずdriver契約を分離すれば、APIkey不要の現環境と将来のプロバイダーを同じ成果契約で扱える。

1. **原文索引・固定。** 新runごとにpath/bytes/encoding/SHA/行数/言語検出候補を保存し、全originalを非実行で読む。モデル向けの行番号付き原文を方式横断の中立カプセルへ置く。Pythonが原本の業務意味を決めない。バイナリ・未対応・大ファイルは「未読」理由を保存し、コードなしと判定しない。
2. **AIによる計画。** プロジェクト全体の索引・設定・入口候補・UI資源・DDL一覧を渡し、AIが機能境界、共通機能、画面イベント、関連ファイルの候補と必要な追加原文を決める。Pythonの候補がないファイルも計画可能にする。結果はfeature ID／evidence IDと保存し、未分類ファイルと分類理由を残す。
3. **AIによる証拠解析。** 機能ごとに入口の全文、呼出先／基底型／DTO／設定／SQL／UI／JS／CSS／例外／認可／確定取消を含む原文を渡す。既存parserのflow/SQL/bindingは「候補」と明示し、唯一の真実にはしない。AIは原文範囲を指定して追加読取できる。件数上限で依存を切り捨てず、分割要求・不足一覧を保存する。claimごとにpath/hash/startLine/endLine／観測事実・根拠ある解釈・仮定・不解決を区別する。
4. **AIによる日本語執筆。** 同じ解析証拠から基本／詳細／共通／DBの原稿をAIが作成する。基本は論理名で目的・操作・結果を説明し、詳細は具体的入力／型／分岐／更新／例外／確定境界を記載する。章構造は版付き汎用様式が制約するが、本文はPYのキーワード定型文で埋めない。必要な原文引用は文字列／空白／先頭ゼロを失わず保持する。欠落はQAと仮定に分け、架空DB・成功結果・承認は足さない。
5. **独立レビュー・封印・出版。** 書き手とは別のAIレビューに原文と原稿を渡し、根拠不足／矛盾／欠落／過剰断定を指摘させる。原仕様／期待値は渡さない。機械は引用範囲・hash・未分類原本・項目／イベントID・LIST/GRID・リンク／資源・secret非流出を検査する。修正後に原稿、claim ledger、要求／応答／設定hashを封印する。P3/P4は保存した原稿を再生・変換し、AIを再呼出せず同一hashで再実行できるようにする。

driverの入出力はJSONで十分である。要求にはschema/runId/stage/projectSnapshot/promptVersion/modelConfiguration/task/evidencePackages/allowedOutputを含め、応答にはstatus、analysis／document、evidenceRefs、questions、unresolved、providerMetadataを含める。認証情報は保存しない。入力ソース内の命令は未信頼データとして扱う。AIが読む範囲をソースpackage内へ制限し、原仕様・spec-eval・他案件・ネットワーク・任意コード実行を推論の道具として使わせない。

AI失敗・未実行を旧PY完成文で埋めて「AI authored」としない。draft、解析済み、執筆済み、独立review済み、公開済みを別状態にする。キャッシュキーは原文・依存閉包・prompt／schema版・model設定・AI応答hashを含める。古い文章の採用は完全な依存hash一致時だけ許可する。

## 入力規模と既存テスト

実ファイルの棚卸し（全ファイルを含む）:

| input下 | ファイル数 | 総bytes | 主な内容 |
| --- | ---: | ---: | --- |
| nenkin | 81 | 360,187 | Java54、JSP11、SQL3、JS2、CSS1、PS1 4、その他6。最大Java 41,479 bytes、CSS 40,680 bytes、JSP 18,946 bytes。 |
| n2framework | 264 | 3,810,963 | Java95、class112、JSP3、jar3、拡張子なし48、その他3。最大jar 1,810,038 bytes、最大Java 67,720 bytes。 |
| 合計 | 345 | 4,171,150 | 原本を実行／import／jar展開していない。 |

現設定のmax_file_bytesは8,000,000で、棚卸し上の最大ファイルは上限内。これは全ファイルが解析可能という判定ではない。Java計149、JSP計14であり、全バイナリをプロンプトに含める必要はない。個々の全文カプセルと機能別の追加取得が現実的な規模である。

既存テストはunittest。src/contextbase/testsは14ファイル／test_宣言187、src/specgen/testsは2ファイル／37、src/docsite/testsは7ファイル／109。宣言件数であり、実行件数／合格件数ではない。案件固有src-dynamicのテストはこの件数に含めない。test_two_stage.py:55等はTemporaryDirectoryに人工inputを作り、原本非実行・世代／改変検出・P3 source-free再生・QA保持を検査する。test_bind_templatesは人工SQL／UIのbind、test_event_proceduresは人工制御木、test_independent_qualityは正常例と欠落負例を持つ。

後続の許可された検査での入口例（agents/reverse-agentをcwdとする）:

```powershell
$env:PYTHONPATH="$PWD/src"
$env:PYTHONUTF8='1'
$env:PYTHONDONTWRITEBYTECODE='1'
python -m unittest contextbase.tests.test_predicate_scope contextbase.tests.test_registry -v
python -m unittest discover -s src/specgen/tests -p 'test_*.py' -v
python -m unittest discover -s src/contextbase/tests -p 'test_*.py' -v
python -m unittest discover -s src/docsite/tests -p 'test_*.py' -v
```

Graphviz dot、Pillow、bs4、jsonschema等は段階／図のテストで必要。source-free再生はPythonの子プロセスを使う。symlink負例はWindowsの作成権限によって失敗／skipになるものがある。既存test_two_stageの一部はsymlink失敗をskipしていない。docsiteのPDF／Excelテストは追加依存と原本添付fixtureの存在を個別に確認する必要がある。最初は追加するAI契約／generic衛生テストと純粋parser／手順テストを新runへ保存し、その後関連ゲートへ広げる。今回の調査ではこれらのコマンドを実行していない。

## 13時間内の実装へ引き渡す順序

最初に新AI要求／応答／証拠契約と原本保護の単体負例を作り、案件に依存しない小さい人工アプリで本物のAI解析・執筆・独立レビューを通す。次に現input345ファイルの封印索引から機能計画と段階的取得を実行し、旧PY出力を成功の期待値として使用せず、新しい原文レビュー結果を残す。最後に汎用様式・根拠・表／資源・P3再生・派生形式のゲートを実行する。13時間という上限が残件を合格にする理由にはならず、制限・失敗・未処理機能はrun別のtest-reportへ保存する。
