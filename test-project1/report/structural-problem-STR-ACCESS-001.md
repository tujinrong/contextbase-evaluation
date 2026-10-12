# STR-ACCESS-001 構造適合問題・中断報告

報告版1.0／2026-10-12。projectId=`test-project1`、工程=`build`、実行記録版=`20261012-build-03`。状態: **全方式のプログラム生成・修正・ビルドを中断**。担当報告の `S-ACE-001` は本件と同じ問題。

Access仕様は、緊急連絡先3項目の全未入力、続柄分類の固定NOT NULL、分類＋続柄値の参照整合付き複合FKを要求する。今回の通常のACE/DAO FK構成では、この正当な入力をDAO3201で拒否することを実機再現した。単独の誤記として訂正せず、指定どおり別Agentの設計・仕様修正を待つ。

## 入力仕様の根拠

| ファイル | 文書ID・版・行 | 要求 |
| --- | --- | --- |
| [共通09](../spec/共通/09_項目制約定義.md) | COM-STU-009、7.0、66～68行、REG-020～022 | 3項目のいずれか入力時だけ全3項目必須。全未入力はNULL相当 |
| [Access学生表](../spec/DB定義/Access/テーブル/01_m_student.md) | DBDEF-ACCESS-M_STUDENT、7.2、46行 | relationship_categoryはNOT NULL、続柄値が空でも固定値RELATIONSHIPを保持 |
| 同表 | 7.2、47行 | relationship_codeはNULL可。分類＋値の複合FKを指定 |
| [Access DB定義](../spec/DB定義/Access/01_DB定義書.md) | DBDEF-ACCESS、7.2、38行、C-006 | 分類列＋値列→m_code、RESTRICT、続柄値NULL可 |
| 同書 | 7.2、73行 | 学生4組の分類＋値をDAO.Relationで参照整合付きにする |

したがって全緊急項目が空の場合でも、保存値は `('RELATIONSHIP',NULL)` となる。本人電話等で他の必須条件を満たした学生を登録しても、現在の通常FK構成はこの部分NULLの組を受け付けなかった。

## 実機再現

Office/MSACCESS.EXE `16.0.20430.20146`、ACEDAO.DLL `16.0.20430.20032`、DAO COM `DAO.DBEngine.120`、ACCDBの専用試験バックエンドで検査した。

1. frontend/backend生成、VBAインポート・コンパイル保存コマンド、4非連結フォーム生成まで実施。
2. Unicode、正規化、和暦、空学生DB、管理者クラス保守と監査等の11検査を通過。
3. 緊急連絡先なし学生の新規保存で `SystemError/E-COM-004`、DAO3201となった。学生・学生監査は確定していない。
4. サービスから独立した2列表でも、SQLの参照整合付きFKと、仕様が指定する `DAO.CreateRelation(...,0)`＋2列Fieldsの構成の双方で同じ拒否を再現。

最小SQL再現:

```sql
CREATE TABLE z_fk_probe (cat TEXT(48) NOT NULL, val TEXT(20));
ALTER TABLE z_fk_probe ADD CONSTRAINT fk_probe
  FOREIGN KEY (cat,val) REFERENCES m_code(category_id,code_value);
INSERT INTO z_fk_probe(cat,val) VALUES('RELATIONSHIP',NULL);
```

エラーは「テーブル 'm_code' にリレーションシップが設定されたレコードが必要なので、レコードの追加や変更を行うことはできません。」だった。DAOによる独立再現手順・出力・バージョン・最終fixtureの状態は [担当報告](legacy-implementation.md)、[証拠JSON](legacy-evidence.json)、[fixture一覧とSHA-256](legacy-fixtures.json) に保存した。

最終再現の `srcs/Access/build/StudentBackend-23.accdb` はコード分類5、コード70、試験クラス1、学生0、操作履歴1、ガード1、空のDAO試験表0件。クラス・履歴は検査用データ。37個のACCDBは専用試験fixtureであり、正式配備の初期バックエンドではない。`srcs/.gitignore`で除外されるローカル証拠なので、別環境へ渡す場合は保存ファイルを別途移送する必要がある。ハッシュと再現手順はreportに残る。

## 判定の限界

**現仕様の通常FK構成で正当入力を保存できない**ことを停止理由とする。Accessのすべての構成・製品版で絶対に不可能と断定しない。Index.IgnoreNulls、Index.Required、外国キー用索引の作成順等を網羅していない。IGNORE NULL索引を前置した探索は、Relationオブジェクトの再Appendが無効となったため、適合・不適合どちらの証拠にも採用しない。

機械的構造検査は章・表・参照の形式を検査する。今回のACE意味適合はその検査対象外であり、`20261012-build-03-structure.json`の形式通過によって本件が解消したことにはならない。

## 中断範囲と別Agentへの引継ぎ

本件の直接影響はAccessの続柄未入力時の学生保存。ユーザーの中断指示に従い、VB、WPF、MVC、Vue/API、COBOL、RPGも含む全方式で新規生成・コード修正・ビルドを停止した。停止後は報告・証拠・途中成果の状態表示とハッシュ保存だけを行った。

分類列をNULLへ変更、未設定用のダミーコードを投入、緊急連絡先を必須化、FKの参照整合を解除する変更は採用していない。別Agentが現契約を満たす実機構成を確定するか、関係する共通・物理DB・方式別共通・詳細仕様を整合させる必要がある。

再開条件:

1. 緊急3項目の全未入力で正当学生を保存でき、非NULLの不正続柄を拒否し、参照中コード削除を拒否する構成を確定する。
2. 代替DAO索引設定で解決する場合は、再現可能な生成順・属性・実機証拠を仕様へ追加する。契約を変更する場合は影響文書の版と記述を整合させる。
3. 修正版の新規入力ハッシュと実行IDを固定し、空のfixtureで再生成・検査する。今回の形式通過、11通過、過去レビューの合格を新改訂へ流用しない。

途中ソース・検査状態は [全体中断報告](build-report.md) を参照。
