# EVALUATOR_ONLY — 既存ASP.NET物理テーブル7冊の新規意味採点

2026-10-13 JST。評価者 `/root/evaluation_inventory`。生成モード `training-assisted`、出力版1.0の `20261013-pilot-v3-tables` を新規に凍結して採点した。過去のbridge/版差分審査を今回の合格結果へ流用していない。

**113行・127点の対象で90点を確認。14行は欠落（28点）、1行は原基準/ソース対応の裁定保留、8行は物理保存契約が観測不能（計9点未採点）。完成得点・正式率は保留。**

| 原文書ID | 審査行 | 原満点 | 確認加点 | 欠落行 | 未採点行 |
| --- | --- | --- | --- | --- | --- |
| DBDEF-SQLSERVER-M_STUDENT | 36 | 38 | 30 | 6 | 0 |
| DBDEF-SQLSERVER-M_CLASS | 18 | 20 | 17 | 1 | 0 |
| DBDEF-SQLSERVER-M_CODE_CATEGORY | 12 | 14 | 10 | 2 | 0 |
| DBDEF-SQLSERVER-M_CODE | 15 | 17 | 13 | 2 | 0 |
| DBDEF-SQLSERVER-T_OPERATION_LOG | 13 | 15 | 11 | 1 | 1 |
| DBDEF-SQLSERVER-T_CONFIRMATION | 10 | 12 | 9 | 1 | 0 |
| DBDEF-SQLSERVER-T_RUNTIME_STATE | 9 | 11 | 0 | 1 | 8 |

[行別採点JSON](table-evaluation.json)に評価ID、判定、原配点、確認加点、生成MD/ソースの行範囲、SHA、原仕様版を保存した。[凍結manifest](frozen-manifest.json)は9冊の選択和集合の83ファイルを固定する。この表の意味採点は物理7冊だけであり、詳細2冊は独立した別評価者が審査する。

一致は属性一式を意味で照合する。物理名/文書ID/数値表記の字面一致を要求せず、整数型域と小数0の桁数表記は意味対応として扱った。Unicodeスカラー上限とUTF-16容量は別条件として照合した。本文にない業務説明へソースだけから点を足していない。

重要制約を含む属性行の型/値/NULL/主体/確定に対する生成矛盾は今回確定0。ただし未採点は合格を意味しない。物理状態テーブルへ接続する保存・消費・暗号化契約の不足を、メモリ実装の動作で埋めていない。

本結果は意味評価だけであり、TABLEメタ情報と９列様式/共通参照は別の欠落として残る。HTML/Excel/PDFでの変換・描画合格、実機SQL/HTTP/UI試験、他方式、原1408点全体の完了/95%資格判定は行っていない。原source/spec/spec-evalは変更していない。
