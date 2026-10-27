<!-- spec-meta: {"schema":"spec-md/1.0","documentId":"SP2-README","version":"1.0","path":"sample-project2/README.md","sheets":[{"heading":"目的と今回の範囲","kind":"GRID","sheet":"01_目的と範囲"},{"heading":"入口","kind":"LIST","sheet":"02_入口","key":["領域"]},{"heading":"実施状態","kind":"GRID","sheet":"03_実施状態"}]} -->
# 社員経歴管理システム — sample-project2

版1.0／2026-10-27。Agent訓練・DEMO用の最小構成。基本設計初版（利用者レビュー前）。

## 目的と今回の範囲

社員の基本情報と職務・案件経歴を登録し、日本語の職務経歴書をExcelで作成する。ログイン、メニュー、社員検索、社員登録（経歴登録を含む）、検索画面からの経歴書出力、汎用コードマスタの6機能を設計する。画面は5種類で、帳票出力の専用画面は増やさない。

今回作成するのは基本設計とその共通設計・論理テーブル仕様である。Markdownが仕様正本。詳細設計、物理DB定義、アプリ、DB、Excel帳票実ファイル、仕様書のExcel変換、正式評価セットは未作成。test-project1の構造・章立てを参考にし、学生管理の業務や認証なしの前提は継承していない。

## 入口

| 領域 | 入口 |
| --- | --- |
| プロジェクト情報 | [工程・方式・配置](プロジェクト情報.md) |
| 方式別基本設計 | [仕様索引](spec/README.md) |
| Access版 | [独立仕様一式](spec/Access/README.md) |
| CSharp_ASPNET版 | [独立仕様一式](spec/CSharp_ASPNET/README.md) |
| 今回の検査 | [生成・検査記録](build/basic-design/report.md) |

## 実施状態

仕様の作成、文書構造の検査、独立レビュー、HTML配置確認をそれぞれ今回の検査記録へ記載する。仕様モックの確認は製品画面の動作試験ではない。アプリ実装・ビルド・DB実行・Excel生成/印刷・利用者受入・正式採点は未実施、formalScore=null。各方式の検査記録はsrcs/方式ID/build/spec-generation/へ固定保存する。
