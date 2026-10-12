# Access の画面撮影用独立fixture

試験ハーネス版 r6／2026-10-12。現在の撮影入口は `Seed-UiFixtureR6.ps1` が生成した `build/20261012-evidence-01-ui-r6/20261012-build-04-access-single-evidence-01-ui-r6.accdb` です。実Access FileFormat=12、架空学生３件・クラス１件・CREATE監査４件をDAOで読返します。修正後の原本SHA-256 `D1777167FD7423BF4399F05D006519FD5A8E005A6FEF2E56B1A8F11AAD73EC87` を引数で固定し、原本を開かず前後照合します。

```powershell
./tests/Evidence/Seed-UiFixtureR6.ps1 -ExpectedProductionSha256 D1777167FD7423BF4399F05D006519FD5A8E005A6FEF2E56B1A8F11AAD73EC87
```

R6出力の再実行は上書きガードで停止します。今回のログ・実DAO読返し・入力ハッシュは `test-project1/test-report/20261012-evidence-01/Access-ui-r6/`。NoStartup、SELF、外部リンクなし。撮影では新規フォームを空のまま保存し、`E-DATE-001: 生年月日の元号・年・月・日を確認してください。` の中点3文字と入力保持を確認できます。通常の操作手順は同報告のREADMEに記載しました。

`Test-MessageEncodingR6.ps1` は58通知の期待値をUTF-8原仕様からPowerShell側で作り、実VBAのMessageTextと完全一致を照合します。項目ラベルと現ANSIコードページでのproduction文字列リテラル走査も行います。`Test-UiEncodingR6.ps1` は実フォームの候補SQL6件をDAOで実行し、中点を含むSQLと確認キャプションを検査します。双方は方式内buildの使い捨てコピーだけを開き、GUIは表示しません。R5の137等は今回再実行していません。

R5 helper・fixture・137等の結果は履歴として保持しています。`Test-FormatAndInitialState.ps1` と `Test-SearchAllR5.ps1` の旧実行結果をR6合格数へ加算しません。

R4 helper・fixture・読返しも履歴として保持しています。R4はACE形式とBooleanを修正済みですが、検索「すべて」空表示が未修正だったため、現在の撮影入口には使いません。

以下の旧helperと旧fixtureは修正前の証拠として保持しています。旧fixtureは拡張子がaccdbでも内部はMDB形式でした。修正後成果の試験結果として流用しません。旧helperの原本ハッシュガードは修正前の値を保持するため、現在の原本へ再実行すると停止します。

`Seed-UiFixture.ps1` は指定した新規buildフォルダーだけへ、既存Build-Access.ps1からSingleFile/IncludeTests/NoStartup ACCDBを作る。原本StudentManagement.accdbは開かず、既知SHA-256を前後照合する。既存出力や報告がある場合は停止する。

生成後、テスト専用 `modEvidenceUiSeed.bas` をAddFromStringで新規ACCDBへ追加し、VBAをコンパイルする。登録はproductionのMaintainClassとclsStudentService.SaveStudentを通す。直接INSERTで業務検査/監査を回避しない。Class1件・仮名学生3件、CREATE監査4件のDAO読返しを行う。ui-data.jsonは今回の実DAO読返しから保存した架空データであり、初期配備マスタではない。

Access方式フォルダーで新規作成時に実行したコマンド:

```powershell
./tests/Evidence/Seed-UiFixture.ps1
```

同名fixtureが既に生成済みのため、現在のスクリプトを再実行すると上書きガードで停止する。新しいIDへ変更して使う場合はテスト専用guardと報告先をまとめて更新する必要がある。

出力は `build/20261012-evidence-01-ui/20261012-build-04-access-single-evidence-01-ui.accdb`。StudentBackendPath=SELF、外部リンクなし。initial-staging.accdbは組立材料で、最終fixtureはそのファイルを参照しない。Visible=falseのCOMで完了し、CloseCurrentDatabase/Quit済み。GUIは表示していない。

rootの撮影では、この新規fixtureだけを開き、frmStudentSearchを通常表示する。NoStartupなので自動起動フォームは設定していない。検索初期条件の在学/休学で2件、卒業を追加すると3件。新規登録・リストの学生を開く操作はproductionフォームの通常操作を使用する。直接frmStudentEditを開く場合のOpenArgsは新規 `|evidence`、既存 `1|evidence`。原本StudentManagement.accdbを開いて撮影しない。

今回の実記録は `test-project1/test-report/20261012-evidence-01/Access-ui/`。共有SQLへの接続/配備/移行、GUI操作・スクリーンショットはこのseed実行の対象外。
