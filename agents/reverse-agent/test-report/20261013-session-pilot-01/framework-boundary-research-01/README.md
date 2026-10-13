# 受信値とサービス引数の境界調査

2026-10-13。対象は学生検索・学生登録の作成手順であり、業務ソースの改修・実行試験ではない。

今回のカプセルに含まれるStudentManagement.Web.csprojはnet10.0を指定する。WebHostSetupのAddControllersWithViews設定とStudentSearchInputを原文で確認した。前稿の空白入力に関する断定はサービスの分岐をHTTPフォーム原入力まで広げており、その根拠が不足していた。

ASP.NET Core v10.0.0の一次ソースを追加調査した。[SimpleTypeModelBinder](https://github.com/dotnet/aspnetcore/blob/v10.0.0/src/Mvc/Mvc.Core/src/ModelBinding/Binders/SimpleTypeModelBinder.cs)には、文字列モデルでConvertEmptyStringToNullが有効かつ空白のみの場合にnullへ変換する分岐がある。[DisplayMetadata](https://github.com/dotnet/aspnetcore/blob/v10.0.0/src/Mvc/Mvc.Core/src/ModelBinding/Metadata/DisplayMetadata.cs)はこの設定の初期値をtrueとする。

これは外部依存の静的調査であり、今回の配置先ランタイム版・カスタム設定の実効値やHTTP実行結果を証明しない。一次ソースは既存カプセルと計画の封印対象に入っていないため、今回のAI factsへobserved-sourceとして混入させない。第2稿へ渡す修正指摘は、HTTP受信値、バインド後DTO、Normalizer/サービス引数を区別し、確認できる層と未確認の境界を明示するという原ソースからの指摘に限定した。

汎用prompts.pyにも受信・バインド・サービスの層を区別する確認手順を追加した。特定項目の期待値や空白入力の業務正解をPythonの条件分岐へ固定していない。
