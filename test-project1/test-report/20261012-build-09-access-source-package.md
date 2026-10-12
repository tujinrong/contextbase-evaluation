# Access source ZIP 単独ビルド・実業務試験

実施日2026-10-12。作業ディレクトリは `srcs/Access/build/source-isolation` のみです。原仕様、spec-eval、他方式を読みませんでした。27個のZIP部材と展開ファイルをSHA256で照合し、すべて一致しました。source ZIP は原仕様・試験期待値・生成器を含みません。生成済みDDL/Schema/Seed、BAS/CLS、Build-Access.ps1だけから構築しました。

Access-source.zip SHA256 は `9A1D7F0E6B74028263BB064D35F7A285FE8632E9ECDD290E7E005E79DA9E9085`、51,362 bytes。開始時09manifestと、現在の10manifestのAccess SHAが一致し、退避した09 ZIPのSHAも一致しました。他方式のZIP更新を、このAccess試験の入力変更として扱いません。全コマンド・個別137チェック・部材ハッシュは [JSON](./20261012-build-09-access-source-package.json)、実コンパイル・DAO・各試験出力と準備失敗は [raw log](./20261012-build-09-access-source-package.raw.log) に保存しました。

```powershell
./Build-Access.ps1 -SingleFile -CreateBackend -Compile
./build/Run-SourcePackageTests-03.ps1
python -X utf8 ./build/Finalize-SourcePackageEvidence.py
```

ZIP内のBuild-Access.ps1で新しいStudentManagement.accdbを生成し、VBAコンパイルが通過しました。これはZIP展開内の成果で、主配布ACCDBと別です。物理表はすべてローカル、５分類70コード、クラス・学生・監査０、４フォーム、単一ファイルSELF設定、試験モジュール不在を確認しました。生成器や元仕様の再読取りを要しません。

| 検査 | 最終結果 |
|---|---|
| source ZIP部材照合 | 27/27一致 |
| source ZIPのみの構築・VBAコンパイル | 終了0、成功 |
| 通常業務 RunSelfTests | 31/31 PASS |
| 権限・確認・競合・監査等 RunExtendedTests | 77/77 PASS |
| 実フォーム・確認ダイアログ RunFormTests | 29/29 PASS |

外部試験はビルド完了後の使い捨てコピーにだけ、既存modSelfTestsを同一ハッシュで注入しました。元のPowerShell testerはclone内へ複製し、元仕様ハッシュ収集の１行だけを除いて同じ期待値を実行しました。単一ファイルなのでroles.confを作りません。試験後の学生４・クラス１・コード71・監査15はその使い捨てコピーだけに残ります。fixture名のbuild04接頭辞は、既存外部装置のCheckFixtureガードに合わせた名称であり、今回新規に作成したbuild09コピーです。前回実行結果の流用ではありません。

準備試行01では試験コピーのStartupForm空文字をDAOが拒否し、業務試験を開始しませんでした。試行02は137項目とtester JSONがすべてPassedでしたが、wrapperが未設定LASTEXITCODEを誤判定しました。両試行のコピーと生ログを残し、03の新規コピーでプロパティ削除とJSON状態確認へ直した試験装置を再実行しました。03は終了0で137項目が通過しました。productionソースや業務仕様の変更はありません。

ZIPだけから構築したproduction SHA256 `C4714BE004F16BF31C4F4D26F5382BA44E08EB25BEFD7C4EB38CC8D62940E6E0` は外部試験の前後で一致します。主配布 `srcs/Access/StudentManagement.accdb` は開かず、SHA256 `C477C908EC3081DD1CEEB16885922BF3CBD5A04E79645E2ACE9E8A3FF002ACFB` が開始前・終了後で一致しました。ZIP、元activeソース、既存報告は変更していません。

実行環境はWindows 64bit Access/DAO、Office COM Version 16.0。Office32bit、別のクリーン端末・信頼設定、共有切断、10,000/10,001件性能、確定応答喪失、画面目視配置、逆生成採点は未実施です。
