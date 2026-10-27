# Agent機構の試験

workflow.test.mjsは許可・入力hash・パス・2回上限・結果の対応、sql.test.mjsは型・式・FK容量の回帰、vba-data.test.mjsは非実行の定数抽出、Test-AccessExtractor.ps1はAutoExec/起動フォーム・Unicode・古い出力の除去を検査する。アプリ固有の正式試験は対象sourceRoot/tests/にある。

優先対象は許可外パスやjunctionの拒否、原本hash不変、作業コピーの同一性、起動処理と外部接続の抑止、非連結フォームとイベント内コードの抽出、生成器が追加した表の検出、未取得と不存在、複合関係、型/照合/NULL/日付、部分失敗時の記録、最新manifestの整合、方式外参照の拒否。

取得抑止は専用の使い捨てfixtureで検証してから対象の実抽出へ進む。DAO/Access、SQL Server等が使えない試験は未実行またはskipとし、抽出・互換性の合格として扱わない。今回の文書確認をこれらの試験の実行済み結果にしない。
