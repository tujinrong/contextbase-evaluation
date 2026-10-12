using StudentManagement.Web;
var builder=WebApplication.CreateBuilder(args);
WebHostSetup.Add(builder);
var app=builder.Build();
WebHostSetup.Use(app);
app.MapControllers();
// API paths stay JSON/404 and never fall through to index.html.
app.MapFallback("/api/{**path}",()=>Results.Json(WebPresentation.Error("notFound","APIが見つかりません。"),statusCode:404));
app.MapFallbackToFile("index.html");
app.Run();
public partial class Program { }
