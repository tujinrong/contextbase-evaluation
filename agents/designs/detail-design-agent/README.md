<!-- spec-meta: {"schema":"spec-md/1.0","documentId":"AG-DETAIL-DESIGN-README","version":"1.0","path":"agents/designs/detail-design-agent/README.md","sheets":[{"heading":"使い方","kind":"GRID","sheet":"01_使い方"},{"heading":"担当と保存先","kind":"GRID","sheet":"02_担当と保存先"},{"heading":"確認と引継ぎ","kind":"GRID","sheet":"03_確認と引継ぎ"},{"heading":"移行した記録","kind":"GRID","sheet":"04_移行した記録"}]} -->
# detail-design-agent

定義版1.0／2026-10-28。詳細設計専用Agent。役割IDはAG-DETAIL-DESIGN。

## 使い方

[AGENT.md](AGENT.md)が役割・入力隔離・出力範囲の契約、[PROMPT.md](PROMPT.md)が実行指示と指定例である。専用規則は[rules/詳細設計書作成ルール.md](rules/詳細設計書作成ルール.md)、執筆・検査・描画・記録は[workflows/詳細設計.md](workflows/詳細設計.md)へ保存する。共通docsと他Agentはこの正本を参照し、詳細設計専用の別正本を作らない。

対象project・方式・詳細化する機能と入力版を指定し、選択specRootの確定前提・採用プロファイル・QAを先に読む。既存ID、利用者確定事項、方式固有の認証/DB/入力/版/監査を維持する。特定業務の項目や検索条件、方式数・採用DBを汎用Agentの既定値へ固定しない。

## 担当と保存先

経験5年程度の実装者が、物理コントロール/バインド/変数/型、API/DTO/クラス/引数戻り値、SQLと物理DB定義の設計、判定・例外・MSG/復帰・確定境界まで実装できる詳細仕様を対象とする。raw/正規化/保存長・単位・NULL、候補・項目移送/更新、3画面分類・寸法・Text行桁/キー、検索/ページングと基本設計の対応を記す。基本設計11列を詳細へ強制しない。

業務仕様・確定前提・QA・採用済み規約版はproject/spec/方式ID/、方式別の最終検査とmanifestはproject/srcs/方式ID/build/spec-generation/、中間物は同方式の.tmp/へ置く。方式を持たない共通工程だけproject/build/detail-design/または当Agent/build/と対応する.tmp/を使う。新しい再利用可能な専用機械処理は当Agentのscripts/へ追加する。過去結果の別名累積をせずGitで履歴を管理する。

仕様生成の試験では、実行要求に明示したsourceRoot/.tmp/等へ採用前ドラフトを保存できる。正式specRootと実出力先、対象版・ハッシュ、検査・採用の状態を記録し、試験生成だけで既存正本を上書きしない。

要件定義は[requirement-agent](../requirement-agent/README.md)（今回はひな型）、基本設計は[basic-design-agent](../basic-design-agent/README.md)を参照する。複合依頼は許可範囲と前提・QA・ID・入力版を引き継ぎ、同じ実行内で担当契約を切り替えてよい。詳細設計だけの依頼から全工程へ展開せず、基本設計や要件の未決を自動承認しない。

## 確認と引継ぎ

AIが本文を執筆し、機械処理は収集・形式検査・ハッシュ・保存・描画を担当する。基本と同じ画面/状態のHTML配置、各IDから型/API/SQL/DB列/CHK/MSG/復帰への対応、対象版の構造・意味レビュー・描画/目視を確認する。既存入力・QA・正式試験コード/fixture・範囲外ローカル変更を保全する。

描画記録はMDと抽出HTML断片のSHA-256、サイズ・倍率・ブラウザー版、状態、計測と目視結果を持つ。Textの文字モックとCCSID/DBCS・端末キー・IMEの実機確認、仕様帳票と実Excel/印刷は別状態である。構造・描画・独立レビューのPASSをアプリ/DB/受入・正式採点へ読み替えず、未採点ならformalScore=nullとする。

最終報告には対象project・方式・工程、入力/出力の文書ID・版・ファイル・SHA-256、改訂理由、検査範囲と結果、未決・未実施を示す。規則更新だけの場合はprojectの仕様一式を自動再生成しない。アプリ実装、DB作成/接続/投入/SQL実行、ビルド、実Excel帳票生成・変換/印刷、正式採点は別の実行要求で扱う。

## 移行した記録

旧汎用仕様Agentの定義版8.7を詳細設計の役割へ整理し、当Agentの定義版1.0として管理する。build/spec-layout/の3記録は移動前の仕様配置検査の証拠を内容・ハッシュごと保持した。当時のAgent名・projectId・絶対パス・入力hashは歴史的識別であり、現在の詳細設計Agentを実行/再検証済みとする証拠ではない。現行の定義・起動・参照先はこのフォルダを使用する。
