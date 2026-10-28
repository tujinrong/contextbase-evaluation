"""Generate the frozen Windows/no-auth sample from this method's templates."""
import sys
sys.dont_write_bytecode = True
from pathlib import Path
import subprocess, os
ROOT=Path(__file__).resolve().parents[1]
os.chdir(ROOT)
subprocess.run([sys.executable,'tools/input_lock.py'],check=True)
if sys.argv[1:] == ['--reusable-only']:
 steps=['catalog.py']
elif sys.argv[1:]:
 raise SystemExit('Usage: regenerate.py [--reusable-only]')
else:
 steps=['generate.py','emit_workflows.py','emit_search.py','emit_prompt.py',
        'emit_navigation.py','emit_maintenance.py','emit_ui.py','catalog.py']
for step in steps:
 subprocess.run([sys.executable,'tools/'+step],check=True)
subprocess.run(['node','tools/generate_database.mjs'],check=True)
print('Generated Windows Text sample sources and SQL/DDL. No database execution or native acceptance implied.')
