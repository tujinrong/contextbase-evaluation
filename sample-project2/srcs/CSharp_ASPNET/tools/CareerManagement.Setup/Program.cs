using System.Text;
using System.Text.Json;
using CareerManagement.Infrastructure.Sql;

Console.OutputEncoding=Encoding.UTF8;
try
{
    if(args.Length!=2||args[0]is not("create" or "seed"))throw new InvalidOperationException("Usage: CareerManagement.Setup create|seed <exact-database-name>. Connection is supplied through SP2_CONNECTION_STRING; no password arguments.");
    var name=args[1];var fixture=name.StartsWith("SP2_WebFixture_",StringComparison.Ordinal);
    var connection=Environment.GetEnvironmentVariable("SP2_CONNECTION_STRING")??throw new InvalidOperationException("SP2_CONNECTION_STRING is required.");
    var options=new DatabaseOptions{ConnectionString=connection,AllowedDatabase=name,Fixture=fixture};options.Validate();
    if(args[0]=="create")
    {
        await SafeInitializer.CreateAsync(options,await File.ReadAllTextAsync(Path.Combine(AppContext.BaseDirectory,"schema.sql")),CancellationToken.None);
        Console.WriteLine("Created a new owned database with 5 tables / 48 columns. No credentials or data were added.");
    }
    else
    {
        var admin=ReadTwice("管理者");var staff=ReadTwice("担当者");
        var dataset=JsonSerializer.Deserialize<SeedDefinition>(await File.ReadAllTextAsync(Path.Combine(AppContext.BaseDirectory,"SP2-DEMO-01.json")),SafeInitializer.Json)??throw new InvalidOperationException("Invalid dataset.");
        var manifest=Path.Combine(Environment.CurrentDirectory,"build","generation","seed-manifest.json");
        var result=await SafeInitializer.SeedAsync(new(options,new NoDbFaults()),new(),dataset,admin,staff,manifest,CancellationToken.None);
        Console.WriteLine($"{result.DatasetId} {result.State}: categories=3 codes=9 users=2 employees=3 careers=3");
    }
    return 0;
}
catch(Exception ex) when(ex is not OutOfMemoryException)
{Console.Error.WriteLine("Setup refused or failed: "+(ex is InvalidOperationException?ex.Message:ex.GetType().Name)+". Existing data is not overwritten.");return 1;}

static string ReadTwice(string label)
{
    if(Console.IsInputRedirected)throw new InvalidOperationException("Interactive non-echo password entry is required.");
    Console.Write(label+" 初期パスワード（12～128スカラー）: ");var first=ReadHidden();
    Console.Write(label+" 確認: ");var second=ReadHidden();
    CareerManagement.Application.Validation.Password(first);
    if(first!=second)throw new InvalidOperationException("Password confirmation does not match.");return first;
}
static string ReadHidden()
{
    var text=new StringBuilder();while(true){var key=Console.ReadKey(true);if(key.Key==ConsoleKey.Enter){Console.WriteLine();return text.ToString();}if(key.Key==ConsoleKey.Backspace){if(text.Length>0)text.Length--;}else if(!char.IsControl(key.KeyChar))text.Append(key.KeyChar);}
}
