# preflight参照分類の限定修正

runId=sp2-ui-regenerate-20261029。アプリ生成前のツール検査。変更はpreflight.mjs、preflight-tests.mjs、input-scope.mjsの3ファイルに限定し、Agent契約・共通docs・採用規約の版と本文は変えていない。

参照を、収集済み仕様入力、既に凍結される共通規約、既知の設計Agent規則への存在案内、自方式のbasic/detail工程report.mdへの存在案内、凍結common docsから既知raw READMEへの出典案内へ区分した。設計ガイドは入口3文書・固有rules/workflows文書とそのディレクトリの完全一致、自方式記録は2本のreport.md、出典はreferences/web-ui-standard/README.mdだけ。案内から内容読取り・hash・再帰展開・入力追加を行わない。既存の凍結共通規約は予定どおり入力検査し、案内の未読と混同しない。

受理するlocal参照にはlstat/realpathと通常ファイル/ディレクトリ確認を適用する。自方式のsrc README、他方式/他projectの記録、任意のAgent .tmp/build/追加規則、任意raw文書やspec-evalへの依存を許可しない。選択spec内であってもspec-eval/spec-analysis/.tmp/build/.gitは先に拒否し、実ディレクトリ名とリンク表記の大小文字も除外判定へ揃えた。仕様ディレクトリの存在案内を仕様ファイル入力と誤表示しない。

隔離fixtureのpreflight回帰は285 assertions PASS。存在案内4種の本文をreadFileSync監視で拒否したまま通過、入力へ追加されないこと、missing/junction leaf/redirected parent/encoded escape/除外subtree/実名.TMP、inspect-onlyの全fixture不変、既存の入力固定/失効/方式選択/WEB・WinForms・Text/Access renderer/明示追加方式/ZIPの回帰を確認した。途中のfixture正例で空hrefを作っていた試験側を修正し、最終3コード版で全件を再実行した。

実specはreadFileSync監視付きinspect-onlyでAccess70入力/Web66入力を維持し、双方findings0。raw README・Basic規則・自方式設計reportは入力に含まれず内容未読。project全ファイル/ディレクトリの名前・サイズ・mtimeとツールSHAは実inspect前後で不変。実アプリのsource本文をsnapshotのために読んでいない。入力ファイル/SHA集合と実行環境、独立レビューは同名JSON/reviewへ固定する。

通常の実project preflight、生成・製品UI JSON・DB実行は未実施。正常preflight/manifest/ZIP等の回帰は隔離した合成fixture内だけである。ツールのPASSはアプリ・UI・DB・受入・正式採点の合格ではなく、formalScore=null。
