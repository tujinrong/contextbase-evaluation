"""Regenerate this project only, in the required deterministic sequence."""
from pathlib import Path
import subprocess,sys,os
ROOT=Path(__file__).resolve().parents[1]
os.chdir(ROOT)
subprocess.run([sys.executable,'tools/input_lock.py'],check=True)
for name in ['generate','emit_workflows','emit_search','emit_prompt','emit_navigation','emit_ui','emit_maintenance','catalog']:
 subprocess.run([sys.executable,f'tools/{name}.py'],check=True)
subprocess.run(['node','tools/generate_database.mjs'],check=True)
