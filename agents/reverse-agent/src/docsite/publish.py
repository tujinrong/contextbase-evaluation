"""Migrate a flat output set, then render Markdown as the sole document input."""
from __future__ import annotations
from collections import Counter
import html, importlib.metadata, json, os, re, time, gc
from pathlib import Path
from urllib.parse import quote, unquote, urlsplit
from bs4 import BeautifulSoup
from . import __version__
from .diagram import render as render_diagram
from .common import (PARSER, FEATURE, BEGIN, END, sha, js, read_json, write, inside,
                     relative, rewrite_links, insert_layout, embed_layout, fences, check_html)


def classify(name: str) -> Path:
    if name == '機能一覧.md': return Path(name)
    m = FEATURE.fullmatch(name)
    if m and not re.match(r'^(?:COM|SYS)(?:-|\d)', m[1], re.I): return Path('基本設計書')/name
    return Path('共通')/name


def migrate(root: Path, prune: bool = False) -> dict:
    """One-way import; preserve manual Markdown edits against later upstream changes."""
    root = root.resolve(); output = root/'output'; state = root/'.specgen-state/docsite'
    previous = read_json(state/'migration.json')
    sources = sorted(p for p in output.glob('*.md') if p.name != 'README.md')
    for p in sources: inside(root,p)
    if not sources:
        if (output/'md').is_dir(): return {'status':'already_migrated','imported':0,'pruned':0}
        raise ValueError('No generated Markdown under output/')
    mapping = {p.resolve():(output/'md'/classify(p.name),'') for p in sources}
    source_hashes = {p:sha(p.read_bytes()) for p in sources}
    layouts = {}
    for p in sources:
        match = FEATURE.fullmatch(p.name)
        if match and classify(p.name).parent == Path('基本設計書'):
            layout = output/('画面レイアウト'+match[1]+'_'+match[2]+'.html')
            if layout.exists():
                inside(root,layout); layouts[p] = layout; source_hashes[layout] = sha(layout.read_bytes())
                mapping[layout.resolve()] = (mapping[p.resolve()][0], 'screen-layout')
    rows = dict(previous.get('files', {})); plans = {}; errors = []; counts = []
    for p in sources:
        target = mapping[p.resolve()][0]; inside(root,target)
        original = p.read_text(encoding='utf-8-sig'); text = original; keys = []
        layout = layouts.get(p)
        if layout:
            block, keys = embed_layout(layout.read_text(encoding='utf-8-sig'))
            text = insert_layout(text, block)
        text = rewrite_links(text,p,target,mapping)
        if fences(original) != fences(text): raise ValueError(f'Fenced examples changed: {p.name}')
        old = previous.get('files',{}).get(p.name,{})
        upstream = sha(original + ('\n'+layout.read_text(encoding='utf-8-sig') if layout else ''))
        generated_hash = sha(text)
        if target.exists() and target.read_text(encoding='utf-8') != text:
            actual = sha(target.read_bytes())
            if actual != old.get('generated_md_sha256', old.get('md_sha256')):
                if upstream == old.get('upstream_sha256'):
                    text = target.read_text(encoding='utf-8')
                else:
                    errors.append(target.relative_to(root).as_posix()); continue
        plans[target] = text
        rows[p.name] = {'md':target.relative_to(root).as_posix(), 'md_sha256':sha(text),
                        'generated_md_sha256':generated_hash, 'upstream_sha256':upstream, 'input_md_sha256':sha(original),
                        'layout':layout.name if layout else None, 'layout_items':len(keys),
                        'fenced_blocks_preserved':len(fences(original)),
                        'mermaid_blocks':sum(a.strip()=='mermaid' for a,b in fences(original))}
        counts.append({'name':p.name, 'layout_items':len(keys), 'embedded':bool(layout)})
    if errors: raise ValueError('Canonical Markdown and upstream both changed; reconcile: '+', '.join(errors))
    references = []
    for folder in [root/'docs',root/'report']:
        for p in sorted(folder.rglob('*.md')) if folder.exists() else []:
            if p.is_symlink() or p.is_relative_to(root/'report/docsite'): continue
            before = p.read_text(encoding='utf-8-sig')
            after = rewrite_links(before,p,p,mapping)
            if before != after: plans[p] = after; references.append(p.relative_to(root).as_posix())
    changed = [str(p) for p,h in source_hashes.items() if not p.exists() or sha(p.read_bytes()) != h]
    if changed: raise ValueError('Upstream changed during migration: ' + ', '.join(changed))
    for target,text in plans.items(): write(target,text)
    write(state/'migration.json',js({'version':__version__,'files':rows}))
    write(root/'report/docsite/migration.json',js({'documents':counts,'reference_links_updated':references,
        'policy':'fenced contracts and Mermaid are unchanged; layout is raw HTML in MD',
        'historical_output':'Previous revisions remain in Git history; current publication is output/md and output/html'}))
    removed = 0
    if prune:
        changed = [str(p) for p,h in source_hashes.items() if not p.exists() or sha(p.read_bytes()) != h]
        if changed: raise ValueError('Upstream changed before pruning: ' + ', '.join(changed))
        for p in list(sources)+list(layouts.values()):
            p.unlink(); removed += 1
    write(output/'README.md', '# 仕様書の閲覧\n\n'
          '- [Markdown原本](md/機能一覧.md) — 画面レイアウトHTMLを各仕様書に埋め込んでいます。\n'
          '- [HTML閲覧用の入口](html/index.html) — ダウンロード後、ブラウザーで開いてください。\n\n'
          '`md/基本設計書` は機能別、`md/共通` は共通・DB・開発規約です。HTMLは同じ分類で `html/` に生成します。\n\n'
          '現行版は `md/` と `html/` を参照してください。過去版はGit履歴で確認できます。\n')
    return {'status':'migrated','imported':len(sources),'embedded_layouts':len(layouts),
            'layout_items':sum(x['layout_items'] for x in counts),'pruned':removed,
            'reference_links_updated':len(references)}


