<!-- spec-meta: {"schema":"spec-md/1.0","documentId":"SP2-SPEC-INDEX","version":"1.6","path":"sample-project2/spec/README.md","sheets":[{"heading":"配置索引","kind":"LIST","sheet":"01_配置索引","key":["方式ID"]},{"heading":"工程","kind":"GRID","sheet":"02_工程"}]} -->
# sample-project2 方式別仕様索引

版1.6／2026-10-28。配置情報のみ。業務仕様の共用入力ではない。

## 配置索引

| 方式ID | specRoot | sourceRoot | 入口 | 要件定義 |
| --- | --- | --- | --- | --- |
| Access | sample-project2/spec/Access/ | sample-project2/srcs/Access/ | [Access](Access/README.md) | [要件定義書](Access/要件定義書.md) |
| CSharp_ASPNET | sample-project2/spec/CSharp_ASPNET/ | sample-project2/srcs/CSharp_ASPNET/ | [CSharp_ASPNET](CSharp_ASPNET/README.md) | [要件定義書](CSharp_ASPNET/要件定義書.md) |

## 工程

既存の基本設計・共通・QAから要件定義書を逆生成した。今回の工程はrequirement-definition / spec-to-requirements。要件本文・根拠・受入条件・未確定事項は各方式内で独立して保持し、新たな利用者承認と区別する。各方式のREADMEから、その方式内の共通設計・機能設計・テーブル・QA・調査を参照する。詳細仕様・物理DB定義・実装は次工程の明示依頼後に作成する。
