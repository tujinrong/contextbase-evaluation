<!-- spec-meta: {"schema":"spec-md/1.0","documentId":"AGENT-INDEX","version":"7.0","path":"agents/README.md","sheets":[{"heading":"概要","kind":"GRID","sheet":"01_概要"},{"heading":"Agent一覧","kind":"LIST","sheet":"02_Agent一覧","key":["Agent-ID"]},{"heading":"実行コンテキスト","kind":"GRID","sheet":"03_実行コンテキスト"}]} -->
# Agent定義一覧

版7.0／2026-10-11。設計・評価基準。アプリ実装・実機試験・逆生成採点は未実施。

## 概要

3種類のAgentの役割を定義する。実装・自動実行済みではない。題材はprojectIdで選択し、全体規則と題材の正解を分離する。実行時に許可ファイルを列挙し、GitHub全体を無制限に参照させない。

## Agent一覧

| Agent-ID | 役割 | 契約文書 |
| --- | --- | --- |
| AG-SPEC | 仕様書作成 | [spec-agent](spec-agent/AGENT.md) |
| AG-BUILD | 仕様からシステム生成 | [build-agent](build-agent/AGENT.md) |
| AG-REVERSE | プログラムから仕様生成 | [reverse-agent](reverse-agent/AGENT.md) |

## 実行コンテキスト

projectId、仕様セット版、方式ID、入力コミット/ハッシュ、許可パス、除外パス、出力先、Agent定義版、実行IDを固定する。spec-evalは採点者の参照先で、逆生成Agentの入力から物理的に除外する。共有docsに業務正解を隠して隔離を迂回しない。
