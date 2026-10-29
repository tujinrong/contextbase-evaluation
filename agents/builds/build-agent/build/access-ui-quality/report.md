<!-- spec-meta: {"schema":"spec-md/1.0","documentId":"AG-ACCESS-UI-QUALITY-REPORT","version":"1.0","path":"agents/builds/build-agent/build/access-ui-quality/report.md","sheets":[{"heading":"対象と根拠","kind":"GRID","sheet":"01_対象と根拠"},{"heading":"変更内容","kind":"GRID","sheet":"02_変更内容"},{"heading":"検証と未実施","kind":"GRID","sheet":"03_検証と未実施"}]} -->
# Access画面品質のAgent改善報告

版1.0／2026-10-29。外部レビューを参照し、Accessの仕様書作成とプログラム作成のAgentを改善した。規則・検査処理の検証記録であり、既存Access製品の品質判定ではない。

## 対象と根拠

入力は[外部レビュー](../../../../../references/access-review.md)「AI向け業務画面作成・修正ルール」v1.0、2026-10-29、SHA-256 `f55df1f0edfa800710ae9fad2cd7f234e6d5018e82d27ec61f03ae219bd6034b`と、今回の全体規則・各Agent定義。原文は変更していない。画面タイプごとの設計と利用者の合理性・統一性・見やすさ・操作性を、[共通規約](../../../../../docs/Access画面品質規約.md) v1.0へ採用した。

工程固有の規則/手順の正本は各Agent配下、方式の確定前提・業務仕様は選択specRoot、ソースと実製品の検査はsourceRootのままとする。既存の確定条件、認証、保存方式、DBをこの改善で変更しない。

## 変更内容

| 対象 | 今回の版 | 主な改善 |
| --- | --- | --- |
| requirement-agent | 入口0.3、専用規則/工程0.2 | 利用者タスク・環境・保存単位と4観点の受入条件を、要求ID/根拠/QA・基本設計への引継ぎへ対応 |
| basic-design-agent | 入口1.10、専用規則1.1、工程1.2 | タイプ別の領域/状態、役割別トークン、対象常時識別、長文/一覧幅、反映/保存/取消をモック・レビュー・完了条件へ対応 |
| detail-design-agent | 入口1.2、専用規則/工程1.1 | Form/Page/Control、寸法/単位/列幅、状態・キー/イベント、未反映入力とバッファ/DB境界、独立した合格条件と証拠を具体化 |
| build-agent | 入口7.11、Access生成チェック1.3 | 事前の期待値固定から最終ACCDBの実部品/画面/実操作/保存後再読込へ接続。本文11ptとタイトル等の採用値を区分 |
| UI適合検査 | 文書/validator 1.1、schemaVersion 1 | 新規約を凍結したAccessにaccessScreenChecksを要求。全画面/9カテゴリ・必要kind/根拠・不正な対象外・万能rule流用・操作証拠欠落を検出 |
| 入力管理/manifest | 今回のスクリプトSHAはvalidation参照 | Access限定で新規約を凍結。入力規約の変更/欠落やUI gate不適合時は旧outputs.jsonを失効。他方式へAccess追加条件を強制しない |

寸法の初期値と100/125/150%の確認候補を正式な対応条件へ昇格させず、全欄同幅・全画面中央寄せ・文字縮小や余白率を品質の代用にしない。保存のない画面に保存機能を追加せず、保存/取消に該当する操作だけDB再読込を要求する。

## 検証と未実施

| 検証 | 結果と範囲 |
| --- | --- |
| preflight-tests.mjs | PASS 100 assertions。凍結入力/独立方式/読取り専用検査、新規Access規約の欠落・不正・更新と旧manifest失効、他方式非影響。隔離fixtureのみ |
| ui-conformance-tests.mjs | PASS 177 assertions。9カテゴリ・全画面・rule参照/必要kind/流用・対象外理由・操作証拠/改変・旧入力・他方式非影響。隔離fixtureのみ |
| 構文と差分 | 変更した5本のJavaScriptをnode --checkで確認。git diff --checkで空白エラーなし |
| 文書と独立レビュー | 版/path/章・sheet/LIST/リンクと根拠、工程間引継ぎ、schema/実行経路を確認。最終ファイルの版・SHAと検査範囲は[validation.json](validation.json)に記録 |

既存のproject仕様・ソース・ACCDBを今回の改善で更新/再生成していない。実Access起動、実画面描画、キーボード/IME、実DBの保存/取消、DPI/Office別環境、利用者受入、正式採点は未実施。fixtureと文書の合格を実製品合格へ転記しない。正式評価値はnullとする。
