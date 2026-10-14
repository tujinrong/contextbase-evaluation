"""Fresh read-only Excel projection helpers; no cell/format/workbook saves."""
from pathlib import Path
P=Path(__file__).resolve().parent
old=(P/'excel_static_readonly_r02.ps1').read_text(encoding='utf8')
start=old.index(' $qaIndex=0\n');end=old.index(" $qaResult.status='STATIC_EXCEL_PDF_EXPORTED_VISUAL_REVIEW_PENDING'",start)
replacement=''' Add-Type -AssemblyName System.Windows.Forms
 Add-Type -AssemblyName System.Drawing
 $qaIndex=0
 foreach($qaPreview in $qaSpec.previews){
  $qaIndex++;$qaSheet=$qaBook.Worksheets.Item([string]$qaPreview.sheet)
  $qaCell=$qaSheet.Range([string]$qaPreview.range)
  Write-QaStage ('copy-own-static-picture-'+$qaIndex)
  $qaCell.CopyPicture(1,2)
  $qaImage=$null
  for($qaRetry=0;$qaRetry -lt 10 -and $null -eq $qaImage;$qaRetry++){
   Start-Sleep -Milliseconds 100
   $qaImage=[System.Windows.Forms.Clipboard]::GetImage()
  }
  if($null -eq $qaImage){throw 'Own Range.CopyPicture returned no bitmap'}
  try{
   $qaPng=Join-Path $qaRoot ('preview-'+$qaIndex.ToString('000')+'.png')
   $qaImage.Save($qaPng,[System.Drawing.Imaging.ImageFormat]::Png)
   $qaResult.sheets+=[ordered]@{sheet=[string]$qaPreview.sheet;range=[string]$qaPreview.range;png=$qaPng;width=$qaImage.Width;height=$qaImage.Height;pngSha256=(Get-FileHash -LiteralPath $qaPng -Algorithm SHA256).Hash.ToLowerInvariant();projection='Excel Range.CopyPicture xlScreen xlBitmap';cellOrFormatChanges=$false}
  }finally{$qaImage.Dispose()}
  [void][System.Runtime.InteropServices.Marshal]::FinalReleaseComObject($qaCell);$qaCell=$null
  [void][System.Runtime.InteropServices.Marshal]::FinalReleaseComObject($qaSheet);$qaSheet=$null
 }
'''
text=old[:start]+replacement+old[end:]
text=text.replace('READ_ONLY_EXCEL_STATIC_DISPLAY_QA','READ_ONLY_EXCEL_RANGE_BITMAP_QA').replace('STATIC_EXCEL_PDF_EXPORTED_VISUAL_REVIEW_PENDING','STATIC_EXCEL_BITMAP_EXPORTED_VISUAL_REVIEW_PENDING')
out=P/'excel_bitmap_readonly_r01.ps1';assert not out.exists();out.write_text(text,encoding='utf8')
py=(P/'run_excel_static_readonly_r03.py').read_text(encoding='utf8').replace('excel_static_readonly_r02.ps1','excel_bitmap_readonly_r01.ps1').replace('STATIC_EXCEL_PDF_EXPORTED_VISUAL_REVIEW_PENDING','STATIC_EXCEL_BITMAP_EXPORTED_VISUAL_REVIEW_PENDING')
out=P/'run_excel_bitmap_readonly_r01.py';assert not out.exists();out.write_text(py,encoding='utf8')
