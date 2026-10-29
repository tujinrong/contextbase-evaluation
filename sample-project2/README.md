<!-- spec-meta: {"schema":"spec-md/1.0","documentId":"SP2-README","version":"1.9","path":"sample-project2/README.md","sheets":[{"heading":"目的と今回の範囲","kind":"GRID","sheet":"01_目的と範囲"},{"heading":"入口","kind":"LIST","sheet":"02_入口","key":["領域"]},{"heading":"実施状態","kind":"GRID","sheet":"03_実施状態"}]} -->
# 社員経歴管理システム — sample-project2

版1.9／2026-10-29。Agent訓練・DEMO用の最小構成。要件・基本・詳細仕様を入力として方式別ソースを生成・検証する。製品受入・正式採点は未実施。

## 目的と今回の範囲

本projectはAccess・CSharp_ASPNETの2方式パターン。sample-project1（旧test-project1）のフル方式パターンと区別し、他方式を自動追加しない。


社員の基本情報と職務・案件経歴を登録し、日本語の職務経歴書をExcelで作成する。ログイン、メニュー、社員検索、社員登録（経歴登録を含む）、検索画面からの経歴書出力、汎用コードマスタの6機能を対象とする。画面は5種類で、帳票出力の専用画面は増やさない。要件逆生成・基本設計・詳細設計は完了し、今回の工程はbuildである。品質要求は高、改善回数は3。各Pilotの実施範囲は方式別の検査対応表で区別する。

Markdownが仕様正本。今回の実装は各srcs/方式ID/へ保持し、設計原本と過去工程の検査記録を保全する。実DB試験は新規の所有fixtureだけ、Access成果は検証用candidateで、稼働配備・利用者秘密による配布初期設定とは区別する。学生管理の業務や認証なしの前提は継承しない。

## 入口

| 領域 | 入口 |
| --- | --- |
| プロジェクト情報 | [工程・方式・配置](プロジェクト情報.md) |
| 方式別要件・基本・詳細設計 | [仕様索引](spec/README.md) |
| Access版 | [独立仕様一式](spec/Access/README.md) |
| CSharp_ASPNET版 | [独立仕様一式](spec/CSharp_ASPNET/README.md) |
| Accessソース・実行手順 | [実装入口](srcs/Access/README.md) |
| CSharp_ASPNETソース・実行手順 | [実装入口](srcs/CSharp_ASPNET/README.md) |
| 詳細設計の今回記録 | [生成・検査記録](build/detail-design/report.md) |
| 要件定義の記録 | [逆生成・検査記録](build/requirement-definition/report.md) |
| 基本設計の記録 | [生成・検査記録](build/basic-design/report.md) |

## 実施状態

今回の自己検証・独立検査・3回の改善、実DB/ブラウザー/Excelの実測と未実施は各sourceRoot/build/test-results/、凍結入力・出力版/SHAはbuild/generation/へ固定する。過去の設計PASSや静的モックを実装合格へ転記しない。SQL Server 2022実機は未導入、現SQL2025/互換160のfixtureで検査する。Access実キー/貼付/目視はデスクトップ操作制約と区別する。Webの未適用検索raw条件→新規→取消には詳細HTTP契約の補完課題があり、リポジトリ直下sample-project2-build-report.mdへ報告する。正式受入・正式採点は未実施、formalScore=null。
