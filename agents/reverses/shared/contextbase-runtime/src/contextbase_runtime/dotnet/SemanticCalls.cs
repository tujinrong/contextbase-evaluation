// Trusted source-only compiler front end. No target Emit, build, scripts or plugins.
using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Text.Json;
using Microsoft.CodeAnalysis;
using Microsoft.CodeAnalysis.CSharp;
using Microsoft.CodeAnalysis.CSharp.Syntax;
using Microsoft.CodeAnalysis.Operations;

static class SemanticCalls
{
    static readonly JsonSerializerOptions Json = new() { PropertyNamingPolicy = JsonNamingPolicy.CamelCase };
    sealed record FileInput(string Path, string Text);
    sealed record ProjectInput(string Id, FileInput[] Files, string[] References, string[] ProjectReferences,
        string LanguageVersion, string[] Defines, string Nullable, string[] GlobalUsings, bool ConfigurationComplete,
        string? AssemblyName = null, string? OutputKind = null);
    sealed record Request(ProjectInput[] Projects, string RootProject);
    static readonly Dictionary<string, CSharpCompilation> Compilations = new();
    static readonly HashSet<string> Building = new();
    static Request Input = null!;

    static int Byte(SyntaxTree tree, int offset) => Encoding.UTF8.GetByteCount(tree.GetText().ToString().AsSpan(0, offset));
    static object Span(SyntaxReference reference) => new { path = reference.SyntaxTree.FilePath,
        startByte = Byte(reference.SyntaxTree, reference.Span.Start), endByte = Byte(reference.SyntaxTree, reference.Span.End) };
    static ISymbol Normalize(ISymbol symbol) => symbol is IMethodSymbol m ? (m.ReducedFrom ?? m).OriginalDefinition : symbol.OriginalDefinition;
    static string DefinitionKey(ISymbol symbol)
    {
        symbol = Normalize(symbol);
        var identity = symbol.GetDocumentationCommentId() ?? symbol.ToDisplayString() + ":" +
            string.Join(";", symbol.DeclaringSyntaxReferences.Select(r => r.SyntaxTree.FilePath + ":" + Byte(r.SyntaxTree, r.Span.Start) + ":" + Byte(r.SyntaxTree, r.Span.End)));
        return symbol.ContainingAssembly?.Identity.ToString() + ":" + identity;
    }
    static string SymbolKey(ISymbol symbol) => DefinitionKey(symbol) + "|bound:" + symbol.ToDisplayString(
        symbol is ITypeSymbol ? SymbolDisplayFormat.FullyQualifiedFormat : SymbolDisplayFormat.CSharpErrorMessageFormat);
    static object Target(ISymbol value)
    {
        var symbol = value;
        var refs = Normalize(symbol).DeclaringSyntaxReferences;
        return new { key = SymbolKey(symbol), definitionKey = DefinitionKey(symbol),
            containingTypeKey = symbol is IMethodSymbol methodSymbol ? SymbolKey(methodSymbol.ContainingType) : null,
            name = symbol.Name,
            qualifiedName = symbol.ContainingSymbol is INamespaceSymbol ns && ns.IsGlobalNamespace ? symbol.Name :
                symbol.ContainingSymbol?.ToDisplayString() + "." + symbol.Name,
            signature = symbol.ToDisplayString(SymbolDisplayFormat.CSharpErrorMessageFormat),
            assembly = symbol.ContainingAssembly?.Identity.ToString(), origin = refs.Length > 0 ? "source" : "metadata",
            declarations = refs.Select(Span).ToArray(), kind = symbol is IMethodSymbol method ?
                method.MethodKind == MethodKind.Constructor || method.MethodKind == MethodKind.StaticConstructor ? "constructor" :
                method.MethodKind == MethodKind.LocalFunction ? "local-function" : "method" :
                symbol is INamedTypeSymbol ? "type" : symbol.Kind.ToString().ToLowerInvariant(),
            methodKind = symbol is IMethodSymbol m ? m.MethodKind.ToString() : null };
    }
    static object DiagnosticRow(Diagnostic d) => new { id = d.Id, severity = d.Severity.ToString().ToLowerInvariant(),
        message = d.GetMessage(System.Globalization.CultureInfo.InvariantCulture),
        path = d.Location.IsInSource ? d.Location.SourceTree!.FilePath : null,
        startByte = d.Location.IsInSource ? (int?)Byte(d.Location.SourceTree!, d.Location.SourceSpan.Start) : null,
        endByte = d.Location.IsInSource ? (int?)Byte(d.Location.SourceTree!, d.Location.SourceSpan.End) : null };

