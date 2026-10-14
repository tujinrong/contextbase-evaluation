using StudentManagement.Web;
var builder=WebApplication.CreateBuilder(args);
WebHostSetup.Add(builder);
var app=builder.Build();
WebHostSetup.Use(app);
app.MapControllers();
app.MapGet("/",()=>Results.Redirect("/students"));
app.Run();
public partial class Program { }
