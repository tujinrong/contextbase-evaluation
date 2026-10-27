"""Source-first Japanese logical names, separate from physical identifiers."""
from __future__ import annotations
import re
from pathlib import Path
from bs4 import BeautifulSoup
from contextbase.shared.store import read, safe

JP=re.compile(r'[ぁ-ゖァ-ヺ一-鿿々〆ヵヶｦ-ﾟ]')

def is_japanese(value):
    return isinstance(value,str) and bool(JP.search(value)) and not any(t in value for t in ['<%','名称未確認','未確認（','仮の名称'])


def load_names(root, sources=None):
    names={}
    for f in sorted(safe(root,'src-dynamic').glob('*/terminology.json')):
        data=read(safe(root,f))
        roots=data.get('source_roots',[])
        foundation=f.parent/'foundation.json'
        if not roots and foundation.is_file():
            roots=sorted({p.split('/')[0] for p in read(foundation).get('features',{})})
        if sources is not None and roots and not any(p.split('/')[0] in roots for p in sources):continue
        if data.get('trust')=='repository-reviewed':names.update(data.get('types',{}));names.update(data.get('fields',{}))
    return names


def source_name(path, text, names=None):
    stem=Path(path).stem; names=names or {}
    if path in names:return names[path]
    if stem in names:return names[stem]
    if Path(path).suffix.lower() in {'.jsp','.html','.cshtml','.aspx','.vue'}:
        alternatives={}
        for m in re.finditer(r'\bString\s+(\w+)\s*=([^;]+);',text,re.S):
            values=re.findall(r'"([^"\n]+)"',m[2])
            values=[v for v in values if is_japanese(v)]
            if values:alternatives[m[1]]='／'.join(dict.fromkeys(values))
        clean=re.sub(r'<%=\s*(\w+)\s*%>',lambda m:alternatives.get(m[1],''),text)
        clean=re.sub(r'<%[\s\S]*?%>','',clean)
        soup=BeautifulSoup(clean,'html.parser')
        for node in [soup.find('title'),soup.find('h1'),soup.find('h2')]:
            value=node.get_text(' ',strip=True) if node else ''
            if is_japanese(value):return value[:100]
    else:
        # Only the class's own immediately preceding Javadoc, not arbitrary comments.
        match=re.search(r'/\*\*([^*]*(?:\*(?!/)[^*]*)*)\*/\s*(?:@[^\n]+\s*)*(?:public\s+)?(?:abstract\s+|final\s+)?(?:class|interface|enum)\s+',text,re.S)
        if match:
            first=re.split(r'@(?:author|param|date|version|since|see)',match[1])[0]
            value=re.sub(r'<[^>]+>|^[ \t]*\*',' ',first,flags=re.M)
            value=re.sub(r'\s+',' ',value).strip(' *。')
            if is_japanese(value):return value[:100]
    return stem
