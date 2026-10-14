"""Apply code-only CSS and browser regressions after parent freezes r17."""
from pathlib import Path
import argparse,ast,hashlib,json

HERE=Path(__file__).resolve().parent
MAIN=HERE.parents[2]/'src'
CSS_PATH=HERE.parent/'source-pilot/table-css-prototype-r03/candidate.css'
CSS_SHA='e3373dc2efc2ee2a60693a34e7a24010c6092a737a7703722f9d053056be3d54'
RENDERER=MAIN/'contextbase/ai/rendering.py'
TEST=MAIN/'contextbase/tests/test_ai_rendering.py'

def safe(path):
    path=Path(path).absolute()
    for current in (path,*path.parents):
        if current.is_symlink() or (current.exists() and getattr(current.lstat(),'st_file_attributes',0)&0x400):
            raise ValueError('Linked code input/output rejected')
    return path
def sha(p):return hashlib.sha256(safe(p).read_bytes()).hexdigest()
def inventory(root):return {p.relative_to(root).as_posix():sha(p) for p in sorted(root.rglob('*'))
    if p.is_file() and '__pycache__' not in p.parts and p.suffix not in {'.pyc','.pyo'}}

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--runtime-receipt',type=Path,required=True)
    parser.add_argument('--runtime-sha256',required=True);args=parser.parse_args()
    receipt_path=safe(args.runtime_receipt)
    assert sha(receipt_path)==args.runtime_sha256
    receipt=json.loads(receipt_path.read_text(encoding='utf8'))
    frozen=safe(receipt['destination'])
    assert receipt['fileCount']==126 and inventory(frozen)==receipt['files']
    before=inventory(MAIN);assert before==receipt['files']
    assert before['contextbase/ai/rendering.py']=='69c1f80c23bacf35f72a29e9f0f4b8d0e07cf527c2b97342355f46c59f37a504'
    assert before['contextbase/tests/test_ai_rendering.py']=='771b51dae14f0d40a9e10fc33f69177752fa2bde599ab93cda174165af53a1a8'
    assert sha(CSS_PATH)==CSS_SHA
    css=CSS_PATH.read_text(encoding='utf8')
    old_renderer=RENDERER.read_text(encoding='utf8')
    tree=ast.parse(old_renderer)
    match=[n for n in tree.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='BASE_STYLE' for t in n.targets)]
    assert len(match)==1
    lines=old_renderer.splitlines(keepends=True)
    index=match[0].end_lineno
    lines[index:index]=['MARKDOWN_TABLE_READABILITY_STYLE = '+repr(css)+'\n',
                        'BASE_STYLE += MARKDOWN_TABLE_READABILITY_STYLE\n']
    new_renderer=''.join(lines)
    new_tree=ast.parse(new_renderer)
    filtered=[n for n in new_tree.body if not (
        isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='MARKDOWN_TABLE_READABILITY_STYLE' for t in n.targets)
        or isinstance(n,ast.AugAssign) and isinstance(n.target,ast.Name) and n.target.id=='BASE_STYLE')]
    assert [ast.dump(n,include_attributes=False) for n in tree.body]==[ast.dump(n,include_attributes=False) for n in filtered]
    methods=(HERE/'table_css_core_test_methods.py.txt').read_text(encoding='utf8')
    ast.parse('class SyntaxCheck:\n'+methods)
    old_test=TEST.read_text(encoding='utf8')
    sentinel='    def test_missing_mermaid_dependency_is_not_rendered(self):'
    assert old_test.count(sentinel)==1
    new_test=old_test.replace(sentinel,methods+sentinel)
    ast.parse(new_test)
    output=HERE/'core-r18-apply.json';assert not output.exists()
    RENDERER.write_text(new_renderer,encoding='utf8',newline='\n')
    TEST.write_text(new_test,encoding='utf8',newline='\n')
    after=inventory(MAIN)
    modified={p:{'old':before[p],'new':after[p]} for p in before if before[p]!=after[p]}
    assert set(modified)=={'contextbase/ai/rendering.py','contextbase/tests/test_ai_rendering.py'}
    assert inventory(frozen)==receipt['files'] and sha(receipt_path)==args.runtime_sha256
    result={'schema':'core-table-css-application/1','revision':'r18','status':'APPLIED_UNTESTED',
        'css':str(CSS_PATH),'cssSha256':CSS_SHA,'runtimeReceipt':str(receipt_path),
        'runtimeReceiptSha256':args.runtime_sha256,'frozenR17All126FilesUnchanged':True,
        'onlyCssAssignmentsAndTestsChanged':True,'modified':modified,'before':before,'after':after,
        'canonicalBodyEdited':False,'originalApplicationExecuted':False,'published':False}
    output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    print(json.dumps({'path':str(output),'sha256':sha(output),'modified':modified},ensure_ascii=False))

if __name__=='__main__':main()
