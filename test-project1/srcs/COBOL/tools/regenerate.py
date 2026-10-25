"""Regenerate the reusable resources while QA-TEXT-COBOL remains unresolved."""
import sys
sys.dont_write_bytecode = True
from pathlib import Path
import subprocess,sys,os
ROOT=Path(__file__).resolve().parents[1]
os.chdir(ROOT)
subprocess.run([sys.executable,'tools/input_lock.py'],check=True)
if sys.argv[1:] != ['--reusable-only']:
 raise SystemExit('BLOCKED QA-TEXT-COBOL: select and specify the terminal/render/input/auth adapter before Text generation. Use --reusable-only for SQL catalog and DDL; this does not generate Text UI.')
subprocess.run([sys.executable,'tools/catalog.py'],check=True)
subprocess.run(['node','tools/generate_database.mjs'],check=True)
print('PARTIAL: SQL catalog and database scripts regenerated; Text application generation BLOCKED; no DB execution.')
