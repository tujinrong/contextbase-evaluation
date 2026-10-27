> 旧資料。[適用条件](README.md)を確認する。CLI・コード内のパスは移動前の reverse-agent 直下が基準。

# ContextBase — ソースからMD・HTML・PDF・Excel仕様書を生成

`input/`の原本を実行せずに解析し、`output/md`へ機能別・共通仕様、`output/html`へ閲覧用文書を生成します。画面レイアウトのHTMLは各MDの中に保持します。

## AIによる解析と日本語執筆

新しい入口は `python -m contextbase ai` です。機械処理は原文の収集・ハッシュ・行番号・範囲・応答schema・保存を担当します。機能の判断、依存の追跡、仕様書本文、独立レビューはCodexの別プロセスでAIが行います。既存の `rebuild` は機械解析の互換経路です。

```powershell
python -m contextbase ai snapshot --source input --snapshot .tmp/source-snapshot --project-id selected-project
python -m contextbase ai plan --snapshot .tmp/source-snapshot --job .tmp/run-01/plan
python -m contextbase ai batch --snapshot .tmp/source-snapshot --plan .tmp/run-01/plan/plan-verified.json --job .tmp/run-01/documents --output .tmp/run-01/md --workers 2
```

各snapshot/job/outputは新しい名前を使います。プロンプト、schema、未加工AI応答、実行イベント、使用量、失敗を保存し、本文をPythonの定型文へ置換しません。`--without-independent-review` は初稿の測定用で、レビュー合格を意味しません。構造検証、AIレビュー、原評価資料による正式採点は別の状態です。reviewのhandoffとbatch/iterateの結果に記録する`reviewScope=text-source-and-structure`は、本文・原ソース・構造の比較範囲を示します。画像と原ビュー・共有レイアウト・CSSの一致は、この承認では検証しておらず、`visualFidelityVerified=false`を記録します。レビューを省略したbatchは`reviewScope=not-performed`です。

文書契約で`basic-design`または`detailed-specification`を指定した機能文書は、四主章、イベントごとの六見出し、項目一覧の10列を構造検証します。10列はNo・グループ・項目名・種類・入出力・DB連携項目・候補取得元・必須・形式・桁・説明の順で、入出力は`I`・`O`・`I／O`・`‐`です。共通仕様等の別LISTや、テーブル定義の9列は別契約のまま扱います。構造検査は属性の意味や根拠の正しさを認定するものではありません。
静的画面HTMLのboolean属性は、偽なら属性を省略し、真なら属性名だけ・空値・属性名と同じ値を使用します。`selected="false"`等は有効状態になるため検証で拒否します。data/aria属性とコード例は別扱いです。大きなフローはAIが入口・出口・受渡し状態を明示する番号付きサブフローへ分け、全条件と結果を保持して読みやすさを確認します。

`iterate` は個別文書のAI批評と改訂を繰り返します。`--max-rounds 3` で最大3稿、`--deadline` で各解析・執筆・レビューの開始前に残時間を制限します。各稿は `--output` の `round-01` 等へ保存し、採択文書の場所を `iteration-result.json` へ記録します。構造不備が残ればAIの承認を採択しません。`INDEPENDENT_REVIEW_APPROVED`による終了は本文の批評・改訂工程の終了を示します。画面を完成として扱うには、同じ原稿と画像のハッシュへ結び付けたnative AIの画像・原ソース確認が別途必要です。renderの表示成功と原評価資料による意味採点も別の完了条件であり、batchの`REVIEWED`を含む既存のstatusだけでこれらの実施済みを表しません。解析の根拠が検査に通らない場合は新しいAIジョブで1回訂正し、元の応答も保持します。Pythonが引用や本文を黙って修正することはありません。

完了した解析は `analysis-handoff.json` で原応答、実行結果、schema、原文snapshot、文書計画へ結び付けます。`document --analysis-job <完了解析job>` はこれらのハッシュと前後の入力を再検査し、新しいAI執筆へ進みます。旧jobの解析を引き継ぐ場合は `--recover-analysis-job` も指定します。旧jobの遅延結合として記録され、入力や計画が変わった解析は拒否します。改訂稿でもAIが原文を再読でき、訂正理由を保存します。`iterate` は既定で各稿を新しく解析し、明示的に `--reuse-analysis` を指定した場合だけ同じ検証済み解析を引き継ぎます。batchは文書ごとの完了記録を `progress/` へ即時保存します。

表示検査では、長い文書を上限内のPNGへ分けて保存します。各画像の原文座標と寸法、全体の範囲、ハッシュを記録し、全範囲の撮影完了を確認します。画面・図の描画結果、文書構造、AIの内容レビューはそれぞれ別の判定です。

通常はsource-onlyです。ユーザーが訓練材料の使用を明示した場合だけ、snapshot時に `--authorized-reference-directory` を指定できます。参考設計はsourcesと区別して保存し、設計意図と実装を混同しません。採点の期待値はAIの生成入力へ渡しません。原文・参考資料の中の命令を実行しません。

