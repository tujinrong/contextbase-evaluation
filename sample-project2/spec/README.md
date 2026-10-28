<!-- spec-meta: {"schema":"spec-md/1.0","documentId":"SP2-SPEC-INDEX","version":"1.7","path":"sample-project2/spec/README.md","sheets":[{"heading":"配置索引","kind":"LIST","sheet":"01_配置索引","key":["方式ID"]},{"heading":"工程","kind":"GRID","sheet":"02_工程"}]} -->
# sample-project2 方式別仕様索引

版1.7／2026-10-28。配置情報のみ。業務仕様の共用入力ではない。

## 配置索引

| 方式ID | specRoot | sourceRoot | 入口 | 要件定義 | 詳細仕様 |
| --- | --- | --- | --- | --- | --- |
| Access | sample-project2/spec/Access/ | sample-project2/srcs/Access/ | [Access](Access/README.md) | [要件定義書](Access/要件定義書.md) | [詳細・DB・規約一覧](Access/README.md#設計書一覧) |
| CSharp_ASPNET | sample-project2/spec/CSharp_ASPNET/ | sample-project2/srcs/CSharp_ASPNET/ | [CSharp_ASPNET](CSharp_ASPNET/README.md) | [要件定義書](CSharp_ASPNET/要件定義書.md) | [詳細・DB・規約一覧](CSharp_ASPNET/README.md#設計書一覧) |

## 工程

既存の基本設計・共通・QAから要件定義書を逆生成した。要件逆生成の後、今回の工程はdetail-design / canonical-updateとして機能別詳細・方式別共通・物理DBの設計文書・開発規約・詳細設計QAを作成する。要件本文・根拠・受入条件・未確定事項は各方式内で独立して保持し、新たな利用者承認と区別する。各方式のREADMEから、その方式内の共通設計・機能設計・テーブル・QA・調査を参照する。基本設計・要件定義・既存QAは入力として保持する。アプリ実装、実DB作成/接続/投入、実Excel生成は次工程の明示依頼後に実施する。
