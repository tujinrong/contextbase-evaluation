# Azure 免费测试部署

版1.1 / 2026-10-23。范围：test-project1 / CSharp_ASPNET 的应用、独立 Azure SQL 数据库和单个所有者账号的网页登录。

- 网站：https://app-contextbase-student-8a14b4.azurewebsites.net
- 存活检查：https://app-contextbase-student-8a14b4.azurewebsites.net/health
- 订阅：8a14b46b-69eb-4469-84f6-1d5e5750c20c。
- 资源组：rg-contextbase-student-demo。区域：Japan West。
- 使用现有 Windows F1 免费计划：mcterp / ASP-mcterp-89b6。未调整该计划规格，未修改它已有的应用。
- SQL Server：sql-contextbase-student-8a14b4.database.windows.net,1433。
- 数据库：contextbase_test_project1_mvc。实际确认 useFreeLimit=true、freeLimitExhaustionBehavior=AutoPause；不是普通付费 serverless 数据库。用完免费额度后暂停至下月。免费额度与限制以 Azure 当前服务说明为准。
- 应用 SQL 用户：student_web，SQL 密码认证，student_staff 角色；部署管理员为独立账号 cbsetup。应用无 db_owner 权限。

## 复现与凭据

在本目录的上级应用目录运行。需要 PowerShell 7、已登录的 Azure CLI、.NET 10 SDK、Python/pyodbc 和 ODBC Driver 18。脚本固定目标资源，不会降级至付费规格。

```powershell
./deployment/Provision-FreeAzure.ps1          # 仅显示计划
./deployment/Provision-FreeAzure.ps1 -Execute
./deployment/Configure-AzureDatabase.ps1
./deployment/Configure-AzureWebLogin.ps1
./deployment/Publish-FreeAzure.ps1
python ./deployment/Verify-AzureRemoteDatabase.py
./deployment/Get-AzureDatabaseLogin.ps1
./deployment/Get-AzureDatabaseLogin.ps1 -ShowPassword  # 仅在本机显示应用账号密码
./deployment/Get-AzureWebLogin.ps1 -ShowPassword       # 显示独立的网页登录密码
./deployment/Get-AzureWebLogin.ps1 -CopyPassword       # 复制网页登录密码
```

密码由随机数生成，保存在 .tmp/deployment-state 下的 Windows DPAPI 加密凭据文件中，仅当前 Windows 用户和机器可以解密；不提交 Git，不包含在发布包内。Azure 的连接字符串只配置到该新应用。需要从其他电脑或 SSMS 连接时，在该 SQL Server 的网络设置中添加自己的公网 IP；不要开放所有 IP。部署脚本只临时开放部署来源，并在 finally 中移除该规则。长期规则仅允许应用出站 IP；计划迁移或出站地址变化后需重新配置。

## SQL 部署适配与验证范围

现有生成 DDL 中，5 个业务代码外键列的物理宽度为 varchar(1/2)，父列为 varchar(10)，实际 SQL Server 拒绝创建这些外键。Initialize-AzureDatabase.py 对部署输入进行精确适配：5 个引用列统一为 varchar(10)，保留原排序规则与可空性，并添加 DATALENGTH<=原宽度的 CHECK。原 DDL、生成器和原规格未修改；业务输入与 SQL 参数仍保持原长度。该缺陷也影响普通 SQL Server，并非 Azure SQL 独有。

原 seed 的表变量未指定排序规则，与目标代码表比较时发生排序规则冲突；部署适配为相应表变量字段补充与目标一致的排序规则，不改变代码值。初始化、已知空库恢复、种子和角色授权在事务中执行；未知状态拒绝恢复，不删库或删表。脚本输出源 schema 与适配 schema 的哈希。

实际数据库验证包括：精确表列、主键/唯一键、外键映射、7 个受信任外键、CHECK 名称和可信状态、7 个普通索引名称、5 类70代码、0学生/0班级、SNAPSHOT、应用账号权限及 TLS 证书验证。DatabaseSmoke 调用真实 SqlServerStudentService 的 LookupAsync 和 SearchAsync，使用独立 SQL 应用账号；Verify-AzureRemoteDatabase.py 从 Azure Windows worker 读取已配置连接执行只读验证。

Production 模式下未开启 evaluation 登录，/health 返回200。/health 的 database=not-tested 只是原有存活接口，不作为数据库验证证据。未进行学生增删改、负载或完整用户验收；未把本地 Express 专用测试作为 Azure 验收。免费 F1 可能休眠或回收，进程内搜索及确认状态会失效。

## 网页登录

入口：https://app-contextbase-student-8a14b4.azurewebsites.net/login 。账号为 admin，密码由 Configure-AzureWebLogin.ps1 随机生成，与SQL账号/密码完全分开。本次为单人测试部署，不提供注册、多用户、找回密码或账户管理。服务器只保存 ASP.NET Core IdentityV3 加盐密码哈希；用户名、哈希与 Administrator 角色通过该站点的 App Settings 配置，不放入源码或发布包。普通本地运行默认 LocalLogin:Enabled=false，不启用空密码或默认密码。

匿名访问业务页时跳转登录；API及未认证的写入请求仍返回401。登录与退出均要求CSRF令牌。会话Cookie为Secure、HttpOnly、SameSite=Strict，闲置30分钟失效；每次登录产生新会话ID。连续失败5次后在当前进程内限制登录5分钟，拦截请求不延长限制；F1回收会清除此失败计数。密码、用户名、角色或Enabled改变后，既有本地登录Cookie会在下次请求时失效。运行 Configure-AzureWebLogin.ps1 -ResetPassword 可生成新密码并更新服务器；普通重配也会重新加盐并使既有登录失效。

从应用目录执行 Get-AzureWebLogin.ps1 -ShowPassword 查看凭据；其Windows DPAPI文件位于 .tmp/deployment-state/web-login.credential.xml，仅当前Windows用户/机器可读取。密码重置需Azure CLI已登录并有该应用配置权限。验证脚本 Verify-AzureWebLogin.py 从 CB_WEB_LOGIN_PASSWORD 环境变量读取密码，用真实Chromium测试登录、错误密码、查询与退出；不记录请求正文、浏览器trace或密码。

重置密码先保存为web-login.pending.credential.xml，Azure配置成功后才替换当前本机凭据。若更新失败或结果不明确，原凭据和待生效凭据均保留；再次运行Configure-AzureWebLogin.ps1会重试同一待生效密码。

現在の配置はsample-project1（旧test-project1）。過去の生成日・runId・凍結入力パスは当時の記録として保持し、今回の改名で再生成/再検証済みとはしない。
