<!-- spec-meta: {"schema":"spec-md/1.0","documentId":"CSHARP-ASPNET-EVAL-INDEX","version":"1.0","path":"test-project1/srcs/CSharp_ASPNET/spec-eval/README.md","sheets":[{"heading":"対象と入口","kind":"GRID","sheet":"01_対象と入口"},{"heading":"文書別評価表","kind":"LIST","sheet":"02_文書別評価表","key":["文書ID"]},{"heading":"状態","kind":"GRID","sheet":"03_状態"}]} -->
# ASP.NET spec-agent 評価表

## 対象と入口

指定された[原仕様フォルダ](../spec/README.md)の基本設計書・詳細仕様書から、文書ごとの減点評価表を作成した。原仕様8.0に対する評価基準1.0／2026-10-13。

- [評価方法・減点ルール](00_評価方法.md)
- [文書別・全体集計](01_評価集計.md)
- [原仕様の確認事項](02_原仕様確認事項.md)
- [文書・版・ハッシュの索引JSON](evaluation-manifest.json)
- [全評価行のJSON](evaluation-items.json)
- [生成検査記録](validation.json)

## 文書別評価表

| 文書ID | 評価表 | 確認行数 | 適用満点 | 95％必要点 | 状態 | 実減点・得点・達成率 | 重大矛盾 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| CSHARP_ASPNET-BAS-STU-01 | [学生検索画面 基本設計書](%E5%9F%BA%E6%9C%AC%E8%A8%AD%E8%A8%88%E6%9B%B8/01_%E5%AD%A6%E7%94%9F%E6%A4%9C%E7%B4%A2%E7%94%BB%E9%9D%A2_%E8%A9%95%E4%BE%A1%E8%A1%A8.md) | 854 | 1062 | 1009 | 未評価 | 未記入 | 未確認 |
| CSHARP_ASPNET-BAS-STU-02 | [学生登録画面 基本設計書](%E5%9F%BA%E6%9C%AC%E8%A8%AD%E8%A8%88%E6%9B%B8/02_%E5%AD%A6%E7%94%9F%E7%99%BB%E9%8C%B2%E7%94%BB%E9%9D%A2_%E8%A9%95%E4%BE%A1%E8%A1%A8.md) | 1113 | 1422 | 1351 | 未評価 | 未記入 | 未確認 |
| CSHARP_ASPNET-BAS-STU-03 | [テーブル仕様書（索引・共通規則）](%E5%9F%BA%E6%9C%AC%E8%A8%AD%E8%A8%88%E6%9B%B8/03_%E3%83%86%E3%83%BC%E3%83%96%E3%83%AB%E4%BB%95%E6%A7%98%E6%9B%B8_%E8%A9%95%E4%BE%A1%E8%A1%A8.md) | 67 | 85 | 81 | 未評価 | 未記入 | 未確認 |
| CSHARP_ASPNET-BAS-STU-04 | [コード設計書（業務コード）](%E5%9F%BA%E6%9C%AC%E8%A8%AD%E8%A8%88%E6%9B%B8/04_%E3%82%B3%E3%83%BC%E3%83%89%E8%A8%AD%E8%A8%88%E6%9B%B8_%E8%A9%95%E4%BE%A1%E8%A1%A8.md) | 751 | 932 | 886 | 未評価 | 未記入 | 未確認 |
| CSHARP_ASPNET-BAS-STU-03-M_STUDENT | [学生基本情報 テーブル仕様書](%E5%9F%BA%E6%9C%AC%E8%A8%AD%E8%A8%88%E6%9B%B8/%E3%83%86%E3%83%BC%E3%83%96%E3%83%AB/01_m_student_%E8%A9%95%E4%BE%A1%E8%A1%A8.md) | 328 | 366 | 348 | 未評価 | 未記入 | 未確認 |
| CSHARP_ASPNET-BAS-STU-03-M_CLASS | [クラスマスタ テーブル仕様書](%E5%9F%BA%E6%9C%AC%E8%A8%AD%E8%A8%88%E6%9B%B8/%E3%83%86%E3%83%BC%E3%83%96%E3%83%AB/02_m_class_%E8%A9%95%E4%BE%A1%E8%A1%A8.md) | 166 | 186 | 177 | 未評価 | 未記入 | 未確認 |
| CSHARP_ASPNET-BAS-STU-03-M_CODE_CATEGORY | [コード種別マスタ テーブル仕様書](%E5%9F%BA%E6%9C%AC%E8%A8%AD%E8%A8%88%E6%9B%B8/%E3%83%86%E3%83%BC%E3%83%96%E3%83%AB/03_m_code_category_%E8%A9%95%E4%BE%A1%E8%A1%A8.md) | 112 | 126 | 120 | 未評価 | 未記入 | 未確認 |
| CSHARP_ASPNET-BAS-STU-03-M_CODE | [コード管理マスタ テーブル仕様書](%E5%9F%BA%E6%9C%AC%E8%A8%AD%E8%A8%88%E6%9B%B8/%E3%83%86%E3%83%BC%E3%83%96%E3%83%AB/04_m_code_%E8%A9%95%E4%BE%A1%E8%A1%A8.md) | 139 | 156 | 149 | 未評価 | 未記入 | 未確認 |
| CSHARP_ASPNET-BAS-STU-03-T_OPERATION_LOG | [操作履歴 テーブル仕様書](%E5%9F%BA%E6%9C%AC%E8%A8%AD%E8%A8%88%E6%9B%B8/%E3%83%86%E3%83%BC%E3%83%96%E3%83%AB/05_t_operation_log_%E8%A9%95%E4%BE%A1%E8%A1%A8.md) | 121 | 136 | 130 | 未評価 | 未記入 | 未確認 |
| CSHARP_ASPNET-DET-CSharp_ASPNET-SCR-STU-001 | [学生検索画面 詳細仕様書（C#／ASP.NET）](%E8%A9%B3%E7%B4%B0%E4%BB%95%E6%A7%98%E6%9B%B8/CSharp_ASPNET/01_%E5%AD%A6%E7%94%9F%E6%A4%9C%E7%B4%A2%E7%94%BB%E9%9D%A2_%E8%A9%95%E4%BE%A1%E8%A1%A8.md) | 1536 | 1866 | 1773 | 未評価 | 未記入 | 未確認 |
| CSHARP_ASPNET-DET-CSharp_ASPNET-SCR-STU-002 | [学生登録画面 詳細仕様書（C#／ASP.NET）](%E8%A9%B3%E7%B4%B0%E4%BB%95%E6%A7%98%E6%9B%B8/CSharp_ASPNET/02_%E5%AD%A6%E7%94%9F%E7%99%BB%E9%8C%B2%E7%94%BB%E9%9D%A2_%E8%A9%95%E4%BE%A1%E8%A1%A8.md) | 1892 | 2345 | 2228 | 未評価 | 未記入 | 未確認 |

## 状態

評価表を作成した段階であり、原仕様・実装・逆生成文書の採点は行っていない。項目長は−1、ER・関連図は−3、記述粒度不足は−2。同一欠陥の重複減点、非適用、原仕様矛盾の保留、重大矛盾の合否条件を評価方法に定義した。元のspecと旧spec-evalは変更していない。
