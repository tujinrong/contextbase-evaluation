<!-- spec-meta: {"schema":"spec-md/1.0","documentId":"SP2-README","version":"1.7","path":"sample-project2/README.md","sheets":[{"heading":"目的と今回の範囲","kind":"GRID","sheet":"01_目的と範囲"},{"heading":"入口","kind":"LIST","sheet":"02_入口","key":["領域"]},{"heading":"実施状態","kind":"GRID","sheet":"03_実施状態"}]} -->
# 社員経歴管理システム — sample-project2

版1.7／2026-10-28。Agent訓練・DEMO用の最小構成。既存の基本設計から方式別の要件定義書を追加する（新たな利用者承認・受入試験は未実施）。

## 目的と今回の範囲

本projectはAccess・CSharp_ASPNETの2方式パターン。sample-project1（旧test-project1）のフル方式パターンと区別し、他方式を自動追加しない。


社員の基本情報と職務・案件経歴を登録し、日本語の職務経歴書をExcelで作成する。ログイン、メニュー、社員検索、社員登録（経歴登録を含む）、検索画面からの経歴書出力、汎用コードマスタの6機能を設計する。画面は5種類で、帳票出力の専用画面は増やさない。既存基本設計は、処理の順序・条件を保った手順の階層化までを含む。今回の工程は既存仕様からの要件定義書の逆生成。Pilotシナリオの実行は未実施。

既存の成果は基本設計・共通設計・論理テーブル仕様であり、今回は各方式の要件定義書を追加する。Markdownが仕様正本。詳細設計、物理DB定義、アプリ、DB、Excel帳票実ファイル、仕様書のExcel変換、正式評価セットは未作成。test-project1の構造・章立てを参考にし、学生管理の業務や認証なしの前提は継承していない。

## 入口

| 領域 | 入口 |
| --- | --- |
| プロジェクト情報 | [工程・方式・配置](プロジェクト情報.md) |
| 方式別要件・基本設計 | [仕様索引](spec/README.md) |
| Access版 | [独立仕様一式](spec/Access/README.md) |
| CSharp_ASPNET版 | [独立仕様一式](spec/CSharp_ASPNET/README.md) |
| 要件定義の今回記録 | [逆生成・検査記録](build/requirement-definition/report.md) |
| 基本設計の記録 | [生成・検査記録](build/basic-design/report.md) |

## 実施状態

今回の要件逆生成では文書構造・根拠資料の版/ハッシュ・要求/受入対応と本文を確認する。基本設計のHTML配置確認は既存の基本設計記録を参照し、今回の要件文書の検査結果へ流用しない。仕様モックの確認は製品画面の動作試験ではない。アプリ実装・ビルド・DB実行・Excel生成/印刷・利用者受入・正式採点は未実施、formalScore=null。今回の方式別要件記録はsrcs/方式ID/build/spec-generation/requirement-definition/へ固定保存し、既存基本設計の検査記録は保全する。
