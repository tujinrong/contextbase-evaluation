"""MD -> v2-inspired, data-only XLSX, with incremental per-document publication.

python -m docsite.excel --root .
python -m docsite.excel --markdown input.md --xlsx output.xlsx
"""
from __future__ import annotations
import argparse
import json
import os
from pathlib import Path
import shutil
import tempfile
from .excel_model import sha
from .v2.render_document_xlsx import markdown_model
from .excel_package import package, verify

VERSION='2.1.0-v2-three-frames'


def safe(root: Path, path: Path) -> Path:
    root=root.resolve();absolute=Path(os.path.abspath(path))
    if not absolute.is_relative_to(root):raise ValueError('Path outside root')
    for part in (absolute,*absolute.parents):
        if part==root:break
        if part.is_symlink():raise ValueError('Symlinks are not allowed')
    if not absolute.resolve().is_relative_to(root):raise ValueError('Path outside root')
    return absolute


def write_json(path: Path, value):
    path.parent.mkdir(parents=True,exist_ok=True)
    temp=path.with_suffix(path.suffix+'.tmp')
    temp.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    os.replace(temp,path)


def convert(markdown: Path, xlsx: Path, *, source: str | None=None, repository='', revision='main') -> dict:
    if xlsx.suffix.lower()!='.xlsx' or markdown.resolve()==xlsx.resolve():raise ValueError('Use a separate .xlsx output path')
    if markdown.is_symlink() or xlsx.is_symlink():raise ValueError('Symlink input/output prohibited')
    if markdown.stat().st_size>8_000_000:raise ValueError('Markdown exceeds 8 MB')
    model=markdown_model(markdown.read_text(encoding='utf-8-sig'),source or markdown.name,repository=repository,revision=revision,markdown_path=markdown,allowed_root=markdown.parent)
    data=package(model);checks=verify(data,model)
    xlsx.parent.mkdir(parents=True,exist_ok=True)
    temporary=xlsx.with_suffix('.xlsx.tmp');temporary.write_bytes(data);os.replace(temporary,xlsx)
    return {**checks,'markdown':source or markdown.name,'markdown_sha256':sha(markdown.read_bytes()),
            'xlsx_sha256':sha(data),'sheet_names':[s['name'] for s in model['sheets']],
            'warnings':model['warnings']}


def build_excels(root: Path, *, repository='', revision='main') -> dict:
    root=root.resolve();mdroot=safe(root,root/'output/md');target=safe(root,root/'output/Excel')
    work=safe(root,root/'.contextbase-work');work.mkdir(exist_ok=True)
    reportroot=safe(root,root/'report/excel');reportroot.mkdir(parents=True,exist_ok=True)
    paths=sorted(mdroot.rglob('*.md'))
    if not paths:raise ValueError('No Markdown in output/md')
    for p in paths:safe(mdroot,p)
    lock=work/'excel.lock'
    with lock.open('x') as f:f.write(str(os.getpid()))
    stage=Path(tempfile.mkdtemp(prefix='excel-',dir=work))
    report={'version':VERSION,'status':'running','documents':[],'errors':[],'source':'output/md','destination':'output/Excel'}
    try:
        oldfile=reportroot/'manifest.json'
        old=json.loads(oldfile.read_text(encoding='utf-8')) if oldfile.is_file() else {'documents':[]}
        owned={x['xlsx']:x for x in old['documents']}
        if target.exists():
            for p in target.rglob('*'):
                safe(target,p)
                if p.is_file():
                    key=p.relative_to(target).as_posix()
                    if key not in owned or sha(p.read_bytes())!=owned[key]['xlsx_sha256']:
                        raise ValueError('Unmanaged or edited Excel output: '+key)
        engine=sha(b''.join((Path(__file__).parent/name).read_bytes() for name in ['excel.py','excel_model.py','excel_package.py','v2/render_document_xlsx.py','v2/upstream_layout.py']))
        for md in paths:
            source=md.relative_to(mdroot).as_posix();key=str(Path(source).with_suffix('.xlsx')).replace(os.sep,'/')
            signature=sha((VERSION+'\0'+engine+'\0'+source+'\0'+repository+'\0'+revision+'\0').encode()+md.read_bytes())
            model=markdown_model(md.read_text(encoding='utf-8-sig'),source,repository=repository,revision=revision,markdown_path=md,allowed_root=mdroot)
            assets=''.join(i['sha256'] for sh in model['sheets'] for i in sh.get('images',[]))
            signature=sha((signature+assets).encode())
            previous=owned.get(key,{})
            destination=stage/key;destination.parent.mkdir(parents=True,exist_ok=True)
            if previous.get('signature')==signature and (target/key).is_file():
                data=(target/key).read_bytes();checks=verify(data,model);reused=True
            else:
                data=package(model);checks=verify(data,model);reused=False
            destination.write_bytes(data)
            record={**checks,'markdown':source,'xlsx':key,'signature':signature,
                    'markdown_sha256':sha(md.read_bytes()),'xlsx_sha256':sha(data),'reused':reused,
                    'sheet_names':[s['name'] for s in model['sheets']],'warnings':model['warnings']}
            report['documents'].append(record)
            # Durable checkpoint remains under report if the next document fails.
            write_json(reportroot/'checkpoint.json',report)
        report.update(status='verified',count=len(report['documents']),
                      checked_cells=sum(d['checked_cells'] for d in report['documents']),
                      sheets=sum(d['sheets'] for d in report['documents']))
        backup=work/('previous-'+stage.name)
        if target.exists():target.rename(backup)
        try:
            target.parent.mkdir(parents=True,exist_ok=True);stage.rename(target)
        except Exception:
            if backup.exists():backup.rename(target)
            raise
        write_json(oldfile,report);write_json(reportroot/'validation.json',report)
        warnings=[{'markdown':d['markdown'],'warning':w} for d in report['documents'] for w in d['warnings']]
        write_json(reportroot/'incomplete.json',{'conversion_warnings':warnings,'status':'needs_review' if warnings else 'none'})
        if backup.exists():shutil.rmtree(backup)
        return report
    except Exception as exc:
        report.update(status='failed',errors=[str(exc)],published=False)
        write_json(reportroot/'validation.json',report)
        raise
    finally:
        if stage.exists():shutil.rmtree(stage)
        lock.unlink(missing_ok=True)


def main(argv=None):
    parser=argparse.ArgumentParser(description='MarkdownからExcel仕様書を作成')
    parser.add_argument('--root',type=Path,default=Path('.'))
    parser.add_argument('--markdown',type=Path)
    parser.add_argument('--xlsx',type=Path)
    parser.add_argument('--repository',default='')
    parser.add_argument('--revision',default='main')
    args=parser.parse_args(argv)
    if bool(args.markdown)!=bool(args.xlsx):parser.error('--markdown and --xlsx must be specified together')
    try:
        result=convert(args.markdown,args.xlsx,repository=args.repository,revision=args.revision) if args.markdown else build_excels(args.root,repository=args.repository,revision=args.revision)
    except (OSError,ValueError) as exc:parser.exit(1,'excel: '+str(exc)+'\n')
    print(json.dumps(result,ensure_ascii=False,indent=2));return 0


if __name__=='__main__':raise SystemExit(main())
