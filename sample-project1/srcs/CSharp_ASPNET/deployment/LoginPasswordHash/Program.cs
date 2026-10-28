using Microsoft.AspNetCore.Identity;
using Microsoft.Extensions.Options;

if (args.Length != 1) throw new ArgumentException("Provide the output hash file path.");
var password = Environment.GetEnvironmentVariable("CB_WEB_LOGIN_PASSWORD") ?? throw new InvalidOperationException("Password environment variable is required.");
if (password.Length < 20 || password.Length > 128) throw new InvalidOperationException("Use a generated deployment password between 20 and 128 characters.");
var hasher = new PasswordHasher<string>(Options.Create(new PasswordHasherOptions { IterationCount = 210000 }));
File.WriteAllText(args[0], hasher.HashPassword("admin", password));
Console.WriteLine("Login password hash created; plaintext password was not written to the hash file.");
