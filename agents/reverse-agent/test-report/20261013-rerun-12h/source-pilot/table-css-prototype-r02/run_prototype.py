"""Fresh r02: code-only nowrap, inherited guarded synthetic r01 comparison."""
from pathlib import Path
import importlib.util

HERE=Path(__file__).resolve().parent
BASE=HERE.parent/'table-css-prototype-r01/run_prototype.py'
spec=importlib.util.spec_from_file_location('table_css_r01_technical_functions',BASE)
probe=importlib.util.module_from_spec(spec)
spec.loader.exec_module(probe)
probe.HERE=HERE
probe.CSS += probe.SELECTOR+' code{white-space:nowrap}'
tokens=['SYNTHETIC-STATUS-0123456789','-12345678901234567890.25','12345678901234567890.012345',
        '2026-10-13T14:45:00+09:00','CODE VALUE WITH SPACES']
probe.FIXTURE=probe.FIXTURE.replace('SYNTHETIC-STATUS-0123456789','PLAIN-LEGAL-WRAP-TOKEN')
probe.FIXTURE=probe.FIXTURE.replace(probe.EMBEDDED,'')
probe.FIXTURE += probe.table(['分類ID','code value','description'],
    [['CODE_'+str(i),'`'+token+'`','合成codeの文字と値を保持する。'] for i,token in enumerate(tokens,1)])
probe.FIXTURE += probe.table(['protected one-column'],[['`OneColumnCodeWithManyCharactersWithoutBreaksAndNoStyleChange`']])
probe.FIXTURE += probe.table(['protected key','protected code'],
    [['TwoColumnProtected','`TwoColumnCodeWithManyCharactersWithoutBreaksAndNoStyleChange`']])
probe.FIXTURE += probe.EMBEDDED
probe.ATOMIC = [t for t in probe.ATOMIC if t != 'SYNTHETIC-STATUS-0123456789'] + tokens
original_table=probe.table
def negative_table(headers,rows):
    # Synthetic negative cases only. No manuscript/HTML from a business input is read.
    if rows and rows[0][0]=='W'*2500:
        rows=[['<code>'+rows[0][0]+'</code>',*rows[0][1:]]]
    if rows and rows[0][0]=='AuthoredAtomic<br>Token':
        rows=[['<code>'+rows[0][0]+'</code>',*rows[0][1:]]]
    return original_table(headers,rows)
probe.table=negative_table

if __name__=='__main__':
    probe.main()
