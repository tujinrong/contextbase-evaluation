# 方式フォルダー名変更の検証

2026-10-28。方式IDをAccess-To-CSharp_ASPNETへ変更した。Agent正本はagents/converts/access-rebuilder-agent/、sourceRootはtest-project1/srcs/Access-To-CSharp_ASPNET/、specRootはtest-project1/spec/Access-To-CSharp_ASPNET/。旧source/specフォルダーは残していない。

Agent設定・ルール・実行指示・正式試験fixture・方式索引・共有DBの説明・DB新規作成helperを新名へ揃えた。既存DBの所有者マーカーは履歴として保持し、読取り検査は旧値と新値の両方へ明示対応する。DBの再作成・名前変更・seed投入・業務データ更新は行っていない。

Debug solution buildとRelease publish、配布ZIPの実隔離Release buildは成功。警告0・エラー0。Agent試験11件、既存DBの7表／7関係／70コード検査、新パスのTrainingSqlプロファイルで既存学生2件の検索・編集・日付表示・PC保存位置の確認がPASS。

移動前の174ファイルは保全し、Core/UIの35ファイル・原Access・封印済み2回の台帳・抽出原文／過去入力記録は不変。過去記録内の旧ID・絶対パス・hashは書き換えず、今回の配置検査と区別した。原Accessの再抽出、追加訓練、正式採点は未実施。formalScore=null。

Visual Studioでは[StudentManagement.slnx](../../StudentManagement.slnx)を開き直し、StudentManagement.Web／TrainingSqlで起動する。
