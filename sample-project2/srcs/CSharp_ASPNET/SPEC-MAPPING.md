# 仕様と実装の対応

凍結された方式内43仕様文書はbuild/generation/inputs.jsonを参照します。詳細83項目・17イベント、共通検査、BUI/UI-P/DUIのUI条件はspec-implementation-map.jsonから実装ファイル・シンボル・UI ruleへ追跡します。

F01はAccountController/AuthService、F02はMenuController/UiController/共通Shell、F03はEmployeesController/SearchReturnCoordinator/SearchState、F04はEmployeesController/EmployeeService/EditState、F05はReportService/ExportOperationRegistry、F06はCodesController/CodeServiceです。共有Razorとsite.css/site.jsが画面を構成します。

PH05はSearchRaw/OpenInput/復帰Coordinatorで保持します。DQA-UI05はJSON fetch200 envelope→一度GET、ログイン303を区別します。履歴・別Tab・状態失効・保存失敗・Unknownは別の検査対象です。

この対応は静的追跡です。実行検査は各記録のexact source/artifact/input SHAに限定し、未観測rule/物理IME/実BFCache未到達/SQLServer2022実機/正式Pilot・受入・採点をPASSとしません。