def slug(text: str) -> str:
    plain = html.unescape(re.sub('<[^>]*>','',text)).lower().strip()
    return re.sub(r'[^\w\-\s]','',plain).replace(' ','-') or 'section'


def prepare_markdown(text: str):
    parser = PARSER(); env = {}; tokens = parser.parse(text,env)
    toc = []; used = Counter()
    for i, token in enumerate(tokens):
        if token.type == 'heading_open' and i+1 < len(tokens):
            label = tokens[i+1].content
            anchor = slug(label); ordinal = used[anchor]; used[anchor]+=1
            if ordinal: anchor += '-'+str(ordinal)
            token.attrSet('id',anchor)
            if token.tag in {'h2','h3'}: toc.append((int(token.tag[1]),label,anchor))
    original_fence = parser.renderer.rules['fence']
    def fence(rule_tokens,index,options,render_env):
        token = rule_tokens[index]
        if token.info.strip() == 'mermaid':
            escaped = html.escape(token.content, quote=False)
            render_env['_diagram_index'] = render_env.get('_diagram_index',0) + 1
            svg = render_diagram(token.content,'diagram-'+str(render_env['_diagram_index']))
            return '<figure class="diagram">'+svg+'<details class="diagram-source"><summary>図の定義を表示</summary><pre><code class="language-mermaid">'+escaped+'</code></pre></details></figure>\n'
        return original_fence(rule_tokens,index,options,render_env)
    parser.renderer.rules['fence'] = fence
    content = parser.renderer.render(tokens,parser.options,env)
    check_html(content)
    return content,toc


