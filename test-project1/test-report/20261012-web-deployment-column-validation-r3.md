# Web導入検証の列数修正・R3非接続検査

2026-10-12／projectId=test-project1／build。現在の001 DDLから物理列を独立に解析し、004の期待件数と全7表で比較。

結果：
PASS
 
20
/
20
。各方式は学生35列・全106列。原バグ33列への戻し、列欠落、表名不一致の負例を検出した。

修正はMVC/Vue 004の学生期待値33→35のみ。逆変換SHAが修正前SHAと一致し、その他byteの不変更を検査した。001と002は変更なし。既存R1/R2報告は保存する。

| 方式 | 004修正前SHA256 | 004修正後SHA256 |
| --- | --- | --- |
| CSharp_ASPNET | 80d9a7c01f809f749acaade923c507878cc74b03595e88a09adab6a4d21ec4a4 | b6d20d90bdad0e300d9f56260a4676c54efb7aeef01931d59646addfae017e75 |
| Vue_CSharpAPI | 95074bc573d27408cde841fd45a725d16b139f45acad7472b44e0ba98729cb3e | 2b9d1bcfae6eba2ed2579495dfaa6c3dd7eb552972a33c4848b6edc647b4fff0 |

実行装置は同名.ps1、詳細はJSONとraw.log。SQLCMD実行、SQL接続、SQL実行、昇格はすべて0件。

これは静的列数照合の合格であり、Express17の導入成功・共有DB接続・権限・業務動作の合格ではない。共有role/SQLCLRの構造衝突は20261012-shared-sql-schema-assessment.mdに記録し、解消前の導入停止を維持する。
