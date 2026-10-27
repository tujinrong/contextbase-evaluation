"""Verify publication independently of frozen business/Pilot approval results."""
from __future__ import annotations
import argparse
import json
import os
import subprocess
import sys
from pathlib import Path
from .common import sha, js, write
from .publish import migrate, check


def fingerprints(folder: Path) -> dict:
    return {p.relative_to(folder).as_posix():sha(p.read_bytes()) for p in sorted(folder.rglob('*'))
            if p.is_file() and '__pycache__' not in p.parts and p.suffix != '.pyc'}


def run(root: Path, repository: str, revision: str) -> dict:
    root=root.resolve();report=root/'report/docsite';report.mkdir(parents=True,exist_ok=True)
    protected=['input','src','src-dynamic','pilot']
    before={p:fingerprints(root/p) for p in protected}
    proc=subprocess.run([sys.executable,'-m','unittest','discover','-s','src/docsite/tests','-v'],cwd=root,capture_output=True,text=True)
    write(report/'tests.log',proc.stdout+proc.stderr)
    if proc.returncode:raise ValueError('Publication tests failed; see report/docsite/tests.log')
    imported=migrate(root,False)
    def isolated(command):
        args=[sys.executable,'-m','docsite',command,'--root',str(root)]
        if command=='build':args+=['--repository',repository,'--revision',revision]
        proc=subprocess.run(args,cwd=root,capture_output=True,text=True,timeout=180)
        if proc.returncode:
            raise ValueError('Publication '+command+' failed: '+proc.stderr[-2000:]+' '+proc.stdout[-2000:])
        return json.loads(proc.stdout)
    first=isolated('build');html_before=fingerprints(root/'output/html')
    second=isolated('build');stable=html_before==fingerprints(root/'output/html')
    validation=isolated('check')
    unchanged=before=={p:fingerprints(root/p) for p in protected}
    passed=stable and unchanged and not validation['errors']
    pruned=migrate(root,True) if passed else {'status':'not_pruned_due_to_validation_failure','pruned':0}
    result={'status':'pass' if passed else 'error','migration':imported,'cleanup':pruned,
            'reproducibility':{'identical':stable,'second_build_writes':second['written']},
            'protected_paths_unchanged':unchanged,'protected_path_counts':{k:len(v) for k,v in before.items()},
            'build':{k:v for k,v in first.items() if k!='documents'},'validation':validation,
            'execution_context':{'workflow_run_id':os.environ.get('GITHUB_RUN_ID'),
                                 'repository':repository,'source_revision':revision},
            'pilot_scope':'Frozen Pilot inputs and implementation are unchanged; publication is not a new business test.'}
    write(report/'execution.json',js(result));return result


def validate_browser_report(root: Path, browser: dict) -> None:
    expected={p.relative_to(root).as_posix() for p in (root/'output/html').rglob('*.html')}
    results=browser.get('results',[]);actual=[r['file'] for r in results]
    if not expected or set(actual)!=expected or len(actual)!=len(expected):
        raise ValueError('Browser report is empty or does not cover all HTML pages')
    if browser.get('pages')!=len(expected):raise ValueError('Browser page count is inconsistent')
    for row in results:
        if sha((root/row['file']).read_bytes())!=row.get('html_sha256'):
            raise ValueError('Browser report is stale: HTML changed')
    bad=[r for r in results if r['page_errors'] or r['external_requests'] or r['horizontal_overflow']
         or r['mermaid']['errors'] or r['mermaid']['rendered']!=r['mermaid']['expected']]
    if len(bad)!=browser.get('failed_pages') or (not bad)!=(browser.get('status')=='pass'):
        raise ValueError('Browser success status does not match individual results')


