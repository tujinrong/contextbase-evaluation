"""DDS positions 1..44 are explicit; numeric/ASCII identifiers are never DBCS."""
import sys
sys.dont_write_bytecode = True
from pathlib import Path
BASE=Path(__file__).resolve().parents[1]
def keyword(value,condition=''):
    chars=[' ']*44;chars[5]='A'
    if condition:chars[7:10]=list(condition.rjust(3))
    return ''.join(chars)+value
def record(name,*keys):
    chars=[' ']*44;chars[5]='A';chars[16]='R';chars[18:28]=list(name.ljust(10))
    return [''.join(chars).rstrip()]+[keyword(k) for k in keys]
def field(name,length,row,col,usage='B',dtype='O',readonly=False):
    chars=[' ']*44;chars[5]='A';chars[18:28]=list(name.ljust(10))
    chars[29:34]=list(str(length).rjust(5));chars[34]=dtype;chars[37]=usage
    if usage!='H':chars[38:41]=list(str(row).rjust(3));chars[41:44]=list(str(col).rjust(3))
    lines=[''.join(chars).rstrip()]
    if readonly:lines.append(keyword('DSPATR(PR)','75'))
    return lines
def literal(text,row,col):
    import unicodedata
    chunks=[];chunk='';start=col
    for ch in text:
        if len((chunk+ch).encode('utf8'))>32:
            chunks.append((chunk,start))
            start+=sum(0 if unicodedata.combining(c) else 2 if unicodedata.east_asian_width(c) in 'WF' else 1 for c in chunk)
            chunk=''
        chunk+=ch
    if chunk:chunks.append((chunk,start))
    lines=[]
    for chunk,start in chunks:
        chars=[' ']*44;chars[5]='A';chars[38:41]=list(str(row).rjust(3));chars[41:44]=list(str(start).rjust(3))
        lines.append(''.join(chars)+"'"+chunk+"'")
    return '\n'.join(lines)
def header():
    return [keyword('DSPSIZ(27 132 *DS4)')]+[keyword(f'CF{key:02d}({key:02d})') for key in (3,4,5,6,7,8,9,10,11,12,14,15,16,20,23)]+[keyword('ROLLUP(25)'),keyword('ROLLDOWN(26)')]
def aux(lines):
    lines+=record('CNFRM')
    lines+=field('CTITLE',100,2,3,'O')
    lines+=[literal('F10=Confirm F12=Cancel PgUp/PgDn',24,3)]
    lines+=field('CREASON',122,4,3)
    lines+=field('CTOTAL',100,6,3,'O')
    lines+=field('CSEL',3,7,5,dtype='A')
    for i in range(1,11):lines+=field(f'C{i:02d}',122,i+9,3,'O')
    lines+=field('CMSG',128,26,3,'O')
    lines+=record('LONGTXT')
    lines+=field('LTITLE',100,2,3,'O')
    lines+=field('LPOS',80,3,3,'O')
    lines += [literal('Unicode escapes / doubled slash',5,3)]
    for i in range(1,7):lines+=field(f'LTXT{i}',120,i*2+5,3,readonly=True)
    lines+=[literal('F10=Apply F12=Cancel PgUp/PgDn',23,3)]
    lines+=field('LMSG',128,26,3,'O')
    return lines
from screen_layout import generate
generate(BASE,header,record,field,literal,keyword,aux)