def html_document(text: str, source: Path, target: Path, documents: dict[Path, Path],
                  root: Path, repository: str, revision: str) -> str:
    content,toc = prepare_markdown(text)
    soup = BeautifulSoup(content,'html.parser')
    for node in soup.find_all(['a','img']):
        attr = 'href' if node.name=='a' else 'src'
        if not node.has_attr(attr): continue
        url = str(node[attr]); parts = urlsplit(url)
        if parts.scheme or parts.netloc or not parts.path: continue
        old = (source.parent/unquote(parts.path)).resolve()
        if old in documents:
            node[attr] = relative(target,documents[old],parts.fragment)
        elif old.is_relative_to(root/'output/md'):
            node[attr] = relative(target,root/'output/html'/old.relative_to(root/'output/md'),parts.fragment)
        elif repository and old.is_relative_to(root):
            rel = quote(old.relative_to(root).as_posix(),safe='/')
            node[attr] = 'https://github.com/'+repository+'/blob/'+revision+'/'+rel+('#'+quote(parts.fragment,safe='-') if parts.fragment else '')
        else:
            node[attr] = relative(target,old,parts.fragment)
    for table in list(soup.find_all('table')):
        if table.find_parent(class_='screen-layout'): continue
        box = soup.new_tag('div',attrs={'class':'table-scroll','tabindex':'0','role':'region','aria-label':'仕様表（横スクロール可）'})
        table.wrap(box)
    heading = soup.find('h1'); title = heading.get_text(' ',strip=True) if heading else source.stem
    nav = ''.join('<li class="level-'+str(level)+'"><a href="#'+html.escape(anchor,quote=True)+'">'+html.escape(label)+'</a></li>' for level,label,anchor in toc)
    index = relative(target,root/'output/html/index.html')
    raw = relative(target,source if source.suffix=='.md' else root/'output/md/機能一覧.md')
    sidebar = '<aside class="toc"><div class="toc-heading">この文書の内容</div><ol>'+nav+'</ol></aside>' if toc else ''
    shell = 'page-shell' if toc else 'page-shell no-toc'
    csp = "default-src 'none'; script-src 'none'; style-src 'self' 'unsafe-inline' file:; img-src 'self' data: file:; font-src 'self' file:; connect-src 'none'; object-src 'none'; base-uri 'none'; form-action 'none'"
    return '<!doctype html>\n<html lang="ja"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'+\
        '<meta http-equiv="Content-Security-Policy" content="'+html.escape(csp,quote=True)+'"><meta name="docsite-source-sha256" content="'+sha(text)+'">'+\
        '<title>'+html.escape(title)+'</title><style>'+(Path(__file__).parent/'assets/site.css').read_text(encoding='utf-8')+'</style></head><body>'+\
        '<header class="topbar"><a class="brand" href="'+index+'">CONTEXTBASE <span>仕様書</span></a><nav><a href="'+index+'">文書一覧</a><a href="'+raw+'">MD原本</a></nav></header>'+\
        '<div class="'+shell+'">'+sidebar+\
        '<main class="document"><article class="doc-body">'+str(soup)+'</article><footer>Markdown原本から生成した閲覧用HTMLです。画面例は実システムを操作しません。</footer></main></div></body></html>\n'


