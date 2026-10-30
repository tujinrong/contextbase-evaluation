<!-- spec-meta: {"schema":"spec-md/1.0","documentId":"SP2-SPEC-INDEX","version":"1.8","path":"sample-project2/spec/README.md","sheets":[{"heading":"配置索引","kind":"LIST","sheet":"01_配置索引","key":["方式ID"]},{"heading":"工程","kind":"GRID","sheet":"02_工程"}]} -->
# sample-project2 方式別仕様索引

版1.8／2026-10-29。配置情報のみ。業務仕様の共用入力ではない。

## 配置索引

| 方式ID | specRoot | sourceRoot | 入口 | 要件定義 | 詳細仕様 |
| --- | --- | --- | --- | --- | --- |
| Access | sample-project2/spec/Access/ | sample-project2/srcs/Access/ | [Access](Access/README.md) | [要件定義書](Access/要件定義書.md) | [詳細・DB・規約一覧](Access/README.md#設計書一覧) |
| CSharp_ASPNET | sample-project2/spec/CSharp_ASPNET/ | sample-project2/srcs/CSharp_ASPNET/ | [CSharp_ASPNET](CSharp_ASPNET/README.md) | [要件定義書](CSharp_ASPNET/要件定義書.md) | [詳細・DB・規約一覧](CSharp_ASPNET/README.md#設計書一覧) |

## 工程

既存の基本設計・共通・QAから逆生成した要件を継承する。2026-10-29の依頼によりbasic-design→detail-design→buildの順に両方式を再生成する。各工程は前工程の対象版・確定前提・QA・各IDを引き継ぎ、両方式の前工程完了とレビューを確認して進める。今回の実施状態は[工程記録](../build/generation/pipeline.json)へ固定する。要件本文・根拠・受入条件・未確定事項は各方式内で独立して保持し、新たな利用者承認と区別する。各方式のREADMEから、その方式内の共通設計・機能設計・テーブル・QA・調査を参照する。実装・実DB・実Excel・実UIの検査結果は設計の静的検査と分け、今回の成果物SHAと環境に対応させる。
