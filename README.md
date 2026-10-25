<!-- spec-meta: {"schema":"spec-md/1.0","documentId":"REPO-README","version":"7.1","path":"README.md","sheets":[{"heading":"概要","kind":"GRID","sheet":"01_概要"},{"heading":"入口一覧","kind":"LIST","sheet":"02_入口一覧","key":["領域"]},{"heading":"状態","kind":"GRID","sheet":"03_状態"}]} -->
# contextbase-evaluation

版7.1／2026-10-25。設計・評価基準。アプリ実装・実機試験・逆生成採点は未実施。

## 概要

仕様書作成→プログラム生成→逆仕様生成の検証基盤。方式別の原仕様はproject/spec/方式ID/、生成ソースはproject/srcs/方式ID/、最終配布物と検査記録はそのsourceRoot/build/へ分ける。今は仕様書策定段階。全体・Agent・題材を分離して複数のテストプロジェクトへ拡張する。

## 入口一覧

| 領域 | 入口 |
| --- | --- |
| 全体情報 | [リポジトリ構成](docs/リポジトリ構成.md) |
| Agent情報 | [README](agents/README.md) |
| 最初の題材 | [README](test-project1/README.md) |
| 題材1の原仕様 | [方式別仕様索引](test-project1/spec/README.md)。正本はtest-project1/spec/方式ID/ |
| 題材1の評価 | [00_採点規則](test-project1/spec-eval/00_採点規則.md) |
| 次の題材 | test-project2（予定・未作成） |

## 状態

設計・HTMLモック・採点基準の成果物。アプリ/Agentの実装、SQL Serverの実接続やデータ移行、逆仕様生成・採点は未実施。
