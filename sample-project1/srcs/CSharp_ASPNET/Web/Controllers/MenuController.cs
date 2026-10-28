using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;

namespace StudentManagement.Web;

[Authorize]
public sealed class MenuController : Controller
{
    [HttpGet("/menu")]
    public IActionResult Index() => View();
}
