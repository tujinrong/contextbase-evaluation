"""Read-only multi-language discovery. Capability levels are never inferred as complete."""
from __future__ import annotations
from collections import Counter
import os
from pathlib import Path
from .registry import digest

EXCLUDED={'.git','node_modules','vendor','.venv','venv','packages','bin','obj','dist','build','__pycache__'}
LANGUAGES={'.py':'Python','.java':'Java','.cs':'C#','.vb':'VB.NET','.vue':'Vue',
           '.js':'JavaScript','.jsx':'JavaScript','.ts':'TypeScript','.tsx':'TypeScript',
           '.sql':'SQL','.vbp':'VB6 project','.frm':'VB6 form','.bas':'VB6/VBA','.cls':'VB6/VBA',
           '.mdb':'Access binary','.accdb':'Access binary','.xaml':'XAML','.csproj':'.NET project',
           '.vbproj':'.NET project','.sln':'.NET solution',
           '.cshtml':'Razor','.html':'HTML','.htm':'HTML','.jsp':'JSP',
           '.aspx':'ASP.NET markup','.ascx':'ASP.NET markup'}
CAPABILITIES={
 'Razor':'Static markup and simple PageModel annotations; dynamic rendering/DB lineage require review',
 'HTML':'Static controls, labels and fixed choices; dynamic JavaScript rendering unresolved',
 'JSP':'Static HTML only; Java/server-generated markup and data lineage unresolved',
 'ASP.NET markup':'Static HTML only; server controls and lifecycle require a target adapter',
 'Python':'AST structural extraction; business meaning requires review',
 'Java':'Limited token parsing; no full symbol or framework resolution',
 'C#':'Limited token parsing; no full symbol or framework resolution',
 'VB.NET':'Project plugin for tested VB/WPF; otherwise declaration-level fallback',
 'VB6/VBA':'Text declaration extraction; no COM or binary form execution',
 'VB6 form':'Control/property declarations; no ActiveX or .frx interpretation',
 'Access binary':'Detected only; exported modules, form/report definitions, queries and schema required',
 'Vue':'SFC template/script structural extraction; dynamic components and API linkage unresolved',
 'SQL':'CREATE TABLE and literal CRUD; not final migration schema'}


def probe(root: Path, cfg: dict) -> dict:
    source=root/cfg['input'];inventory=[]
    for folder,dirs,files in os.walk(source,followlinks=False):
        keep=[]
        for name in sorted(dirs):
            p=Path(folder)/name
            if p.is_symlink() or name in EXCLUDED:
                inventory.append({'path':p.relative_to(source).as_posix(),'status':'excluded_directory','reason':'symlink' if p.is_symlink() else 'dependencies_or_build'})
            else:keep.append(name)
        dirs[:]=keep
        for name in sorted(files):
            p=Path(folder)/name;rel=p.relative_to(source).as_posix()
            if p.is_symlink():inventory.append({'path':rel,'status':'excluded','reason':'symlink'});continue
            raw=p.read_bytes();ext=p.suffix.lower();language=LANGUAGES.get(ext)
            status='selected' if language else 'inventory_only'
            if language=='Access binary':status='requires_export'
            if len(raw)>cfg['max_file_bytes']:status='too_large'
            inventory.append({'path':rel,'sha256':digest(raw),'bytes':len(raw),'language':language,'status':status})
    langs=Counter(i['language'] for i in inventory if i.get('language'));families=[]
    if any(k in langs for k in ['VB6 project','VB6 form']):families.append('VB6')
    if 'Access binary' in langs:families.append('Access')
    if 'Java' in langs:families.append('Java')
    if any(k in langs for k in ['VB.NET','C#','.NET project','.NET solution']):families.append('.NET')
    if 'Vue' in langs:
        families.append('Vue')
        if any(k in langs for k in ['Java','C#','Python','JavaScript','TypeScript']):families.append('Vue + API candidate (linkage unverified)')
    for l in ['Python','SQL']:
        if l in langs:families.append(l)
    return {'schema_version':1,'project':cfg['id'],'input':cfg['input'],'languages':dict(langs),
            'families':families,'author':'未確認','customer':'未確認','business':'未確認',
            'source_files':sum('sha256' in i for i in inventory),'inventory':inventory,
            'capabilities':CAPABILITIES,'status':'requires_review',
            'snapshot_sha256':digest(__import__('json').dumps(inventory,sort_keys=True,ensure_ascii=False).encode())}
