# 実装の責務

workflow.mjsは入力・許可・パス・hash・反復上限・結果の対応を検査し、固定manifestを管理する。sql.mjsはDAO構造と検証済みの式の部分集合をT-SQLへ変換する。vba-data.mjsはVBAの定数配列を実行せず取り出す。

Access/DAO取得はscripts/Export-Access.ps1。移行設計とC#業務コードはCodexが抽出原文から作成する。学生管理固有の解答や既存Webソースをこの汎用実装へ埋め込まない。ContextBaseへの依存は追加していない。
