# 独立配置検査 20261012-isolation-draft-04

FAILED。7方式、760ファイル、1493参照。

- test-project1/srcs/VB.NET_WinForms/database/README.md: SHARED_RESOURCE_PATH 
- test-project1/srcs/VB.NET_WinForms/README.md: SHARED_RESOURCE_PATH 
- test-project1/srcs/CSharp_WPF/database/README.md: DOCUMENT_REFERENCE_MISSING native/README.md

ローカル参照・ProjectReference・独立specの閉鎖・共有元不使用を検査。外部処理系や動的経路全体の保証ではない。
