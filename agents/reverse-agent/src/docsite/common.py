"""Content-preserving relocation and safe HTML fragment handling."""
from __future__ import annotations
import hashlib, html, json, os, re
from collections import Counter
from pathlib import Path
from urllib.parse import quote, unquote, urlsplit, urlunsplit
from bs4 import BeautifulSoup
from markdown_it import MarkdownIt
import tinycss2

PARSER = lambda: MarkdownIt('commonmark', {'html': True}).enable(['table', 'strikethrough'])
FEATURE = re.compile(r'^(?:概要仕様書|基本設計書)([^_]+)_(.+)\.md$')
BEGIN = '<!-- docsite:screen-layout begin -->'
END = '<!-- docsite:screen-layout end -->'


def sha(value: str | bytes) -> str:
    return hashlib.sha256(value.encode('utf-8') if isinstance(value, str) else value).hexdigest()


def js(value) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + '\n'


def read_json(path: Path) -> dict:
    if not path.exists(): return {}
    value = json.loads(path.read_text(encoding='utf-8'))
    if not isinstance(value, dict): raise ValueError(f'Invalid manifest: {path}')
    return value


def write(path: Path, value: str | bytes) -> bool:
    raw = value.encode('utf-8') if isinstance(value, str) else value
    if path.exists() and path.read_bytes() == raw: return False
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_name(path.name + '.tmp-' + str(os.getpid()))
    try:
        temp.write_bytes(raw)
        os.replace(temp, path)
    finally: temp.unlink(missing_ok=True)
    return True


def inside(root: Path, path: Path) -> Path:
    p = path.resolve()
    if p == root or not p.is_relative_to(root): raise ValueError(f'Outside project: {path}')
    current = path
    while current != root and current != current.parent:
        if current.is_symlink(): raise ValueError(f'Symlink is not supported: {path}')
        current = current.parent
    return p


def relative(src: Path, dest: Path, fragment: str = '') -> str:
    value = quote(os.path.relpath(dest, src.parent).replace(os.sep, '/'), safe='/')
    return value + ('#' + quote(unquote(fragment), safe='-_.~') if fragment else '')


def relocate_url(url: str, origin: Path, destination: Path, mapping: dict[Path, tuple[Path, str]]) -> str:
    parsed = urlsplit(html.unescape(url))
    if parsed.scheme or parsed.netloc or not parsed.path: return url
    target = (origin.parent / unquote(parsed.path)).resolve()
    moved, anchor = mapping.get(target, (target, parsed.fragment))
    new = relative(destination, moved, anchor or parsed.fragment)
    if parsed.query:
        pieces = urlsplit(new)
        new = urlunsplit(('', '', pieces.path, parsed.query, pieces.fragment))
    return new


def rewrite_links(text: str, origin: Path, destination: Path, mapping: dict) -> str:
    """Keep prose, examples, fenced JSON and Mermaid; relocate links only."""
    lines = text.splitlines(keepends=True)
    protected = set()
    for token in PARSER().parse(text):
        if token.type in {'fence', 'code_block'} and token.map:
            protected.update(range(*token.map))
    mdlink = re.compile(r'(!?\[[^\]\n]*\]\()(<[^>\n]+>|[^\s)]+)([^)\n]*\))')
    ref = re.compile(r'^(\s{0,3}\[[^\]\n]+\]:\s*)(<[^>\n]+>|\S+)(.*)$')
    attr = re.compile(r'((?:href|src)\s*=\s*)([\'\"])(.*?)\2', re.I)
    def convert(url):
        enclosed = url.startswith('<') and url.endswith('>')
        value = relocate_url(url[1:-1] if enclosed else url, origin, destination, mapping)
        return '<'+value+'>' if enclosed else value
    for n, line in enumerate(lines):
        if n in protected: continue
        chunks = re.split(r'(`+[^`\n]*`+)', line)
        for i in range(0, len(chunks), 2):
            chunks[i] = mdlink.sub(lambda m: m[1]+convert(m[2])+m[3], chunks[i])
            chunks[i] = ref.sub(lambda m: m[1]+convert(m[2])+m[3], chunks[i])
            chunks[i] = attr.sub(lambda m: m[1]+m[2]+html.escape(relocate_url(m[3], origin, destination, mapping), quote=True)+m[2], chunks[i])
        lines[n] = ''.join(chunks)
    return ''.join(lines)


