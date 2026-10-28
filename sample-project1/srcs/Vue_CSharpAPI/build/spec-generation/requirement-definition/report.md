<!-- spec-meta: {"schema":"spec-md/1.0","documentId":"VUE_CSHARPAPI-REQUIREMENT-RUN","version":"1.0","path":"sample-project1/srcs/Vue_CSharpAPI/build/spec-generation/requirement-definition/report.md","sheets":[{"heading":"入出力と範囲","kind":"GRID","sheet":"01_入出力と範囲"},{"heading":"確認結果","kind":"GRID","sheet":"02_確認結果"},{"heading":"残件と未実施","kind":"GRID","sheet":"03_残件と未実施"}]} -->
# Vue_CSharpAPI 要件逆生成の今回記録

版1.0／2026-10-28。stage=requirement-definition、generationMode=spec-to-requirements、Agent=AG-REQUIREMENT 0.2。

## 入出力と範囲

[要件定義書](../../../../../spec/Vue_CSharpAPI/要件定義書.md) 1.0を同方式の既存仕様から作成し、READMEと既存文書一覧へ入口を追加。業務入力は根拠資料表の13文書。ID・版・SHA-256・適用範囲は[manifest](manifest.json)で固定。未コミット内容を含む実ファイルハッシュを入力の識別に使用した。

機能22、データ7、非機能・制約11、受入24、QA/引継ぎ8件。確定前提・既存仕様・設計案・未確定を分け、新たな承認と扱わない。

## 確認結果

構造・LIST・リンク・方式内依存・根拠ID/版/ハッシュ・全要件の受入対応を確認しPASS。全40要件が対応する受入条件を持つ。受入はすべて未実施、QA未確定の目標は採用後の条件とした。[検査結果](validation.json)へ対象ハッシュと範囲を保存。

作成担当/root/req_webが自己確認、独立担当/root/req_desktopが元資料と方式前提を照合。rootが最終版の機械検査を実行した。AIレビューは利用者承認や製品試験の代替ではない。

Cookie/CSRFとAPI認可を継承。SharedAccessを適用せず、旧形式通知・未検索再初期化と最終所属期間の重なりを明記。

## 残件と未実施

未確定事項は要件定義書のQA章へ保持。利用者承認、アプリ生成/ビルド、実DB、実機/IME/端末/性能/受入、Excel/PDF変換、正式採点は未実施。formalScore=null。

元の業務仕様・QA・正式試験コード・fixtureは保持。今回の仕様追加と入口更新、専用固定記録だけを作成し、過去の試験結果を今回のPASSへ流用していない。
