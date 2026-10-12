# 共有DB Create の局所修正レビュー R3

レビューID: `20261012-shared-sql-root-review-r3`。2026-10-12。project: `test-project1`。

**Create の最終PS5構文検査と非接続Planは通過、追加修正候補はない。** R1/R2およびrootの実機記録を上書きせず、今回変更された1ファイルだけを再検査した。

## 入力と差分

対象: `agents/build-agent/scripts/Create-SharedSqlDatabase.ps1`。

| 項目 | 値 |
| --- | --- |
| 今回のSHA-256 | `439E7B31FED8264CA8563924AC2578E78A3717D0D9C7018CA4BD86B7B86D554D` |
| R2のSHA-256 | `D79248ED74C3B027D0B23820D436BD64806FEF139367EFC6EF58C03F44042AFF` |
| 検査前後の入力hash | 一致 |

39行目の `$cn.ChangeDatabase($database)` が、40行目の `sys.databases` メタデータSELECTより前に移動した。固定DBの存在確認とsysadminの完全メタデータ可視性確認は先に実施し、54行目でmasterへ戻してからユーザーDB一覧を調べる。DBオプションを変更するSQLの追加はない。

AUTO_CLOSEがONで閉じたDBでは、`sys.databases.collation_name` などがNULLになることが公式資料に記載されている。DBを接続先として開いてからメタデータを読む今回の順序は、閉じたDBのNULLを設定不一致と誤判定したrootのVerify01事例に対応する。[Microsoft: sys.databases](https://learn.microsoft.com/en-us/sql/relational-databases/system-catalog-views/sys-databases-transact-sql?view=sql-server-ver17)。

VerifyOnlyの変更は接続の現在DB切替であり、AUTO_CLOSE設定、schema、業務データ、roles、CLRを変更しない。ただし閉じたDBの再オープンに伴うエンジンの処理やI/Oは起こり得るため、「接続先切替にも一切の副作用がない」とは扱わない。本レビュー担当はVerifyOnlyを実行していない。

## 今回の非接続検査

| 検査 | 結果 |
| --- | --- |
| Windows PowerShell 5.1.26100.9549 ParseFile | 終了0、ParseError0、1ファイル |
| Create既定Plan | 終了0、PLAN_ONLY |
| Planの固定値 | DB=contextbase_test_project1、ODBC18、期待証明書名localhost、Encrypt=true、TrustServerCertificate=false |
| Plan実行用ディレクトリ生成 | なし |
| ASTのSQL定数比較 | 10文すべてR2と順序付きOrdinal比較で一致 |
| TSql170Parser再実行 | 未実施。SQL文字列が同一なのでR2検査を参照 |

```powershell
& "$env:SystemRoot\System32\WindowsPowerShell\v1.0\powershell.exe" -NoLogo -NoProfile -NonInteractive -File agents/build-agent/scripts/Create-SharedSqlDatabase.ps1 -RunId 20261012-review-r3-plan-create
```

Planは13行目でreturnし、18行目のODBC接続オブジェクト生成と21行目のOpenに到達しない。Execute/VerifyOnly、SQL接続/送信、サーバ設定、証明書生成、サービス再起動、権限昇格は今回すべて **NOT_RUN**。他4スクリプトも今回再実行していない。

## rootの既存実機証拠の読取

`test-report/20261012-shared-sql-verify-02/shared-database.json` をファイルとして読んだ。SHA-256は `15268163852F050038245856A2A20DED7D762FBBF43FD1E924CF55F1A1E6DE2F`。その記録は `INFRASTRUCTURE_PASSED_MIGRATION_BLOCKED`、databaseCreated=false、ONLINE、compatibility160、Japanese_XJIS_140_CI_AS、owner=sa、ユーザーtable/objects/assembly/独自roleが各0である。アプリ認可はfalseのまま。本レビューの新たなSQL実行結果とは区別する。

rootは別実行としてx64/x86のTLS正例・hostname不一致負例・空DB確認の6PASS、および既存DB作成拒否負例/Verify02の2PASSを報告した。この合計は親Agentの報告値であり、本R3では8件を再実行していない。共有schema/API、CLR、非sysadminアプリ主体、CRUD、Access/RPG接続移行は今回の検査範囲に含まれない。証明書Repair成功の記録としても扱わない。

## 新規証拠

- `20261012-shared-sql-root-review-r3-results.json`
- `20261012-shared-sql-root-review-r3-ps5-parser.raw.json`
- `20261012-shared-sql-root-review-r3-plan-create.raw.json`

旧報告の合格を今回のCreate入力にそのまま流用せず、変更されたPS5入力は新しくParse/Planした。変更されていないSQL文字列についてだけR2と対応付けた。
