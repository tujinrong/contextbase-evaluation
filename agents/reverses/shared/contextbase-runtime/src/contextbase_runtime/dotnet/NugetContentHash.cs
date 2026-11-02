// Read package archives as data using the installed SDK's NuGet implementation.
// Content hashes identify package bytes; this does not authenticate a publisher.
using System;
using System.Collections.Generic;
using System.Text;
using System.Text.Json;
using System.Threading;
using NuGet.Packaging;

static class NugetContentHash
{
    public static void Main()
    {
        Console.InputEncoding = new UTF8Encoding(false);
        Console.OutputEncoding = new UTF8Encoding(false);
        var paths = JsonSerializer.Deserialize<string[]>(Console.In.ReadToEnd())!;
        var hashes = new Dictionary<string, string>();
        foreach (var path in paths)
        {
            using var archive = new PackageArchiveReader(path);
            hashes.Add(path, archive.GetContentHash(CancellationToken.None));
        }
        Console.Write(JsonSerializer.Serialize(hashes));
    }
}