def summarize(root: Path) -> bool:
    root=root.resolve();report=root/'report/docsite'
    execution=json.loads((report/'execution.json').read_text(encoding='utf-8'))
    browser=json.loads((report/'browser.json').read_text(encoding='utf-8'))
    validate_browser_report(root,browser);checks=check(root)
    status='成功' if execution['status']=='pass' and browser['status']=='pass' and not checks['errors'] else '要修正'
    rows=[('Markdown原本',execution['build']['html_documents']),('MD内の画面レイアウト',checks['embedded_layouts']),
          ('HTML内の画面項目',checks['layout_items']),('HTMLページ（入口含む）',checks['html_pages_including_index']),
          ('flowchartのSVG描画',str(browser['mermaid_rendered'])+' / '+str(browser['mermaid_expected'])),
          ('ローカルリンク・アンカー検査',checks['local_links_checked']),('変換検査エラー',len(checks['errors'])),
          ('ブラウザー描画検査失敗',browser['failed_pages']),('同一入力での再ビルド書込件数',execution['reproducibility']['second_build_writes']),
          ('入力・解析器・固定Pilot入力の不変',execution['protected_paths_unchanged'])]
    text='# MD埋め込み・HTML変換の検証結果\n\n状態：**'+status+'**。表示変換の検証であり、業務仕様の新たな合格判定ではありません。\n\n'
    text+='| 検査 | 結果 |\n| --- | --- |\n'+''.join('| '+k+' | '+str(v)+' |\n' for k,v in rows)
    text+='\n## 配置\n\n各機能は`output/md/基本設計書`、共通・DB・開発規約は`output/md/共通`。画面レイアウトはMD内の生HTML断片です。`output/html`はMDだけから再生成します。\n\n[HTML入口](../../output/html/index.html) ／ [機能一覧MD](../../output/md/機能一覧.md)。\n'
    text+='\n## 検証の内容\n\n項目・共通部品・本文の文字列・表のセル・コード例・Mermaid原文・図のノードと接続数・相互リンクとアンカーを照合しました。検査対象が0件、ページ欠落、改変された本文、古いブラウザー結果は成功として扱いません。手修正したMDを複数回取り込んでも生成元の基準ハッシュを保持し、後日の原本変更との競合を検出します。\n'
    text+='\n## ブラウザー検査の範囲\n\nChromiumに全HTMLの内容をメモリで読み込み、外部リクエストを遮断した状態でSVGの描画と横方向のはみ出しを検査しました。ファイルを開いた実際のクリック遷移はこの検査の対象外です。リンク先の存在とアンカーは静的検査に含みます。\n'
    text+='\n## 実行と保存の証跡\n\n'
    ctx=execution['execution_context']
    if ctx.get('workflow_run_id'):
        text+='GitHub Actions実行ID：`'+ctx['workflow_run_id']+'`。入力コードの版：`'+ctx['source_revision']+'`。この文書は保存前の検証ステップで生成されます。リポジトリへの保存成功は、該当Actionsの保存ステップと生成コミットで確認してください。\n'
    else:
        text+='このレポートはローカル実行結果です。GitHub反映の成功を意味しません。入力コードの版：`'+ctx['source_revision']+'`。\n'
    text+='\n## 制限\n\nMDプレビューはCSS・フォーム部品を制限することがあるため、仕上がりはHTMLで確認します。画面例は実アプリを動作させません。Mermaidの基本flowchartをGraphvizでSVG化しており、Mermaid.jsと同じ配置や全構文対応は保証しません。未対応構文はエラーとします。入力・固定Pilotの仕様とソースは変更せず、従来の業務上の保留事項を維持しています。\n'
    write(report/'検証結果.md',text);return status=='成功'


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--root',default='.')
    parser.add_argument('--repository',default=os.environ.get('GITHUB_REPOSITORY',''))
    parser.add_argument('--revision',default='main');parser.add_argument('--summary',action='store_true')
    args=parser.parse_args();root=Path(args.root)
    if args.summary:raise SystemExit(0 if summarize(root) else 1)
    result=run(root,args.repository,args.revision);print(js(result));raise SystemExit(int(result['status']!='pass'))
