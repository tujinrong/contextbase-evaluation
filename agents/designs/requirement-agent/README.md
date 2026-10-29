<!-- spec-meta: {"schema":"spec-md/1.0","documentId":"AG-REQUIREMENT-README","version":"0.3","path":"agents/designs/requirement-agent/README.md","sheets":[{"heading":"状態と入口","kind":"GRID","sheet":"01_状態と入口"},{"heading":"担当範囲","kind":"GRID","sheet":"02_担当範囲"},{"heading":"実行例と確認","kind":"GRID","sheet":"03_実行例と確認"}]} -->
# requirement-agent

定義版0.3／2026-10-29。既存仕様からの逆生成に加え、Access画面の利用者タスク・環境・保存単位・4観点の受入条件を基本設計へ引き継ぐ。

## 状態と入口

[AGENT.md](AGENT.md)に契約、[PROMPT.md](PROMPT.md)に実行指示、[専用規則](rules/要件定義書作成ルール.md)に書き方、[処理手順](workflows/要件定義.md)に調査・執筆・検査・記録を置く。Codexが契約を読んで実行する。専用CLIや固定業務文章の自動生成器は設けない。

0.1はひな型、0.2は仕様からの逆生成手順を具体化したもの。0.3は[Access画面品質規約](../../../docs/Access画面品質規約.md)を要件整理・受入条件・引継ぎへ接続する。要求起点の新規案件への汎用適用性や利用者承認の完了を表さない。今回の実施範囲は対象projectの固定build/記録で確認する。

## 担当範囲

requests-to-requirementsは要求・原資料から、spec-to-requirementsは既存仕様書から、目的・利用者・範囲・機能/データ/非機能・受入条件・QA・根拠を整理する。後者も当Agentの機能で、実装を解析するreverses配下のAgentとは契約が異なる。

業務入力と要件定義書.mdはspecRoot=project/spec/方式ID/で閉じる。sourceRoot=project/srcs/方式ID/には固定build/記録と.tmp/だけを書き込む。認証・採用DB・利用者確定前提・QA決定を継承し、他方式の要求や結果を転用しない。

要求ID・採用版・前提・QAを[基本設計Agent](../basic-design-agent/AGENT.md)へ渡し、実装粒度は[詳細設計Agent](../detail-design-agent/AGENT.md)が採用基本設計を踏まえて扱う。依頼されていない後工程へ展開しない。

Accessでは利用者が行う作業、操作対象の識別、利用環境と入力方法、保存方式・保存単位・確定時期・取消範囲を要求として整理する。合理性・統一性・見やすさ・操作性の受入条件に、対象要求ID・根拠・確認方法を付ける。具体的な配置とモック作成の手順は基本設計Agentに委ねる。

## 実行例と確認

「対象projectの指定方式について、既存仕様からspec/方式ID/要件定義書.mdを逆生成する」と依頼できる。実行時にproject索引、方式、入力版・ハッシュ、出力、確定前提を固定する。方式数や業務値を汎用Agentへ固定しない。

構造・資料ハッシュ検査と本文レビューを行い、記録はsourceRoot/build/spec-generation/requirement-definition/へ更新する。manifest.jsonに対象・規則・入出力、validation.jsonに検査範囲と結果、report.mdに判断・残件・未実施を記す。方式なし全体記録はproject/build/requirement-definition/へ集約する。

受入条件は未実施の確認計画で、アプリ・DB試験合格や利用者承認ではない。Excel/PDF変換、実装、実DB、受入試験、正式採点は当工程に含めない。

完了時はUI要件から基本設計へ渡す利用者タスク・環境・保存/取消契約・4観点の受入条件、未確認とQAを示す。画像から動作を確定せず、暫定寸法・倍率を対応保証へ変更しない。既存の認証なし等の確定前提を継承し、画面品質の改善を理由に業務機能や保存方式を追加・変更しない。
