# Access 検索表示・連動修正 R5

実行ID `20261012-evidence-01-access-r5`。修正後の入力を固定し、新規DBで以下を実行した。R4以前のPASSは今回の結果として流用していない。詳細、入力SHA-256、変更前後SHA-256、実行ログの対応は [inputs.json](inputs.json) / [results.json](results.json)。独立仕様45ファイルは不変、業務版8.0・単体配置版8.1・DB索引版8.2。共有SQL設計は変更していない。

検索の年度・学年・クラス・都道府県が空欄表示になっていたが、当方式の詳細検索 L87–89/L92、SRC-004/005/006/009は初期「すべて」、未設定NULL相当を要求している。検索画面だけに「すべて」候補を追加した。画面の選択値0／`*`はReadCriteriaと候補連動でNULLへ戻す。学年00・登録画面のraw入力・DB正規化入口は変更していない。

modStudentForms / modCandidatesを修正した。検索クラス候補は年度降順→学年表示順→クラス表示順→コード→IDで、学年名称を含める。不適合クラスを解除した時はW-STU-107を一般変更文言で上書きしない。候補再取得時に適合する選択クラスを保持し、Clear・未所属時には「すべて」を表示する。

| 最終ソースでの新規実行 | 結果・証拠 |
|---|---|
| SingleFile / VBA compile | 成功、build-tests.raw.log |
| 業務31＋拡張77＋実フォーム29 | 137 PASS、application.raw.log |
| 続柄NULL・複合FK | 21 PASS、relationship.raw.log |
| clean配布成果の同一バイトコピー | 19 PASS、deployment.raw.log |
| FileFormat12・ACEヘッダー・初期Boolean | 10 PASS、format-initial-state.raw.log |
| 実フォーム検索表示・NULL・学年00・連動・通知 | 21 PASS、search-all.raw.log |
| 2つのAccessプロセスの最終1席 | 保存1件／E-STU-102拒否1件、占有1件・CREATE監査1件 PASS、race.raw.log |
| Windows PowerShell 5.1 Parser | 対象6スクリプト、0エラー、ps5-parser.raw.json |

検索21項目は実productionフォームで、初期4条件の表示とNULL変換、実DAO検索、学年00、クラス選択による年度・学年同期、学年名称、有効選択の保持、不適合解除とW-STU-107、未所属の表示と非活性、Clear復帰と再検索を検証した。候補並び順はSQLの明示ORDER BYを静的に確認した。複数年度・学年の全組合せでの手動並び順確認までは実施していない。

配布 `Access/StudentManagement.accdb` の最終SHA-256は `0547CB5FF9D70C5F17F97D42E8D14E5EAEAB6D3CDEDD2B3F0DA9744960B22E2A`。実Access FileFormat=12、ヘッダーStandard ACE DB、StartupFormあり、SELF、外部リンク0、試験モジュール0、学生・クラス・監査0、5分類70コード。VBA compile / コピーでの起動検証後に置換した。原本自体はCOMで開いていない。[replacement.json](replacement.json)

旧MDB成果のbyte exact SHA `838F5FE...DE5` とR4成果SHA `090DB949...C896` は `Access/build/20261012-evidence-01-backup/` にそれぞれ保持した。撮影用の架空学生3件は別のR5 fixtureだけに保存し、最終配布原本へ混入していない。[撮影fixtureの手順・証拠](../Access-ui-r5/README.md)

共有SQL移行・配備・Windows認可・CRUD結合、Office 32-bit、10,000／10,001件性能、確定応答喪失は未実施。実画面の手動操作・撮影はrootの別記録。このAgentはbuild10 ZIPを再生成していないため、既存ZIPの改訂と最終ソースの改訂を区別する。