def scoped_css(css: str) -> str:
    """Scope layout CSS including media rules. No external CSS."""
    if re.search(r'url\s*\(|@import|expression\s*\(', css, re.I): raise ValueError('External or executable layout CSS')
    output = []
    for rule in tinycss2.parse_stylesheet(css, skip_comments=True, skip_whitespace=True):
        if rule.type == 'qualified-rule':
            selectors = tinycss2.serialize(rule.prelude).strip()
            rewritten = []
            for selector in selectors.split(','):
                selector = selector.strip()
                if not selector: raise ValueError('Empty CSS selector')
                selector = re.sub(r'\bmain\b', '.layout-root', selector)
                if re.match(r'^body\b', selector): selector = re.sub(r'^body\b', '.screen-layout', selector)
                elif not selector.startswith('.screen-layout'): selector = '.screen-layout ' + selector
                rewritten.append(selector)
            output.append(','.join(rewritten) + '{' + tinycss2.serialize(rule.content) + '}')
        elif rule.type == 'at-rule' and rule.lower_at_keyword in {'media', 'supports'} and rule.content is not None:
            output.append('@'+rule.lower_at_keyword+' '+tinycss2.serialize(rule.prelude).strip()+'{'+scoped_css(tinycss2.serialize(rule.content))+'}')
        else: raise ValueError('Unsupported CSS rule in layout')
    return '\n'.join(output)


def check_html(fragment: str) -> None:
    soup = BeautifulSoup(fragment, 'html.parser')
    if soup.find(['script','iframe','object','embed','base','meta','link','form']):
        raise ValueError('Active HTML/external inclusion is forbidden in Markdown')
    for node in soup.find_all(True):
        for key, value in node.attrs.items():
            if key.lower().startswith('on') or key.lower() in {'srcdoc','formaction'}:
                raise ValueError('HTML event handlers are forbidden')
            if key in {'src','href','action','xlink:href'}:
                scheme = urlsplit(str(value).strip()).scheme.lower()
                if scheme not in {'','https','http','mailto'}: raise ValueError('Unsafe URL scheme')
        if node.name == 'style' or node.has_attr('style'):
            css = node.get_text() if node.name == 'style' else str(node['style'])
            if re.search(r'url\s*\(|@import|expression\s*\(', css, re.I): raise ValueError('External or executable CSS')
            if node.name == 'style':
                def verify(rules):
                    for r in rules:
                        if r.type == 'qualified-rule':
                            if any(not s.strip().startswith('.screen-layout') for s in tinycss2.serialize(r.prelude).split(',')):
                                raise ValueError('Layout style must be scoped to .screen-layout')
                        elif r.type == 'at-rule' and r.lower_at_keyword in {'media','supports'} and r.content is not None:
                            verify(tinycss2.parse_rule_list(r.content, skip_comments=True, skip_whitespace=True))
                        else: raise ValueError('Unsupported style rule')
                verify(tinycss2.parse_stylesheet(css, skip_comments=True, skip_whitespace=True))


def embed_layout(standalone: str) -> tuple[str, list[str]]:
    soup = BeautifulSoup(standalone, 'html.parser')
    main = soup.find('main')
    if main is None: raise ValueError('Layout HTML must have a main element')
    css = '\n'.join(s.get_text() for s in soup.find_all('style'))
    main.name = 'div'; main['class'] = list(main.get('class', [])) + ['layout-root']
    ids = {n['id']: 'screen-control-'+n['id'] for n in main.find_all(id=True)}
    for node in main.find_all(True):
        if node.get('id') in ids: node['id'] = ids[node['id']]
        if node.get('for') in ids: node['for'] = ids[node['for']]
    keys = [n['data-item'] for n in main.select('[data-item]')]
    fragment = '<div class="screen-layout" id="screen-layout">\n<style>\n'+scoped_css(css)+'\n</style>\n'+str(main)+'\n</div>'
    check_html(fragment)
    return BEGIN+'\n\n'+fragment+'\n\n'+END, keys


def fences(text: str) -> list[tuple[str, str]]:
    return [(t.info, t.content) for t in PARSER().parse(text) if t.type == 'fence']


def insert_layout(text: str, block: str) -> str:
    if BEGIN in text: raise ValueError('Layout already embedded; build from Markdown instead of migrating again')
    heading = re.search(r'^###\s+1\.2\s+レイアウト[^\n]*\n', text, re.M)
    if heading is None:
        heading = re.search(r'^#{2,4}\s+.*(?:レイアウト|画面構成)[^\n]*\n', text, re.M)
    if heading is None: raise ValueError('Screen layout section is absent; refusing to silently append it')
    begin = heading.end()
    tail = text[begin:]
    tail = re.sub(r'^\s*\[[^\]\n]*HTML[^\]\n]*\]\([^\n]+\)\s*\n', '\n', tail, count=1)
    return text[:begin] + '\n' + block + '\n' + tail
