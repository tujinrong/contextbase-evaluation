"""Fresh functions-only synthetic fixtures; no production inputs or provider."""
from pathlib import Path
BASE = Path(__file__).parent
for old_name, new_name, old_out, new_out in (
    ('self_check_writer_driver_r02.py', 'self_check_writer_driver_r03.py', 'author-driver-synthetic-r02', 'author-driver-synthetic-r03'),
    ('self_check_previous_revision_r02.py', 'self_check_previous_revision_r03.py', 'author-revision-synthetic-r02', 'author-revision-synthetic-r03'),
):
    source = (BASE / old_name).read_text(encoding='utf-8').replace('nenkin_writer_driver_r02.py', 'nenkin_writer_driver_r03.py').replace(old_out, new_out)
    if old_name.startswith('self_check_previous'):
        source = source.replace("(job / 'prompt.txt').write_text(prompt, encoding='utf-8')", "(job / 'prompt.txt').write_bytes(prompt.encode('utf-8'))")
    with (BASE / new_name).open('x', encoding='utf-8', newline='\n') as out:
        out.write(source)
