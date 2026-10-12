# 仕様書解析用の独立ソース

以下のZIPは **20261012-build-10の凍結版** です。20261012-evidence-01で行った実装不具合の修正は、これらのZIPにまだ反映していません。[今回の修正・試験報告](../test-report/20261012-evidence-01/README.md)に最新ソースと配布accdbの版・hashを記録しています。修正後の逆生成評価を実行する場合は、新しい隔離ソースZIPを作成してから使用してください。旧ZIPを新改訂として扱わないでください。

各ZIPを別の作業領域へ展開して、当該方式だけを解析します。原仕様、評価基準、試験期待値、入力manifest、他方式を含めません。元のsrcs/<方式>を丸ごと解析入力へ渡すとspecが混入するため、このZIPを使用してください。

- [VB.NET_WinForms source](VB.NET_WinForms-source.zip)
- [CSharp_WPF source](CSharp_WPF-source.zip)
- [CSharp_ASPNET source](CSharp_ASPNET-source.zip)
- [Vue_CSharpAPI source](Vue_CSharpAPI-source.zip)
- [COBOL source](COBOL-source.zip)
- [AS400_RPG source](AS400_RPG-source.zip)
- [Access source](Access-source.zip)

Accessを実行する際の配布成果はsrcs/Access/StudentManagement.accdb 1個です。これらのZIPはプログラム解析用のソース入力です。
