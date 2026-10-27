<!-- spec-meta: {"schema":"spec-md/1.0","documentId":"AG-BASIC-DESIGN-README","version":"1.0","path":"agents/basic-design-agent/README.md","sheets":[{"heading":"使い方","kind":"GRID","sheet":"01_使い方"},{"heading":"成果物","kind":"GRID","sheet":"02_成果物"},{"heading":"確認と引継ぎ","kind":"GRID","sheet":"03_確認と引継ぎ"}]} -->
# basic-design-agent

定義版1.0／2026-10-27。利用者要求から基本設計を作成するための運用入口。役割IDはAG-BASIC-DESIGN。

## 使い方

[AGENT.md](AGENT.md)が役割・入出力・工程の契約、[PROMPT.md](PROMPT.md)が起動指示と実行例である。CodexへPROMPT.mdと対象project・方式・基本設計の要求を渡す。専用の業務アプリや自動採点プログラムを起動する構成ではない。[spec-agent](../spec-agent/README.md)の契約を参考に、基本設計へ範囲を絞ったAgentである。

全体docsを読み、specRoot=project/spec/方式ID/とsourceRoot=project/srcs/方式ID/、許可入力・出力、除外、版・ハッシュを固定する。新projectは利用者の明示作成依頼があるときだけ作る。既存projectは許可された構造と書式を参照し、別題材の業務値や確定前提を転用しない。

選択specRootの利用者確定前提・採用プロファイル・QA決定を先に読み、変更指示や新たな矛盾がなければ次回も継承する。設計者の採用判断を利用者承認と呼ばず、方式固有の値を他方式へ無断展開しない。AIが業務本文を執筆し、機械処理は保存・検査・ハッシュ・描画に使う。

## 成果物

方式README、プロジェクト情報・前提、必要な共通設計、1機能1基本設計、テーブル索引・関係・1テーブル1分冊、必要な帳票設計、QA・出典を各specRoot内へ置く。ファイル名・文書ID・対象範囲は実行ごとにmanifestへ列挙する。複数方式の業務仕様は方式内で完結させ、project/spec/README.mdは配置索引に限定する。

機能設計は概要・項目一覧・イベント仕様・補足説明を主章とし、各イベントの6下位見出しに論理的な処理・DB操作・結果/例外を記す。テーブルはHEADERと9列LISTを同じシートに置く規約を適用する。画面はWEB系・WinForms系・Text系の分類と方式標準部品へ従い、概要内のHTML/CSSだけを正本とする。別HTMLや画面PNGを仕様へ併置しない。

帳票は元データ、項目、順序、表示、印刷、改ページ、長文、空値、失敗・再出力まで設計する。Excel経歴書を出すシステムの設計と、基本設計書をExcelへ変換する作業を区別する。基本設計だけの依頼では、詳細仕様・DDL・アプリ・ACCDB・実DB・実Excel帳票・採点表を生成しない。

2026-10-27の初回対象はsample-project2、方式はAccessとCSharp_ASPNET、題材は社員経歴管理である。具体的な業務仕様は[方式索引](../../sample-project2/spec/README.md)から選択し、このAgentへ埋め込まない。test-project1は今回許可された構成・書式の参照先であり、社員業務の正解入力ではない。

## 確認と引継ぎ

要求・項目・イベント・CRUD・テーブル・帳票の意味を照合し、spec-meta、見出し、LIST/TABLE、ID、リンク、方式内依存を検査する。画面HTMLはsourceRoot/.tmp/へ同じ断片を抽出して描画・目視し、サイズ・倍率・状態・対象版・断片ハッシュ・計測/目視を記録する。静的モック、実Excelの印刷、製品実機の操作確認は別の状態である。

最終検査記録と入出力manifestは各sourceRoot/build/spec-generation/へ固定名で更新する。方式を持たない共通記録だけproject/build/basic-design/を使用する。中間生成・失敗試行は.tmp/へ置き、履歴はGitを使う。原入力・QA・正式試験コード・fixtureと対象外ローカル変更を保全する。

最終報告には入力/出力の版・ファイル・SHA-256、検査範囲、設計判断、未決・未実施を含める。構造・意味レビュー・描画/目視・実Excel・実装・ビルド・DB/実機・正式採点を分け、未採点ならformalScore=null。基本設計の存在を実装着手可能な詳細仕様の完成や受入合格と扱わない。次工程へは文書ID・版、機能/項目/イベントID、確定前提・QA決定を引き継ぐ。
