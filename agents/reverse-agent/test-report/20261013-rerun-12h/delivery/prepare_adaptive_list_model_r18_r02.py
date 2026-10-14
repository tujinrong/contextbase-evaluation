"""Fresh LIST width-only projection. Never change literal strings or row order."""
from pathlib import Path
import hashlib
HERE=Path(__file__).resolve().parent
source=HERE/'delivery_model.py';target=HERE/'delivery_model_r18_r02.py'
assert not target.exists()
text=source.read_text(encoding='utf8')
needle="    columns=len(matrix[0]); begin=row\n"
assert text.count(needle)==1
adapter='''    columns=len(matrix[0]); begin=row
    if sheet['role']=='list' and not grid:
        # Whole ASCII identifiers/numbers reserve sufficient width before the
        # existing height gate. Canonical matrices remain one record per row.
        widths=[]
        longest=[]
        for index in range(columns):
            tokens=[token.group() for values in matrix for token in re.finditer(r'[A-Za-z0-9_]+(?:[.\\-][A-Za-z0-9_]+)*',values[index])]
            token_length=max((len(token) for token in tokens),default=0)
            width=max(18,math.ceil((token_length+4)*18/13/2)*2)
            while True:
                if width>120:raise ValueError('LIST indivisible token or row exceeds bounded width; no truncation permitted')
                try:
                    heights=[cell_height(values[index],max(8,width*13/18)) for values in matrix]
                    if max(heights)<=350:break
                except ValueError as exc:
                    if 'readable Excel row height' not in str(exc):raise
                width+=2
            widths.append(width);longest.append(token_length)
        sheet['columnWidths']=widths
        sheet['geometryProjection']={'kind':'adaptive-list-whole-token-width-only','originalDefaultColumnWidth':18,'widths':widths,'longestAsciiTokenCharacters':longest,'literalMatrixOrderPreserved':True,'maxTargetRowHeightPt':350,'maximumWidth':120}
'''
target.write_text(text.replace(needle,adapter),encoding='utf8')
print({'baseSha256':hashlib.sha256(source.read_bytes()).hexdigest(),'freshAdapterSha256':hashlib.sha256(target.read_bytes()).hexdigest(),'path':str(target)})