def build(root: Path, repository: str = '', revision: str = 'main', _unused: bool = False) -> dict:
    root=root.resolve();mdroot=inside(root,root/'output/md');htmlroot=inside(root,root/'output/html')
    files=sorted(mdroot.rglob('*.md'))
    if not files: raise ValueError('No Markdown in output/md. Run migrate first.')
    for p in files: inside(root,p)
    if revision != 'main' and not re.fullmatch('[a-fA-F0-9]{40}',revision): raise ValueError('Revision must be main or a full commit SHA')
    if repository and not re.fullmatch(r'[\w.-]+/[\w.-]+',repository): raise ValueError('Invalid repository name')
    manifest_path=root/'.specgen-state/docsite/html.json';previous=read_json(manifest_path)
    pages={p.resolve():htmlroot/p.relative_to(mdroot).with_suffix('.html') for p in files}
    rows=[]
    for source,target in pages.items():
        title=next((l[2:] for l in source.read_text(encoding='utf-8').splitlines() if l.startswith('# ')),source.stem)
        category=source.parent.name if source.parent!=mdroot else '一覧'
        rows.append((category,title,relative(htmlroot/'index.html',target)))
    plans={};summaries=[];began=time.perf_counter()
    for source,target in pages.items():
        text=source.read_text(encoding='utf-8')
        plans[target]=html_document(text,source,target,pages,root,repository,revision)
        gc.collect()
        summaries.append({'source':source.relative_to(root).as_posix(),'html':target.relative_to(root).as_posix(),
            'source_sha256':sha(text),'html_sha256':sha(plans[target]),'embedded_layouts':text.count(BEGIN),
            'mermaid_blocks':sum(a.strip()=='mermaid' for a,b in fences(text))})
    group_order=['一覧','基本設計書','共通']
    index='<p class="lead">機能別の基本設計書と、システムを横断する共通仕様をまとめています。</p>'
    for category in group_order+sorted({r[0] for r in rows}-set(group_order)):
        selected=[r for r in rows if r[0]==category]
        if not selected: continue
        index+='<h2>'+html.escape(category)+' <small>'+str(len(selected))+'文書</small></h2><div class="doc-grid">'
        for cat,title,url in selected:
            index+='<a class="doc-card" href="'+url+'"><span>'+html.escape(cat)+'</span><strong>'+html.escape(title)+'</strong></a>'
        index+='</div>'
    index_md='# 仕様書一覧\n\n'+index
    plans[htmlroot/'index.html']=html_document(index_md,htmlroot/'index.html',htmlroot/'index.html',{},root,'',revision)
    assets=Path(__file__).parent/'assets'
    for name in ['site.css']:plans[htmlroot/'_assets'/name]=(assets/name).read_bytes()
    for p in mdroot.rglob('*'):
        if p.is_file() and p.suffix.lower() in {'.png','.jpg','.jpeg','.webp','.gif','.svg','.css'}:
            inside(root,p);plans[htmlroot/p.relative_to(mdroot)]=p.read_bytes()
    conflicts=[]
    for target,value in plans.items():
        inside(root,target);key=target.relative_to(root).as_posix()
        if target.exists() and sha(target.read_bytes()) not in {sha(value),previous.get('files',{}).get(key)}: conflicts.append(key)
    if conflicts:raise ValueError('Edited/unmanaged HTML output would be overwritten: '+', '.join(conflicts))
    written=sum(write(p,value) for p,value in plans.items())
    owned={p.relative_to(root).as_posix():sha(value) for p,value in plans.items()}
    stale=[]
    for key,digest in previous.get('files',{}).items():
        if key in owned:continue
        p=inside(root,root/key)
        if p.is_relative_to(htmlroot) and p.exists() and sha(p.read_bytes())==digest:p.unlink();stale.append(key)
    write(manifest_path,js({'version':__version__,'files':owned,'revision':revision}))
    report={'version':__version__,'documents':summaries,'html_documents':len(pages),'embedded_layouts':sum(x['embedded_layouts'] for x in summaries),
       'mermaid_blocks':sum(x['mermaid_blocks'] for x in summaries),'written':written,'unchanged':len(plans)-written,'stale_removed':stale,
       'elapsed_seconds':round(time.perf_counter()-began,3),'source_revision':revision,
       'diagram_engine':'Graphviz strict flowchart subset (static SVG)',
       'packages':{name:importlib.metadata.version(name) for name in ['markdown-it-py','beautifulsoup4','tinycss2']}}
    write(root/'report/docsite/build.json',js(report))
    return report


