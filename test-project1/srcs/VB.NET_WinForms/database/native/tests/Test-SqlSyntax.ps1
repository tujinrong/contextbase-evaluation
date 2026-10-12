param([string]$ScriptDomPath='C:\Program Files\Microsoft Visual Studio\18\Community\Common7\IDE\Extensions\Microsoft\SQLDB\DAC\Microsoft.SqlServer.TransactSql.ScriptDom.dll',[string]$ReportPath)
$ErrorActionPreference='Stop'
if($ReportPath -and (Test-Path -LiteralPath $ReportPath)){throw 'Existing SQL test report must not be overwritten.'}
Add-Type -LiteralPath $ScriptDomPath
$taskParser=[Microsoft.SqlServer.TransactSql.ScriptDom.TSql160Parser]::new($true)
$taskResults=@()
foreach($taskName in @('000_sqlclr.sql','010_student_api.sql','020_master_api.sql')) {
 $taskFile=Join-Path $PSScriptRoot "../$taskName";$taskSql=Get-Content -LiteralPath $taskFile -Encoding UTF8 -Raw
 $taskErrors=$null; $taskFragment=$taskParser.Parse([IO.StringReader]::new($taskSql),[ref]$taskErrors)
 $taskResult=@{file=$taskName;parseErrors=@($taskErrors | Select-Object Number,Line,Column,Message);sha256=(Get-FileHash -LiteralPath $taskFile -Algorithm SHA256).Hash}
 $taskResults+=$taskResult;Write-Output "$taskName syntax issues: $($taskErrors.Count)"
 if($taskErrors.Count -gt 0) { $taskErrors | Format-List;throw 'T-SQL syntax failed.' }
}
$taskCandidateSql=Get-Content -LiteralPath (Join-Path $PSScriptRoot '../010_student_api.sql') -Encoding UTF8 -Raw
$taskProjection=[regex]::Match($taskCandidateSql,'(?m)^\s*SELECT (?<columns>[^\r\n]+?) FROM dbo\.m_student s LEFT JOIN dbo\.m_class c ON c\.class_id=s\.class_id WHERE s\.student_id IN\(SELECT TOP\(20\) student_id FROM @candidates ORDER BY student_id\)')
$taskColumns=@($taskProjection.Groups['columns'].Value.Split(',') | ForEach-Object {$_.Trim()})
if(-not $taskProjection.Success -or ($taskColumns -join ',') -ne "s.student_no,s.student_name,s.birth_date,CASE WHEN c.class_id IS NULL THEN NULL ELSE c.class_code+N' '+c.class_name END class_name"){throw 'Duplicate candidate projection exceeds the four permitted display categories.'}
Write-Output 'Candidate projection: four permitted fields only; full candidate ID/version hash remains server-side.'
if($ReportPath){@{status='Passed';parser='TSql160Parser';scriptDomVersion=[Microsoft.SqlServer.TransactSql.ScriptDom.TSqlParser].Assembly.GetName().Version.ToString();files=$taskResults;candidateProjection=$taskColumns;candidateProjectionPassed=$true;databaseExecution=$false} | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $ReportPath -Encoding UTF8}
