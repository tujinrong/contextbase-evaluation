<!-- spec-meta: {"schema":"spec-md/1.0","documentId":"AGENT-INDEX","version":"7.2","path":"agents/README.md","sheets":[{"heading":"概要","kind":"GRID","sheet":"01_概要"},{"heading":"Agent一覧","kind":"LIST","sheet":"02_Agent一覧","key":["Agent-ID"]},{"heading":"実行コンテキスト","kind":"GRID","sheet":"03_実行コンテキスト"}]} -->
# Agent定義一覧

版7.2／2026-10-23。AG-REVERSE を ContextBase 構築・調査・独立検証の統一入口として同期。アプリ実装・実機試験・採点の状態は各実行の報告で区別する。

## 概要

3種類のAgentの役割を定義する。Codexが契約と実行指示を読んで作業する。定義文書の存在だけで各工程を実行済みとしない。題材はprojectIdで選択し、全体規則と題材の正解を分離する。実行時に許可ファイルを列挙し、GitHub全体を無制限に参照させない。

## Agent一覧

| Agent-ID | 役割 | 契約文書 |
| --- | --- | --- |
| AG-SPEC | 指定project・方式の仕様書作成・既存改善。検索条件と画面配置の改善を含む | [契約](spec-agent/AGENT.md)・[実行指示](spec-agent/PROMPT.md)・[運用案内](spec-agent/README.md) |
| AG-BUILD | 仕様からシステム生成 | [build-agent](build-agent/AGENT.md) |
| AG-REVERSE | ソースから ContextBase を構築し、目標に応じた追加調査と独立検証を行う | [契約](reverse-agent/AGENT.md)・[実行指示](reverse-agent/PROMPT.md)・[運用案内](reverse-agent/README.md) |

AG-REVERSE の内部役割は discovery-agent（取得・初期理解）、investigation-agent（関係調査・動作深化）、review-agent（各段階の独立原文確認）とする。共通制御が候補の採用と範囲受入れを管理する。仕様書の構成・執筆・変換・公開は下流の責務とし、担当と旧コードの移管は未決定である。新しい3役割の自動実行機構は未実装であり、現存する旧仕様書生成 CLI と区別する。

## 実行コンテキスト

projectId、仕様セット版、方式ID、入力コミット/ハッシュ、許可パス、除外パス、出力先、Agent定義版、実行IDを固定する。spec-evalは採点者の参照先で、逆生成Agentの入力から物理的に除外する。共有docsに業務正解を隠して隔離を迂回しない。
