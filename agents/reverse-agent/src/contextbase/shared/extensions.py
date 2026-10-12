"""Explicit reviewed project extensions; input is never an import directory."""
from __future__ import annotations
import importlib.util
from pathlib import Path
from .store import safe, read, digest


def load_extension(root: Path, input_dir: str):
    accepted=[];changed=[]
    source=safe(root,input_dir)
    for manifest_path in sorted(safe(root,'src-dynamic').glob('*/extension.json')):
        directory=manifest_path.parent;safe(root,manifest_path)
        manifest=read(manifest_path)
        if manifest.get('schema')!='contextbase.extension.v1' or manifest.get('trust')!='repository-reviewed':
            raise ValueError('Unreviewed extension')
        config=read(safe(directory,manifest['source_config']))
        if not safe(source,config['source']).is_file():continue
        mismatch=[]
        for relative,expected in config['checksums'].items():
            p=safe(source,Path(config['base'])/relative)
            if not p.is_file() or digest(p.read_text(encoding='utf-8-sig').replace('\r\n','\n'))!=expected:
                mismatch.append(relative)
        if mismatch:
            changed.extend(mismatch);continue
        adapter=safe(directory,manifest['adapter'])
        if digest(adapter.read_bytes())!=manifest['adapter_sha256']:
            raise ValueError('Extension code changed without updating the reviewed hash')
        spec=importlib.util.spec_from_file_location('contextbase_extension_'+digest(str(directory))[:12],adapter)
        if not spec or not spec.loader:raise ValueError('Invalid extension module')
        module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
        accepted.append(({**config,'directory':directory,'review_data':manifest['review_data']},module))
    if len(accepted)>1:raise ValueError('Multiple reviewed extensions match; select one project explicitly')
    return (*accepted[0],changed) if accepted else (None,None,changed)
