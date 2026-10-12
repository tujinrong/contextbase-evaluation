# 全方式 fixture/source 独立性監査（修正前・中間記録）

20261012-evidence-01／test-project1／2026-10-12。**PRE_FIX_INTERMEDIATE_AUDIT。最終合格ではない。** 利用者によるbug修正指示を受け、MVC本体のvalidation描画とWPF試験ホスト起動を別担当が修正中である。root通知後に新しい実行IDで再監査する。この記録を上書きして最終結果にしない。

既存 check-isolation.mjs の検査本体を読取り実行した。固定出力が指定された監査保存先と異なるため、メモリー内でroot/出力prefixを今回値へ置換し、元スクリプトのmkdir/writeを抑制した。元checkerファイルとZIPは変更していない。command・置換・元/実行コードhash・stdout結果をJSONへ記録した。

既存検査：841ファイル／1511参照、指摘0。追加のtests/EvidenceHost/GuiEvidence/EvidenceおよびCOBOL/RPG試験harness：33ファイル／14 project item、相互方式・Shared等への依存指摘0。元checkerでtestsを除外する相互参照判定、cs/vb/basとwildcard Compileを補完した。すべてのproject itemは自方式内を参照し、方式間symlink/hardlinkも検出されていない。動的パス全般の保証ではない。

## fixture の責務

| 方式 | 今回fixtureの独立性・限界 |
| --- | --- |
| VB.NET_WinForms | 自方式のproduction Forms/Presenters/Controls等を同方式内Compile参照。撮影サービスは専用JSONを読む。保存/削除は拒否し、SQLへ接続しない。 |
| CSharp_WPF | 自方式StudentManagement.Wpf.csprojの画面/VMへ専用FixtureGatewayを注入。保存/削除は拒否。起動修正が進行中のため最終hashは後で再固定。 |
| CSharp_ASPNET | 自方式Web project/controller/Razor資源を参照。DBサービスをfixtureへ置換し接続文字列を空にする。読取り合成JSON、保存/削除はForbidden。本体validation描画修正が進行中。 |
| Vue_CSharpAPI | 自方式backend/APIと当方式wwwrootを使用し、他方式Webプロジェクトを参照しない。専用JSON、DBサービス置換、保存/削除拒否。 |
| COBOL | 当方式の既存production exeを実行。新仮名/学籍番号入力を境界検証へ渡すだけ。CGI撮影は401/400の実HTML、SQL接続前に拒否する。 |
| AS400_RPG | 当方式production C helperを新しいtest exeへコンパイル。専用仮名/学籍番号fixture。IBM i/Db2/5250なし、画面は捏造しない。 |
| Access | 自方式内で新規SingleFile ACE fixtureを構築し、既存MaintainClass/SaveStudentで３学生・１クラスを保存、４CREATE監査をDAOで読返し。１accdb原本はhash読取りのみ。新規ACE fixture内の書込みを共有SQLデータ作成と扱わない。 |

撮影fixtureの疑似サービス/主体は、SQL実DBの認証・保存・監査・競合合格の代替ではない。共通DBは構造契約未修正のため移行停止中で、業務テストデータを投入していない。Accessの集合先test-reportへの出力は監査/報告の集約であり、別方式の仕様・ソース・DDLへの依存ではない。

## 前回固定入力との差分・ZIP

sqlserver-12 outputs manifest の既存srcs 986ファイルを再hash比較した。差分2件：

- test-project1/srcs/Access/tests/Test-Application.ps1
- test-project1/srcs/VB.NET_WinForms/Tests/StudentManagement.WinForms.Tests.vbproj

既存Access Test-Application.ps1は試験COM解放を追加した差分。VB既存Tests projectはGuiEvidenceのソースを通常のテストCompileから除外するローカル設定を持つ。いずれもtests配下で、他方式への参照・production DB/DDLの変更ではない。修正進行中の状態を最終合格へ流用しない。

今回比較したdatabase SQL/JSON資源31件の差分は0。方式別source ZIP７件はbuild-10 source-packages manifestと全hash一致し、再生成していない。原本Access accdbもsqlserver-12 artifactと同hash `838f5fe63826fce58face6c5102d363af41c3ef433d6b2d7229c8d5de0c93de5`、監査では開いていない。全根拠hashはJSONへ保存した。

## 共有SQL DB の読取り再検証

sql-readonly.json に、ODBC Driver18／Windows認証／Encrypt=Yes／TrustServerCertificate=No／HostnameInCertificate=localhostの実接続と固定SELECT４本を保存した。13検査通過。サーバーはExpress17.0.5005.3、Windows-only、接続暗号化TRUE。DBは contextbase_test_project1 のみ、ONLINE、compatibility160、Japanese_XJIS_140_CI_AS。ユーザー表・ユーザーオブジェクト・ユーザーassembly・アプリ独自役割は全０。

監査接続はsysadminなので完全なmetadata可視性を確認できたが、通常アプリ主体の権限合格ではない。DDL/DML・ログイン/役割・DB option・サービス・サーバー設定変更は一切行っていない。共有DBの業務テストデータ投入０。共通スキーマ/役割/排他/正規化契約の修正後に移行を再開する。

COBOL loopbackホストはroot撮影完了通知まで維持する。監査担当はブラウザー/GUIを操作していない。
