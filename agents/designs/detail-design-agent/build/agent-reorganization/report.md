<!-- spec-meta: {"schema":"spec-md/1.0","documentId":"DESIGN-AGENT-REORGANIZATION","version":"1.0","path":"agents/designs/detail-design-agent/build/agent-reorganization/report.md","sheets":[{"heading":"担当と配置","kind":"GRID","sheet":"01_担当と配置"},{"heading":"移動と保全","kind":"GRID","sheet":"02_移動と保全"},{"heading":"検査と未実施","kind":"GRID","sheet":"03_検査と未実施"}]} -->
# 設計Agentの3工程への整理

版1.0／2026-10-28。利用者指定により汎用仕様Agentを廃止し、工程別に定義を整理した。

## 担当と配置

- requirement-agent：要件定義のひな型0.1、template/draft。運用・業務生成の検証は今後整備する。
- basic-design-agent：基本設計専用1.8。専用規則1.0・工程1.1を同Agent配下に置く。
- detail-design-agent：詳細仕様書専用1.0。専用規則と工程1.0を同Agent配下に置く。

要件・基本・詳細の要求、許可範囲、採用版、文書/機能/項目/イベントID、確定前提・QAを引き継ぐ。別Agent起動・別チャット送信は必須にしない。未指定の後工程へ自動展開せず、ひな型の存在を要件確定や実行検証済みとは扱わない。

## 移動と保全

旧agents/designs/spec-agentフォルダをdetail-design-agentへ移動し、3定義を詳細設計専用として再構成した。旧フォルダと互換入口は存在しない。過去のbuild/spec-layout/のreport・manifest・validation計3ファイルはraw SHA-256一致で保全し、当時のAgent名、入力パス、版とハッシュを書き換えていない。

共通docsの詳細設計専用記述を専用規則への参照へ整理した。root索引・Agent索引・配置・基本設計の引継ぎ・テストデータの責務を更新した。実装Agentの固定入力は詳細設計契約・規則・工程の明示3ファイルへ変更し、要件定義ひな型を実装入力へ追加していない。既存のproject内採用規約、原入力、QA、過去の生成・検査記録は履歴と対象版の入力として保持する。

## 検査と未実施

19文書のメタ情報・版・見出し/sheets・13LIST・147相対リンク、旧フォルダ不存在、過去3記録のraw SHA、現行Agent間の責務・権限・前提継承を検査し、独立レビューを含めPASS。実装入力コード2ファイルの構文と既存隔離fixture65項目もPASS。入出力の版・SHAと今回の検査はmanifest.json、validation.json、review.jsonへ固定保存した。

この記録はAgent定義とルーティングの整理に限る。Access仕様の試験生成確認はsample-project1/srcs/Access/build/spec-generation/design-generation-check/の別記録で判定する。アプリ実装・ビルド、DB作成/実行、実Excel/印刷、業務受入れ、正式採点、Git commit/merge/pushは本記録の対象外で未実施。formalScore=null。
