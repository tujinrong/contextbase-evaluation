# 解析用独立ソースの入口

2026-10-25。解析用ZIPは各方式build/source.zipへ固定名で更新する。このフォルダーへ旧ZIPや実行ID別のコピーを保存しない。履歴はGitで参照する。

- [VB.NET_WinForms source](../srcs/VB.NET_WinForms/build/source.zip)
- [CSharp_WPF source](../srcs/CSharp_WPF/build/source.zip)
- [CSharp_ASPNET source](../srcs/CSharp_ASPNET/build/source.zip)
- [Vue_CSharpAPI source](../srcs/Vue_CSharpAPI/build/source.zip)
- [COBOL source](../srcs/COBOL/build/source.zip)
- [AS400_RPG source](../srcs/AS400_RPG/build/source.zip)
- [Access source](../srcs/Access/build/source.zip)

ZIPは原仕様・spec-eval・入力manifest・試験期待値・他方式・中間物を除外する。移動後のsample-project1/spec/全体は、ZIP作成と逆生成の取得・調査・独立検証のいずれからも除外する。元の方式フォルダーを丸ごと逆生成へ渡さない。ZIPの今回run-id・source hash・member hashは各方式build/generation/source-packages.jsonで照合する。Accessの配布実体は[最終accdb](../srcs/Access/build/StudentManagement.accdb)1個であり、ZIPはソース解析用。
