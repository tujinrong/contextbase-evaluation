<!-- spec-meta: {"schema":"spec-md/1.0","documentId":"AG-REQUIREMENT-README","version":"0.1","path":"agents/designs/requirement-agent/README.md","sheets":[{"heading":"状態と入口","kind":"GRID","sheet":"01_状態と入口"},{"heading":"担当範囲","kind":"GRID","sheet":"02_担当範囲"},{"heading":"今後の整備","kind":"GRID","sheet":"03_今後の整備"}]} -->
# requirement-agent

定義版0.1／2026-10-28。状態はtemplate/draft。要件定義Agentのひな型で、業務での実行検証は未実施。

## 状態と入口

要件定義専用のAG-REQUIREMENTを今後整備するための骨子である。[AGENT.md](AGENT.md)に役割・範囲・工程の骨子、[PROMPT.md](PROMPT.md)に実行要求と起動指示のひな型を置く。今回は特定projectの要件文書を生成していない。

## 担当範囲

目的、対象利用者、業務範囲、機能/非機能要求、制約、業務データ/外部IF要求、受入条件、QAと根拠を整理する。要件ID・採用版・利用者確定前提を[基本設計Agent](../basic-design-agent/AGENT.md)へ渡し、基本設計を踏まえた実装粒度は[詳細設計Agent](../detail-design-agent/AGENT.md)が扱う。

対象projectと方式は実行要求とproject索引で選び、業務仕様はspecRoot=project/spec/方式ID/、ソースはsourceRoot=project/srcs/方式ID/へ分ける。既存の確定前提・QA決定を継承し、特定業務や別方式の前提を汎用Agentへ埋め込まない。要件定義専用ルールと工程は今後このフォルダで管理する。

## 今後の整備

利用者が実行を依頼した時点で、対象資料・成果物構成・要求ID/変更管理・優先度と決定者・非機能の測定条件・レビュー方法を具体化する。今回は3文書のひな型だけであり、運用手順の完成、業務受入れ、設計・実装・実DB・実Excel・正式採点の完了を意味しない。

構造確認、本文レビュー、実行検証と受入試験を区別し、入力/出力の版・ファイル・ハッシュ、対象、未決・未実施を報告する。ひな型の改善だけで後続工程を自動実行しない。
