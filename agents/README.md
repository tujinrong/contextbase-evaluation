<!-- spec-meta: {"schema":"spec-md/1.0","documentId":"AGENT-INDEX","version":"7.7","path":"agents/README.md","sheets":[{"heading":"概要","kind":"GRID","sheet":"01_概要"},{"heading":"Agent一覧","kind":"LIST","sheet":"02_Agent一覧","key":["Agent-ID"]},{"heading":"実行コンテキスト","kind":"GRID","sheet":"03_実行コンテキスト"}]} -->
# Agent定義一覧

版7.7／2026-10-26。AG-REVERSE を ContextBase 構築・調査・独立検証の統一入口として同期。アプリ実装・実機試験・採点の状態は各実行の報告で区別する。

## 概要

3種類のAgentの役割を定義する。Codexが契約と実行指示を読んで作業する。定義文書の存在だけで各工程を実行済みとしない。題材はprojectIdで選択し、全体規則と題材の正解を分離する。実行時に許可ファイルを列挙し、GitHub全体を無制限に参照させない。

AG-REVERSEの設計上の3子Agentは [discovery](reverse-agent/roles/discovery/AGENT.md)（取得・目録化）、[relationship](reverse-agent/roles/relationship/AGENT.md)（関係構築）、[behavior](reverse-agent/roles/behavior/AGENT.md)（動作深化）。独立検証は共通能力として抽出と別task・文脈で実行し、ホストが採用・範囲受入れを管理する。第4の段階子Agentにはしない。仕様書の構成・執筆・変換・公開は下流の責務である。

現コードはv2のstage（discovery／relationship／behavior）と、独立検証operationを分ける。step／verify／run／revise、封印入力、ホスト採用を実装した。runは定義済み目標グラフ内で局所の検証済み前提から進め、阻害時は保存停止する。旧v1と --role は自動移行しない。任意の自動補査修復、cross-session P6再利用、長期運用、実モデル業務品質・人手受入れは未完了。操作は [実装ガイド](reverse-agent/docs/ContextBase初期実装.md)を参照する。

## Agent一覧

| Agent-ID | 役割 | 契約文書 |
| --- | --- | --- |
| AG-SPEC | 指定project・方式の仕様書作成・既存改善。検索条件と画面配置の改善を含む | [契約](spec-agent/AGENT.md)・[実行指示](spec-agent/PROMPT.md)・[運用案内](spec-agent/README.md) |
| AG-BUILD | 仕様からシステム生成 | [build-agent](build-agent/AGENT.md) |
| AG-REVERSE | ソースから ContextBase を構築し、目標に応じた追加調査と独立検証を行う | [契約](reverse-agent/AGENT.md)・[実行指示](reverse-agent/PROMPT.md)・[運用案内](reverse-agent/README.md) |

## 実行コンテキスト

projectId、仕様セット版、方式ID、specRoot=project/spec/方式ID、sourceRoot=project/srcs/方式ID、入力コミット/ハッシュ、許可パス、除外パス、出力先、Agent定義版、実行IDを固定する。AG-SPECはspecRootを更新し、AG-BUILDは同じspecRootからsourceRootへ生成する。AG-SPEC／AG-BUILDの業務入力は選択方式のspecRoot内で閉じ、旧sourceRoot/specや他方式を代替入力にしない。AG-REVERSEは原仕様を読まず、選択source-only入力を使う。全Agentは最終正本を更新し、最終成果・検査結果はsourceRoot/build/の固定先へ更新する。中間結果はsourceRoot/.tmp/、方式を持たない共通作業は担当Agentまたはprojectの.tmp/を使う。過去生成結果の別名保存はせずGit履歴を使う。spec-evalは採点者の参照先で、逆生成Agentの実行権限・入力選択では移動後のproject/spec/全体とともに禁止し、選択ソース根の外へ物理的に隔離する。逆生成CLIのallowedPaths／excludedPathsはそのソース根内の相対パスに限定し、兄弟の仕様へ範囲を広げない。共有docsに業務正解を隠して隔離を迂回しない。
