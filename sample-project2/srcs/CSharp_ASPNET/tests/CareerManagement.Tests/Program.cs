using System.Diagnostics;
using System.Security.Cryptography;
using System.Security.Cryptography.X509Certificates;
using System.Text;
using System.Text.Json;
using CareerManagement.Application;
using CareerManagement.Infrastructure.Authentication;
using CareerManagement.Infrastructure.Reports;
using CareerManagement.Infrastructure.Sql;
using CareerManagement.Infrastructure.State;
using ClosedXML.Excel;
using Microsoft.Data.SqlClient;

Console.OutputEncoding=Encoding.UTF8;
var root=Path.GetFullPath(Path.Combine(AppContext.BaseDirectory,"../../../../../.."));
if(!File.Exists(Path.Combine(root,"global.json")))root=Environment.CurrentDirectory;
var inputFile=Path.Combine(root,"build","generation","inputs.json");
using var inputJson=JsonDocument.Parse(File.ReadAllBytes(inputFile));
var currentRunId=inputJson.RootElement.GetProperty("runId").GetString();
var inputManifestSha256=Convert.ToHexStringLower(SHA256.HashData(File.ReadAllBytes(inputFile)));
var testedRuntimeArtifacts=new[]{typeof(EmployeeService).Assembly,typeof(BusinessClock).Assembly}.Select(a=>new{file=Path.GetFileName(a.Location),sha256=Convert.ToHexStringLower(SHA256.HashData(File.ReadAllBytes(a.Location)))}).ToArray();
var results=new List<object>();var failed=0;var cycle=args.Contains("--cycle")?int.Parse(args[Array.IndexOf(args,"--cycle")+1],System.Globalization.CultureInfo.InvariantCulture):1;
var ct=CancellationToken.None;var clock=new BusinessClock(TimeProvider.System);
async Task Check(string id,string name,Func<Task> test)
{
    var sw=Stopwatch.StartNew();try{await test();results.Add(new{id,name,status="PASS",elapsedMs=sw.ElapsedMilliseconds});Console.WriteLine("PASS "+id+" "+name);}
    catch(Exception ex){failed++;results.Add(new{id,name,status="FAIL",error=ex.GetType().Name,detail=ex is BusinessException b?b.Outcome.MessageId:ex.Message,elapsedMs=sw.ElapsedMilliseconds});Console.WriteLine("FAIL "+id+" "+name+" "+ex.GetType().Name);}
}
static void Assert(bool ok,string reason="Assertion failed"){if(!ok)throw new InvalidOperationException(reason);}
static async Task Expect(int msg,Func<Task> action){try{await action();throw new InvalidOperationException("Expected MSG-"+msg);}catch(BusinessException b){Assert(b.Outcome.MessageId==$"MSG-{msg:000}",b.Outcome.MessageId);}}
var definition=JsonSerializer.Deserialize<SeedDefinition>(await File.ReadAllTextAsync(Path.Combine(root,"fixtures","SP2-DEMO-01.json")),SafeInitializer.Json)!;
var adminPassword=DemoCredentialUpdater.Password;var staffPassword=DemoCredentialUpdater.Password;
var ui=args.Contains("--prepare-ui");
var browser=args.Contains("--prepare-browser")||args.Contains("--prepare-http")||ui;var http=args.Contains("--prepare-http");
if(ui&&File.Exists(Path.Combine(root,".tmp","ui-runtime","profile.json")))throw new InvalidOperationException("An owned UI profile already exists. Explicitly stop and clean up that fixture before creating another.");
var dbName=ui?"SP2_WebFixture_UI_"+Guid.NewGuid().ToString("N")[..12]:browser?(http?"SP2_WebFixture_Http_"+Guid.NewGuid().ToString("N")[..12]:"SP2_WebFixture_20261029"):"SP2_WebFixture_Test_"+Guid.NewGuid().ToString("N")[..12];
var options=new DatabaseOptions{ConnectionString=$"Server=.\\SQLEXPRESS;Database={dbName};Integrated Security=True;Encrypt=True;TrustServerCertificate=True",AllowedDatabase=dbName,Fixture=true};
var repo=new Repository();var database=new Database(options,new NoDbFaults());
var sessions=new SessionRegistry(clock);var current=new CurrentUserService(database,repo,sessions);var auth=new AuthService(database,repo,clock,sessions);
var employees=new EmployeeService(database,repo,current,clock);var codes=new CodeService(database,repo,current,clock);
var manifestPath=Path.Combine(root,".tmp","fixtures",dbName,"seed-manifest.json");
var created=false;
object? credentialMigrationEvidence=null;
try
{
    await Check("SQL-01","new owned fixture schema",async()=>{await SafeInitializer.CreateAsync(options,await File.ReadAllTextAsync(Path.Combine(root,"database","schema.sql")),ct);created=true;});
    if(!created)throw new InvalidOperationException("Fixture creation refused; no existing DB is reused.");
    await Check("SQL-02","seed exact SP2-DEMO-01",async()=>{var m=await SafeInitializer.SeedAsync(database,repo,definition,adminPassword,staffPassword,manifestPath,ct);Assert(m.Counts.Values.Sum()==20);});
    await Check("SQL-03","seed idempotency exact match",async()=>Assert((await SafeInitializer.SeedAsync(database,repo,definition,adminPassword,staffPassword,manifestPath,ct)).State=="SkippedExactMatch"));
    if(browser)
    {
        var runtime=Path.Combine(root,".tmp",ui?"ui-runtime":http?"http-runtime":"runtime");Directory.CreateDirectory(runtime);
        using var rsa=RSA.Create(2048);var request=new CertificateRequest("CN=localhost",rsa,HashAlgorithmName.SHA256,RSASignaturePadding.Pkcs1);
        var san=new SubjectAlternativeNameBuilder();san.AddDnsName("localhost");san.AddIpAddress(System.Net.IPAddress.Loopback);request.CertificateExtensions.Add(san.Build());
        request.CertificateExtensions.Add(new X509KeyUsageExtension(X509KeyUsageFlags.DigitalSignature|X509KeyUsageFlags.KeyEncipherment,true));
        using var cert=request.CreateSelfSigned(DateTimeOffset.UtcNow.AddMinutes(-5),DateTimeOffset.UtcNow.AddDays(7));
        var certPassword=Convert.ToHexString(RandomNumberGenerator.GetBytes(24));var certPath=Path.Combine(runtime,"server.pfx");await File.WriteAllBytesAsync(certPath,cert.Export(X509ContentType.Pfx,certPassword));
        await File.WriteAllTextAsync(Path.Combine(runtime,"profile.json"),JsonSerializer.Serialize(new{database=dbName,connectionString=options.ConnectionString,adminPassword,staffPassword,certificate=certPath,certificatePassword=certPassword,url=ui?"https://localhost:7445":http?"https://localhost:7444":"https://localhost:7443",keys=Path.Combine(runtime,"keys")},SafeInitializer.Json));
        Console.WriteLine("Owned browser fixture and private runtime profile created. Secrets omitted.");return 0;
    }
    await Check("SQL-04","5 tables 48 physical columns",async()=>
    {
        await using var u=await database.BeginAsync(false,ct);await SafeInitializer.RequireOwnerAsync(u,ct);
        await using var q=u.Command("SELECT COUNT(DISTINCT t.object_id),COUNT(*) FROM sys.tables t JOIN sys.columns c ON c.object_id=t.object_id WHERE t.is_ms_shipped=0;");await using var r=await q.ExecuteReaderAsync(ct);await r.ReadAsync(ct);Assert(r.GetInt32(0)==5&&r.GetInt32(1)==48);
    });
    await Check("AUTH-DEMO-01","password3/128 scalar boundaries retain original values",async()=>
    {
        foreach(var value in new[]{"123","😀12",new string('x',128)})Validation.Password(value);
        await Expect(4,()=>{Validation.Password("");return Task.CompletedTask;});
        foreach(var value in new[]{"1","12",new string('x',129),"\ud800"})
            await Expect(5,()=>{Validation.Password(value);return Task.CompletedTask;});
    });
    await Check("AUTH-DEMO-02","auth migration refuses foreign ownership without changes",async()=>
    {
        var before=await UserSnapshot(database,ct);
        await using(var u=await database.BeginAsync(true,ct))
        {await using var q=u.Command("EXEC sys.sp_updateextendedproperty @name=N'SP2Owner',@value=N'foreign-credential-fixture';");await q.ExecuteNonQueryAsync(ct);await u.CommitAsync(ct);}
        try
        {
            try{await DemoCredentialUpdater.ApplyAsync(database,repo,ct);throw new Exception("Expected ownership refusal");}
            catch(InvalidOperationException){}
            Assert(before==await UserSnapshot(database,ct));
        }
        finally
        {
            await using var u=await database.BeginAsync(true,ct);await using var q=u.Command("EXEC sys.sp_updateextendedproperty @name=N'SP2Owner',@value=@owner;",P.N("@owner",200,SafeInitializer.Owner));await q.ExecuteNonQueryAsync(ct);await u.CommitAsync(ct);
        }
    });
    var previousPassword=Convert.ToHexString(RandomNumberGenerator.GetBytes(24));
    await Check("AUTH-DEMO-03","login collision rolls back both accounts",async()=>
    {
        await using(var u=await database.BeginAsync(true,ct))
        {
            foreach(var value in definition.Users)
            {
                var user=(await repo.UserAsync(u,value[0],false,ct))!;var verifier=AuthService.CreateHasher().HashPassword(user,previousPassword);
                await using var q=u.Command("UPDATE dbo.m_app_user SET login_id=@login,password_verifier=@verifier,is_enabled=0,failed_count=5,locked_until=DATEADD(minute,15,SYSUTCDATETIME()) WHERE user_id=@id;",
                    P.V("@login",20,user.Role==UserRole.ADMIN?"demoadmin":"demostaff"),P.N("@verifier",2048,verifier),P.N("@id",40,user.UserId));await q.ExecuteNonQueryAsync(ct);
            }
            var other=new AppUser("OTHER1","staff","unrelated fixture","",UserRole.STAFF,true,0,null);
            await using(var q=u.Command("INSERT dbo.m_app_user(user_id,login_id,display_name,password_verifier,role_id,is_enabled,failed_count) VALUES(N'OTHER1','staff',N'unrelated fixture',@verifier,'STAFF',1,0);",P.N("@verifier",2048,AuthService.CreateHasher().HashPassword(other,previousPassword))))await q.ExecuteNonQueryAsync(ct);
            await u.CommitAsync(ct);
        }
        var before=await UserSnapshot(database,ct);
        try{await DemoCredentialUpdater.ApplyAsync(database,repo,ct);throw new Exception("Expected collision refusal");}
        catch(InvalidOperationException){}
        Assert(before==await UserSnapshot(database,ct));
        await using var update=await database.BeginAsync(true,ct);await using var rename=update.Command("UPDATE dbo.m_app_user SET login_id='otheruser' WHERE user_id=N'OTHER1';");await rename.ExecuteNonQueryAsync(ct);await update.CommitAsync(ct);
    });
    await Check("AUTH-DEMO-04","legacy DEMO auth-only migration preserves full business values",async()=>
    {
        var migration=await DemoCredentialUpdater.ApplyAsync(database,repo,ct);
        Assert(migration.State=="AppliedAuthOnly"&&migration.AccountsChanged==2&&migration.BusinessBefore.OrderBy(x=>x.Key).SequenceEqual(migration.BusinessAfter.OrderBy(x=>x.Key))&&migration.OtherUsersBefore==migration.OtherUsersAfter);
        var beforeRepeat=await UserSnapshot(database,ct);var repeat=await DemoCredentialUpdater.ApplyAsync(database,repo,ct);
        Assert(repeat.State=="SkippedExactMatch"&&repeat.AccountsChanged==0&&beforeRepeat==await UserSnapshot(database,ct));
        credentialMigrationEvidence=new{migration,repeatState=repeat.State,repeatAccountChanges=repeat.AccountsChanged,otherUserPreserved=true,collisionRefusalWithoutChanges=true,foreignOwnerRefusalWithoutChanges=true};
    });
    await Check("AUTH-DEMO-05","old login IDs and previous verifiers rejected after migration",async()=>
    {
        foreach(var login in new[]{"demoadmin","demostaff"})Assert(await auth.AuthenticateAsync(new(login,"123"),ct)is null);
        foreach(var login in new[]{"admin","staff"})
        {
            Assert(await auth.AuthenticateAsync(new(login,previousPassword),ct)is null);
            Assert(await auth.AuthenticateAsync(new(login,"123"),ct)is not null);
        }
    });
    await Check("AUTH-DEMO-06","IdentityV3 salted100000 verifiers retained for both DEMO users",async()=>
    {
        await using var u=await database.BeginAsync(false,ct);var salts=new List<string>();
        foreach(var id in new[]{"SP2ADMIN","SP2STAFF"})
        {
            var user=(await repo.UserAsync(u,id,false,ct))!;var encoded=Convert.FromBase64String(user.PasswordVerifier);
            Assert(encoded[0]==1&&System.Buffers.Binary.BinaryPrimitives.ReadUInt32BigEndian(encoded.AsSpan(5,4))==100000);
            var saltLength=checked((int)System.Buffers.Binary.BinaryPrimitives.ReadUInt32BigEndian(encoded.AsSpan(9,4)));Assert(saltLength>=16);
            salts.Add(Convert.ToHexString(encoded.AsSpan(13,saltLength)));
            Assert(AuthService.CreateHasher().VerifyHashedPassword(user,user.PasswordVerifier,"123")!=Microsoft.AspNetCore.Identity.PasswordVerificationResult.Failed);
        }
        Assert(salts.Distinct(StringComparer.Ordinal).Count()==2);
    });
    await Check("AUTH-DEMO-07","two-account writes roll back completely on BeforeCommit failure",async()=>
    {
        // Move only the owned test identities back to legacy IDs, requiring two writes.
        await using(var u=await database.BeginAsync(true,ct))
        {
            await using var q=u.Command("UPDATE dbo.m_app_user SET login_id=CASE user_id WHEN N'SP2ADMIN' THEN 'demoadmin' ELSE 'demostaff' END WHERE user_id IN(N'SP2ADMIN',N'SP2STAFF');");
            await q.ExecuteNonQueryAsync(ct);await u.CommitAsync(ct);
        }
        var before=await DatabaseSnapshot(database,ct);var faulty=new Database(options,new Faults{BeforeCommitFailure=true});
        try{await DemoCredentialUpdater.ApplyAsync(faulty,repo,ct);throw new Exception("Expected pre-commit failure");}
        catch(IOException){}
        Assert(before==await DatabaseSnapshot(database,ct));
        Assert((await DemoCredentialUpdater.ApplyAsync(database,repo,ct)).AccountsChanged==2);
    });
    Actor? admin=null,staff=null;
    await Check("AUTH-01","normal ADMIN STAFF current roles",async()=>{admin=await auth.AuthenticateAsync(new("admin",adminPassword),ct);staff=await auth.AuthenticateAsync(new("staff",staffPassword),ct);Assert(admin?.Role==UserRole.ADMIN&&staff?.Role==UserRole.STAFF);});
    if(admin is null||staff is null)throw new InvalidOperationException("Normal authentication failed.");
    var a=admin;var s=staff;
    await Check("F03-01","initial status default two ascending results",async()=>{var found=await employees.SearchAsync(s,new(null,null,null,"01"),ct);Assert(found.Rows.Select(x=>x.EmployeeNo).SequenceEqual(new[]{"000001","000002"}));});
    await Check("F03-02","all statuses and normalized name AND",async()=>{var found=await employees.SearchAsync(s,new(null,"ﾔﾏﾀﾞ　ﾀﾛｳ","01",null),ct);Assert(found.Rows.Count==1&&found.Rows[0].EmployeeNo=="000001");Assert((await employees.SearchAsync(s,new(null,null,null,null),ct)).Rows.Count==3);});
    await Check("F03-03","symbols are literal",async()=>Assert((await employees.SearchAsync(s,new(null,"%_*?[]",null,null),ct)).Rows.Count==0));
    var first=(await employees.SearchAsync(s,new("000001",null,null,null),ct)).Rows.Single().EmployeeId;
    var snapshot=(await employees.ReadAsync(s,first,ct)).Snapshot;
    await Check("F04-01","no change leaves version and audit intact",async()=>{var r=await employees.SaveAsync(s,snapshot,snapshot.Employee.Raw(),snapshot.Careers.Select(x=>x.Raw()).ToArray(),[],ct);var after=(await employees.ReadAsync(s,first,ct)).Snapshot;Assert(r.Outcome.MessageId=="MSG-021"&&after.Revision==snapshot.Revision&&after.UpdatedAt==snapshot.UpdatedAt);});
    await Check("F04-02","child-only update increments parent once",async()=>{var rows=snapshot.Careers.Select(x=>x.Raw()).ToArray();rows[0]=rows[0]with{Duties=rows[0].Duties+"確認"};var r=await employees.SaveAsync(s,snapshot,snapshot.Employee.Raw(),rows,[],ct);Assert(r.Revision==snapshot.Revision+1);});
    await Check("F04-03","stale no change conflicts before comparison",()=>Expect(8,()=>employees.SaveAsync(s,snapshot,snapshot.Employee.Raw(),snapshot.Careers.Select(x=>x.Raw()).ToArray(),[],ct)));
    snapshot=(await employees.ReadAsync(s,first,ct)).Snapshot;
    await Check("F04-04","missing child is not deletion",()=>Expect(25,()=>employees.SaveAsync(s,snapshot,snapshot.Employee.Raw(),snapshot.Careers.Skip(1).Select(x=>x.Raw()).ToArray(),[],ct)));
    await Check("F04-05","explicit child deletion preserves other ID",async()=>{var kept=snapshot.Careers[1];await employees.SaveAsync(s,snapshot,snapshot.Employee.Raw(),[kept.Raw()],[snapshot.Careers[0].CareerId!.Value],ct);var after=(await employees.ReadAsync(s,first,ct)).Snapshot;Assert(after.Careers.Count==1&&after.Careers[0].CareerId==kept.CareerId);});
    var fresh=definition.Employees[0]with{EmployeeNo="000004",Name="架空 新規"};
    SaveResult? inserted=null;
    await Check("F04-06","new employee with zero careers",async()=>{inserted=await employees.SaveAsync(s,null,fresh,[],[],ct);Assert(inserted.Revision==1);});
    await Check("F04-07","duplicate number atomically rejected",()=>Expect(6,()=>employees.SaveAsync(s,null,fresh,[],[],ct)));
    await Check("F05-01","zero careers refuses report",()=>Expect(12,()=>employees.ReportAsync(s,inserted!.EmployeeId,ct)));
    await Check("F06-01","STAFF cannot access code service",()=>Expect(3,()=>codes.ReadAsync(s,"DEPARTMENT",ct)));
    await Check("F06-02","ADMIN add / disable / preserve references",async()=>
    {
        var raw=new CodeSaveInput("",1,"DEPARTMENT","04","試験部署","4",true,null);await codes.SaveAsync(a,null,raw,false,ct);
        var row=(await codes.ReadAsync(a,"DEPARTMENT",ct)).Single(x=>x.Code=="04");await Expect(38,()=>codes.SaveAsync(a,row,raw with{Enabled=false,ExpectedRevision=row.Revision},false,ct));
        await codes.SaveAsync(a,row,raw with{Enabled=false,ExpectedRevision=row.Revision},true,ct);Assert(!(await codes.ReadAsync(a,"DEPARTMENT",ct)).Single(x=>x.Code=="04").Enabled);
    });
    await Check("F06-03","fixed employment rejects identical save",()=>Expect(23,()=>codes.SaveAsync(a,new("EMPLOYMENT_STATUS","01","在職",1,true,1),new("",1,"EMPLOYMENT_STATUS","01","在職","1",true,1),false,ct)));
    await Check("TEXT-01","Unicode scalar boundaries",()=>{Assert(Validation.ScalarLength(string.Concat(Enumerable.Repeat("😀",40)))==40);Validation.Text(string.Concat(Enumerable.Repeat("😀",40)),40,true,"x","x");return Expect(5,()=>{Validation.Text(string.Concat(Enumerable.Repeat("😀",41)),40,true,"x","x");return Task.CompletedTask;});});
    await Check("TEXT-02","raw vs normalized / LF / no business NFKC",()=>{Assert(Validation.Text("Ａ\r\nB\t",40,true,"x","x")=="Ａ\nB");return Expect(5,()=>{Validation.Text("\ud800",40,true,"x","x");return Task.CompletedTask;});});
    await Check("F05-02","ClosedXML exact apostrophes formula-looking values",()=>
    {
        string[] values=["000001","'ABC","''ABC","'=1+1","'","=1+1","+x","@x","-x","😀e\u0301\n二行"];
        using var book=new XLWorkbook();var ws=book.AddWorksheet("test");for(var i=0;i<values.Length;i++)ReportText.SetExact(ws.Cell(i+1,1),values[i]);
        using var stream=new MemoryStream();book.SaveAs(stream);stream.Position=0;using var read=new XLWorkbook(stream);for(var i=0;i<values.Length;i++)Assert(read.Worksheet(1).Cell(i+1,1).GetText()==values[i]&&!read.Worksheet(1).Cell(i+1,1).HasFormula);return Task.CompletedTask;
    });
    await Check("F05-03","real GDI two-sheet full workbook",async()=>
    {
        var report=await employees.ReportAsync(s,first,ct);using var stream=new ReportService(new GdiTextWidthMeasurer()).Create(report,ct);Assert(stream.Length>1000);
        var path=Path.Combine(root,".tmp","report-normal.xlsx");await File.WriteAllBytesAsync(path,stream.ToArray());
    });
    if(cycle>=2)
    {
        await Check("AUTH-02","fifth failure lock then no extension",async()=>
        {
            await using(var u=await database.BeginAsync(true,ct)){await repo.UpdateAuthAsync(u,"SP2STAFF",4,null,ct);await u.CommitAsync(ct);}
            Assert(await auth.AuthenticateAsync(new("staff",new string('x',16)),ct)is null);
            AppUser before;await using(var u=await database.BeginAsync(false,ct)){before=(await repo.UserAsync(u,"SP2STAFF",false,ct))!;}
            Assert(before.FailedCount==5&&before.LockedUntil>DateTimeOffset.UtcNow.AddMinutes(14));Assert(await auth.AuthenticateAsync(new("staff",staffPassword),ct)is null);
            await using(var u=await database.BeginAsync(true,ct)){var after=(await repo.UserAsync(u,"SP2STAFF",false,ct))!;Assert(after.LockedUntil==before.LockedUntil);await repo.UpdateAuthAsync(u,"SP2STAFF",0,null,ct);await u.CommitAsync(ct);}
        });
        await Check("STATE-01","exact idle 30 minute expiry",()=>
        {
            var time=new ManualTime(DateTimeOffset.UtcNow);var registry=new SessionRegistry(new(time));var id=registry.Create("u");time.Now=time.Now.AddMinutes(30).AddTicks(-1);Assert(registry.IsValid(id,"u"));time.Now=time.Now.AddTicks(1);Assert(!registry.IsValid(id,"u"));return Task.CompletedTask;
        });
        await Check("F04-08","20 children Unicode maximal aggregate",async()=>
        {
            var text=string.Concat(Enumerable.Repeat("😀",1000));var raw=definition.Employees[0]with{EmployeeNo="000005",CareerSummary=text,Skills=text,Qualifications=text,SelfPr=text};
            var careers=Enumerable.Range(0,20).Select(i=>new CareerRaw(null,Guid.NewGuid(),"2024-04",null,new string('会',100),"案件"+i,new string('概',1000),text,text,new string('技',500),new string('工',200),"01","999")).ToArray();
            var saved=await employees.SaveAsync(s,null,raw,careers,[],ct);var read=(await employees.ReadAsync(s,saved.EmployeeId,ct)).Snapshot;Assert(read.Careers.Count==20&&read.Employee.CareerSummary==text);
            using var stream=new ReportService(new GdiTextWidthMeasurer()).Create(await employees.ReportAsync(s,saved.EmployeeId,ct),ct);Assert(stream.Length<32*1024*1024);await File.WriteAllBytesAsync(Path.Combine(root,".tmp","report-maximum.xlsx"),stream.ToArray());
        });
        await Check("F04-09","21 careers rejected",()=>Expect(18,()=>employees.SaveAsync(s,null,definition.Employees[0]with{EmployeeNo="000006"},Enumerable.Range(0,21).Select(i=>CareerRaw.Empty()).ToArray(),[],ct)));
        await Check("F04-10","11-value duplicate / one different allowed",async()=>
        {
            var template=snapshot.Careers[0].Raw()with{CareerId=null,ClientRowKey=Guid.NewGuid()};
            await Expect(26,()=>employees.SaveAsync(s,null,definition.Employees[0]with{EmployeeNo="000006"},[template,template with{ClientRowKey=Guid.NewGuid()}],[],ct));
            await employees.SaveAsync(s,null,definition.Employees[0]with{EmployeeNo="000006"},[template,template with{ClientRowKey=Guid.NewGuid(),Duties=template.Duties+"差分"}],[],ct);
        });
        await Check("F04-11","known rollback vs lost commit acknowledgement",async()=>
        {
            var failBefore=new Faults{ChildFailure=true};var failedDb=new Database(options,failBefore);var svc=new EmployeeService(failedDb,repo,new(failedDb,repo,sessions),clock);
            var child=snapshot.Careers[0].Raw()with{CareerId=null,ClientRowKey=Guid.NewGuid()};await Expect(17,()=>svc.SaveAsync(s,null,definition.Employees[0]with{EmployeeNo="000007"},[child],[],ct));Assert((await employees.SearchAsync(s,new("000007",null,null,null),ct)).Rows.Count==0);
            var lost=new Faults{AfterCommitFailure=true};var lostDb=new Database(options,lost);var lostSvc=new EmployeeService(lostDb,repo,new(lostDb,repo,sessions),clock);
            await Expect(34,()=>lostSvc.SaveAsync(s,null,definition.Employees[0]with{EmployeeNo="000008"},[],[],ct));Assert((await employees.SearchAsync(s,new("000008",null,null,null),ct)).Rows.Count==1);
        });
        await Check("F04-12","rollback confirmation failure remains Unknown",async()=>
        {
            var faults=new Faults{ChildFailure=true,RollbackFailure=true};var faultDb=new Database(options,faults);var svc=new EmployeeService(faultDb,repo,new(faultDb,repo,sessions),clock);
            var child=snapshot.Careers[0].Raw()with{CareerId=null,ClientRowKey=Guid.NewGuid()};await Expect(34,()=>svc.SaveAsync(s,null,definition.Employees[0]with{EmployeeNo="000009"},[child],[],ct));
        });
        await Check("F04-13","two independent connections same employee number",async()=>
        {
            var raw=definition.Employees[0]with{EmployeeNo="000010"};var work=await Task.WhenAll(Enumerable.Range(0,2).Select(async _=>{try{await employees.SaveAsync(s,null,raw,[],[],ct);return "saved";}catch(BusinessException b){return b.Outcome.MessageId;}}));Assert(work.Count(x=>x=="saved")==1&&work.Count(x=>x=="MSG-006")==1);
        });
        await Check("F04-14","10-second exclusive gate timeout",async()=>
        {
            await using var held=await database.BeginAsync(true,ct);var sw=Stopwatch.StartNew();await Expect(27,()=>employees.SaveAsync(s,null,definition.Employees[0]with{EmployeeNo="000011"},[],[],ct));Assert(sw.Elapsed.TotalSeconds>=9&&sw.Elapsed.TotalSeconds<20);
        });
        await Check("SEED-04","changed seed data stops without mutation",async()=>
        {
            try{await SafeInitializer.SeedAsync(database,repo,definition,adminPassword,staffPassword,manifestPath,ct);throw new Exception("Expected refusal");}catch(InvalidOperationException){}Assert((await employees.SearchAsync(s,new("000010",null,null,null),ct)).Rows.Count==1);
        });
        await Check("AUTH-03","lock exact deadline and concurrent increments",async()=>
        {
            var deadline=DateTimeOffset.UtcNow;await using(var u=await database.BeginAsync(true,ct)){await repo.UpdateAuthAsync(u,"SP2STAFF",5,deadline,ct);await u.CommitAsync(ct);}
            var time=new ManualTime(deadline.AddTicks(-1));var registry=new SessionRegistry(new(time));var verifier=new AuthService(database,repo,new(time),registry);
            Assert(await verifier.AuthenticateAsync(new("staff",staffPassword),ct)is null);time.Now=deadline;Assert(await verifier.AuthenticateAsync(new("staff",staffPassword),ct)is not null);
            await using(var u=await database.BeginAsync(true,ct)){await repo.UpdateAuthAsync(u,"SP2STAFF",3,null,ct);await u.CommitAsync(ct);}
            var denied=await Task.WhenAll(Enumerable.Range(0,2).Select(_=>auth.AuthenticateAsync(new("staff",new string('x',16)),ct)));Assert(denied.All(x=>x is null));
            await using(var u=await database.BeginAsync(true,ct)){var user=(await repo.UserAsync(u,"SP2STAFF",false,ct))!;Assert(user.FailedCount==5);await repo.UpdateAuthAsync(u,"SP2STAFF",0,null,ct);await u.CommitAsync(ct);}
        });
        await Check("F04-15","editable invalid business value vs report corruption",async()=>
        {
            await using(var u=await database.BeginAsync(true,ct)){await using var q=u.Command("UPDATE dbo.m_employee SET employee_name=N'' WHERE employee_id=@id;",P.L("@id",first));await q.ExecuteNonQueryAsync(ct);await u.CommitAsync(ct);}
            var corrupt=(await employees.ReadAsync(s,first,ct)).Snapshot;Assert(corrupt.Employee.Name=="");await Expect(20,()=>employees.ReportAsync(s,first,ct));
            await employees.SaveAsync(s,corrupt,corrupt.Employee.Raw()with{Name="訂正済み 架空"},corrupt.Careers.Select(x=>x.Raw()).ToArray(),[],ct);
            Assert((await employees.ReadAsync(s,first,ct)).Snapshot.Employee.Name=="訂正済み 架空");
        });
        await Check("F04-16","stopped role retained only by original row",async()=>
        {
            var old=(await employees.ReadAsync(s,first,ct)).Snapshot;var role=(await codes.ReadAsync(a,"PROJECT_ROLE",ct)).Single(x=>x.Code==old.Careers[0].Values.RoleCode);
            await codes.SaveAsync(a,role,new("",1,role.Category,role.Code,role.Name,role.SortOrder.ToString(System.Globalization.CultureInfo.InvariantCulture),false,role.Revision),true,ct);
            var keep=old.Careers.Select(x=>x.Raw()).ToArray();keep[0]=keep[0]with{Duties=keep[0].Duties+"停止保持"};await employees.SaveAsync(s,old,old.Employee.Raw(),keep,[],ct);
            var updated=(await employees.ReadAsync(s,first,ct)).Snapshot;await Expect(16,()=>employees.SaveAsync(s,updated,updated.Employee.Raw(),[..updated.Careers.Select(x=>x.Raw()),updated.Careers[0].Raw()with{CareerId=null,ClientRowKey=Guid.NewGuid(),Duties="新規割当"}],[],ct));
        });
        await Check("F03-04","literal positive / no TOP before managed name filter",async()=>
        {
            await employees.SaveAsync(s,null,definition.Employees[0]with{EmployeeNo="000012",Name="%_*?[]"},[],[],ct);
            Assert((await employees.SearchAsync(s,new(null,"%_*?[]","01","01"),ct)).Rows.Count==1);
        });
        await Check("F06-04","99 codes include stopped / invalid100 / duplicate",async()=>
        {
            var rows=await codes.ReadAsync(a,"DEPARTMENT",ct);
            await using(var u=await database.BeginAsync(true,ct))
            {
                for(var i=1;i<=99;i++)if(!rows.Any(x=>x.Code==$"{i:00}"))await repo.WriteCodeAsync(u,new("DEPARTMENT",$"{i:00}","架空部署"+i,(short)i,true),null,a.UserId,DateTimeOffset.UtcNow,ct);
                await u.CommitAsync(ct);
            }
            Assert((await codes.ReadAsync(a,"DEPARTMENT",ct)).Count==99);
            await Expect(5,()=>codes.SaveAsync(a,null,new("",1,"DEPARTMENT","100","x","1",true,null),false,ct));
            await Expect(22,()=>codes.SaveAsync(a,null,new("",1,"DEPARTMENT","99","x","1",true,null),false,ct));
        });
        await Check("SEC-01","DB application role denies parent delete and DDL",async()=>
        {
            await using var connection=new SqlConnection(options.ConnectionString);await connection.OpenAsync(ct);
            await using(var permissions=new SqlCommand(await File.ReadAllTextAsync(Path.Combine(root,"database","application-permissions.sql")),connection))await permissions.ExecuteNonQueryAsync(ct);
            await using(var user=new SqlCommand("CREATE USER SP2FixtureWeb WITHOUT LOGIN; ALTER ROLE SP2_Career_App ADD MEMBER SP2FixtureWeb;",connection))await user.ExecuteNonQueryAsync(ct);
            foreach(var statement in new[]{"DELETE dbo.m_employee WHERE employee_id=-1;","DELETE dbo.m_app_user WHERE user_id=N'NONEXISTENT';","DELETE dbo.m_code WHERE code='00';","DELETE dbo.m_code_category WHERE category_id='NONE';","CREATE TABLE dbo.ForbiddenDDL(x int);","UPDATE dbo.m_app_user SET role_id='ADMIN' WHERE user_id=N'NONEXISTENT';"})
            {
                try{await using var q=new SqlCommand("EXECUTE AS USER=N'SP2FixtureWeb'; BEGIN TRY "+statement+" REVERT; END TRY BEGIN CATCH REVERT; THROW; END CATCH;",connection);await q.ExecuteNonQueryAsync(ct);throw new InvalidOperationException("Permission unexpectedly granted.");}
                catch(SqlException ex)when(ex.Number is 229 or 230 or 262 or 2760){}
            }
            await using var allowed=new SqlCommand("EXECUTE AS USER=N'SP2FixtureWeb'; DELETE dbo.t_career WHERE career_id=-1; REVERT;",connection);Assert(await allowed.ExecuteNonQueryAsync(ct)==0);
        });
        await Check("F04-17","199 to 200 race and 201st search refusal",async()=>
        {
            await using(var u=await database.BeginAsync(true,ct))
            {
                var count=await repo.EmployeeCountAsync(u,ct);
                for(var i=count;i<199;i++)await repo.InsertEmployeeAsync(u,Validation.Employee(definition.Employees[0]with{EmployeeNo=$"{900000+i:000000}",Name="上限確認 架空"},clock.Begin().Date),a.UserId,DateTimeOffset.UtcNow,ct);
                await u.CommitAsync(ct);
            }
            var race=await Task.WhenAll(new[]{"800001","800002"}.Select(async no=>{try{await employees.SaveAsync(s,null,definition.Employees[0]with{EmployeeNo=no},[],[],ct);return "saved";}catch(BusinessException ex){return ex.Outcome.MessageId;}}));Assert(race.Count(x=>x=="saved")==1&&race.Count(x=>x=="MSG-018")==1);
            Assert((await employees.SearchAsync(s,new(null,null,null,null),ct)).Rows.Count==200);
            await using(var u=await database.BeginAsync(true,ct)){await repo.InsertEmployeeAsync(u,Validation.Employee(definition.Employees[0]with{EmployeeNo="999999",Name="最終候補 専用"},clock.Begin().Date),a.UserId,DateTimeOffset.UtcNow,ct);await u.CommitAsync(ct);}
            await Expect(10,()=>employees.SearchAsync(s,new(null,null,null,null),ct));Assert((await employees.SearchAsync(s,new(null,"最終候補",null,null),ct)).Rows.Single().EmployeeNo=="999999");
        });
    }
}
catch(Exception ex){failed++;results.Add(new{id="HARNESS",status="FAIL",error=ex.GetType().Name,detail=ex.Message});Console.WriteLine("FAIL HARNESS "+ex.GetType().Name);}
finally
{
    if(created&&!browser)
    {
        try
        {
            await using(var u=await database.BeginAsync(false,ct))await SafeInitializer.RequireOwnerAsync(u,ct);
            SqlConnection.ClearAllPools();var b=new SqlConnectionStringBuilder(options.ConnectionString){InitialCatalog="master"};await using var master=new SqlConnection(b.ConnectionString);await master.OpenAsync(ct);
            if(!dbName.StartsWith("SP2_WebFixture_Test_",StringComparison.Ordinal))throw new InvalidOperationException("Cleanup scope violation.");
            await using var drop=new SqlCommand("ALTER DATABASE ["+dbName+"] SET SINGLE_USER WITH ROLLBACK IMMEDIATE; DROP DATABASE ["+dbName+"];",master);await drop.ExecuteNonQueryAsync(ct);
        }
        catch(Exception ex){failed++;results.Add(new{id="CLEANUP",status="FAIL",error=ex.GetType().Name});}
    }
    if(!browser)
    {
        var dir=Path.Combine(root,"build","test-results");Directory.CreateDirectory(dir);
        await File.WriteAllTextAsync(Path.Combine(dir,$"self-cycle-{cycle}.json"),JsonSerializer.Serialize(new{projectId="sample-project2",methodId="CSharp_ASPNET",runId=currentRunId,inputManifestSha256,testedRuntimeArtifacts,cycle,executedUtc=DateTimeOffset.UtcNow,dbEngine="SQL Server 2025 Express (17.0), compatibility 160; SQL Server 2022 host untested",passed=failed==0,failed,tests=results,credentialMigrationEvidence,unperformed=new[]{"formal acceptance","SQL Server 2022 physical host","real Excel print","browser (root independent)"}},SafeInitializer.Json));
    }
}
return failed==0?0:1;
static async Task<string> UserSnapshot(Database database,CancellationToken ct)
{
    await using var u=await database.BeginAsync(false,ct);await using var q=u.Command("SELECT * FROM dbo.m_app_user ORDER BY user_id FOR JSON PATH,INCLUDE_NULL_VALUES;");
    var value=new StringBuilder();await using var r=await q.ExecuteReaderAsync(ct);while(await r.ReadAsync(ct))value.Append(r.GetString(0));return value.ToString();
}
static async Task<string> DatabaseSnapshot(Database database,CancellationToken ct)
{
    (string Table,string Order)[] tables=[("m_app_user","user_id"),("m_code_category","category_id"),("m_code","category_id,code"),("m_employee","employee_id"),("t_career","career_id")];
    await using var u=await database.BeginAsync(false,ct);var value=new StringBuilder();
    foreach(var table in tables)
    {
        value.Append(table.Table);await using var q=u.Command($"SELECT * FROM dbo.{table.Table} ORDER BY {table.Order} FOR JSON PATH,INCLUDE_NULL_VALUES;");
        await using var r=await q.ExecuteReaderAsync(ct);while(await r.ReadAsync(ct))value.Append(r.GetString(0));
    }
    return value.ToString();
}
sealed class ManualTime(DateTimeOffset value):TimeProvider{public DateTimeOffset Now{get;set;}=value;public override DateTimeOffset GetUtcNow()=>Now;}
sealed class Faults:IDbFaults
{
    public bool ChildFailure{get;init;}public bool AfterCommitFailure{get;init;}public bool RollbackFailure{get;init;}public bool BeforeCommitFailure{get;init;}
    public void BeforeChildWrite(){if(ChildFailure)throw new IOException("Test child fault.");}public void BeforeCommit(){if(BeforeCommitFailure)throw new IOException("Test pre-commit fault.");}public void BeforeRead(){}
    public void AfterCommit(){if(AfterCommitFailure)throw new IOException("Test acknowledgement loss.");}
    public void BeforeRollback(){if(RollbackFailure)throw new IOException("Test rollback confirmation loss.");}
}
