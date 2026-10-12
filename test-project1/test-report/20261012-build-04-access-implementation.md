# Access 生成・実機試験結果

2026-10-12。projectId=test-project1、工程build。spec-evalは読んでいない。過去reportを上書きせず本報告と生ログ・JSONを新規保存した。

成果物 srcs/Access/StudentManagement.accdb は１ファイルで、４フォーム、VBA、業務５表、ゲート、内包評価役割表、５分類70コードを含む。外部リンク０、学生０、クラス０、監査０、ゲート１、主体１。配布用にはmodSelfTestsを含めない。Windows実主体と内包役割照合により実起動・検索フォーム初期化・専用DAO読取りを実行できた。

最終SHA256は C477C908EC3081DD1CEEB16885922BF3CBD5A04E79645E2ACE9E8A3FF002ACFB。実行終了後のSHAをdeployment-02.jsonに記録した。Access起動で内部管理情報が変わる場合があるため、引渡し時のSHAを最終固定する。

入力はAccess/specのみ。独立業務仕様8.0、README・プロジェクト情報・Access規約・方式別共通・DB索引は8.1。最新版の利用者指示で旧分離配備を単体評価へ変更した。業務契約は維持する。tools/generate_schema.pyはAccess/specだけを読み、６表・業務89列・７FK・５分類70コードを生成する。他方式・外部共通ソースに依存しない。全ローカル入力SHAはdeployment-02.json、成果・ソース・証拠一覧はaccess-evidence.jsonに保存する。

| 検査 | 今回の実行結果 | 原本 |
| --- | --- | --- |
| 最小任意複合FK | 21項目通過 | access-fk.json / raw.log |
| 単体ACCDB通常業務 | 31項目通過 | access-single-02.json / log |
| 拡張業務・物理学生・権限・監査・確認 | 77項目通過 | access-single-02.json / log |
| 実フォーム・確認ダイアログ | 29項目通過 | access-single-02.json / log |
| 異なる２Accessプロセスの最後１席 | 通過、Saved１件、E-STU-102１件、人数1/定員1、学生CREATE監査1 | access-race-02.json / log |
| 正式成果の初期状態・実起動・表・FK・試験除外 | 19項目通過 | access-deployment-02.json / log |

表の原本名には全て20261012-build-04-接頭辞が付く。最小検査は仕様7.4、単体試験は独立8.1配置へ変更後に新規fixtureで実行した。過去合格を新配置の合格に流用していない。build-06元入力は当時の比較証拠として保持し、最終実行入力はAccess/specファイル別SHAで特定する。

旧STR-ACCESS-001の再検証は、双方Required=False、AllowZeroLength=False、分類既定値なし、緊急４項目一式の行内ValidationRule、属性0の参照整合付きFKで行った。実学生AddNewでも全NULL・全非NULLは成功、部分NULLは全14組合せ拒否、参照中親DELETE／キーUPDATEはDAO3200で拒否、不正コード・別分類も拒否。FKを解除していない。

業務試験は採番・版1、補助文字往復、変更なしの版／監査不変、旧版、定員、論理削除と検索除外、最小一覧DTOを確認した。拡張は緊急一式クリアと分類変更列監査、Reader/Staff/Admin、不成立E-COM-001と認可E-COM-002、故意の監査失敗による業務取消、初期値同値／差分停止、保護コード、停止中名称変更UPDATE、実状態遷移DISABLE/ENABLE、候補全消失時の再確認と０候補再確認後保存を確認した。

実フォームは未検索・20件・01/02、一覧・全文、AppliedCriteria、クリア、未所属選択、旧番号固定、人数/定員、和暦４部品、非自動保存、Reader制御、新規初期値を検査した。実確認ダイアログは０候補、全21件中20件表示、和暦、理由必須、理由付き続行、既定取消/Esc、削除対象と取消を実行した。

競合試験のAccess PIDは359532 / 305740。開始09:25:20.1027163Z / 09:25:20.1343645Z、結果Saved / ValidationFailed E-STU-102。双方は同じ単体fixture・ゲート・業務／監査ファイルを使用し、人数超過も失敗側監査も発生しなかった。途中から自動再試行していない。

全fixtureはsrcs/Access/build内に区別保存する。single-01/02は業務試験、single-03は２プロセス競合、final-stagingは初期表の組立素材。旧分離fixture群は旧構成の証拠。配布成果からstaging/fixtureへのリンクはなく、正式ファイルを業務サンプルで変更していない。

途中の実装失敗も保存した。VBA予約語、閉じたRecordset後始末、初期ListBoxのParent未確立による91、フォーム初期化91、試験の月日ゼロ埋め比較を修正し、service-13は31/77/20通過、その後単体single-02は31/77/29通過。中断/RPC切断でraw.logだけの実行は合格扱いしない。race-01はlock_bitを常時Falseと誤判定してFailedとなった。正常な確定反転を検査するようハーネスを修正し、新規single-03でrace-02通過。deployment-01は19検査通過後COM解放前のファイルロックでSHA保存失敗。解放を修正してdeployment-02では検査とSHA保存まで通過。旧失敗ログは保持する。

実環境はAccess/MSACCESS.EXE16.0.20430.20146・64bit、DAO.DBEngine.120/ACEDAO.DLL16.0.20430.20032、Python3.11.9。Office32bit、共有切断、10000/10001件性能、確定応答喪失、全共通ベクトル、目視配置は未実施。VBA役割制御は直接ファイル編集者に対する強いDB境界ではない。

新たな構造問題は検出していない。単体Access生成と利用可能な実機試験は完了した。仕様対応と手順はsrcs/Access/SPEC-MAPPING.md / README.mdに記載した。
