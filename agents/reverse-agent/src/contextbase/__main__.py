"""Unified CLI. `rebuild` starts fresh; `build` preserves edited Markdown."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
from .registry import configure, resolve_profile
from .discovery import probe


def main(argv=None) -> int:
    p=argparse.ArgumentParser(description='汎用検出・対象別解析・Markdown/HTML生成と検証')
    p.add_argument('command',choices=['probe','rebuild','build','check','pdf','excel','foundation','detail','specification','validate'])
    p.add_argument('--root',default='.')
    p.add_argument('--config',default='config/project.toml')
    p.add_argument('--replace-output',action='store_true',help='検証成功後に既存の生成領域を置換（inputは保持）')
    p.add_argument('--native',action='store_true',help='対象プロファイルの実言語Pilot比較と欠陥検出試験')
    p.add_argument('--browser',action='store_true',help='全HTMLをChromiumで検査')
    p.add_argument('--pdf',action='store_true',help='build/rebuildで検証付きPDFを生成')
    p.add_argument('--excel',action='store_true',help='build/rebuildでExcel仕様書を生成')
    p.add_argument('--feature',help='P2/P3の対象機能ID')
    p.add_argument('--cold',action='store_true',help='P1/P2のキャッシュを再利用しない')
    a=p.parse_args(argv);root=Path(a.root).resolve()
    if a.excel and a.command not in {'build','rebuild'}:
        p.error('--excelはbuild/rebuild用です。Excelのみの生成にはexcelコマンドを使用してください。')
    if a.pdf and a.command not in {'build','rebuild'}:
        p.error('--pdfはbuild/rebuild用です。PDFのみの生成にはpdfコマンドを使用してください。')
    try:
        # build/check read MD and HTML only; do not require source or load its profile.
        cfg=configure(root,a.config,require_input=a.command in {'probe','rebuild'})
        if a.command in {'foundation','detail','specification','validate'}:
            import importlib
            module='validation' if a.command=='validate' else a.command
            run=importlib.import_module('contextbase.'+module+'.core').run
            result=run(root,feature=a.feature,cold=a.cold,config_file=a.config)
        elif a.command=='probe':
            result=probe(root,cfg);pr=resolve_profile(root,cfg)
            result['selected_profile']=pr['id'] if pr else 'generic'
        elif a.command=='rebuild':
            from .pipeline import rebuild
            result=rebuild(root,a.config,native=a.native,browser=a.browser,replace_output=a.replace_output,pdf=a.pdf,excel=a.excel)
        elif a.command=='excel':
            from docsite.excel import build_excels
            result=build_excels(root,repository=cfg['repository'])
        elif a.command=='pdf':
            from docsite.pdf import build_pdfs
            result=build_pdfs(root)
        else:
            from docsite.publish import build,check
            result=build(root,cfg['repository']) if a.command=='build' else check(root)
        if a.command=='build' and a.excel and not result.get('errors'):
            from docsite.excel import build_excels
            result['excel']=build_excels(root,repository=cfg['repository'])
        if a.command=='build' and a.pdf and not result.get('errors'):
            from docsite.pdf import build_pdfs
            result['pdf']=build_pdfs(root)
        print(json.dumps(result,ensure_ascii=False,indent=2));return int(bool(result.get('errors')))
    except (OSError,ValueError,RuntimeError) as exc:
        p.exit(1,'contextbase: '+str(exc)+'\n')

if __name__=='__main__':raise SystemExit(main())
