# Express17導入入口・sqlcmd選択修正 R2

2026-10-12。2方式の `database/Deploy-Database.ps1` のみを修正した。旧準備報告は保持する。

旧実装のGet-Command sqlcmdは本PCで2件を返し、Sourceの配列がstringへ連結されて単一実行ファイルとして使えなかった。各方式に独立した候補選択を実装した。実exeのPE resource ProductMajorPart>=16、Microsoft SQL Server / SQLCMD.exe識別とPE machineを確認し、x64優先・製品版降順で適合する1件だけを返す。Go版・旧ODBC版・不適合な明示pathは使用しない。候補exeは起動せず、PlanOnlyでも同じ選択と版/hashを記録する。

実候補はmodern64bit `C:\Program Files\Microsoft SQL Server\Client SDK\ODBC\170\Tools\Binn\SQLCMD.EXE`（ProductVersion16.0.1000.6、FileVersion2022.0160.1000.06）と旧x86 SQLCMD（ProductVersion9.00.3042.00、FileVersion2005.090.3042.00）。FileVersion先頭の年をSQL majorとして扱わない。

PowerShell 7.6.5で20/20の未接続検査を実行した。2入口の完全parse、実2候補からの単一選択、候補順逆転でも同じ選択、modern明示path検証、旧9版の明示/候補指定拒否、各Install/Verify/BindPrincipalのPlanOnlyと安全ガードを確認した。SQLCMD起動0、SQL接続0、SQL文実行0、昇格0。

JSONに現在の6入力hashと旧記録のhashを照合して保存した。変更は各Deploy-Database.ps1だけで、001_schema.sql / 002_seed.sql / 003_web_permissions.sql / 004_verify_deployment.sql / EXPRESS17.mdは不変。新しいPlanOnly実出力をraw.logへ保存した。

rootの新しい管理者インストールexecute-01は、この未接続検査の完了後に承認・取得中と通知された。本R2はインストール・導入・実SQL・有効権限・アプリ試験の合格を示さない。今後の明示依頼を受けて、導入済み各DBへ生成コードによる読取りを検査する。sysadminWindows接続の読取り成功を書込み・認可・最小権限の合格として扱わない。
