# ContextBase — ソースからMD・HTML・PDF・Excel仕様書を生成

`input/`の原本を実行せずに解析し、`output/md`へ機能別・共通仕様、`output/html`へ閲覧用文書を生成します。画面レイアウトのHTMLは各MDの中に保持します。

## 現在の対象

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

新対象のネイティブ再実装Pilotは未作成です。`--native`が付いた共通ワークフローでも、新対象に対応する比較がない場合は`not_run`を記録し、過去案件の成功を流用しません。詳細は[解析と再生成](docs/MCTERPの解析と再生成.md)を参照してください。

## 閲覧と検証

[機能一覧MD](output/md/機能一覧.md)から個別仕様を開きます。配布ZIPでは`output/html/index.html`が閲覧の入口です。CSSとSVGを内包し、閲覧には外部CDNを必要としません。原本へのGitHubリンクにはネットワークとリポジトリの閲覧権限が必要です。

現対象の解析範囲と未完成事項は`report/incomplete/`、質問は`QA/`、構造照合は`report/generic/evaluation.json`、実行全体は`report/rebuild/result.json`、表示変換は`report/docsite/validation.json`を確認します。機械的な一致と業務仕様の完全性・顧客承認は別判定です。

## 別案件

入力先と案件IDを変更し、`profile="auto"`または`"generic"`で調査します。レビュー済みの対象だけをJSONの照合条件で選定してから対象別コードを読み込みます。`input`をPythonのモジュール検索先へ加えることはありません。別案件の名称辞書・業務ルールの流用を防ぎます。

VB6、Access、Java、.NET、Vue+API等には形式検出と限定抽出がありますが、対象特有の共通基盤や動的処理には別アダプターと検証が必要です。未抽出を「不存在」と扱いません。[構成と拡張](docs/構成と拡張.md)を参照してください。

## Excel仕様書とQA運用

```shell
python -m contextbase rebuild --replace-output --pdf --excel
python -m contextbase excel
md-to-excel --markdown spec.md --xlsx spec.xlsx
```

Excelは `output/Excel/`。MDと同じ名前・フォルダで、表紙と章別シートに展開します。v2を参照した10列の項目一覧、日本語、固定見出し、印刷設定を備えます。質問は `QA/`、未完成・未検証事項は `report/` に保存し、成果物は仮定を明示して出力します。運用規則は `AGENTS.md`、詳細は `docs/doc/MDからExcel仕様書.md` を参照してください。

## V2様式・職員番号入力Pilot

添付V2の実生成経路 `render_document_xlsx.py` を起点に必要な処理を移植し、標準Excel出力をV2の表紙・62列本文・10列項目表へ変更しました。職員番号入力は画面・遷移図を埋め込んだ5シートのPilotとして、現行ソースをレビューした仕様を出力します。

[V2移植とPilotの詳細](docs/doc/V2テンプレート移植と職員番号Pilot.md) ／ [PilotのMD](output/md/基本設計書/基本設計書_100008_職員番号入力.md)

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
