"""python -m docsite migrate | build | check | publish"""
from __future__ import annotations
import argparse, os
from pathlib import Path
from .common import js
from .publish import migrate, build, check


def main(argv=None) -> int:
    parser=argparse.ArgumentParser(description='画面HTMLを含むMarkdown原本と閲覧用HTMLを生成')
    parser.add_argument('command',choices=['migrate','build','check','publish'])
    parser.add_argument('--root',default='.')
    parser.add_argument('--prune-flat',action='store_true',help='移行が済んだ旧output直下のMD・画面HTMLだけを削除')
    parser.add_argument('--repository',default=os.environ.get('GITHUB_REPOSITORY',''),help='原本・評価へのリンク用owner/repo。空文字でローカルリンク')
    parser.add_argument('--revision',default='main',help='証跡リンクに使うcommit SHA')
    args=parser.parse_args(argv);root=Path(args.root).resolve()
    try:
        if args.command=='migrate':result=migrate(root,args.prune_flat)
        elif args.command=='build':result=build(root,args.repository,args.revision)
        elif args.command=='check':result=check(root)
        else:
            imported=migrate(root,False)
            generated=build(root,args.repository,args.revision)
            validation=check(root)
            cleanup=migrate(root,True) if args.prune_flat and not validation['errors'] else {'pruned':0}
            result={'migration':imported,'build':{k:v for k,v in generated.items() if k!='documents'},'validation':validation,'cleanup':cleanup}
        print(js(result))
        return int(result.get('status')=='error' or bool(result.get('validation',{}).get('errors')))
    except (OSError,ValueError) as error:
        parser.exit(1,'docsite: '+str(error)+'\n')

if __name__=='__main__':raise SystemExit(main())
