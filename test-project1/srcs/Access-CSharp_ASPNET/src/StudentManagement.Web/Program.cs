using Microsoft.AspNetCore.Http.Features;
using Microsoft.AspNetCore.Mvc;
using StudentManagement.Core;
using StudentManagement.Web.Infrastructure;

var builder = WebApplication.CreateBuilder(args);
var provider = builder.Configuration["Storage:Provider"] ?? "SqlServer";
var verification = builder.Environment.IsEnvironment("Verification");
if (provider is not ("SqlServer" or "VerificationMemory")) throw new InvalidOperationException("Unknown Storage:Provider.");
if (provider == "VerificationMemory" && !verification) throw new InvalidOperationException("VerificationMemory requires the Verification environment.");

builder.Services.AddSingleton<IStudentRepository>(_ => provider == "VerificationMemory"
    ? InMemoryStudentRepository.CreateVerification(builder.Configuration["Verification:ApprovedMastersPath"] ??
        Path.GetFullPath(Path.Combine(builder.Environment.ContentRootPath, "../../database/seed/approved-masters.json")))
    : new SqlStudentRepository(builder.Configuration.GetConnectionString("StudentManagement") ?? ""));
builder.Services.AddSingleton(sp => new StudentService(sp.GetRequiredService<IStudentRepository>()));
builder.Services.AddSingleton<ConfirmationStore>();
builder.Services.AddSingleton<EditorSnapshotStore>();
builder.Services.AddScoped<ActorFilter>();
builder.Services.AddControllersWithViews(options =>
{
    options.Filters.Add(new AutoValidateAntiforgeryTokenAttribute());
    options.Filters.AddService<ActorFilter>();
});
builder.Services.AddDistributedMemoryCache();
builder.Services.AddSession(options =>
{
    options.Cookie.Name = "AccessRebuilder.Session";
    options.Cookie.HttpOnly = true;
    options.Cookie.SameSite = SameSiteMode.Strict;
    options.Cookie.IsEssential = true;
    options.IdleTimeout = TimeSpan.FromMinutes(30);
});
builder.Services.Configure<FormOptions>(options =>
{
    options.ValueCountLimit = 100;
    options.ValueLengthLimit = 16_384;
    options.MultipartBodyLengthLimit = 65_536;
});

var app = builder.Build();
app.UseExceptionHandler("/System/Error");
app.UseStaticFiles();
app.UseRouting();
app.UseSession();
app.MapGet("/health", () => Results.Ok(new { status = "running", provider, verification, databaseConnectionTested = false }));
app.MapControllerRoute("default", "{controller=Students}/{action=Index}/{id?}");
app.Run();

public partial class Program;
