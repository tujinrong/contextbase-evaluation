<!-- spec-meta: {"schema":"spec-md/1.0","documentId":"PROJECT-README","version":"7.0","path":"test-project1/README.md","sheets":[{"heading":"概要","kind":"GRID","sheet":"01_概要"},{"heading":"入口一覧","kind":"LIST","sheet":"02_入口一覧","key":["区分"]},{"heading":"境界","kind":"GRID","sheet":"03_境界"}]} -->
# test-project1 学生管理

版7.0／2026-10-11。設計・評価基準。アプリ実装・実機試験・逆生成採点は未実施。

## 概要

学生基本情報管理を題材にした仕様作成・往復生成の評価プロジェクト。検索/登録、氏名/住所、クラス/コードを対象とし、成績は対象外。

## 入口一覧

| 区分 | 入口 |
| --- | --- |
| プロジェクト情報 | [対象・プロファイル](プロジェクト情報.md) |
| 仕様書 | [文書一覧](spec/共通/00_設計書一覧.md) |
| 評価 | [基本・詳細・共通・DBの評価](spec-eval/00_採点規則.md) |
| 項目長 | [基準値＋50%](spec/共通/11_項目長設計基準.md) |
| SQL Server | [DB定義](spec/DB定義/SQLServer/01_DB定義書.md) |
| レビュー | [更新検証記録](docs/仕様書レビュー結果.md) |

## 境界

Agent共通情報は[agents](../agents/README.md)、全体ルールは[docs](../docs/リポジトリ構成.md)。この題材の期待値を逆生成Agentの共通規約へ混入しない。
