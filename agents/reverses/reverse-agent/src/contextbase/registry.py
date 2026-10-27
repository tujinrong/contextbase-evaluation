"""Trusted project plugins are separate from untrusted analysis input."""
from __future__ import annotations
import hashlib
import json
import os
import re
import tomllib
from pathlib import Path


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def configure(root: Path, filename: str = 'config/project.toml', *, require_input: bool = True) -> dict:
    """Read safe settings; publication-only commands need no application input."""
    root = root.resolve(); file=(root/filename).resolve()
    if not file.is_relative_to(root):raise ValueError('Configuration must be inside repository')
    data=tomllib.loads(file.read_text(encoding='utf-8')) if file.exists() else {'project':{'id':'project','input':'input','profile':'auto'}}
    cfg=data.get('project',{})
    if set(cfg)-{'id','input','profile','repository','max_file_bytes'}:raise ValueError('Unknown project configuration key')
    cfg={'id':'project','input':'input','profile':'auto','repository':'','max_file_bytes':4_000_000,**cfg}
    if not re.fullmatch(r'[A-Za-z0-9_-]+',cfg['id']):raise ValueError('Invalid project ID')
    source=root/cfg['input'];resolved=source.resolve()
    if source.is_symlink() or resolved==root or not resolved.is_relative_to(root):raise ValueError('Unsafe input directory')
    for name in ['src','src-dynamic','output','ContextBase','report','QA','pilot','.specgen-state','.contextbase-work']:
        p=root/name
        if resolved.is_relative_to(p) or p.is_relative_to(resolved):raise ValueError('Input overlaps code or generated folders')
    if require_input and not source.is_dir():raise ValueError('Input directory does not exist')
    if not isinstance(cfg['max_file_bytes'],int) or cfg['max_file_bytes']<=0:raise ValueError('Invalid size limit')
    return cfg


def resolve_profile(root: Path, cfg: dict) -> dict | None:
    """Inspect JSON only. No target-supplied code is executed for plugin selection."""
    requested=cfg['profile']
    if requested=='generic':return None
    home=(root/'src-dynamic').resolve();candidates=[]
    for file in sorted(home.glob('*/manifest.json')):
        if file.is_symlink() or not file.resolve().is_relative_to(home):raise ValueError('Unsafe plugin manifest')
        p=json.loads(file.read_text(encoding='utf-8'))
        if requested not in {'auto',p['id']}:continue
        if p.get('schema_version')!=1 or p.get('trust')!='repository-reviewed':raise ValueError('Unapproved profile schema or trust')
        source=(root/cfg['input']).resolve();matches=[]
        for a in p.get('anchors',[]):
            f=source/a['path']
            matches.append(f.is_file() and not f.is_symlink() and f.resolve().is_relative_to(source) and digest(f.read_bytes())==a['sha256'])
        if matches and all(matches):candidates.append({**p,'directory':str(file.parent.resolve())})
    if len(candidates)>1:raise ValueError('Several profiles match; choose one explicitly')
    if not candidates and requested!='auto':raise ValueError('Requested profile does not match source identity; use generic or review src-dynamic profile')
    return candidates[0] if candidates else None


def process_env(root: Path, profile: dict | None = None) -> dict:
    paths=[str((root/'src').resolve())]
    if profile:
        path=Path(profile['directory']).resolve()
        if not path.is_relative_to((root/'src-dynamic').resolve()):raise ValueError('Dynamic code outside src-dynamic')
        paths.insert(0,str(path))
    return {**os.environ,'PYTHONPATH':os.pathsep.join(paths),'PYTHONUTF8':'1','PYTHONDONTWRITEBYTECODE':'1'}
