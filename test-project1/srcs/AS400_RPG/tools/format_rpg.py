"""Wrap UTF8 SQLRPGLE source safely below precompiler source columns.
Only statement/layout formatting, preserving literal values and escaped quotes.
"""
from pathlib import Path
import re
B=Path(__file__).resolve().parents[1]
def tokens(s):
 out=[];i=0
 while i<len(s):
  if s[i].isspace():i+=1;continue
  if s[i:i+2]=='//':out.append(s[i:]);break
  if s[i]=="'":
   start=i;i+=1
   while i<len(s):
    if s[i]=="'":
     if i+1<len(s) and s[i+1]=="'":i+=2;continue
     i+=1;break
    i+=1
   literal=s[start:i]
   if out and re.search(r'(?:^|[=(,:])[dDtTxXzZ]$',out[-1]):out[-1]+=literal
   else:out.append(literal)
   continue
  j=i
  while i<len(s) and not s[i].isspace() and s[i] not in "';():,":i+=1
  if i==j:i+=1
  out.append(s[j:i])
 return out
def fmt(line):
 if line.lstrip().startswith('/'):return [line.lstrip()]
 if line.startswith('**') or line.lstrip().startswith('//'):return [line]
 words=tokens(line);words2=[]
 for t in words:
  if t.startswith("'") and len(t.encode('utf8'))>74:
   decoded=t[1:-1].replace("''", "'");part=''
   for ch in decoded:
    if len((part+ch).replace("'","''").encode('utf8'))>52:
     words2.extend(["'"+part.replace("'","''")+"'",'+']);part=''
    part+=ch
   words2.append("'"+part.replace("'","''")+"'")
  else:words2.append(t)
 out=[];buf=' '
 for t in words2:
  if len((buf+' '+t).encode('utf8'))>96 and buf.strip():out.append(buf.rstrip());buf='  '
  tight=(t=='(' or t.startswith('.') or buf.rstrip().endswith(':'))
  buf+=('' if not buf.strip() or tight else ' ')+t
  if t==';':out.append(buf.rstrip());buf=' '
 if buf.strip():out.append(buf.rstrip())
 return out
for p in [*B.joinpath('src').glob('*.sqlrpgle'),*B.joinpath('src').glob('*.rpgleinc'),*B.joinpath('copy').glob('*.rpgleinc')]:
 lines=[]
 for line in p.read_text('utf8').splitlines():
  line=re.sub(r"\b([dDtTxXzZ]) +(?=')",r'\1',line)
  lines+=fmt(line)
 p.write_text('\n'.join(lines)+'\n','utf8')
print('RPG/COPY source statements wrapped to UTF8<=96 bytes')
