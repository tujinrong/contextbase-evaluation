<!-- spec-meta: {"schema":"spec-md/1.0","documentId":"CSHARP_ASPNET-SPEC-INDEX","version":"8.2","path":"test-project1/srcs/CSharp_ASPNET/spec/README.md","sheets":[{"heading":"対象","kind":"GRID","sheet":"01_対象"},{"heading":"入口","kind":"LIST","sheet":"02_入口","key":["区分"]},{"heading":"隔離","kind":"GRID","sheet":"03_隔離"}]} -->
# CSharp_ASPNET 仕様書

版8.2／2026-10-23。検索画面に続き学生編集画面を改善。

## 対象

本プロジェクトだけの実装・DB・画面仕様。

検索条件を12項目から4項目（学籍番号・氏名・クラス・在籍区分）へ整理し、一覧を7列に再配置した。ブラウザー本文1366×650 CSS pxで主要領域を1画面に配置し、一覧内でスクロールする。改善理由・試験観点は[設計判断](共通/06_要件対応・設計判断.md)、画面は[HTML](詳細仕様書/CSharp_ASPNET/assets/学生検索.html)／[PNG](詳細仕様書/CSharp_ASPNET/assets/学生検索.png)、今回の描画条件とハッシュは[画面確認記録](詳細仕様書/CSharp_ASPNET/assets/学生検索.render.json)を参照。アプリ実装・実DB試験・正式採点は今回の範囲外。

学生編集画面も上段の基本情報＋下段3列に再配置し、全34項目と保存・検査・権限の契約を維持した。通常編集と確認ダイアログを分け、同じ1366×650・1280×650で全入力グループと操作の配置を確認する。新規・参照も同じ配置を使用する。[編集画面HTML](詳細仕様書/CSharp_ASPNET/assets/学生登録.html)／[PNG](詳細仕様書/CSharp_ASPNET/assets/学生登録.png)／[画面確認記録](詳細仕様書/CSharp_ASPNET/assets/学生登録.render.json)。

## 入口

| 区分 | 文書 |
| --- | --- |
| 対象 | [プロジェクト仕様](プロジェクト情報.md) |
| 業務 | [仕様索引](共通/00_設計書一覧.md) |
| 検索 | [詳細](詳細仕様書/CSharp_ASPNET/01_学生検索画面.md) |
| 登録 | [詳細](詳細仕様書/CSharp_ASPNET/02_学生登録画面.md) |
| 方式 | [方式内実装仕様](共通/方式別/CSharp_ASPNET/01_共通実装仕様.md) |
| DB | [物理定義](DB定義/SQLServer/01_DB定義書.md) |
| 規約 | [実装規約](規約/CSharp_ASPNET.md) |

## 隔離

すべての仕様参照はこのフォルダー内で閉じる。業務項目・規則IDは維持し、文書IDは本方式専用とした。他プロジェクトと共通の仕様ファイル、symlink、外部への相互引用は使用しない。
