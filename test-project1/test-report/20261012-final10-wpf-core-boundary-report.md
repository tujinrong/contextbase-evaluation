# WPF Core 純粋境界試験更新

2026-10-12。変更対象はsrcs/CSharp_WPF/tests/Core/Program.csだけです。現在のnative DB入口に合わせ、複合不正StudentDraftをStudentNormalizer.Normalize(raw,day)へ直接渡し、InputValidationException.Errorsの拒否・フィールド対応を検査しました。SaveResultを作成して代替していません。

Viewer/StaffのクライアントRoleからDB更新権限を判定する旧2件を、形式不正SessionIdと空PrincipalがOpenより前に拒否される2件へ置換しました。DBロールの認可は実DB試験の範囲です。

Core試験プロジェクトは0警告/0エラーでビルドし、純粋な境界96件PASSです。SQL接続・DB認可・DDL/CRUDと対話画面は未実施です。production/SQLCLR/他方式のソースは変更していません。

- [機械結果・試験ソースhash](20261012-final10-wpf-core-boundary-results.json)
- [ビルド生ログ](20261012-final10-wpf-core-boundary-build.log)
- [実行生ログ](20261012-final10-wpf-core-boundary-run.log)
