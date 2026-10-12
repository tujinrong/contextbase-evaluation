# 仕様書解析用の独立ソース

各ZIPを別の作業領域へ展開して、当該方式だけを解析します。原仕様、評価基準、試験期待値、入力manifest、他方式を含めません。元のsrcs/<方式>を丸ごと解析入力へ渡すとspecが混入するため、このZIPを使用してください。

- [VB.NET_WinForms source](VB.NET_WinForms-source.zip)
- [CSharp_WPF source](CSharp_WPF-source.zip)
- [CSharp_ASPNET source](CSharp_ASPNET-source.zip)
- [Vue_CSharpAPI source](Vue_CSharpAPI-source.zip)
- [COBOL source](COBOL-source.zip)
- [AS400_RPG source](AS400_RPG-source.zip)
- [Access source](Access-source.zip)

Accessを実行する際の配布成果はsrcs/Access/StudentManagement.accdb 1個です。これらのZIPはプログラム解析用のソース入力です。
