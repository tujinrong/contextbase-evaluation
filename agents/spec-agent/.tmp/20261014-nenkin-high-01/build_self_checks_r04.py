"""Fresh toy fixed-boundary positive and matched-prompt-SHA negative."""
from pathlib import Path
BASE = Path(__file__).parent
for old_name,new_name,old_out,new_out in (
    ('self_check_writer_driver_r03.py','self_check_writer_driver_r04.py','author-driver-synthetic-r03','author-driver-synthetic-r04'),
    ('self_check_previous_revision_r03.py','self_check_previous_revision_r04.py','author-revision-synthetic-r03','author-revision-synthetic-r04'),
):
    source=(BASE/old_name).read_text(encoding='utf-8').replace('nenkin_writer_driver_r03.py','nenkin_writer_driver_r04.py').replace(old_out,new_out)
    if old_name.startswith('self_check_writer'):
        source=source.replace('from types import SimpleNamespace','from types import SimpleNamespace, ModuleType')
        source=source.replace("# Actual AST provider-evidence function runs", "toy_pkg=ModuleType('contextbase'); toy_pkg.__path__=[]\ntoy_ai=ModuleType('contextbase.ai'); toy_ai.__path__=[]\ntoy_ai.provider=SimpleNamespace(COMMON_POLICY='toy frozen policy')\nsys.modules.update({'contextbase':toy_pkg,'contextbase.ai':toy_ai})\n# Actual AST provider-evidence function runs")
        source=source.replace("(job / 'prompt.txt').write_text('toy prompt', encoding='utf-8')", "(job / 'prompt.txt').write_bytes((toy_ai.provider.COMMON_POLICY + '\\nUser task (within that boundary):\\ntoy prompt').encode('utf-8'))")
        marker="case('toy provider raw4 evidence2 accepted', lambda: env['provider_evidence'](snap, job, schema, state), True)"
        source=source.replace(marker,marker+"\nold_prompt=(job/'prompt.txt').read_bytes()\n(job/'prompt.txt').write_bytes(b'other policy with unchanged data')\nbad=deepcopy(result);bad['metadata']['prompt_sha256']=env['sha'](job/'prompt.txt');jwrite(job/'result.json',bad)\ncase('provider rejects changed policy with matched promptSHA',lambda:env['provider_evidence'](snap,job,schema,state),False)\n(job/'prompt.txt').write_bytes(old_prompt);jwrite(job/'result.json',result)")
    else:
        source=source.replace('ai.workflow = workflow; ai.capsule = capsule; ai.schemas = schemas','ai.workflow = workflow; ai.capsule = capsule; ai.schemas = schemas; ai.provider = SimpleNamespace(COMMON_POLICY="toy frozen policy")')
        source=source.replace("(job / 'prompt.txt').write_bytes(prompt.encode('utf-8'))", "(job / 'prompt.txt').write_bytes((ai.provider.COMMON_POLICY + '\\nUser task (within that boundary):\\n' + prompt).encode('utf-8'))")
    with (BASE/new_name).open('x',encoding='utf-8',newline='\n') as out:
        out.write(source)