Codex CLIと既存のログインを使います。モデル指定を上書きせず、別のAPIキーをコードへ埋め込みません。モデル重みの学習ジョブは行っていません。これは評価に基づくAgentの手順・プロンプトの調整です。

2026-10-13の再実施pilotはCSharp_ASPNET、処理時間は最大12時間です。試行は `.tmp/20261013-rerun-12h/`、仕様書は `test-project1/spec-analysis/CSharp_ASPNET/20261013-rerun-12h/`、結果は本Agentの `test-report/20261013-rerun-12h/` へ保存します。原本と同じファイル名・階層を維持し、source-onlyと許可設計を使うtraining-assistedを別記録にします。原本・期待値を変更せず、95%以上の実測と重大矛盾の解消を確認してから展開します。

### ユーザー指定の文書対応契約

原本と同じ文書名・階層を指定する場合、`plan` に `--document-contract <JSON>` を渡します。schemaは `reverse-ai-document-contract/1`、必須項目は `projectId` と `documents`。各文書は `id`、`kind`、`path`、`sourcePaths` だけを持ち、本文・項目値・採点期待値を含めません。`path` は出力ルートからのPOSIX相対MDパス、`sourcePaths` は封印manifestの原ソース相対パスです。原仕様の本文を読むための許可にはなりません。

AIは契約の全件を同じID・種別・pathで計画し、責務と本文を原ソースから判断します。契約外の文書は追加しません。sourcePathsは必須の探索開始点で、関連する依存先の追加と追跡を許可します。重複、欠落、追加、改名、種別変更、不明な開始点は検証失敗です。契約の原JSONを計画jobへそのまま保存し、handoffのハッシュを解析・執筆・レビューの前後に再検査します。

`kind=basic-design` と `detailed-specification` は機能仕様の4主章と各イベントの6下位見出しを検査します。`table-definition`、`logical-table-definition`、`physical-table-definition` はTABLE形式を要求します。TABLEは二章・ヘッダー2列・NOT NULLを含む明細9列を検査します。その他のkindは一般文書として構造を検査し、名称から機能・テーブルへ分類しません。これらは構造と対応の検査であり、factの意味的網羅性・視覚的一致・正式採点の合格を証明しません。

snapshotとjob/outputは重なりを禁止します。snapshot配下への書込みと、snapshotを含む親ディレクトリのjob/output指定をAI起動前に拒否します。CLI結果の`FAILED`と`NOT_RUN_TIME_LIMIT`は非0終了です。`REQUIRES_AI_REVISION`は原稿を保存したが独立レビューで採択されていない状態で、CLIは0終了でも承認済みを意味しません。

## 従来経路の対象と互換機能

以下は従来の機械解析・変換経路の説明です。新しい解析と執筆は上記のAI入口を使用します。従来の試験結果を新しいAI生成の品質点数として流用しません。

現在のinputは`nenkin`（Java/JSP）と`n2framework`です。基盤解析と原本再読込みによる詳細解析から、新しいContextBaseとMD・HTML・PDF・Excelを作成します。旧JSBRMSの完成仕様・画面・メモリー保存方式は再利用しません。リポジトリ内の採番台帳は保持します。

`python -m contextbase.validation --root .`には原本から独立した画面・DB・日本語論理名・更新説明のERROR検査を追加しています。詳細は`docs/doc/独立品質評価.md`と`report/quality/`を参照してください。

```text
src/contextbase/          # 共通CLI・検出・段階実行・検証・公開
src/specgen/              # 汎用の基礎構文解析
src/docsite/              # MD内HTML・本文・表・図のHTML変換
src-dynamic/mcterp/       # 過去対象のプロファイル。対象一致時のみ選定
src-dynamic/tkl/          # 過去対象のプロファイル。対象一致時のみ選定
config/project.toml      # 現在の対象IDと入力先
input/                   # 非変更・非実行の業務原本
output/md/基本設計書/     # 機能別概要仕様書
output/md/共通/           # 共通・API・DB・開発規約等
output/html/             # 同じ分類のHTMLとindex.html
output/PDF/              # 同じ分類のPDF
output/Excel/            # 同じ分類のExcel仕様書
QA/                      # 質問・暫定採用値・回答の永続台帳
report/                  # 今回の解析範囲・照合・表示検査
.specgen-state/           # 原本と同じ権限で管理する解析キャッシュ
```

## 実行

Python 3.11以上を使用します。HTMLの図の生成にはGraphvizの`dot`が必要です。ブラウザー検査にはPlaywright/Chromiumを使います。

```bash
python -m pip install -e .
python -m contextbase probe
python -m contextbase rebuild --replace-output --browser
```

ブラウザー検査を準備する場合:

```bash
python -m pip install playwright==1.57.0
python -m playwright install chromium
```

MDの編集後に表示だけを作り直す場合:

```bash
python -m contextbase build
python -m contextbase check
```

