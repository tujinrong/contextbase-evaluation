"""Fresh own-clipboard sequence proof; never reads preexisting clipboard content."""
from pathlib import Path
P=Path(__file__).resolve().parent
ps=(P/'excel_bitmap_readonly_r01.ps1').read_text(encoding='utf8')
ps=ps.replace(' Add-Type -AssemblyName System.Drawing\n', ''' Add-Type -AssemblyName System.Drawing
 Add-Type -TypeDefinition 'using System; using System.Runtime.InteropServices; public static class OwnClipboardSequence { [DllImport("user32.dll")] public static extern uint GetClipboardSequenceNumber(); }'
 $qaResult.clipboardSideEffect='Own Excel Range.CopyPicture temporarily overwrites clipboard; no prior content is read or output.'
''')
ps=ps.replace('  $qaCell.CopyPicture(1,2)\n', '''  $qaSequenceBefore=[OwnClipboardSequence]::GetClipboardSequenceNumber()
  $qaCell.CopyPicture(1,2)
  $qaSequenceOwn=[OwnClipboardSequence]::GetClipboardSequenceNumber()
  if($qaSequenceOwn -eq $qaSequenceBefore){throw 'CopyPicture did not change clipboard; preexisting contents will not be read'}
''')
ps=ps.replace('   $qaImage=[System.Windows.Forms.Clipboard]::GetImage()\n', '''   if([OwnClipboardSequence]::GetClipboardSequenceNumber() -ne $qaSequenceOwn){throw 'Clipboard changed after own CopyPicture; refuse content read'}
   $qaImage=[System.Windows.Forms.Clipboard]::GetImage()
   if([OwnClipboardSequence]::GetClipboardSequenceNumber() -ne $qaSequenceOwn){if($null -ne $qaImage){$qaImage.Dispose()};throw 'Clipboard raced during own bitmap read; no output'}
''')
ps=ps.replace("projection='Excel Range.CopyPicture xlScreen xlBitmap';cellOrFormatChanges=$false", "projection='Excel Range.CopyPicture xlScreen xlBitmap';clipboardSequenceBefore=$qaSequenceBefore;clipboardOwnSequence=$qaSequenceOwn;clipboardOnlyOwnContentRead=$true;cellOrFormatChanges=$false")
out=P/'excel_bitmap_readonly_r02.ps1';assert not out.exists();out.write_text(ps,encoding='utf8')
py=(P/'run_excel_bitmap_readonly_r01.py').read_text(encoding='utf8').replace('excel_bitmap_readonly_r01.ps1','excel_bitmap_readonly_r02.ps1')
out=P/'run_excel_bitmap_readonly_r02.py';assert not out.exists();out.write_text(py,encoding='utf8')
