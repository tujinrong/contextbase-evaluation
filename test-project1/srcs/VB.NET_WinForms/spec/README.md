<!-- spec-meta: {"schema":"spec-md/1.0","documentId":"VB.NET_WINFORMS-SPEC-INDEX","version":"8.1","path":"test-project1/srcs/VB.NET_WinForms/spec/README.md","sheets":[{"heading":"対象","kind":"GRID","sheet":"01_対象"},{"heading":"入口","kind":"LIST","sheet":"02_入口","key":["区分"]},{"heading":"隔離","kind":"GRID","sheet":"03_隔離"},{"heading":"画面最適化の改訂","kind":"GRID","sheet":"04_画面最適化の改訂"}]} -->
# VB.NET_WinForms 仕様書

版8.1／2026-10-23。

## 対象

本プロジェクトだけの実装・DB・画面仕様。

## 入口

| 区分 | 文書 |
| --- | --- |
| 対象 | [プロジェクト仕様](プロジェクト情報.md) |
| 業務 | [仕様索引](共通/00_設計書一覧.md) |
| 検索 | [詳細](詳細仕様書/VB.NET_WinForms/01_学生検索画面.md) |
| 登録 | [詳細](詳細仕様書/VB.NET_WinForms/02_学生登録画面.md) |
| 方式 | [方式内実装仕様](共通/方式別/VB.NET_WinForms/01_共通実装仕様.md) |
| DB | [物理定義](DB定義/SQLServer/01_DB定義書.md) |
| 規約 | [実装規約](規約/VB.NET_WinForms.md) |

## 隔離

すべての仕様参照はこのフォルダー内で閉じる。業務項目・規則IDは維持し、文書IDは本方式専用とした。他プロジェクトと共通の仕様ファイル、symlink、外部への相互引用は使用しない。

## 画面最適化の改訂

2026-10-23、検索4条件・7列と学生編集の上段基本＋下段3列へ改訂。方式固有のネイティブUIと既存保存契約を維持する。各文書版・確認範囲は[画面最適化記録](画面最適化記録.md)を参照。実装・実DB・実機・正式採点は未実施、formalScore=null。
