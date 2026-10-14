"""Create a fresh geometry-only mechanical model adapter; base code is immutable."""
from pathlib import Path
import hashlib
HERE=Path(__file__).resolve().parent
source=HERE/'delivery_model.py';target=HERE/'delivery_model_r18.py'
assert not target.exists()
text=source.read_text(encoding='utf8')
needle="    columns=len(matrix[0]); begin=row\n"
assert text.count(needle)==1
adapter='''    columns=len(matrix[0]); begin=row
    if sheet['role']=='list' and not grid:
        # A literal matrix stays one row/cell per original record. Only widths
        # grow to satisfy the same Excel row-height gate; never split/omit text.
        widths=[]
        for index in range(columns):
            width=18
            while True:
                try:
                    heights=[cell_height(values[index],max(8,width*13/18)) for values in matrix]
                    if max(heights)<=350:break
                except ValueError as exc:
                    if 'readable Excel row height' not in str(exc):raise
                width+=2
                if width>120:raise ValueError('LIST column exceeds bounded width; no truncation permitted')
            widths.append(width)
        sheet['columnWidths']=widths
        sheet['geometryProjection']={'kind':'adaptive-list-column-width-only','originalDefaultColumnWidth':18,'widths':widths,'literalMatrixOrderPreserved':True,'maxTargetRowHeightPt':350}
'''
target.write_text(text.replace(needle,adapter),encoding='utf8')
print({'baseSha256':hashlib.sha256(source.read_bytes()).hexdigest(),'freshAdapterSha256':hashlib.sha256(target.read_bytes()).hexdigest(),'path':str(target)})
