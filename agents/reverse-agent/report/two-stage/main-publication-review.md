# ２段階解析の実装・再実行・main反映記録

確認日：2026-10-08。変更先：tujinrong/contextbase-chatgpt のmainのみ。V2リポジトリは変更していない。

## 反映結果

| 対象 | 値 |
|---|---|
| 変更前main | 4f606d45f10b7078f77437b071f715dabda77b36 |
| 実装コミット | 74e1c44dc2bc9162be0d8c44546678f92878138a |
| 再生成成果物コミット | 1407ab6c178de6d8d97e4a3cf39a6f7cc118da33 |
| Actions実行 | 37765137238、rebuildジョブ113270826521、全工程success |
| input Gitツリー | 807791c000c42b9b9074fe9b39f322a78a0a0066、変更なし |
| output Gitツリー | 52076529b47e7a96f79a8ccf8495eb22f3d624df |
| ContextBase Gitツリー | 5677f7617c3ca3c591ad90fb35b33e87af9fab3e |

Actions：https://github.com/tujinrong/contextbase-chatgpt/actions/runs/37765137238

## 実装した処理分離

P1：`src/contextbase/foundation/`。原本の構造、機能骨子、テーブル基礎情報、原本索引を `ContextBase/01-foundation/` へ保存する。画面とPageModelを結び付け、DTOと物理DB表を分ける。

P2：`src/contextbase/detail/`。P1の世代と原本ハッシュを照合して関連ソースを再読込みし、条件付きフロー、順序、状態操作、関連メソッド候補を解析する。項目・イベント・データ関連・シナリオ・説明・文書ブロックを `ContextBase/02-detailed/` へ保存する。完成MDを差し替えるだけの方式ではない。

P3：`src/contextbase/specification/`。P2のハッシュ検証済みresolvedデータと素材だけからMDを生成する。input、P1、src-dynamicの解析コードを参照しない。

P4：既存の `src/docsite/`。MDからHTML・PDF・Excelへ変換する。V2の表紙・通常・一覧の３パターン、通常の太線外枠、枠外無罫線のコードは変更していない。

統括は既存pipeline.pyから独立プロセスを呼び出す。共通スキーマ・ハッシュ・封印検証はshared、独立評価はvalidationへ分離した。

`src/specgen/adapters/csharp_flow.py` は案件横断の構文解析。C#プライマリーコンストラクターをクラス全体のメソッドと誤認する問題を避け、OnGet・OnPost・OnPostClearを別処理として取得する。単純な早期return後の否定条件を後続処理へ関連付ける。

`src-dynamic/jsbrms-pilot/` は案件固有の名称指定・構造化レビューJSON・画面素材作成を担当する。extension.jsonの承認状態、原本11ファイルのハッシュ、アダプターコードのハッシュを検証してP2からのみ使用する。旧MCTERP/TKL用コードは維持している。

AGENTS.mdに工程境界、src/src-dynamicの役割、QA、ContextBaseとキャッシュの区別を追記した。添付の設計方針は `docs/doc/ContextBase２段階解析_実装方針.md`、実装範囲と制限は `docs/doc/２段階解析_実装と制限.md` に保存している。

## GitHubの完全checkoutによる再生成結果

| 検証対象 | 結果 |
|---|---|
| input | 182ファイル、変更なし |
| P1の解析対象 | 54ファイル |
| 機能骨子 | 19件：画面8、共通処理等11 |
| P2の原本再読込み | 54ファイル |
| 静的処理単位 | 117件 |
| イベント | 79件 |
| 検出した物理テーブル | 0件 |
| データオブジェクト | 18件。物理テーブルと別管理 |
| MD | 39文書 |
| HTML | 40ページ、ブラウザー検査失敗0件 |
| PDF | 39文書・117ページ、生成時検証成功 |
| Excel | 39冊・151シート、生成時検証成功 |
| 全自動テスト | 232件成功：specgen37、docsite109、contextbase86 |
| 今回追加したテスト | 25件 |
| P1/P2/文書間の契約検査 | 316件、エラー0件 |
| Pilot既存追加検査 | 20件成功、5シート、216セル、2画像 |

