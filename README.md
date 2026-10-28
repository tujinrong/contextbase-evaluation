<!-- spec-meta: {"schema":"spec-md/1.0","documentId":"REPO-README","version":"7.7","path":"README.md","sheets":[{"heading":"概要","kind":"GRID","sheet":"01_概要"},{"heading":"入口一覧","kind":"LIST","sheet":"02_入口一覧","key":["領域"]},{"heading":"状態","kind":"GRID","sheet":"03_状態"},{"heading":"サンプルの方式パターン","kind":"GRID","sheet":"04_方式パターン"}]} -->
# contextbase-evaluation

版7.7／2026-10-28。設計工程を要件定義・基本設計・詳細設計へ整理する。各工程の実施状態は対象版の検査記録で区別する。

## 概要

仕様書作成→プログラム生成→逆仕様生成の検証基盤。方式別の原仕様はproject/spec/方式ID/、生成ソースはproject/srcs/方式ID/、最終配布物と検査記録はそのsourceRoot/build/へ分ける。今は仕様書策定段階。全体・Agent・題材を分離して複数のテストプロジェクトへ拡張する。

## 入口一覧

| 領域 | 入口 |
| --- | --- |
| 全体情報 | [リポジトリ構成](docs/リポジトリ構成.md) |
| Agent情報 | [分類別索引](agents/README.md)：builds（仕様からの実装）、converts（移行・変換）、reverses（コード解析）、designs（要件定義・基本設計・詳細設計） |
| フル方式パターン（拡張可） | [README](sample-project1/README.md) |
| 題材1の原仕様 | [方式別仕様索引](sample-project1/spec/README.md)。正本はsample-project1/spec/方式ID/ |
| 題材1の評価 | [00_採点規則](sample-project1/spec-eval/00_採点規則.md) |
| 2方式パターン | [sample-project2](sample-project2/README.md)（Access・CSharp_ASPNETの要件・基本設計） |
| 次の題材 | test-project2（予定・未作成） |

## 状態

設計工程の入口は[要件定義](agents/designs/requirement-agent/README.md)・[基本設計](agents/designs/basic-design-agent/README.md)・[詳細設計](agents/designs/detail-design-agent/README.md)へ分かれる。要件定義Agentは既存仕様からの逆生成にも対応する。sample-project1の各方式に要件定義書を置き、今回の文書検査と利用者承認・受入試験を区別する。

設計・HTMLモック・採点基準の成果物。アプリ/Agentの実装、SQL Serverの実接続やデータ移行、逆仕様生成・採点は未実施。

## サンプルの方式パターン

sample-project1（旧test-project1）は全登録方式を扱うフル方式パターン。現在は基本7方式とAccess移行拡張を保持し、方式追加を上限7で禁止しない。追加時は方式索引・プロファイル・入出力境界と検査を更新する。sample-project2はAccess・CSharp_ASPNETの2方式パターンで、既存基本設計から要件定義書を逆生成した。詳細設計・実装は未実施。方式数と実装/検査の完了を混同しない。
