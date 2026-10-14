"""Fresh helper delta only; preserve prior synthetic attempt evidence."""
from pathlib import Path
P=Path(__file__).resolve().parent
ps=(P/'excel_static_readonly_r01.ps1').read_text(encoding='utf8')
old="if(-not($qaValue -is [string]) -or $qaValue -cne [string]$qaItem.value){throw"
new="if(([string]$qaItem.value -ne '' -and (-not($qaValue -is [string]) -or $qaValue -cne [string]$qaItem.value)) -or ([string]$qaItem.value -eq '' -and $null -ne $qaValue -and $qaValue -cne '')){throw"
assert old in ps
ps=ps.replace(old,new).replace('value2Type=$qaValue.GetType().FullName','value2Type=$(if($null -eq $qaValue){"null"}else{$qaValue.GetType().FullName})')
out=P/'excel_static_readonly_r02.ps1';assert not out.exists();out.write_text(ps,encoding='utf8')
py=(P/'run_excel_static_readonly_r02.py').read_text(encoding='utf8').replace('excel_static_readonly_r01.ps1','excel_static_readonly_r02.ps1')
needle="assert all(sha(Path(p))==s for p,s in before.items())"
newcheck="""assert all(sha(Path(p))==s for p,s in before.items())
 if status=='COMPLETE':
  result=a.output/'result.json'
  if not result.exists():status='FAILED_NO_RESULT'
  else:
   data=json.loads(result.read_text(encoding='utf-8-sig'))
   if data['status']!='STATIC_EXCEL_PDF_EXPORTED_VISUAL_REVIEW_PENDING' or data['workbookBytesUnchanged'] is not True or data['planBytesUnchanged'] is not True:status='FAILED_HELPER_RESULT'"""
assert needle in py;py=py.replace(needle,newcheck)
out=P/'run_excel_static_readonly_r03.py';assert not out.exists();out.write_text(py,encoding='utf8')