def check(root: Path) -> dict:
    root=root.resolve();files=sorted((root/'output/html').rglob('*.html'));errors=[]
    # Keep only the anchor index, not every page's DOM, during full verification.
    pages=set(files);anchors={}
    for path in files:
        fragment=BeautifulSoup(path.read_text(encoding='utf-8'),'html.parser')
        anchors[path]={n['id'] for n in fragment.find_all(id=True)}
        fragment.decompose()
    gc.collect()
    links=0;layouts=0;items=0;diagrams=0
    md_files=sorted((root/'output/md').rglob('*.md'))
    if not md_files:errors.append({'rule':'no_markdown_sources'})
    if not files:errors.append({'rule':'no_html_pages'})
    for source in md_files:
        target=root/'output/html'/source.relative_to(root/'output/md').with_suffix('.html')
        if target not in pages:errors.append({'file':source.name,'rule':'missing_html_page'})
    if root/'output/html/index.html' not in pages:errors.append({'rule':'missing_index'})
    for path in files:
        soup=BeautifulSoup(path.read_text(encoding='utf-8'),'html.parser')
        ids=[n['id'] for n in soup.find_all(id=True)]
        if len(ids)!=len(set(ids)):errors.append({'file':path.name,'rule':'duplicate_ids'})
        for node in soup.select('[href], [src]'):
            url=node.get('href',node.get('src',''));u=urlsplit(url)
            if u.scheme or u.netloc:continue
            target=(path.parent/unquote(u.path)).resolve() if u.path else path
            links+=1
            if not target.exists():errors.append({'file':path.name,'rule':'broken_link','target':url});continue
            if u.fragment and target in pages and unquote(u.fragment) not in anchors[target]:
                errors.append({'file':path.name,'rule':'missing_anchor','target':url})
        if path.name=='index.html' and path.parent==root/'output/html':continue
        source=root/'output/md'/path.relative_to(root/'output/html').with_suffix('.md')
        if not source.exists():errors.append({'file':path.name,'rule':'missing_md_source'});continue
        text=source.read_text(encoding='utf-8');expected=PARSER().parse(text)
        meta=soup.find('meta',attrs={'name':'docsite-source-sha256'})
        if meta is None or meta.get('content')!=sha(text):errors.append({'file':path.name,'rule':'source_hash'})
        article=soup.select_one('article.doc-body')
        if article is None:
            errors.append({'file':path.name,'rule':'missing_article'});continue
        raw=BeautifulSoup(PARSER().render(text),'html.parser')
        for selector in ['[data-item]','[data-component]']:
            attribute='data-item' if selector=='[data-item]' else 'data-component'
            if Counter(n[attribute] for n in raw.select(selector))!=Counter(n[attribute] for n in article.select(selector)):
                errors.append({'file':path.name,'rule':'embedded_component_loss','selector':selector})
        md_mermaids=[t.content for t in expected if t.type=='fence' and t.info.strip()=='mermaid']
        html_mermaids=[n.get_text() for n in article.select('.diagram-source code.language-mermaid')]
        if md_mermaids!=html_mermaids:errors.append({'file':path.name,'rule':'mermaid_changed'})
        svgs=article.select('svg.flowchart-svg')
        if len(svgs)!=len(md_mermaids):errors.append({'file':path.name,'rule':'diagram_svg_loss'})
        for code,svg in zip(md_mermaids,svgs):
            if svg.get('data-source-sha256')!=sha(code):errors.append({'file':path.name,'rule':'diagram_source_hash'})
            if len(svg.select('g.node'))!=int(svg.get('data-node-count',0)) or len(svg.select('g.edge'))!=int(svg.get('data-edge-count',0)):errors.append({'file':path.name,'rule':'diagram_node_edge_loss'})
        if len(raw.find_all('table'))!=len(article.find_all('table')):errors.append({'file':path.name,'rule':'table_loss'})
        if len(raw.select('table tr'))!=len(article.select('table tr')):errors.append({'file':path.name,'rule':'table_row_loss'})
        def cells(container):
            return [[c.get_text(' ',strip=True) for c in row.find_all(['th','td'],recursive=False)] for row in container.select('table tr')]
        if cells(raw)!=cells(article):errors.append({'file':path.name,'rule':'table_cell_changed'})
        visible=BeautifulSoup(str(article),'html.parser')
        for node in visible.select('figure.diagram svg, figure.diagram summary'):node.decompose()
        def content_text(container):
            for node in container.find_all(['style','script']):node.decompose()
            return ' '.join(container.get_text(' ',strip=True).split())
        if content_text(BeautifulSoup(str(raw),'html.parser'))!=content_text(visible):
            errors.append({'file':path.name,'rule':'visible_content_changed'})
        expected_code=[t.content for t in expected if t.type in {'fence','code_block'} and t.info.strip()!='mermaid']
        actual_code=[n.get_text() for n in article.select('pre > code') if 'language-mermaid' not in n.get('class',[])]
        if expected_code!=actual_code:errors.append({'file':path.name,'rule':'code_example_changed'})
        layouts+=len(article.select('.screen-layout'));items+=len(article.select('[data-item]'));diagrams+=len(html_mermaids)
        raw.decompose();visible.decompose();soup.decompose();gc.collect()
    result={'status':'pass' if not errors else 'error','html_pages_including_index':len(files),'embedded_layouts':layouts,'layout_items':items,'mermaid_blocks':diagrams,'local_links_checked':links,'errors':errors,
       'scope':'conversion fidelity, links, counts, hashes; not a reassessment of business specifications'}
    write(root/'report/docsite/validation.json',js(result))
    return result
