using StudentManagement.Core;

var connection = Environment.GetEnvironmentVariable("CB_AZURE_SQL_CONNECTION") ?? throw new InvalidOperationException("Explicit Azure connection is required.");
var service = new SqlServerStudentService(connection, () => new CurrentUser("azure-deployment-smoke", "deployment-verification", Role.Staff), webTokens: true);
var lookups = await service.LookupAsync();
if (lookups.Codes.Count != 70 || lookups.Classes.Count != 0) throw new Exception("Unexpected initial lookup data.");
var result = await service.SearchAsync(new SearchCriteria());
if (result.Outcome != Outcome.NoChange || result.Count != 0 || result.Items.Count != 0 || result.Errors.Count != 0 || result.LimitExceeded) throw new Exception($"Actual Azure SQL search failed: {result.Outcome}; Count={result.Count}; Errors={string.Join(';',result.Errors.Select(e=>e.Code+':'+e.Message))}");
Console.WriteLine("PASS: actual SqlServerStudentService against Azure SQL, 70 codes, 0 classes, student search 0 rows; no business writes.");