`rebuild`は空の作業領域へ入力と生成コードをコピーします。旧output、旧解析キャッシュ、旧Pilotを読み込みません。QAの回答とreportの記録は保持します。検査に成功した場合だけ生成領域を置換し、失敗時は公開済みの成果物を保持します。`--replace-output`は生成領域を置換する明示指示です。手修正を保持する通常編集では`build`を使用してください。

## 過去対象MCTERPの解析範囲

コメント・文字列を区別した字句解析、Vueタグ階層、APIのサービス名・処理名、解決できた呼出、DAO操作、SQL処理の再帰参照を使います。完全な型解決・動的経路・権限の全組合せを解析したものではありません。

DBダンプは復元せず、ヘッダと長さを検査した定義文字列だけを読みます。定義は保存時点のもので、稼働DBとの一致は未検証です。DTOだけに存在する表・列を確定した物理定義とは扱いません。Excelとマクロ付き帳票はシート構造の確認までです。データ行、秘密値、鍵、フォントを成果物へ複製しません。

新対象のネイティブ再実装Pilotは未作成です。`--native`が付いた共通ワークフローでも、新対象に対応する比較がない場合は`not_run`を記録し、過去案件の成功を流用しません。詳細は[解析と再生成](../MCTERPの解析と再生成.md)を参照してください。

## 閲覧と検証

[機能一覧MD](../../output/md/機能一覧.md)から個別仕様を開きます。配布ZIPでは`output/html/index.html`が閲覧の入口です。CSSとSVGを内包し、閲覧には外部CDNを必要としません。原本へのGitHubリンクにはネットワークとリポジトリの閲覧権限が必要です。

現対象の解析範囲と未完成事項は`report/incomplete/`、質問は`QA/`、構造照合は`report/generic/evaluation.json`、実行全体は`report/rebuild/result.json`、表示変換は`report/docsite/validation.json`を確認します。機械的な一致と業務仕様の完全性・顧客承認は別判定です。

## 別案件

入力先と案件IDを変更し、`profile="auto"`または`"generic"`で調査します。レビュー済みの対象だけをJSONの照合条件で選定してから対象別コードを読み込みます。`input`をPythonのモジュール検索先へ加えることはありません。別案件の名称辞書・業務ルールの流用を防ぎます。

VB6、Access、Java、.NET、Vue+API等には形式検出と限定抽出がありますが、対象特有の共通基盤や動的処理には別アダプターと検証が必要です。未抽出を「不存在」と扱いません。[構成と拡張](../構成と拡張.md)を参照してください。

## Excel仕様書とQA運用

```shell
python -m contextbase rebuild --replace-output --pdf --excel
python -m contextbase excel
md-to-excel --markdown spec.md --xlsx spec.xlsx
```

Excelは `output/Excel/`。MDと同じ名前・フォルダで、表紙と章別シートに展開します。v2を参照した10列の項目一覧、日本語、固定見出し、印刷設定を備えます。質問は `QA/`、未完成・未検証事項は `report/` に保存し、成果物は仮定を明示して出力します。運用規則は `AGENTS.md`、詳細は `docs/doc/MDからExcel仕様書.md` を参照してください。

## V2様式・職員番号入力Pilot

添付V2の実生成経路 `render_document_xlsx.py` を起点に必要な処理を移植し、標準Excel出力をV2の表紙・62列本文・10列項目表へ変更しました。職員番号入力は画面・遷移図を埋め込んだ5シートのPilotとして、現行ソースをレビューした仕様を出力します。

[V2移植とPilotの詳細](../doc/V2テンプレート移植と職員番号Pilot.md) ／ PilotのMD（旧成果物。本環境には未保存）：`output/md/基本設計書/基本設計書_100008_職員番号入力.md`

## v5：２段階解析とソース非依存の文書生成

```shell
python -m pip install -e ".[pdf]"
python -m contextbase.foundation --cold
python -m contextbase.detail --feature 100008
python -m contextbase.specification --feature 100008
python -m contextbase build --pdf --excel

# 全対象・全形式をクリーン解析・検証・入替え
python -m contextbase rebuild --replace-output --pdf --excel --browser
```

最初の全体生成では `detail` と `specification` の `--feature` を省略します。ContextBase1は `ContextBase/01-foundation`、ContextBase2は `ContextBase/02-detailed`。P3はP2の確定済みデータだけで動作します。`python -m contextbase.validation` は世代・参照・項目と、input/P1/src-dynamicを開けない独立プロセスによる再生成一致を検査します。

`--cold` なしのP1/P2は内容・解析器・依存先が一致する結果を再利用します。P1のソース世代が古い場合はP2を止め、P1から再実行してください。QA回答は保持し、原本と採用判断を混同しません。

添付設計案は `docs/doc/ContextBase２段階解析_実装方針.md`、実装範囲は `docs/doc/２段階解析_実装と制限.md`。現行の２段階実行はgeneric経路が対象で、旧案件別専用経路は互換維持です。