    static CSharpCompilation Build(string id)
    {
        if (Compilations.TryGetValue(id, out var found)) return found;
        if (!Building.Add(id)) throw new ArgumentException("Cyclic project reference: " + id);
        var project = Input.Projects.Single(p => p.Id == id);
        if (!LanguageVersionFacts.TryParse(project.LanguageVersion, out var language)) throw new ArgumentException("Unsupported language version");
        var parse = new CSharpParseOptions(language, preprocessorSymbols: project.Defines);
        var trees = project.Files.Select(f => CSharpSyntaxTree.ParseText(f.Text, parse, path: f.Path)).ToList();
        if (project.GlobalUsings.Length > 0)
            trees.Add(CSharpSyntaxTree.ParseText(string.Join("\n", project.GlobalUsings.Select(u => "global using " + u + ";")), parse,
                path: "<implicit-usings:" + id + ">"));
        var references = project.References.Select(p => (MetadataReference)MetadataReference.CreateFromFile(p)).ToList();
        references.AddRange(project.ProjectReferences.Select(p => Build(p).ToMetadataReference()));
        var nullable = project.Nullable == "enable" ? NullableContextOptions.Enable : project.Nullable == "annotations" ?
            NullableContextOptions.Annotations : project.Nullable == "warnings" ? NullableContextOptions.Warnings : NullableContextOptions.Disable;
        var output = project.OutputKind?.ToLowerInvariant() switch {
            "console" or "exe" or "consoleapplication" => OutputKind.ConsoleApplication,
            "winexe" or "windowsapplication" => OutputKind.WindowsApplication,
            null or "library" or "dynamicallylinkedlibrary" => OutputKind.DynamicallyLinkedLibrary,
            _ => throw new ArgumentException("Unsupported compilation output kind") };
        var compilation = CSharpCompilation.Create(project.AssemblyName ?? id.Replace('/', '_').Replace('\\', '_'), trees, references,
            new CSharpCompilationOptions(output, nullableContextOptions: nullable));
        Compilations[id] = compilation;
        Building.Remove(id);
        return compilation;
    }
    static bool ErrorType(ITypeSymbol? type) => type != null && (type.TypeKind == TypeKind.Error ||
        (type is IArrayTypeSymbol a && ErrorType(a.ElementType)) ||
        (type is INamedTypeSymbol n && n.TypeArguments.Any(ErrorType)));
    static bool ErrorHierarchy(INamedTypeSymbol? type)
    {
        for (var current = type; current != null; current = current.BaseType)
            if (ErrorType(current) || current.Interfaces.Any(ErrorType)) return true;
        return false;
    }
    static bool IncompleteSignature(ISymbol? symbol) => symbol is IMethodSymbol m &&
        (ErrorType(m.ReturnType) || m.Parameters.Any(p => ErrorType(p.Type)) || m.TypeArguments.Any(ErrorType) || ErrorHierarchy(m.ContainingType));
    static IEnumerable<INamedTypeSymbol> Types(INamespaceOrTypeSymbol root)
    {
        foreach (var item in root.GetMembers())
        {
            if (item is INamedTypeSymbol type) yield return type;
            if (item is INamespaceOrTypeSymbol nested)
                foreach (var child in Types(nested)) yield return child;
        }
    }
    static object? Registration(InvocationExpressionSyntax node, SemanticModel model, IMethodSymbol? method)
    {
        if (method == null || method.DeclaringSyntaxReferences.Length != 0 ||
            method.ContainingType.ToDisplayString() != "Microsoft.Extensions.DependencyInjection.ServiceCollectionServiceExtensions" ||
            method.ContainingAssembly.Name != "Microsoft.Extensions.DependencyInjection.Abstractions" ||
            (method.Name != "AddScoped" && method.Name != "AddSingleton" && method.Name != "AddTransient") ||
            (method.TypeArguments.Length != 1 && method.TypeArguments.Length != 2) ||
            method.TypeArguments.Any(ErrorType)) return null;
        var implementations = new List<ITypeSymbol>();
        var factory = false;
        if (method.TypeArguments.Length == 2) implementations.Add(method.TypeArguments[1]);
        foreach (var argument in node.ArgumentList.Arguments)
        {
            if (argument.Expression is not LambdaExpressionSyntax lambda) continue;
            factory = true;
            var expressions = new List<ExpressionSyntax>();
            if (lambda.Body is ExpressionSyntax expression) expressions.Add(expression);
            else if (lambda.Body is BlockSyntax block)
                expressions.AddRange(block.DescendantNodes().OfType<ReturnStatementSyntax>()
                    .Where(r => r.Expression != null &&
                        !r.Ancestors().TakeWhile(a => a != block).Any(a => a is AnonymousFunctionExpressionSyntax || a is LocalFunctionStatementSyntax))
                    .Select(r => r.Expression!));
            foreach (var expressionValue in expressions)
            {
                ExpressionSyntax value = expressionValue;
                while (value is ParenthesizedExpressionSyntax wrapped) value = wrapped.Expression;
                if (value is not BaseObjectCreationExpressionSyntax) continue;
                var type = model.GetTypeInfo(value).Type;
                if (type != null && !ErrorType(type)) implementations.Add(type);
            }
        }
        return new { path = node.SyntaxTree.FilePath, startByte = Byte(node.SyntaxTree, node.Span.Start),
            endByte = Byte(node.SyntaxTree, node.Span.End), serviceType = Target(method.TypeArguments[0]),
            implementationTypes = implementations.Distinct<ITypeSymbol>(SymbolEqualityComparer.Default).Select(Target).ToArray(),
            factory, registrationMethod = method.ToDisplayString(SymbolDisplayFormat.CSharpErrorMessageFormat),
            conditional = true, runtimeTargetConfirmed = false };
    }
    static object Analyze(ProjectInput project)
    {
        var compilation = Build(project.Id);
        var diagnostics = compilation.GetDiagnostics();
        var declarations = new List<object>();
        var calls = new List<object>();
        var registrations = new List<object>();
        var sourceTypes = Compilations.Values.SelectMany(c => Types(c.Assembly.GlobalNamespace)).ToArray();
        foreach (var tree in compilation.SyntaxTrees.Where(t => !t.FilePath.StartsWith("<implicit-usings:")))
        {
            var model = compilation.GetSemanticModel(tree);
            foreach (var node in tree.GetRoot().DescendantNodes())
            {
                if (node is BaseMethodDeclarationSyntax || node is LocalFunctionStatementSyntax ||
                    node is BaseTypeDeclarationSyntax || node is DelegateDeclarationSyntax || node is PropertyDeclarationSyntax)
                {
                    var declaration = model.GetDeclaredSymbol(node);
                    if (declaration != null) declarations.Add(Target(declaration));
                }
                if (node is not InvocationExpressionSyntax && node is not ObjectCreationExpressionSyntax && node is not ImplicitObjectCreationExpressionSyntax) continue;
                var info = model.GetSymbolInfo(node);
                var operation = model.GetOperation(node);
                var dynamic = operation is IDynamicInvocationOperation || operation is IDynamicObjectCreationOperation;
                var symbol = info.Symbol;
                var method = symbol as IMethodSymbol;
                if (node is InvocationExpressionSyntax invocation && Registration(invocation, model, method) is object registration)
                    registrations.Add(registration);
                var dispatch = dynamic ? "dynamic" : method?.MethodKind == MethodKind.DelegateInvoke ? "delegate" :
                    method?.ContainingType.TypeKind == TypeKind.Interface ? "interface" :
                    method != null && (method.IsVirtual || method.IsOverride || method.IsAbstract) ? "virtual" :
                    node is InvocationExpressionSyntax ? "direct" : "constructor";
                var binding = diagnostics.Where(d => d.Severity == DiagnosticSeverity.Error && d.Location.SourceTree == tree &&
                    (d.Location.SourceSpan.IntersectsWith(node.Span) || node.Span.Contains(d.Location.SourceSpan))).Select(DiagnosticRow).ToList();
                if (IncompleteSignature(symbol)) binding.Add(new { id = "error-type", severity = "error", message = "Declared target contains an unresolved type" });
                if (!project.ConfigurationComplete) binding.Add(new { id = "configuration-incomplete", severity = "error", message = "Static project configuration is incomplete" });
                var implementations = new List<object>();
                if (method?.ContainingType.TypeKind == TypeKind.Interface)
                    foreach (var type in sourceTypes)
                        foreach (var iface in type.AllInterfaces.Where(i => SymbolKey(i) == SymbolKey(method.ContainingType)))
                        {
                            var member = iface.GetMembers(method.Name).OfType<IMethodSymbol>().FirstOrDefault(m =>
                                DefinitionKey(m) == DefinitionKey(method));
                            if (member != null && type.FindImplementationForInterfaceMember(member) is ISymbol implementation)
                                implementations.Add(Target(implementation));
                        }
                calls.Add(new { path = tree.FilePath, startByte = Byte(tree, node.Span.Start), endByte = Byte(tree, node.Span.End),
                    kind = node is InvocationExpressionSyntax ? "invocation" : "object-creation",
                    compilerStatus = dynamic ? "dynamic" : symbol != null ? "resolved" : info.CandidateSymbols.Length > 0 ? "candidates" : "unresolved",
                    declaredTarget = symbol == null || dynamic ? null : Target(symbol),
                    candidates = dynamic && symbol != null ? new[] { Target(symbol) } : info.CandidateSymbols.Select(Target).ToArray(),
                    candidateReason = info.CandidateReason.ToString(), dispatchKind = dispatch, implementationCandidates = implementations,
                    bindingDiagnostics = binding });
            }
        }
        return new { id = project.Id, diagnostics = diagnostics.Select(DiagnosticRow).ToArray(), declarations, calls, registrations };
    }
    public static void Main()
    {
        Console.InputEncoding = new UTF8Encoding(false);
        Console.OutputEncoding = new UTF8Encoding(false);
        Input = JsonSerializer.Deserialize<Request>(Console.In.ReadToEnd(), new JsonSerializerOptions { PropertyNameCaseInsensitive = true })!;
        foreach (var project in Input.Projects) Build(project.Id);
        Console.Write(JsonSerializer.Serialize(new { projects = Input.Projects.Select(Analyze).ToArray() }, Json));
    }
}
