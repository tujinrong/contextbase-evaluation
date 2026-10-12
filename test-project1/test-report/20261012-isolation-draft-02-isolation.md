# 独立配置検査 20261012-isolation-draft-02

FAILED。7方式、723ファイル、1484参照。

- test-project1/srcs/VB.NET_WinForms/database/README.md: SHARED_RESOURCE_PATH 
- test-project1/srcs/VB.NET_WinForms/database/tests/SqlServer.IntegrationTests.csproj: PROJECT_REFERENCE_OUTSIDE ../../../Shared/StudentManagement.Core/StudentManagement.Core.csproj
- test-project1/srcs/VB.NET_WinForms/README.md: SHARED_RESOURCE_PATH 
- test-project1/srcs/VB.NET_WinForms/StudentManagement.WinForms.vbproj: PROJECT_REFERENCE_OUTSIDE ..\Shared\StudentManagement.Core\StudentManagement.Core.csproj
- test-project1/srcs/VB.NET_WinForms/Tests/NativeSmoke.csproj: PROJECT_REFERENCE_OUTSIDE ..\..\CSharp_WPF\StudentManagement.Wpf.csproj
- test-project1/srcs/CSharp_WPF/database/README.md: DOCUMENT_REFERENCE_MISSING native/README.md

ローカル参照・ProjectReference・独立specの閉鎖・共有元不使用を検査。外部処理系や動的経路全体の保証ではない。
