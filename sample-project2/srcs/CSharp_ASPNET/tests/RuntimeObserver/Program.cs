using System.Diagnostics;
using System.Reflection;
using System.Runtime.Loader;
using System.Security.Cryptography;
using System.Text.Json;
using System.Text.Json.Serialization;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Hosting;

// Test-only host observer. The application is the unchanged final publish assembly.
// Only Hosting diagnostics and read-only, Gate-protected snapshots cross this IPC boundary.
if(args.Length!=1)throw new ArgumentException("Exact publish directory argument required.");
var publish=Path.GetFullPath(args[0]);
var sourceRoot=Directory.GetParent(Directory.GetParent(publish)!.FullName)!.FullName;
if(publish!=Path.Combine(sourceRoot,"build","publish")||Environment.GetEnvironmentVariable("SP2_DATABASE")!="SP2_WebFixture_ADDITIONAL_R20261030"||Environment.GetEnvironmentVariable("ASPNETCORE_URLS")!="https://localhost:5184")throw new InvalidOperationException("Observer is restricted to the new author fixture.");
var web=Path.Combine(publish,"CareerManagement.Web.dll");
var resolver=new AssemblyDependencyResolver(web);
AssemblyLoadContext.Default.Resolving+=(_,name)=>resolver.ResolveAssemblyToPath(name)is string file?AssemblyLoadContext.Default.LoadFromAssemblyPath(file):null;
AssemblyLoadContext.Default.ResolvingUnmanagedDll+=(_,name)=>resolver.ResolveUnmanagedDllToPath(name)is string file?System.Runtime.InteropServices.NativeLibrary.Load(file):IntPtr.Zero;
var infrastructure=AssemblyLoadContext.Default.LoadFromAssemblyPath(Path.Combine(publish,"CareerManagement.Infrastructure.dll"));
var storeType=infrastructure.GetType("CareerManagement.Infrastructure.State.ScreenStateStore",true)!;
var ready=new TaskCompletionSource<IHost>(TaskCreationOptions.RunContinuationsAsynchronously);
var sqlCounters=new SqlCounters();
using var subscription=DiagnosticListener.AllListeners.Subscribe(new Listener(ready,storeType,sqlCounters));
var application=AssemblyLoadContext.Default.LoadFromAssemblyPath(web);
var applicationTask=Task.Run(async()=>{var result=application.EntryPoint!.Invoke(null,[new[]{"--contentRoot",publish,"--applicationName","CareerManagement.Web"}]);if(result is Task task)await task;});
var host=await ready.Task.WaitAsync(TimeSpan.FromSeconds(30));
var store=host.Services.GetRequiredService(storeType);
var states=storeType.GetField("states",BindingFlags.Instance|BindingFlags.NonPublic)!.GetValue(store)!;
var options=new JsonSerializerOptions(JsonSerializerDefaults.Web);options.Converters.Add(new JsonStringEnumConverter());
void Emit(object value)=>Console.WriteLine("OBSERVER:"+JsonSerializer.Serialize(value,options));
Emit(new{kind="ready",pid=Environment.ProcessId,productFile=web,productSha256=Convert.ToHexStringLower(SHA256.HashData(File.ReadAllBytes(web))),url="https://localhost:5184",database="SP2_WebFixture_ADDITIONAL_R20261030"});
try
{
    while(await Console.In.ReadLineAsync() is string line)
    {
        try
        {
            using var request=JsonDocument.Parse(line);var command=request.RootElement.GetProperty("command").GetString();
            if(command=="stop"){host.Services.GetRequiredService<IHostApplicationLifetime>().StopApplication();Emit(new{kind="stopping"});break;}
            if(command=="sqlCounters"){Emit(new{kind="sqlCounters",snapshot=sqlCounters.Snapshot()});continue;}
            if(command!="snapshot")throw new ArgumentException("Read-only snapshot or stop only.");
            var id=request.RootElement.GetProperty("stateId").GetString();
            if(id is null||id.Length!=64||id.Any(c=>!char.IsAsciiHexDigit(c)))throw new ArgumentException("Exact state identity required.");
            object?[] lookup=[id,null];var found=(bool)states.GetType().GetMethod("TryGetValue")!.Invoke(states,lookup)!;
            if(!found){Emit(new{kind="snapshot",stateId=id,found=false});continue;}
            var state=lookup[1]!;var gate=(SemaphoreSlim)state.GetType().GetProperty("Gate")!.GetValue(state)!;
            if(!await gate.WaitAsync(TimeSpan.FromSeconds(5)))throw new TimeoutException("State snapshot Gate was busy.");
            try
            {
                var fields=new SortedDictionary<string,JsonElement>(StringComparer.Ordinal);
                foreach(var property in state.GetType().GetProperties(BindingFlags.Public|BindingFlags.Instance).Where(p=>p.Name!="Gate"&&p.GetIndexParameters().Length==0))
                {
                    var value=property.GetValue(state);
                    if(property.Name=="OwnerSessionId"&&value is string owner)value=Convert.ToHexStringLower(SHA256.HashData(System.Text.Encoding.UTF8.GetBytes(owner)));
                    fields[property.Name]=JsonSerializer.SerializeToElement(value,value?.GetType()??typeof(object),options);
                }
                var bytes=JsonSerializer.SerializeToUtf8Bytes(fields,options);
                Emit(new{kind="snapshot",stateId=id,found=true,stateType=state.GetType().Name,fields,sha256=Convert.ToHexStringLower(SHA256.HashData(bytes)),readOnly=true});
            }
            finally{gate.Release();}
        }
        catch(Exception error){Emit(new{kind="error",error=error.GetType().Name,message=error.Message});}
    }
}
finally{host.Services.GetRequiredService<IHostApplicationLifetime>().StopApplication();}
await applicationTask.WaitAsync(TimeSpan.FromSeconds(15));

