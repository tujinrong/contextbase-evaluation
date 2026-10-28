<!-- spec-meta: {"schema":"spec-md/1.0","documentId":"REPO-README","version":"7.4","path":"README.md","sheets":[{"heading":"概要","kind":"GRID","sheet":"01_概要"},{"heading":"入口一覧","kind":"LIST","sheet":"02_入口一覧","key":["領域"]},{"heading":"状態","kind":"GRID","sheet":"03_状態"},{"heading":"サンプルの方式パターン","kind":"GRID","sheet":"04_方式パターン"}]} -->
# contextbase-evaluation

版7.4／2026-10-28。Agent入口をbuilds・converts・reverses・designsへ分類。設計・評価基準。アプリ実装・実機試験・逆生成採点は未実施。

## 概要

仕様書作成→プログラム生成→逆仕様生成の検証基盤。方式別の原仕様はproject/spec/方式ID/、生成ソースはproject/srcs/方式ID/、最終配布物と検査記録はそのsourceRoot/build/へ分ける。今は仕様書策定段階。全体・Agent・題材を分離して複数のテストプロジェクトへ拡張する。

## 入口一覧

| 領域 | 入口 |
| --- | --- |
| 全体情報 | [リポジトリ構成](docs/リポジトリ構成.md) |
| Agent情報 | [分類別索引](agents/README.md)：builds（仕様からの実装）、converts（移行・変換）、reverses（コード解析）、designs（仕様・基本設計） |
| フル方式パターン（拡張可） | [README](sample-project1/README.md) |
| 題材1の原仕様 | [方式別仕様索引](sample-project1/spec/README.md)。正本はsample-project1/spec/方式ID/ |
| 題材1の評価 | [00_採点規則](sample-project1/spec-eval/00_採点規則.md) |
| 2方式パターン | [sample-project2](sample-project2/README.md)（Access・CSharp_ASPNETの基本設計） |
| 次の題材 | test-project2（予定・未作成） |

## 状態

設計・HTMLモック・採点基準の成果物。アプリ/Agentの実装、SQL Serverの実接続やデータ移行、逆仕様生成・採点は未実施。

## サンプルの方式パターン

sample-project1（旧test-project1）は全登録方式を扱うフル方式パターン。現在は基本7方式とAccess移行拡張を保持し、方式追加を上限7で禁止しない。追加時は方式索引・プロファイル・入出力境界と検査を更新する。sample-project2はAccess・CSharp_ASPNETの2方式パターンで、現在の工程は基本設計のみ。方式数と実装/検査の完了を混同しない。