182ファイルすべてに同じ深さの業務解析を行った意味ではない。解析対象・除外・未対応は原本索引とreportへ記録している。物理テーブル0件は検出結果であり、本番環境にDBが存在しない保証ではない。

以前のoutputと解析キャッシュを入力にせず、新規領域で全工程を実行した。検証成功後にContextBaseとoutputを入れ替え、QA回答とreport記録は保持した。全体結果の判定は `verified_structure_only`。

## P3の独立性と途中再開

P2だけを一時領域へコピーし、input・P1・src-dynamicへのファイルopenを拒否する独立プロセスでP3を再実行した。39MDと2素材の計41ファイルが通常生成と完全一致した。

ソース変更、中間情報の改変、参照不整合、QA回答保持、同一内容のキャッシュ再利用、output削除後の再生成をテストした。--coldなしのP1/P2は入力・解析器・依存情報のハッシュ一致時だけ結果を再利用する。P1の世代が古い場合はP2を止めて再解析を要求する。

これは完全な動的依存追跡や、全案件で最小範囲だけを再計算する保証ではない。原本を再読込みして世代を検証し、解析結果の再利用範囲を保守的に判定する実装である。

## 保存後の読み戻し

Actions artifact ID：11544057014。元ZIPのSHA-256：80d7f67f8b1258ab67ad3960a009cc8bfc6f354ca0fc21077d8b86261e697818。

取得したoutput・ContextBase・src・src-dynamicからGitツリーSHAを再計算し、mainの該当ツリーと一致した。Excel生成時のZIP/XML検査とは別に、artifact_toolで全39冊を読み込み、151シート・4,864非空セルを照合し、すべて一致した。

Pilotの表紙と項目表はローカル生成版、保存後のイベント仕様冒頭は取得したCI版を描画確認した。ローカル生成PDFの画面・遷移図ページも確認した。全PDFページやExcelデスクトップの全印刷結果を目視承認したという意味ではない。

CI Pilot XLSXのSHA-256：a910219b4c38f91a24ab01cb69dd144fca33c0b99f5d8f752474d3f0ba569446。

## 今回残る範囲

実行基盤と現行generic経路の２段階化を実装した。添付計画全項目の同一精度での完了を意味しない。

- C#/Javaの解析は構文・静的条件・呼出候補の抽出であり、完全な型解決、動的呼出、例外伝播、全実行経路の解析ではない。
- 職員番号入力は構造化レビュー情報を原本照合して適用する。その他の機能も骨子から再解析するが、同等の業務レビュー済みとは扱わない。
- Excel等のテーブル定義書の汎用自動読取り・採用、ALTERの適用順確定、実DB照合は未実装または未検証。定義候補と矛盾は保存する。
- 帳票・バッチ・API等の一覧には静的な候補が含まれる。完全な業務境界の承認、全画面の共有レイアウト再現、全機能のCRUD/ER図・開発規約の充実は後続課題として残る。
- 他言語は既存の限定抽出を再利用している。旧MCTERP/TKL専用経路は今回２段階移行していない。
- P2→P1の訂正提案保存先は用意したが、共有定義を自動承認・自動修正しない。
- QA回答は自由記述を勝手に事実化せず、approvedの型付き採用判断と依存ハッシュを検査する。
- 実アプリ・本番DBの実行同等性、全環境の画面・印刷品質は未検証。

詳細は `report/incomplete/foundation.json`、`report/incomplete/detail.json`、`report/incomplete/未完成事項.md`。質問・回答は `QA/questions.json` と `QA/仕様確認.md`。

## 再実行

```shell
python -m pip install -e ".[pdf]"
# Pilotの画像生成とブラウザー検査にはGraphvizとPlaywright/Chromiumも必要
python -m pip install playwright==1.57.0
python -m playwright install chromium

# 全工程・全形式をクリーン再生成
python -m contextbase rebuild --replace-output --pdf --excel --browser

# 工程単独。最初は全件で実行する
python -m contextbase.foundation --root .
python -m contextbase.detail --root .
python -m contextbase.specification --root .
python -m contextbase build --pdf --excel

# 確定済みP1からPilotだけ再解析・文書更新
python -m contextbase.detail --root . --feature 100008
python -m contextbase.specification --root . --feature 100008

# 独立検証
python -m contextbase.validation --root .
```