sealed class Listener(TaskCompletionSource<IHost> ready,Type store,SqlCounters counters):IObserver<DiagnosticListener>
{
    public void OnNext(DiagnosticListener listener){if(listener.Name=="Microsoft.Extensions.Hosting")listener.Subscribe(new Events(ready,store));if(listener.Name=="SqlClientDiagnosticListener"){counters.AddListener();listener.Subscribe(counters);}}
    public void OnError(Exception error){}
    public void OnCompleted(){}
}
sealed class SqlCounters:IObserver<KeyValuePair<string,object?>>
{
    private readonly object gate=new();private long before,after,errors,callbacks,failures,listeners;
    private readonly List<object> searchEvents=[];
    public void AddListener(){lock(gate)listeners++;}
    public object Snapshot(){lock(gate)return new{listenerCount=listeners,commandCallbacks=callbacks,callbackFailures=failures,searchBefore=before,searchAfter=after,searchError=errors,events=searchEvents.ToArray()};}
    public void OnNext(KeyValuePair<string,object?> item)
    {
        try
        {
            if(item.Value?.GetType().GetProperty("Command")?.GetValue(item.Value)is not System.Data.Common.DbCommand command)return;
            if(command.Connection?.Database!="SP2_WebFixture_ADDITIONAL_R20261030")return;
            lock(gate)
            {
                callbacks++;
                var text=command.CommandText;
                if(!text.Contains("SELECT e.employee_id,e.employee_no",StringComparison.Ordinal)||!text.Contains("ORDER BY e.employee_no;",StringComparison.Ordinal))return;
                if(item.Key.EndsWith("WriteCommandBefore",StringComparison.Ordinal))before++;
                else if(item.Key.EndsWith("WriteCommandAfter",StringComparison.Ordinal))after++;
                else if(item.Key.EndsWith("WriteCommandError",StringComparison.Ordinal))errors++;
                else return;
                searchEvents.Add(new{eventName=item.Key,database=command.Connection.Database,commandFingerprintSha256=Convert.ToHexStringLower(SHA256.HashData(System.Text.Encoding.UTF8.GetBytes(text))),observedAtUtc=DateTimeOffset.UtcNow});
            }
        }
        catch{lock(gate)failures++;}
    }
    public void OnError(Exception error){lock(gate)failures++;}
    public void OnCompleted(){}
}
sealed class Events(TaskCompletionSource<IHost> ready,Type store):IObserver<KeyValuePair<string,object?>>
{
    public void OnNext(KeyValuePair<string,object?> item){if(item.Key=="HostBuilt"&&item.Value is IHost host&&host.Services.GetService(store)is not null)ready.TrySetResult(host);}
    public void OnError(Exception error){}
    public void OnCompleted(){}
}
