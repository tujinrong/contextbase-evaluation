<!-- spec-meta: {"schema":"spec-md/1.0","documentId":"AG-REQUIREMENT-PROMPT","version":"0.1","path":"agents/designs/requirement-agent/PROMPT.md","sheets":[{"heading":"ひな型の状態","kind":"GRID","sheet":"01_ひな型の状態"},{"heading":"実行要求の骨子","kind":"LIST","sheet":"02_実行要求","key":["項目"]},{"heading":"今後の起動指示","kind":"GRID","sheet":"03_今後の起動指示"}]} -->
# requirement-agent 実行指示ひな型

定義版0.1／2026-10-28。状態はtemplate/draft。業務での実行検証は未実施。

## ひな型の状態

[AGENT.md](AGENT.md)は要件定義専用Agent（AG-REQUIREMENT）の契約骨子、[README.md](README.md)は整備状況と入口である。今回はひな型を配置する段階で、特定projectの要件定義は開始しない。

## 実行要求の骨子

| 項目 | 指定内容 |
| --- | --- |
| projectId / creationAuthority | 対象project、新規作成の明示許可または既存要件の改善 |
| stage / scope | requirement-definition。目的、対象利用者、業務範囲と対象外、今回整理する要求 |
| methodIds / specRoot / sourceRoot | 指定方式とproject/spec/方式ID/、project/srcs/方式ID/。未確定の方式はQAで扱い、自動作成しない |
| requiredDocuments / requirementIds | 採用する成果物構成、文書ID・版、要求IDと変更管理の方針 |
| premiseProfile / decisionSources | 既存の利用者確定前提、QA決定、根拠ID・版・SHA-256・適用範囲 |
| inputSet / allowedPaths / excludedPaths | 許可された資料、入力版・SHA-256、読取り/書込みの範囲と除外 |
| acceptanceAndReview | 受入条件の記述粒度、レビュー担当・判定条件、未確定時の扱い。試験実施とは分ける |
| runId / reportRoot | 識別属性と固定記録先。中間物は対応する.tmp/、履歴はGit |

## 今後の起動指示

利用者が要件定義の実行を依頼したら、ルートAGENTS.mdと共通docs、当契約を読み、上記実行条件を固定する。選択specRootの確定前提・採用プロファイル・QA決定を先に読み、変更指示や新たな矛盾がなければ継承する。

AIが要求と根拠を読み、目的・範囲・機能/非機能・制約・業務データ/外部IF・受入条件を要求IDで対応付ける。推測や提案は利用者確定と分けて記録し、未確定はQAへ残す。特定業務、認証方式、物理DB、画面部品や実装手順をこのひな型から補わない。

成果物の版・ファイル・SHA-256、確認範囲、未決・未実施を記録し、[基本設計Agent](../basic-design-agent/AGENT.md)へ要求ID・確定前提・QAを渡す。[詳細設計Agent](../detail-design-agent/AGENT.md)へは採用された基本設計と要求対応を引き継ぐ。要件定義の依頼だけで、設計・実装・実DB操作・受入試験・正式採点へ進めない。
